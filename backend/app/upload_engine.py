"""集团上报流程引擎（增强版 V2）"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.asset import (
    UploadResourceSystem, UploadResourceDatabase, UploadResourceTable, UploadResourceField,
    AuditRule,
)
from app.models.upload_mid import (
    UploadMidSystem, UploadMidDatabase, UploadMidTable, UploadMidField,
    MidFieldGenRule, MetadataFieldMapping, MidFieldModifyLog,
    UploadOperationLog, UploadResultTable, UploadResultMid, UploadGroupResult,
    ExcludeMark, MergeLog, SyncDefaultValue, ClassifyMid,
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

# 中间表模型映射
MID_MODEL_MAP = {
    "system": UploadMidSystem,
    "database": UploadMidDatabase,
    "table": UploadMidTable,
    "field": UploadMidField,
}

ASSET_LEVELS = ["system", "database", "table", "field"]

# 层级父级字段映射（当前层 → 直接父层）
PARENT_FK_MAP = {
    "database": "sys_local_biz_id",
    "table": "db_local_biz_id",
    "field": "tbl_local_biz_id",
}

OPER_TYPE_NEW = "0"       # 新增
OPER_TYPE_MODIFY = "1"    # 修改
OPER_TYPE_DELETE = "2"    # 删除


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
        sync_type: str = "full",
    ) -> Dict[str, Any]:
        """同步本地元数据到中间表（UPSERT）
        sync_type: full=全量, incremental=仅增量
        """
        if asset_type not in LOCAL_MODEL_MAP:
            return {"totalCount": 0, "syncCount": 0, "emptyOverwriteWarnings": []}

        local_model, mid_model, id_field = LOCAL_MODEL_MAP[asset_type]
        field_map = self._get_field_map(asset_type)
        default_values = self._get_default_values(asset_type)

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

            # 检测操作类型
            if sync_type == "incremental":
                if existing:
                    op_type = self._detect_oper_type(existing, rec, field_map)
                else:
                    op_type = OPER_TYPE_NEW
                if op_type == OPER_TYPE_DELETE:
                    # 标记删除
                    existing.oper_type = OPER_TYPE_DELETE
                    existing.oper_time = datetime.now().strftime("%Y%m%d%H%M%S")
                    self.db.flush()
                    continue

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

            # 应用默认值（空值使用默认值填充）
            if not existing:
                for field, def_val in default_values.items():
                    if field not in update_data or not update_data.get(field):
                        update_data[field] = def_val

            if not existing:
                if sync_type == "incremental":
                    update_data["oper_type"] = OPER_TYPE_NEW
                    update_data["oper_time"] = datetime.now().strftime("%Y%m%d%H%M%S")
                obj = mid_model(local_biz_id=local_biz_id, **update_data)
                self.db.add(obj)
            else:
                for k, v in update_data.items():
                    setattr(existing, k, v)
                if sync_type == "incremental":
                    existing.oper_type = OPER_TYPE_MODIFY
                existing.last_sync_time = datetime.now()

            sync_count += 1

            # 同步后执行字段生成规则（生成集团唯一标识等）
            if not existing or existing.group_id_generated != 1:
                self._apply_gen_rules(asset_type, local_biz_id)

            # 生成数据库/表/字段的集团唯一标识
            if not existing or not existing.group_unique_id:
                self._generate_group_unique_id(asset_type, local_biz_id, update_data)

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
        cascade: bool = False,
    ) -> Dict[str, Any]:
        """对中间表记录执行稽核
        cascade=True: 按系统级联稽核（系统+所有下级）
        """
        if asset_type not in LOCAL_MODEL_MAP:
            return {"totalCount": 0, "passCount": 0, "failCount": 0, "auditBatchId": ""}

        if asset_type == "system" and cascade:
            return self._audit_system_cascade(scope_ids)

        mid_model = LOCAL_MODEL_MAP[asset_type][1]

        query = self.db.query(mid_model).filter(
            mid_model.audit_status.in_(["pending", "fail"])
        )
        if scope_ids:
            if scope_type == "system" and asset_type != "system":
                parent_model = LOCAL_MODEL_MAP["system"][1]
                parents = self.db.query(parent_model).filter(
                    parent_model.local_biz_id.in_(scope_ids)
                ).all()
                parent_ids = set(p.local_biz_id for p in parents)
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
            asset_dict = {"asset_id": rec.local_biz_id}
            for col in mid_model.__table__.columns:
                asset_dict[col.name] = getattr(rec, col.name)

            rules = self.db.query(AuditRule).filter(
                AuditRule.target_asset.in_([asset_type, "全部"]),
                AuditRule.is_enabled == "是",
            ).all()

            reasons = []
            for rule in rules:
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

    def _audit_system_cascade(self, sys_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """级联稽核：先稽核系统，再逐级稽核数据库→表→字段"""
        mid_system = LOCAL_MODEL_MAP["system"][1]
        sys_query = self.db.query(mid_system).filter(
            mid_system.audit_status.in_(["pending", "fail"])
        )
        if sys_ids:
            sys_query = sys_query.filter(mid_system.local_biz_id.in_(sys_ids))
        systems = sys_query.all()

        total = {"system": {"pass": 0, "fail": 0}, "database": {"pass": 0, "fail": 0},
                  "table": {"pass": 0, "fail": 0}, "field": {"pass": 0, "fail": 0}}
        child_levels = ["database", "table", "field"]
        child_fks = ["sys_local_biz_id", "db_local_biz_id", "tbl_local_biz_id"]

        for sys_rec in systems:
            # 稽核系统本身
            sys_pass = self._audit_single_record("system", sys_rec)
            if sys_pass:
                total["system"]["pass"] += 1
            else:
                total["system"]["fail"] += 1

            # 级联稽核下级
            current_ids = [sys_rec.local_biz_id]
            all_pass = sys_pass
            for i, level in enumerate(child_levels):
                mid_model = LOCAL_MODEL_MAP[level][1]
                children = self.db.query(mid_model).filter(
                    getattr(mid_model, child_fks[i]).in_(current_ids)
                ).all()
                next_ids = []
                for child in children:
                    child_pass = self._audit_single_record(level, child)
                    if child_pass:
                        total[level]["pass"] += 1
                    else:
                        total[level]["fail"] += 1
                        all_pass = False
                    next_ids.append(child.local_biz_id)
                current_ids = next_ids
                if not current_ids:
                    break

            # 如果系统本身通过但下级有不通过，系统状态不改变
            # 系统级状态反映其自身稽核结果

        self.db.commit()
        result = {
            "totalCount": sum(v["pass"] + v["fail"] for v in total.values()),
            "passCount": total["system"]["pass"],
            "failCount": total["system"]["fail"],
            "detail": total,
            "cascade": True,
        }
        self._log_operation("AUDIT_CASCADE", "all", "system",
                            sys_ids[0] if sys_ids else None,
                            "SUCCESS" if total["system"]["fail"] == 0 else "PARTIAL",
                            f"系统通过{total['system']['pass']}个, 数据库通过{total['database']['pass']}个, "
                            f"表通过{total['table']['pass']}个, 字段通过{total['field']['pass']}个")
        return result

    def _audit_single_record(self, asset_type: str, rec) -> bool:
        """稽核单条中间表记录，返回是否通过"""
        mid_model = LOCAL_MODEL_MAP[asset_type][1]
        asset_dict = {"asset_id": rec.local_biz_id}
        for col in mid_model.__table__.columns:
            asset_dict[col.name] = getattr(rec, col.name)

        rules = self.db.query(AuditRule).filter(
            AuditRule.target_asset.in_([asset_type, "全部"]),
            AuditRule.is_enabled == "是",
        ).all()

        reasons = []
        for rule in rules:
            from app.services.audit_engine import _evaluate_single_rule
            is_pass, reason = _evaluate_single_rule(asset_dict, rule)
            if not is_pass:
                reasons.append(f"[{rule.rule_code}]{reason}")

        joined = "；".join(reasons)
        rec.audit_status = "pass" if not reasons else "fail"
        rec.non_compliant_reason = joined
        rec.audit_time = datetime.now()
        return not bool(reasons)

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

    # ─── 6. 同步到中间结果表（带账期） ─────────────

    def sync_to_result_mid(
        self,
        asset_type: str,
        scope_type: str = "system",
        scope_ids: Optional[List[str]] = None,
        bill_month: Optional[str] = None,
    ) -> Dict[str, Any]:
        """将合规记录同步到中间结果表（带账期）"""
        if asset_type not in LOCAL_MODEL_MAP:
            return {"syncCount": 0, "skippedCount": 0, "mergeSuggestions": []}

        mid_model = LOCAL_MODEL_MAP[asset_type][1]
        bill_month = bill_month or self._calc_bill_month()

        query = self.db.query(mid_model).filter(
            mid_model.audit_status == "pass",
        )
        # UploadMidField 没有 upload_flag 字段，需防错
        if hasattr(mid_model, "upload_flag"):
            query = query.filter(mid_model.upload_flag == "1")
        if scope_ids:
            query = query.filter(mid_model.local_biz_id.in_(scope_ids))
        records = query.all()

        sync_count = 0
        skipped = 0
        merge_suggestions = []

        for rec in records:
            # 跳过未通过稽核的
            if rec.audit_status != "pass":
                skipped += 1
                continue

            # 构建快照
            snapshot = {}
            for col in mid_model.__table__.columns:
                val = getattr(rec, col.name)
                if val is not None:
                    snapshot[col.name] = str(val)

            # UPSERT到中间结果表
            existing = self.db.query(UploadResultMid).filter(
                UploadResultMid.asset_type == asset_type,
                UploadResultMid.mid_local_biz_id == rec.local_biz_id,
                UploadResultMid.bill_month == bill_month,
            ).first()

            if existing:
                existing.data_snapshot = json.dumps(snapshot, ensure_ascii=False)
                existing.sync_time = datetime.now()
                existing.audit_status = rec.audit_status
            else:
                obj = UploadResultMid(
                    asset_type=asset_type,
                    mid_local_biz_id=rec.local_biz_id,
                    group_unique_id=rec.group_unique_id,
                    bill_month=bill_month,
                    data_snapshot=json.dumps(snapshot, ensure_ascii=False),
                    sync_time=datetime.now(),
                    audit_status=rec.audit_status,
                    oper_type=rec.oper_type or OPER_TYPE_NEW,
                )
                self.db.add(obj)

            rec.upload_status = "synced"
            sync_count += 1

        # 检测合并建议（仅系统级别）
        if asset_type == "system":
            merge_suggestions = self._check_merge_suggestions(bill_month)

        self.db.commit()
        self._log_operation("SYNC_TO_RESULT_MID", asset_type, scope_type,
                            scope_ids[0] if scope_ids else None, "SUCCESS",
                            f"同步{sync_count}条到中间结果表[{bill_month}]")

        return {
            "syncCount": sync_count,
            "skippedCount": skipped,
            "billMonth": bill_month,
            "mergeSuggestions": merge_suggestions,
        }

    # ─── 7. 确认上传到集团结果表 ─────────────────

    def confirm_upload(
        self,
        asset_type: str,
        scope_type: str = "system",
        scope_ids: Optional[List[str]] = None,
        bill_month: Optional[str] = None,
        cascade: bool = False,
    ) -> Dict[str, Any]:
        """从中间结果表确认上传到集团结果表（全量无账期）
        cascade=True 时，上传系统级联上传其下所有库/表/字段
        """
        bill_month = bill_month or self._calc_bill_month()

        # 收集本级别的记录
        query = self.db.query(UploadResultMid).filter(
            UploadResultMid.asset_type == asset_type,
            UploadResultMid.bill_month == bill_month,
            UploadResultMid.result_status.in_(["pending", "audited"]),
            UploadResultMid.audit_status == "pass",
        )
        if scope_ids:
            query = query.filter(UploadResultMid.id.in_(scope_ids))
        records = list(query.all())

        # 级联：如果上传系统，同时上传其下所有库/表/字段
        if cascade and asset_type == "system":
            # 获取所选系统的 local_biz_id
            sys_local_ids = set()
            for r in records:
                sys_local_ids.add(r.mid_local_biz_id)
            if not sys_local_ids and scope_ids:
                sys_recs = self.db.query(UploadResultMid.mid_local_biz_id).filter(
                    UploadResultMid.id.in_(scope_ids),
                    UploadResultMid.asset_type == "system",
                ).all()
                sys_local_ids = {s[0] for s in sys_recs}

            if sys_local_ids:
                # 查库 → 表 → 字段 的 local_biz_id
                db_recs = self.db.query(UploadMidDatabase.local_biz_id).filter(
                    UploadMidDatabase.sys_local_biz_id.in_(sys_local_ids)).all()
                db_ids = {d[0] for d in db_recs}
                tbl_recs = self.db.query(UploadMidTable.local_biz_id).filter(
                    UploadMidTable.db_local_biz_id.in_(db_ids)).all()
                tbl_ids = {t[0] for t in tbl_recs}
                fld_recs = self.db.query(UploadMidField.local_biz_id).filter(
                    UploadMidField.tbl_local_biz_id.in_(tbl_ids)).all()
                fld_ids = {f[0] for f in fld_recs}

                all_child_ids = db_ids | tbl_ids | fld_ids
                child_records = self.db.query(UploadResultMid).filter(
                    UploadResultMid.bill_month == bill_month,
                    UploadResultMid.result_status.in_(["pending", "audited"]),
                    UploadResultMid.audit_status == "pass",
                    UploadResultMid.mid_local_biz_id.in_(all_child_ids),
                ).all()
                records.extend(child_records)

        success = 0
        skipped = 0

        now = datetime.now()
        for rec in records:
            if rec.audit_status != "pass":
                skipped += 1
                continue

            # UPSERT到集团结果表
            existing = self.db.query(UploadGroupResult).filter(
                UploadGroupResult.group_unique_id == rec.group_unique_id,
            ).first()

            if existing:
                existing.data_snapshot = rec.data_snapshot
                existing.sync_time = now
                existing.oper_type = OPER_TYPE_MODIFY
                existing.oper_time = now.strftime("%Y%m%d%H%M%S")
                existing.bill_month = rec.bill_month
            else:
                obj = UploadGroupResult(
                    asset_type=rec.asset_type,
                    group_unique_id=rec.group_unique_id,
                    bill_month=rec.bill_month,
                    data_snapshot=rec.data_snapshot,
                    sync_time=now,
                    oper_type=OPER_TYPE_NEW,
                    oper_time=now.strftime("%Y%m%d%H%M%S"),
                )
                self.db.add(obj)

            rec.result_status = "uploaded"
            rec.upload_time = now
            success += 1

        self.db.commit()
        asset_desc = f"{asset_type}+下级" if cascade else asset_type
        self._log_operation("CONFIRM_UPLOAD", asset_desc, scope_type,
                            scope_ids[0] if scope_ids else None, "SUCCESS",
                            f"上传{success}条到集团结果表，跳过{skipped}条")

        return {"successCount": success, "skippedCount": skipped, "billMonth": bill_month}

    # ─── 8. 从集团结果表删除 ─────────────────────

    def delete_from_group_result(
        self,
        asset_type: str,
        biz_id: str,
    ) -> Dict[str, Any]:
        """删除集团结果表记录，回退中间结果表状态
        asset_type: system 或 database
        biz_id: 对应的 local_biz_id（从级联筛选获得），也支持传入 group_unique_id
        """
        # 如果传入的是 group_unique_id，先解析为 local_biz_id
        resolved_biz_id = biz_id
        if biz_id.startswith("JT-SYS-"):
            # 查找对应系统的 local_biz_id
            sys_rec = self.db.query(UploadMidSystem.local_biz_id).filter(
                UploadMidSystem.group_unique_id == biz_id).first()
            if sys_rec:
                resolved_biz_id = sys_rec[0]
                asset_type = "system"
            else:
                return {"deletedCount": 0, "updatedCount": 0, "reason": "未找到对应系统记录"}
        elif biz_id.count("-") >= 2 and not biz_id.startswith("CQ-"):
            # 可能是 database 的 group_unique_id
            db_rec = self.db.query(UploadMidDatabase.local_biz_id).filter(
                UploadMidDatabase.group_unique_id == biz_id).first()
            if db_rec:
                resolved_biz_id = db_rec[0]
                asset_type = "database"

        # 收集所有需要处理的 local_biz_id（级联下级）
        all_ids = {resolved_biz_id}

        if asset_type == "system":
            dbs = self.db.query(UploadMidDatabase.local_biz_id).filter(
                UploadMidDatabase.sys_local_biz_id == biz_id).all()
            db_ids = {d[0] for d in dbs}
            all_ids.update(db_ids)
            for did in db_ids:
                tbls = self.db.query(UploadMidTable.local_biz_id).filter(
                    UploadMidTable.db_local_biz_id == did).all()
                tbl_ids = {t[0] for t in tbls}
                all_ids.update(tbl_ids)
                for tid in tbl_ids:
                    flds = self.db.query(UploadMidField.local_biz_id).filter(
                        UploadMidField.tbl_local_biz_id == tid).all()
                    all_ids.update({f[0] for f in flds})
        elif asset_type == "database":
            tbls = self.db.query(UploadMidTable.local_biz_id).filter(
                UploadMidTable.db_local_biz_id == biz_id).all()
            tbl_ids = {t[0] for t in tbls}
            all_ids.update(tbl_ids)
            for tid in tbl_ids:
                flds = self.db.query(UploadMidField.local_biz_id).filter(
                    UploadMidField.tbl_local_biz_id == tid).all()
                all_ids.update({f[0] for f in flds})
        else:
            return {"deletedCount": 0, "updatedCount": 0, "reason": "不支持的资产类型，仅支持 system/database"}

        # 从 mid 表找到对应的 group_unique_id
        group_ids = set()
        type_map = {
            "system": UploadMidSystem,
            "database": UploadMidDatabase,
            "table": UploadMidTable,
            "field": UploadMidField,
        }
        for at, mdl in type_map.items():
            records = self.db.query(mdl.group_unique_id).filter(
                mdl.local_biz_id.in_(all_ids)).all()
            group_ids.update({r[0] for r in records if r[0]})

        if not group_ids:
            return {"deletedCount": 0, "updatedCount": 0, "reason": "未找到对应记录"}

        # 删除 UploadGroupResult 记录
        deleted = self.db.query(UploadGroupResult).filter(
            UploadGroupResult.group_unique_id.in_(group_ids)).delete(synchronize_session=False)

        # 更新 UploadResultMid 状态（已上传→未上传）
        updated = self.db.query(UploadResultMid).filter(
            UploadResultMid.group_unique_id.in_(group_ids),
            UploadResultMid.result_status == "uploaded",
        ).update({"result_status": "pending"}, synchronize_session=False)

        self.db.commit()
        self._log_operation("DELETE_FROM_GROUP", asset_type, "single", biz_id,
                            "SUCCESS",
                            f"删除{deleted}条集团结果表，回退{updated}条中间结果表状态")

        return {"deletedCount": deleted, "updatedCount": updated}

    # ─── 9. 标记是否上传 ─────────────────────────

    def mark_upload_flag(
        self,
        asset_type: str,
        asset_id: str,
        exclude_flag: bool = True,
        reason: str = "",
    ) -> Dict[str, Any]:
        """标记中间表的库/表是否上传
        exclude_flag: True=不上传, False=恢复上传
        """
        if asset_type not in MID_MODEL_MAP:
            return {"success": False, "reason": "不支持的资产类型"}

        mid_model = MID_MODEL_MAP[asset_type]
        record = self.db.query(mid_model).filter(
            mid_model.local_biz_id == asset_id
        ).first()
        if not record:
            return {"success": False, "reason": "记录不存在"}

        record.upload_flag = "0" if exclude_flag else "1"

        # 获取系统信息
        sys_name = ""
        sys_id = ""
        asset_name = ""
        if hasattr(record, "sys_local_biz_id") and record.sys_local_biz_id:
            sys_rec = self.db.query(UploadMidSystem).filter(
                UploadMidSystem.local_biz_id == record.sys_local_biz_id
            ).first()
            if sys_rec:
                sys_name = sys_rec.sys_name or ""
                sys_id = sys_rec.local_biz_id or ""
        if asset_type == "database":
            asset_name = record.db_name or ""
        elif asset_type == "table":
            asset_name = record.table_name or record.table_name_en or ""

        if exclude_flag:
            mark = ExcludeMark(
                asset_type=asset_type,
                asset_id=asset_id,
                asset_name=asset_name,
                sys_id=sys_id,
                sys_name=sys_name,
                exclude_reason=reason,
                operator=self.operator,
            )
            self.db.add(mark)
            self._log_operation("MARK_EXCLUDE", asset_type, "single", asset_id,
                                "SUCCESS", f"标记不上传: {asset_name}")
        else:
            self.db.query(ExcludeMark).filter(
                ExcludeMark.asset_type == asset_type,
                ExcludeMark.asset_id == asset_id,
            ).delete()
            self._log_operation("UNMARK_EXCLUDE", asset_type, "single", asset_id,
                                "SUCCESS", f"恢复上传: {asset_name}")

        self.db.commit()
        return {"success": True, "uploadFlag": record.upload_flag}

    # ─── 9. 合并记录 ───────────────────────────────

    def merge_records(
        self,
        asset_type: str,
        source_ids: List[str],
        target_id: str,
        bill_month: Optional[str] = None,
    ) -> Dict[str, Any]:
        """合并定级备案名称重复的记录"""
        if asset_type not in MID_MODEL_MAP:
            return {"merged": False, "reason": "不支持的资产类型"}

        bill_month = bill_month or self._calc_bill_month()
        mid_model = MID_MODEL_MAP[asset_type]
        result_model = UploadResultMid

        # 获取目标记录
        target = self.db.query(result_model).filter(
            result_model.mid_local_biz_id == target_id,
            result_model.bill_month == bill_month,
        ).first()
        if not target:
            return {"merged": False, "reason": "目标记录不存在"}

        merge_detail = {"fields": {}}

        for src_id in source_ids:
            if src_id == target_id:
                continue
            source = self.db.query(result_model).filter(
                result_model.mid_local_biz_id == src_id,
                result_model.bill_month == bill_month,
            ).first()
            if not source:
                continue

            # 合并字段（源非空覆盖目标空值）
            src_snapshot = json.loads(source.data_snapshot or "{}")
            tgt_snapshot = json.loads(target.data_snapshot or "{}")
            for key, val in src_snapshot.items():
                if val and (key not in tgt_snapshot or not tgt_snapshot.get(key)):
                    tgt_snapshot[key] = val
                    merge_detail["fields"][key] = {"from": src_id, "value": str(val)}
            target.data_snapshot = json.dumps(tgt_snapshot, ensure_ascii=False)

            # 标记源记录为已合并
            source.result_status = "merged"
            source.merge_flag = 1

            # 重定向子记录
            if asset_type == "system":
                # 将下级数据库的归属改到目标系统
                self.db.query(UploadMidDatabase).filter(
                    UploadMidDatabase.sys_local_biz_id == src_id
                ).update({"sys_local_biz_id": target_id})
                merge_detail.setdefault("children_reparented", []).append(f"db:{src_id}->{target_id}")

        target.merge_flag = 1

        # 记录合并日志
        log = MergeLog(
            asset_type=asset_type,
            target_local_biz_id=target_id,
            source_local_biz_ids=json.dumps(source_ids),
            merge_reason="定级备案名称匹配合并",
            merge_detail=json.dumps(merge_detail, ensure_ascii=False),
            operator=self.operator,
        )
        self.db.add(log)
        self.db.flush()
        log_id = log.id

        self.db.commit()
        self._log_operation("MERGE", asset_type, "multi", target_id,
                            "SUCCESS", f"合并{len(source_ids)}条记录到{target_id}")

        return {"merged": True, "mergeLogId": log_id, "mergeDetail": merge_detail}

    # ─── 10. 工具方法 ────────────────────────────

    @staticmethod
    def _calc_bill_month() -> str:
        """计算当前账期：上月26日至本月25日"""
        from datetime import date
        today = date.today()
        if today.day >= 26:
            # 本月26日之后 → 下月账期
            y, m = today.year, today.month
            if m == 12:
                return f"{y + 1}01"
            return f"{y}{str(m + 1).zfill(2)}"
        else:
            # 本月25日之前 → 本月账期
            return f"{today.year}{str(today.month).zfill(2)}"

    def _get_default_values(self, asset_type: str) -> Dict[str, str]:
        """获取同步默认值配置"""
        configs = self.db.query(SyncDefaultValue).filter(
            SyncDefaultValue.asset_type == asset_type,
            SyncDefaultValue.is_enabled == 1,
        ).all()
        return {c.field_name: c.default_value for c in configs}

    def _detect_oper_type(self, existing: Any, local_rec: Any, field_map: Dict[str, str]) -> str:
        """比对元数据与中间表，确定操作类型"""
        if existing.oper_type == OPER_TYPE_DELETE:
            # 之前标记删除的如果重新出现，视为新增
            return OPER_TYPE_NEW

        # 检查是否有字段变更
        for local_f, mid_f in field_map.items():
            local_val = str(getattr(local_rec, local_f, "") or "")
            mid_val = str(getattr(existing, mid_f, "") or "")
            if local_val != mid_val:
                return OPER_TYPE_MODIFY

        return OPER_TYPE_MODIFY  # 默认按修改处理

    def _generate_group_unique_id(self, asset_type: str, local_biz_id: str, update_data: Dict[str, str]):
        """生成集团唯一标识
        数据库: sys_code + db_name + db_type + IP + port
        表/字段: 基于层级关系生成
        """
        mid_model = LOCAL_MODEL_MAP[asset_type][1]
        obj = self.db.query(mid_model).filter(
            mid_model.local_biz_id == local_biz_id
        ).first()
        if not obj or obj.group_unique_id:
            return

        if asset_type == "database":
            sys_code = (obj.sys_code or update_data.get("sys_code") or "")
            db_name = (obj.db_name or update_data.get("db_name") or "")
            db_type = (obj.db_type or update_data.get("db_type") or "")
            db_ip = (obj.db_ip or update_data.get("db_ip") or "")
            db_port = (obj.db_port or update_data.get("db_port") or "")
            unique_id = f"{sys_code}-{db_name}-{db_type}-{db_ip}-{db_port}"
            obj.group_unique_id = unique_id
            obj.group_id_generated = 1
        elif asset_type == "table":
            # 查找上级库的group_unique_id
            parent = self.db.query(UploadMidDatabase).filter(
                UploadMidDatabase.local_biz_id == obj.db_local_biz_id
            ).first()
            prefix = parent.group_unique_id if parent and parent.group_unique_id else (obj.db_local_biz_id or "")
            tbl_name = obj.table_name_en or update_data.get("table_name_en") or ""
            obj.group_unique_id = f"{prefix}-TBL-{tbl_name}"
            obj.group_id_generated = 1
        elif asset_type == "field":
            parent = self.db.query(UploadMidTable).filter(
                UploadMidTable.local_biz_id == obj.tbl_local_biz_id
            ).first()
            prefix = parent.group_unique_id if parent and parent.group_unique_id else (obj.tbl_local_biz_id or "")
            fld_name = obj.field_name_en or update_data.get("field_name_en") or ""
            obj.group_unique_id = f"{prefix}-FLD-{fld_name}"
            obj.group_id_generated = 1

    def _check_merge_suggestions(self, bill_month: str) -> List[Dict[str, Any]]:
        """检测中间结果表中定级备案名称重复的系统"""
        result_model = UploadResultMid

        # 查询所有已同步的系统记录
        systems = self.db.query(result_model).filter(
            result_model.asset_type == "system",
            result_model.bill_month == bill_month,
            result_model.result_status != "merged",
        ).all()

        # 解析快照中的 record_name
        name_map = {}
        for sys_rec in systems:
            snapshot = json.loads(sys_rec.data_snapshot or "{}")
            record_name = snapshot.get("record_name", "")
            if record_name:
                name_map.setdefault(record_name, []).append(sys_rec)

        suggestions = []
        for name, recs in name_map.items():
            if len(recs) > 1:
                suggestions.append({
                    "recordName": name,
                    "ids": [r.mid_local_biz_id for r in recs],
                    "count": len(recs),
                })
        return suggestions

    # ─── 11. 新查询方法 ──────────────────────────

    def query_result_mid_list(
        self,
        asset_type: Optional[str] = None,
        bill_month: Optional[str] = None,
        result_status: Optional[str] = None,
        group_unique_id: Optional[str] = None,
        mid_local_biz_id: Optional[str] = None,
        parent_local_biz_id: Optional[str] = None,
        page: int = 1,
        size: int = 10,
    ) -> Dict[str, Any]:
        """查询中间结果表数据（支持下钻过滤+级联精确过滤 - v2）"""
        query = self.db.query(UploadResultMid)
        if asset_type:
            query = query.filter(UploadResultMid.asset_type == asset_type)
        if bill_month:
            query = query.filter(UploadResultMid.bill_month == bill_month)
        if result_status:
            query = query.filter(UploadResultMid.result_status == result_status)
        if group_unique_id:
            query = query.filter(UploadResultMid.group_unique_id.like(f"%{group_unique_id}%"))
        if mid_local_biz_id:
            # 按 mid_local_biz_id 精确过滤（级联选择当前层级时使用）
            import logging
            logging.warning(f"MID_LOCAL_BIZ_ID FILTER: mid_local_biz_id={mid_local_biz_id}, asset_type={asset_type}")
            query = query.filter(UploadResultMid.mid_local_biz_id == mid_local_biz_id)
        if parent_local_biz_id and asset_type and not mid_local_biz_id:
            # 下钻过滤：根据父级 ID 查找子级记录
            child_ids = self._get_child_ids_for_result(asset_type, parent_local_biz_id)
            if child_ids:
                query = query.filter(UploadResultMid.mid_local_biz_id.in_(child_ids))
            else:
                query = query.filter(text("1=0"))

        total = query.count()
        items = query.order_by(UploadResultMid.sync_time.desc()).offset(
            (page - 1) * size).limit(size).all()

        rows = []
        for i in items:
            row = {
                "id": i.id,
                "assetType": i.asset_type,
                "midLocalBizId": i.mid_local_biz_id,
                "groupUniqueId": i.group_unique_id,
                "billMonth": i.bill_month,
                "resultStatus": i.result_status,
                "auditStatus": i.audit_status,
                "nonCompliantReason": i.non_compliant_reason,
                "mergeFlag": i.merge_flag,
                "syncTime": str(i.sync_time) if i.sync_time else None,
                "uploadTime": str(i.upload_time) if i.upload_time else None,
            }

            # 从 data_snapshot 解析字段数据（包含所有 mid-table 字段）
            try:
                if i.data_snapshot:
                    snap = json.loads(i.data_snapshot) if isinstance(i.data_snapshot, str) else i.data_snapshot
                    for snap_key, snap_val in snap.items():
                        if snap_key not in ("id", "local_biz_id", "mid_local_biz_id", "data_snapshot"):
                            row[snap_key] = snap_val
            except Exception:
                pass

            # 补充父级名称（使用正确的 data_snapshot key 名）
            row["sysName"] = ""
            row["dbName"] = ""
            row["tableName"] = ""
            if i.asset_type == "database":
                sys_local_biz_id = row.get("sys_local_biz_id", "")
                if sys_local_biz_id:
                    p = self.db.query(UploadMidSystem.sys_name).filter(UploadMidSystem.local_biz_id == sys_local_biz_id).first()
                    row["sysName"] = p[0] if p else ""
            elif i.asset_type == "table":
                db_local_biz_id = row.get("db_local_biz_id", "")
                if db_local_biz_id:
                    p = self.db.query(UploadMidDatabase.db_name, UploadMidDatabase.sys_local_biz_id).filter(
                        UploadMidDatabase.local_biz_id == db_local_biz_id).first()
                    if p:
                        row["dbName"] = p[0] or ""
                        sys_id = p[1] or ""
                        if sys_id:
                            sp = self.db.query(UploadMidSystem.sys_name).filter(
                                UploadMidSystem.local_biz_id == sys_id).first()
                            row["sysName"] = sp[0] if sp else ""
            elif i.asset_type == "field":
                tbl_local_biz_id = row.get("tbl_local_biz_id", "")
                if tbl_local_biz_id:
                    p = self.db.query(UploadMidTable.table_name, UploadMidTable.db_local_biz_id).filter(
                        UploadMidTable.local_biz_id == tbl_local_biz_id).first()
                    if p:
                        row["tableName"] = p[0] or ""
                        db_id = p[1] or ""
                        if db_id:
                            dp = self.db.query(UploadMidDatabase.db_name, UploadMidDatabase.sys_local_biz_id).filter(
                                UploadMidDatabase.local_biz_id == db_id).first()
                            if dp:
                                row["dbName"] = dp[0] or ""
                                sys_id = dp[1] or ""
                                if sys_id:
                                    sp = self.db.query(UploadMidSystem.sys_name).filter(
                                        UploadMidSystem.local_biz_id == sys_id).first()
                                    row["sysName"] = sp[0] if sp else ""

            rows.append(row)

        return {"total": total, "list": rows, "page": page, "size": size}

    def _get_child_ids_for_result(self, asset_type: str, parent_local_biz_id: str) -> List[str]:
        """查找指定父级下所有子级的 local_biz_id（用于结果表下钻）"""
        level_idx = ASSET_LEVELS.index(asset_type)
        if level_idx <= 0:
            return []

        parent_level = ASSET_LEVELS[level_idx - 1]
        fk = PARENT_FK_MAP.get(asset_type)
        mid_model = MID_MODEL_MAP.get(asset_type)
        if not fk or not mid_model:
            return []

        # 查找该父级下的子记录
        children = self.db.query(mid_model.local_biz_id).filter(
            getattr(mid_model, fk) == parent_local_biz_id
        ).all()
        return [c[0] for c in children]

    def query_group_result_list(
        self,
        asset_type: Optional[str] = None,
        group_unique_id: Optional[str] = None,
        bill_month: Optional[str] = None,
        page: int = 1,
        size: int = 10,
    ) -> Dict[str, Any]:
        """查询集团结果表数据（只读，支持账期过滤）"""
        query = self.db.query(UploadGroupResult)
        if asset_type:
            query = query.filter(UploadGroupResult.asset_type == asset_type)
        if group_unique_id:
            query = query.filter(UploadGroupResult.group_unique_id.like(f"%{group_unique_id}%"))
        if bill_month:
            query = query.filter(UploadGroupResult.bill_month == bill_month)

        total = query.count()
        items = query.order_by(UploadGroupResult.sync_time.desc()).offset(
            (page - 1) * size).limit(size).all()

        rows = []
        for i in items:
            row = {
                "id": i.id,
                "assetType": i.asset_type,
                "groupUniqueId": i.group_unique_id,
                "syncTime": str(i.sync_time) if i.sync_time else None,
                "operType": i.oper_type,
                "operTime": i.oper_time,
            }

            # 从 data_snapshot 解析字段数据
            try:
                if i.data_snapshot:
                    snap = json.loads(i.data_snapshot) if isinstance(i.data_snapshot, str) else i.data_snapshot
                    for snap_key, snap_val in snap.items():
                        if snap_key not in ("id", "local_biz_id", "mid_local_biz_id", "data_snapshot"):
                            row[snap_key] = snap_val
            except Exception:
                pass

            # 补充父级名称（使用正确的 data_snapshot key 名）
            row["sysName"] = ""
            row["dbName"] = ""
            row["tableName"] = ""
            if i.asset_type == "database":
                sys_local_biz_id = row.get("sys_local_biz_id", "")
                if sys_local_biz_id:
                    p = self.db.query(UploadMidSystem.sys_name).filter(UploadMidSystem.local_biz_id == sys_local_biz_id).first()
                    row["sysName"] = p[0] if p else ""
            elif i.asset_type == "table":
                db_local_biz_id = row.get("db_local_biz_id", "")
                if db_local_biz_id:
                    p = self.db.query(UploadMidDatabase.db_name, UploadMidDatabase.sys_local_biz_id).filter(
                        UploadMidDatabase.local_biz_id == db_local_biz_id).first()
                    if p:
                        row["dbName"] = p[0] or ""
                        sys_id = p[1] or ""
                        if sys_id:
                            sp = self.db.query(UploadMidSystem.sys_name).filter(
                                UploadMidSystem.local_biz_id == sys_id).first()
                            row["sysName"] = sp[0] if sp else ""
            elif i.asset_type == "field":
                tbl_local_biz_id = row.get("tbl_local_biz_id", "")
                if tbl_local_biz_id:
                    p = self.db.query(UploadMidTable.table_name, UploadMidTable.db_local_biz_id).filter(
                        UploadMidTable.local_biz_id == tbl_local_biz_id).first()
                    if p:
                        row["tableName"] = p[0] or ""
                        db_id = p[1] or ""
                        if db_id:
                            dp = self.db.query(UploadMidDatabase.db_name, UploadMidDatabase.sys_local_biz_id).filter(
                                UploadMidDatabase.local_biz_id == db_id).first()
                            if dp:
                                row["dbName"] = dp[0] or ""
                                sys_id = dp[1] or ""
                                if sys_id:
                                    sp = self.db.query(UploadMidSystem.sys_name).filter(
                                        UploadMidSystem.local_biz_id == sys_id).first()
                                    row["sysName"] = sp[0] if sp else ""

            rows.append(row)

        return {"total": total, "list": rows, "page": page, "size": size}

    def query_exclude_marks(
        self,
        sys_id: Optional[str] = None,
        asset_type: Optional[str] = None,
        page: int = 1,
        size: int = 10,
    ) -> Dict[str, Any]:
        """查询排除上传标记"""
        query = self.db.query(ExcludeMark)
        if sys_id:
            query = query.filter(ExcludeMark.sys_id == sys_id)
        if asset_type:
            query = query.filter(ExcludeMark.asset_type == asset_type)

        total = query.count()
        items = query.order_by(ExcludeMark.create_time.desc()).offset(
            (page - 1) * size).limit(size).all()

        rows = []
        for i in items:
            rows.append({
                "id": i.id,
                "assetType": i.asset_type,
                "assetId": i.asset_id,
                "assetName": i.asset_name,
                "sysId": i.sys_id,
                "sysName": i.sys_name,
                "excludeReason": i.exclude_reason,
                "operator": i.operator,
                "createTime": str(i.create_time) if i.create_time else None,
            })

        return {"total": total, "list": rows, "page": page, "size": size}

    def query_merge_logs(
        self,
        asset_type: Optional[str] = None,
        page: int = 1,
        size: int = 10,
    ) -> Dict[str, Any]:
        """查询合并日志"""
        query = self.db.query(MergeLog)
        if asset_type:
            query = query.filter(MergeLog.asset_type == asset_type)

        total = query.count()
        items = query.order_by(MergeLog.create_time.desc()).offset(
            (page - 1) * size).limit(size).all()

        rows = []
        for i in items:
            rows.append({
                "id": i.id,
                "assetType": i.asset_type,
                "targetLocalBizId": i.target_local_biz_id,
                "sourceLocalBizIds": json.loads(i.source_local_biz_ids) if i.source_local_biz_ids else [],
                "mergeReason": i.merge_reason,
                "mergeDetail": json.loads(i.merge_detail) if i.merge_detail else {},
                "operator": i.operator,
                "createTime": str(i.create_time) if i.create_time else None,
            })

        return {"total": total, "list": rows, "page": page, "size": size}

    def query_pending_merges(
        self,
        bill_month: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """查询待合并建议"""
        bill_month = bill_month or self._calc_bill_month()
        return self._check_merge_suggestions(bill_month)

    # ─── 12. 内部方法 ────────────────────────────

    def _apply_parent_filter(self, query, mid_model, asset_type: str, parent_local_biz_id: str,
                              parent_level: Optional[str] = None):
        """按父级（支持间接上级）local_biz_id 过滤中间表"""
        if asset_type == "system" or not parent_local_biz_id:
            return query

        fk = PARENT_FK_MAP.get(asset_type)
        if not fk or not hasattr(mid_model, fk):
            return query

        # 直接父级过滤（默认行为）
        if not parent_level or parent_level == ASSET_LEVELS[ASSET_LEVELS.index(asset_type) - 1]:
            return query.filter(getattr(mid_model, fk) == parent_local_biz_id)

        # 间接上级过滤：通过中间层级构建子查询链
        target_idx = ASSET_LEVELS.index(asset_type)
        parent_idx = ASSET_LEVELS.index(parent_level)

        current_ids = [parent_local_biz_id]
        for level_idx in range(parent_idx, target_idx - 1):
            next_level = ASSET_LEVELS[level_idx + 1]
            next_model = MID_MODEL_MAP[next_level]
            next_fk = PARENT_FK_MAP.get(next_level)
            if not next_fk:
                break
            results = self.db.query(next_model.local_biz_id).filter(
                getattr(next_model, next_fk).in_(current_ids)
            ).all()
            current_ids = [r[0] for r in results]
            if not current_ids:
                break

        if current_ids:
            return query.filter(getattr(mid_model, fk).in_(current_ids))
        return query.filter(text("1=0"))

    def query_mid_options(
        self,
        asset_type: str,
        parent_local_biz_id: Optional[str] = None,
    ) -> list:
        """获取中间表选项列表（用于级联下拉框）"""
        if asset_type not in LOCAL_MODEL_MAP:
            return []

        mid_model = LOCAL_MODEL_MAP[asset_type][1]
        query = self.db.query(mid_model)
        query = self._apply_parent_filter(query, mid_model, asset_type, parent_local_biz_id)
        items = query.all()

        result = []
        for item in items:
            d = {"localBizId": item.local_biz_id}
            # 每个层级返回该层级的关键展示字段
            if asset_type == "system":
                d["sysCode"] = item.sys_code or ""
                d["sysName"] = item.sys_name or ""
                d["recordName"] = item.record_name or ""
            elif asset_type == "database":
                d["dbName"] = item.db_name or ""
                d["dbType"] = item.db_type or ""
            elif asset_type == "table":
                d["tableNameEn"] = item.table_name_en or ""
                d["tableName"] = item.table_name or ""
                d["tableDomain"] = item.table_domain or ""
            elif asset_type == "field":
                d["fieldNameEn"] = item.field_name_en or ""
                d["fieldNameCn"] = item.field_name_cn or ""
                d["fieldType"] = item.field_type or ""
            result.append(d)
        return result

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
            # 先处理父级过滤
            parent_id = filters.pop("parent_local_biz_id", None)
            parent_level = filters.pop("parent_level", None)
            query = self._apply_parent_filter(query, mid_model, asset_type, parent_id, parent_level)
            # 再处理普通文本过滤
            for field, val in filters.items():
                if val and hasattr(mid_model, field):
                    if field == "local_biz_id":
                        query = query.filter(getattr(mid_model, field) == val)
                    else:
                        query = query.filter(getattr(mid_model, field).like(f"%{val}%"))

        total = query.count()
        items = query.offset((page - 1) * size).limit(size).all()

        result = []
        # 缓存父级名称查询
        sys_cache = {}  # local_biz_id → sys_name
        db_cache = {}   # local_biz_id → db_name

        for item in items:
            d = {"localBizId": item.local_biz_id}
            for col in mid_model.__table__.columns:
                d[col.name] = getattr(item, col.name)

            # 为子级列表添加父级名称
            if asset_type == "database":
                sys_id = getattr(item, "sys_local_biz_id", None) or getattr(item, "sys_code", None) or ""
                if sys_id:
                    if sys_id not in sys_cache:
                        parent = self.db.query(UploadMidSystem.sys_name).filter(
                            UploadMidSystem.local_biz_id == sys_id
                        ).first()
                        sys_cache[sys_id] = parent[0] if parent else ""
                    d["sysName"] = sys_cache[sys_id]
            elif asset_type == "table":
                db_id = getattr(item, "db_local_biz_id", None) or ""
                if db_id:
                    if db_id not in db_cache:
                        parent = self.db.query(UploadMidDatabase.db_name, UploadMidDatabase.sys_local_biz_id).filter(
                            UploadMidDatabase.local_biz_id == db_id
                        ).first()
                        if parent:
                            db_cache[db_id] = {"dbName": parent[0] or "", "sysLocalBizId": parent[1] or ""}
                            sys_id = parent[1] or ""
                            if sys_id and sys_id not in sys_cache:
                                sp = self.db.query(UploadMidSystem.sys_name).filter(
                                    UploadMidSystem.local_biz_id == sys_id
                                ).first()
                                sys_cache[sys_id] = sp[0] if sp else ""
                        else:
                            db_cache[db_id] = {"dbName": "", "sysLocalBizId": ""}
                    d["dbName"] = db_cache[db_id]["dbName"]
                    d["sysName"] = sys_cache.get(db_cache[db_id]["sysLocalBizId"], "")
            elif asset_type == "field":
                tbl_id = getattr(item, "tbl_local_biz_id", None) or ""
                if tbl_id:
                    tbl = self.db.query(UploadMidTable.table_name, UploadMidTable.db_local_biz_id).filter(
                        UploadMidTable.local_biz_id == tbl_id
                    ).first()
                    if tbl:
                        d["tableName"] = tbl[0] or ""
                        db_id = tbl[1] or ""
                        if db_id not in db_cache:
                            parent = self.db.query(UploadMidDatabase.db_name, UploadMidDatabase.sys_local_biz_id).filter(
                                UploadMidDatabase.local_biz_id == db_id
                            ).first()
                            if parent:
                                db_cache[db_id] = {"dbName": parent[0] or "", "sysLocalBizId": parent[1] or ""}
                                sys_id = parent[1] or ""
                                if sys_id and sys_id not in sys_cache:
                                    sp = self.db.query(UploadMidSystem.sys_name).filter(
                                        UploadMidSystem.local_biz_id == sys_id
                                    ).first()
                                    sys_cache[sys_id] = sp[0] if sp else ""
                            else:
                                db_cache[db_id] = {"dbName": "", "sysLocalBizId": ""}
                        d["dbName"] = db_cache[db_id]["dbName"]
                        d["sysName"] = sys_cache.get(db_cache[db_id]["sysLocalBizId"], "")
                    else:
                        d["tableName"] = ""
                        d["dbName"] = ""
                        d["sysName"] = ""

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

    def query_result_list(
        self,
        asset_type: Optional[str] = None,
        upload_status: Optional[str] = None,
        batch_no: Optional[str] = None,
        page: int = 1,
        size: int = 10,
    ) -> Dict[str, Any]:
        """查询上传结果表（最终上传数据确认查看，只读）"""
        query = self.db.query(UploadResultTable)
        if asset_type:
            query = query.filter(UploadResultTable.asset_type == asset_type)
        if upload_status:
            query = query.filter(UploadResultTable.upload_status == upload_status)
        if batch_no:
            query = query.filter(UploadResultTable.upload_batch_no.like(f"%{batch_no}%"))

        total = query.count()
        items = query.order_by(UploadResultTable.upload_time.is_(None), UploadResultTable.upload_time.desc()).offset(
            (page - 1) * size).limit(size).all()

        rows = []
        for i in items:
            rows.append({
                "id": i.id,
                "assetType": i.asset_type,
                "localBizId": i.local_biz_id,
                "groupUniqueId": i.group_unique_id,
                "uploadStatus": i.upload_status,
                "uploadTime": str(i.upload_time) if i.upload_time else None,
                "uploadBatchNo": i.upload_batch_no,
                "syncToResultTime": str(i.sync_to_result_time) if i.sync_to_result_time else None,
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
