"""
构建演示数据：在中间结果表（带账期）中插入稽核状态为"不通过"的系统记录

用法: python seed_demo_fail.py

该脚本会在 t_upload_result_mid 中创建几条 audit_status='fail' 的记录，
同时在对应的中间表（t_upload_mid_system 等）中同步设置 audit_status='fail'，
方便演示"编辑→保存并重新稽核→变为正常"的完整流程。

注意：运行前请确认 seed_from_dx.py 已执行过（即有基础数据）。
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from datetime import datetime
from app.database import SessionLocal
from app.models.upload_mid import (
    UploadMidSystem, UploadMidDatabase, UploadMidTable, UploadMidField,
    UploadResultMid, UploadOperationLog,
)


def _calc_bill_month() -> str:
    """计算当前账期：每月20日全量稽核，使用当前月份"""
    from datetime import date
    today = date.today()
    if today.day >= 26:
        y, m = today.year, today.month
        if m == 12:
            return f"{y + 1}01"
        return f"{y}{str(m + 1).zfill(2)}"
    else:
        return f"{today.year}{str(today.month).zfill(2)}"


def build_data_snapshot(asset_type: str, rec) -> dict:
    """从中间表记录构建data_snapshot"""
    snap = {}
    for col in rec.__table__.columns:
        val = getattr(rec, col.name, None)
        if val is not None:
            snap[col.name] = str(val)
    return snap


def seed_fail_records(db):
    """
    选取若干系统层级，分别构建"稽核不通过"演示数据
    """
    bill_month = _calc_bill_month()
    now = datetime.now()
    now_str = now.strftime("%Y%m%d%H%M%S")
    print(f"当前账期: {bill_month}")

    # ── 演示数据配置 ─────────────────────────────────────
    # 选取几组有完整层级关系的记录
    demo_setups = [
        # ===== 1. 系统：CQ-AQ-WDZX-0001（文档中心系统）=====
        {
            "sys_local_biz_id": "CQ-AQ-WDZX-0001",
            "sys_fail_reason": "[MM-001]必填字段为空: biz_owner, org_dept",
            "db_fail_records": [
                {
                    "local_biz_id": "CQ-AQ-WDZX-DB-0001",
                    "db_fail_reason": "[MM-001]数据库版本信息为空",
                    "tbl_fail_records": [
                        {
                            "local_biz_id": "CQ-AQ-WDZX-TABLE-000001",
                            "tbl_fail_reason": "[MM-001]必填字段为空: table_introduct, table_domain",
                        },
                    ],
                },
            ],
        },
        # ===== 2. 系统：CQ-AY-SJWK-0001（数据安全审计系统）=====
        {
            "sys_local_biz_id": "CQ-AY-SJWK-0001",
            "sys_fail_reason": "[MM-001]必填字段为空: record_name",
            "db_fail_records": [
                {
                    "local_biz_id": "CQ-AY-SJWK-DB-0001",
                    "db_fail_reason": "[MM-001]数据库IP地址为空",
                    "tbl_fail_records": [
                        {
                            "local_biz_id": "CQ-AY-SJWK-TABLE-000001",
                            "tbl_fail_reason": "[MM-008]样例数据少于10条",
                        },
                    ],
                },
            ],
        },
    ]

    total_sys = 0
    total_db = 0
    total_tbl = 0

    for setup in demo_setups:
        sys_id = setup["sys_local_biz_id"]
        sys_fail_reason = setup["sys_fail_reason"]

        # ── 查找系统中间表记录 ──
        sys_rec = db.query(UploadMidSystem).filter(
            UploadMidSystem.local_biz_id == sys_id
        ).first()
        if not sys_rec:
            print(f"  [跳过] 系统 {sys_id} 不存在，跳过")
            continue

        # 更新系统中间表 audit_status = fail
        sys_rec.audit_status = "fail"
        sys_rec.non_compliant_reason = sys_fail_reason
        sys_rec.audit_time = now
        sys_rec.upload_status = "pending"
        print(f"  [系统] {sys_id} ({sys_rec.sys_name}) → audit_status=fail, reason={sys_fail_reason}")

        # 构建系统快照
        sys_snapshot = build_data_snapshot("system", sys_rec)

        # UPSERT 到中间结果表
        existing = db.query(UploadResultMid).filter(
            UploadResultMid.asset_type == "system",
            UploadResultMid.mid_local_biz_id == sys_id,
            UploadResultMid.bill_month == bill_month,
        ).first()
        if existing:
            existing.audit_status = "fail"
            existing.non_compliant_reason = sys_fail_reason
            existing.data_snapshot = json.dumps(sys_snapshot, ensure_ascii=False)
            existing.result_status = "pending"
            print(f"    → 更新中间结果表记录 ID={existing.id}")
        else:
            obj = UploadResultMid(
                asset_type="system",
                mid_local_biz_id=sys_id,
                group_unique_id=sys_rec.group_unique_id,
                bill_month=bill_month,
                result_status="pending",
                audit_status="fail",
                non_compliant_reason=sys_fail_reason,
                data_snapshot=json.dumps(sys_snapshot, ensure_ascii=False),
                sync_time=now,
                oper_type=sys_rec.oper_type or "0",
                oper_time=now_str,
            )
            db.add(obj)
            print(f"    → 新增中间结果表记录")
        total_sys += 1

        # ── 处理数据库层级 ──
        for db_setup in setup.get("db_fail_records", []):
            db_id = db_setup["local_biz_id"]
            db_fail_reason = db_setup["db_fail_reason"]

            db_rec = db.query(UploadMidDatabase).filter(
                UploadMidDatabase.local_biz_id == db_id
            ).first()
            if not db_rec:
                print(f"    [跳过] 数据库 {db_id} 不存在")
                continue

            db_rec.audit_status = "fail"
            db_rec.non_compliant_reason = db_fail_reason
            db_rec.audit_time = now
            db_rec.upload_status = "pending"
            print(f"    [数据库] {db_id} ({db_rec.db_name}) → audit_status=fail, reason={db_fail_reason}")

            db_snapshot = build_data_snapshot("database", db_rec)
            existing = db.query(UploadResultMid).filter(
                UploadResultMid.asset_type == "database",
                UploadResultMid.mid_local_biz_id == db_id,
                UploadResultMid.bill_month == bill_month,
            ).first()
            if existing:
                existing.audit_status = "fail"
                existing.non_compliant_reason = db_fail_reason
                existing.data_snapshot = json.dumps(db_snapshot, ensure_ascii=False)
                existing.result_status = "pending"
            else:
                obj = UploadResultMid(
                    asset_type="database",
                    mid_local_biz_id=db_id,
                    group_unique_id=db_rec.group_unique_id,
                    bill_month=bill_month,
                    result_status="pending",
                    audit_status="fail",
                    non_compliant_reason=db_fail_reason,
                    data_snapshot=json.dumps(db_snapshot, ensure_ascii=False),
                    sync_time=now,
                    oper_type=db_rec.oper_type or "0",
                    oper_time=now_str,
                )
                db.add(obj)
            total_db += 1

            # ── 处理表层级 ──
            for tbl_setup in db_setup.get("tbl_fail_records", []):
                tbl_id = tbl_setup["local_biz_id"]
                tbl_fail_reason = tbl_setup["tbl_fail_reason"]

                tbl_rec = db.query(UploadMidTable).filter(
                    UploadMidTable.local_biz_id == tbl_id
                ).first()
                if not tbl_rec:
                    print(f"      [跳过] 表 {tbl_id} 不存在")
                    continue

                tbl_rec.audit_status = "fail"
                tbl_rec.non_compliant_reason = tbl_fail_reason
                tbl_rec.audit_time = now
                tbl_rec.upload_status = "pending"
                print(f"      [表] {tbl_id} ({tbl_rec.table_name_en}) → audit_status=fail, reason={tbl_fail_reason}")

                tbl_snapshot = build_data_snapshot("table", tbl_rec)
                existing = db.query(UploadResultMid).filter(
                    UploadResultMid.asset_type == "table",
                    UploadResultMid.mid_local_biz_id == tbl_id,
                    UploadResultMid.bill_month == bill_month,
                ).first()
                if existing:
                    existing.audit_status = "fail"
                    existing.non_compliant_reason = tbl_fail_reason
                    existing.data_snapshot = json.dumps(tbl_snapshot, ensure_ascii=False)
                    existing.result_status = "pending"
                else:
                    obj = UploadResultMid(
                        asset_type="table",
                        mid_local_biz_id=tbl_id,
                        group_unique_id=tbl_rec.group_unique_id,
                        bill_month=bill_month,
                        result_status="pending",
                        audit_status="fail",
                        non_compliant_reason=tbl_fail_reason,
                        data_snapshot=json.dumps(tbl_snapshot, ensure_ascii=False),
                        sync_time=now,
                        oper_type=tbl_rec.oper_type or "0",
                        oper_time=now_str,
                    )
                    db.add(obj)
                total_tbl += 1

    # ── 提交 ──
    db.commit()

    # ── 统计 ──
    print(f"\n=== 稽核不通过演示数据构建完成 ===")
    print(f"系统: {total_sys} 条")
    print(f"数据库: {total_db} 条")
    print(f"表: {total_tbl} 条")
    print(f"账期: {bill_month}")

    # 验证：查询结果
    fail_count = db.query(UploadResultMid).filter(
        UploadResultMid.audit_status == "fail",
        UploadResultMid.bill_month == bill_month,
    ).count()
    print(f"\n当前账期 t_upload_result_mid 中 audit_status=fail 的记录数: {fail_count}")


def main():
    db = SessionLocal()
    try:
        seed_fail_records(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
