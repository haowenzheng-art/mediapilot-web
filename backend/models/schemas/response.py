"""
API 响应模型定义
从 shared/schemas.py 迁移
"""
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

class APIResponse(BaseModel):
    """统一API响应格式"""
    success: bool = True
    data: Optional[Any] = None
    message: str = "操作成功"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TranscriptLine(BaseModel):
    """逐字稿行"""
    time: str  # "00:00"
    text:   str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class OutlineItem(BaseModel):
    """大纲项"""
    section: str
    title: str
    summary: str

class Shot(BaseModel):
    """分镜头"""
    scene: str = Field(..., description="场景描述")
    visual: str = Field(..., description="视觉画面")
    audio: str = Field(..., description="音频/台词")
    duration: Optional[float] = Field(default=None, description="时长(秒)")

class Copywriting(BaseModel):
    """文案内容"""
    platform: str = Field(..., description="平台")
    topic: str = Field(..., description="选题")
    script: str = Field(..., description="脚本内容")
    hooks: List[str] = Field(default_factory=list, description="开头钩子")
    cta: Optional[str] = Field(default=None, description="行动号召")

class HotTopicResponse(BaseModel):
    """热点话题响应"""
    id: Optional[str] = Field(default=None, description="稳定 ID（hash 自 source+title）")
    title: str
    heat_value: float = Field(description="热度值")
    source: str = Field(description="来源平台")
    trend_direction: str = Field(default="same", description="趋势方向: up/down/same")
    summary: Optional[str] = Field(default=None, description="摘要")
    source_url: Optional[str] = Field(default=None, alias="url", description="原文链接")
    published_at: Optional[datetime] = Field(default=None, description="发布时间")
    category: Optional[str] = Field(default=None, description="分类")
    crawled_at: Optional[datetime] = Field(default=None, description="爬取时间")
    keywords: Optional[str] = Field(default=None, description="关键词")
    image_url: Optional[str] = Field(default=None, description="配图URL")

    class Config:
        populate_by_name = True  # 允许使用 url 作为 source_url 的别名

class CompetitorAccountResponse(BaseModel):
    """对标账号响应"""
    account_id: str
    nickname: str
    platform: str
    followers: int
    total_likes: int
    video_count: int
    avg_likes: float
    avg_comments: float = 0.0
    profile_url: Optional[str] = None
    avatar_url: Optional[str] = None
    signature: Optional[str] = None

class VideoInfo(BaseModel):
    """视频信息"""
    url: str
    platform: str
    video_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    published_at: Optional[datetime] = None

class VideoTranscriptResponse(BaseModel):
    """视频转写响应"""
    video_id: str
    full_transcript: str
    lines: List[TranscriptLine]

class MediaTranscribeResponse(BaseModel):
    """媒体转写响应"""
    task_id: str
    status: str  # pending, processing, completed, failed
    transcript: Optional[str] = None
    outline: Optional[List[OutlineItem]] = None
    timestamps: Optional[List[TranscriptLine]] = None
    error: Optional[str] = None

class ContentGenerateResponse(BaseModel):
    """内容生成响应"""
    title: str
    content: str
    outline: Optional[List[OutlineItem]] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class CompetitorSearchResponse(BaseModel):
    """对标账号响应"""
    niche: str
    total_count: int
    competitors: List[Any]
    is_demo: bool = False


class TrendingSearchResponse(BaseModel):
    """热点搜索响应"""
    keyword: str
    total_count: int
    hot_topics: List[HotTopicResponse]