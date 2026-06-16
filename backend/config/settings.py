"""
MediaPilot 应用配置
单一配置来源，所有模块通过 Settings 获取
"""
import os
from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局应用配置，从环境变量 / .env 文件读取"""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==================== 服务配置 ====================
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    API_TITLE: str = "MediaPilot API"
    API_VERSION: str = "1.0.0"

    # ==================== 开发模式 ====================
    # True 时启用 dev user 绕过认证、放宽限流、CORS 开放
    DEV_MODE: bool = False

    # ==================== 数据库 ====================
    DATABASE_URL: str = "sqlite:///./mediapilot.db"

    # ==================== 认证 ====================
    JWT_SECRET: str = "dev-secret-key-change-in-production"
    DEFAULT_QUOTA: int = 100

    # ==================== CORS ====================
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ==================== AI ====================
    AI_PROVIDER: str = "openai"
    AI_API_KEY: str = ""
    AI_BASE_URL: str = "https://apihub.agnes-ai.com/v1"
    AI_MODEL: str = "agnes-2.0-flash"
    AI_TIMEOUT: int = 60
    AI_MAX_RETRIES: int = 3

    # ==================== 平台数据 API ====================
    XINBANG_API_KEY: str = ""
    HUITUN_API_KEY: str = ""

    # ==================== 音视频转写 ====================
    TRANSCRIBE_ENGINE: str = "whisper_local"
    USE_MOCK_TRANSCRIBE: bool = False
    WHISPER_MODEL: str = "base"
    WHISPER_LANGUAGE: str = "zh"

    ALIYUN_ACCESS_KEY_ID: str = ""
    ALIYUN_ACCESS_KEY_SECRET: str = ""
    ALIYUN_APP_KEY: str = ""

    VOLCENGINE_ACCESS_KEY: str = ""
    VOLCENGINE_SECRET_ACCESS_KEY: str = ""
    VOLCENGINE_APP_ID: str = ""

    # ==================== 文件上传 ====================
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100 MB
    ALLOWED_AUDIO_EXTENSIONS: str = ".mp3,.wav,.m4a,.aac"
    ALLOWED_VIDEO_EXTENSIONS: str = ".mp4,.mov,.avi,.mkv"

    # ==================== 日志 ====================
    LOG_LEVEL: str = "INFO"

    # ==================== 速率限制 ====================
    RATE_LIMIT_ENABLED: bool = True

    # ==================== 任务队列 ====================
    REDIS_URL: str = "redis://localhost:6379/0"

    # ==================== 辅助方法 ====================

    @property
    def upload_dir(self) -> str:
        """获取上传目录，不存在则创建"""
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        return self.UPLOAD_DIR

    @property
    def cors_origins_list(self) -> list[str]:
        """将逗号分隔的 CORS_ORIGINS 转为列表"""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    def allowed_audio_extensions(self) -> list[str]:
        """解析 ALLOWED_AUDIO_EXTENSIONS 为列表"""
        return [e.strip() for e in self.ALLOWED_AUDIO_EXTENSIONS.split(",") if e.strip()]

    def allowed_video_extensions(self) -> list[str]:
        """解析 ALLOWED_VIDEO_EXTENSIONS 为列表"""
        return [e.strip() for e in self.ALLOWED_VIDEO_EXTENSIONS.split(",") if e.strip()]

    def is_audio_file(self, filename: str) -> bool:
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.allowed_audio_extensions()

    def is_video_file(self, filename: str) -> bool:
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.allowed_video_extensions()

    @classmethod
    def get_dev_user(cls, db):
        """
        获取开发用默认用户。
        仅在 DEV_MODE=True 时返回用户，否则返回 None。
        路由层应通过 ensure_dev_user(db) 获取，后者在 DEV_MODE=False 时抛 401。
        """
        if not settings.DEV_MODE:
            return None
        from backend.models.database.tables import UserTable
        user = db.query(UserTable).filter(UserTable.username == "dev").first()
        if not user:
            user = UserTable(
                username="dev",
                email="dev@mediapilot.local",
                password_hash="dev",
                quota_balance=9999,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user


# 全局单例
settings = Settings()


def ensure_dev_user(db):
    """
    确保当前处于开发模式。
    DEV_MODE=False 时抛出 HTTPException(401)，强制走 JWT 认证流程。
    """
    from fastapi import HTTPException, status
    user = settings.get_dev_user(db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="开发模式未开启，请使用 JWT 认证",
        )
    return user


# ==================== 模块级便捷函数（供 media.py 等旧代码向后兼容） ====================

def get_upload_dir() -> str:
    return settings.upload_dir


def is_audio_file(filename: str) -> bool:
    return settings.is_audio_file(filename)


def is_video_file(filename: str) -> bool:
    return settings.is_video_file(filename)
