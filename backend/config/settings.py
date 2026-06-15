"""
MediaPilot 应用配置
从 shared/config.py 迁移
"""
import os


class Settings:
    """应用配置"""

    # API配置
    API_HOST = "127.0.0.1"
    API_PORT = 8000
    API_TITLE = "MediaPilot API"
    API_VERSION = "1.0.0"

    # 数据库配置
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///./mediapilot.db"
    )

    # AI配置
    AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_BASE_URL = os.getenv("AI_BASE_URL", "https://apihub.agnes-ai.com/v1")
    AI_MODEL = os.getenv("AI_MODEL", "agnes-2.0-flash")
    AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "60"))
    AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "3"))

    # 文件配置
    UPLOAD_DIR = "./uploads"
    MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
    ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac"}
    ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}

    # 第三方API配置
    XINBANG_API_KEY = os.getenv("XINBANG_API_KEY")
    HUITUN_API_KEY = os.getenv("HUITUN_API_KEY")

    # 音视频转写配置
    # 转写引擎: whisper_local, aliyun, volcengine, mock
    TRANSCRIBE_ENGINE = os.getenv("TRANSCRIBE_ENGINE", "whisper_local")

    # Whisper配置（本地）
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # base, small, medium, large
    WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "zh")  # 转写语言

    # 阿里云语音识别配置
    ALIYUN_ACCESS_KEY_ID = os.getenv("ALIYUN_ACCESS_KEY_ID", "")
    ALIYUN_ACCESS_KEY_SECRET = os.getenv("ALIYUN_ACCESS_KEY_SECRET", "")
    ALIYUN_APP_KEY = os.getenv("ALIYUN_APP_KEY", "")

    # 火山引擎语音转写配置
    VOLCENGINE_ACCESS_KEY = os.getenv("VOLCENGINE_ACCESS_KEY", "")
    VOLCENGINE_SECRET_ACCESS_KEY = os.getenv("VOLCENGINE_SECRET_ACCESS_KEY", "")
    VOLCENGINE_APP_ID = os.getenv("VOLCENGINE_APP_ID", "")

    # 是否使用Mock转写（用于测试）
    USE_MOCK_TRANSCRIBE = os.getenv("USE_MOCK_TRANSCRIBE", "false").lower() == "true"


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
