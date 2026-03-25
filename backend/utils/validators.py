"""
数据验证工具
"""
import re


def validate_keyword(keyword: str) -> bool:
    """
    验证搜索关键词

    Args:
        keyword: 搜索关键词

    Returns:
        验证是否通过

    Raises:
        ValueError: 关键词不合法
    """
    if not keyword or not keyword.strip():
        raise ValueError("关键词不能为空")

    if len(keyword.strip()) > 50:
        raise ValueError("关键词长度不能超过50个字符")

    # 检查是否包含非法字符
    if re.search(r'[<>{}"\\]', keyword):
        raise ValueError("关键词包含非法字符")

    return True


def validate_niche(niche: str) -> bool:
    """
    验证赛道名称

    Args:
        niche: 赛道名称

    Returns:
        验证是否通过

    Raises:
        ValueError: 赛道名称不合法
    """
    if not niche or not niche.strip():
        raise ValueError("赛道不能为空")

    if len(niche.strip()) > 30:
        raise ValueError("赛道长度不能超过30个字符")

    return True


def validate_platforms(platforms: list) -> bool:
    """
    验证平台列表

    Args:
        platforms: 平台列表

    Returns:
        验证是否通过
    """
    valid_platforms = {
        "douyin", "xiaohongshu", "weibo",
        "kuaishou", "bilibili"
    }

    for platform in platforms:
        if platform.lower() not in valid_platforms:
            raise ValueError(f"不支持的平台: {platform}")

    return True
