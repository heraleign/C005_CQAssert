"""集团上报流程 - 中间表及支持表模型"""

from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Text, JSON, SmallInteger, func
from app.database import Base


class UploadMidSystem(Base):
    """资源类-系统中间表"""
    __tablename__ = "t_upload_mid_system"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    local_biz_id = Column(String(255), nullable=False, unique=True, comment="本地业务唯一标识")

    group_unique_id = Column(String(255), comment="集团唯一标识")
    group_id_generated = Column(SmallInteger, default=0, comment="0=未生成 1=已生成")

    sys_code = Column(String(255), comment="子系统编码")
    sys_name = Column(String(255), comment="系统名称")
    record_name = Column(String(255), comment="定级备案名称")
    master_data_code = Column(String(255), comment="集团主数据编码")
    org_unit = Column(String(255), comment="所属单位")
    org_dept = Column(String(255), comment="所属部门")
    biz_owner = Column(String(255), comment="业务负责人")
    status = Column(String(50), default="建设中", comment="系统状态")
    sys_func_type = Column(String(10), comment="系统功能类型：1纯数据/2纯功能/3数据+功能")
    if_managed = Column(String(10), default="0", comment="是否需要纳管/盘点")
    online_time = Column(String(20), comment="上线时间")

    audit_status = Column(String(20), default="pending", comment="pending/pass/fail")
    audit_time = Column(DateTime, comment="稽核时间")
    non_compliant_reason = Column(String(2000), comment="不合规原因")
    upload_status = Column(String(20), default="pending", comment="pending/synced/uploaded/failed")
    mid_modify_flag = Column(SmallInteger, default=0, comment="0=未修改 1=已在中间表修改")
    last_sync_time = Column(DateTime, comment="最后同步时间")
    oper_type = Column(String(10), comment="0新增/1修改/2删除")
    oper_time = Column(String(20), comment="操作时间")


class UploadMidDatabase(Base):
    """资源类-数据库中间表"""
    __tablename__ = "t_upload_mid_database"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    local_biz_id = Column(String(255), nullable=False, unique=True, comment="本地业务唯一标识")

    group_unique_id = Column(String(255), comment="集团唯一标识")
    group_id_generated = Column(SmallInteger, default=0)

    sys_local_biz_id = Column(String(255), comment="所属系统本地标识")
    db_name = Column(String(255), comment="数据库名")
    db_type = Column(String(255), comment="数据库类型")

    audit_status = Column(String(20), default="pending")
    audit_time = Column(DateTime)
    non_compliant_reason = Column(String(2000))
    upload_status = Column(String(20), default="pending")
    mid_modify_flag = Column(SmallInteger, default=0)
    last_sync_time = Column(DateTime)
    oper_type = Column(String(10))
    oper_time = Column(String(20))


class UploadMidTable(Base):
    """资源类-表中间表"""
    __tablename__ = "t_upload_mid_table"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    local_biz_id = Column(String(255), nullable=False, unique=True, comment="本地业务唯一标识")

    group_unique_id = Column(String(255), comment="集团唯一标识")
    group_id_generated = Column(SmallInteger, default=0)

    db_local_biz_id = Column(String(255), comment="所属数据库本地标识")
    table_name_en = Column(String(255), comment="表英文名")
    table_name = Column(String(255), comment="表中文名")
    table_introduct = Column(String(1000), comment="表简介")
    table_domain = Column(String(255), comment="主题域")
    sample_data = Column(Text, comment="样例数据")
    lake_data_type = Column(String(10), comment="入湖数据类型")
    premium_model_in_lake = Column(String(10), comment="数据入湖前是否精模型")
    uploaded_to_big_lake = Column(String(10), comment="是否已入湖")
    is_shared = Column(String(10), comment="是否共享")
    create_time_col = Column(String(20), comment="创建时间列")
    is_partitioned = Column(String(10), comment="是否分区表")

    audit_status = Column(String(20), default="pending")
    audit_time = Column(DateTime)
    non_compliant_reason = Column(String(2000))
    upload_status = Column(String(20), default="pending")
    mid_modify_flag = Column(SmallInteger, default=0)
    last_sync_time = Column(DateTime)
    oper_type = Column(String(10))
    oper_time = Column(String(20))


class UploadMidField(Base):
    """资源类-字段中间表"""
    __tablename__ = "t_upload_mid_field"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    local_biz_id = Column(String(255), nullable=False, unique=True, comment="本地业务唯一标识")

    group_unique_id = Column(String(255), comment="集团唯一标识")
    group_id_generated = Column(SmallInteger, default=0)

    tbl_local_biz_id = Column(String(255), comment="所属表本地标识")
    field_name_en = Column(String(255), comment="字段英文名")
    field_name_cn = Column(String(255), comment="字段中文名")
    field_type = Column(String(255), comment="字段类型")

    audit_status = Column(String(20), default="pending")
    audit_time = Column(DateTime)
    non_compliant_reason = Column(String(2000))
    upload_status = Column(String(20), default="pending")
    mid_modify_flag = Column(SmallInteger, default=0)
    last_sync_time = Column(DateTime)
    oper_type = Column(String(10))
    oper_time = Column(String(20))


# ─── 支持表 ─────────────────────────────────────────────

class MidFieldGenRule(Base):
    """中间表字段自动生成规则配置"""
    __tablename__ = "t_mid_field_gen_rule"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_type = Column(String(50), comment="资产类型")
    target_field = Column(String(100), comment="目标字段")
    rule_type = Column(String(50), comment="COPY/CONCAT/ENUM_MAP/FORMULA")
    source_fields = Column(JSON, comment="来源字段列表")
    rule_expr = Column(String(1000), comment="规则表达式")
    trigger_condition = Column(String(500), comment="触发条件")
    is_enabled = Column(SmallInteger, default=1)
    remark = Column(String(500))


class MetadataFieldMapping(Base):
    """本地元数据到中间表字段映射"""
    __tablename__ = "t_metadata_field_mapping"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_type = Column(String(50), comment="资产类型")
    local_field = Column(String(100), comment="本地字段名")
    mid_field = Column(String(100), comment="中间表字段名")
    transform_rule = Column(String(500), comment="转换规则")
    is_enabled = Column(SmallInteger, default=1)


class MidFieldModifyLog(Base):
    """中间表字段修改日志"""
    __tablename__ = "t_mid_field_modify_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_type = Column(String(50))
    local_biz_id = Column(String(255))
    field_name = Column(String(100))
    old_value = Column(String(2000))
    new_value = Column(String(2000))
    operator = Column(String(100))
    modify_time = Column(DateTime, server_default=func.now())
    modify_reason = Column(String(500))


class UploadOperationLog(Base):
    """上传操作日志"""
    __tablename__ = "t_upload_operation_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    operation_type = Column(String(50), comment="SYNC/AUDIT/MID_MODIFY/SYNC_TO_RESULT/UPLOAD")
    asset_type = Column(String(50))
    scope_type = Column(String(50), comment="SYSTEM/DATABASE/TABLE/FIELD/ALL")
    scope_id = Column(String(255), comment="操作范围ID")
    operator = Column(String(100))
    operate_time = Column(DateTime, server_default=func.now())
    operation_detail = Column(Text, comment="操作详情JSON")
    result = Column(String(20), comment="SUCCESS/FAIL/PARTIAL")
    result_msg = Column(String(500))


class UploadResultTable(Base):
    """集团上传中间结果表"""
    __tablename__ = "t_upload_result_table"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_type = Column(String(50))
    local_biz_id = Column(String(255), unique=True, comment="关联中间表")
    group_unique_id = Column(String(255), comment="集团唯一标识")
    data_snapshot = Column(Text, comment="数据快照JSON")
    sync_to_result_time = Column(DateTime, comment="同步到结果表时间")
    upload_status = Column(String(20), default="pending", comment="pending/uploaded/failed")
    upload_time = Column(DateTime)
    upload_batch_no = Column(String(50), comment="上传批次号")


class ClassifyMid(Base):
    """分级分类中间表"""
    __tablename__ = "t_classify_mid"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    local_biz_id = Column(String(255), unique=True)
    asset_type = Column(String(50))
    data_level = Column(String(10), comment="数据级别1-5")
    data_category = Column(String(50), comment="数据分类")
    classify_status = Column(String(20), default="pending", comment="valid/invalid/pending")
    classify_time = Column(DateTime)
    source = Column(String(50), comment="来源")


class MetadataCompleteTask(Base):
    """元数据补全任务"""
    __tablename__ = "t_metadata_complete_task"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_type = Column(String(50), comment="SYSTEM/DATABASE/TABLE/FIELD")
    scope_id = Column(String(255))
    scope_name = Column(String(255))
    complete_fields = Column(JSON, comment="待补全字段列表")
    total_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    task_status = Column(String(20), default="pending", comment="pending/running/done/failed")
    operator = Column(String(100))
    create_time = Column(DateTime, server_default=func.now())
    finish_time = Column(DateTime)
