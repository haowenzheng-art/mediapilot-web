"""
热点搜索路由
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter
from models.schemas.request import TrendingSearchRequest
from models.schemas.response import APIResponse
from services.trending_service import TrendingService

router = APIRouter(prefix="/trending", tags=["热点搜索"])

# 初始化服务
trending_service = TrendingService()


@router.post("/search", response_model=APIResponse)
async def search_trending(request: TrendingSearchRequest):
    """搜索热点话题"""
    platforms = [p.value for p in request.platforms]
    result = await trending_service.search(
        keyword=request.keyword,
        platforms=platforms,
        days=request.days
    )
    return APIResponse(data=result)
