"""
MediaPilot Pydantic 模型
用于 API 请求/响应验证
"""
from .request import (
    TrendingSearchRequest,
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
    VideoInfo,
    VideoTranscriptResponse,
    MediaTranscribeResponse,
    ContentGenerateResponse,
    TrendingSearchResponse,
)

__all__ = [
    'TrendingSearchRequest',
    'VideoFetchRequest',
    'VideoRewriteRequest',
    'ContentGenerateRequest',
    'APIResponse',
    'TrendingSearchResponse',
    'VideoInfo',
    'VideoTranscriptResponse',
    'TranscriptLine',
    'MediaTranscribeResponse',
    'ContentGenerateResponse',
    'OutlineItem',
]
