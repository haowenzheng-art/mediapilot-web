"""
对标账号路由
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from models.schemas.request import CompetitorSearchRequest
from models.schemas.response import APIResponse
from services.competitor_service import CompetitorService

router = APIRouter(prefix="/competitors", tags=["对标账号"])

# 初始化服务
competitor_service = CompetitorService()


@router.post("/search", response_model=APIResponse)
async def search_competitors(request: CompetitorSearchRequest):
    """搜索对标账号"""
    platforms = [p.value for p in request.platforms]
    result = await competitor_service.search(
        niche=request.niche,
        platforms=platforms,
        min_followers=request.min_followers or 10000,
        max_followers=request.max_followers or 1000000,
        min_avg_likes=request.min_avg_likes or 100
    )
    return APIResponse(data=result)


@router.get("/export")
async def export_competitors(niche: str):
    """导出对标账号Excel"""
    excel_file = await competitor_service.export_excel(niche)
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=competitors.xlsx"}
    )
