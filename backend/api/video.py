"""
视频分析路由
"""
import logging

from fastapi import APIRouter, Query
from fastapi.responses import Response
from backend.models.schemas.request import VideoFetchRequest, VideoRewriteRequest, VideoTranscriptRequest
from backend.models.schemas.response import APIResponse
from backend.services.video_service import VideoService
from backend.core.ai_service import ai_manager

router = APIRouter(prefix="/video", tags=["视频分析"])

logger = logging.getLogger(__name__)

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
async def get_video_transcript(request: VideoTranscriptRequest):
    """获取视频逐字稿"""
    result = await video_service.get_transcript(request.video_id)
    return APIResponse(data=result)


@router.post("/rewrite", response_model=APIResponse)
async def rewrite_video(request: VideoRewriteRequest):
    """改写视频文案"""
    mock_result = f"[示例改写] {request.transcript[:50]}...（{request.style.value}风格，目标{request.target_duration or 60}秒）"

    try:
        if ai_manager.is_available():
            rewritten = await ai_manager.rewrite_transcript(
                request.transcript,
                request.style.value,
                request.target_duration or 60
            )
            return APIResponse(data={"rewritten_text": rewritten})
        else:
            return APIResponse(data={"rewritten_text": mock_result}, message="AI服务暂不可用，已返回示例数据")
    except Exception as e:
        logger.warning(f"视频文案改写AI失败，回退mock: {e}")
        return APIResponse(data={"rewritten_text": mock_result}, message="AI服务暂不可用，已返回示例数据")


BLANK_PNG = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'


@router.get("/proxy-image")
async def proxy_image(url: str = Query(..., description="图片URL")):
    """代理图片，解决B站防盗链问题"""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url, headers={'Referer': 'https://www.bilibili.com'})

            if response.status_code == 200:
                return Response(
                    content=response.content,
                    media_type=response.headers.get('content-type', 'image/jpeg'),
                    headers={'Cache-Control': 'public, max-age=86400'}
                )
            else:
                logger.warning(f"下载图片失败: status={response.status_code}")
                return Response(content=BLANK_PNG, media_type='image/png')

    except Exception as e:
        logger.error(f"代理图片失败: {e}")
        return Response(content=BLANK_PNG, media_type='image/png')
