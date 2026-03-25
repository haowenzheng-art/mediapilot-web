"""
数据库表定义
"""
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from .base import Base


class TaskTable(Base):
    """任务表"""
    __tablename__ = "tasks"

    task_id = Column(String(36), primary_key=True, index=True)
    status = Column(String(20), nullable=False, default="pending")
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
