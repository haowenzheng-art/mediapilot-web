"""
内容生成路由
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter
from models.schemas.request import ContentGenerateRequest, VideoRewriteRequest
from models.schemas.response import APIResponse
from services.content_service import ContentService
from services.auth_service import AuthService

router = APIRouter(prefix="/content", tags=["内容生成"])

# 初始化服务
content_service = ContentService()
auth_service = AuthService()


@router.post("/generate", response_model=APIResponse)
async def generate_content(request: ContentGenerateRequest):
    """生成分镜头脚本和文案"""
    result = await content_service.generate_script(
        topic=request.topic,
        platform=request.platform.value,
        duration=request.duration,
        style=request.style.value
    )
    return APIResponse(data=result)


@router.post("/rewrite", response_model=APIResponse)
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
            message="AI服务不可用",
            data=None
        )

    return APIResponse(data=result)
