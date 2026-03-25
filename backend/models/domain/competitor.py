"""
对标账号领域模型
"""
from typing import Optional


class CompetitorAccount:
    """对标账号实体"""

    def __init__(
        self,
        account_id: str,
        nickname: str,
        platform: str,
        followers: int,
        total_likes: int,
        video_count: int,
        avg_likes: float,
        avg_comments: float,
        profile_url: str,
        avatar_url: Optional[str] = None,
        signature: Optional[str] = None,
    ):
        self.account_id = account_id
        self.nickname = nickname
        self.platform = platform
        self.followers = followers
        self.total_likes = total_likes
        self.video_count = video_count
        self.avg_likes = avg_likes
        self.avg_comments = avg_comments
        self.profile_url = profile_url
        self.avatar_url = avatar_url
        self.signature = signature

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "account_id": self.account_id,
            "nickname": self.nickname,
            "platform": self.platform,
            "followers": self.followers,
            "total_likes": self.total_likes,
            "video_count": self.video_count,
            "avg_likes": self.avg_likes,
            "avg_comments": self.avg_comments,
            "profile_url": self.profile_url,
            "avatar_url": self.avatar_url,
            "signature": self.signature,
        }
