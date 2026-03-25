"""
任务领域模型
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import json


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Task:
    """异步任务实体"""

    def __init__(
        self,
        task_id: str,
        status: TaskStatus = TaskStatus.PENDING,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.task_id = task_id
        self.status = status
        self.result = result or {}
        self.error = error
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def update_status(
        self,
        status: TaskStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        """更新任务状态"""
        self.status = status
        self.updated_at = datetime.utcnow()
        if result is not None:
            self.result = result
        if error is not None:
            self.error = error

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
