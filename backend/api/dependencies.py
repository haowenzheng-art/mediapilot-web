"""
API 依赖注入模块
提供认证和配额检查的依赖
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.models.database.tables import UserTable
from backend.services.auth_service import auth_service


# JWT Bearer 认证
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> UserTable:
    """
    获取当前登录用户

    Raises:
        HTTPException: 认证失败或 token 无效
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "no_token", "message": "未提供认证令牌"}
        )

    try:
        user = auth_service.get_user_from_token(db, credentials.credentials)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_token", "message": "认证令牌无效或已过期"}
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": f"认证失败: {str(e)}"}
        )


async def check_quota(user: UserTable, operation: str) -> bool:
    """
    检查用户配额是否足够

    Args:
        user: 用户对象
        operation: 操作名称

    Returns:
        bool: 是否足够
    """
    return auth_service.check_quota(None, user.id, operation)


async def deduct_quota(user: UserTable, operation: str) -> tuple[bool, int]:
    """
    扣减用户配额

    Args:
        user: 用户对象
        operation: 操作名称

    Returns:
        tuple: (是否成功, 新余额)
    """
    return auth_service.deduct_quota(None, user.id, operation)
