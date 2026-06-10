from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.asset import (
    UploadResourceSystem, UploadResourceDatabase, UploadResourceTable, UploadResourceField,
    AuditRule,
)
from app.models.upload_mid import (
    UploadMidSystem, UploadMidDatabase, UploadMidTable, UploadMidField,
    MidFieldGenRule, MetadataFieldMapping, MidFieldModifyLog,
    UploadOperationLog, UploadResultTable, ClassifyMid,
)
from app.services.audit_engine import evaluate_rules


# 资产类型 → 本地模型映射
LOCAL_MODEL_MAP = {
    "system": (UploadResourceSystem, UploadMidSystem, "sys_group_id"),
    "database": (UploadResourceDatabase, UploadMidDatabase, "db_group_id"),
    "table": (UploadResourceTable, UploadMidTable, "tbl_group_id"),
    "field": (UploadResourceField, UploadMidField, "field_group_id"),
}

# 本地字段 → 中间表字段 默认映射
DEFAULT_FIELD_MAP = {
    "system": {"sys_code": "sys_code", "sys_name": "sys_name", "record_name": "record_name",
                "master_data_code": "master_data_code", "org_unit": "org_unit", "org_dept": "org_dept",
                "biz_owner": "biz_owner", "status": "status", "sys_func_type": "sys_func_type",
                "if_managed": "if_managed", "online_time": "online_time"},
    "database": {"db_name": "db_name", "db_type": "db_type"},
    "table": {"table_name_en": "table_name_en", "table_name_cn": "table_name",
              "table_desc": "table_introduct", "topic_domain": "table_domain",
              "sample_data": "sample_data"},
    "field": {"field_name_en": "field_name_en", "field_name_cn": "field_name_cn",
              "field_type": "field_type"},
}


class UploadEngine:
    """集团上报流程引擎"""

    def __init__(self, db: Session, operator: str = "系统"):
        self.db = db
        self.operator = operator

    # ─── 1. 同步到中间表 ─────────────────────────────

    def sync_to_mid(
        self,
        asset_type: str,
        scope_type: str = "system",
        scope_ids: Optional[List[str]] = None,
        overwrite_empty: bool = False,
    ) -> Dict[str, Any]:
        """同步本地元数据到中间表（UPSERT）"""
        if asset_type not in LOCAL_MODEL_MAP:
            return {"totalCount": 0, "syncCount": 0, "emptyOverwriteWarnings": []}

        local_model, mid_model, id_field = LOCAL_MODEL_MAP[asset_type]
        field_map = self._get_field_map(asset_type)

        # 查询本地记录
        query = self.db.query(local_model)
        if scope_ids:
            query = query.filter(getattr(local_model, id_field).in_(scope_ids))
        local_records = query.all()

        warnings = []
        sync_count = 0

        for rec in local_records:
            local_biz_id = str(getattr(rec, id_field))
            # 检查中间表是否已有记录
            existing = self.db.query(mid_model).filter(
                mid_model.local_biz_id == local_biz_id
            ).first()

            # 构建更新数据
            update_data = {}
            for local_f, mid_f in field_map.items():
                val = getattr(rec, local_f, None)
                str_val = str(val) if val is not None else None

                if existing and not overwrite_empty:
                    existing_val = getattr(existing, mid_f, None)
                    if existing_val is not None and str(existing_val).strip() and not str_val:
                        warnings.append({
                            "localBizId": local_biz_id,
                            "fieldName": mid_f,
                            "currentValue": str(existing_val),
                            "newValue": None,
                        })
                        continue  # 跳过空值覆盖

                update_data[mid_f] = str_val

            if not existing:
                obj = mid_model(local_biz_id=local_biz_id, **update_data)
                self.db.add(obj)
            else:
                for k, v in update_data.items():
                    setattr(existing, k, v)
                existing.last_sync_time = datetime.now()

            sync_count += 1

            # 同步后执行字段生成规则
            if not existing or existing.group_id_generated != 1:
                self._apply_gen_rules(asset_type, local_biz_id)

        self.db.commit()
        self._log_operation("SYNC", asset_type, scope_type,
                            scope_ids[0] if scope_ids else None, "SUCCESS",
                            f"同步{sync_count}条")

        return {
            "totalCount": len(local_records),
            "syncCount": sync_count,
            "emptyOverwriteWarnings": warnings,
        }

    def _get_field_map(self, asset_type: str) -> Dict[str, str]:
        """获取本地→中间表字段映射（优先从配置表读取）"""
        configs = self.db.query(MetadataFieldMapping).filter(
            MetadataFieldMapping.asset_type == asset_type,
            MetadataFieldMapping.is_enabled == 1,
        ).all()
        if configs:
            return {c.local_field: c.mid_field for c in configs}
        return DEFAULT_FIELD_MAP.get(asset_type, {})

    def _apply_gen_rules(self, asset_type: str, local_biz_id: str):
        """应用字段生成规则"""
        rules = self.db.query(MidFieldGenRule).filter(
            MidFieldGenRule.asset_type == asset_type,
            MidFieldGenRule.is_enabled == 1,
        ).all()

        mid_model = LOCAL_MODEL_MAP[asset_type][1]
        obj = self.db.query(mid_model).filter(
            mid_model.local_biz_id == local_biz_id
        ).first()
        if not obj:
            return

        for rule in rules:
            current = getattr(obj, rule.target_field, None)
            if current is not None and str(current).strip():
                continue  # 已有值不覆盖

            value = self._eval_gen_rule(rule, obj)
            if value is not None:
                setattr(obj, rule.target_field, value)

    def _eval_gen_rule(self, rule: MidFieldGenRule, obj: Any) -> Optional[str]:
        """执行单条字段生成规则"""
        if rule.rule_type == "COPY":
            if rule.source_fields and len(rule.source_fields) > 0:
                src_val = getattr(obj, rule.source_fields[0], None)
                return str(src_val) if src_val is not None else None
            return None
        elif rule.rule_type == "ENUM_MAP":
            return "0"  # 湖外系统默认值
        elif rule.rule_type == "CONCAT":
            parts = []
            for sf in (rule.source_fields or []):
                parts.append(str(getattr(obj, sf, "")))
            return "-".join(parts) if rule.rule_expr else "".join(parts)
        elif rule.rule_type == "FORMULA":
            # 集团唯一标识生成
            if rule.target_field == "group_unique_id":
                from app.services.unique_id import generate_id
                gid = generate_id("GROUP", local_biz_id=obj.local_biz_id)
                obj.group_id_generated = 1
                return gid
        return None

    # ─── 2. 稽核中间表 ─────────────────────────────

    def audit_mid(
        self,
        asset_type: str,
        scope_type: str = "system",
        scope_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """对中间表记录执行稽核"""
        if asset_type not in LOCAL_MODEL_MAP:
            return {"totalCount": 0, "passCount": 0, "failCount": 0, "auditBatchId": ""}

        mid_model = LOCAL_MODEL_MAP[asset_type][1]

        query = self.db.query(mid_model).filter(
            mid_model.audit_status.in_(["pending", "fail"])
        )
        if scope_ids:
            if scope_type == "system" and asset_type != "system":
                # 按系统查子表
                parent_model = LOCAL_MODEL_MAP["system"][1]
                parents = self.db.query(parent_model).filter(
                    parent_model.local_biz_id.in_(scope_ids)
                ).all()
                parent_ids = set(p.local_biz_id for p in parents)
                # 查找关联的子记录
                fk_field = {"database": "sys_local_biz_id",
                            "table": "db_local_biz_id",
                            "field": "tbl_local_biz_id"}
                fk = fk_field.get(asset_type)
                if fk:
                    query = query.filter(getattr(mid_model, fk).in_(parent_ids))
            else:
                query = query.filter(mid_model.local_biz_id.in_(scope_ids))

        records = query.all()
        pass_count = 0
        fail_count = 0

        for rec in records:
            # 将中间表记录转为asset dict格式供稽核引擎使用
            asset_dict = {"asset_id": rec.local_biz_id}
            for col in mid_model.__table__.columns:
                asset_dict[col.name] = getattr(rec, col.name)

            rules = self.db.query(AuditRule).filter(
                AuditRule.target_asset.in_([asset_type, "全部"]),
                AuditRule.is_enabled == "是",
            ).all()

            reasons = []
            for rule in rules:
                # 简单稽核：非空/格式
                from app.services.audit_engine import _evaluate_single_rule
                is_pass, reason = _evaluate_single_rule(asset_dict, rule)
                if not is_pass:
                    reasons.append(f"[{rule.rule_code}]{reason}")

            joined = "；".join(reasons)
            rec.audit_status = "pass" if not reasons else "fail"
            rec.non_compliant_reason = joined
            rec.audit_time = datetime.now()

            if not reasons:
                pass_count += 1
            else:
                fail_count += 1

        self.db.commit()
        audit_batch_id = f"AUDIT-{datetime.now().strftime('%Y%m%d')}-{pass_count:03d}"
        self._log_operation("AUDIT", asset_type, scope_type,
                            scope_ids[0] if scope_ids else None,
                            "SUCCESS" if fail_count == 0 else "PARTIAL",
                            f"通过{pass_count}条，不通过{fail_count}条")

        return {
            "totalCount": len(records),
            "passCount": pass_count,
            "failCount": fail_count,
            "auditBatchId": audit_batch_id,
        }

    # ─── 3. 修改中间表 ─────────────────────────────

    def modify_mid(
        self,
        asset_type: str,
        local_biz_id: str,
        modify_fields: Dict[str, str],
        modify_reason: str,
    ) -> Dict[str, Any]:
        """修改中间表字段值，记录修改日志"""
        if asset_type not in LOCAL_MODEL_MAP:
            return {"modifyLogId": 0}

        mid_model = LOCAL_MODEL_MAP[asset_type][1]
        obj = self.db.query(mid_model).filter(
            mid_model.local_biz_id == local_biz_id
        ).first()
        if not obj:
            return {"modifyLogId": 0}

        log_id = None
        for field, new_val in modify_fields.items():
            if not hasattr(obj, field):
                continue
            old_val = getattr(obj, field)
            old_str = str(old_val) if old_val is not None else ""

            setattr(obj, field, new_val)

            log = MidFieldModifyLog(
                asset_type=asset_type,
                local_biz_id=local_biz_id,
                field_name=field,
                old_value=old_str,
                new_value=new_val,
                operator=self.operator,
                modify_reason=modify_reason,
            )
            self.db.add(log)
            self.db.flush()
            log_id = log.id

        obj.mid_modify_flag = 1
        obj.audit_status = "pending"  # 修改后重置稽核状态
        self.db.commit()

        self._log_operation("MID_MODIFY", asset_type, "single", local_biz_id,
                            "SUCCESS", f"修改{len(modify_fields)}个字段")

        return {"modifyLogId": log_id}

    # ─── 4. 同步到结果表 ─────────────────────────────

    def sync_to_result(
        self,
        asset_type: str,
        scope_type: str = "system",
        scope_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """将合规记录同步到结果表（需通过稽核审计+分级分类校验）"""
        if asset_type not in LOCAL_MODEL_MAP:
            return {"syncCount": 0, "skippedCount": 0}

        mid_model = LOCAL_MODEL_MAP[asset_type][1]

        query = self.db.query(mid_model).filter(mid_model.audit_status == "pass")
        if scope_ids:
            query = query.filter(mid_model.local_biz_id.in_(scope_ids))

        records = query.all()
        sync_count = 0
        skipped = 0

        for rec in records:
            # 检查分级分类状态：只同步分类有效的记录
            classify = self.db.query(ClassifyMid).filter(
                ClassifyMid.local_biz_id == rec.local_biz_id,
                ClassifyMid.asset_type == asset_type,
                ClassifyMid.classify_status == "valid",
            ).first()
            if not classify:
                skipped += 1
                continue
            # 检查是否已在结果表
            existing = self.db.query(UploadResultTable).filter(
                UploadResultTable.local_biz_id == rec.local_biz_id,
                UploadResultTable.asset_type == asset_type,
            ).first()

            # 构建数据快照
            snapshot = {}
            for col in mid_model.__table__.columns:
                val = getattr(rec, col.name)
                if val is not None:
                    snapshot[col.name] = str(val)

            import json
            if existing:
                existing.data_snapshot = json.dumps(snapshot, ensure_ascii=False)
                existing.sync_to_result_time = datetime.now()
            else:
                obj = UploadResultTable(
                    asset_type=asset_type,
                    local_biz_id=rec.local_biz_id,
                    group_unique_id=rec.group_unique_id,
                    data_snapshot=json.dumps(snapshot, ensure_ascii=False),
                    sync_to_result_time=datetime.now(),
                )
                self.db.add(obj)

            rec.upload_status = "synced"
            sync_count += 1

        self.db.commit()
        self._log_operation("SYNC_TO_RESULT", asset_type, scope_type,
                            scope_ids[0] if scope_ids else None, "SUCCESS",
                            f"同步{sync_count}条，跳过{skipped}条")

        return {"syncCount": sync_count, "skippedCount": skipped}

    # ─── 5. 上传集团 ─────────────────────────────

    def upload_to_group(
        self,
        asset_type: str,
        scope_type: str = "system",
        scope_ids: Optional[List[str]] = None,
        upload_mode: str = "all",
    ) -> Dict[str, Any]:
        """从结果表上传集团"""
        query = self.db.query(UploadResultTable).filter(
            UploadResultTable.asset_type == asset_type,
            UploadResultTable.upload_status == "pending",
        )
        if scope_ids:
            query = query.filter(UploadResultTable.local_biz_id.in_(scope_ids))

        records = query.all()
        batch_no = f"BATCH-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        success = 0
        fail = 0

        for rec in records:
            try:
                # 实际上传（当前仅标记状态）
                rec.upload_status = "uploaded"
                rec.upload_time = datetime.now()
                rec.upload_batch_no = batch_no
                success += 1
            except Exception:
                rec.upload_status = "failed"
                fail += 1

        self.db.commit()
        self._log_operation("UPLOAD", asset_type, scope_type,
                            scope_ids[0] if scope_ids else None,
                            "SUCCESS" if fail == 0 else "PARTIAL",
                            f"成功{success}条，失败{fail}条")

        return {"batchNo": batch_no, "successCount": success, "failCount": fail}

    # ─── 6. 查询方法 ─────────────────────────────

    def query_mid_list(
        self,
        asset_type: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        size: int = 10,
    ) -> Dict[str, Any]:
        """查询中间表数据"""
        if asset_type not in LOCAL_MODEL_MAP:
            return {"total": 0, "list": []}

        mid_model = LOCAL_MODEL_MAP[asset_type][1]
        query = self.db.query(mid_model)

        if filters:
            for field, val in filters.items():
                if val and hasattr(mid_model, field):
                    query = query.filter(getattr(mid_model, field).like(f"%{val}%"))

        total = query.count()
        items = query.offset((page - 1) * size).limit(size).all()

        result = []
        for item in items:
            d = {"localBizId": item.local_biz_id}
            for col in mid_model.__table__.columns:
                d[col.name] = getattr(item, col.name)
            result.append(d)

        return {"total": total, "list": result, "page": page, "size": size}

    def query_modify_log(
        self,
        asset_type: Optional[str] = None,
        local_biz_id: Optional[str] = None,
        operator: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        field_name: Optional[str] = None,
        page: int = 1,
        size: int = 10,
    ) -> Dict[str, Any]:
        """查询修改日志"""
        query = self.db.query(MidFieldModifyLog)
        if asset_type:
            query = query.filter(MidFieldModifyLog.asset_type == asset_type)
        if local_biz_id:
            query = query.filter(MidFieldModifyLog.local_biz_id == local_biz_id)
        if operator:
            query = query.filter(MidFieldModifyLog.operator.like(f"%{operator}%"))
        if field_name:
            query = query.filter(MidFieldModifyLog.field_name == field_name)

        total = query.count()
        items = query.order_by(MidFieldModifyLog.modify_time.desc()).offset(
            (page - 1) * size).limit(size).all()

        rows = []
        for i in items:
            rows.append({
                "logId": i.id,
                "assetType": i.asset_type,
                "localBizId": i.local_biz_id,
                "fieldName": i.field_name,
                "oldValue": i.old_value,
                "newValue": i.new_value,
                "operator": i.operator,
                "modifyTime": str(i.modify_time) if i.modify_time else None,
                "modifyReason": i.modify_reason,
            })

        return {"total": total, "list": rows, "page": page, "size": size}

    def query_upload_log(
        self,
        asset_type: Optional[str] = None,
        batch_no: Optional[str] = None,
        operator: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        upload_status: Optional[str] = None,
        page: int = 1,
        size: int = 10,
    ) -> Dict[str, Any]:
        """查询上传日志"""
        query = self.db.query(UploadOperationLog).filter(
            UploadOperationLog.operation_type == "UPLOAD"
        )
        if asset_type:
            query = query.filter(UploadOperationLog.asset_type == asset_type)
        if operator:
            query = query.filter(UploadOperationLog.operator.like(f"%{operator}%"))

        total = query.count()
        items = query.order_by(UploadOperationLog.operate_time.desc()).offset(
            (page - 1) * size).limit(size).all()

        rows = []
        for i in items:
            rows.append({
                "batchNo": i.scope_id,
                "uploadTime": str(i.operate_time) if i.operate_time else None,
                "operator": i.operator,
                "assetType": i.asset_type,
                "scopeDesc": i.operation_detail,
                "successCount": 0,
                "failCount": 0,
                "uploadStatus": i.result,
            })

        return {"total": total, "list": rows, "page": page, "size": size}

    # ─── 内部方法 ─────────────────────────────

    def _log_operation(
        self, op_type: str, asset_type: str,
        scope_type: str, scope_id: Optional[str],
        result: str, result_msg: str,
    ):
        """记录操作日志"""
        log = UploadOperationLog(
            operation_type=op_type,
            asset_type=asset_type,
            scope_type=scope_type,
            scope_id=scope_id or "",
            operator=self.operator,
            operation_detail=result_msg,
            result=result,
            result_msg=result_msg,
        )
        self.db.add(log)
        self.db.flush()
