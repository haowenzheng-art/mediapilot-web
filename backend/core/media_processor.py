
"""
MediaPilot 音视频处理模块
"""
import asyncio
import os
import uuid
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from .transcribe_engine import TranscribeEngineManager

logger = logging.getLogger(__name__)


class MediaProcessor:
    """媒体处理器"""

    def __init__(
        self,
        upload_dir: str,
        transcribe_engine: Optional[TranscribeEngineManager] = None
    ):
        self.upload_dir = upload_dir
        self.transcribe_engine = transcribe_engine
        os.makedirs(upload_dir, exist_ok=True)

    def save_uploaded_file(self, file_bytes: bytes, filename: str) -> str:
        """保存上传的文件，返回文件路径"""
        ext = os.path.splitext(filename)[1]
        file_id = str(uuid.uuid4())
        save_path = os.path.join(self.upload_dir, f"{file_id}{ext}")
        with open(save_path, "wb") as f:
            f.write(file_bytes)
        return save_path

    def extract_audio_from_video(self, video_path: str) -> Optional[str]:
        """从视频中提取音频"""
        try:
            audio_path = os.path.splitext(video_path)[0] + ".wav"

            # 使用 ffmpeg 提取音频
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vn",  # 禁用视频
                "-acodec", "pcm_s16le",  # 音频编码
                "-ar", "16000",  # 采样率 16kHz（Whisper 推荐）
                "-ac", "1",  # 单声道
                "-y",  # 覆盖已存在文件
                audio_path
            ]

            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
                timeout=300  # 5分钟超时
            )

            logger.info(f"Extracted audio: {video_path} -> {audio_path}")
            return audio_path
        except subprocess.TimeoutExpired:
            logger.error(f"Audio extraction timeout: {video_path}")
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio extraction failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Audio extraction error: {e}")
            return None

    def transcribe_audio(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        """语音转文字（同步版本）"""
        if self.transcribe_engine and self.transcribe_engine.is_available():
            try:
                return self.transcribe_engine.transcribe(audio_path, **kwargs)
            except Exception as e:
                logger.warning(f"Transcribe engine failed, falling back to mock: {e}")

        logger.info("Using mock transcribe result")
        return {
            "transcript": "这是模拟的语音转文字结果...",
            "timestamps": [
                {"time": "00:00", "text": "大家好"},
                {"time": "00:05", "text": "今天我们来聊一聊"}
            ]
        }

    async def transcribe_audio_async(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        """语音转文字（异步版本，避免阻塞事件循环）"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.transcribe_audio, audio_path)


class MockMediaProcessor(MediaProcessor):
    """模拟媒体处理器（用于开发测试）"""

    def transcribe_audio(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        """模拟语音转文字"""
        return {
            "transcript": "大家好，今天我们来聊一聊新媒体运营的技巧。首先，我们要关注热点话题，然后进行对标分析竞品账号，最后创作优质内容。希望这些建议对你有帮助！",
            "timestamps": [
                {"time": "00:00", "text": "大家好"},
                {"time": "00:03", "text": "今天我们来聊一聊新媒体运营的技巧"},
                {"time": "00:08", "text": "首先，我们要关注热点话题"},
                {"time": "00:12", "text": "然后进行对标分析竞品账号"},
                {"time": "00:17", "text": "最后创作优质内容"},
                {"time": "00:22", "text": "希望这些建议对你有帮助"}
            ]
        }

