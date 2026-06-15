"""
MediaPilot Pydantic 模型
用于 API 请求/响应验证
"""
from .request import (
    TrendingSearchRequest,
    CompetitorSearchRequest,
    VideoFetchRequest,
    VideoRewriteRequest,
    ContentGenerateRequest,
)
from .response import (
    APIResponse,
    TranscriptLine,
    OutlineItem,
    Shot,
    Copywriting,
    HotTopicResponse,
    CompetitorAccountResponse,
    CompetitorSearchResponse,
    VideoInfo,
    VideoTranscriptResponse,
    MediaTranscribeResponse,
    ContentGenerateResponse,
    TrendingSearchResponse,
)

__all__ = [
    'TrendingSearchRequest',
    'CompetitorSearchRequest',
    'VideoFetchRequest',
    'VideoRewriteRequest',
    'ContentGenerateRequest',
    'APIResponse',
    'TrendingSearchResponse',
    'CompetitorSearchResponse',
    'VideoInfo',
    'VideoTranscriptResponse',
    'TranscriptLine',
    'MediaTranscribeResponse',
    'ContentGenerateResponse',
    'OutlineItem',
]
