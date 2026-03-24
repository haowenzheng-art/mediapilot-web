
"""
MediaPilot 简化版后端 - 可以直接运行
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import random

print("="*60)
print("   MediaPilot Backend")
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


@app.get("/api/v1/test")
async def test_api():
    """测试API"""
    return {
        "message": "API is working!",
        "timestamp": "now",
        "data": [1, 2, 3, 4, 5]
    }


@app.get("/api/v1/trending/mock")
async def get_mock_trending(keyword: str = "美妆"):
    """获取模拟热点"""
    topics = [
        f"{keyword}行业新趋势",
        f"{keyword}爆款内容分析",
        f"{keyword}怎么做",
        f"{keyword}避坑指南",
        f"{keyword}入门教程"
    ]
    results = []
    platforms = ["抖音", "小红书", "微博"]
    for i, title in enumerate(topics):
        results.append({
            "id": i + 1,
            "title": title,
            "heat_index": random.randint(10000, 999999),
            "platform": random.choice(platforms),
            "trend": random.choice(["上升", "平稳", "下降"])
        })
    return {"keyword": keyword, "data": sorted(results, key=lambda x: x["heat_index"], reverse=True)}


@app.get("/api/v1/competitors/mock")
async def get_mock_competitors(niche: str = "护肤"):
    """获取模拟对标账号"""
    nicknames = [
        f"{niche}小能手",
        f"{niche}达人",
        f"{niche}研习社",
        f"{niche}学姐",
        f"{niche}学长"
    ]
    platforms = ["抖音", "小红书", "微博"]
    accounts = []
    for i, nickname in enumerate(nicknames):
        followers = random.randint(10000, 1000000)
        accounts.append({
            "account_id": f"account_{i:04d}",
            "nickname": nickname,
            "platform": random.choice(platforms),
            "followers": followers,
            "total_likes": random.randint(followers * 2, followers * 20),
            "video_count": random.randint(50, 500),
            "avg_likes": round(random.uniform(100, 5000), 1)
        })
    return {"niche": niche, "data": sorted(accounts, key=lambda x: x["followers"], reverse=True)}


print("[OK] FastAPI app created!")
print()
print("API endpoints:")
print("  GET /              - Root")
print("  GET /health        - Health check")
print("  GET /api/v1/test   - Test API")
print("  GET /api/v1/trending/mock?keyword=xxx    - Mock trending")
print("  GET /api/v1/competitors/mock?niche=xxx  - Mock competitors")
print()
print("="*60)
print("Starting server...")
print("="*60)
print()

if __name__ == "__main__":
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

