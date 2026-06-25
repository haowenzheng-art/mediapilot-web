"""
媒体处理业务逻辑
"""
import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.models.schemas.response import (
    TranscriptLine,
    OutlineItem,
    MediaTranscribeResponse,
)
from backend.core.media_processor import MediaProcessor, MockMediaProcessor
from backend.core.transcribe_engine import TranscribeEngineManager
from backend.repository.task_repo import TaskRepository
from backend.config.database import SessionLocal

logger = logging.getLogger(__name__)


class MediaService:
    """媒体处理服务"""

    def __init__(
        self,
        upload_dir: str,
        db_session: Session,
        transcribe_engine: Optional[TranscribeEngineManager] = None,
        use_mock: bool = False
    ):
        if use_mock:
            self.media_processor = MockMediaProcessor(upload_dir)
        else:
            self.media_processor = MediaProcessor(upload_dir, transcribe_engine)
        self.db = db_session
        self.task_repo = TaskRepository(db_session)
        self.transcribe_engine = transcribe_engine

    async def upload_and_process(
        self,
        file_content: bytes,
        filename: str,
        user_id: int = None
    ) -> Dict[str, str]:
        """
        上传并处理媒体文件

        Args:
            file_content: 文件内容
            filename: 文件名
            user_id: 用户 ID

        Returns:
            包含 task_id 和 status 的字典
        """
        task_id = str(uuid.uuid4())
        self.task_repo.create_task(task_id, "pending", user_id=user_id)

        # 保存文件
        file_path = self.media_processor.save_uploaded_file(file_content, filename)

        # 异步处理，不阻塞 upload 响应。
        # 注意：原 self.db 是 FastAPI 注入的 session，请求结束后会被关闭，
        # 后台任务必须自己开新 session，不能复用 self.task_repo
        asyncio.create_task(self._process_media_task_bg(task_id, file_path))

        return {"task_id": task_id, "status": "processing"}

    async def _process_media_task_bg(self, task_id: str, file_path: str):
        """后台任务包装器：独立 DB session，避免请求结束后 session 关闭"""
        db = SessionLocal()
        try:
            task_repo = TaskRepository(db)
            task_repo.update_status(task_id, "processing")
            try:
                result = await self.media_processor.transcribe_audio_async(file_path)

                outline_dict = [
                    {"section": "1", "title": "开场", "summary": "打招呼介绍主题"},
                    {"section": "2", "title": "主题内容", "summary": "核心内容讲解"},
                    {"section": "3", "title": "总结", "summary": "总结和引导关注"}
                ]

                timestamps_dict = result["timestamps"] if result.get("timestamps") else []

                task_repo.update_status(
                    task_id,
                    "completed",
                    transcript=result["transcript"],
                    outline=outline_dict,
                    timestamps=timestamps_dict
                )
                logger.info(f"媒体任务完成: {task_id}")
            except Exception as e:
                logger.error(f"媒体任务失败 {task_id}: {e}", exc_info=True)
                task_repo.update_status(task_id, "failed", error=str(e))
        finally:
            db.close()

    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取处理状态

        Args:
            task_id: 任务 ID

        Returns:
            任务状态字典
        """
        task = self.task_repo.get_by_task_id(task_id)
        if not task:
            return {}
        return {"status": task.status, "error": task.error}

    async def get_result(self, task_id: str) -> MediaTranscribeResponse:
        """
        获取处理结果

        Args:
            task_id: 任务 ID

        Returns:
            媒体转写响应
        """
        task = self.task_repo.get_by_task_id(task_id)
        if not task:
            raise ValueError(f"任务 {task_id} 不存在")

        timestamps = None
        if task.status == "completed" and task.timestamps:
            timestamps = [TranscriptLine(**t) for t in task.timestamps]

        outline = None
        if task.status == "completed" and task.outline:
            outline = [OutlineItem(**o) for o in task.outline]

        return MediaTranscribeResponse(
            task_id=task_id,
            status=task.status,
            transcript=task.transcript if task.status == "completed" else None,
            outline=outline,
            timestamps=timestamps,
            error=task.error
        )

    def task_exists(self, task_id: str) -> bool:
        """
        检查任务是否存在

        Args:
            task_id: 任务 ID

        Returns:
            任务是否存在
        """
        return self.task_repo.task_exists(task_id)
