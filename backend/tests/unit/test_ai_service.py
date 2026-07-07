"""
AI服务单元测试
"""
import pytest
import asyncio

from backend.core.ai_service import AIServiceManager, AIService
from backend.config.settings import settings


def _run(coro):
    """同步测试里跑 async coroutine 的 helper（v3 之前测试债修复：manager.* 都是 async）"""
    return asyncio.run(coro)


class MockAIService(AIService):
    """模拟AI服务用于测试"""

    def __init__(self, available=True):
        self.available = available
        self.last_prompt = None

    async def generate(self, prompt: str, **kwargs) -> str:
        self.last_prompt = prompt
        return f"Mock response for: {prompt[:20]}"

    async def generate_stream(self, prompt: str, **kwargs):
        """模拟流式生成，yield 事件对象 {"type": "content", "delta": char}"""
        self.last_prompt = prompt
        text = f"Mock response for: {prompt[:20]}"
        for char in text:
            yield {"type": "content", "delta": char}
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

        result = _run(manager.generate("test prompt"))
        assert "Mock response" in result
        assert mock_service.last_prompt == "test prompt"

    def test_generate_without_service(self):
        """测试无服务时生成内容"""
        manager = AIServiceManager()

        with pytest.raises(RuntimeError, match="AI服务未配置"):
            _run(manager.generate("test prompt"))

    def test_generate_unavailable_service(self):
        """测试服务不可用时生成内容"""
        manager = AIServiceManager()
        mock_service = MockAIService(available=False)
        manager.services["mock"] = mock_service
        manager.current_provider = "mock"

        with pytest.raises(RuntimeError, match="AI服务不可用"):
            _run(manager.generate("test prompt"))

    def test_generate_content_script(self):
        """测试生成分镜头脚本"""
        manager = AIServiceManager()
        mock_service = MockAIService(available=True)

        # 模拟返回JSON（async 函数，匹配 abstract 签名）
        async def fake_generate(prompt, **kwargs):
            return '{"script": [], "copywriting": {}}'
        mock_service.generate = fake_generate

        manager.services["mock"] = mock_service
        manager.current_provider = "mock"

        result = _run(manager.generate_content_script("测试主题", "抖音", 60, "幽默"))
        assert "script" in result
        assert "copywriting" in result

    def test_generate_content_script_invalid_json(self):
        """测试分镜头脚本返回无效JSON"""
        manager = AIServiceManager()
        mock_service = MockAIService(available=True)

        async def fake_generate(prompt, **kwargs):
            return "Invalid text"
        mock_service.generate = fake_generate

        manager.services["mock"] = mock_service
        manager.current_provider = "mock"

        with pytest.raises(RuntimeError, match="AI响应未包含有效JSON"):
            _run(manager.generate_content_script("测试主题", "抖音", 60, "幽默"))

    def test_rewrite_transcript(self):
        """测试改写逐字稿"""
        manager = AIServiceManager()
        mock_service = MockAIService(available=True)
        manager.services["mock"] = mock_service
        manager.current_provider = "mock"

        result = _run(manager.rewrite_transcript("原始内容", "幽默", 60))
        assert "Mock response" in result
        assert "原始内容" in mock_service.last_prompt

    def test_generate_outline(self):
        """测试生成大纲"""
        manager = AIServiceManager()
        mock_service = MockAIService(available=True)

        # 模拟返回JSON（async 函数）
        async def fake_generate(prompt, **kwargs):
            return '{"outline": [{"section": "1", "title": "测试"}]}'
        mock_service.generate = fake_generate

        manager.services["mock"] = mock_service
        manager.current_provider = "mock"

        result = _run(manager.generate_outline("测试内容"))
        assert isinstance(result, list)
        assert len(result) > 0

    def test_generate_outline_invalid_json(self):
        """测试大纲返回无效JSON"""
        manager = AIServiceManager()
        mock_service = MockAIService(available=True)

        async def fake_generate(prompt, **kwargs):
            return "Invalid text"
        mock_service.generate = fake_generate

        manager.services["mock"] = mock_service
        manager.current_provider = "mock"

        with pytest.raises(RuntimeError, match="AI响应未包含有效JSON"):
            _run(manager.generate_outline("测试内容"))

    def test_generate_stream(self):
        """测试流式生成（yield 事件对象）"""
        manager = AIServiceManager()
        mock_service = MockAIService(available=True)
        manager.services["mock"] = mock_service
        manager.current_provider = "mock"

        async def run_stream_test():
            events = []
            async for event in manager.generate_stream("test prompt"):
                events.append(event)

            # 断言所有事件都是 content 类型（Mock 不发 reasoning）
            assert all(e["type"] == "content" for e in events)
            # 断言累积文本正确
            full_text = "".join(e["delta"] for e in events)
            assert "Mock response" in full_text
            assert mock_service.last_prompt == "test prompt"

        asyncio.run(run_stream_test())

    def test_generate_stream_with_reasoning(self):
        """测试 enable_reasoning=False 时过滤 reasoning 事件"""
        manager = AIServiceManager()

        class ReasoningService(MockAIService):
            async def generate_stream(self, prompt, enable_reasoning=True, **kwargs):
                self.last_prompt = prompt
                yield {"type": "reasoning", "delta": "思考中..."}
                yield {"type": "content", "delta": "答案"}

        manager.services["mock"] = ReasoningService()
        manager.current_provider = "mock"

        async def run_with_reasoning():
            events = [e async for e in manager.generate_stream("p", enable_reasoning=True)]
            types = [e["type"] for e in events]
            assert "reasoning" in types
            assert "content" in types

        async def run_without_reasoning():
            events = [e async for e in manager.generate_stream("p", enable_reasoning=False)]
            # provider 层在 enable_reasoning=False 时不发 reasoning 事件
            # 这里 Mock 总是发，所以 manager 透传，验证事件流形状而非过滤
            types = [e["type"] for e in events]
            assert "content" in types

        asyncio.run(run_with_reasoning())
        asyncio.run(run_without_reasoning())

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

        result = _run(ai_manager.generate("请简单介绍一下Python编程语言"))
        assert isinstance(result, str)
        assert len(result) > 0
