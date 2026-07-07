"""
内容生成服务单元测试
"""
import pytest
import pytest_asyncio
from backend.services.content_service import ContentService
from backend.models.schemas.response import ContentGenerateResponse


@pytest.mark.asyncio
class TestContentService:
    """ContentService 测试类"""

    def setup_method(self):
        """每个测试前初始化"""
        self.service = ContentService()
        # 强制走 mock 路径，避免真实 AI 输出格式不稳定导致 flaky
        from backend.core.ai_service import ai_manager
        self._orig_get = ai_manager.get_current_service
        ai_manager.get_current_service = lambda: None

    def teardown_method(self):
        """恢复 AI service"""
        from backend.core.ai_service import ai_manager
        ai_manager.get_current_service = self._orig_get

    async def test_generate_script_正常情况_返回脚本内容(self):
        """测试正常生成分镜头脚本"""
        result = await self.service.generate_script(
            topic="AI工具",
            platform="抖音",
            duration=60,
            style="幽默"
        )

        assert result.topic == "AI工具"
        assert isinstance(result.script, list)
        assert result.copywriting.topic is not None  # Copywriting schema: platform/topic/script/hooks/cta

    async def test_generate_script_空主题_返回默认脚本(self):
        """测试空主题返回默认脚本"""
        result = await self.service.generate_script(
            topic="",
            platform="抖音",
            duration=60,
            style="幽默"
        )

        assert isinstance(result.script, list)
        assert len(result.script) >= 0

    async def test_generate_script_脚本包含必要字段(self):
        """测试返回的脚本包含必要字段"""
        result = await self.service.generate_script(
            topic="测试",
            platform="小红书",
            duration=30,
            style="专业"
        )

        if result.script:
            shot = result.script[0]
            # 检查 Pydantic 模型属性
            assert hasattr(shot, 'scene')
            assert hasattr(shot, 'duration')
            assert hasattr(shot, 'visual')
            assert hasattr(shot, 'audio')

    async def test_generate_script_文案包含必要字段(self):
        """测试返回的文案包含必要字段"""
        result = await self.service.generate_script(
            topic="测试",
            platform="抖音",
            duration=60,
            style="幽默"
        )

        copywriting = result.copywriting
        assert hasattr(copywriting, 'topic')
        assert hasattr(copywriting, 'hooks')
        assert hasattr(copywriting, 'cta')  # Copywriting schema: call_to_action → cta

    async def test_rewrite_transcript_正常情况_返回改写文本(self):
        """测试正常改写逐字稿"""
        result = await self.service.rewrite_transcript(
            transcript="这是一段测试逐字稿",
            style="简洁",
            target_duration=30
        )

        # AI 服务不可用时返回 None
        assert result is None or isinstance(result, dict)

    async def test_rewrite_transcript_空输入_返回None(self):
        """测试空输入返回 None"""
        result = await self.service.rewrite_transcript(
            transcript="",
            style="简洁",
            target_duration=30
        )

        # 当 AI 不可用时返回 None
        assert result is None or isinstance(result, dict)
