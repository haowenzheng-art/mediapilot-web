"""
爬虫模块

v4 精简：weibo/zhihu/douyin/xiaohongshu 4 源已下线（不支持垂直赛道搜索）
"""
from .base import BaseScraper
from .baidu_news import BaiduNewsScraper
from .aggregator import HotTopicAggregator
from .content_reference_scraper import ContentReferenceScraper, content_reference_scraper

__all__ = [
    "BaseScraper",
    "BaiduNewsScraper",
    "HotTopicAggregator",
    "ContentReferenceScraper",
    "content_reference_scraper",
]