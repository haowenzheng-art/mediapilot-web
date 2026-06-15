"""
网页爬虫基础模块
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import random
from fake_useragent import UserAgent
import httpx

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """爬虫基础类"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.ua = UserAgent()
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self._get_headers()
        )

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive"
        }

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    @abstractmethod
    async def search(
        self,
        keyword: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        搜索热点话题

        Args:
            keyword: 搜索关键词
            days: 搜索天数

        Returns:
            热点话题列表
        """
        pass

    def _normalize_topic(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化热点话题数据格式

        Returns:
            {
                "title": str,              # 标题
                "summary": str,            # 摘要
                "source": str,             # 来源（百度热搜、微博热搜等）
                "source_url": str,         # 原文链接
                "category": str,           # 分类
                "heat_value": float,       # 热度值
                "trend_direction": str,    # 趋势：up/down/same
                "published_at": datetime,  # 发布时间
                "crawled_at": datetime,    # 爬取时间
                "keywords": str,           # 相关关键词
                "image_url": str,          # 配图URL
            }
        """
        # 确保必需字段存在
        if "title" not in topic:
            raise ValueError("缺少必需字段: title")

        # 设置默认值
        now = datetime.now()
        return {
            "title": topic.get("title", ""),
            "summary": topic.get("summary", topic.get("description", "")),
            "source": topic.get("source", self.__class__.__name__.replace("Scraper", "")),
            "source_url": topic.get("source_url", topic.get("url", "")),
            "category": topic.get("category", ""),
            "heat_value": float(topic.get("heat_value", topic.get("heat_index", 0))),
            "trend_direction": topic.get("trend_direction", topic.get("trend", "same")),
            "published_at": topic.get("published_at", now),
            "crawled_at": now,
            "keywords": topic.get("keywords", ""),
            "image_url": topic.get("image_url", topic.get("thumbnail", "")),
        }

    def _extract_heat_value(self, text: str) -> Optional[float]:
        """从文本中提取热度值"""
        import re
        # 匹配数字（可能包含万、w、k等单位）
        match = re.search(r'(\d+(?:\.\d+)?)\s*([万wkWK]?)', text)
        if match:
            value = float(match.group(1))
            unit = match.group(2).lower()
            if unit in ["万", "w"]:
                value *= 10000
            elif unit in ["k"]:
                value *= 1000
            return value
        return None

    def _random_delay(self, min_sec: float = 0.5, max_sec: float = 2.0):
        """随机延迟，避免被封"""
        return random.uniform(min_sec, max_sec)