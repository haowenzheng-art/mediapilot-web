"""
视频分析路由
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter
from models.schemas.request import VideoFetchRequest
from models.schemas.response import APIResponse
from services.video_service import VideoService

router = APIRouter(prefix="/video", tags=["视频分析"])

# 初始化服务
video_service = VideoService()


@router.post("/fetch", response_model=APIResponse)
async def fetch_video(request: VideoFetchRequest):
    """获取视频信息"""
    result = await video_service.fetch_video(
        video_url=request.video_url,
        platform=request.platform.value
    )
    return APIResponse(data=result)


@router.post("/transcript", response_model=APIResponse)
async def get_video_transcript(video_id: str):
    """获取视频逐字稿"""
    result = await video_service.get_transcript(video_id)
    return APIResponse(data=result)
