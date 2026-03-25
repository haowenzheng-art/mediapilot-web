"""
对标账号数据访问（占位）
"""
from typing import List
from sqlalchemy.orm import Session


class CompetitorRepository:
    """对标账号数据访问"""

    def __init__(self, db: Session):
        self.db = db

    # TODO: 实现实际的数据库操作
    def save_competitor(self, account_data: dict):
        """保存对标账号数据"""
        pass

    def get_competitors(self, niche: str) -> List[dict]:
        """查询对标账号数据"""
        return []
