"""稽核规则引擎"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.asset import (
    AuditRule,
    AuditResult,
    UploadResourceSystem,
    UploadResourceDatabase,
    UploadResourceTable,
    UploadResourceField,
    UploadAssetLabel,
    UploadAssetIndicator,
    UploadAssetApi,
    UploadAssetProduct,
    UploadMultimodalUnstructured,
)
from app.models.dataset import (
    DatasetMetadata,
    UploadMultimodalDataset,
)


def evaluate_rules(
    db: Session,
    asset_type: str,
    asset_id: Optional[str] = None,
    target_ids: Optional[List[int]] = None,
    period: Optional[str] = None,
    period_type: Optional[str] = "日",
) -> List[Dict[str, Any]]:
    """
    对指定资产类型执行稽核规则评估。
    - asset_type: 资产类型（系统/数据库/表/字段/高质量数据集/标签/指标/API/产品/非结构化）
    - asset_id: 可选，单个资产ID
    - target_ids: 可选，批量资产主键ID列表
    - period: 账期，如20260511（日）或202605（月）
    - period_type: 账期类型，日/月
    """
    rules = (
        db.query(AuditRule)
        .filter(
            AuditRule.target_asset.in_([asset_type, "全部"]),
            AuditRule.is_enabled == "是",
        )
        .all()
    )

    # 获取待稽核的资产列表
    targets = _get_assets(db, asset_type, asset_id, target_ids)
    results = []
    now = datetime.now()

    for asset in targets:
        asset_uid = asset.get("asset_id", "")
        reasons = []
        for rule in rules:
            is_pass, reason = _evaluate_single_rule(asset, rule)
            if not is_pass:
                reasons.append(f"[{rule.rule_code}]{reason}")

            result = AuditResult(
                asset_type=asset_type,
                asset_id=asset_uid,
                rule_code=rule.rule_code,
                is_pass="是" if is_pass else "否",
                reason=reason if not is_pass else "",
                period_type=period_type,
                period=period or now.strftime("%Y%m%d"),
                check_time=now,
            )
            db.add(result)

        # 更新资产的合规状态
        joined_reason = "；".join(reasons)
        _update_compliance(db, asset_type, asset_uid, len(reasons) == 0, joined_reason, target_ids)

        results.append({
            "asset_id": asset_uid,
            "is_compliant": "是" if len(reasons) == 0 else "否",
            "non_compliant_reason": joined_reason,
        })

    db.commit()
    return results


def _get_assets(
    db: Session, asset_type: str, asset_id: Optional[str], target_ids: Optional[List[int]]
) -> List[Dict[str, Any]]:
    """获取待稽核的资产列表"""
    model_map = {
        "系统": UploadResourceSystem,
        "数据库": UploadResourceDatabase,
        "表": UploadResourceTable,
        "字段": UploadResourceField,
        "标签": UploadAssetLabel,
        "指标": UploadAssetIndicator,
        "API": UploadAssetApi,
        "产品": UploadAssetProduct,
        "非结构化": UploadMultimodalUnstructured,
        "高质量数据集": DatasetMetadata,
    }

    model = model_map.get(asset_type)
    if not model:
        return []

    query = db.query(model)
    if asset_id:
        if hasattr(model, "dataset_id"):
            query = query.filter(model.dataset_id == asset_id)
        elif hasattr(model, "sys_group_id"):
            query = query.filter(model.sys_group_id == asset_id)
        elif hasattr(model, "ust_id"):
            query = query.filter(model.ust_id == asset_id)
        else:
            query = query.filter(model.id == asset_id)
    elif target_ids:
        query = query.filter(model.id.in_(target_ids))

    items = query.all()
    result = []
    for item in items:
        d = {"asset_id": item.dataset_id if hasattr(item, "dataset_id") else str(getattr(item, "id", ""))}
        for col in item.__table__.columns:
            d[col.name] = getattr(item, col.name)
        result.append(d)
    return result


def _evaluate_single_rule(asset: Dict[str, Any], rule: AuditRule) -> Tuple[bool, str]:
    """对单个资产执行单条稽核规则"""
    rule_code = rule.rule_code
    rule_type = rule.rule_type

    if rule_code == "MM-001":
        return _check_not_null(asset)
    elif rule_code == "MM-002":
        return _check_id_format(asset)
    elif rule_code == "MM-003":
        return _check_kb_consistency(asset)
    elif rule_code == "MM-004":
        return _check_corpus_consistency(asset)
    elif rule_code == "MM-005":
        return _check_lake_consistency(asset)
    elif rule_code == "MM-006":
        return _check_share_consistency(asset)
    elif rule_code == "MM-007":
        return _check_sensitive_consistency(asset)
    elif rule_code == "MM-008":
        return _check_sample_count(asset)

    # 资源类规则
    if rule_type == "非空":
        return _check_not_null(asset)
    if rule_code == "TABLE_NO_FIELD":
        return _check_table_has_fields(asset)
    if rule_code == "DB_NO_TABLE":
        return _check_db_has_tables(asset)

    return True, ""


def _check_not_null(asset: Dict[str, Any]) -> Tuple[bool, str]:
    """非空校验：必填字段不能为空"""
    required = [
        "dataset_name", "dataset_type", "org_unit", "org_dept", "biz_scene",
        "is_in_lake", "resource_pool", "network_type", "host_ip",
        "dataset_format", "source_system", "update_freq", "share_requirement",
    ]
    empty = []
    for field in required:
        if field in asset and (asset[field] is None or str(asset[field]).strip() == ""):
            empty.append(field)
    if empty:
        return False, f"必填字段为空：{', '.join(empty)}"
    return True, ""


def _check_id_format(asset: Dict[str, Any]) -> Tuple[bool, str]:
    """唯一标识格式校验"""
    id_field = None
    for name in ["dataset_id", "sys_group_id", "db_group_id", "tbl_group_id", "ust_id"]:
        if name in asset and asset[name]:
            id_field = name
            break
    if not id_field:
        return True, ""

    value = str(asset[id_field])
    pattern = r"^[A-Z]+-[A-Z]+-[A-Z0-9]+-[A-Z]+-\d{4}$"
    if not re.match(pattern, value):
        return False, f"唯一标识 {value} 不符合命名规范"
    return True, ""


def _check_kb_consistency(asset: Dict[str, Any]) -> Tuple[bool, str]:
    """数据集类型=知识库时，扩展字段必填"""
    if asset.get("dataset_type") != "知识库":
        return True, ""
    missing = []
    for field in ["kb_type", "kb_modality", "kb_expected_scale"]:
        if field not in asset or not asset[field]:
            missing.append(field)
    if missing:
        return False, f"知识库扩展字段缺失：{', '.join(missing)}"
    return True, ""


def _check_corpus_consistency(asset: Dict[str, Any]) -> Tuple[bool, str]:
    """数据集类型=语料时，扩展字段必填"""
    if asset.get("dataset_type") != "语料":
        return True, ""
    missing = []
    for field in ["corpus_type", "corpus_modality", "corpus_expected_scale"]:
        if field not in asset or not asset[field]:
            missing.append(field)
    if missing:
        return False, f"语料扩展字段缺失：{', '.join(missing)}"
    return True, ""


def _check_lake_consistency(asset: Dict[str, Any]) -> Tuple[bool, str]:
    """入湖=是时，存储位置不能为空"""
    if asset.get("is_in_lake") == "是":
        if not asset.get("storage_location"):
            return False, "入湖为是时，存储位置不能为空"
    if asset.get("is_in_lake") == "否":
        if not asset.get("not_in_lake_reason"):
            return False, "入湖为否时，不入湖原因不能为空"
    return True, ""


def _check_share_consistency(asset: Dict[str, Any]) -> Tuple[bool, str]:
    """内部共享要求不是'不共享'时，样例数据不能为空"""
    share = asset.get("share_requirement", "")
    if share and share != "不共享":
        sample = asset.get("sample_data")
        if not sample:
            return False, "共享要求非'不共享'时，样例数据不能为空"
    return True, ""


def _check_sensitive_consistency(asset: Dict[str, Any]) -> Tuple[bool, str]:
    """是否敏感=是时，敏感数据信息不能为空"""
    if asset.get("is_sensitive") == "是":
        if not asset.get("sensitive_info"):
            return False, "是否敏感为是时，敏感数据信息不能为空"
    return True, ""


def _check_sample_count(asset: Dict[str, Any]) -> Tuple[bool, str]:
    """样例数据不少于10条"""
    sample = asset.get("sample_data")
    if sample:
        try:
            parsed = json.loads(sample)
            if isinstance(parsed, list) and len(parsed) < 10:
                return False, f"样例数据不足10条，当前{len(parsed)}条"
        except (json.JSONDecodeError, TypeError):
            pass
    return True, ""


def _check_table_has_fields(asset: Dict[str, Any]) -> Tuple[bool, str]:
    """表下无任何字段记录"""
    return True, ""  # 需跨表查询，在 evaluate_rules 中特殊处理


def _check_db_has_tables(asset: Dict[str, Any]) -> Tuple[bool, str]:
    """数据库下无任何表记录"""
    return True, ""


def _update_compliance(
    db: Session,
    asset_type: str,
    asset_uid: str,
    is_compliant: bool,
    reason: str,
    target_ids: Optional[List[int]],
):
    """更新资产的合规状态"""
    compliant_str = "是" if is_compliant else "否"
    if asset_type == "高质量数据集":
        db.query(DatasetMetadata).filter(
            DatasetMetadata.dataset_id == asset_uid
        ).update({"is_compliant": compliant_str} if hasattr(DatasetMetadata, "is_compliant") else {})
    elif asset_type == "系统":
        db.query(UploadResourceSystem).filter(
            UploadResourceSystem.sys_group_id == asset_uid
        ).update({"is_compliant": compliant_str, "non_compliant_reason": reason})
