"""
Seed data from ay_dx_assets_* and dx_assets_system_cq into flow tables.
Run: python seed_from_ay.py
"""
import sys
from datetime import datetime
from app.config import settings
from sqlalchemy import create_engine, text

engine = create_engine(settings.database_url)
NOW_STR = datetime.now().strftime("%Y%m%d%H%M%S")

def seed():
    with engine.connect() as conn:
        print("=== 1.1 t_upload_resource_system ===")
        rows = conn.execute(text("""
            SELECT sys_id, sys_name, assigned_organization, belong_dept,
                   sys_func_type, if_managed, sys_status, record_name, master_data_code,
                   oper_type, oper_time
            FROM dx_assets_system_cq
        """)).fetchall()
        print(f"  源表 {len(rows)} 条")
        inserted = 0
        for r in rows:
            sys_code = str(r[0] or "")
            exist = conn.execute(text("SELECT id FROM t_upload_resource_system WHERE sys_code = :sc"), sc=sys_code).fetchone()
            if exist: continue
            conn.execute(text("""
                INSERT INTO t_upload_resource_system
                (sys_group_id, sys_code, sys_name, record_name, master_data_code,
                 org_unit, org_dept, status, sys_func_type, if_managed,
                 is_uploaded, is_compliant, oper_type, oper_time, create_time)
                VALUES (:gid, :sc, :sn, :rn, :mdc, :ou, :od, :st, :sft, :ifm,
                        '否', '否', :ot, :otm, NOW())
            """), gid=sys_code, sc=sys_code, sn=str(r[1] or ""),
                   rn=str(r[7] or ""), mdc=str(r[8] or ""),
                   ou=str(r[2] or ""), od=str(r[3] or ""),
                   st=str(r[6] or "建设中"), sft=str(r[4] or ""), ifm=str(r[5] or ""),
                   ot=str(r[9] or "0"), otm=str(r[10] or NOW_STR))
            inserted += 1
        conn.commit()
        print(f"  新增 {inserted} 条")

        print("=== 1.2 t_upload_mid_system ===")
        rows = conn.execute(text("""
            SELECT sys_id, sys_name, sub_sys_name, sys_classify,
                   assigned_organization, belong_dept,
                   contractor_unit, contractor_department, contractor_leader,
                   construction_vendor, management_leader,
                   operation_unit, operation_department,
                   launch_time, project_code, project_name, contract_code,
                   sys_func_type, if_managed, website, netins_sys_id, sys_status,
                   record_name, master_data_code, external_tag,
                   oper_type, oper_time
            FROM dx_assets_system_cq
        """)).fetchall()
        inserted = 0
        for r in rows:
            sys_code = str(r[0] or "")
            exist = conn.execute(text("SELECT id FROM t_upload_mid_system WHERE local_biz_id = :lb"), lb=sys_code).fetchone()
            if exist: continue
            conn.execute(text("""
                INSERT INTO t_upload_mid_system
                (local_biz_id, sys_code, sys_name, sub_sys_name, sys_classify,
                 record_name, master_data_code, org_unit, org_dept, 
                 sys_func_type, if_managed, status, online_time,
                 contractor_unit, contractor_department, contractor_leader,
                 construction_vendor, management_leader,
                 operation_unit, operation_department,
                 launch_time, project_code, project_name, contract_code, website,
                 netins_sys_id, external_tag, upload_flag,
                 audit_status, upload_status, oper_type, oper_time)
                VALUES (:lb, :sc, :sn, :ssn, :scl,
                        :rn, :mdc, :ou, :od,
                        :sft, :ifm, :st, :olt,
                        :cu, :cd, :cl, :cv, :ml, :opu, :opd,
                        :lt, :pjc, :pjn, :cc, :ws, :ns, :et, '1',
                        'pending', 'pending', :ot, :otm)
            """), lb=sys_code, sc=sys_code, sn=str(r[1] or ""), ssn=str(r[2] or ""),
                   scl=str(r[3] or ""), rn=str(r[22] or ""), mdc=str(r[23] or ""),
                   ou=str(r[4] or ""), od=str(r[5] or ""),
                   sft=str(r[17] or ""), ifm=str(r[18] or ""), st=str(r[21] or "建设中"),
                   olt=str(r[12] or ""),
                   cu=str(r[6] or ""), cd=str(r[7] or ""), cl=str(r[8] or ""),
                   cv=str(r[9] or ""), ml=str(r[10] or ""),
                   opu=str(r[11] or ""), opd=str(r[12] or ""),
                   lt=str(r[12] or ""), pjc=str(r[13] or ""), pjn=str(r[14] or ""),
                   cc=str(r[15] or ""), ws=str(r[19] or ""), ns=str(r[20] or ""),
                   et=str(r[24] or ""), ot=str(r[25] or "0"), otm=str(r[26] or NOW_STR))
            inserted += 1
        conn.commit()
        print(f"  新增 {inserted} 条")
