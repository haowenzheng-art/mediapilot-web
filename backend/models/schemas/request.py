"""
API 请求模型定义
从 shared/schemas.py 迁移
"""
from typing import List, Optional
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


class TrendingSearchRequest(BaseModel):
    """热点搜索请求"""
    keyword: str = Field(..., description="搜索关键词")
    platforms: List[Platform] = Field(
        default=[Platform.WEIBO, Platform.DOUYIN, Platform.XIAOHONGSHU]
    )
    days: int = Field(default=7, ge=1, le=30, description="搜索天数")


class CompetitorSearchRequest(BaseModel):
    """对标账号搜索请求"""
    niche: str = Field(..., description="赛道/领域")
    platforms: List[Platform] = Field(
        default=[Platform.DOUYIN, Platform.XIAOHONGSHU]
    )
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
