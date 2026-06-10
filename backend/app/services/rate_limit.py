"""查询频次控制服务"""

import time
from datetime import date
from typing import Dict, Tuple

from app.config import settings

# 内存计数器（生产环境应替换为 Redis）
_search_counters: Dict[str, int] = {}
_last_date: str = ""


def _today_key(user_id: str) -> str:
    global _last_date, _search_counters
    today = date.today().isoformat()
    if _last_date != today:
        _search_counters.clear()
        _last_date = today
    return f"{user_id}:{today}"


def check_search_limit(user_id: str) -> Tuple[bool, int]:
    """检查用户当日查询次数是否超限。返回 (是否允许, 今日已用次数)"""
    key = _today_key(user_id)
    count = _search_counters.get(key, 0)
    limit = settings.search_daily_limit
    if count >= limit:
        return False, count
    return True, count


def increment_search_count(user_id: str) -> int:
    """增加用户当日查询次数。返回当前次数"""
    key = _today_key(user_id)
    _search_counters[key] = _search_counters.get(key, 0) + 1
    return _search_counters[key]


def get_search_count(user_id: str) -> int:
    """获取用户当日查询次数"""
    key = _today_key(user_id)
    return _search_counters.get(key, 0)
