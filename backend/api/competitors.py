"""
对标账号路由
使用统一的 API 响应模型和错误处理
"""
import logging

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, Query, status, HTTPException
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from backend.models.schemas.request import CompetitorSearchRequest
from backend.models.schemas.api_response import ErrorCode
from backend.utils.api_response import success_response, error_response
from backend.services.competitor_service import CompetitorService
from backend.services.import_export_service import import_export_service
from backend.api.dependencies import get_current_user
from backend.config.database import get_db
from backend.models.database.tables import UserTable

router = APIRouter(prefix="/competitors", tags=["对标账号"])

# 初始化服务
competitor_service = CompetitorService()


@router.post("/search")
async def search_competitors(
    request: CompetitorSearchRequest,
    user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    搜索对标账号
    使用统一的响应模型和错误处理
    """
    from backend.services.auth_service_typed import auth_service

    # 检查配额
    check_result = auth_service.check_quota(db, user.id, "search_competitors")
    quota_ok = check_result[0] if isinstance(check_result, tuple) and len(check_result) >= 2 else check_result
    balance = check_result[1] if isinstance(check_result, tuple) and len(check_result) >= 2 else user.quota_balance
    if not quota_ok:
        return error_response(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=f"配额不足，当前余额: {balance}",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

    try:
        logger.info(f"Searching competitors: niche={request.niche}, platforms={request.platforms}")
        platforms = [p.value for p in request.platforms]
        result = await competitor_service.search(
            niche=request.niche,
            platforms=platforms,
            min_followers=request.min_followers,
            max_followers=request.max_followers,
            min_avg_likes=request.min_avg_likes
        )

        logger.info(f"Search result: {len(result.competitors)} competitors")

        # 扣减配额
        auth_service.deduct_quota(db, user.id, "search_competitors")

        return success_response(
            data=result,
            message=f"找到 {len(result.competitors)} 个对标账号"
        )
    except Exception as e:
        logger.error(f"Search competitors error: {e}")
        return error_response(
            code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            message=f"搜索对标账号失败: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/export")
async def export_competitors(
    niche: str = Query(..., description="赛道/领域"),
    format: str = Query("csv", pattern="^(csv|xlsx)$", description="导出格式"),
    current_user: UserTable = Depends(get_current_user)
):
    """
    导出对标账号为 CSV 或 Excel
    不消耗配额（分析功能）
    """
    try:
        # 执行搜索（不扣减配额）
        platforms = ["douyin", "xiaohongshu"]
        result = await competitor_service.search(
            niche=niche,
            platforms=platforms,
            min_followers=10000,
            max_followers=1000000,
            min_avg_likes=100
        )

        # 获取账号列表
        accounts = result.competitors

        file_content = import_export_service.export_competitors(accounts, format)

        if format == "csv":
            media_type = "text/csv"
            filename = f"competitors_{niche}.csv"
        else:
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"competitors_{niche}.xlsx"

        return Response(
            content=file_content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "export_error", "message": str(e)})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "server_error", "message": f"导出失败: {str(e)}"}
        )


@router.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return success_response(data={"status": "ok"}, message="对标账号服务正常")
