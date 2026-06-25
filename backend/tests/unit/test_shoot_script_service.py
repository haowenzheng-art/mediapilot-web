"""
QA — ShootScriptService 纯逻辑单元测试

不需要 DB / AI / HTTP，只测：
- _get_platform_config: 三平台配置
- _build_prompt: 提示词构造
- _mock_generate: 三平台 mock 数据
- _parse_ai_result: AI 文本解析、# 清洗
- _calculate_duration: 时长估算
"""
import pytest
from backend.services.shoot_script_service import ShootScriptService
from backend.models.domain.shoot_script import (
    ShootScriptRequest, PlatformType, ScriptStyle, Shot
)


@pytest.fixture
def svc():
    return ShootScriptService()


@pytest.fixture
def req_douyin():
    return ShootScriptRequest(
        topic="AI写作",
        platform=PlatformType.DOUYIN,
        style=ScriptStyle.ENERGETIC,
        persona="干货博主"
    )


@pytest.fixture
def req_xhs():
    return ShootScriptRequest(
        topic="AI写作",
        platform=PlatformType.XIAOHONGSHU,
        style=ScriptStyle.RELAXED,
    )


@pytest.fixture
def req_bili():
    return ShootScriptRequest(
        topic="AI写作",
        platform=PlatformType.BILIBILI,
        style=ScriptStyle.PROFESSIONAL,
    )


class TestPlatformConfig:
    def test_douyin_config(self, svc):
        c = svc._get_platform_config(PlatformType.DOUYIN, ScriptStyle.ENERGETIC)
        assert c["orientation"] == "竖屏"
        assert "60" in c["target_duration"]

    def test_xhs_config(self, svc):
        c = svc._get_platform_config(PlatformType.XIAOHONGSHU, ScriptStyle.RELAXED)
        assert c["orientation"] == "竖屏"
        assert "3" in c["target_duration"]

    def test_bili_config(self, svc):
        c = svc._get_platform_config(PlatformType.BILIBILI, ScriptStyle.PROFESSIONAL)
        assert c["orientation"] == "横屏"


class TestBuildPrompt:
    def test_includes_topic_and_persona(self, svc, req_douyin):
        cfg = svc._get_platform_config(req_douyin.platform, req_douyin.style)
        p = svc._build_prompt(req_douyin, cfg)
        assert "AI写作" in p
        assert "干货博主" in p
        assert "douyin" in p
        # 规则约束
        assert '禁止使用"#"符号' in p

    def test_default_persona_when_missing(self, svc, req_xhs):
        cfg = svc._get_platform_config(req_xhs.platform, req_xhs.style)
        p = svc._build_prompt(req_xhs, cfg)
        assert "专业视频创作者" in p

    def test_style_mapping(self, svc, req_bili):
        cfg = svc._get_platform_config(req_bili.platform, req_bili.style)
        p = svc._build_prompt(req_bili, cfg)
        assert "专业分析" in p


class TestMockGenerate:
    """_mock_generate — 三平台都应返回 (shots, title, hooks, cta, tags)"""

    @pytest.mark.parametrize("fixture_name", ["req_douyin", "req_xhs", "req_bili"])
    def test_returns_full_tuple(self, svc, fixture_name, request):
        req = request.getfixturevalue(fixture_name)
        cfg = svc._get_platform_config(req.platform, req.style)
        shots, title, hooks, cta, tags = svc._mock_generate(req, cfg)
        assert isinstance(shots, list) and len(shots) >= 3
        assert all(isinstance(s, Shot) for s in shots)
        assert title and isinstance(title, str)
        assert isinstance(hooks, list) and len(hooks) >= 1
        assert cta and isinstance(cta, str)
        assert isinstance(tags, list)

    def test_douyin_has_5_shots(self, svc, req_douyin):
        cfg = svc._get_platform_config(req_douyin.platform, req_douyin.style)
        shots, *_ = svc._mock_generate(req_douyin, cfg)
        assert len(shots) == 5

    def test_xhs_has_8_shots(self, svc, req_xhs):
        cfg = svc._get_platform_config(req_xhs.platform, req_xhs.style)
        shots, *_ = svc._mock_generate(req_xhs, cfg)
        assert len(shots) == 8

    def test_bili_has_15_shots(self, svc, req_bili):
        cfg = svc._get_platform_config(req_bili.platform, req_bili.style)
        shots, *_ = svc._mock_generate(req_bili, cfg)
        assert len(shots) == 15

    def test_topic_in_title(self, svc, req_douyin):
        cfg = svc._get_platform_config(req_douyin.platform, req_douyin.style)
        _, title, _, _, _ = svc._mock_generate(req_douyin, cfg)
        assert req_douyin.topic in title

    def test_topic_in_tags(self, svc, req_douyin):
        cfg = svc._get_platform_config(req_douyin.platform, req_douyin.style)
        _, _, _, _, tags = svc._mock_generate(req_douyin, cfg)
        assert req_douyin.topic in tags


class TestParseAIResult:
    STANDARD_OUTPUT = """标题：3分钟讲清AI写作

钩子（2-3个备选）：
1. 90%的人都不知道这个工具
2. 一句话搞定一篇文章

分镜头脚本：
镜头1
时长：0:00-0:10
画面：人物正面特写
台词：今天聊聊AI写作。
场景建议：简洁背景
运镜建议：固定镜头

镜头2
时长：0:10-0:20
画面：中景
台词：很多人还在用老办法。
场景建议：自然光
运镜建议：轻微推进

行动号召：点赞关注！

标签：AI，写作，干货
"""

    def test_extracts_title(self, svc):
        r = svc._parse_ai_result(self.STANDARD_OUTPUT, PlatformType.DOUYIN)
        assert r["title"] == "3分钟讲清AI写作"

    def test_extracts_hooks(self, svc):
        r = svc._parse_ai_result(self.STANDARD_OUTPUT, PlatformType.DOUYIN)
        assert len(r["hooks"]) >= 2
        # 编号已剥离
        for h in r["hooks"]:
            assert not h.startswith(("1.", "2.", "3."))

    def test_extracts_shots(self, svc):
        r = svc._parse_ai_result(self.STANDARD_OUTPUT, PlatformType.DOUYIN)
        assert len(r["shots"]) == 2
        assert r["shots"][0]["dialogue"] == "今天聊聊AI写作。"
        assert r["shots"][1]["visual_description"] == "中景"

    def test_extracts_tags(self, svc):
        r = svc._parse_ai_result(self.STANDARD_OUTPUT, PlatformType.DOUYIN)
        assert "AI" in r["tags"]
        assert "写作" in r["tags"]

    def test_strips_hash_symbol(self, svc):
        """规范要求 AI 内容禁 # — 解析层兜底剥离"""
        text = """标题：#测试#

分镜头脚本：
镜头1
台词：#内容#带井号
"""
        r = svc._parse_ai_result(text, PlatformType.DOUYIN)
        assert "#" not in r["title"]
        # 镜头中的 # 也应清理（解析时已 replace）
        for shot in r["shots"]:
            assert "#" not in shot.get("dialogue", "")

    def test_empty_input_does_not_crash(self, svc):
        r = svc._parse_ai_result("", PlatformType.DOUYIN)
        assert isinstance(r["shots"], list)
        assert isinstance(r["hooks"], list)
        assert isinstance(r["title"], str)


class TestCalculateDuration:
    def test_short_script(self, svc):
        shots = [Shot(shot_number=i, duration="0:00-0:10",
                      visual_description="x", dialogue="x") for i in range(5)]
        assert svc._calculate_duration(shots) == "约60秒"

    def test_medium_script(self, svc):
        shots = [Shot(shot_number=i, duration="0:00-0:10",
                      visual_description="x", dialogue="x") for i in range(8)]
        assert svc._calculate_duration(shots) == "约3分钟"

    def test_long_script(self, svc):
        shots = [Shot(shot_number=i, duration="0:00-0:10",
                      visual_description="x", dialogue="x") for i in range(15)]
        assert svc._calculate_duration(shots) == "约5-10分钟"
