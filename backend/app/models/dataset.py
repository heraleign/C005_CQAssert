from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Text, DECIMAL, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class DatasetMetadata(Base):
    __tablename__ = "t_dataset_metadata"

    dataset_id = Column(String(255), primary_key=True, comment="数据集唯一标识")
    dataset_name = Column(String(255), nullable=False, comment="数据集名称")
    dataset_type = Column(String(255), nullable=False, comment="原始数据/知识库/语料/提示词")
    biz_owner = Column(String(255), nullable=False, comment="业务负责人")
    biz_owner_phone = Column(String(255), nullable=False, comment="业务负责人联系电话")
    contact_name = Column(String(255), nullable=False, comment="数据集接口人姓名")
    contact_phone = Column(String(255), nullable=False, comment="数据集接口人联系方式")
    org_unit = Column(String(255), nullable=False, comment="所属单位")
    org_dept = Column(String(255), nullable=False, comment="所属部门")
    biz_scene = Column(String(255), nullable=False, comment="业务场景名称")
    biz_sub_scene = Column(String(255), nullable=False, comment="业务子场景名称")
    application = Column(String(255), nullable=False, comment="应用")
    work_order_no = Column(String(255), nullable=False, comment="工单号")

    # 存储信息组
    expected_size = Column(String(255), nullable=False, comment="预计数据集大小")
    actual_size = Column(String(255), comment="实际采集大小")
    storage_location = Column(String(255), comment="存储位置")
    is_in_lake = Column(String(10), nullable=False, comment="是否入湖")
    not_in_lake_reason = Column(Text, comment="不入湖原因")
    resource_pool = Column(String(255), nullable=False, comment="数据所在资源池")
    network_type = Column(String(255), nullable=False, comment="网络类型")
    host_ip = Column(Text, nullable=False, comment="主机IP")

    # 结构属性信息组
    dataset_format = Column(String(255), nullable=False, comment="数据集格式")
    source_system = Column(String(255), nullable=False, comment="来源系统")
    update_freq = Column(String(255), nullable=False, comment="更新频率")
    is_sensitive = Column(String(10), nullable=False, comment="是否敏感")
    sensitive_info = Column(Text, comment="敏感数据信息")
    share_requirement = Column(Text, nullable=False, comment="内部共享要求")
    use_structured = Column(String(10), nullable=False, comment="是否使用结构化数据")
    dataset_scope = Column(String(255), comment="数据集范围")
    data_level = Column(String(50), nullable=False, comment="数据层级")

    # 知识库扩展
    kb_type = Column(String(255), comment="知识库数据集类型")
    kb_modality = Column(String(255), comment="知识库数据集模态")
    kb_expected_scale = Column(String(255), comment="知识库预期规模")
    kb_actual_scale = Column(String(255), comment="知识库实际规模")

    # 语料扩展
    corpus_type = Column(String(255), comment="语料数据集类型")
    corpus_modality = Column(String(255), comment="语料数据集模态")
    corpus_expected_scale = Column(String(255), comment="语料预期规模")
    corpus_actual_scale = Column(String(255), comment="语料实际规模")
    is_annotated = Column(String(10), comment="语料是否标注")
    annotation_labels = Column(Text, comment="语料标注标签")
    annotation_method = Column(String(255), comment="语料标注方式")
    annotator_type = Column(String(255), comment="语料标注人员类型")

    # 提示词扩展
    prompt_expected_scale = Column(String(255), comment="提示词预期规模")
    prompt_actual_scale = Column(String(255), comment="提示词实际规模")
    prompt_target_model = Column(String(255), comment="提示词目标模型")
    prompt_task = Column(String(255), comment="提示词适用任务")
    prompt_app_sys = Column(String(255), comment="提示词应用系统")

    # 生命周期组
    create_time = Column(String(20), nullable=False, comment="数据集创建时间")
    update_time = Column(String(20), nullable=False, comment="最新更新时间")
    version = Column(String(50), nullable=False, comment="版本信息")
    status = Column(String(50), nullable=False, comment="状态标识")
    build_unit = Column(String(255), nullable=False, comment="数据集建设单位")
    build_target = Column(Text, comment="数据集建设目标")
    build_plan = Column(Text, comment="数据集建设计划")
    dataset_desc = Column(Text, comment="数据集描述")
    scene_online_time = Column(String(20), nullable=False, comment="子场景实际/预计上线时间")
    sample_data = Column(Text, comment="样例数据")

    # 稽核合规字段
    is_compliant = Column(String(10), default="否", comment="是否合规")

    # 同步字段
    oper_type = Column(String(10), comment="0新增/1修改/2删除")
    oper_time = Column(String(20), comment="操作时间")
    sync_time = Column(DateTime, server_default=func.now(), comment="同步时间")

    qualities = relationship("DatasetQuality", back_populates="dataset", cascade="all, delete-orphan")


class DatasetQuality(Base):
    __tablename__ = "t_dataset_quality"

    quality_id = Column(BigInteger, primary_key=True, autoincrement=True)
    dataset_id = Column(String(255), ForeignKey("t_dataset_metadata.dataset_id"), nullable=False)
    quality_dim = Column(String(100), nullable=False, comment="质量维度")
    quality_score = Column(DECIMAL(5, 2), comment="质量得分")
    quality_desc = Column(String(500), comment="质量描述")
    check_time = Column(DateTime, server_default=func.now())

    dataset = relationship("DatasetMetadata", back_populates="qualities")


class DatasetCatalog(Base):
    __tablename__ = "t_dataset_catalog"

    catalog_id = Column(String(255), primary_key=True)
    catalog_name = Column(String(255), nullable=False)
    parent_id = Column(String(255), comment="父节点")
    catalog_level = Column(Integer, nullable=False, comment="层级")
    catalog_type = Column(String(50), comment="领域/场景/细类")
    sort_order = Column(Integer, default=0)
    create_time = Column(DateTime, server_default=func.now())
    status = Column(String(20), default="1")


class MetaFieldConfig(Base):
    """元模型字段配置表 - 支持管理员在线配置字段定义、必填规则、枚举值、展示分组"""
    __tablename__ = "t_meta_field_config"

    field_id = Column(String(255), primary_key=True, comment="字段英文标识")
    field_name = Column(String(255), nullable=False, comment="字段中文名")
    field_group = Column(String(50), nullable=False, comment="所属分组: 基础信息组/存储信息组/结构属性信息组/生命周期组")
    field_type = Column(String(50), nullable=False, comment="字段类型: VARCHAR/TEXT/SELECT/MULTI_SELECT/BOOLEAN/DATE")
    source_type = Column(String(50), default="manual", comment="来源: manual/system/enum")
    is_required = Column(String(10), default="否", comment="是否必填")
    enum_values = Column(Text, comment="枚举值JSON数组, 如 [\"原始数据\",\"知识库\",\"语料\",\"提示词\"]")
    default_value = Column(String(500), comment="默认值")
    max_length = Column(Integer, comment="最大长度")
    sort_order = Column(Integer, default=0, comment="组内排序号")
    condition_expr = Column(Text, comment="条件必填JSON, 如 {\"field\":\"dataset_type\",\"eq\":\"知识库\",\"required_fields\":[\"kb_type\",\"kb_modality\"]}")
    display_width = Column(Integer, default=2, comment="展示宽度列数: 1=半行/2=整行")
    is_active = Column(String(10), default="是", comment="是否启用")
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())


class UploadMultimodalDataset(Base):
    __tablename__ = "t_upload_multimodal_dataset"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ust_id = Column(String(255), nullable=False, comment="文件唯一标识")
    sys_name = Column(String(255))
    sys_id = Column(String(255))
    asset_type = Column(String(255), default="高质量数据集")
    asset_format = Column(String(255))
    data_amount = Column(String(255))
    data_size = Column(String(255))
    total_data_size = Column(String(255))
    asset_desc = Column(String(255))
    update_freq = Column(String(255))
    scenario_tag = Column(String(255))
    is_classified = Column(String(10))
    is_sharable = Column(String(10))
    assignee_name = Column(String(255))
    assignee_phone = Column(String(255))
    data_level = Column(String(50))
    oper_type = Column(String(10))
    oper_time = Column(String(20))

    dataset_type = Column(String(255))
    biz_scene = Column(String(255))
    biz_sub_scene = Column(String(255))
    kb_type = Column(String(255))
    kb_modality = Column(String(255))
    corpus_type = Column(String(255))
    corpus_modality = Column(String(255))
    is_in_lake = Column(String(10))
    share_requirement = Column(Text)

    is_compliant = Column(String(10), default="否")
    non_compliant_reason = Column(Text)
    upload_status = Column(String(20), default="待上传")
    upload_time = Column(DateTime)
