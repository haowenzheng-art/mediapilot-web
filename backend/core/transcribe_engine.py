"""
音视频转写引擎

支持多种转写引擎：
- whisper_local: 本地 Whisper 模型
- aliyun: 阿里云语音识别
- volcengine: 火山引擎语音转写
"""
import os
import subprocess
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class TranscribeEngine(ABC):
    """转写引擎抽象基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_available = self._check_availability()

    @abstractmethod
    def _check_availability(self) -> bool:
        """检查引擎是否可用"""
        pass

    @abstractmethod
    def transcribe(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        """
        执行转写

        Args:
            audio_path: 音频文件路径
            **kwargs: 其他参数（如语言、模型等）

        Returns:
            转写结果字典，包含：
            - transcript: 完整文本
            - timestamps: 时间戳列表 [{"time": "00:00", "text": "xxx"}]
        """
        pass


class WhisperLocalEngine(TranscribeEngine):
    """本地 Whisper 转写引擎"""

    def __init__(self, config: Dict[str, Any]):
        self.model_name = config.get("model", "base")
        self.language = config.get("language", "zh")
        super().__init__(config)

    def _check_availability(self) -> bool:
        """检查 Whisper 是否可用"""
        try:
            import whisper
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2
            )
            return True
        except (ImportError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("Whisper local engine not available")
            return False

    def transcribe(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        """
        使用 Whisper 进行转写

        Args:
            audio_path: 音频文件路径
            **kwargs: 其他参数

        Returns:
            转写结果
        """
        if not self.is_available:
            raise RuntimeError("Whisper engine not available")

        model = kwargs.get("model", self.model_name)
        language = kwargs.get("language", self.language)

        try:
            import whisper

            # 加载模型
            whisper_model = whisper.load_model(model)

            # 执行转写
            result = whisper_model.transcribe(
                audio_path,
                language=language,
                verbose=False
            )

            # 解析结果
            transcript = result.get("text", "")
            segments = result.get("segments", [])

            timestamps = []
            for segment in segments:
                start_time = self._format_timestamp(segment.get("start", 0))
                timestamps.append({
                    "time": start_time,
                    "text": segment.get("text", "").strip()
                })

            return {
                "transcript": transcript.strip(),
                "timestamps": timestamps
            }

        except Exception as e:
            logger.error(f"Whisper transcribe failed: {e}")
            raise

    def _format_timestamp(self, seconds: float) -> str:
        """将秒数格式化为时间戳 MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"


class AliyunEngine(TranscribeEngine):
    """阿里云语音识别引擎"""

    def __init__(self, config: Dict[str, Any]):
        self.access_key_id = config.get("access_key_id", "")
        self.access_key_secret = config.get("access_key_secret", "")
        self.app_key = config.get("app_key", "")
        super().__init__(config)

    def _check_availability(self) -> bool:
        """检查阿里云配置是否完整"""
        return all([self.access_key_id, self.access_key_secret, self.app_key])

    def transcribe(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        """使用阿里云进行转写"""
        # TODO: 实现阿里云 API 调用
        raise NotImplementedError("Aliyun engine not implemented yet")


class VolcengineEngine(TranscribeEngine):
    """火山引擎语音转写引擎"""

    def __init__(self, config: Dict[str, Any]):
        self.access_key = config.get("access_key", "")
        self.secret_access_key = config.get("secret_access_key", "")
        self.app_id = config.get("app_id", "")
        super().__init__(config)

    def _check_availability(self) -> bool:
        """检查火山引擎配置是否完整"""
        return all([self.access_key, self.secret_access_key, self.app_id])

    def transcribe(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        """使用火山引擎进行转写"""
        # TODO: 实现火山引擎 API 调用
        raise NotImplementedError("Volcengine engine not implemented yet")


class MockEngine(TranscribeEngine):
    """Mock 转写引擎（用于测试和演示）"""

    def _check_availability(self) -> bool:
        return True

    def transcribe(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        return {
            "transcript": "这是模拟转写结果。实际使用时请配置 whisper_local、aliyun 或 volcengine 引擎。",
            "timestamps": [
                {"time": "00:00", "text": "这是模拟转写结果"},
                {"time": "00:03", "text": "实际使用时请配置真实转写引擎"},
            ]
        }


class TranscribeEngineManager:
    """转写引擎管理器"""

    def __init__(self, engine_type: str, config: Dict[str, Any]):
        self.engine_type = engine_type
        self.engine = self._create_engine(engine_type, config)

    def _create_engine(self, engine_type: str, config: Dict[str, Any]) -> Optional[TranscribeEngine]:
        """根据类型创建引擎"""
        engines = {
            "whisper_local": WhisperLocalEngine,
            "aliyun": AliyunEngine,
            "volcengine": VolcengineEngine,
            "mock": MockEngine,
        }

        engine_class = engines.get(engine_type)
        if not engine_class:
            logger.warning(f"Unknown engine type: {engine_type}")
            return None

        return engine_class(config)

    def transcribe(self, audio_path: str, **kwargs) -> Dict[str, Any]:
        """执行转写"""
        if not self.engine or not self.engine.is_available:
            raise RuntimeError(f"Transcribe engine {self.engine_type} not available")

        return self.engine.transcribe(audio_path, **kwargs)

    def is_available(self) -> bool:
        """检查引擎是否可用"""
        return self.engine is not None and self.engine.is_available

    def get_available_engines(self) -> List[str]:
        """获取可用的引擎列表"""
        available = []
        test_config = {}

        for engine_name in ["whisper_local", "aliyun", "volcengine"]:
            engine = self._create_engine(engine_name, test_config)
            if engine and engine.is_available:
                available.append(engine_name)

        return available
