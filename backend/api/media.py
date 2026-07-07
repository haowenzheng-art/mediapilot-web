"""
媒体处理路由
"""
import os
import json
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.services.media_service import MediaService
from backend.services.video_edit_service import VideoEditService
from backend.core.transcribe_engine import TranscribeEngineManager
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
