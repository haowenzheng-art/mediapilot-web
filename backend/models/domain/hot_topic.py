"""
热点话题领域模型
"""
from datetime import datetime
from typing import Optional


class HotTopic:
    """热点话题实体"""

    def __init__(
        self,
        title: str,
        heat_value: float,
        source: str,
        trend_direction: str = "same",
        summary: Optional[str] = None,
        source_url: Optional[str] = None,
        published_at: Optional[datetime] = None,
        crawled_at: Optional[datetime] = None,
        category: Optional[str] = None,
        keywords: Optional[str] = None,
        image_url: Optional[str] = None,
    ):
        self.title = title
        self.heat_value = heat_value
        self.source = source
        self.trend_direction = trend_direction
        self.summary = summary
        self.source_url = source_url
        self.published_at = published_at
        self.crawled_at = crawled_at
        self.category = category
        self.keywords = keywords
        self.image_url = image_url

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "heat_value": self.heat_value,
            "source": self.source,
            "trend_direction": self.trend_direction,
            "summary": self.summary,
            "source_url": self.source_url,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "crawled_at": self.crawled_at.isoformat() if self.crawled_at else None,
            "category": self.category,
            "keywords": self.keywords,
            "image_url": self.image_url,
        }