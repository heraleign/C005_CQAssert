from typing import Optional, Any
from pydantic import BaseModel


class HandoverCreate(BaseModel):
    asset_type: str = "系统"
    asset_id: str
    from_user: str
    to_user: str
    operator: str
    remark: Optional[str] = None


class HandoverOut(BaseModel):
    log_id: int
    asset_type: str
    asset_id: str
    from_user: str
    to_user: str
    operator: str
    operate_time: Any
    remark: Optional[str]

    class Config:
        from_attributes = True
