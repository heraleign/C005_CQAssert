from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class UploadResourceSystem(Base):
    __tablename__ = "t_upload_resource_system"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sys_group_id = Column(String(255), comment="集团唯一标识")
    sys_code = Column(String(255), comment="子系统编码")
    sys_name = Column(String(255))
    record_name = Column(String(255), comment="定级备案名称")
    master_data_code = Column(String(255), comment="集团主数据编码")
    org_unit = Column(String(255))
    org_dept = Column(String(255))
    biz_owner = Column(String(255))
    status = Column(String(50), default="建设中")
    sys_func_type = Column(String(10), comment="系统功能类型：1纯数据/2纯功能/3数据+功能")
    if_managed = Column(String(10), default="0", comment="是否需要纳管/盘点")
    online_time = Column(String(20))
    is_uploaded = Column(String(10), default="否")
    is_compliant = Column(String(10), default="否")
    non_compliant_reason = Column(String(2000))
    oper_type = Column(String(10))
    oper_time = Column(String(20))
    create_time = Column(DateTime, server_default=func.now())


class UploadResourceDatabase(Base):
    __tablename__ = "t_upload_resource_database"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    db_group_id = Column(String(255))
    sys_id = Column(BigInteger, ForeignKey("t_upload_resource_system.id"))
    db_name = Column(String(255))
    db_type = Column(String(255))
    is_compliant = Column(String(10), default="否")
    non_compliant_reason = Column(String(2000))
    oper_type = Column(String(10))
    oper_time = Column(String(20))


class UploadResourceTable(Base):
    __tablename__ = "t_upload_resource_table"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tbl_group_id = Column(String(255))
    db_id = Column(BigInteger, ForeignKey("t_upload_resource_database.id"))
    table_name_en = Column(String(255))
    table_name_cn = Column(String(255))
    table_desc = Column(String(1000))
    topic_domain = Column(String(255))
    sample_data = Column(Text)
    is_compliant = Column(String(10), default="否")
    non_compliant_reason = Column(String(2000))
    oper_type = Column(String(10))
    oper_time = Column(String(20))


class UploadResourceField(Base):
    __tablename__ = "t_upload_resource_field"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    field_group_id = Column(String(255))
    tbl_id = Column(BigInteger, ForeignKey("t_upload_resource_table.id"))
    field_name_en = Column(String(255))
    field_name_cn = Column(String(255))
    field_type = Column(String(255))
    is_compliant = Column(String(10), default="否")
    non_compliant_reason = Column(String(2000))
    oper_type = Column(String(10))
    oper_time = Column(String(20))


class UploadAssetLabel(Base):
    __tablename__ = "t_upload_asset_label"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    label_group_id = Column(String(255))
    label_name = Column(String(255))
    category_l1 = Column(String(255))
    category_l2 = Column(String(255))
    biz_definition = Column(String(2000))
    is_compliant = Column(String(10), default="否")
    non_compliant_reason = Column(String(2000))
    oper_type = Column(String(10))
    oper_time = Column(String(20))


class UploadAssetIndicator(Base):
    __tablename__ = "t_upload_asset_indicator"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    indicator_group_id = Column(String(255))
    indicator_name = Column(String(255))
    unit = Column(String(255))
    period = Column(String(255))
    is_compliant = Column(String(10), default="否")
    non_compliant_reason = Column(String(2000))
    oper_type = Column(String(10))
    oper_time = Column(String(20))


class UploadAssetApi(Base):
    __tablename__ = "t_upload_asset_api"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    api_group_id = Column(String(255))
    api_name = Column(String(255))
    api_url = Column(String(1000))
    method = Column(String(20))
    is_compliant = Column(String(10), default="否")
    non_compliant_reason = Column(String(2000))
    oper_type = Column(String(10))
    oper_time = Column(String(20))


class UploadAssetProduct(Base):
    __tablename__ = "t_upload_asset_product"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_group_id = Column(String(255))
    product_name = Column(String(255))
    biz_domain = Column(String(255))
    category = Column(String(255))
    is_effective = Column(String(10))
    shelf_time = Column(String(20))
    expire_time = Column(String(20))
    is_compliant = Column(String(10), default="否")
    non_compliant_reason = Column(String(2000))
    oper_type = Column(String(10))
    oper_time = Column(String(20))


class UploadMultimodalUnstructured(Base):
    __tablename__ = "t_upload_multimodal_unstructured"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ust_id = Column(String(255))
    file_name_cn = Column(String(255))
    file_name_en = Column(String(255))
    sys_name = Column(String(255))
    is_compliant = Column(String(10), default="否")
    non_compliant_reason = Column(String(2000))
    oper_type = Column(String(10))
    oper_time = Column(String(20))


class AuditRule(Base):
    __tablename__ = "t_audit_rule"
    rule_id = Column(BigInteger, primary_key=True, autoincrement=True)
    rule_code = Column(String(50), nullable=False, unique=True)
    rule_name = Column(String(255), nullable=False)
    rule_desc = Column(String(1000))
    rule_type = Column(String(50), comment="非空/格式/一致性/数量")
    target_asset = Column(String(50), comment="适用对象")
    expression = Column(Text, comment="规则表达式/伪代码")
    is_enabled = Column(String(10), default="是")
    create_time = Column(DateTime, server_default=func.now())


class AuditResult(Base):
    __tablename__ = "t_audit_result"
    result_id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_type = Column(String(50), nullable=False)
    asset_id = Column(String(255), nullable=False)
    rule_code = Column(String(50))
    is_pass = Column(String(10))
    reason = Column(String(2000))
    period_type = Column(String(10), default="日", comment="账期类型：日/月")
    period = Column(String(20), comment="账期：日账期如20260511，月账期如202605")
    check_time = Column(DateTime, server_default=func.now())


class MetadataCompleteLog(Base):
    __tablename__ = "t_metadata_complete_log"
    log_id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_type = Column(String(50))
    asset_id = Column(String(255))
    complete_type = Column(String(50), comment="表中文名/简介/主题域/字段中文名")
    before_value = Column(String(1000))
    after_value = Column(String(1000))
    source = Column(String(50), default="AI")
    operate_time = Column(DateTime, server_default=func.now())


class AssetHandoverLog(Base):
    __tablename__ = "t_asset_handover_log"
    log_id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_type = Column(String(50), default="系统")
    asset_id = Column(String(255))
    from_user = Column(String(100))
    to_user = Column(String(100))
    operator = Column(String(100))
    operate_time = Column(DateTime, server_default=func.now())
    remark = Column(String(500))
