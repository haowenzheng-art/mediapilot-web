"""
用户领域模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class User(BaseModel):
    """用户模型"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: Optional[str] = None
    quota_balance: int = Field(default=100, description="配额余额")
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserCreate(BaseModel):
    """创建用户请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    email: Optional[EmailStr] = Field(None, description="邮箱")


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """用户响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: Optional[str] = None
    quota_balance: int
    is_active: bool
    created_at: datetime


class QuasiRecharge(BaseModel):
    """配额充值请求"""
    amount: int = Field(..., gt=0, le=100000, description="充值金额")


class QuasiResponse(BaseModel):
    """配额响应"""
    user_id: int
    balance: int
    added: int
