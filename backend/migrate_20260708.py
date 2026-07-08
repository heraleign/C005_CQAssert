"""数据库迁移脚本 - 为中间表和集团结果表添加新字段"""
from app.database import engine, SessionLocal
from sqlalchemy import text

MIGRATIONS = [
    # t_upload_mid_system - 新增字段
    "ALTER TABLE t_upload_mid_system ADD COLUMN create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'",
    "ALTER TABLE t_upload_mid_system ADD COLUMN update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'",
    "ALTER TABLE t_upload_mid_system ADD COLUMN is_primary TINYINT DEFAULT 1 COMMENT '1=主系统 0=副系统'",
    "ALTER TABLE t_upload_mid_system ADD COLUMN primary_system_id VARCHAR(255) COMMENT '所属主系统的local_biz_id'",
    "ALTER TABLE t_upload_mid_system ADD COLUMN primary_sys_name VARCHAR(255) COMMENT '所属主系统的名称'",
    "ALTER TABLE t_upload_mid_system ADD COLUMN primary_sys_code VARCHAR(255) COMMENT '所属主系统的编码'",
    "ALTER TABLE t_upload_mid_system ADD COLUMN group_uploaded TINYINT DEFAULT 0 COMMENT '0=未上传集团 1=已上传集团'",

    # t_upload_mid_database - 新增字段
    "ALTER TABLE t_upload_mid_database ADD COLUMN create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'",
    "ALTER TABLE t_upload_mid_database ADD COLUMN update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'",

    # t_upload_mid_table - 新增字段
    "ALTER TABLE t_upload_mid_table ADD COLUMN create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'",
    "ALTER TABLE t_upload_mid_table ADD COLUMN update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'",

    # t_upload_mid_field - 新增字段
    "ALTER TABLE t_upload_mid_field ADD COLUMN create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'",
    "ALTER TABLE t_upload_mid_field ADD COLUMN update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'",

    # t_upload_group_result - 新增字段
    "ALTER TABLE t_upload_group_result ADD COLUMN record_status VARCHAR(20) DEFAULT 'active' COMMENT 'active=有效 disabled=已禁用'",
]


def run_migrations():
    with engine.connect() as conn:
        for i, sql in enumerate(MIGRATIONS):
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"[OK] ({i+1}/{len(MIGRATIONS)}) {sql[:60]}...")
            except Exception as e:
                error_msg = str(e)
                if "Duplicate column" in error_msg or "already exists" in error_msg:
                    print(f"[SKIP] ({i+1}/{len(MIGRATIONS)}) 字段已存在: {sql[:60]}...")
                else:
                    print(f"[ERROR] ({i+1}/{len(MIGRATIONS)}) {e}")
    print("迁移完成")


if __name__ == "__main__":
    run_migrations()
