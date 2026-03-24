
"""
MediaPilot 后端API路由
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional
import uuid

from shared.schemas import (
    TrendingSearchRequest, TrendingSearchResponse, HotTopic,
    CompetitorSearchRequest, CompetitorSearchResponse, CompetitorAccount,
    VideoFetchRequest, VideoInfo, VideoTranscriptResponse, TranscriptLine,
    VideoRewriteRequest, ContentGenerateRequest, ContentGenerateResponse,
    Shot, Copywriting, OutlineItem, MediaTranscribeResponse,
    APIResponse
)
from backend.core.ai_service import ai_manager
from backend.core.media_processor import MockMediaProcessor
from backend.core.excel_exporter import ExcelExporter
from backend.services.mock_data import MockDataService
from shared.config import get_upload_dir

router = APIRouter(prefix="/api/v1", tags=["MediaPilot API"])

# 初始化服务
mock_data = MockDataService()
media_processor = MockMediaProcessor(get_upload_dir())
excel_exporter = ExcelExporter()

# 任务状态存储
tasks: Dict[str, Dict[str, Any]] = {}


@router.post("/trending/search", response_model=APIResponse)
async def search_trending(request: TrendingSearchRequest):
    """搜索热点话题"""
    topics = mock_data.search_trending(
        keyword=request.keyword,
        platforms=[p.value for p in request.platforms],
        days=request.days
    )

    hot_topics = [HotTopic(**t) for t in topics]

    return APIResponse(
        data=TrendingSearchResponse(
            keyword=request.keyword,
            total_count=len(hot_topics),
            hot_topics=hot_topics
        )
    )


@router.post("/competitors/search", response_model=APIResponse)
async def search_competitors(request: CompetitorSearchRequest):
    """搜索对标账号"""
    accounts = mock_data.search_competitors(
        niche=request.niche,
        platforms=[p.value for p in request.platforms],
        min_followers=request.min_followers or 10000,
        max_followers=request.max_followers or 1000000,
        min_avg_likes=request.min_avg_likes or 100
    )

    competitor_accounts = [CompetitorAccount(**a) for a in accounts]

    return APIResponse(
        data=CompetitorSearchResponse(
            niche=request.niche,
            total_count=len(competitor_accounts),
            accounts=competitor_accounts
        )
    )


@router.get("/competitors/export")
async def export_competitors(niche: str):
    """导出对标账号Excel"""
    accounts = mock_data.search_competitors(
        niche=niche,
        platforms=["douyin", "xiaohongshu"],
        min_followers=10000,
        max_followers=1000000,
        min_avg_likes=100
    )

    excel_file = excel_exporter.export_competitors(accounts)

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=competitors.xlsx"}
    )


@router.post("/video/fetch", response_model=APIResponse)
async def fetch_video(request: VideoFetchRequest):
    """获取视频信息"""
    video = mock_data.fetch_video(request.video_url, request.platform.value)
    return APIResponse(data=VideoInfo(**video))


@router.post("/video/transcript", response_model=APIResponse)
async def get_video_transcript(video_id: str):
    """获取视频逐字稿"""
    transcript = mock_data.get_video_transcript(video_id)
    lines = [TranscriptLine(**l) for l in transcript["lines"]]
    return APIResponse(
        data=VideoTranscriptResponse(
            video_id=video_id,
            full_transcript=transcript["full_transcript"],
            lines=lines
        )
    )


@router.post("/video/rewrite", response_model=APIResponse)
async def rewrite_video(request: VideoRewriteRequest):
    """改写视频文案"""
    if not ai_manager.get_current_service() or not ai_manager.get_current_service().is_available():
        return APIResponse(
            success=False,
            message="请先配置AI服务",
            data=None
        )

    rewritten = ai_manager.rewrite_transcript(
        request.transcript,
        request.style.value,
        request.target_duration or 60
    )

    return APIResponse(data={"rewritten_text": rewritten})


@router.post("/content/generate", response_model=APIResponse)
async def generate_content(request: ContentGenerateRequest):
    """生成分镜头脚本和文案"""
    if not ai_manager.get_current_service() or not ai_manager.get_current_service().is_available():
        # 返回模拟数据
        mock_script = [
            {"scene": 1, "duration": "0:00-0:05", "visual": "开头吸引眼球", "audio": "大家好", "notes": "要有冲击力"},
            {"scene": 2, "duration": "0:05-0:15", "visual": "展示主题", "audio": f"今天我们来聊{request.topic}", "notes": ""},
            {"scene": 3, "duration": "0:15-0:30", "visual": "详细讲解", "audio": "具体内容...", "notes": "配合图表"},
            {"scene": 4, "duration": "0:30-0:45", "visual": "总结升华", "audio": "希望对你有帮助", "notes": ""},
            {"scene": 5, "duration": "0:45-0:60", "visual": "引导关注", "audio": "点赞关注", "notes": "强调CTA"}
        ]
        mock_copy = {
            "title": f"{request.topic}爆款标题",
            "hooks": ["你还不知道的秘密！", "90%的人都做错了", "建议收藏！"],
            "call_to_action": "点赞关注，下期更精彩！",
            "tags": [f"#{request.topic}", "#新媒体", "#干货"]
        }
        return APIResponse(
            data=ContentGenerateResponse(
                topic=request.topic,
                script=[Shot(**s) for s in mock_script],
                copywriting=Copywriting(**mock_copy)
            )
        )

    result = ai_manager.generate_content_script(
        request.topic,
        request.platform.value,
        request.duration,
        request.style.value
    )

    script = [Shot(**s) for s in result.get("script", [])]
    copywriting = Copywriting(**result.get("copywriting", {}))

    return APIResponse(
        data=ContentGenerateResponse(
            topic=request.topic,
            script=script,
            copywriting=copywriting
        )
    )


@router.post("/media/upload")
async def upload_media(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """上传音视频文件"""
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "pending"}

    content = await file.read()
    file_path = media_processor.save_uploaded_file(content, file.filename)

    # 后台处理
    background_tasks.add_task(process_media_task, task_id, file_path)

    return APIResponse(data={"task_id": task_id, "status": "processing"})


def process_media_task(task_id: str, file_path: str):
    """后台处理媒体文件"""
    tasks[task_id] = {"status": "processing"}
    try:
        result = media_processor.transcribe_audio(file_path)

        outline = []
        if ai_manager.get_current_service() and ai_manager.get_current_service().is_available():
            outline_data = ai_manager.generate_outline(result["transcript"])
            outline = [OutlineItem(**o) for o in outline_data]
        else:
            outline = [
                {"section": "1", "title": "开场", "summary": "打招呼介绍主题"},
                {"section": "2", "title": "主题内容", "summary": "核心内容讲解"},
                {"section": "3", "title": "总结", "summary": "总结和引导关注"}
            ]
            outline = [OutlineItem(**o) for o in outline]

        tasks[task_id] = {
            "status": "completed",
            "transcript": result["transcript"],
            "outline": outline,
            "timestamps": result["timestamps"]
        }
    except Exception as e:
        tasks[task_id] = {"status": "failed", "error": str(e)}


@router.get("/media/{task_id}/status")
async def get_media_status(task_id: str):
    """获取媒体处理状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    return APIResponse(data=tasks[task_id])


@router.get("/media/{task_id}/result")
async def get_media_result(task_id: str):
    """获取媒体处理结果"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]
    if task["status"] != "completed":
        return APIResponse(data={"status": task["status"]})

    return APIResponse(
        data=MediaTranscribeResponse(
            task_id=task_id,
            status=task["status"],
            transcript=task.get("transcript"),
            outline=task.get("outline"),
            timestamps=[TranscriptLine(**t) for t in task.get("timestamps", [])]
        )
    )


@router.post("/ai/configure")
async def configure_ai(provider: str, api_key: str, base_url: str = None, model: str = None):
    """配置AI服务"""
    try:
        ai_manager.configure_service(provider, api_key, base_url, model)
        return APIResponse(message="AI服务配置成功")
    except Exception as e:
        return APIResponse(success=False, message=str(e))

