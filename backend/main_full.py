
"""
MediaPilot 完整后端API
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import uuid
import random
from io import BytesIO

print("="*60)
print("   MediaPilot Backend - Full Version")
print("="*60)
print()

app = FastAPI(
    title="MediaPilot API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api/v1", tags=["MediaPilot API"])

# 任务状态存储
tasks = {}


# ============ 模拟数据服务 ============

class MockDataService:
    """模拟数据服务"""

    def __init__(self):
        self.platforms = ["抖音", "小红书", "微博"]

    def search_trending(self, keyword, platforms, days):
        """搜索热点"""
        topics = [
            f"{keyword}行业新趋势",
            f"{keyword}爆款内容分析",
            f"{keyword}怎么做",
            f"{keyword}避坑指南",
            f"{keyword}入门教程"
        ]
        results = []
        for i, title in enumerate(topics):
            results.append({
                "title": title,
                "heat_index": random.randint(10000, 999999),
                "platform": random.choice(platforms or self.platforms),
                "trend": random.choice(["rising", "stable", "falling"]),
                "summary": f"这是关于{title}的摘要..."
            })
        return sorted(results, key=lambda x: x["heat_index"], reverse=True)

    def search_competitors(self, niche, platforms, min_followers, max_followers, min_avg_likes):
        """搜索对标账号"""
        nicknames = [
            f"{niche}小能手",
            f"{niche}达人",
            f"{niche}研习社",
            f"{niche}学姐",
            f"{niche}学长"
        ]
        accounts = []
        for i, nickname in enumerate(nicknames):
            followers = random.randint(min_followers or 10000, max_followers or 1000000)
            accounts.append({
                "account_id": f"account_{i:04d}",
                "nickname": nickname,
                "platform": random.choice(platforms or self.platforms),
                "followers": followers,
                "total_likes": random.randint(followers * 2, followers * 20),
                "video_count": random.randint(50, 500),
                "avg_likes": round(random.uniform(100, 5000), 1),
                "profile_url": f"https://example.com/profile/{i}"
            })
        return sorted(accounts, key=lambda x: x["followers"], reverse=True)

    def generate_script(self, topic):
        """生成分镜头脚本"""
        return {
            "script": [
                {"scene": 1, "duration": "0:00-0:05", "visual": "开头吸引眼球", "audio": "大家好！今天给大家分享一个超实用的技巧！", "notes": ""},
                {"scene": 2, "duration": "0:05-0:15", "visual": "展示主题", "audio": f"今天我们来聊一聊{topic}", "notes": ""},
                {"scene": 3, "duration": "0:15-0:30", "visual": "详细讲解", "audio": "具体怎么做呢？首先...", "notes": ""},
                {"scene": 4, "duration": "0:30-0:45", "visual": "总结升华", "audio": "以上就是今天的全部内容", "notes": ""},
                {"scene": 5, "duration": "0:45-0:60", "visual": "引导关注", "audio": "记得点赞关注，下期更精彩！", "notes": ""}
            ],
            "copywriting": {
                "title": f"{topic}爆款标题 - 90%的人都不知道！",
                "hooks": ["你还不知道的秘密！", "建议收藏！", "最后一条绝了"],
                "call_to_action": "点赞关注，下期更精彩！",
                "tags": [f"#{topic}", "#新媒体", "#干货"]
            }
        }


mock_data = MockDataService()


# ============ API路由 ============

@app.get("/")
async def root():
    return {
        "name": "MediaPilot API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.post("/trending/search")
async def search_trending_endpoint(data: dict):
    """搜索热点"""
    keyword = data.get("keyword", "美妆")
    platforms = data.get("platforms", ["抖音", "小红书", "微博"])
    days = data.get("days", 7)
    topics = mock_data.search_trending(keyword, platforms, days)
    return {
        "success": True,
        "data": {
            "keyword": keyword,
            "total_count": len(topics),
            "hot_topics": topics
        }
    }


@router.post("/competitors/search")
async def search_competitors_endpoint(data: dict):
    """搜索对标账号"""
    niche = data.get("niche", "护肤")
    platforms = data.get("platforms", ["抖音", "小红书"])
    min_followers = data.get("min_followers", 10000)
    max_followers = data.get("max_followers", 1000000)
    min_avg_likes = data.get("min_avg_likes", 100)
    accounts = mock_data.search_competitors(niche, platforms, min_followers, max_followers, min_avg_likes)
    return {
        "success": True,
        "data": {
            "niche": niche,
            "total_count": len(accounts),
            "accounts": accounts
        }
    }


@router.post("/content/generate")
async def generate_content_endpoint(data: dict):
    """生成分镜头脚本"""
    topic = data.get("topic", "如何做短视频")
    result = mock_data.generate_script(topic)
    return {
        "success": True,
        "data": {
            "topic": topic,
            "script": result["script"],
            "copywriting": result["copywriting"]
        }
    }


@router.post("/media/upload")
async def upload_media_endpoint(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """上传媒体文件"""
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "processing"}
    # 模拟处理
    tasks[task_id] = {
        "status": "completed",
        "transcript": "这是模拟的语音转文字结果...",
        "outline": [
            {"section": "1", "title": "开场", "summary": "打招呼介绍主题"},
            {"section": "2", "title": "主题内容", "summary": "核心内容讲解"},
            {"section": "3", "title": "总结", "summary": "总结和引导关注"}
        ]
    }
    return {"success": True, "data": {"task_id": task_id, "status": "completed"}}


app.include_router(router)

print("[OK] API routes registered!")
print()
print("Available endpoints:")
print("  GET  /                      - Root")
print("  GET  /health                - Health check")
print("  POST /api/v1/trending/search   - Search trending")
print("  POST /api/v1/competitors/search - Search competitors")
print("  POST /api/v1/content/generate  - Generate content script")
print("  POST /api/v1/media/upload      - Upload media")
print()
print("API docs:")
print("  http://localhost:8000/docs")
print()
print("="*60)
print("Starting server...")
print("="*60)
print()

if __name__ == "__main__":
    uvicorn.run(
        "main_full:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

