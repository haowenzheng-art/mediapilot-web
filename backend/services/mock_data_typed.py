"""
Mock 数据服务
使用 Python 类型提示，遵循 PEP 8 标准
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class MockDataService:
    """
    Mock 数据服务（用于 API 失败时的降级）

    提供模拟的平台数据和热点话题
    """

    @staticmethod
    def search_trending(
        keyword: str,
        platforms: List[str],
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        生成模拟热点数据

        Args:
            keyword: 搜索关键词
            platforms: 平台列表
            days: 搜索天数

        Returns:
            List[Dict]: 模拟话题列表
        """
        logger.info(f"生成模拟热点数据: keyword={keyword}, platforms={platforms}, days={days}")

        mock_topics: List[Dict[str, Any]] = []

        for platform in platforms:
            for i in range(min(5, days)):  # 生成模拟数据
                mock_topic = {
                    "title": f"{keyword} 相关话题 {i+1}",
                    "heat_index": (days * 10) + i,
                    "platform": platform,
                    "trend": "stable",
                    "summary": f"这是关于 {keyword} 的模拟热点话题",
                    "url": f"https://example.com/{platform}/topic/{i+1}",
                    "published_at": None
                }
                mock_topics.append(mock_topic)

        return mock_topics

    @staticmethod
    def fetch_video(video_url: str, platform: str) -> Dict[str, Any]:
        """
        获取模拟视频信息

        Args:
            video_url: 视频 URL
            platform: 平台名称

        Returns:
            Dict: 视频信息
        """
        logger.info(f"生成模拟视频信息: video_url={video_url}, platform={platform}")

        return {
            "video_id": "mock_video_123",
            "title": "模拟视频标题",
            "platform": platform,
            "author": "模拟作者",
            "views": 12500,
            "likes": 890,
            "comments": 256,
            "shares": 102,
            "duration": 60,
            "thumbnail_url": f"https://example.com/thumb.jpg",
            "video_url": video_url
        }

    @staticmethod
    def get_video_transcript(video_id: str) -> Dict[str, Any]:
        """
        获取模拟视频逐字稿

        Args:
            video_id: 视频 ID

        Returns:
            Dict: 逐字稿数据
        """
        logger.info(f"生成模拟视频逐字稿: video_id={video_id}")

        return {
            "video_id": video_id,
            "full_transcript": "这是模拟的视频逐字稿内容，包含了完整的对话或旁白...",
            "lines": [
                {"time": "00:00", "text": "大家好，今天我们来讲一个有趣的话题"},
                {"time": "00:05", "text": "首先，让我们看看发生了什么"},
                {"time": "00:10", "text": "这个话题确实很吸引人"},
                {"time": "00:15", "text": "接下来，我们来深入分析一下"},
                {"time": "00:20", "text": "总的来说，这是一个值得关注的趋势"},
                {"time": "00:25", "text": "如果你喜欢这个内容，记得点赞关注"}
                {"time": "00:30", "text": "好了，今天的分享就到这里"},
                {"time": "00:35", "text": "感谢大家的观看，我们下次见"}
            ]
        }
