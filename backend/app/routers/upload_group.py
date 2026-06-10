from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.dataset import UploadMultimodalDataset
from app.models.asset import (
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
from app.schemas.common import CommonResponse

router = APIRouter()

# ==================== 多模态 - 高质量数据集上报 ====================

@router.get("/multimodal/dataset")
def list_multimodal_uploads(
    dataset_name: Optional[str] = None,
    dataset_type: Optional[str] = None,
    org_unit: Optional[str] = None,
    is_compliant: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    q = db.query(UploadMultimodalDataset)
    if dataset_type:
        q = q.filter(UploadMultimodalDataset.dataset_type == dataset_type)
    if is_compliant:
        q = q.filter(UploadMultimodalDataset.is_compliant == is_compliant)
    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    rows = []
    for i in items:
        rows.append({
            "id": i.id,
            "ust_id": i.ust_id,
            "dataset_type": i.dataset_type,
            "biz_scene": i.biz_scene,
            "is_compliant": i.is_compliant,
            "non_compliant_reason": i.non_compliant_reason,
            "upload_status": i.upload_status,
            "upload_time": str(i.upload_time) if i.upload_time else None,
        })
    return CommonResponse(data={"total": total, "list": rows, "page": page, "size": size})


@router.post("/multimodal/dataset/upload")
def do_upload_multimodal(ids: list, db: Session = Depends(get_db)):
    now = datetime.now()
    success = 0
    fail = 0
    for pk in ids:
        obj = db.query(UploadMultimodalDataset).filter(UploadMultimodalDataset.id == pk).first()
        if not obj:
            continue
        if obj.is_compliant != "是":
            fail += 1
            continue
        obj.upload_status = "已上传"
        obj.upload_time = now
        obj.oper_type = obj.oper_type or "0"
        obj.oper_time = now.strftime("%Y%m%d%H%M%S")
        success += 1
    db.commit()
    return CommonResponse(data={"success": success, "fail": fail})


@router.post("/multimodal/dataset/modify")
def modify_multimodal_upload(data: dict, db: Session = Depends(get_db)):
    """单条/批量修改高质量数据集上传记录"""
    ids = data.get("ids", [])
    updates = data.get("updates", {})
    count = 0
    for pk in ids:
        obj = db.query(UploadMultimodalDataset).filter(UploadMultimodalDataset.id == pk).first()
        if not obj:
            continue
        for k, v in updates.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        count += 1
    db.commit()
    return CommonResponse(data={"updated": count})


# ==================== 多模态 - 非结构化数据上报 ====================

@router.get("/multimodal/unstructured")
def list_unstructured_uploads(
    file_name: Optional[str] = None,
    sys_name: Optional[str] = None,
    is_compliant: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    q = db.query(UploadMultimodalUnstructured)
    if file_name:
        q = q.filter(
            UploadMultimodalUnstructured.file_name_cn.like(f"%{file_name}%")
            | UploadMultimodalUnstructured.file_name_en.like(f"%{file_name}%")
        )
    if sys_name:
        q = q.filter(UploadMultimodalUnstructured.sys_name.like(f"%{sys_name}%"))
    if is_compliant:
        q = q.filter(UploadMultimodalUnstructured.is_compliant == is_compliant)
    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    rows = []
    for i in items:
        rows.append({
            "id": i.id,
            "ust_id": i.ust_id,
            "file_name_cn": i.file_name_cn,
            "file_name_en": i.file_name_en,
            "sys_name": i.sys_name,
            "is_compliant": i.is_compliant,
            "non_compliant_reason": i.non_compliant_reason,
            "oper_type": i.oper_type,
        })
    return CommonResponse(data={"total": total, "list": rows, "page": page, "size": size})


@router.post("/multimodal/unstructured/upload")
def do_upload_unstructured(ids: list, db: Session = Depends(get_db)):
    now = datetime.now()
    count = 0
    for pk in ids:
        obj = db.query(UploadMultimodalUnstructured).filter(UploadMultimodalUnstructured.id == pk).first()
        if not obj or obj.is_compliant != "是":
            continue
        obj.oper_type = "0"
        obj.oper_time = now.strftime("%Y%m%d%H%M%S")
        count += 1
    db.commit()
    return CommonResponse(data={"uploaded": count})


# ==================== 资源类 - 系统上报 ====================

@router.get("/resource/system")
def list_resource_system(
    sys_name: Optional[str] = None,
    sys_code: Optional[str] = None,
    record_name: Optional[str] = None,
    is_uploaded: Optional[str] = None,
    is_compliant: Optional[str] = None,
    is_offline: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    q = db.query(UploadResourceSystem)
    if sys_name:
        q = q.filter(UploadResourceSystem.sys_name.like(f"%{sys_name}%"))
    if sys_code:
        q = q.filter(UploadResourceSystem.sys_code.like(f"%{sys_code}%"))
    if record_name:
        q = q.filter(UploadResourceSystem.record_name.like(f"%{record_name}%"))
    if is_uploaded:
        q = q.filter(UploadResourceSystem.is_uploaded == is_uploaded)
    if is_compliant:
        q = q.filter(UploadResourceSystem.is_compliant == is_compliant)
    if is_offline:
        q = q.filter(UploadResourceSystem.status == "下线")
    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    rows = []
    for i in items:
        rows.append({
            "id": i.id,
            "sys_group_id": i.sys_group_id,
            "sys_code": i.sys_code,
            "sys_name": i.sys_name,
            "record_name": i.record_name,
            "org_unit": i.org_unit,
            "org_dept": i.org_dept,
            "status": i.status,
            "online_time": i.online_time,
            "is_compliant": i.is_compliant,
            "non_compliant_reason": i.non_compliant_reason,
            "is_uploaded": i.is_uploaded,
            "master_data_code": i.master_data_code,
        })
    return CommonResponse(data={"total": total, "list": rows, "page": page, "size": size})


@router.post("/resource/system/upload")
def do_upload_system(ids: list, db: Session = Depends(get_db)):
    """上传系统到集团（模式一/二）"""
    now = datetime.now()
    for pk in ids:
        obj = db.query(UploadResourceSystem).filter(UploadResourceSystem.id == pk).first()
        if not obj or obj.is_compliant != "是":
            continue
        obj.is_uploaded = "是"
        obj.oper_type = obj.oper_type or "0"
        obj.oper_time = now.strftime("%Y%m%d%H%M%S")
    db.commit()
    return CommonResponse()


@router.post("/resource/system/upload-with-children")
def do_upload_system_with_children(sys_id: int, db: Session = Depends(get_db)):
    """整体上传（系统粒度）：上传系统及其下数据库、表、字段"""
    now = datetime.now()
    ts = now.strftime("%Y%m%d%H%M%S")
    sys_obj = db.query(UploadResourceSystem).filter(
        UploadResourceSystem.id == sys_id,
        UploadResourceSystem.is_compliant == "是",
    ).first()
    if not sys_obj:
        raise HTTPException(status_code=400, detail="系统不存在或不合规")
    sys_obj.is_uploaded = "是"
    sys_obj.oper_type = "0" if not sys_obj.oper_type or sys_obj.oper_type == "0" else "1"
    sys_obj.oper_time = ts

    for db_obj in db.query(UploadResourceDatabase).filter(UploadResourceDatabase.sys_id == sys_id).all():
        db_obj.oper_type = "0"
        db_obj.oper_time = ts
        for tbl_obj in db.query(UploadResourceTable).filter(UploadResourceTable.db_id == db_obj.id).all():
            tbl_obj.oper_type = "0"
            tbl_obj.oper_time = ts
            for fld_obj in db.query(UploadResourceField).filter(UploadResourceField.tbl_id == tbl_obj.id).all():
                fld_obj.oper_type = "0"
                fld_obj.oper_time = ts
    db.commit()
    return CommonResponse()


@router.post("/resource/system/offline")
def do_offline_system(ids: list, db: Session = Depends(get_db)):
    """下线上传（模式四）：oper_type=2"""
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    count = 0
    for pk in ids:
        obj = db.query(UploadResourceSystem).filter(UploadResourceSystem.id == pk).first()
        if not obj:
            continue
        obj.oper_type = "2"
        obj.oper_time = now
        obj.status = "下线"
        count += 1
    db.commit()
    return CommonResponse(data={"offlined": count})


@router.post("/resource/system/modify")
def modify_resource_system(data: dict, db: Session = Depends(get_db)):
    """单条/批量修改系统元数据"""
    ids = data.get("ids", [])
    updates = data.get("updates", {})
    count = 0
    for pk in ids:
        obj = db.query(UploadResourceSystem).filter(UploadResourceSystem.id == pk).first()
        if not obj:
            continue
        for k, v in updates.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        obj.oper_type = "1"
        obj.oper_time = datetime.now().strftime("%Y%m%d%H%M%S")
        count += 1
    db.commit()
    return CommonResponse(data={"updated": count})


# ==================== 资源类 - 数据库/表/字段上报 ====================

@router.get("/resource/database")
def list_resource_database(
    sys_id: Optional[int] = None,
    db_name: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    q = db.query(UploadResourceDatabase)
    if sys_id:
        q = q.filter(UploadResourceDatabase.sys_id == sys_id)
    if db_name:
        q = q.filter(UploadResourceDatabase.db_name.like(f"%{db_name}%"))
    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    return CommonResponse(data={
        "total": total,
        "list": [{"id": i.id, "db_group_id": i.db_group_id, "sys_id": i.sys_id,
                   "db_name": i.db_name, "db_type": i.db_type,
                   "is_compliant": i.is_compliant, "non_compliant_reason": i.non_compliant_reason,
                   "oper_type": i.oper_type} for i in items],
        "page": page, "size": size,
    })


@router.post("/resource/database/upload")
def do_upload_database(ids: list, db: Session = Depends(get_db)):
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    count = 0
    for pk in ids:
        obj = db.query(UploadResourceDatabase).filter(UploadResourceDatabase.id == pk).first()
        if not obj or obj.is_compliant != "是":
            continue
        obj.oper_type = "0"
        obj.oper_time = now
        count += 1
    db.commit()
    return CommonResponse(data={"uploaded": count})


@router.get("/resource/table")
def list_resource_table(
    db_id: Optional[int] = None,
    table_name: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    session: Session = Depends(get_db),
):
    q = session.query(UploadResourceTable)
    if db_id:
        q = q.filter(UploadResourceTable.db_id == db_id)
    if table_name:
        q = q.filter(
            UploadResourceTable.table_name_en.like(f"%{table_name}%")
            | UploadResourceTable.table_name_cn.like(f"%{table_name}%")
        )
    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    return CommonResponse(data={
        "total": total,
        "list": [{"id": i.id, "tbl_group_id": i.tbl_group_id, "db_id": i.db_id,
                   "table_name_en": i.table_name_en, "table_name_cn": i.table_name_cn,
                   "table_desc": i.table_desc, "topic_domain": i.topic_domain,
                   "is_compliant": i.is_compliant, "non_compliant_reason": i.non_compliant_reason,
                   "oper_type": i.oper_type} for i in items],
        "page": page, "size": size,
    })


@router.get("/resource/field")
def list_resource_field(
    tbl_id: Optional[int] = None,
    field_name: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    session: Session = Depends(get_db),
):
    q = session.query(UploadResourceField)
    if tbl_id:
        q = q.filter(UploadResourceField.tbl_id == tbl_id)
    if field_name:
        q = q.filter(
            UploadResourceField.field_name_en.like(f"%{field_name}%")
        )
    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    return CommonResponse(data={
        "total": total,
        "list": [{"id": i.id, "field_group_id": i.field_group_id, "tbl_id": i.tbl_id,
                   "field_name_en": i.field_name_en, "field_name_cn": i.field_name_cn,
                   "field_type": i.field_type, "is_compliant": i.is_compliant,
                   "non_compliant_reason": i.non_compliant_reason, "oper_type": i.oper_type} for i in items],
        "page": page, "size": size,
    })


# ==================== 资产类 - 标签上报 ====================

@router.get("/asset/label")
def list_asset_label(
    label_name: Optional[str] = None,
    is_compliant: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    q = db.query(UploadAssetLabel)
    if label_name:
        q = q.filter(UploadAssetLabel.label_name.like(f"%{label_name}%"))
    if is_compliant:
        q = q.filter(UploadAssetLabel.is_compliant == is_compliant)
    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    rows = [{"id": i.id, "label_group_id": i.label_group_id, "label_name": i.label_name,
             "category_l1": i.category_l1, "category_l2": i.category_l2,
             "biz_definition": i.biz_definition, "is_compliant": i.is_compliant,
             "non_compliant_reason": i.non_compliant_reason} for i in items]
    return CommonResponse(data={"total": total, "list": rows, "page": page, "size": size})


@router.post("/asset/label/upload")
def do_upload_label(ids: list, db: Session = Depends(get_db)):
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    count = 0
    for pk in ids:
        obj = db.query(UploadAssetLabel).filter(UploadAssetLabel.id == pk).first()
        if not obj or obj.is_compliant != "是":
            continue
        obj.oper_type = "0"
        obj.oper_time = now
        count += 1
    db.commit()
    return CommonResponse(data={"uploaded": count})


# ==================== 资产类 - 指标上报 ====================

@router.get("/asset/indicator")
def list_asset_indicator(
    indicator_name: Optional[str] = None,
    is_compliant: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    q = db.query(UploadAssetIndicator)
    if indicator_name:
        q = q.filter(UploadAssetIndicator.indicator_name.like(f"%{indicator_name}%"))
    if is_compliant:
        q = q.filter(UploadAssetIndicator.is_compliant == is_compliant)
    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    rows = [{"id": i.id, "indicator_group_id": i.indicator_group_id, "indicator_name": i.indicator_name,
             "unit": i.unit, "period": i.period, "is_compliant": i.is_compliant,
             "non_compliant_reason": i.non_compliant_reason} for i in items]
    return CommonResponse(data={"total": total, "list": rows, "page": page, "size": size})


@router.post("/asset/indicator/upload")
def do_upload_indicator(ids: list, db: Session = Depends(get_db)):
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    count = 0
    for pk in ids:
        obj = db.query(UploadAssetIndicator).filter(UploadAssetIndicator.id == pk).first()
        if not obj or obj.is_compliant != "是":
            continue
        obj.oper_type = "0"
        obj.oper_time = now
        count += 1
    db.commit()
    return CommonResponse(data={"uploaded": count})


# ==================== 资产类 - API上报 ====================

@router.get("/asset/api")
def list_asset_api(
    api_name: Optional[str] = None,
    is_compliant: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    q = db.query(UploadAssetApi)
    if api_name:
        q = q.filter(UploadAssetApi.api_name.like(f"%{api_name}%"))
    if is_compliant:
        q = q.filter(UploadAssetApi.is_compliant == is_compliant)
    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    rows = [{"id": i.id, "api_group_id": i.api_group_id, "api_name": i.api_name,
             "api_url": i.api_url, "method": i.method, "is_compliant": i.is_compliant,
             "non_compliant_reason": i.non_compliant_reason} for i in items]
    return CommonResponse(data={"total": total, "list": rows, "page": page, "size": size})


@router.post("/asset/api/upload")
def do_upload_api(ids: list, db: Session = Depends(get_db)):
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    count = 0
    for pk in ids:
        obj = db.query(UploadAssetApi).filter(UploadAssetApi.id == pk).first()
        if not obj or obj.is_compliant != "是":
            continue
        obj.oper_type = "0"
        obj.oper_time = now
        count += 1
    db.commit()
    return CommonResponse(data={"uploaded": count})


# ==================== 资产类 - 产品上报 ====================

@router.get("/asset/product")
def list_asset_product(
    product_name: Optional[str] = None,
    is_compliant: Optional[str] = None,
    page: int = Query(1),
    size: int = Query(10),
    db: Session = Depends(get_db),
):
    q = db.query(UploadAssetProduct)
    if product_name:
        q = q.filter(UploadAssetProduct.product_name.like(f"%{product_name}%"))
    if is_compliant:
        q = q.filter(UploadAssetProduct.is_compliant == is_compliant)
    total = q.count()
    items = q.offset((page - 1) * size).limit(size).all()
    rows = [{"id": i.id, "product_group_id": i.product_group_id, "product_name": i.product_name,
             "biz_domain": i.biz_domain, "category": i.category, "is_effective": i.is_effective,
             "shelf_time": i.shelf_time, "expire_time": i.expire_time,
             "is_compliant": i.is_compliant, "non_compliant_reason": i.non_compliant_reason} for i in items]
    return CommonResponse(data={"total": total, "list": rows, "page": page, "size": size})


@router.post("/asset/product/upload")
def do_upload_product(ids: list, db: Session = Depends(get_db)):
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    count = 0
    for pk in ids:
        obj = db.query(UploadAssetProduct).filter(UploadAssetProduct.id == pk).first()
        if not obj or obj.is_compliant != "是":
            continue
        obj.oper_type = "0"
        obj.oper_time = now
        count += 1
    db.commit()
    return CommonResponse(data={"uploaded": count})

# ==================== 资源类元数据修改 ====================

@router.post("/resource/database/modify")
def modify_resource_database(data: dict, db: Session = Depends(get_db)):
    ids = data.get("ids", [])
    updates = data.get("updates", {})
    count = 0
    for pk in ids:
        obj = db.query(UploadResourceDatabase).filter(UploadResourceDatabase.id == pk).first()
        if not obj:
            continue
        for k, v in updates.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        count += 1
    db.commit()
    return CommonResponse(data={"updated": count})


@router.post("/resource/table/modify")
def modify_resource_table(data: dict, db: Session = Depends(get_db)):
    ids = data.get("ids", [])
    updates = data.get("updates", {})
    count = 0
    for pk in ids:
        obj = db.query(UploadResourceTable).filter(UploadResourceTable.id == pk).first()
        if not obj:
            continue
        for k, v in updates.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        count += 1
    db.commit()
    return CommonResponse(data={"updated": count})


@router.post("/resource/field/modify")
def modify_resource_field(data: dict, db: Session = Depends(get_db)):
    ids = data.get("ids", [])
    updates = data.get("updates", {})
    count = 0
    for pk in ids:
        obj = db.query(UploadResourceField).filter(UploadResourceField.id == pk).first()
        if not obj:
            continue
        for k, v in updates.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        count += 1
    db.commit()
    return CommonResponse(data={"updated": count})
