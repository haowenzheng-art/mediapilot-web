"""
内容数据访问（占位）
"""
from typing import List
from sqlalchemy.orm import Session


class ContentRepository:
    """生成内容数据访问"""

    def __init__(self, db: Session):
        self.db = db

    # TODO: 实现实际的数据库操作
    def save_content(self, content_data: dict):
        """保存生成内容"""
        pass

    def get_content_history(self, limit: int = 50) -> List[dict]:
        """查询历史记录"""
        return []
