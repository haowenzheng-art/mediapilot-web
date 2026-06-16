"""
JWT 工具模块
提供 JWT access token 和 refresh token 的生成与验证
"""
import hashlib
import uuid
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
from jwt import PyJWTError

from backend.config.settings import settings


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30分钟
REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7天


def hash_token(token: str) -> str:
    """SHA-256 hash of a token string (for DB storage without persisting raw tokens)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT access token

    Args:
        data: 要编码的数据（通常包含 user_id 和 username）
        expires_delta: 过期时间增量，默认为 ACCESS_TOKEN_EXPIRE_MINUTES

    Returns:
        JWT access token 字符串
    """
    to_encode = data.copy()
    to_encode["type"] = "access"

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_refresh_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT refresh token

    Args:
        data: 要编码的数据（通常包含 user_id 和 username）
        expires_delta: 过期时间增量，默认为 REFRESH_TOKEN_EXPIRE_DAYS

    Returns:
        JWT refresh token 字符串
    """
    to_encode = data.copy()
    to_encode["type"] = "refresh"
    to_encode["jti"] = uuid.uuid4().hex

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str, expected_type: Optional[str] = None) -> Dict:
    """
    解码并验证 JWT token

    Args:
        token: JWT token 字符串
        expected_type: 期望的 token 类型 ("access" 或 "refresh")，None 则不检查

    Returns:
        解码后的 payload 字典

    Raises:
        PyJWTError: token 无效、过期或类型不匹配
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])

        if expected_type and payload.get("type") != expected_type:
            raise PyJWTError(f"Expected {expected_type} token, got {payload.get('type')}")

        return payload
    except PyJWTError as e:
        raise PyJWTError(f"Invalid token: {str(e)}")


# 向后兼容
decode_access_token = lambda token: decode_token(token, expected_type="access")


def get_user_id_from_token(token: str) -> int:
    """
    从 access token 中提取 user_id

    Args:
        token: JWT access token 字符串

    Returns:
        用户 ID
    """
    payload = decode_token(token, expected_type="access")
    user_id = payload.get("sub")

    if user_id is None:
        raise PyJWTError("Token does not contain user_id")

    return int(user_id)


def verify_token(token: str) -> bool:
    """
    验证 token 是否有效

    Args:
        token: JWT token 字符串

    Returns:
        True 表示有效，False 表示无效
    """
    try:
        decode_token(token)
        return True
    except PyJWTError:
        return False
