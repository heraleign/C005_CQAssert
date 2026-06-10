from typing import Optional, List, Any
from pydantic import BaseModel, field_serializer


class DatasetQualitySchema(BaseModel):
    quality_id: Optional[int] = None
    quality_dim: str
    quality_score: Optional[float] = None
    quality_desc: Optional[str] = None

    class Config:
        from_attributes = True


class DatasetMetadataCreate(BaseModel):
    dataset_id: str
    dataset_name: str
    dataset_type: str
    biz_owner: str
    biz_owner_phone: str
    contact_name: str
    contact_phone: str
    org_unit: str
    org_dept: str
    biz_scene: str
    biz_sub_scene: str
    application: str
    work_order_no: str

    expected_size: str
    is_in_lake: str
    resource_pool: str
    network_type: str
    host_ip: str
    storage_location: Optional[str] = None
    not_in_lake_reason: Optional[str] = None
    actual_size: Optional[str] = None

    dataset_format: str
    source_system: str
    update_freq: str
    is_sensitive: str
    sensitive_info: Optional[str] = None
    share_requirement: str
    use_structured: str
    dataset_scope: Optional[str] = None
    data_level: str

    kb_type: Optional[str] = None
    kb_modality: Optional[str] = None
    kb_expected_scale: Optional[str] = None
    corpus_type: Optional[str] = None
    corpus_modality: Optional[str] = None
    corpus_expected_scale: Optional[str] = None
    is_annotated: Optional[str] = None
    annotation_labels: Optional[str] = None
    annotation_method: Optional[str] = None
    annotator_type: Optional[str] = None
    prompt_expected_scale: Optional[str] = None
    prompt_target_model: Optional[str] = None
    prompt_task: Optional[str] = None
    prompt_app_sys: Optional[str] = None

    create_time: str
    version: str = "v1.0.0"
    status: str = "在用"
    build_unit: str
    build_target: Optional[str] = None
    build_plan: Optional[str] = None
    dataset_desc: Optional[str] = None
    scene_online_time: str
    sample_data: Optional[str] = None


class DatasetMetadataUpdate(BaseModel):
    dataset_name: Optional[str] = None
    dataset_type: Optional[str] = None
    biz_owner: Optional[str] = None
    biz_owner_phone: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    org_unit: Optional[str] = None
    org_dept: Optional[str] = None
    biz_scene: Optional[str] = None
    biz_sub_scene: Optional[str] = None
    application: Optional[str] = None
    work_order_no: Optional[str] = None
    expected_size: Optional[str] = None
    actual_size: Optional[str] = None
    storage_location: Optional[str] = None
    is_in_lake: Optional[str] = None
    not_in_lake_reason: Optional[str] = None
    resource_pool: Optional[str] = None
    network_type: Optional[str] = None
    host_ip: Optional[str] = None
    dataset_format: Optional[str] = None
    source_system: Optional[str] = None
    update_freq: Optional[str] = None
    is_sensitive: Optional[str] = None
    sensitive_info: Optional[str] = None
    share_requirement: Optional[str] = None
    use_structured: Optional[str] = None
    dataset_scope: Optional[str] = None
    data_level: Optional[str] = None
    kb_type: Optional[str] = None
    kb_modality: Optional[str] = None
    kb_expected_scale: Optional[str] = None
    corpus_type: Optional[str] = None
    corpus_modality: Optional[str] = None
    corpus_expected_scale: Optional[str] = None
    is_annotated: Optional[str] = None
    annotation_labels: Optional[str] = None
    annotation_method: Optional[str] = None
    annotator_type: Optional[str] = None
    prompt_expected_scale: Optional[str] = None
    prompt_target_model: Optional[str] = None
    prompt_task: Optional[str] = None
    prompt_app_sys: Optional[str] = None
    status: Optional[str] = None
    build_unit: Optional[str] = None
    build_target: Optional[str] = None
    build_plan: Optional[str] = None
    dataset_desc: Optional[str] = None
    scene_online_time: Optional[str] = None
    sample_data: Optional[str] = None


class DatasetMetadataOut(DatasetMetadataCreate):
    update_time: Optional[str] = None
    oper_type: Optional[str] = None
    oper_time: Optional[str] = None
    sync_time: Any = None
    qualities: List[DatasetQualitySchema] = []
    is_compliant: Optional[str] = None

    class Config:
        from_attributes = True


class DatasetQuery(BaseModel):
    dataset_name: Optional[str] = None
    dataset_type: Optional[str] = None
    org_unit: Optional[str] = None
    org_dept: Optional[str] = None
    biz_scene: Optional[str] = None
    biz_sub_scene: Optional[str] = None
    is_in_lake: Optional[str] = None
    status: Optional[str] = None
    is_compliant: Optional[str] = None
    page: int = 1
    size: int = 10
