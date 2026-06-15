"""
转写引擎单元测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile


class TestWhisperLocalEngine:
    """Whisper 本地引擎测试"""

    def test_init(self):
        """测试初始化"""
        from backend.core.transcribe_engine import WhisperLocalEngine

        config = {"model": "base", "language": "zh"}
        engine = WhisperLocalEngine(config)

        assert engine.model_name == "base"
        assert engine.language == "zh"

    def test_check_availability_no_ffmpeg(self):
        """测试没有 ffmpeg 时不可用"""
        from backend.core.transcribe_engine import WhisperLocalEngine

        config = {}
        engine = WhisperLocalEngine(config)

        # mock subprocess.run 失败
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert not engine._check_availability()

    def test_check_availability_with_ffmpeg(self):
        """测试有 ffmpeg 时可用"""
        from backend.core.transcribe_engine import WhisperLocalEngine

        config = {}
        engine = WhisperLocalEngine(config)

        # mock 成功的 subprocess.run 和 import
        with patch("subprocess.run"), \
             patch("builtins.__import__"):
            assert engine._check_availability()

    def test_format_timestamp(self):
        """测试时间戳格式化"""
        from backend.core.transcribe_engine import WhisperLocalEngine

        engine = WhisperLocalEngine({})

        assert engine._format_timestamp(0) == "00:00"
        assert engine._format_timestamp(65) == "01:05"
        assert engine._format_timestamp(125.5) == "02:05"

    @patch("builtins.open")
    def test_transcribe_mock(self, mock_open):
        """测试 mock 转写结果"""
        from backend.core.transcribe_engine import WhisperLocalEngine

        engine = WhisperLocalEngine({"model": "base"})

        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_file = f.name

        try:
            # mock Whisper 模块
            mock_whisper = MagicMock()
            mock_whisper.load_model.return_value = MagicMock()
            mock_whisper.load_model.return_value.transcribe.return_value = {
                "text": "测试文本",
                "segments": [
                    {"start": 0, "text": "测试"}
                ]
            }

            with patch.dict("sys.modules", {"whisper": mock_whisper}):
                engine.is_available = True
                result = engine.transcribe(temp_file)

                assert "transcript" in result
                assert "timestamps" in result
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestAliyunEngine:
    """阿里云引擎测试"""

    def test_init(self):
        """测试初始化"""
        from backend.core.transcribe_engine import AliyunEngine

        config = {
            "access_key_id": "key_id",
            "access_key_secret": "secret",
            "app_key": "app_key"
        }
        engine = AliyunEngine(config)

        assert engine.access_key_id == "key_id"

    def test_check_availability_no_config(self):
        """测试配置不完整时不可用"""
        from backend.core.transcribe_engine import AliyunEngine

        engine = AliyunEngine({})
        assert not engine._check_availability()

    def test_check_availability_with_config(self):
        """测试配置完整时可用"""
        from backend.core.transcribe_engine import AliyunEngine

        config = {
            "access_key_id": "key_id",
            "access_key_secret": "secret",
            "app_key": "app_key"
        }
        engine = AliyunEngine(config)
        assert engine._check_availability()


class TestVolcengineEngine:
    """火山引擎引擎测试"""

    def test_init(self):
        """测试初始化"""
        from backend.core.transcribe_engine import VolcengineEngine

        config = {
            "access_key": "key",
            "secret_access_key": "secret",
            "app_id": "app_id"
        }
        engine = VolcengineEngine(config)

        assert engine.access_key == "key"

    def test_check_availability_no_config(self):
        """测试配置不完整时不可用"""
        from backend.core.transcribe_engine import VolcengineEngine

        engine = VolcengineEngine({})
        assert not engine._check_availability()

    def test_check_availability_with_config(self):
        """测试配置完整时可用"""
        from backend.core.transcribe_engine import VolcengineEngine

        config = {
            "access_key": "key",
            "secret_access_key": "secret",
            "app_id": "app_id"
        }
        engine = VolcengineEngine(config)
        assert engine._check_availability()


class TestTranscribeEngineManager:
    """转写引擎管理器测试"""

    def test_create_whisper_engine(self):
        """测试创建 Whisper 引擎"""
        from backend.core.transcribe_engine import TranscribeEngineManager

        config = {"model": "base"}
        manager = TranscribeEngineManager("whisper_local", config)

        assert manager.engine_type == "whisper_local"
        assert manager.engine is not None

    def test_create_aliyun_engine(self):
        """测试创建阿里云引擎"""
        from backend.core.transcribe_engine import TranscribeEngineManager

        config = {
            "access_key_id": "key_id",
            "access_key_secret": "secret",
            "app_key": "app_key"
        }
        manager = TranscribeEngineManager("aliyun", config)

        assert manager.engine_type == "aliyun"
        assert manager.engine is not None

    def test_create_volcengine_engine(self):
        """测试创建火山引擎"""
        from backend.core.transcribe_engine import TranscribeEngineManager

        config = {
            "access_key": "key",
            "secret_access_key": "secret",
            "app_id": "app_id"
        }
        manager = TranscribeEngineManager("volcengine", config)

        assert manager.engine_type == "volcengine"
        assert manager.engine is not None

    def test_transcribe_unavailable(self):
        """测试引擎不可用时报错"""
        from backend.core.transcribe_engine import TranscribeEngineManager

        manager = TranscribeEngineManager("whisper_local", {})
        # mock engine as unavailable
        manager.engine = None

        with pytest.raises(RuntimeError):
            manager.transcribe("audio.wav")

    def test_is_available(self):
        """测试可用性检查"""
        from backend.core.transcribe_engine import TranscribeEngineManager

        # 可用的情况
        config = {
            "access_key_id": "key_id",
            "access_key_secret": "secret",
            "app_key": "app_key"
        }
        manager = TranscribeEngineManager("aliyun", config)
        assert manager.is_available()

        # 不可用的情况
        manager = TranscribeEngineManager("whisper_local", {})
        manager.engine = None
        assert not manager.is_available()
