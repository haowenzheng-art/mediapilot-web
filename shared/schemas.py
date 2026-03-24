
"""
MediaPilot 数据模型定义
使用Pydantic进行数据验证
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class AIProvider(str, Enum):
    """AI服务提供商"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    ARK = "ark"


class Platform(str, Enum):
    """社交平台"""
    DOUYIN = "douyin"
    XIAOHONGSHU = "xiaohongshu"
    WEIBO = "weibo"
    KUAISHOU = "kuaishou"
    BILIBILI = "bilibili"


class ContentStyle(str, Enum):
    """内容风格"""
    PROFESSIONAL = "professional"
    HUMOROUS = "humorous"
    CONCISE = "concise"
    EMOTIONAL = "emotional"
    STORYTELLING = "storytelling"


# ============ 请求模型 ============

class TrendingSearchRequest(BaseModel):
    """热点搜索请求"""
    keyword: str = Field(..., description="搜索关键词")
    platforms: List[Platform] = Field(default=[Platform.WEIBO, Platform.DOUYIN, Platform.XIAOHONGSHU])
    days: int = Field(default=7, ge=1, le=30, description="搜索天数")


class CompetitorSearchRequest(BaseModel):
    """对标账号搜索请求"""
    niche: str = Field(..., description="赛道/领域")
    platforms: List[Platform] = Field(default=[Platform.DOUYIN, Platform.XIAOHONGSHU])
    min_followers: Optional[int] = Field(default=10000, ge=0)
    max_followers: Optional[int] = Field(default=1000000, ge=0)
    min_avg_likes: Optional[int] = Field(default=100, ge=0)


class VideoFetchRequest(BaseModel):
    """视频获取请求"""
    video_url: str = Field(..., description="视频URL")
    platform: Platform = Field(..., description="平台")


class VideoRewriteRequest(BaseModel):
    """视频文案改写请求"""
    transcript: str = Field(..., description="原逐字稿")
    style: ContentStyle = Field(default=ContentStyle.PROFESSIONAL)
    target_duration: Optional[int] = Field(default=60, description="目标时长(秒)")


class ContentGenerateRequest(BaseModel):
    """内容生成请求"""
    topic: str = Field(..., description="选题")
    platform: Platform = Field(default=Platform.DOUYIN)
    duration: int = Field(default=60, ge=15, le=300, description="视频时长(秒)")
    style: ContentStyle = Field(default=ContentStyle.PROFESSIONAL)
    additional_notes: Optional[str] = Field(default=None, description="附加说明")


# ============ 响应模型 ============

class APIResponse(BaseModel):
    """统一API响应格式"""
    success: bool = True
    data: Optional[Any] = None
    message: str = "操作成功"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HotTopic(BaseModel):
    """热点话题"""
    title: str
    heat_index: int
    platform: str
    trend: str = "stable"  # rising, falling, stable
    summary: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[datetime] = None


class TrendingSearchResponse(BaseModel):
    """热点搜索响应"""
    keyword: str
    total_count: int
    hot_topics: List[HotTopic]


class CompetitorAccount(BaseModel):
    """对标账号"""
    account_id: str
    nickname: str
    platform: str
    followers: int
    total_likes: int
    video_count: int
    avg_likes: float
    avg_comments: float
    profile_url: str
    avatar_url: Optional[str] = None
    signature: Optional[str] = None


class CompetitorSearchResponse(BaseModel):
    """对标账号搜索响应"""
    niche: str
    total_count: int
    accounts: List[CompetitorAccount]


class VideoInfo(BaseModel):
    """视频信息"""
    video_id: str
    title: str
    platform: str
    author: str
    views: int
    likes: int
    comments: int
    shares: int
    duration: int
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None


class TranscriptLine(BaseModel):
    """逐字稿行"""
    time: str  # "00:00"
    text: str


class VideoTranscriptResponse(BaseModel):
    """视频逐字稿响应"""
    video_id: str
    full_transcript: str
    lines: List[TranscriptLine]


class OutlineItem(BaseModel):
    """大纲项"""
    section: str
    title: str
    summary: str


class MediaTranscribeResponse(BaseModel):
    """媒体转写响应"""
    task_id: str
    status: str  # pending, processing, completed, failed
    transcript: Optional[str] = None
    outline: Optional[List[OutlineItem]] = None
    timestamps: Optional[List[TranscriptLine]] = None


class Shot(BaseModel):
    """分镜头"""
    scene: int
    duration: str
    visual: str
    audio: str
    notes: Optional[str] = None


class Copywriting(BaseModel):
    """文案"""
    title: str
    hooks: List[str]
    call_to_action: str
    tags: List[str]


class ContentGenerateResponse(BaseModel):
    """内容生成响应"""
    topic: str
    script: List[Shot]
    copywriting: Copywriting

