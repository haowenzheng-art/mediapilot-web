"""
媒体处理业务逻辑
"""
import uuid
from fastapi import UploadFile, File
from typing import Dict, Any

from models.schemas.response import (
    TranscriptLine,
    OutlineItem,
    MediaTranscribeResponse,
    APIResponse,
)
from backend.core.ai_service import ai_manager
from backend.core.media_processor import MockMediaProcessor


class MediaService:
    """媒体处理服务"""

    def __init__(self, upload_dir: str):
        self.media_processor = MockMediaProcessor(upload_dir)
        self.tasks: Dict[str, Dict[str, Any]] = {}

    async def upload_and_process(
        self,
        file_content: bytes,
        filename: str
    ) -> Dict[str, str]:
        """
        上传并处理媒体文件

        Args:
            file_content: 文件内容
            filename: 文件名

        Returns:
            包含 task_id 和 status 的字典
        """
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {"status": "pending"}

        # 保存文件并开始处理
        file_path = self.media_processor.save_uploaded_file(file_content, filename)
        await self._process_media_task(task_id, file_path)

        return {"task_id": task_id, "status": "processing"}

    async def get_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取处理状态

        Args:
            task_id: 任务 ID

        Returns:
            任务状态字典
        """
        return self.tasks.get(task_id, {})

    async def get_result(self, task_id: str) -> MediaTranscribeResponse:
        """
        获取处理结果

        Args:
            task_id: 任务 ID

        Returns:
            媒体转写响应
        """
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"任务 {task_id} 不存在")

        if task["status"] != "completed":
            return MediaTranscribeResponse(
                task_id=task_id,
                status=task["status"]
            )

        return MediaTranscribeResponse(
            task_id=task_id,
            status=task["status"],
            transcript=task.get("transcript"),
            outline=task.get("outline"),
            timestamps=[TranscriptLine(**t) for t in task.get("timestamps", [])]
        )

    async def _process_media_task(self, task_id: str, file_path: str):
        """
        后台处理媒体文件

        Args:
            task_id: 任务 ID
            file_path: 文件路径
        """
        self.tasks[task_id] = {"status": "processing"}

        try:
            result = self.media_processor.transcribe_audio(file_path)

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

            self.tasks[task_id] = {
                "status": "completed",
                "transcript": result["transcript"],
                "outline": outline,
                "timestamps": result["timestamps"]
            }
        except Exception as e:
            self.tasks[task_id] = {"status": "failed", "error": str(e)}

    def task_exists(self, task_id: str) -> bool:
        """
        检查任务是否存在

        Args:
            task_id: 任务 ID

        Returns:
            任务是否存在
        """
        return task_id in self.tasks
