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
    sub_sys_name = Column(String(255), comment="子系统名称")
    sys_introduct = Column(String(2000), comment="系统简介")
    sys_classify = Column(String(255), comment="系统分类")
    record_name = Column(String(255), comment="定级备案名称")
    master_data_code = Column(String(255), comment="集团主数据编码")
    org_unit = Column(String(255), comment="所属单位")
    org_dept = Column(String(255), comment="所属部门")
    biz_owner = Column(String(255), comment="业务负责人")
    status = Column(String(50), default="建设中", comment="系统状态")
    sys_func_type = Column(String(10), comment="系统功能类型：1纯数据/2纯功能/3数据+功能")
    if_managed = Column(String(10), default="0", comment="是否需要纳管/盘点")
    online_time = Column(String(20), comment="上线时间")

    # 承建信息
    contractor_unit = Column(String(255), comment="承建单位")
    contractor_department = Column(String(255), comment="承建部门")
    contractor_leader = Column(String(255), comment="承建负责人姓名")
    contractor_leader_phone = Column(String(255), comment="承建负责人手机")
    contractor_leader_email = Column(String(255), comment="承建负责人邮箱")
    construction_vendor = Column(String(255), comment="承建厂商")

    # 管理信息
    management_leader = Column(String(255), comment="系统管理负责人姓名")
    management_leader_phone = Column(String(255), comment="系统管理负责人电话")
    management_leader_email = Column(String(255), comment="系统管理负责人邮箱")

    # 运营信息
    operation_unit = Column(String(255), comment="运营单位")
    operation_department = Column(String(255), comment="运营部门")
    operation_leader = Column(String(255), comment="运营负责人姓名")
    operation_leader_phone = Column(String(255), comment="运营负责人手机")
    operation_leader_email = Column(String(255), comment="运营负责人邮箱")

    # 其他集团字段
    launch_time = Column(String(255), comment="系统上线时间")
    project_code = Column(String(255), comment="所属工程项目编码")
    project_name = Column(String(255), comment="所属工程项目名称")
    contract_code = Column(String(255), comment="合同编码或自建系统编码")
    website = Column(String(255), comment="前台登录地址")
    netins_sys_id = Column(String(255), comment="网信安系统编码")
    external_tag = Column(String(255), comment="是否对外产数项目")

    upload_flag = Column(String(10), default="1", comment="是否上传: 1上传 0不上传")
    merge_flag = Column(SmallInteger, default=0, comment="0=未合并 1=已合并")

    audit_status = Column(String(20), default="pending", comment="pending/pass/fail")
    audit_time = Column(DateTime, comment="稽核时间")
    non_compliant_reason = Column(String(2000), comment="不合规原因")
    upload_status = Column(String(20), default="pending", comment="pending/synced/uploaded/failed")
    mid_modify_flag = Column(SmallInteger, default=0, comment="0=未修改 1=已在中间表修改")
    last_sync_time = Column(DateTime, comment="最后同步时间")
    oper_type = Column(String(10), comment="0新增/1修改/2删除")
    oper_time = Column(String(20), comment="操作时间")

    # 新增字段：创建/更新时间（评审意见1、3）
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 新增字段：合并系统标识（评审意见5）
    is_primary = Column(SmallInteger, default=1, comment="1=主系统 0=副系统")
    primary_system_id = Column(String(255), comment="所属主系统的local_biz_id，副系统使用")
    primary_sys_name = Column(String(255), comment="所属主系统的名称，副系统使用")
    primary_sys_code = Column(String(255), comment="所属主系统的编码，副系统使用")

    # 新增字段：是否已上传集团（评审意见11）
    group_uploaded = Column(SmallInteger, default=0, comment="0=未上传集团 1=已上传集团")


class UploadMidDatabase(Base):
    """资源类-数据库中间表"""
    __tablename__ = "t_upload_mid_database"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    local_biz_id = Column(String(255), nullable=False, unique=True, comment="本地业务唯一标识")

    group_unique_id = Column(String(255), comment="集团唯一标识")
    group_id_generated = Column(SmallInteger, default=0)

    sys_local_biz_id = Column(String(255), comment="所属系统本地标识")
    sys_code = Column(String(255), comment="归属系统编码")
    db_name = Column(String(255), comment="数据库名")
    db_type = Column(String(255), comment="数据库类型")
    db_version = Column(String(255), comment="数据库版本")
    db_ip = Column(String(255), comment="数据库IP")
    db_port = Column(String(255), comment="数据库端口")

    upload_flag = Column(String(10), default="1", comment="是否上传: 1上传 0不上传")

    audit_status = Column(String(20), default="pending")
    audit_time = Column(DateTime)
    non_compliant_reason = Column(String(2000))
    upload_status = Column(String(20), default="pending")
    mid_modify_flag = Column(SmallInteger, default=0)
    last_sync_time = Column(DateTime)
    oper_type = Column(String(10))
    oper_time = Column(String(20))

    # 新增字段：创建/更新时间
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")


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

    # 集团上传扩展字段
    scenario_tag = Column(String(255), comment="应用场景标签")
    lake_data_type = Column(String(255), comment="湖内/湖外数据（本单位）")
    in_unit_lakes = Column(String(255), comment="是否已入各单位湖")
    premium_model_in_lake = Column(String(255), comment="是否各单位湖内精品模型")
    uploaded_to_big_lake = Column(String(255), comment="是否已上传至集团大数据湖")
    external_unique_identifier = Column(String(255), comment="湖外表的唯一标识")
    is_shareable = Column(String(255), comment="是否可共享")
    is_shared = Column(String(255), comment="是否已共享")
    sharing_channel = Column(String(255), comment="共享渠道")
    tech_contact = Column(String(255), comment="技术联系人")
    tech_contact_phone = Column(String(255), comment="技术人员电话")
    data_aggregation_method = Column(String(255), comment="数据汇聚方式")
    data_collection_time = Column(String(255), comment="数据采集时间")
    aggregation_granularity = Column(String(255), comment="汇聚粒度")
    is_incremental_or_full = Column(String(255), comment="增量/全量")
    storage_period = Column(String(255), comment="存储周期")
    reference_count = Column(String(255), comment="引用次数")
    sub_count = Column(String(255), comment="订阅次数")
    col_count = Column(String(255), comment="收藏次数")
    access_count = Column(String(255), comment="访问次数")
    table_level = Column(String(255), comment="表的分级")
    tabtable_category = Column(String(255), comment="表的分类")
    layer_level = Column(String(255), comment="层级")
    business_domain = Column(String(255), comment="业务域")
    source_system = Column(String(255), comment="数据来源系统")
    is_partitioned = Column(String(255), comment="是否分区表")
    data_quality = Column(String(255), comment="数据质量")
    industry_catalog = Column(String(255), comment="行业数据目录")
    industry_expert = Column(String(255), comment="行业专家")
    group_gather_tbname = Column(String(255), comment="集团数据湖采集接口层表名")

    upload_flag = Column(String(10), default="1", comment="是否上传: 1上传 0不上传")

    audit_status = Column(String(20), default="pending")
    audit_time = Column(DateTime)
    non_compliant_reason = Column(String(2000))
    upload_status = Column(String(20), default="pending")
    mid_modify_flag = Column(SmallInteger, default=0)
    last_sync_time = Column(DateTime)
    oper_type = Column(String(10))
    oper_time = Column(String(20))

    # 新增字段：创建/更新时间
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")


class UploadMidField(Base):
    """资源类-字段中间表"""
    __tablename__ = "t_upload_mid_field"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    local_biz_id = Column(String(255), nullable=False, unique=True, comment="本地业务唯一标识")

    group_unique_id = Column(String(255), comment="集团唯一标识")
    group_id_generated = Column(SmallInteger, default=0)

    tbl_local_biz_id = Column(String(255), comment="所属表本地标识")
    db_local_biz_id = Column(String(255), comment="所属数据库本地标识")
    field_name_en = Column(String(255), comment="字段英文名")
    field_name_cn = Column(String(255), comment="字段中文名")
    field_type = Column(String(255), comment="字段类型")
    field_length = Column(String(255), comment="字段长度")
    field_desc = Column(String(2000), comment="字段描述")
    process_caliber_desc = Column(String(255), comment="加工口径说明")

    is_primary_key = Column(String(255), comment="是否主键")
    is_foreign_key = Column(String(255), comment="是否外键")
    is_shareable = Column(String(255), comment="是否可共享")
    field_category = Column(String(255), comment="字段分类")
    sensitivity_level = Column(String(255), comment="敏感级别")
    sensitive_field_elements = Column(String(255), comment="字段的敏感元素")
    is_desensitized = Column(String(255), comment="是否需脱敏")
    value_definition = Column(String(255), comment="取值定义")
    mdm_field = Column(String(255), comment="引用主数据字段")
    mdm_type = Column(String(255), comment="引用主数据类型")

    audit_status = Column(String(20), default="pending")
    audit_time = Column(DateTime)
    non_compliant_reason = Column(String(2000))
    upload_status = Column(String(20), default="pending")
    mid_modify_flag = Column(SmallInteger, default=0)
    last_sync_time = Column(DateTime)
    oper_type = Column(String(10))
    oper_time = Column(String(20))

    # 新增字段：创建/更新时间
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")


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
    """集团上传中间结果表（旧，保留兼容）"""
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


# ─── 新增：中间结果表（带账期） ─────────────────────────

class UploadResultMid(Base):
    """中间结果表 - 带账期，每月20日全量稽核"""
    __tablename__ = "t_upload_result_mid"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_type = Column(String(50), comment="资产类型: system/database/table/field")
    mid_local_biz_id = Column(String(255), comment="关联中间表本地标识")
    group_unique_id = Column(String(255), comment="集团唯一标识")
    bill_month = Column(String(10), comment="账期 YYYYMM")
    result_status = Column(String(20), default="pending", comment="pending/audited/uploaded/merged")
    audit_status = Column(String(20), default="pending", comment="pending/pass/fail")
    audit_time = Column(DateTime, comment="稽核时间")
    non_compliant_reason = Column(String(2000), comment="不合规原因")
    data_snapshot = Column(Text, comment="数据快照JSON")
    merge_flag = Column(SmallInteger, default=0, comment="0=未合并 1=已合并")
    sync_time = Column(DateTime, comment="同步到中间结果表时间")
    upload_time = Column(DateTime, comment="上传到集团结果表时间")
    oper_type = Column(String(10), comment="0新增/1修改")
    oper_time = Column(String(20))


class UploadGroupResult(Base):
    """集团结果表 - 全量无账期"""
    __tablename__ = "t_upload_group_result"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_type = Column(String(50), comment="资产类型")
    group_unique_id = Column(String(255), nullable=False, comment="集团唯一标识")
    bill_month = Column(String(10), comment="上传账期 YYYYMM")
    data_snapshot = Column(Text, comment="数据全量快照JSON")
    sync_time = Column(DateTime, comment="同步时间")
    oper_type = Column(String(10), comment="操作类型")
    oper_time = Column(String(20), comment="操作时间")

    # 新增字段：记录状态（评审意见4）
    record_status = Column(String(20), default="active", comment="active=有效 disabled=已禁用")


class ExcludeMark(Base):
    """排除上传标记"""
    __tablename__ = "t_exclude_mark"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_type = Column(String(50), comment="资产类型: database/table")
    asset_id = Column(String(255), comment="资产本地标识")
    asset_name = Column(String(255), comment="资产名称")
    sys_id = Column(String(255), comment="归属系统标识")
    sys_name = Column(String(255), comment="归属系统名称")
    exclude_reason = Column(String(500), comment="排除原因")
    operator = Column(String(100))
    create_time = Column(DateTime, server_default=func.now())


class MergeLog(Base):
    """合并操作日志"""
    __tablename__ = "t_merge_log"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_type = Column(String(50), comment="资产类型")
    target_local_biz_id = Column(String(255), comment="合并目标标识")
    source_local_biz_ids = Column(Text, comment="合并来源标识列表(JSON数组)")
    merge_reason = Column(String(500), comment="合并原因")
    merge_detail = Column(Text, comment="合并详情JSON")
    operator = Column(String(100))
    create_time = Column(DateTime, server_default=func.now())


class SyncDefaultValue(Base):
    """同步默认值配置"""
    __tablename__ = "t_sync_default_value"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    asset_type = Column(String(50), comment="资产类型")
    field_name = Column(String(100), comment="字段名")
    default_value = Column(String(500), comment="默认值")
    is_enabled = Column(SmallInteger, default=1, comment="是否启用")
    remark = Column(String(500))


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
