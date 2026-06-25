
"""
MediaPilot 模拟数据服务（用于演示）
实际使用时请集成新榜、灰豚等第三方API
"""
import random
from datetime import datetime, timedelta


class MockDataService:
    """模拟数据服务"""

    def __init__(self):
        self.platforms = {
            "baidu": "百度新闻",
            "weibo": "微博热搜",
            "zhihu": "知乎热榜",
            "douyin": "抖音热榜",
            "xiaohongshu": "小红书",
            "kuaishou": "快手",
            "bilibili": "B站"
        }

    def search_trending(self, keyword, platforms, days):
        """搜索热点话题（模拟）"""
        topics = [
            f"{keyword}行业新趋势",
            f"{keyword}爆款内容分析",
            f"{keyword}怎么做",
            f"{keyword}避坑指南",
            f"{keyword}入门教程",
            f"{keyword}运营技巧",
            f"{keyword}数据增长",
            f"{keyword}爆款标题",
            f"{keyword}流量密码",
            f"2026最新{keyword}玩法"
        ]

        # 平台搜索页 URL 模板：返回可访问的真实搜索链接，不再用 example.com 占位
        from urllib.parse import quote
        search_url_templates = {
            "baidu": "https://www.baidu.com/s?wd={q}&tn=news",
            "weibo": "https://s.weibo.com/weibo?q={q}",
            "zhihu": "https://www.zhihu.com/search?type=content&q={q}",
            "douyin": "https://www.douyin.com/search/{q}",
            "xiaohongshu": "https://www.xiaohongshu.com/search_result?keyword={q}",
            "bilibili": "https://search.bilibili.com/all?keyword={q}",
        }

        hot_topics = []
        for i, title in enumerate(topics):
            platform_key = random.choice(platforms)
            source_name = self.platforms.get(platform_key, platform_key)
            url_tpl = search_url_templates.get(platform_key, "https://www.google.com/search?q={q}")
            real_url = url_tpl.format(q=quote(title))
            hot_topics.append({
                "title": title,
                "heat_value": float(random.randint(10000, 999999)),
                "source": source_name,
                "trend_direction": random.choice(["up", "down", "same"]),
                "summary": f"这是关于{title}的热点摘要...",
                "source_url": real_url,
                "published_at": datetime.now() - timedelta(days=random.randint(0, days)),
                "crawled_at": datetime.now(),
                "category": "综合",
                "keywords": keyword,
                "image_url": "",
            })

        return sorted(hot_topics, key=lambda x: x["heat_value"], reverse=True)

    def search_competitors(self, niche, platforms,
                           min_followers, max_followers,
                           min_avg_likes):
        """搜索对标账号（模拟）"""
        nicknames = [
            f"{niche}小能手",
            f"{niche}达人",
            f"{niche}研习社",
            f"{niche}学姐",
            f"{niche}学长",
            f"{niche}研究院",
            f"{niche}日记",
            f"{niche}笔记"
        ]

        accounts = []
        for i, nickname in enumerate(nicknames):
            followers = random.randint(min_followers, max_followers)
            video_count = random.randint(50, 500)
            total_likes = random.randint(followers * 2, followers * 20)
            avg_likes = total_likes / video_count

            if avg_likes < min_avg_likes:
                continue

            accounts.append({
                "account_id": f"account_{i:04d}",
                "nickname": nickname,
                "platform": random.choice(platforms),
                "followers": followers,
                "total_likes": total_likes,
                "video_count": video_count,
                "avg_likes": round(avg_likes, 1),
                "avg_comments": round(avg_likes * 0.05, 1),
                "profile_url": f"https://example.com/profile/{i}",
                "avatar_url": f"https://example.com/avatar/{i}.jpg",
                "signature": f"专注{niche}领域，分享实用干货！"
            })

        return sorted(accounts, key=lambda x: x["followers"], reverse=True)

    def fetch_video(self, video_url, platform):
        """获取视频信息（模拟）"""
        # 从URL提取video_id
        if '/video/' in video_url:
            video_id = video_url.split('/video/')[-1].split('?')[0]
        else:
            video_id = video_url.split('/')[-1].split('?')[0]

        return {
            "url": video_url,
            "platform": platform,
            "video_id": video_id,
            "title": "爆款视频标题示例",
            "description": "这是一个关于爆款视频的描述...",
            "thumbnail_url": "https://example.com/thumb.jpg",
            "duration": random.randint(30, 120),
            "view_count": random.randint(100000, 10000000),
            "like_count": random.randint(10000, 1000000),
            "comment_count": random.randint(1000, 100000),
            "published_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
        }

    def get_video_transcript(self, video_id):
        """获取视频逐字稿（模拟）"""
        transcript_lines = [
            {"time": "00:00", "text": "大家好"},
            {"time": "00:03", "text": "今天给大家分享一个非常有用的技巧"},
            {"time": "00:08", "text": "首先，我们需要准备以下材料"},
            {"time": "00:12", "text": "第一步，我们先这样做"},
            {"time": "00:18", "text": "第二步，再那样做"},
            {"time": "00:25", "text": "大家学会了吗"},
            {"time": "00:28", "text": "记得点赞关注哦"}
        ]

        full_transcript = " ".join([line["text"] for line in transcript_lines])

        return {
            "video_id": video_id,
            "full_transcript": full_transcript,
            "lines": transcript_lines
        }

