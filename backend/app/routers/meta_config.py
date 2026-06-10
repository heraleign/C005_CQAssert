"""元模型配置管理 - 支持管理员在线配置字段定义、必填规则、枚举值、展示分组"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.dataset import MetaFieldConfig
from app.schemas.common import CommonResponse

router = APIRouter()


@router.get("/fields")
def list_field_configs(
    field_group: Optional[str] = None,
    is_active: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(100),
    db: Session = Depends(get_db),
):
    """查询元模型字段配置列表"""
    q = db.query(MetaFieldConfig)
    if field_group:
        q = q.filter(MetaFieldConfig.field_group == field_group)
    if is_active:
        q = q.filter(MetaFieldConfig.is_active == is_active)
    total = q.count()
    items = q.order_by(MetaFieldConfig.sort_order).offset((page - 1) * size).limit(size).all()

    rows = []
    for i in items:
        rows.append({
            "field_id": i.field_id,
            "field_name": i.field_name,
            "field_group": i.field_group,
            "field_type": i.field_type,
            "source_type": i.source_type,
            "is_required": i.is_required,
            "enum_values": json.loads(i.enum_values) if i.enum_values else None,
            "default_value": i.default_value,
            "max_length": i.max_length,
            "sort_order": i.sort_order,
            "condition_expr": json.loads(i.condition_expr) if i.condition_expr else None,
            "display_width": i.display_width,
            "is_active": i.is_active,
        })
    return CommonResponse(data={"total": total, "list": rows, "page": page, "size": size})


@router.get("/fields/groups")
def get_field_groups(db: Session = Depends(get_db)):
    """获取按分组聚合的字段配置（供动态表单渲染使用）"""
    items = db.query(MetaFieldConfig).filter(
        MetaFieldConfig.is_active == "是"
    ).order_by(MetaFieldConfig.sort_order).all()

    groups: Dict[str, List[dict]] = {}
    for i in items:
        group_name = i.field_group
        if group_name not in groups:
            groups[group_name] = []
        groups[group_name].append({
            "field_id": i.field_id,
            "field_name": i.field_name,
            "field_type": i.field_type,
            "source_type": i.source_type,
            "is_required": i.is_required,
            "enum_values": json.loads(i.enum_values) if i.enum_values else None,
            "default_value": i.default_value,
            "max_length": i.max_length,
            "condition_expr": json.loads(i.condition_expr) if i.condition_expr else None,
            "display_width": i.display_width,
        })

    return CommonResponse(data={
        "groups": groups,
        "group_order": ["基础信息组", "存储信息组", "结构属性信息组", "生命周期组"],
    })


@router.post("/fields/create")
def create_field_config(data: dict, db: Session = Depends(get_db)):
    """新增字段配置"""
    if db.query(MetaFieldConfig).filter(MetaFieldConfig.field_id == data.get("field_id")).first():
        raise HTTPException(status_code=400, detail="字段标识已存在")

    enum_raw = data.get("enum_values")
    cond_raw = data.get("condition_expr")
    obj = MetaFieldConfig(
        field_id=data["field_id"],
        field_name=data["field_name"],
        field_group=data.get("field_group", "基础信息组"),
        field_type=data.get("field_type", "VARCHAR"),
        source_type=data.get("source_type", "manual"),
        is_required=data.get("is_required", "否"),
        enum_values=json.dumps(enum_raw, ensure_ascii=False) if enum_raw else None,
        default_value=data.get("default_value"),
        max_length=data.get("max_length"),
        sort_order=data.get("sort_order", 0),
        condition_expr=json.dumps(cond_raw, ensure_ascii=False) if cond_raw else None,
        display_width=data.get("display_width", 2),
        is_active=data.get("is_active", "是"),
    )
    db.add(obj)
    db.commit()
    return CommonResponse(data={"field_id": obj.field_id})


@router.post("/fields/update/{field_id}")
def update_field_config(field_id: str, data: dict, db: Session = Depends(get_db)):
    """修改字段配置"""
    obj = db.query(MetaFieldConfig).filter(MetaFieldConfig.field_id == field_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="字段不存在")
    for k, v in data.items():
        if k == "enum_values" and v is not None:
            v = json.dumps(v, ensure_ascii=False)
        elif k == "condition_expr" and v is not None:
            v = json.dumps(v, ensure_ascii=False)
        if hasattr(obj, k):
            setattr(obj, k, v)
    db.commit()
    return CommonResponse()


@router.post("/fields/delete/{field_id}")
def delete_field_config(field_id: str, db: Session = Depends(get_db)):
    """删除字段配置（软删除：设置 is_active=否）"""
    obj = db.query(MetaFieldConfig).filter(MetaFieldConfig.field_id == field_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="字段不存在")
    obj.is_active = "否"
    db.commit()
    return CommonResponse()


@router.post("/validate-conditions")
def validate_conditional_rules(data: dict, db: Session = Depends(get_db)):
    """校验条件必填规则：传入当前表单值，返回缺失的必填字段列表"""
    form_values = data.get("form_values", {})
    dataset_type = form_values.get("dataset_type", "")

    rules = db.query(MetaFieldConfig).filter(
        MetaFieldConfig.condition_expr.isnot(None),
        MetaFieldConfig.condition_expr != "",
        MetaFieldConfig.is_active == "是",
    ).all()

    missing = []
    for rule in rules:
        if not rule.condition_expr:
            continue
        try:
            cond = json.loads(rule.condition_expr)
        except json.JSONDecodeError:
            continue

        trigger_field = cond.get("field", "dataset_type")
        trigger_value = form_values.get(trigger_field, "")
        if trigger_value != cond.get("eq"):
            continue

        for req_field in cond.get("required_fields", []):
            if req_field not in form_values or not form_values[req_field]:
                # 查找对应中文名
                cfg = db.query(MetaFieldConfig).filter(
                    MetaFieldConfig.field_id == req_field
                ).first()
                field_name_cn = cfg.field_name if cfg else req_field
                missing.append({
                    "field_id": req_field,
                    "field_name": field_name_cn,
                    "condition": f"当{cond.get('field')}={cond.get('eq')}时必填",
                })

    return CommonResponse(data={"missing": missing, "is_valid": len(missing) == 0})
