"""
认证 API 路由
提供用户注册、登录、获取信息、配额管理等接口
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.config. database import get_db
from backend.models.database.tables import UserTable
from backend.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RechargeRequest(BaseModel):
    amount: int


@router.post("/register")
async def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    用户注册

    创建新用户并返回 JWT token
    """
    try:
        user = await auth_service.register(
            db=db,
            username=request.username,
            password=request.password,
            email=request.email
        )

        # 获取 JWT token
        token = auth_service.generate_token(user.id)

        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "quota_balance": user.quota_balance,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat()
            },
            "token": token,
            "message": "注册成功"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "registration_failed", "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "server_error", "message": f"注册失败: {str(e)}"}
        )


@router.post("/login")
async def login_user(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录

    验证用户名密码并返回 JWT token
    """
    try:
        user = await auth_service.login(
            db=db,
            username=request.username,
            password=request.password
        )

        if not user or not user.is_active:
            raise HTTPException(
                status_code=401,
                detail={"code": "invalid_credentials", "message": "用户名或密码错误"}
            )

        # 获取 JWT token
        token = auth_service.generate_token(user.id)

        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "quota_balance": user.quota_balance,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat()
            },
            "token": token,
            "message": "登录成功"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail={"code": "invalid_credentials", "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "server_error", "message": f"登录失败: {str(e)}"}
        )


@router.get("/me")
async def get_current_user_info(
    current_user: UserTable = Depends(get_current_user)
):
    """
    获取当前登录用户信息

    需要 JWT 认证
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "quota_balance": current_user.quota_balance,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat()
    }


@router.get("/quota")
async def get_user_quota(
    current_user: UserTable = Depends(get_current_user)
):
    """
    获取用户配额余额

    需要 JWT 认证
    """
    return {
        "user_id": current_user.id,
        "balance": current_user.quota_balance,
        "added": 0
    }


@router.post("/recharge")
async def recharge_quota(
    request: RechargeRequest,
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    充值配额

    需要 JWT 认证
    """
    if request.amount <= 0 or request.amount > 10000:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_amount", "message": "充值金额必须在 1-10000 之间"}
        )

    try:
        success, new_balance = await auth_service.recharge(
            db=db,
            user_id=current_user.id,
            amount=request.amount
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail={"code": "recharge_failed", "message": "充值失败"}
            )

        return {
            "user_id": current_user.id,
            "balance": new_balance,
            "added": request.amountser": "充值成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "server_error", "message": f"充值失败: {str(e)}"}
        )


@router.post("/admin/recharge")
async def admin_recharge_quota(
    user_id: int,
    amount: int,
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    管理员充值配额

    需要 JWT 认证 + 管理员权限
    """
    # 检查管理员权限
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail={"code": "permission_denied", "message": "需要管理员权限"}
        )

    if amount <= 0 or amount > 10000:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_amount", "message": "充值金额必须在 1-10000 之间"}
        )

    try:
        success, new_balance = await auth_service.recharge(
            db=db,
            user_id=user_id,
            amount=amount
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail={"code": "recharge_failed", "message": "充值失败"}
            )

        return {
            "user_id": user_id,
            "balance": new_balance,
            "added": amount,
            "message": "管理员充值成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "server_error", "message": f"管理员充值失败: {str(e)}"}
        )


@router.get("/admin/users")
async def get_all_users(
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取所有用户列表

    需要 JWT 认证 + 管理员权限
    """
    # 检查管理员权限
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail={"code": "permission_denied", "message": "需要管理员权限"}
        )

    try:
        users = await auth_service.get_all_users(db)

        return {
            "users": [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "quota_balance": user.quota_balance,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at.isoformat()
                }
                for user in users
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "server_error", "message": f"获取用户列表失败: {str(e)}"}
        )


# 需要导入 get_current_user 函数
from backend.api.dependencies import get_current_user
