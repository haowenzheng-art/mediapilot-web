"""
认证 API 路由
使用统一的 API 响应模型和正确的错误处理
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from backend.config.database import get_db
from backend.models.database.tables import UserTable
from backend.services.auth_service_typed import auth_service
from backend.models.domain.user import UserCreate, UserLogin
from backend.core.jwt import create_access_token, create_refresh_token, decode_token
from backend.api.dependencies import get_current_user
from backend.services.token_cleanup_service import token_cleanup_service
from backend.utils.api_response import (
    success_response,
    error_response,
    ErrorCode
)

router = APIRouter(prefix="/auth", tags=["认证"])


class RegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    email: EmailStr = Field(..., description="邮箱")


class LoginRequest(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class RechargeRequest(BaseModel):
    """充值请求"""
    amount: int


class RefreshRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str


class LogoutRequest(BaseModel):
    """登出请求"""
    refresh_token: str


@router.post("/register")
async def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    用户注册

    创建新用户账户并返回 JWT 访问令牌

    - **请求体**：
      - username: 用户名（3-50个字符）
      - password: 密码（至少6个字符）
      - email: 电子邮箱地址

    - **成功响应**（200）：
      ```json
      {
        "success": true,
        "data": {
          "user": { "id": 1, "username": "...", "email": "...", "quota_balance": 100, ... },
          "token": "eyJhbGc..."
        },
        "message": "注册成功",
        "timestamp": "2026-04-13T10:30:00"
      }
      ```

    - **错误响应**（400）：
      ```json
      {
        "success": false,
        "error": {
          "code": "validation_error",
          "message": "用户名已存在"
        }
      }
      ```
    """
    try:
        user_data = UserCreate(
            username=request.username,
            password=request.password,
            email=request.email
        )

        user = auth_service.register_user(db, user_data)

        # 获取 JWT token
        token_data = {"sub": str(user.id), "username": user.username}
        token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)

        # 存储刷新令牌哈希到黑名单表
        auth_service.store_refresh_token(db, refresh_token, user.id)

        return success_response(
            data={
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "quota_balance": user.quota_balance,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat()
                },
                "token": token,
                "refresh_token": refresh_token
            },
            message="注册成功"
        )
    except ValueError as e:
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"注册失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/login", response_model=None)
async def login_user(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录

    验证用户名密码并返回 JWT token
    """
    try:
        login_data = UserLogin(username=request.username, password=request.password)
        user, token, refresh_token = auth_service.login_user(db, login_data)

        if not user or not user.is_active:
            return error_response(
                code=ErrorCode.UNAUTHORIZED,
                message="用户名或密码错误",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        return success_response(
            data={
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "quota_balance": user.quota_balance,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat()
                },
                "token": token,
                "refresh_token": refresh_token
            },
            message="登录成功"
        )
    except ValueError as e:
        return error_response(
            code=ErrorCode.UNAUTHORIZED,
            message=str(e),
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"登录失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/refresh")
async def refresh_token(
    request: RefreshRequest,
    db: Session = Depends(get_db)
):
    """
    刷新访问令牌

    使用 refresh_token 获取新的 access_token 和 refresh_token（轮转）
    旧的 refresh_token 将被撤销
    """
    try:
        # 验证刷新令牌（JWT + DB 黑名单检查）
        user_id, username = auth_service.validate_refresh_token(
            db, request.refresh_token
        )

        # 验证用户仍存在且活跃
        user = db.query(UserTable).filter(UserTable.id == user_id).first()
        if not user or not user.is_active:
            return error_response(
                code=ErrorCode.UNAUTHORIZED,
                message="用户不存在或已被禁用",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # 吊销旧 refresh token
        auth_service.revoke_refresh_token(db, request.refresh_token)

        # 生成新 token 对（轮转）
        token_data = {"sub": str(user.id), "username": user.username}
        new_token = create_access_token(data=token_data)
        new_refresh = create_refresh_token(data=token_data)

        # 存储新 refresh token
        auth_service.store_refresh_token(db, new_refresh, user.id)

        return success_response(
            data={
                "token": new_token,
                "refresh_token": new_refresh
            },
            message="刷新令牌成功"
        )
    except ValueError as e:
        return error_response(
            code=ErrorCode.UNAUTHORIZED,
            message=str(e),
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.UNAUTHORIZED,
            message=f"刷新令牌失败: {str(e)}",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


@router.get("/me", response_model=None)
async def get_current_user_info(
    current_user: UserTable = Depends(get_current_user)
):
    """
    获取当前登录用户信息

    需要 JWT 认证
    """
    return success_response(
        data={
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "quota_balance": current_user.quota_balance,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat()
        },
        message="获取用户信息成功"
    )


@router.post("/logout")
async def logout_user(
    request: LogoutRequest,
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    用户登出

    撤销指定的刷新令牌，需要 JWT 认证
    """
    try:
        revoked = auth_service.revoke_refresh_token(db, request.refresh_token)
        if not revoked:
            return error_response(
                code=ErrorCode.VALIDATION_ERROR,
                message="刷新令牌无效或已撤销",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return success_response(
            data={"revoked": True},
            message="登出成功"
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"登出失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/quota", response_model=None)
async def get_user_quota(
    current_user: UserTable = Depends(get_current_user)
):
    """
    获取用户配额余额

    需要 JWT 认证
    """
    return success_response(
        data={
            "user_id": current_user.id,
            "balance": current_user.quota_balance,
            "added": 0
        },
        message="获取配额成功"
    )


@router.post("/recharge", response_model=None)
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
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="充值金额必须在 1-10000 之间",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        success, old_balance, new_balance = auth_service.recharge_quota(
            db=db,
            user_id=current_user.id,
            amount=request.amount
        )

        if not success:
            return error_response(
                code=ErrorCode.INTERNAL_ERROR,
                message="充值失败",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return success_response(
            data={
                "user_id": current_user.id,
                "balance": new_balance,
                "added": request.amount
            },
            message="充值成功"
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"充值失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/admin/recharge", response_model=None)
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
        return error_response(
            code=ErrorCode.FORBIDDEN,
            message="需要管理员权限",
            status_code=status.HTTP_403_FORBIDDEN
        )

    if amount <= 0 or amount > 10000:
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="充值金额必须在 1-10000 之间",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    try:
        success, old_balance, new_balance = auth_service.recharge_quota(
            db=db,
            user_id=user_id,
            amount=amount
        )

        if not success:
            return error_response(
                code=ErrorCode.INTERNAL_ERROR,
                message="充值失败",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return success_response(
            data={
                "user_id": user_id,
                "balance": new_balance,
                "added": amount
            },
            message="管理员充值成功"
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"管理员充值失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/admin/users", response_model=None)
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
        return error_response(
            code=ErrorCode.FORBIDDEN,
            message="需要管理员权限",
            status_code=status.HTTP_403_FORBIDDEN
        )

    try:
        users = auth_service.get_all_users(db)

        return success_response(
            data={
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
            },
            message="获取用户列表成功"
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"获取用户列表失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/admin/cleanup-tokens", response_model=None)
async def admin_cleanup_tokens(
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    管理员手动清理过期令牌

    需要 JWT 认证 + 管理员权限
    """
    if not current_user.is_admin:
        return error_response(
            code=ErrorCode.FORBIDDEN,
            message="需要管理员权限",
            status_code=status.HTTP_403_FORBIDDEN
        )

    try:
        result = token_cleanup_service.cleanup_expired_and_revoked(db)
        return success_response(
            data=result,
            message="令牌清理完成"
        )
    except Exception as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"令牌清理失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
