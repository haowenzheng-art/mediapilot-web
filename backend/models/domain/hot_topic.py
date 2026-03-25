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
        heat_index: int,
        platform: str,
        trend: str = "stable",
        summary: Optional[str] = None,
        url: Optional[str] = None,
        published_at: Optional[datetime] = None,
    ):
        self.title = title
        self.heat_index = heat_index
        self.platform = platform
        self.trend = trend  # rising, falling, stable
        self.summary = summary
        self.url = url
        self.published_at = published_at

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "title": self.title,
            "heat_index": self.heat_index,
            "platform": self.platform,
            "trend": self.trend,
            "summary": self.summary,
            "url": self.url,
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }
