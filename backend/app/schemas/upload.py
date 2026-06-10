from typing import Optional, Dict, List, Any
from pydantic import BaseModel


class SyncToMidRequest(BaseModel):
    asset_type: str
    scope_type: str = "system"
    scope_ids: Optional[List[str]] = None
    overwrite_empty: bool = False


class AuditMidRequest(BaseModel):
    asset_type: str
    scope_type: str = "system"
    scope_ids: Optional[List[str]] = None


class MidModifyRequest(BaseModel):
    asset_type: str
    local_biz_id: str
    modify_fields: Dict[str, str]
    modify_reason: str


class SyncToResultRequest(BaseModel):
    asset_type: str
    scope_type: str = "system"
    scope_ids: Optional[List[str]] = None


class UploadToGroupRequest(BaseModel):
    asset_type: str
    scope_type: str = "system"
    scope_ids: Optional[List[str]] = None
    upload_mode: str = "all"


class MidListQuery(BaseModel):
    asset_type: str
    sys_code: Optional[str] = None
    sys_name: Optional[str] = None
    record_name: Optional[str] = None
    audit_status: Optional[str] = None
    upload_status: Optional[str] = None
    sys_status: Optional[str] = None
    sys_func_type: Optional[str] = None
    if_managed: Optional[str] = None
    page: int = 1
    size: int = 10
