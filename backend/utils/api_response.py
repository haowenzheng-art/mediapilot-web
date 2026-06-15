"""
API 响应辅助函数
提供统一的响应创建逻辑
"""
from typing import Optional, List, Any, Dict
from datetime import datetime
from fastapi import status
from backend.models.schemas.api_response import (
    APISuccessResponse,
    APICollectionResponse,
    PaginatedResponse,
    APIError,
    ErrorCode
)


def success_response(
    data: Optional[Any] = None,
    message: str = "操作成功"
) -> APISuccessResponse:
    """
    创建成功响应（单条数据）
    """
    return APISuccessResponse(
        success=True,
        data=data,
        message=message,
        timestamp=datetime.utcnow()
    )


def collection_response(
    data: List[Any],
    meta: Optional[Dict[str, Any]] = None,
    links: Optional[Dict[str, str]] = None,
    message: Optional[str] = None
) -> APICollectionResponse:
    """
    创建集合响应（列表数据）
    """
    response_meta = {}
    if meta:
        response_meta.update(meta)

    response_links = {}
    if links:
        response_links.update(links)

    return APICollectionResponse(
        success=True,
        data=data,
        meta=response_meta,
        links=response_links,
        message=message or "操作成功",
        timestamp=datetime.utcnow()
    )


def paginated_response(
    data: List[Any],
    total: int,
    page: int = 1,
    per_page: int = 20,
    next_page: Optional[int] = None,
    prev_page: Optional[int] = None
) -> PaginatedResponse:
    """
    创建分页响应
    """
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    meta = {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }

    links = {}
    if next_page:
        links["next"] = f"?page={next_page}&per_page={per_page}"
    if prev_page:
        links["prev"] = f"?page={prev_page}&per_page={per_page}"

    return PaginatedResponse(
        data=data,
        meta=meta,
        links=links if links else None
    )


def error_response(
    code: str,
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail: Optional[Dict[str, Any]] = None
):
    """
    创建错误响应
    返回 FastAPI 可直接使用的 Response 对象
    """
    from fastapi.responses import JSONResponse

    error_detail = {
        "code": code,
        "message": message
    }
    if detail:
        error_detail.update(detail)

    response_data = {
        "success": False,
        "error": error_detail
    }

    return JSONResponse(
        status_code=status_code,
        content=response_data
    )
