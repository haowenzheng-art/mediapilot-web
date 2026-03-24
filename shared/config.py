
"""
MediaPilot 共享配置模块
"""
import os


class Settings:
    """应用配置"""

    # API配置
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    API_TITLE = "MediaPilot API"
    API_VERSION = "1.0.0"

    # 数据库配置
    DATABASE_URL = "sqlite:///./mediapilot.db"

    # AI配置
    DEFAULT_AI_PROVIDER = "anthropic"

    # 文件配置
    UPLOAD_DIR = "./uploads"
    MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
    ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac"}
    ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}

    # 第三方API配置
    XINBANG_API_KEY = None
    HUITUN_API_KEY = None


# 全局配置实例
settings = Settings()


def get_upload_dir():
    """获取上传目录，不存在则创建"""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    return settings.UPLOAD_DIR


def is_audio_file(filename):
    """检查是否为允许的音频文件"""
    ext = os.path.splitext(filename.lower())[1]
    return ext in settings.ALLOWED_AUDIO_EXTENSIONS


def is_video_file(filename):
    """检查是否为允许的视频文件"""
    ext = os.path.splitext(filename.lower())[1]
    return ext in settings.ALLOWED_VIDEO_EXTENSIONS

