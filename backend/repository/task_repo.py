"""
任务数据访问
"""
from typing import Optional
from sqlalchemy.orm import Session
from .base_repository import BaseRepository
from models.database.tables import TaskTable


class TaskRepository(BaseRepository[TaskTable]):
    """任务数据访问"""

    def __init__(self, db: Session):
        super().__init__(db, TaskTable)

    def get_by_task_id(self, task_id: str) -> Optional[TaskTable]:
        """根据任务 ID 查询"""
        return self.db.query(TaskTable).filter(
            TaskTable.task_id == task_id
        ).first()

    def update_status(
        self,
        task_id: str,
        status: str,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[TaskTable]:
        """更新任务状态"""
        task = self.get_by_task_id(task_id)
        if task:
            task.status = status
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error
            self.db.commit()
            self.db.refresh(task)
        return task
