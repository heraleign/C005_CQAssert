from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.asset import AuditRule, AuditResult
from app.schemas.audit import AuditRuleCreate, AuditRuleUpdate, AuditRuleOut, AuditExecuteRequest
from app.schemas.common import CommonResponse
from app.services.audit_engine import evaluate_rules

router = APIRouter()


@router.get("/rules")
def list_rules(
    rule_code: Optional[str] = None,
    rule_name: Optional[str] = None,
    target_asset: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    q = db.query(AuditRule)
    if rule_code:
        q = q.filter(AuditRule.rule_code.like(f"%{rule_code}%"))
    if rule_name:
        q = q.filter(AuditRule.rule_name.like(f"%{rule_name}%"))
    if target_asset:
        q = q.filter(AuditRule.target_asset == target_asset)
    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    return CommonResponse(data={
        "total": total,
        "list": [AuditRuleOut.model_validate(i).model_dump() for i in items],
        "page": page,
        "size": size,
    })


@router.post("/rules/create")
def create_rule(data: AuditRuleCreate, db: Session = Depends(get_db)):
    if db.query(AuditRule).filter(AuditRule.rule_code == data.rule_code).first():
        raise HTTPException(status_code=400, detail="规则编码已存在")
    obj = AuditRule(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return CommonResponse(data={"rule_id": obj.rule_id})


@router.post("/rules/update/{rule_id}")
def update_rule(rule_id: int, data: AuditRuleUpdate, db: Session = Depends(get_db)):
    obj = db.query(AuditRule).filter(AuditRule.rule_id == rule_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="规则不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return CommonResponse()


@router.post("/execute")
def execute_audit(req: AuditExecuteRequest, db: Session = Depends(get_db)):
    """执行稽核规则评估，记录账期"""
    now = datetime.now()
    period = req.period or now.strftime("%Y%m%d")
    period_type = req.period_type or "日"
    results = evaluate_rules(
        db=db,
        asset_type=req.asset_type,
        asset_id=req.asset_id,
        target_ids=req.batch_ids,
        period=period,
        period_type=period_type,
    )
    return CommonResponse(data={"results": results})


@router.get("/results")
def list_results(
    asset_type: Optional[str] = None,
    asset_id: Optional[str] = None,
    period_type: Optional[str] = None,
    period: Optional[str] = None,
    is_pass: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    q = db.query(AuditResult)
    if asset_type:
        q = q.filter(AuditResult.asset_type == asset_type)
    if asset_id:
        q = q.filter(AuditResult.asset_id == asset_id)
    if period_type:
        q = q.filter(AuditResult.period_type == period_type)
    if period:
        q = q.filter(AuditResult.period == period)
    if is_pass:
        q = q.filter(AuditResult.is_pass == is_pass)
    total = q.count()
    items = q.order_by(AuditResult.check_time.desc()).offset((page - 1) * size).limit(size).all()
    rows = []
    for i in items:
        rows.append({
            "result_id": i.result_id,
            "asset_type": i.asset_type,
            "asset_id": i.asset_id,
            "rule_code": i.rule_code,
            "is_pass": i.is_pass,
            "reason": i.reason,
            "period_type": i.period_type,
            "period": i.period,
            "check_time": str(i.check_time) if i.check_time else None,
        })
    return CommonResponse(data={"total": total, "list": rows, "page": page, "size": size})
