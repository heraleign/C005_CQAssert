"""
从 dx_assets_*_cq 集团上传源表 全量同步到 资源上传中间表 + 资源管理表

用法: python seed_from_dx.py

清理所有旧数据后，从4张源表重新灌入:
  - dx_assets_system_cq   → t_upload_mid_system + t_upload_resource_system
  - dx_assets_database_cq → t_upload_mid_database + t_upload_resource_database
  - dx_assets_table_cq    → t_upload_mid_table + t_upload_resource_table
  - dx_assets_field_cq    → t_upload_mid_field + t_upload_resource_field
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models.upload_mid import (
    UploadMidSystem, UploadMidDatabase, UploadMidTable, UploadMidField,
    UploadResultMid, UploadGroupResult, UploadResultTable, ClassifyMid,
)
from app.models.asset import (
    UploadResourceSystem, UploadResourceDatabase, UploadResourceTable, UploadResourceField,
)

NOW_STR = datetime.now().strftime("%Y%m%d%H%M%S")


def _map_status(raw: str) -> str:
    """转换系统状态: 1→在用, 0/2→已下线, 其他原样返回"""
    if not raw or raw.strip() == "":
        return "建设中"
    v = raw.strip()
    if v == "1":
        return "在用"
    if v in ("0", "2"):
        return "已下线"
    return v


def _safe(val):
    """None → 空字符串"""
    return str(val) if val is not None else ""


def _safe_sample(val, max_len=50000):
    """安全处理样例数据，超长截断"""
    if val is None:
        return None
    s = str(val)
    return s[:max_len] if len(s) > max_len else s


def _safe_or_none(val):
    """None 保留 None，空字符串也保留"""
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def clear_all(db):
    """按依赖顺序清除旧数据（包括结果表与分类数据）"""
    for tbl in [ClassifyMid, UploadResultMid, UploadGroupResult, UploadResultTable,
                UploadMidField, UploadMidTable, UploadMidDatabase, UploadMidSystem,
                UploadResourceField, UploadResourceTable, UploadResourceDatabase, UploadResourceSystem]:
        cnt = db.query(tbl).delete()
        if cnt:
            print(f"  Cleared {cnt} from {tbl.__tablename__}")
    db.commit()
    print("[CLEAR] 已清除所有相关表的数据\n")


def seed_systems(db):
    """从 dx_assets_system_cq 同步系统数据（包含所有集团上报字段）"""
    print("=== 1. dx_assets_system_cq → t_upload_resource_system + t_upload_mid_system ===")
    rows = db.execute(text("""
        SELECT sys_id, sys_name, sub_sys_name, sys_introduct,
               sys_classify, assigned_organization, belong_dept,
               contractor_unit, contractor_department, contractor_leader,
               contractor_leader_phone, contractor_leader_email,
               construction_vendor, management_leader,
               management_leader_phone, management_leader_email,
               operation_unit, operation_department,
               operation_leader, operation_leader_phone, operation_leader_email,
               launch_time, project_code, project_name, contract_code,
               sys_func_type, if_managed, website, netins_sys_id, sys_status,
               record_name, master_data_code, external_tag,
               oper_type, oper_time
        FROM dx_assets_system_cq
    """)).fetchall()
    print(f"   源表记录数: {len(rows)}")

    # 缓存 sys_code → 资源表 auto-increment id
    sys_id_map = {}

    rsrc_count = 0
    mid_count = 0

    for r in rows:
        sys_code = _safe(r[0])
        if not sys_code:
            continue
        sys_name = _safe(r[1])
        sub_sys_name = _safe(r[2])
        sys_introduct = _safe(r[3])
        sys_classify = _safe(r[4])
        org_unit = _safe(r[5])
        org_dept = _safe(r[6])
        contractor_unit = _safe(r[7])
        contractor_department = _safe(r[8])
        contractor_leader = _safe(r[9])
        contractor_leader_phone = _safe(r[10])
        contractor_leader_email = _safe(r[11])
        construction_vendor = _safe(r[12])
        management_leader = _safe(r[13])
        management_leader_phone = _safe(r[14])
        management_leader_email = _safe(r[15])
        operation_unit = _safe(r[16])
        operation_department = _safe(r[17])
        operation_leader = _safe(r[18])
        operation_leader_phone = _safe(r[19])
        operation_leader_email = _safe(r[20])
        launch_time = _safe(r[21])
        project_code = _safe(r[22])
        project_name = _safe(r[23])
        contract_code = _safe(r[24])
        sys_func_type = _safe(r[25])
        if_managed = _safe(r[26])
        website = _safe(r[27])
        netins_sys_id = _safe(r[28])
        sys_status = _map_status(_safe(r[29]))
        record_name = _safe(r[30])
        master_data_code = _safe(r[31])
        external_tag = _safe(r[32])
        oper_type = _safe(r[33])
        oper_time = _safe(r[34])

        # --- t_upload_resource_system ---
        obj = UploadResourceSystem(
            sys_group_id=sys_code,
            sys_code=sys_code,
            sys_name=sys_name,
            record_name=record_name,
            master_data_code=master_data_code,
            org_unit=org_unit,
            org_dept=org_dept,
            status=sys_status,
            sys_func_type=sys_func_type,
            if_managed=if_managed,
            online_time=launch_time,
            is_uploaded="否",
            is_compliant="否",
            oper_type=oper_type if oper_type else "0",
            oper_time=oper_time if oper_time else NOW_STR,
        )
        db.add(obj)
        db.flush()
        sys_id_map[sys_code] = obj.id  # 保存 auto-increment id
        rsrc_count += 1

        # --- t_upload_mid_system (包含所有集团字段) ---
        mid = UploadMidSystem(
            local_biz_id=sys_code,
            sys_code=sys_code,
            sys_name=sys_name,
            sub_sys_name=sub_sys_name,
            sys_introduct=sys_introduct,
            sys_classify=sys_classify,
            record_name=record_name,
            master_data_code=master_data_code,
            org_unit=org_unit,
            org_dept=org_dept,
            biz_owner="",
            status=sys_status,
            sys_func_type=sys_func_type,
            if_managed=if_managed,
            online_time=launch_time,
            contractor_unit=contractor_unit,
            contractor_department=contractor_department,
            contractor_leader=contractor_leader,
            contractor_leader_phone=contractor_leader_phone,
            contractor_leader_email=contractor_leader_email,
            construction_vendor=construction_vendor,
            management_leader=management_leader,
            management_leader_phone=management_leader_phone,
            management_leader_email=management_leader_email,
            operation_unit=operation_unit,
            operation_department=operation_department,
            operation_leader=operation_leader,
            operation_leader_phone=operation_leader_phone,
            operation_leader_email=operation_leader_email,
            launch_time=launch_time,
            project_code=project_code,
            project_name=project_name,
            contract_code=contract_code,
            website=website,
            netins_sys_id=netins_sys_id,
            external_tag=external_tag if external_tag else None,
            upload_flag="1",
            audit_status="pending",
            upload_status="pending",
            oper_type=oper_type if oper_type else "0",
            oper_time=oper_time if oper_time else NOW_STR,
        )
        db.add(mid)
        mid_count += 1

    db.commit()
    print(f"   resource_system: {rsrc_count} 条")
    print(f"   mid_system: {mid_count} 条")
    return sys_id_map


def seed_databases(db):
    """从 dx_assets_database_cq 同步数据库数据"""
    print("\n=== 2. dx_assets_database_cq → t_upload_resource_database + t_upload_mid_database ===")
    rows = db.execute(text("""
        SELECT dbs_id, db_type, db_name, db_version,
               sys_id, db_ip, db_port,
               oper_type, oper_time
        FROM dx_assets_database_cq
    """)).fetchall()
    print(f"   源表记录数: {len(rows)}")

    rsrc_count = 0
    mid_count = 0

    for r in rows:
        dbs_id = _safe(r[0])
        if not dbs_id:
            continue
        db_type = _safe(r[1])
        db_name = _safe(r[2])
        db_version = _safe(r[3])
        sys_id = _safe(r[4])
        db_ip = _safe(r[5])
        db_port = _safe(r[6])
        oper_type = _safe(r[7])
        oper_time = _safe(r[8])

        # --- t_upload_resource_database ---
        # 查找所属系统的 auto-increment id
        sys_rec = db.query(UploadResourceSystem).filter(
            UploadResourceSystem.sys_code == sys_id
        ).first()
        sys_fk = sys_rec.id if sys_rec else None

        rsrc = UploadResourceDatabase(
            db_group_id=dbs_id,
            sys_id=sys_fk,
            db_name=db_name,
            db_type=db_type,
            is_compliant="否",
            oper_type=oper_type if oper_type else "0",
            oper_time=oper_time if oper_time else NOW_STR,
        )
        db.add(rsrc)
        rsrc_count += 1

        # --- t_upload_mid_database ---
        mid = UploadMidDatabase(
            local_biz_id=dbs_id,
            sys_local_biz_id=sys_id,
            sys_code=sys_id,
            db_name=db_name,
            db_type=db_type,
            db_version=db_version,
            db_ip=db_ip,
            db_port=db_port,
            upload_flag="1",
            audit_status="pending",
            upload_status="pending",
            oper_type=oper_type if oper_type else "0",
            oper_time=oper_time if oper_time else NOW_STR,
        )
        db.add(mid)
        mid_count += 1

    db.commit()
    print(f"   resource_database: {rsrc_count} 条")
    print(f"   mid_database: {mid_count} 条")


def seed_tables(db):
    """从 dx_assets_table_cq 同步表数据"""
    print("\n=== 3. dx_assets_table_cq → t_upload_resource_table + t_upload_mid_table ===")
    rows = db.execute(text("""
        SELECT tbl_id, table_schema, table_en_name, table_name, table_introduct,
               dbs_id, table_domain, scenario_tag,
               lake_data_type, in_unit_lakes, premium_model_in_lake, uploaded_to_big_lake,
               external_unique_identifier, is_shareable, is_shared, sharing_channel,
               tech_contact, tech_contact_phone,
               data_aggregation_method, data_collection_time, aggregation_granularity,
               is_incremental_or_full, storage_period,
               reference_count, sub_count, col_count, access_count,
               table_level, tabtable_category,
               sample_data, layer_level, business_domain, source_system,
               is_partitioned, data_quality, industry_catalog, industry_expert,
               group_gather_tbname,
               oper_type, oper_time
        FROM dx_assets_table_cq
    """)).fetchall()
    print(f"   源表记录数: {len(rows)}")

    rsrc_count = 0
    mid_count = 0

    for r in rows:
        tbl_id = _safe(r[0])
        if not tbl_id:
            continue
        table_schema = _safe(r[1])
        table_en_name = _safe(r[2])
        table_name = _safe(r[3])
        table_introduct = _safe(r[4])
        dbs_id = _safe(r[5])
        table_domain = _safe(r[6])
        scenario_tag = _safe(r[7])
        lake_data_type = _safe(r[8])
        in_unit_lakes = _safe(r[9])
        premium_model_in_lake = _safe(r[10])
        uploaded_to_big_lake = _safe(r[11])
        external_unique_identifier = _safe(r[12])
        is_shareable = _safe(r[13])
        is_shared = _safe(r[14])
        sharing_channel = _safe(r[15])
        tech_contact = _safe(r[16])
        tech_contact_phone = _safe(r[17])
        data_aggregation_method = _safe(r[18])
        data_collection_time = _safe(r[19])
        aggregation_granularity = _safe(r[20])
        is_incremental_or_full = _safe(r[21])
        storage_period = _safe(r[22])
        reference_count = _safe(r[23])
        sub_count = _safe(r[24])
        col_count = _safe(r[25])
        access_count = _safe(r[26])
        table_level = _safe(r[27])
        tabtable_category = _safe(r[28])
        sample_data = _safe(r[29])
        layer_level = _safe(r[30])
        business_domain = _safe(r[31])
        source_system = _safe(r[32])
        is_partitioned = _safe(r[33])
        data_quality = _safe(r[34])
        industry_catalog = _safe(r[35])
        industry_expert = _safe(r[36])
        group_gather_tbname = _safe(r[37])
        oper_type = _safe(r[38])
        oper_time = _safe(r[39])

        # --- t_upload_resource_table ---
        # 查找所属数据库的 auto-increment id
        db_rec = db.query(UploadResourceDatabase).filter(
            UploadResourceDatabase.db_group_id == dbs_id
        ).first()
        db_fk = db_rec.id if db_rec else None

        rsrc = UploadResourceTable(
            tbl_group_id=tbl_id,
            db_id=db_fk,
            table_name_en=table_en_name,
            table_name_cn=table_name,
            table_desc=table_introduct,
            topic_domain=table_domain,
            sample_data=_safe_sample(sample_data),
            is_compliant="否",
            oper_type=oper_type if oper_type else "0",
            oper_time=oper_time if oper_time else NOW_STR,
        )
        db.add(rsrc)
        rsrc_count += 1

        # --- t_upload_mid_table ---
        mid = UploadMidTable(
            local_biz_id=tbl_id,
            db_local_biz_id=dbs_id,
            table_name_en=table_en_name,
            table_name=table_name,
            table_introduct=table_introduct,
            table_domain=table_domain,
            sample_data=_safe_sample(sample_data),
            scenario_tag=scenario_tag,
            lake_data_type=lake_data_type,
            in_unit_lakes=in_unit_lakes,
            premium_model_in_lake=premium_model_in_lake,
            uploaded_to_big_lake=uploaded_to_big_lake,
            external_unique_identifier=external_unique_identifier,
            is_shareable=is_shareable,
            is_shared=is_shared,
            sharing_channel=sharing_channel,
            tech_contact=tech_contact,
            tech_contact_phone=tech_contact_phone,
            data_aggregation_method=data_aggregation_method,
            data_collection_time=data_collection_time,
            aggregation_granularity=aggregation_granularity,
            is_incremental_or_full=is_incremental_or_full,
            storage_period=storage_period,
            reference_count=reference_count,
            sub_count=sub_count,
            col_count=col_count,
            access_count=access_count,
            table_level=table_level,
            tabtable_category=tabtable_category,
            layer_level=layer_level,
            business_domain=business_domain,
            source_system=source_system,
            is_partitioned=is_partitioned,
            data_quality=data_quality,
            industry_catalog=industry_catalog,
            industry_expert=industry_expert,
            group_gather_tbname=group_gather_tbname,
            upload_flag="1",
            audit_status="pending",
            upload_status="pending",
            oper_type=oper_type if oper_type else "0",
            oper_time=oper_time if oper_time else NOW_STR,
        )
        db.add(mid)
        mid_count += 1

    db.commit()
    print(f"   resource_table: {rsrc_count} 条")
    print(f"   mid_table: {mid_count} 条")


def seed_fields(db):
    """从 dx_assets_field_cq 同步字段数据"""
    print("\n=== 4. dx_assets_field_cq → t_upload_resource_field + t_upload_mid_field ===")
    rows = db.execute(text("""
        SELECT id, tbl_id, field_en_name, field_name, field_type,
               field_length, field_desc, process_caliber_desc,
               is_primary_key, is_foreign_key, is_shareable,
               field_category, sensitivity_level, sensitive_field_elements,
               is_desensitized, value_definition,
               mdm_field, mdm_type,
               oper_type, oper_time
        FROM dx_assets_field_cq
    """)).fetchall()
    print(f"   源表记录数: {len(rows)}")

    rsrc_count = 0
    mid_count = 0

    for r in rows:
        field_id = _safe(r[0])
        if not field_id:
            continue
        tbl_id = _safe(r[1])
        field_en_name = _safe(r[2])
        field_name = _safe(r[3])
        field_type = _safe(r[4])
        field_length = _safe(r[5])
        field_desc = _safe(r[6])
        process_caliber_desc = _safe(r[7])
        is_primary_key = _safe(r[8])
        is_foreign_key = _safe(r[9])
        is_shareable = _safe(r[10])
        field_category = _safe(r[11])
        sensitivity_level = _safe(r[12])
        sensitive_field_elements = _safe(r[13])
        is_desensitized = _safe(r[14])
        value_definition = _safe(r[15])
        mdm_field = _safe(r[16])
        mdm_type = _safe(r[17])
        oper_type = _safe(r[18])
        oper_time = _safe(r[19])

        # --- t_upload_resource_field ---
        # 查找所属表的 auto-increment id
        tbl_rec = db.query(UploadResourceTable).filter(
            UploadResourceTable.tbl_group_id == tbl_id
        ).first()
        tbl_fk = tbl_rec.id if tbl_rec else None

        rsrc = UploadResourceField(
            field_group_id=field_id,
            tbl_id=tbl_fk,
            field_name_en=field_en_name,
            field_name_cn=field_name,
            field_type=field_type,
            is_compliant="否",
            oper_type=oper_type if oper_type else "0",
            oper_time=oper_time if oper_time else NOW_STR,
        )
        db.add(rsrc)
        rsrc_count += 1

        # --- t_upload_mid_field ---
        mid = UploadMidField(
            local_biz_id=field_id,
            tbl_local_biz_id=tbl_id,
            field_name_en=field_en_name,
            field_name_cn=field_name,
            field_type=field_type,
            field_length=field_length,
            field_desc=field_desc,
            process_caliber_desc=process_caliber_desc,
            is_primary_key=is_primary_key,
            is_foreign_key=is_foreign_key,
            is_shareable=is_shareable,
            field_category=field_category,
            sensitivity_level=sensitivity_level,
            sensitive_field_elements=sensitive_field_elements,
            is_desensitized=is_desensitized,
            value_definition=value_definition,
            mdm_field=mdm_field,
            mdm_type=mdm_type,
            audit_status="pending",
            upload_status="pending",
            oper_type=oper_type if oper_type else "0",
            oper_time=oper_time if oper_time else NOW_STR,
        )
        db.add(mid)
        mid_count += 1

    db.commit()
    print(f"   resource_field: {rsrc_count} 条")
    print(f"   mid_field: {mid_count} 条")


def generate_classify(db):
    """为所有中间表记录生成分级分类记录（sync-to-result 流程需要）"""
    print("\n=== 5. 生成分级分类记录 ===")
    from datetime import datetime
    now = datetime.now()
    count = 0

    # 查询所有需要分类的记录（使用批量查询避免 OOM）
    for asset_type, model in [("system", UploadMidSystem), ("database", UploadMidDatabase),
                               ("table", UploadMidTable), ("field", UploadMidField)]:
        # 分批处理，避免大数据量时内存溢出
        batch_size = 500
        offset = 0
        while True:
            batch = db.query(model.local_biz_id).offset(offset).limit(batch_size).all()
            if not batch:
                break
            for (lid,) in batch:
                # 跳过已有分类的
                exist = db.query(ClassifyMid).filter(
                    ClassifyMid.local_biz_id == lid,
                    ClassifyMid.asset_type == asset_type,
                ).first()
                if not exist:
                    db.add(ClassifyMid(
                        local_biz_id=lid,
                        asset_type=asset_type,
                        data_level="3",
                        data_category="生产数据",
                        classify_status="valid",
                        classify_time=now,
                        source="自动生成",
                    ))
                    count += 1
            offset += batch_size
            db.flush()

    db.commit()
    print(f"   生成 {count} 条分类记录")


def _calc_bill_month() -> str:
    """计算当前账期：上月26日至本月25日"""
    from datetime import date
    today = date.today()
    if today.day >= 26:
        y, m = today.year, today.month
        if m == 12:
            return f"{y + 1}01"
        return f"{y}{str(m + 1).zfill(2)}"
    else:
        return f"{today.year}{str(today.month).zfill(2)}"


def generate_group_unique_id(db):
    """为所有中间表记录生成集团唯一标识"""
    print("\n=== 6. 生成集团唯一标识（group_unique_id） ===")
    count = 0

    # 系统：使用 sys_code 作为唯一标识前缀
    for sys in db.query(UploadMidSystem).filter(UploadMidSystem.group_unique_id.is_(None)).all():
        sys.group_unique_id = f"JT-SYS-{sys.sys_code}"
        sys.group_id_generated = 1
        count += 1
    db.flush()

    # 数据库：sys_code + db_name + db_type
    for db_rec in db.query(UploadMidDatabase).filter(UploadMidDatabase.group_unique_id.is_(None)).all():
        sys_code = db_rec.sys_code or ""
        db_name = db_rec.db_name or ""
        db_type = db_rec.db_type or ""
        db_rec.group_unique_id = f"{sys_code}-{db_name}-{db_type}"
        db_rec.group_id_generated = 1
        count += 1
    db.flush()

    # 表：parent + TBL + table_name_en
    for tbl in db.query(UploadMidTable).filter(UploadMidTable.group_unique_id.is_(None)).all():
        parent = db.query(UploadMidDatabase).filter(
            UploadMidDatabase.local_biz_id == tbl.db_local_biz_id
        ).first()
        prefix = parent.group_unique_id if parent and parent.group_unique_id else (tbl.db_local_biz_id or "")
        tbl_name = tbl.table_name_en or tbl.table_name or ""
        tbl.group_unique_id = f"{prefix}-TBL-{tbl_name}"
        tbl.group_id_generated = 1
        count += 1
    db.flush()

    # 字段：parent + FLD + field_name_en
    for fld in db.query(UploadMidField).filter(UploadMidField.group_unique_id.is_(None)).all():
        parent = db.query(UploadMidTable).filter(
            UploadMidTable.local_biz_id == fld.tbl_local_biz_id
        ).first()
        prefix = parent.group_unique_id if parent and parent.group_unique_id else (fld.tbl_local_biz_id or "")
        fld_name = fld.field_name_en or fld.field_name_cn or ""
        fld.group_unique_id = f"{prefix}-FLD-{fld_name}"
        fld.group_id_generated = 1
        count += 1
    db.flush()

    db.commit()
    print(f"   生成 {count} 条 group_unique_id")


def set_all_audit_pass(db):
    """将所有中间表记录设为稽核通过"""
    print("\n=== 7. 设置稽核状态为 pass ===")
    for model in [UploadMidSystem, UploadMidDatabase, UploadMidTable, UploadMidField]:
        cnt = db.query(model).filter(model.audit_status == "pending").update({"audit_status": "pass"})
        print(f"   {model.__tablename__}: {cnt} 条")
    db.commit()


def generate_result_mid(db):
    """使用直接 SQL 快速生成中间结果表（带账期），避免逐条 INSERT 性能问题"""
    print("\n=== 8. 生成中间结果表（带账期） ===")
    from sqlalchemy import text as sql_text
    bill_month = _calc_bill_month()

    # 清除旧数据
    db.execute(sql_text("DELETE FROM t_upload_result_mid"))
    db.commit()

    for asset_type, table, has_flag in [
        ("system", "t_upload_mid_system", True),
        ("database", "t_upload_mid_database", True),
        ("table", "t_upload_mid_table", True),
        ("field", "t_upload_mid_field", False),
    ]:
        flag_filter = "upload_flag = '1'" if has_flag else "1=1"

        # 第1步：批量插入基础记录
        sql = f"""
            INSERT INTO t_upload_result_mid
                (asset_type, mid_local_biz_id, group_unique_id, bill_month,
                 result_status, audit_status, data_snapshot, sync_time, oper_type)
            SELECT :at, m.local_biz_id, m.group_unique_id, :bm,
                   'pending', 'pass', '', NOW(), COALESCE(m.oper_type, '0')
            FROM {table} m
            WHERE m.audit_status = 'pass' AND {flag_filter}
        """
        db.execute(sql_text(sql), {"at": asset_type, "bm": bill_month})
        db.flush()

    # 第2步：用 MySQL JSON_OBJECT 批量更新 data_snapshot
    for asset_type, table in [
        ("system", "t_upload_mid_system"),
        ("database", "t_upload_mid_database"),
        ("table", "t_upload_mid_table"),
        ("field", "t_upload_mid_field"),
    ]:
        cols = db.execute(sql_text(
            f"SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            f"WHERE TABLE_NAME = '{table}' AND TABLE_SCHEMA = DATABASE()"
        )).fetchall()
        json_parts = [f"'{c[0]}', COALESCE(m.{c[0]}, '')" for c in cols]
        json_expr = f"JSON_OBJECT({', '.join(json_parts)})"

        sql = f"""
            UPDATE t_upload_result_mid r
            JOIN {table} m ON r.mid_local_biz_id = m.local_biz_id
            SET r.data_snapshot = {json_expr}
            WHERE r.asset_type = :at AND r.bill_month = :bm
        """
        result = db.execute(sql_text(sql), {"at": asset_type, "bm": bill_month})
        print(f"   {asset_type}: {result.rowcount} 条")

    db.commit()

    # 统计
    rows = db.execute(sql_text(
        "SELECT asset_type, COUNT(*) FROM t_upload_result_mid GROUP BY asset_type"
    )).fetchall()
    total = sum(r[1] for r in rows)
    print(f"   总计: {total} 条 (账期: {bill_month})")
    for r in rows:
        print(f"     {r[0]}: {r[1]}")


def main():
    db = SessionLocal()
    try:
        clear_all(db)
        seed_systems(db)
        seed_databases(db)
        seed_tables(db)
        seed_fields(db)
        generate_classify(db)
        generate_group_unique_id(db)
        set_all_audit_pass(db)
        generate_result_mid(db)
        print("\n=== ALL DONE ===")
        print("数据已从 dx_assets_*_cq 源表成功同步到:")
        print("  - t_upload_mid_system/database/table/field")
        print("  - t_upload_resource_system/database/table/field")
        print("  - t_classify_mid")
        print("  - t_upload_result_mid（带账期，可直接在「中间结果表」页面查看）")
        print(f"  当前账期: {_calc_bill_month()}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
