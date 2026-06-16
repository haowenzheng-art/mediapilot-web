"""
AI服务单元测试
"""
import pytest
import asyncio

from backend.core.ai_service import AIServiceManager, AIService


class MockAIService(AIService):
    """模拟AI服务用于测试"""

    def __init__(self, available=True):
        self.available = available
        self.last_prompt = None

    def generate(self, prompt: str, **kwargs) -> str:
        self.last_prompt = prompt
        return f"Mock response for: {prompt[:20]}"

    async def generate_stream(self, prompt: str, **kwargs):
        """模拟流式生成"""
        self.last_prompt = prompt
        text = f"Mock response for: {prompt[:20]}"
        for char in text:
            yield char
            await asyncio.sleep(0.01)

    def is_available(self) -> bool:
        return self.available


class TestAIServiceManager:
    """AI服务管理器测试"""

    def test_manager_initialization(self):
        """测试管理器初始化"""
        manager = AIServiceManager()
        assert manager.current_provider is None
        assert manager.services == {}
        assert not manager.is_available()

    def test_configure_service(self):
        """测试配置服务"""
        manager = AIServiceManager()

        # 使用模拟服务进行测试
        mock_service = MockAIService()
        manager.services["mock"] = mock_service
        manager.current_provider = "mock"

        assert manager.get_current_service() == mock_service
        assert manager.is_available()

    def test_generate_with_service(self):
        """测试使用服务生成内容"""
        manager = AIServiceManager()
        mock_service = MockAIService()
        manager.services["mock"] = mock_service
        manager.current_provider = "mock"

        result = manager.generate("test prompt")
        assert "Mock response" in result
        assert mock_service.last_prompt == "test prompt"

    def test_generate_without_service(self):
        """测试无服务时生成内容"""
        manager = AIServiceManager()

        with pytest.raises(RuntimeError, match="AI服务未配置"):
            manager.generate("test prompt")

    def test_generate_unavailable_service(self):
        """测试服务不可用时生成内容"""
        manager = AIServiceManager()
        mock_service = MockAIService(available=False)
        manager.services["mock"] = mock_service
        manager.current_provider = "mock"

        with pytest.raises(RuntimeError, match="AI服务不可用"):
            manager.generate("test prompt")

    def test_generate_content_script(self):
        """测试生成分镜头脚本"""
        manager = AIServiceManager()
        mock_service = MockAIService(available=True)

        # 模拟返回JSON
        mock_service.generate = lambda prompt, **kwargs: '{"script": [], "copywriting": {}}'

        manager.services["mock"] = mock_service
        manager.current_provider = "mock"

        result = manager.generate_content_script("测试主题", "抖音", 60, "幽默")
        assert "script" in result
        assert "copywriting" in result

    def test_generate_content_script_invalid_json(self):
        """测试分镜头脚本返回无效JSON"""
        manager = AIServiceManager()
        mock_service = MockAIService(available=True)
        mock_service.generate = lambda prompt, **kwargs: "Invalid text"

        manager.services["mock"] = mock_service
        manager.current_provider = "mock"

        with pytest.raises(RuntimeError, match="AI响应未包含有效JSON"):
            manager.generate_content_script("测试主题", "抖音", 60, "幽默")

    def test_rewrite_transcript(self):
        """测试改写逐字稿"""
        manager = AIServiceManager()
        mock_service = MockAIService(available=True)
        manager.services["mock"] = mock_service
        manager.current_provider = "mock"

        result = manager.rewrite_transcript("原始内容", "幽默", 60)
        assert "Mock response" in result
        assert "原始内容" in mock_service.last_prompt

    def test_generate_outline(self):
        """测试生成大纲"""
        manager = AIServiceManager()
        mock_service = MockAIService(available=True)

        # 模拟返回JSON
        mock_service.generate = lambda prompt, **kwargs: '{"outline": [{"section": "1", "title": "测试"}]}'

        manager.services["mock"] = mock_service
        manager.current_provider = "mock"

        result = manager.generate_outline("测试内容")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_generate_outline_invalid_json(self):
        """测试大纲返回无效JSON"""
        manager = AIServiceManager()
        mock_service = MockAIService(available=True)
        mock_service.generate = lambda prompt, **kwargs: "Invalid text"

        manager.services["mock"] = mock_service
        manager.current_provider = "mock"

        with pytest.raises(RuntimeError, match="AI响应未包含有效JSON"):
            manager.generate_outline("测试内容")

    def test_generate_stream(self):
        """测试流式生成"""
        manager = AIServiceManager()
        mock_service = MockAIService(available=True)
        manager.services["mock"] = mock_service
        manager.current_provider = "mock"

        async def run_stream_test():
            chunks = []
            async for chunk in manager.generate_stream("test prompt"):
                chunks.append(chunk)

            full_text = "".join(chunks)
            assert "Mock response" in full_text
            assert mock_service.last_prompt == "test prompt"

        asyncio.run(run_stream_test())

    def test_generate_stream_unavailable_service(self):
        """测试服务不可用时流式生成"""
        manager = AIServiceManager()

        async def run_stream_test():
            with pytest.raises(RuntimeError, match="AI服务未配置"):
                async for _ in manager.generate_stream("test prompt"):
                    pass

        asyncio.run(run_stream_test())


# 测试真实配置（如果环境变量存在）
class TestRealAIConfiguration:
    """真实AI配置测试（集成测试）"""

    @pytest.mark.skipif(not settings.AI_API_KEY, reason="AI_API_KEY未配置")
    def test_configure_real_ark_service(self):
        """测试配置真实的Ark服务"""
        from backend.core.ai_service import ai_manager

        ai_manager.configure(
            provider=settings.AI_PROVIDER,
            api_key=settings.AI_API_KEY,
            base_url=settings.AI_BASE_URL,
            model=settings.AI_MODEL
        )

        assert ai_manager.is_available()
        assert ai_manager.current_provider is not None

    @pytest.mark.skipif(not settings.AI_API_KEY, reason="AI_API_KEY未配置")
    @pytest.mark.integration
    def test_real_generation(self):
        """测试真实的AI生成"""
        from backend.core.ai_service import ai_manager

        ai_manager.configure(
            provider=settings.AI_PROVIDER,
            api_key=settings.AI_API_KEY,
            base_url=settings.AI_BASE_URL,
            model=settings.AI_MODEL
        )

        result = ai_manager.generate("请简单介绍一下Python编程语言")
        assert isinstance(result, str)
        assert len(result) > 0
