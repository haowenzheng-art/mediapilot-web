"""
媒体处理路由
"""
import os
import json
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.services.media_service import MediaService
from backend.services.video_edit_service import VideoEditService
from backend.core.transcribe_engine import TranscribeEngineManager
from backend.repository.video_edit_repo import VideoEditRepository
from backend.models.schemas.response import VideoEditTaskSummary, VideoEditReapplyRequest
from backend.config.settings import get_upload_dir, settings
from backend.config.database import get_db
from backend.api.dependencies import get_current_user
from backend.models.database.tables import UserTable
from backend.services.auth_service_typed import auth_service
from backend.utils.api_response import (
    success_response,
    error_response,
    ErrorCode
)

router = APIRouter(prefix="/media", tags=["媒体处理"])

# 全局转写引擎引用（在 main.py 中初始化）
_transcribe_engine: Optional[TranscribeEngineManager] = None


def set_transcribe_engine(engine: Optional[TranscribeEngineManager]):
    """设置转写引擎"""
    global _transcribe_engine
    _transcribe_engine = engine


def get_media_service(db: Session = Depends(get_db)) -> MediaService:
    """获取 MediaService 实例（依赖注入）"""
    return MediaService(
        get_upload_dir(),
        db,
        transcribe_engine=_transcribe_engine,
        use_mock=settings.USE_MOCK_TRANSCRIBE
    )


def get_video_edit_service(db: Session = Depends(get_db)) -> VideoEditService:
    """获取 VideoEditService 实例（依赖注入）"""
    return VideoEditService(
        upload_dir=get_upload_dir(),
        db_session=db,
        transcribe_engine=_transcribe_engine,
        subtitle_format="srt",
    )


@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    media_service: MediaService = Depends(get_media_service),
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传音视频文件"""
    filename_lower = file.filename.lower() if file.filename else ""
    if filename_lower.endswith(('.mp3', '.wav', '.m4a', '.aac')):
        feature = "transcribe_audio"
    else:
        feature = "transcribe_video"

    has_quota, balance = auth_service.check_quota(db, current_user.id, feature)
    if not has_quota:
        return error_response(
            code=ErrorCode.FORBIDDEN,
            message=f"配额不足，当前余额: {balance}",
            status_code=status.HTTP_403_FORBIDDEN
        )

    content = await file.read()
    result = await media_service.upload_and_process(content, file.filename, user_id=current_user.id)

    auth_service.deduct_quota(db, current_user.id, feature)

    return success_response(data=result, message="文件上传成功，正在处理")


@router.get("/task/{task_id}")
async def get_media_task(
    task_id: str,
    media_service: MediaService = Depends(get_media_service)
):
    """获取媒体处理任务状态和结果"""
    if not media_service.task_exists(task_id):
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="任务不存在",
            status_code=status.HTTP_404_NOT_FOUND
        )
    result = await media_service.get_result(task_id)
    return success_response(data=result.model_dump(), message="获取任务状态成功")


# ==================== 视频剪辑（AI 自动去除磕巴片段） ====================

@router.get("/video-edit/tasks")
async def list_video_edit_tasks(
    skip: int = Query(0, ge=0, description="分页跳过"),
    limit: int = Query(20, ge=1, le=100, description="分页大小"),
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """B1: 列出当前用户的视频剪辑历史任务（按 created_at 倒序）"""
    repo = VideoEditRepository(db)
    tasks = repo.get_tasks_by_user(current_user.id, skip=skip, limit=limit)
    items = []
    for t in tasks:
        items.append(VideoEditTaskSummary(
            task_id=t.task_id,
            status=t.status,
            source_video_name=t.source_video_name,
            # strength 存在 edit_config JSON 里（不单独占字段）
            strength=(t.edit_config or {}).get("strength") if t.edit_config else None,
            original_duration=t.original_duration,
            final_duration=t.final_duration,
            output_video_path=t.output_video_path,
            preview_video_path=t.preview_video_path,
            subtitle_path=t.subtitle_path,
            subtitle_format=t.subtitle_format,
            error=t.error,
            created_at=t.created_at.isoformat() if t.created_at else None,
            updated_at=t.updated_at.isoformat() if t.updated_at else None,
            # C1: 关联的热点（从 edit_config 提取）
            hot_topic_id=(t.edit_config or {}).get("hot_topic_id") if t.edit_config else None,
            hot_topic_title=(t.edit_config or {}).get("hot_topic_title") if t.edit_config else None,
            hot_topic_source=(t.edit_config or {}).get("hot_topic_source") if t.edit_config else None,
        ))
    return success_response(
        data={"tasks": items, "total": len(items), "skip": skip, "limit": limit},
        message="获取剪辑任务列表成功",
    )


@router.post("/video-edit/upload")
async def upload_video_for_edit(
    file: UploadFile = File(...),
    strength: Optional[str] = Form("medium"),
    config: Optional[str] = Form(None),
    video_edit_service: VideoEditService = Depends(get_video_edit_service),
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传视频进行 AI 剪辑（自动识别并删除无效片段）"""
    has_quota, balance = auth_service.check_quota(db, current_user.id, "video_edit")
    if not has_quota:
        return error_response(
            code=ErrorCode.FORBIDDEN,
            message=f"配额不足，当前余额: {balance}",
            status_code=status.HTTP_403_FORBIDDEN
        )

    # 构造 edit_config
    edit_config = {"strength": strength}
    if config:
        try:
            cfg_dict = json.loads(config)
            edit_config = {**edit_config, **cfg_dict}
        except json.JSONDecodeError:
            return error_response(
                code=ErrorCode.INVALID_INPUT,
                message="config 参数不是有效的 JSON",
                status_code=status.HTTP_400_BAD_REQUEST
            )

    content = await file.read()
    result = await video_edit_service.upload_and_process(
        content, file.filename, user_id=current_user.id, edit_config=edit_config
    )
    auth_service.deduct_quota(db, current_user.id, "video_edit")
    return success_response(data=result, message="视频上传成功，AI 剪辑中")


@router.get("/video-edit/task/{task_id}")
async def get_video_edit_task(
    task_id: str,
    video_edit_service: VideoEditService = Depends(get_video_edit_service),
    current_user: UserTable = Depends(get_current_user),
):
    """获取视频剪辑任务状态和结果"""
    task = video_edit_service.get_task_owned_by(task_id, current_user.id)
    if not task:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="任务不存在或无权访问",
            status_code=status.HTTP_404_NOT_FOUND
        )
    result = await video_edit_service.get_result(task_id, current_user.id)
    return success_response(data=result.model_dump(), message="获取任务状态成功")


@router.get("/video-edit/{task_id}/segments")
async def get_video_edit_segments(
    task_id: str,
    video_edit_service: VideoEditService = Depends(get_video_edit_service),
    current_user: UserTable = Depends(get_current_user),
):
    """获取剪辑保留/删除片段详情"""
    task = video_edit_service.get_task_owned_by(task_id, current_user.id)
    if not task:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="任务不存在或无权访问",
            status_code=status.HTTP_404_NOT_FOUND
        )
    result = await video_edit_service.get_result(task_id, current_user.id)
    return success_response(
        data={
            "kept_segments": [s.model_dump() for s in result.kept_segments or []],
            "removed_segments": [s.model_dump() for s in result.removed_segments or []],
            "total_kept": len(result.kept_segments or []),
            "total_removed": len(result.removed_segments or []),
        },
        message="获取片段信息成功"
    )


@router.get("/video-edit/{task_id}/download/{file_type}")
async def download_video_edit_file(
    task_id: str,
    file_type: str,  # "video" or "subtitle"
    video_edit_service: VideoEditService = Depends(get_video_edit_service),
    current_user: UserTable = Depends(get_current_user),
):
    """下载剪辑后的视频或字幕文件"""
    if file_type not in ("video", "subtitle"):
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="file_type 必须为 video 或 subtitle",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    task = video_edit_service.get_task_owned_by(task_id, current_user.id)
    if not task:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="任务不存在或无权访问",
            status_code=status.HTTP_404_NOT_FOUND
        )
    if task.status != "completed":
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"任务未完成，当前状态: {task.status}",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    if file_type == "video":
        file_path = task.output_video_path
        if not file_path or not os.path.isfile(file_path):
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message="视频文件不存在",
                status_code=status.HTTP_404_NOT_FOUND
            )
        filename = f"edited_{task.source_video_name or task_id}.mp4"
        media_type = "video/mp4"
    else:
        file_path = task.subtitle_path
        if not file_path or not os.path.isfile(file_path):
            return error_response(
                code=ErrorCode.NOT_FOUND,
                message="字幕文件不存在",
                status_code=status.HTTP_404_NOT_FOUND
            )
        ext = task.subtitle_format or "srt"
        filename = f"subtitle_{task_id}.{ext}"
        media_type = "text/plain"

    return FileResponse(
        path=file_path, filename=filename, media_type=media_type
    )


@router.post("/video-edit/{task_id}/reapply")
async def reapply_video_edit_segments(
    task_id: str,
    request: VideoEditReapplyRequest,
    video_edit_service: VideoEditService = Depends(get_video_edit_service),
    current_user: UserTable = Depends(get_current_user),
):
    """B3: 用户微调 kept_segments 后重新生成视频/字幕/预览

    Body: { "kept_segments": [[start, end], ...] }

    不重新跑转写 + LLM，复用 task.word_timestamps，仅重跑 ffmpeg cut + subtitle。
    不扣配额（属于同一任务的微调，不是新任务）。
    """
    task = video_edit_service.get_task_owned_by(task_id, current_user.id)
    if not task:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="任务不存在或无权访问",
            status_code=status.HTTP_404_NOT_FOUND
        )
    try:
        result = await video_edit_service.reapply_segments(task_id, current_user.id, request)
    except ValueError as e:
        msg = str(e)
        # 区分 "无权" → 403, "不存在" → 404, 其他 → 400
        if "无权" in msg:
            return error_response(
                code=ErrorCode.FORBIDDEN, message=msg,
                status_code=status.HTTP_403_FORBIDDEN
            )
        if "不存在" in msg:
            return error_response(
                code=ErrorCode.NOT_FOUND, message=msg,
                status_code=status.HTTP_404_NOT_FOUND
            )
        return error_response(
            code=ErrorCode.INVALID_INPUT, message=msg,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except RuntimeError as e:
        return error_response(
            code=ErrorCode.INTERNAL_ERROR, message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    return success_response(data=result, message="已应用微调并重新生成视频")


@router.get("/video-edit/{task_id}/preview")
async def get_video_edit_preview(
    task_id: str,
    video_edit_service: VideoEditService = Depends(get_video_edit_service),
    current_user: UserTable = Depends(get_current_user),
):
    """360p 预览视频端点（v3 改造）

    与 /download/video 区别：
    - 返回 inline（不是 attachment），浏览器 <video> 标签可直接播放
    - 加 Accept-Ranges: bytes 支持 seek
    - 加 Cache-Control: private, max-age=3600，二次访问秒开
    - 404 场景：任务不存在/未完成/preview 未生成（视频剪辑失败兜底）

    用户先预览，满意后再点下载按钮调 /download/video 拉原画质 mp4。
    """
    task = video_edit_service.get_task_owned_by(task_id, current_user.id)
    if not task:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="任务不存在或无权访问",
            status_code=status.HTTP_404_NOT_FOUND
        )
    if task.status != "completed":
        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message=f"任务未完成，当前状态: {task.status}",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    preview_path = task.preview_video_path
    if not preview_path or not os.path.isfile(preview_path):
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="预览未生成或已失效，请重新上传视频",
            status_code=status.HTTP_404_NOT_FOUND
        )

    return FileResponse(
        path=preview_path,
        filename=f"preview_{task_id}.mp4",
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",                  # 支持 Range 请求（seek 关键）
            "Cache-Control": "private, max-age=3600",  # 浏览器缓存 1 小时
            "Content-Disposition": "inline",           # 浏览器内播放，不弹下载
        },
    )
