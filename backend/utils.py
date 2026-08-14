"""通用工具：时间统一用北京时间（客户在保定，服务器显示 UTC 会差8小时）"""
from datetime import datetime, timezone, timedelta

CN_TZ = timezone(timedelta(hours=8))


def now_cn() -> datetime:
    """当前北京时间（naive，与SQLite列类型一致）"""
    return datetime.now(CN_TZ).replace(tzinfo=None)
