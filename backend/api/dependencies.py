"""
API 依赖注入模块
提供认证和配额检查的依赖
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.config.settings import settings


# JWT Bearer 认证
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Session:
    """
    获取当前用户（依赖注入）

    开发模式下直接返回数据库会话，调用方可通过 settings.get_dev_user(db) 获取用户。
    生产模式暂不实现 JWT 认证，后续接入。
    """
    return db


async def check_quota(user_id: int, operation: str, db: Session) -> bool:
    """
    检查用户配额是否足够
    """
    from backend.services.auth_service_typed import auth_service
    return auth_service.check_quota(db, user_id, operation)


async def deduct_quota(user_id: int, operation: str, db: Session) -> tuple[bool, int]:
    """
    扣减用户配额
    """
    from backend.services.auth_service_typed import auth_service
    return auth_service.deduct_quota(db, user_id, operation)
