"""
热点数据访问（占位）
"""
from typing import List
from sqlalchemy.orm import Session


class TrendingRepository:
    """热点数据访问"""

    def __init__(self, db: Session):
        self.db = db

    # TODO: 实现实际的数据库操作
    def save_trending(self, topic_data: dict):
        """保存热点数据"""
        pass

    def get_trending(self, keyword: str, days: int) -> List[dict]:
        """查询热点数据"""
        return []
