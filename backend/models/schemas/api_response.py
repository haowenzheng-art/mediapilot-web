"""
统一 API 响应模型
按照 api-design skill 规范实现
"""
from typing import List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ErrorDetail(BaseModel):
    """错误详情"""
    field: Optional[str] = None
    message: str
    code: str


class PaginationMeta(BaseModel):
    """分页元数据"""
    total: int
    page: int
    per_page: int = Field(default=20, ge=1, le=100)
    total_pages: int


class PaginationLinks(BaseModel):
    """分页链接"""
    self: Optional[str] = None
    next: Optional[str] = None
    prev: Optional[str] = None
    first: Optional[str] = None
    last: Optional[str] = None


class APIError(BaseModel):
    """错误响应"""
    error: ErrorDetail


class APISuccessResponse(BaseModel):
    """成功响应 - 单条数据"""
    success: bool = Field(default=True, description="是否成功")
    data: Optional[Any] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class APICollectionResponse(BaseModel):
    """成功响应 - 集合数据"""
    success: bool = Field(default=True, description="是否成功")
    data: List[Any]
    meta: Optional[PaginationMeta] = None
    links: Optional[PaginationLinks] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel):
    """分页响应（标准格式）"""
    data: List[Any]
    meta: PaginationMeta
    links: Optional[PaginationLinks] = None


# 错误码常量
class ErrorCode:
    """错误码定义"""
    # 客户端错误 (4xx)
    VALIDATION_ERROR = "validation_error"
    INVALID_INPUT = "invalid_input"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

    # 服务端错误 (5xx)
    INTERNAL_ERROR = "internal_error"
    DATABASE_ERROR = "database_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    TASK_NOT_FOUND = "task_not_found"
