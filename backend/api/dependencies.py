"""
API 依赖注入模块
提供认证和配额检查的依赖
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.models.database.tables import UserTable
from backend.services.auth_service_typed import auth_service


# JWT Bearer 认证
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> UserTable:
    """
    获取当前登录用户

    开发模式下直接返回默认用户，跳过认证
    """
    # 开发模式：直接返回默认用户或创建一个
    user = db.query(UserTable).filter(UserTable.username == "dev").first()
    if not user:
        user = UserTable(
            username="dev",
            email="dev@mediapilot.local",
            hashed_password="dev",
            quota_balance=9999,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


async def check_quota(user: UserTable, operation: str, db: Session) -> bool:
    """
    检查用户配额是否足够

    Args:
        user: 用户对象
        operation: 操作名称
        db: 数据库会话

    Returns:
        bool: 是否足够
    """
    return auth_service.check_quota(db, user.id, operation)


async def deduct_quota(user: UserTable, operation: str, db: Session) -> tuple[bool, int]:
    """
    扣减用户配额

    Args:
        user: 用户对象
        operation: 操作名称
        db: 数据库会话

    Returns:
        tuple: (是否成功, 新余额)
    """
    return auth_service.deduct_quota(db, user.id, operation)
