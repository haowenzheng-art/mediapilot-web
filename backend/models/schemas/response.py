"""
API 响应模型定义
从 shared/schemas.py 迁移
"""
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

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
    is_today: bool = Field(default=False, description="是否为今日热点（前端展示 today 徽章）")

    @model_validator(mode="after")
    def _compute_is_today(self):
        ts = self.published_at or self.crawled_at
        if ts is None:
            return self
        today = datetime.utcnow().date()
        try:
            self.is_today = ts.date() == today
        except Exception:
            pass
        return self

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
    """内容生成响应（v3：兼容 ContentService 实际返回）

    历史 schema 期望 title/content/outline，但 ContentService 实际返回
    topic/script/copywriting。保留旧字段作 Optional 兼容，加新字段满足 service。
    """
    # 旧字段（保留兼容）
    title: Optional[str] = Field(default=None, description="旧字段：标题")
    content: Optional[str] = Field(default=None, description="旧字段：内容")
    outline: Optional[List[OutlineItem]] = None
    # 新字段（ContentService 实际返回）
    topic: Optional[str] = Field(default=None, description="选题")
    script: Optional[List[Shot]] = Field(default=None, description="分镜头脚本")
    copywriting: Optional[Copywriting] = Field(default=None, description="文案内容")
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
    # v3 改造：UI 透明化字段
    degraded_platforms: List[str] = Field(
        default_factory=list,
        description="本次搜索降级的平台列表（前端用于黄条提示）"
    )
    sixty_failed_platforms: List[str] = Field(
        default_factory=list,
        description="60s-api 失败的具体平台（5 个 60s 端点）"
    )
    used_cache: bool = Field(default=False, description="是否全部命中缓存")
    cached_at: Optional[datetime] = Field(default=None, description="缓存命中时的缓存时间")
    freshness: str = Field(default="fresh", description="fresh | stale | degraded")


class VideoEditSegment(BaseModel):
    """视频剪辑片段（保留或删除）"""
    start: float = Field(..., description="开始时间（秒）")
    end: float = Field(..., description="结束时间（秒）")
    text: Optional[str] = Field(default=None, description="对应文字（删除片段不填）")
    reason: Optional[str] = Field(default=None, description="删除原因（仅删除片段填）")


class VideoEditResponse(BaseModel):
    """视频剪辑任务响应"""
    task_id: str
    status: str  # pending, processing, completed, failed
    source_video_name: Optional[str] = None
    transcript: Optional[str] = None
    kept_segments: Optional[List[VideoEditSegment]] = None
    removed_segments: Optional[List[VideoEditSegment]] = None
    output_video_path: Optional[str] = None
    preview_video_path: Optional[str] = None  # v3 新增：360p preview 路径
    preview_size_bytes: Optional[int] = None   # v3 新增：preview 文件大小
    subtitle_path: Optional[str] = None
    subtitle_format: Optional[str] = "srt"
    original_duration: Optional[float] = None
    final_duration: Optional[float] = None
    error: Optional[str] = None


class VideoEditSegmentsResponse(BaseModel):
    """视频剪辑片段响应"""
    kept_segments: List[VideoEditSegment]
    removed_segments: List[VideoEditSegment]
    total_kept: int
    total_removed: int