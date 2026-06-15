"""
内容库相关的领域模型
定义请求和响应的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ContentType(str, Enum):
    """内容类型"""
    COPYWRITING = "copywriting"
    SHOOT_SCRIPT = "shoot_script"


class ContentCreate(BaseModel):
    """创建内容记录请求"""
    content_type: ContentType = Field(..., description="内容类型")
    content_id: str = Field(..., max_length=100, description="内容ID")
    title: str = Field(..., max_length=500, description="内容标题")
    summary: Optional[str] = Field(None, description="内容摘要")
    hot_topic_id: Optional[str] = Field(None, max_length=100, description="关联热点ID")
    hot_topic_title: Optional[str] = Field(None, max_length=500, description="热点标题")
    hot_topic_source: Optional[str] = Field(None, max_length=50, description="热点来源")
    mode: Optional[str] = Field(None, max_length=20, description="生成模式")
    persona: Optional[str] = Field(None, max_length=500, description="人设")
    platform: Optional[str] = Field(None, max_length=20, description="平台")
    style: Optional[str] = Field(None, max_length=20, description="风格")


class ContentUpdate(BaseModel):
    """更新内容记录请求"""
    title: Optional[str] = Field(None, max_length=500, description="内容标题")
    summary: Optional[str] = Field(None, description="内容摘要")
    persona: Optional[str] = Field(None, max_length=500, description="人设")
    platform: Optional[str] = Field(None, max_length=20, description="平台")
    style: Optional[str] = Field(None, max_length=20, description="风格")


class ContentResponse(BaseModel):
    """内容记录响应"""
    id: int
    content_type: ContentType
    content_id: str
    hot_topic_id: Optional[str]
    hot_topic_title: Optional[str]
    hot_topic_source: Optional[str]
    user_id: int
    title: str
    summary: Optional[str]
    mode: Optional[str]
    persona: Optional[str]
    platform: Optional[str]
    style: Optional[str]
    is_processed: bool
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TopicHistoryRequest(BaseModel):
    """话题历史趋势请求"""
    hot_topic_id: str = Field(..., max_length=100, description="热点ID")
    limit: int = Field(default=100, ge=1, le=500, description="返回数量限制")


class TrendRecordResponse(BaseModel):
    """趋势记录响应"""
    id: int
    hot_topic_id: str
    hot_topic_title: Optional[str]
    hot_topic_source: Optional[str]
    heat_score: Optional[int]
    trend_direction: Optional[str]
    recorded_at: datetime

    class Config:
        from_attributes = True


class TopicHistoryResponse(BaseModel):
    """话题历史趋势响应"""
    hot_topic_id: str
    hot_topic_title: Optional[str]
    trends: List[TrendRecordResponse]


class TrendDirection(str, Enum):
    """趋势方向"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"