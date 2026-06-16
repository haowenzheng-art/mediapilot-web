"""
数据库基础配置
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

from backend.config.settings import settings


class Base(DeclarativeBase):
    pass


# 创建引擎（与 config/database.py 保持一致）
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)
