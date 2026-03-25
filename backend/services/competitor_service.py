"""
对标账号业务逻辑
"""
from fastapi.responses import StreamingResponse
from typing import Iterator

from models.schemas.response import (
    CompetitorAccountResponse,
    CompetitorSearchResponse,
)
from models.schemas.response import APIResponse
from services.mock_data import MockDataService
from backend.core.excel_exporter import ExcelExporter


class CompetitorService:
    """对标账号服务"""

    def __init__(self):
        self.mock_data = MockDataService()
        self.excel_exporter = ExcelExporter()

    async def search(
        self,
        niche: str,
        platforms: list,
        min_followers: int = 10000,
        max_followers: int = 1000000,
        min_avg_likes: int = 100
    ) -> CompetitorSearchResponse:
        """
        搜索对标账号

        Args:
            niche: 赛道
            platforms: 平台列表
            min_followers: 最小粉丝数
            max_followers: 最大粉丝数
            min_avg_likes: 最小平均点赞

        Returns:
            对标账号搜索响应
        """
        accounts = self.mock_data.search_competitors(
            niche=niche,
            platforms=platforms,
            min_followers=min_followers,
            max_followers=max_followers,
            min_avg_likes=min_avg_likes
        )

        competitor_accounts = [CompetitorAccountResponse(**a) for a in accounts]

        return CompetitorSearchResponse(
            niche=niche,
            total_count=len(competitor_accounts),
            accounts=competitor_accounts
        )

    async def export_excel(self, niche: str) -> Iterator[bytes]:
        """
        导出对标账号 Excel

        Args:
            niche: 赛道

        Returns:
            Excel 文件字节流
        """
        accounts = self.mock_data.search_competitors(
            niche=niche,
            platforms=["douyin", "xiaohongshu"],
            min_followers=10000,
            max_followers=1000000,
            min_avg_likes=100
        )

        return self.excel_exporter.export_competitors(accounts)
