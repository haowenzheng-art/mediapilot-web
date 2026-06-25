"""
API 依赖注入模块
提供认证和配额检查的依赖
"""
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jwt.exceptions import PyJWTError

from backend.config.database import get_db
from backend.config.settings import settings
from backend.core.jwt import decode_token
from backend.models.database.tables import UserTable

logger = logging.getLogger(__name__)

# JWT Bearer 认证
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> UserTable:
    """
    解析 Authorization: Bearer <token>，验签后从 DB 取出用户。
    失败一律抛 401，绝不返回 db Session。
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_token(token, expected_type="access")
    except PyJWTError as e:
        logger.info(f"JWT 校验失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或过期的 token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_raw = payload.get("sub")
    if user_id_raw is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token 缺少 sub")

    try:
        user_id = int(user_id_raw)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token sub 格式错误")

    user = db.query(UserTable).filter(UserTable.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已停用",
        )

    return user


async def check_quota(user_id: int, operation: str, db: Session) -> bool:
    """检查用户配额是否足够"""
    from backend.services.auth_service_typed import auth_service
    return auth_service.check_quota(db, user_id, operation)


async def deduct_quota(user_id: int, operation: str, db: Session) -> tuple[bool, int]:
    """扣减用户配额"""
    from backend.services.auth_service_typed import auth_service
    return auth_service.deduct_quota(db, user_id, operation)
