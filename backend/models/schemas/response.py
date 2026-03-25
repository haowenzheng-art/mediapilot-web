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
    text: str


class OutlineItem(BaseModel):
    """大纲项"""
    section: str
    title: str
    summary: str


class HotTopicResponse(BaseModel):
    """热点话题响应"""
    title: str
    heat_index: int
    platform: str
    trend: str = "stable"
    summary: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[datetime] = None


class TrendingSearchResponse(BaseModel):
    """热点搜索响应"""
    keyword: str
    total_count: int
    hot_topics: List[HotTopicResponse]


class CompetitorAccountResponse(BaseModel):
    """对标账号响应"""
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
    accounts: List[CompetitorAccountResponse]


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


class VideoTranscriptResponse(BaseModel):
    """视频逐字稿响应"""
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
