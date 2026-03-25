"""
数据格式化工具
"""
from datetime import datetime


def format_timestamp(dt: datetime) -> str:
    """
    格式化时间戳

    Args:
        dt: 日期时间对象

    Returns:
        格式化后的字符串，如 "2026-03-25 14:30:00"
    """
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_number(num: int, use_suffix: bool = False) -> str:
    """
    格式化数字

    Args:
        num: 数字
        use_suffix: 是否使用后缀（K, M, B）

    Returns:
        格式化后的字符串
    """
    if not use_suffix:
        return str(num)

    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return str(num)


def format_trend(trend: str) -> str:
    """
    格式化趋势标识

    Args:
        trend: 趋势 (rising, falling, stable)

    Returns:
        格式化后的字符串和符号
    """
    trend_map = {
        "rising": ("📈", "上升"),
        "falling": ("📉", "下降"),
        "stable": ("➡️", "平稳"),
    }

    icon, text = trend_map.get(trend.lower(), ("➡️", "未知"))
    return f"{icon} {text}"
