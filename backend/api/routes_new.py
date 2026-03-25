"""
MediaPilot 后端API路由 - 简化版
业务逻辑已抽取到 services 层
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict, Any

# 使用新的 schemas
from models.schemas.request import (
    TrendingSearchRequest,
    CompetitorSearchRequest,
    VideoFetchRequest,
    VideoRewriteRequest,
    ContentGenerateRequest,
)
from models.schemas.response import APIResponse

# 导入业务服务
from services import (
    TrendingService,
    CompetitorService,
    ContentService,
    MediaService,
    VideoService,
    AuthService,
)

# 导入配置
from config.settings import settings, get_upload_dir

router = APIRouter(prefix="/api/v1", tags=["MediaPilot API"])

# 初始化服务
trending_service = TrendingService()
competitor_service = CompetitorService()
content_service = ContentService()
media_service = MediaService(get_upload_dir())
video_service = VideoService()
auth_service = AuthService()


@router.post("/trending/search", response_model=APIResponse)
async def search_trending(request: TrendingSearchRequest):
    """搜索热点话题"""
    platforms = [p.value for p in request.platforms]
    result = await trending_service.search(
        keyword=request.keyword,
        platforms=platforms,
        days=request.days
    )
    return APIResponse(data=result)


@router.post("/competitors/search", response_model=APIResponse)
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


@router.get("/competitors/export")
async def export_competitors(niche: str):
    """导出对标账号Excel"""
    excel_file = await competitor_service.export_excel(niche)
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=competitors.xlsx"}
    )


@router.post("/video/fetch", response_model=APIResponse)
async def fetch_video(request: VideoFetchRequest):
    """获取视频信息"""
    result = await video_service.fetch_video(
        video_url=request.video_url,
        platform=request.platform.value
    )
    return APIResponse(data=result)


@router.post("/video/transcript", response_model=APIResponse)
async def get_video_transcript(video_id: str):
    """获取视频逐字稿"""
    result = await video_service.get_transcript(video_id)
    return APIResponse(data=result)


@router.post("/video/rewrite", response_model=APIResponse)
async def rewrite_video(request: VideoRewriteRequest):
    """改写视频文案"""
    if not auth_service.is_ai_available():
        return APIResponse(
            success=False,
            message="请先配置AI服务",
            data=None
        )

    result = await content_service.rewrite_transcript(
        transcript=request.transcript,
        style=request.style.value,
        target_duration=request.target_duration or 60
    )

    if result is None:
        return APIResponse(
            success=False,
            message="AI 服务不可用",
            data=None
        )

    return APIResponse(data=result)


@router.post("/content/generate", response_model=APIResponse)
async def generate_content(request: ContentGenerateRequest):
    """生成分镜头脚本和文案"""
    result = await content_service.generate_script(
        topic=request.topic,
        platform=request.platform.value,
        duration=request.duration,
        style=request.style.value
    )
    return APIResponse(data=result)


@router.post("/media/upload")
async def upload_media(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """上传音视频文件"""
    content = await file.read()
    result = await media_service.upload_and_process(content, file.filename)
    return APIResponse(data=result)


@router.get("/media/{task_id}/status")
async def get_media_status(task_id: str):
    """获取媒体处理状态"""
    if not media_service.task_exists(task_id):
        raise HTTPException(status_code=404, detail="任务不存在")
    result = await media_service.get_status(task_id)
    return APIResponse(data=result)


@router.get("/media/{task_id}/result")
async def get_media_result(task_id: str):
    """获取媒体处理结果"""
    if not media_service.task_exists(task_id):
        raise HTTPException(status_code=404, detail="任务不存在")
    result = await media_service.get_result(task_id)
    return APIResponse(data=result)


@router.post("/ai/configure")
async def configure_ai(provider: str, api_key: str, base_url: str = None, model: str = None):
    """配置AI服务"""
    result = await auth_service.configure_ai(provider, api_key, base_url, model)
    return APIResponse(
        success=result["success"],
        message=result["message"]
    )
