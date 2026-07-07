"""
视频剪辑任务数据访问
"""
from typing import Optional, List
from sqlalchemy.orm import Session

from backend.repository.base_repository import BaseRepository
from backend.models.database.tables import VideoEditTaskTable


class VideoEditRepository(BaseRepository[VideoEditTaskTable]):
    """视频剪辑任务数据访问"""

    def __init__(self, db: Session):
        super().__init__(db, VideoEditTaskTable)

    def get_by_task_id(self, task_id: str) -> Optional[VideoEditTaskTable]:
        """根据 task_id 查询"""
        return self.db.query(VideoEditTaskTable).filter(
            VideoEditTaskTable.task_id == task_id,
            VideoEditTaskTable.is_deleted == False
        ).first()

    def task_exists(self, task_id: str) -> bool:
        """检查任务是否存在"""
        return self.get_by_task_id(task_id) is not None

    def create_task(
        self,
        task_id: str,
        source_video_path: str,
        user_id: int,
        source_video_name: Optional[str] = None,
        edit_config: Optional[dict] = None,
    ) -> VideoEditTaskTable:
        """创建新任务"""
        task = VideoEditTaskTable(
            task_id=task_id,
            source_video_path=source_video_path,
            source_video_name=source_video_name,
            user_id=user_id,
            status="pending",
            edit_config=edit_config,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update_status(
        self,
        task_id: str,
        status: str,
        transcript: Optional[str] = None,
        word_timestamps: Optional[list] = None,
        kept_segments: Optional[list] = None,
        removed_segments: Optional[list] = None,
        llm_reasoning: Optional[list] = None,
        output_video_path: Optional[str] = None,
        subtitle_path: Optional[str] = None,
        subtitle_format: Optional[str] = None,
        original_duration: Optional[float] = None,
        final_duration: Optional[float] = None,
        error: Optional[str] = None,
        edit_config: Optional[dict] = None,
        preview_video_path: Optional[str] = None,
        preview_size_bytes: Optional[int] = None,
    ) -> Optional[VideoEditTaskTable]:
        """更新任务状态和结果"""
        task = self.get_by_task_id(task_id)
        if not task:
            return None
        task.status = status
        if transcript is not None:
            task.transcript = transcript
        if word_timestamps is not None:
            task.word_timestamps = word_timestamps
        if kept_segments is not None:
            task.kept_segments = kept_segments
        if removed_segments is not None:
            task.removed_segments = removed_segments
        if llm_reasoning is not None:
            task.llm_reasoning = llm_reasoning
        if output_video_path is not None:
            task.output_video_path = output_video_path
        if subtitle_path is not None:
            task.subtitle_path = subtitle_path
        if subtitle_format is not None:
            task.subtitle_format = subtitle_format
        if original_duration is not None:
            task.original_duration = original_duration
        if final_duration is not None:
            task.final_duration = final_duration
        if error is not None:
            task.error = error
        if edit_config is not None:
            task.edit_config = edit_config
        if preview_video_path is not None:
            task.preview_video_path = preview_video_path
        if preview_size_bytes is not None:
            task.preview_size_bytes = preview_size_bytes
        self.db.commit()
        self.db.refresh(task)
        return task

    def soft_delete(self, task_id: str) -> bool:
        """软删除任务"""
        task = self.get_by_task_id(task_id)
        if not task:
            return False
        from datetime import datetime
        task.is_deleted = True
        task.deleted_at = datetime.utcnow()
        self.db.commit()
        return True

    def get_tasks_by_user(
        self, user_id: int, skip: int = 0, limit: int = 20
    ) -> List[VideoEditTaskTable]:
        """获取用户的任务列表"""
        return self.db.query(VideoEditTaskTable).filter(
            VideoEditTaskTable.user_id == user_id,
            VideoEditTaskTable.is_deleted == False
        ).order_by(VideoEditTaskTable.created_at.desc()).offset(skip).limit(limit).all()
