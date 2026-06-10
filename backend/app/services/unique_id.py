"""集团唯一标识生成原子能力"""

from typing import Optional


def _make_id(org_code: str, dept_abbr: str, middle: str, seq: int, padding: int = 4) -> str:
    return f"{org_code}-{dept_abbr}-{middle}-{str(seq).zfill(padding)}"


def generate_id(id_type: str, local_biz_id: str = "") -> str:
    """通用唯一标识生成，供字段规则引擎调用"""
    from datetime import datetime
    seq = abs(hash(local_biz_id or datetime.now().isoformat())) % 10000
    return _make_id("JT", "SYSTEM", f"{id_type}", seq)


def generate_system_id(org_code: str, dept_abbr: str, sys_abbr: str, seq: int) -> str:
    """系统唯一标识：[组织编码]-[部门缩写]-[系统名称缩写]-[顺序编码]"""
    return _make_id(org_code, dept_abbr, f"{sys_abbr}-SYS", seq)


def generate_database_id(org_code: str, dept_abbr: str, sys_abbr: str, seq: int) -> str:
    """数据库唯一标识：[组织编码]-[部门缩写]-[系统名称缩写]-DB-[顺序编码]"""
    return _make_id(org_code, dept_abbr, f"{sys_abbr}-DB", seq)


def generate_table_id(org_code: str, dept_abbr: str, sys_abbr: str, seq: int) -> str:
    """表唯一标识：[组织编码]-[部门缩写]-[系统名称缩写]-TABLE-[顺序编码]"""
    return _make_id(org_code, dept_abbr, f"{sys_abbr}-TABLE", seq)


def generate_field_id(org_code: str, dept_abbr: str, sys_abbr: str, seq: int) -> str:
    """字段唯一标识"""
    return _make_id(org_code, dept_abbr, f"{sys_abbr}-FIELD", seq)


def generate_label_id(org_code: str, dept_abbr: str, sys_abbr: str, seq: int) -> str:
    """标签唯一标识：[组织编码]-[部门缩写]-[系统名称缩写]-BQ-[顺序编码]"""
    return _make_id(org_code, dept_abbr, f"{sys_abbr}-BQ", seq)


def generate_indicator_id(org_code: str, dept_abbr: str, sys_abbr: str, seq: int) -> str:
    """指标唯一标识：[组织编码]-[部门缩写]-[系统名称缩写]-ZB-[顺序编码]"""
    return _make_id(org_code, dept_abbr, f"{sys_abbr}-ZB", seq)


def generate_api_id(org_code: str, dept_abbr: str, sys_abbr: str, seq: int) -> str:
    """API唯一标识：[组织编码]-[部门缩写]-[系统名称缩写]-API-[顺序编码]"""
    return _make_id(org_code, dept_abbr, f"{sys_abbr}-API", seq)


def generate_product_id(org_code: str, dept_abbr: str, sys_abbr: str, seq: int) -> str:
    """产品唯一标识：[组织编码]-[部门缩写]-[系统名称缩写]-PRD-[顺序编码]"""
    return _make_id(org_code, dept_abbr, f"{sys_abbr}-PRD", seq)


def generate_unstructured_id(org_code: str, dept_abbr: str, sys_abbr: str, seq: int) -> str:
    """非结构化唯一标识：[组织编码]-[部门缩写]-[系统名称缩写]-UST-[顺序编码]"""
    return _make_id(org_code, dept_abbr, f"{sys_abbr}-UST", seq)


def generate_dataset_id(org_code: str, dept_abbr: str, scene_abbr: str, seq: int) -> str:
    """高质量数据集唯一标识：[组织编码]-[部门缩写]-[场景缩写]-DATASET-[顺序编码]"""
    return _make_id(org_code, dept_abbr, f"{scene_abbr}-DATASET", seq, padding=4)
