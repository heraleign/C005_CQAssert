"""数据脱敏服务"""

import re


def mask_phone(phone: str) -> str:
    """手机号脱敏：133****1100"""
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + "****" + phone[-4:]


def mask_email(email: str) -> str:
    """邮箱脱敏：abc***@chinatelecom.cn"""
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 3:
        return local + "***@" + domain
    return local[:3] + "***@" + domain


def mask_tel(tel: str) -> str:
    """电话脱敏：010-****1234"""
    if not tel:
        return tel
    m = re.match(r"(\d{3,4})-(\d+)", tel)
    if m:
        return m.group(1) + "-****" + m.group(2)[-4:]
    return tel


def mask_name(name: str) -> str:
    """姓名脱敏：张明 -> 张*"""
    if not name:
        return name
    if len(name) == 2:
        return name[0] + "*"
    if len(name) > 2:
        return name[0] + "*" * (len(name) - 2) + name[-1]
    return name


def mask_id_card(id_no: str) -> str:
    """身份证号脱敏：110101199001011234 -> 110101****1234"""
    if not id_no or len(id_no) < 10:
        return id_no
    return id_no[:6] + "****" + id_no[-4:]


FIELDS_TO_MASK = {
    "biz_owner_phone": mask_phone,
    "contact_phone": mask_phone,
    "email": mask_email,
    "phone": mask_tel,
    "tel": mask_tel,
    "telephone": mask_tel,
    "id_card": mask_id_card,
    "biz_owner": mask_name,
    "contact_name": mask_name,
}


def mask_dict(data: dict, *, strict: bool = False) -> dict:
    """对字典中已知敏感字段进行脱敏。strict=True 时对 phone-like 值也脱敏。"""
    result = {}
    for k, v in data.items():
        if isinstance(v, str):
            lower_k = k.lower()
            if lower_k in FIELDS_TO_MASK:
                result[k] = FIELDS_TO_MASK[lower_k](v)
            elif strict and re.search(r"1[3-9]\d{9}", v):
                result[k] = mask_phone(v)
            else:
                result[k] = v
        else:
            result[k] = v
    return result
