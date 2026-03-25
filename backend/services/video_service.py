"""
视频分析业务逻辑
"""
from models.schemas.response import (
    VideoInfo,
    VideoTranscriptResponse,
    TranscriptLine,
)
from services.mock_data import MockDataService


class VideoService:
    """视频分析服务"""

    def __init__(self):
        self.mock_data = MockDataService()

    async def fetch_video(self, video_url: str, platform: str) -> VideoInfo:
        """
        获取视频信息

        Args:
            video_url: 视频 URL
            platform: 平台

        Returns:
            视频信息
        """
        video = self.mock_data.fetch_video(video_url, platform)
        return VideoInfo(**video)

    async def get_transcript(self, video_id: str) -> VideoTranscriptResponse:
        """
        获取视频逐字稿

        Args:
            video_id: 视频 ID

        Returns:
            视频逐字稿响应
        """
        transcript = self.mock_data.get_video_transcript(video_id)
        lines = [TranscriptLine(**l) for l in transcript["lines"]]
        return VideoTranscriptResponse(
            video_id=video_id,
            full_transcript=transcript["full_transcript"],
            lines=lines
        )
