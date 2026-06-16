"""口播文案数据表"""
from sqlalchemy import Column, String, Text, DateTime, TypeDecorator, Integer, ForeignKey, Index, func
from sqlalchemy.orm import relationship
import json

from .base import Base


class JSONColumn(TypeDecorator):
    """自定义 JSON 列，兼容 SQLite"""
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value, ensure_ascii=False)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value


class CopywritingTable(Base):
    """口播文案表"""
    __tablename__ = "copywritings"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    copywriting_id = Column(String(100), nullable=False, unique=True, index=True)
    title = Column(String(500), nullable=False)
    hooks = Column(JSONColumn, nullable=True)
    content = Column(Text, nullable=True)
    mode = Column(String(20), nullable=True)  # from_zero, hotspot, rewrite
    persona = Column(String(500), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    user = relationship("UserTable", back_populates="user_copywritings")

    __table_args__ = (
        Index('idx_copywriting_user_mode', 'user_id', 'mode'),
        Index('idx_copywriting_created_at', 'created_at'),
    )
