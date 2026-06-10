from typing import Optional, Any
from pydantic import BaseModel


class AuditRuleCreate(BaseModel):
    rule_code: str
    rule_name: str
    rule_desc: Optional[str] = None
    rule_type: str
    target_asset: str
    expression: Optional[str] = None


class AuditRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    rule_desc: Optional[str] = None
    rule_type: Optional[str] = None
    target_asset: Optional[str] = None
    expression: Optional[str] = None
    is_enabled: Optional[str] = None


class AuditRuleOut(BaseModel):
    rule_id: int
    rule_code: str
    rule_name: str
    rule_desc: Optional[str]
    rule_type: str
    target_asset: str
    expression: Optional[str]
    is_enabled: str
    create_time: Any

    class Config:
        from_attributes = True


class AuditExecuteRequest(BaseModel):
    asset_type: str
    asset_id: Optional[str] = None
    batch_ids: Optional[list] = None
    period_type: Optional[str] = "日"
    period: Optional[str] = None
