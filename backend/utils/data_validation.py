"""
数据验证工具

提供输入验证、数据清理等功能
"""
import re
from typing import Optional, List, Dict, Any

logger = __import__('logging').getLogger(__name__)


class ValidationError(Exception):
    """验证错误"""
    pass


def validate_email(email: str) -> bool:
    """
    验证邮箱格式

    Args:
        email: 邮箱地址

    Returns:
        bool: 是否有效
    """
    if not email:
        return False

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9._-]{2,}$'
    return re.match(pattern, email) is not None


def validate_username(username: str) -> bool:
    """
    验证用户名格式

    Args:
        username: 用户名

    Returns:
        bool: 是否有效
    """
    if not username:
        return False

    # 用户名规则：
    # 1. 长度 3-20 个字符
    # 2. 只能包含字母、数字、下划线、连字符
    if len(username) < 3 or len(username) > 20:
        return False

    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False

    return True


def validate_password(password: str) -> Optional[str]:
    """
    验证密码强度

    Args:
        password: 密码

    Returns:
        Optional[str]: 错误信息，None 表示有效
    """
    if not password:
        return "密码不能为空"

    if len(password) < 8:
        return "密码长度至少为 8 个字符"

    # 检查是否包含大小写字母
    if not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password):
        return "密码必须包含大小写字母和数字"

    # 检查是否包含特殊字符
    if re.search(r'[!@#$%^&*()\-+=\[\]{}|\\:;\'"<>,.?/]', password):
        if not re.search(r'[a-zA-Z0-9]', password):
            return "密码不能仅包含特殊字符"

    return None


def sanitize_string(text: str, max_length: int = 1000) -> str:
    """
    清理字符串，防止 XSS 和注入攻击

    Args:
        text: 原始字符串
        max_length: 最大长度

    Returns:
        str: 清理后的字符串
    """
    if not text:
        return ""

    # 移除危险的 HTML 标签
    dangerous_tags = ['<script', '</script>', '<iframe', '</iframe>', '<object>', '</object>',
                     '<embed>', '</embed>', '<javascript:', 'onerror=', 'onload=']
    clean_text = text
    for tag in dangerous_tags:
        clean_text = clean_text.replace(tag, '', ignore_case=True)

    # 移除 SQL 注入风险字符
    sql_risky_chars = ["'", ";", "--", "/*", "*/", "xp_", "UNION",
                       "SELECT", "INSERT", "UPDATE", "DELETE", "DROP"]
    for char in sql_risky_chars:
        clean_text = clean_text.replace(char, '')

    # 限制长度
    if len(clean_text) > max_length:
        clean_text = clean_text[:max_length]

    logger.warning(f"字符串被截断: 原始长度 {len(text)}, 清理后长度 {len(clean_text)}")

    return clean_text.strip()


def validate_positive_int(value: int, field_name: str = "值", min_val: int = 1) -> Optional[str]:
    """
    验证正整数

    Args:
        value: 要验证的值
        field_name: 字段名称（用于错误信息）
        min_val: 最小值

    Returns:
        Optional[str]: 错误信息，None 表示有效
    """
    if not isinstance(value, int):
        return f"{field_name} 必须是整数"

    if value < min_val:
        return f"{field_name} 必须大于或等于 {min_val}"

    return None


def validate_pagination_params(page: int, per_page: int, max_per_page: int = 100) -> Dict[str, Any]:
    """
    验证分页参数

    Args:
        page: 页码
        per_page: 每页数量
        max_per_page: 最大每页数量

    Returns:
        Dict: 验证结果和修正后的参数
    """
    errors = []

    if page < 1:
        errors.append("页码必须大于 0")
        page = 1

    if per_page < 1:
        errors.append("每页数量必须大于 0")
        per_page = 10

    if per_page > max_per_page:
        errors.append(f"每页数量不能超过 {max_per_page}")
        per_page = max_per_page

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "page": page,
        "per_page": per_page
    }


def validate_sort_params(sort_by: str, valid_fields: List[str]) -> Optional[str]:
    """
    验证排序参数

    Args:
        sort_by: 排序字段
        valid_fields: 有效的字段列表

    Returns:
        Optional[str]: 错误信息，None 表示有效
    """
    if not sort_by:
        return None

    # 移除降序标记
    field = sort_by.lstrip('-')
    if field not in valid_fields:
        return f"无效的排序字段: {field}"

    # 检查降序
    is_desc = sort_by.startswith('-')
    if is_desc:
        return None

    return None


def validate_json_structure(data: Any, required_fields: List[str]) -> Optional[str]:
    """
    验证 JSON 数据结构

    Args:
        data: 要验证的数据
        required_fields: 必须字段列表

    Returns:
        Optional[str]: 错误信息，None 表示有效
    """
    if not isinstance(data, dict):
        return "数据必须是字典类型"

    for field in required_fields:
        if field not in data:
            return f"缺少必填字段: {field}"

    return None
