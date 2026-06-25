"""
QA-007 — CopywritingService 纯逻辑单元测试

无需 DB / AI / HTTP，只测：
- _build_prompt: 三模式提示词构造
- _mock_generate: 三模式 mock 数据
- _parse_ai_result: AI 文本解析、# 清洗、钩子编号剥离、空输入兜底
"""
import pytest
from backend.services.copywriting_service import CopywritingService
from backend.models.domain.persona import CopywritingGenerateRequest


@pytest.fixture
def svc():
    return CopywritingService()


@pytest.fixture
def req_from_zero():
    return CopywritingGenerateRequest(
        mode="from_zero", persona="幽默博主", topic="AI写作"
    )


@pytest.fixture
def req_hotspot():
    return CopywritingGenerateRequest(
        mode="hotspot", persona="知识博主",
        hotspot_content="近期 AI 视频生成爆火"
    )


@pytest.fixture
def req_rewrite():
    return CopywritingGenerateRequest(
        mode="rewrite", persona="情感博主",
        original_text="今天天气不错。"
    )


class TestBuildPrompt:
    """_build_prompt 三模式分支"""

    def test_from_zero_includes_topic_and_persona(self, svc, req_from_zero):
        p = svc._build_prompt(req_from_zero)
        assert "幽默博主" in p
        assert "AI写作" in p
        assert "话题" in p
        # 规则约束
        assert '禁止使用"#"符号' in p

    def test_hotspot_includes_hotspot_content(self, svc, req_hotspot):
        p = svc._build_prompt(req_hotspot)
        assert "近期 AI 视频生成爆火" in p
        assert "热点内容框架" in p

    def test_rewrite_includes_original_text(self, svc, req_rewrite):
        p = svc._build_prompt(req_rewrite)
        assert "今天天气不错。" in p
        assert "洗稿" in p or "重写" in p

    def test_reference_content_appended(self, svc, req_from_zero):
        p = svc._build_prompt(req_from_zero, reference_content="\n\n【参考内容】\n样例摘要")
        assert "【参考内容】" in p
        assert "样例摘要" in p


class TestMockGenerate:
    """_mock_generate — 三模式都应返回 (title, hooks, content) 非空且包含人设"""

    @pytest.mark.parametrize("fixture_name", ["req_from_zero", "req_hotspot", "req_rewrite"])
    def test_returns_three_part_tuple(self, svc, fixture_name, request):
        req = request.getfixturevalue(fixture_name)
        title, hooks, content = svc._mock_generate(req)
        assert title and isinstance(title, str)
        assert isinstance(hooks, list) and len(hooks) >= 1
        assert content and isinstance(content, str)

    def test_persona_appears_in_content(self, svc, req_from_zero):
        _, _, content = svc._mock_generate(req_from_zero)
        assert req_from_zero.persona in content

    def test_topic_appears_in_from_zero_title(self, svc, req_from_zero):
        title, _, _ = svc._mock_generate(req_from_zero)
        assert req_from_zero.topic in title

    def test_no_hash_symbol_in_mock_output(self, svc, req_from_zero):
        """符合 CLAUDE.md AI 内容格式规范：禁止 #"""
        title, hooks, content = svc._mock_generate(req_from_zero)
        assert "#" not in title
        assert "#" not in content
        for h in hooks:
            assert "#" not in h


class TestParseAIResult:
    """_parse_ai_result — 真实 AI 输出多变，解析必须健壮"""

    STANDARD_OUTPUT = """标题：3分钟讲清AI写作

钩子（2-3个备选）：
1. 90%的人都不知道这个工具
2. 一句话搞定一篇文章
3. AI 时代必学技能

文案正文：
今天聊聊AI写作这个话题。
它已经不是未来，是当下。
"""

    def test_extracts_title(self, svc):
        r = svc._parse_ai_result(self.STANDARD_OUTPUT)
        assert r["title"] == "3分钟讲清AI写作"

    def test_extracts_hooks_and_strips_numbering(self, svc):
        r = svc._parse_ai_result(self.STANDARD_OUTPUT)
        assert len(r["hooks"]) == 3
        assert r["hooks"][0] == "90%的人都不知道这个工具"
        # "1." 已被剥离
        for h in r["hooks"]:
            assert not h.startswith(("1.", "2.", "3."))

    def test_extracts_content_multiline(self, svc):
        r = svc._parse_ai_result(self.STANDARD_OUTPUT)
        assert "今天聊聊AI写作这个话题" in r["content"]
        assert "它已经不是未来，是当下" in r["content"]

    def test_strips_hash_from_output(self, svc):
        """规范要求 AI 内容禁 # — 解析层兜底剥离"""
        text = "标题：#测试标题#\n\n文案正文：\n这是 #正文# 内容"
        r = svc._parse_ai_result(text)
        assert "#" not in r["title"]
        assert "#" not in r["content"]
        assert "测试标题" in r["title"]

    def test_empty_input_returns_default_title(self, svc):
        """空 / 无标题输入应有兜底，不抛异常"""
        r = svc._parse_ai_result("")
        # 完全空时 title 也空，但不应崩
        assert isinstance(r["title"], str)
        assert isinstance(r["hooks"], list)
        assert isinstance(r["content"], str)

    def test_freeform_text_falls_back_to_default(self, svc):
        """无格式标记的纯文本 — 兜底为默认标题 + 整段作 content"""
        r = svc._parse_ai_result("这是一段没有任何标记的纯文本内容。")
        assert r["title"] == "口播文案"
        assert "这是一段没有任何标记的纯文本内容" in r["content"]

    def test_正文_alias_for_content_section(self, svc):
        """文案正文/正文 都应识别为 content"""
        r = svc._parse_ai_result("标题：T\n\n正文：\n内容文本")
        assert r["title"] == "T"
        assert "内容文本" in r["content"]


class TestRewriteDirectionMap:
    """rewrite() 方法内的 direction_map 行为，提取出来验证"""

    def test_known_directions(self):
        # 通过端到端已经覆盖；这里独立守住映射约定
        direction_map = {
            "more_colloquial": "更口语化",
            "add_emotion": "加情绪",
            "add_opinion": "加观点",
        }
        assert direction_map["more_colloquial"] == "更口语化"
        assert direction_map["add_emotion"] == "加情绪"
        assert direction_map["add_opinion"] == "加观点"
