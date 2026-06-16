"""
数据库表定义（优化版本）
使用 Python 类型提示，遵循 PEP 8 标准

根据 database-architecture-review.md 的建议进行优化：

1. 添加复合索引（username + email）
2. 软查询过滤软删除记录（如需要）
"""
import logging
import json
from sqlalchemy import Column, String, Integer, Text, DateTime, TypeDecorator, Boolean, Index, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Optional

# 从 base.py 导入基类，确保所有表使用同一个 Base
from .base import Base

logger = logging.getLogger(__name__)


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


class TaskTable(Base):
    """任务表（优化版本）"""
    __tablename__ = "tasks"

    # 主键字段
    task_id = Column(String(36), primary_key=True, index=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    transcript = Column(Text, nullable=True)
    outline = Column(JSONColumn, nullable=True)
    timestamps = Column(JSONColumn, nullable=True)
    error = Column(Text, nullable=True)

    # 软删除相关字段
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)

    # 关联字段 - 添加外键约束
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 创建时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # 定义关系
    user = relationship("UserTable", back_populates="user_tasks")

    # 索引
    __table_args__ = (
        Index('idx_task_status', 'status'),
        Index('idx_task_user_deleted', 'is_deleted'),
        Index('idx_task_created_at', 'created_at'),
    )


class UserTable(Base):
    """用户表（优化版本）"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True, index=True)
    quota_balance = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, nullable=False, default=True)
    is_admin = Column(Boolean, nullable=False, default=False)

    # 创建时间戳
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # 反向关系
    user_tasks = relationship("TaskTable", back_populates="user")
    user_personas = relationship("UserPersonaTable")
    user_subscriptions = relationship("SubscriptionTable")
    token_blacklist_entries = relationship("TokenBlacklistTable", back_populates="user")
    user_copywritings = relationship("CopywritingTable")

    # 复合索引
    __table_args__ = (
        Index('idx_user_username_email', 'username', 'email'),
        Index('idx_user_active_quota', 'is_active', 'quota_balance'),
    )


class UserPersonaTable(Base):
    """用户人设表"""
    __tablename__ = "user_personas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    persona_description = Column(Text, nullable=False)
    last_used_at = Column(DateTime, server_default=func.now(), index=True)
    created_at = Column(DateTime, server_default=func.now())

    # 定义关系
    user = relationship("UserTable")

    # 索引
    __table_args__ = (
        Index('idx_persona_user_last_used', 'user_id', 'last_used_at'),
    )


class SubscriptionTable(Base):
    """话题订阅表"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)
    description = Column(String(200), nullable=True)
    frequency = Column(String(20), nullable=False, default="daily")  # daily, every_3_days
    status = Column(String(20), nullable=False, default="active", index=True)  # active, paused
    last_pushed_at = Column(DateTime, nullable=True)
    next_push_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # 定义关系
    user = relationship("UserTable")
    push_records = relationship("PushRecordTable", back_populates="subscription")

    # 索引
    __table_args__ = (
        Index('idx_subscription_user_status', 'user_id', 'status'),
        Index('idx_subscription_next_push', 'next_push_at'),
    )


class PushRecordTable(Base):
    """推送记录表"""
    __tablename__ = "push_records"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)
    hot_topic_data = Column(JSONColumn, nullable=True)
    status = Column(String(20), nullable=False, default="new", index=True)  # new, read
    pushed_at = Column(DateTime, server_default=func.now(), index=True)
    read_at = Column(DateTime, nullable=True)

    # 定义关系
    subscription = relationship("SubscriptionTable", back_populates="push_records")

    # 索引
    __table_args__ = (
        Index('idx_push_subscription_status', 'subscription_id', 'status'),
        Index('idx_push_pushed_at', 'pushed_at'),
    )


class TokenBlacklistTable(Base):
    """刷新令牌黑名单表"""
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True,
                        comment="SHA-256 hash of the refresh token")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_revoked = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("UserTable", back_populates="token_blacklist_entries")

    __table_args__ = (
        Index('idx_token_blacklist_user_revoked', 'user_id', 'is_revoked'),
    )


class ContentTable(Base):
    """内容表（内容库）"""
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    content_type = Column(String(20), nullable=False, index=True)  # copywriting, shoot_script
    content_id = Column(String(100), nullable=False, index=True)
    hot_topic_id = Column(String(100), nullable=True, index=True)
    hot_topic_title = Column(String(500), nullable=True)
    hot_topic_source = Column(String(50), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    mode = Column(String(20), nullable=True)
    persona = Column(String(500), nullable=True)
    platform = Column(String(20), nullable=True)
    style = Column(String(20), nullable=True)
    is_processed = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime, nullable=True)

    # 定义关系
    user = relationship("UserTable")

    # 索引
    __table_args__ = (
        Index('idx_content_user_type', 'user_id', 'content_type'),
        Index('idx_content_topic', 'hot_topic_id'),
        Index('idx_content_processed', 'is_processed'),
        Index('idx_content_created_at', 'created_at'),
    )


class HotTopicTrendTable(Base):
    """热点趋势表（追踪热点热度变化）"""
    __tablename__ = "hot_topic_trends"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    hot_topic_id = Column(String(100), nullable=False, index=True)
    hot_topic_title = Column(String(500), nullable=True)
    hot_topic_source = Column(String(50), nullable=True)
    heat_score = Column(Integer, nullable=True)  # 热度分数
    trend_direction = Column(String(20), nullable=True)  # up, down, stable
    recorded_at = Column(DateTime, server_default=func.now(), index=True)

    # 索引
    __table_args__ = (
        Index('idx_trend_topic', 'hot_topic_id'),
        Index('idx_trend_recorded', 'recorded_at'),
        Index('idx_trend_topic_time', 'hot_topic_id', 'recorded_at'),
    )
