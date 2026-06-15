"""
爬虫模块
"""
from .base import BaseScraper
from .baidu_news import BaiduNewsScraper
from .weibo import WeiboScraper
from .zhihu import ZhihuScraper
from .douyin import DouyinScraper
from .xiaohongshu import XiaohongshuScraper
from .aggregator import HotTopicAggregator
from .content_reference_scraper import ContentReferenceScraper, content_reference_scraper

__all__ = [
    "BaseScraper",
    "BaiduNewsScraper",
    "WeiboScraper",
    "ZhihuScraper",
    "DouyinScraper",
    "XiaohongshuScraper",
    "HotTopicAggregator",
    "ContentReferenceScraper",
    "content_reference_scraper",
]