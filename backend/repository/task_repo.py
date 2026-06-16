"""
任务数据访问
"""
from typing import Optional, List, Dict, Any
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

    def create_task(self, task_id: str, status: str = "pending", user_id: int = None) -> TaskTable:
        """创建新任务"""
        task = TaskTable(task_id=task_id, status=status, user_id=user_id)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update_status(
        self,
        task_id: str,
        status: str,
        transcript: Optional[str] = None,
        outline: Optional[List[Dict]] = None,
        timestamps: Optional[List[Dict]] = None,
        error: Optional[str] = None,
    ) -> Optional[TaskTable]:
        """更新任务状态和结果"""
        task = self.get_by_task_id(task_id)
        if task:
            task.status = status
            if transcript is not None:
                task.transcript = transcript
            if outline is not None:
                task.outline = outline
            if timestamps is not None:
                task.timestamps = timestamps
            if error is not None:
                task.error = error
            self.db.commit()
            self.db.refresh(task)
        return task

    def get_tasks_by_status(self, status: str) -> List[TaskTable]:
        """根据状态查询任务列表"""
        return self.db.query(TaskTable).filter(
            TaskTable.status == status
        ).all()

    def task_exists(self, task_id: str) -> bool:
        """检查任务是否存在"""
        return self.db.query(TaskTable).filter(
            TaskTable.task_id == task_id
        ).first() is not None

    def create(self, task_id: str, user_id: int, task_type: str, status: str, metadata: Optional[Dict] = None) -> TaskTable:
        """创建任务（支持 type 字段）"""
        task = TaskTable(
            task_id=task_id,
            user_id=user_id,
            status=status,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update(self, task_id: str, status: str, result: Optional[Any] = None, error: Optional[str] = None) -> Optional[TaskTable]:
        """更新任务状态和结果"""
        task = self.get_by_task_id(task_id)
        if task:
            task.status = status
            if result is not None:
                task.outline = result if isinstance(result, dict) else None
                task.transcript = str(result) if result and not isinstance(result, dict) else task.transcript
            if error is not None:
                task.error = error
            self.db.commit()
            self.db.refresh(task)
        return task
