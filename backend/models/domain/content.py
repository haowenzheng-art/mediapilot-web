"""
内容生成领域模型
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class Shot:
    """分镜头"""

    def __init__(
        self,
        scene: int,
        duration: str,
        visual: str,
        audio: str,
        notes: Optional[str] = None,
    ):
        self.scene = scene
        self.duration = duration
        self.visual = visual
        self.audio = audio
        self.notes = notes

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "scene": self.scene,
            "duration": self.duration,
            "visual": self.visual,
            "audio": self.audio,
            "notes": self.notes,
        }


class Copywriting:
    """文案"""

    def __init__(
        self,
        title: str,
        hooks: List[str],
        call_to_action: str,
        tags: List[str],
    ):
        self.title = title
        self.hooks = hooks
        self.call_to_action = call_to_action
        self.tags = tags

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "title": self.title,
            "hooks": self.hooks,
            "call_to_action": self.call_to_action,
            "tags": self.tags,
        }


class ContentType(str, Enum):
    """内容类型"""
    COPYWRITING = "copywriting"
    SHOOT_SCRIPT = "shoot_script"


class ContentMode(str, Enum):
    """内容生成模式"""
    FROM_SCRATCH = "from_scratch"  # 从0到1
    HOT_TOPIC = "hot_topic"  # 热点框架
    REWRITE = "rewrite"  # 改写


class ContentCreate(BaseModel):
    """创建内容请求"""
    content_type: ContentType = Field(..., description="内容类型")
    content_id: str = Field(..., min_length=1, max_length=100, description="内容ID")
    hot_topic_id: Optional[str] = Field(None, max_length=100, description="关联的热点ID")
    hot_topic_title: Optional[str] = Field(None, max_length=500, description="热点标题")
    hot_topic_source: Optional[str] = Field(None, max_length=50, description="热点来源")
    title: str = Field(..., min_length=1, max_length=500, description="内容标题")
    summary: Optional[str] = Field(None, description="内容摘要")
    mode: Optional[ContentMode] = Field(None, description="生成模式")
    persona: Optional[str] = Field(None, max_length=500, description="人设")
    platform: Optional[str] = Field(None, max_length=20, description="平台")
    style: Optional[str] = Field(None, max_length=20, description="风格")


class ContentUpdate(BaseModel):
    """更新内容请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="内容标题")
    summary: Optional[str] = Field(None, description="内容摘要")
    mode: Optional[ContentMode] = Field(None, description="生成模式")
    persona: Optional[str] = Field(None, max_length=500, description="人设")
    platform: Optional[str] = Field(None, max_length=20, description="平台")
    style: Optional[str] = Field(None, max_length=20, description="风格")
    is_processed: Optional[bool] = Field(None, description="是否已处理")


class ContentResponse(BaseModel):
    """内容响应"""
    id: int
    content_type: ContentType
    content_id: str
    hot_topic_id: Optional[str]
    hot_topic_title: Optional[str]
    hot_topic_source: Optional[str]
    user_id: int
    title: str
    summary: Optional[str]
    mode: Optional[ContentMode]
    persona: Optional[str]
    platform: Optional[str]
    style: Optional[str]
    is_processed: bool
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TopicHistoryRequest(BaseModel):
    """话题历史请求"""
    hot_topic_id: str = Field(..., min_length=1, max_length=100, description="热点ID")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")


class TrendDirection(str, Enum):
    """趋势方向"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class TrendDataPoint(BaseModel):
    """趋势数据点"""
    hot_topic_id: str
    hot_topic_title: Optional[str]
    hot_topic_source: Optional[str]
    heat_score: Optional[int]
    trend_direction: TrendDirection
    recorded_at: datetime

    class Config:
        from_attributes = True


class TopicHistoryResponse(BaseModel):
    """话题历史响应"""
    hot_topic_id: str
    hot_topic_title: Optional[str]
    hot_topic_source: Optional[str]
    trend_data: List[TrendDataPoint]
