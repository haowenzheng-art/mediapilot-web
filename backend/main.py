"""
MediaPilot 后端API服务入口
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 导导配置（向后兼容：优先使用新路径，如果不存在则使用旧路径）
try:
    from backend.config.settings import settings
except ImportError:
    from shared.config import settings

# 导导路由注册函数
from backend.api import register_routes

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
register_routes(app)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "MediaPilot API",
        "version": settings.API_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
