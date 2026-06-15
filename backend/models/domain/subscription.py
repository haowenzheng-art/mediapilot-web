"""
话题订阅相关的领域模型
定义请求和响应的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SubscriptionStatus(str, Enum):
    """订阅状态"""
    ACTIVE = "active"
    PAUSED = "paused"


class FrequencyType(str, Enum):
    """更新频率"""
    DAILY = "daily"
    EVERY_3_DAYS = "every_3_days"


class SubscriptionCreate(BaseModel):
    """创建订阅请求"""
    topic: str = Field(..., min_length=1, max_length=100, description="话题关键词")
    description: Optional[str] = Field(None, max_length=200, description="话题描述")
    frequency: FrequencyType = Field(default=FrequencyType.DAILY, description="更新频率")


class SubscriptionUpdate(BaseModel):
    """更新订阅请求"""
    topic: Optional[str] = Field(None, min_length=1, max_length=100, description="话题关键词")
    description: Optional[str] = Field(None, max_length=200, description="话题描述")
    frequency: Optional[FrequencyType] = Field(None, description="更新频率")
    status: Optional[SubscriptionStatus] = Field(None, description="订阅状态")


class SubscriptionResponse(BaseModel):
    """订阅响应"""
    id: int
    topic: str
    description: Optional[str]
    frequency: FrequencyType
    status: SubscriptionStatus
    last_pushed_at: Optional[datetime]
    next_push_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PushStatus(str, Enum):
    """推送状态"""
    NEW = "new"
    READ = "read"


class PushRecordCreate(BaseModel):
    """创建推送记录请求"""
    subscription_id: int = Field(..., description="订阅ID")
    hot_topic_data: dict = Field(..., description="热点数据")


class PushRecordResponse(BaseModel):
    """推送记录响应"""
    id: int
    subscription_id: int
    topic: str
    hot_topic_data: dict
    status: PushStatus
    pushed_at: datetime
    read_at: Optional[datetime]

    class Config:
        from_attributes = True