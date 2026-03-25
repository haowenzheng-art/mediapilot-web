"""
数据访问基类
提供通用的 CRUD 操作
"""
from typing import Generic, TypeVar, List, Optional, Type, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    数据访问基类

    子类使用示例:
        class TaskRepository(BaseRepository[TaskTable]):
            def __init__(self, db: Session):
                super().__init__(db, TaskTable)
    """

    def __init__(self, db: Session, model: Type[ModelType]):
        self.db = db
        self.model = model

    def get_by_id(self, id: Any) -> Optional[ModelType]:
        """根据 ID 查询"""
        return self.db.query(self.model).filter(
            getattr(self.model, "task_id") == id
        ).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """查询所有记录"""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """创建记录"""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, obj_in: Dict[str, Any]) -> ModelType:
        """更新记录"""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: Any) -> bool:
        """删除记录"""
        obj = self.get_by_id(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False

    def count(self) -> int:
        """统计记录数"""
        return self.db.query(self.model).count()
