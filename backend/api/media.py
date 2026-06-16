"""
媒体处理路由
"""
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from sqlalchemy.orm import Session

from backend.services.media_service import MediaService
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
