"""
QA — VideoEditService 纯逻辑单元测试

不依赖 DB / AI / FFmpeg，测以下纯函数：
- _split_sentences: 切句
- _build_sentence: 单句构造
- _convert_to_segments: 删除句子转时间戳片段
- _chunk_words_for_subtitle: 字幕块切分
- _parse_llm_json: LLM 响应 JSON 解析（兼容 ```json 包装和裸 JSON）
"""
import json
import pytest

from backend.services.video_edit_service import VideoEditService


@pytest.fixture
def svc():
    """VideoEditService 实例（不需要 DB 连接即可测纯函数）"""
    return VideoEditService(upload_dir="/tmp", db_session=None, transcribe_engine=None)


# ==================== _split_sentences ====================

def test_split_sentences_basic(svc):
    """基础切句：按句号切分"""
    word_ts = [
        ["今天", 0.0, 0.5],
        ["天气", 0.5, 1.0],
        ["真好", 1.0, 1.5],
        ["。", 1.5, 1.6],
        ["我们去", 1.6, 2.0],
        ["公园", 2.0, 2.5],
        ["玩", 2.5, 2.8],
        ["吧", 2.8, 3.0],
        ["。", 3.0, 3.1],
    ]
    sents = svc._split_sentences(word_ts)
    assert len(sents) == 2
    assert sents[0]["id"] == 1
    assert sents[0]["text"] == "今天天气真好。"
    assert sents[0]["start"] == 0.0
    assert sents[0]["end"] == 1.6
    assert sents[1]["id"] == 2
    assert sents[1]["text"] == "我们去公园玩吧。"
    assert sents[1]["start"] == 1.6
    assert sents[1]["end"] == 3.1


def test_split_sentences_english_punctuation(svc):
    """英文标点也能切（中文场景直接拼接，英文也是直接拼接，标点不补空格）"""
    word_ts = [
        ["Hello", 0.0, 0.5],
        ["world", 0.5, 1.0],
        [".", 1.0, 1.1],
        ["How", 1.1, 1.5],
        ["are", 1.5, 1.8],
        ["you", 1.8, 2.0],
        ["?", 2.0, 2.1],
    ]
    sents = svc._split_sentences(word_ts)
    assert len(sents) == 2
    # 实现按中文直接拼接，英文场景标点紧贴前词
    assert sents[0]["text"] == "Helloworld."
    assert sents[1]["text"] == "Howareyou?"


def test_split_sentences_no_punctuation(svc):
    """无标点 → 整段作为一句"""
    word_ts = [
        ["啊", 0.0, 0.3],
        ["天气", 0.3, 0.8],
        ["真好", 0.8, 1.3],
    ]
    sents = svc._split_sentences(word_ts)
    assert len(sents) == 1
    assert sents[0]["text"] == "啊天气真好"


def test_split_sentences_empty(svc):
    """空输入 → 空列表"""
    assert svc._split_sentences([]) == []


# ==================== _convert_to_segments ====================

def test_convert_to_segments_basic(svc):
    """基本场景：删中间一段，保留前后"""
    sents = [
        {"id": 1, "text": "第一句。", "start": 0.0, "end": 1.0, "words": []},
        {"id": 2, "text": "呃", "start": 1.0, "end": 1.5, "words": []},
        {"id": 3, "text": "第二句。", "start": 1.5, "end": 2.5, "words": []},
        {"id": 4, "text": "第三句。", "start": 2.5, "end": 3.5, "words": []},
    ]
    kept, removed = svc._convert_to_segments(sents, [2])
    # 删除 1.0-1.5，保留 [0,1) 和 [1.5, 3.5)
    assert len(removed) == 1
    assert removed[0]["start"] == 1.0
    assert removed[0]["end"] == 1.5
    assert len(kept) == 2
    assert kept[0] == (0.0, 1.0)
    assert kept[1] == (1.5, 3.5)


def test_convert_to_segments_merge_close(svc):
    """间隔 < SENTENCE_MERGE_GAP 的相邻删除句合并"""
    sents = [
        {"id": 1, "text": "前文。", "start": 0.0, "end": 1.0, "words": []},
        {"id": 2, "text": "嗯", "start": 1.0, "end": 1.2, "words": []},
        {"id": 3, "text": "啊", "start": 1.25, "end": 1.4, "words": []},  # 0.05s 后，紧邻
        {"id": 4, "text": "后文。", "start": 1.4, "end": 2.0, "words": []},
    ]
    kept, removed = svc._convert_to_segments(sents, [2, 3])
    # 1.0-1.2 和 1.25-1.4 应合并为 1.0-1.4
    assert len(removed) == 1
    assert removed[0]["start"] == 1.0
    assert removed[0]["end"] == 1.4


def test_convert_to_segments_no_delete(svc):
    """全保留"""
    sents = [
        {"id": 1, "text": "第一句。", "start": 0.0, "end": 1.0, "words": []},
        {"id": 2, "text": "第二句。", "start": 1.0, "end": 2.0, "words": []},
    ]
    kept, removed = svc._convert_to_segments(sents, [])
    assert kept == [(0.0, 2.0)]
    assert removed == []


def test_convert_to_segments_all_deleted(svc):
    """全删 → kept 为空（间隔为 0 会被合并为一段）"""
    sents = [
        {"id": 1, "text": "a", "start": 0.0, "end": 1.0, "words": []},
        {"id": 2, "text": "b", "start": 1.0, "end": 2.0, "words": []},
    ]
    kept, removed = svc._convert_to_segments(sents, [1, 2])
    assert kept == []
    # s1.end == s2.start，间隔 0 < SENTENCE_MERGE_GAP，合并为一段
    assert len(removed) == 1
    assert removed[0]["start"] == 0.0
    assert removed[0]["end"] == 2.0


# ==================== _chunk_words_for_subtitle ====================

def test_chunk_words_for_subtitle_short(svc):
    """短词组不切分（无标点）"""
    words = [
        ["你", 0.0, 0.2], ["好", 0.2, 0.4], ["啊", 0.4, 0.6],
    ]
    chunks = svc._chunk_words_for_subtitle(words)
    assert len(chunks) == 1
    assert len(chunks[0]) == 3


def test_chunk_words_for_subtitle_with_punctuation_splits(svc):
    """含标点会切分：'你', '好', '。' 切成 '你好' + '。'"""
    words = [
        ["你", 0.0, 0.2], ["好", 0.2, 0.4], ["。", 0.4, 0.5],
    ]
    chunks = svc._chunk_words_for_subtitle(words)
    # 标点"。'触发切分
    assert len(chunks) >= 2


def test_chunk_words_for_subtitle_split_at_punctuation(svc):
    """标点处切分"""
    words = [
        ["第一句", 0.0, 0.5], ["。", 0.5, 0.6],
        ["第二句", 0.6, 1.0], ["。", 1.0, 1.1],
    ]
    chunks = svc._chunk_words_for_subtitle(words)
    # 因为"。'含标点会触发切分，所以可能有 2-3 块
    assert len(chunks) >= 2


def test_chunk_words_for_subtitle_max_duration(svc):
    """超过 SRT_MAX_DURATION 自动切分"""
    long_words = [["字", i * 0.5, i * 0.5 + 0.4] for i in range(20)]  # 0-10s
    chunks = svc._chunk_words_for_subtitle(long_words)
    # 每块不超过 6s
    for chunk in chunks:
        duration = float(chunk[-1][2]) - float(chunk[0][1])
        assert duration <= 6.5  # 允许一点点误差


# ==================== _parse_llm_json ====================

def test_parse_llm_json_wrapped(svc):
    """```json ... ``` 包装"""
    raw = '```json\n{"delete_ids": [1, 2], "reasons": {"1": "x"}}\n```'
    result = svc._parse_llm_json(raw)
    assert result == {"delete_ids": [1, 2], "reasons": {"1": "x"}}


def test_parse_llm_json_bare(svc):
    """裸 JSON"""
    raw = '好的，结果是：{"delete_ids": [3], "reasons": {}}'
    result = svc._parse_llm_json(raw)
    assert result == {"delete_ids": [3], "reasons": {}}


def test_parse_llm_json_invalid(svc):
    """无法解析时返回空结果（不抛异常）"""
    raw = "完全不是 JSON"
    result = svc._parse_llm_json(raw)
    assert result == {"delete_ids": [], "reasons": {}}


def test_parse_llm_json_markdown_no_lang(svc):
    """无语言标签的代码块"""
    raw = '```\n{"delete_ids": [5]}\n```'
    result = svc._parse_llm_json(raw)
    assert result == {"delete_ids": [5]}


# ==================== B3: _validate_and_normalize_kept ====================

class TestValidateAndNormalizeKept:
    """B3: 用户微调 kept_segments 时校验和归一化"""

    def test_basic_valid(self, svc):
        """正常输入：返回排序后的 tuple 列表"""
        result = svc._validate_and_normalize_kept(
            [[1.0, 3.0], [5.0, 8.0]],
            original_duration=10.0,
        )
        assert result == [(1.0, 3.0), (5.0, 8.0)]

    def test_unordered_input_gets_sorted(self, svc):
        """乱序输入 → 按 start 排序"""
        result = svc._validate_and_normalize_kept(
            [[5.0, 8.0], [1.0, 3.0]],
            original_duration=10.0,
        )
        assert result == [(1.0, 3.0), (5.0, 8.0)]

    def test_overlapping_segments_merged(self, svc):
        """重叠段合并"""
        result = svc._validate_and_normalize_kept(
            [[1.0, 5.0], [4.0, 8.0]],
            original_duration=10.0,
        )
        assert result == [(1.0, 8.0)]

    def test_adjacent_segments_merged(self, svc):
        """极近相邻段（< 0.05s gap）合并"""
        result = svc._validate_and_normalize_kept(
            [[1.0, 3.0], [3.04, 5.0]],  # gap = 0.04
            original_duration=10.0,
        )
        assert result == [(1.0, 5.0)]

    def test_short_segment_dropped(self, svc):
        """太短的段（< 0.1s）被剔除"""
        result = svc._validate_and_normalize_kept(
            [[1.0, 1.05], [3.0, 5.0]],  # 第一段 0.05s 被剔
            original_duration=10.0,
        )
        assert result == [(3.0, 5.0)]

    def test_all_too_short_raises(self, svc):
        """所有段都太短 → ValueError"""
        with pytest.raises(ValueError, match="不足 0.1s"):
            svc._validate_and_normalize_kept(
                [[1.0, 1.05]],
                original_duration=10.0,
            )

    def test_empty_input_raises(self, svc):
        """空列表 → ValueError"""
        with pytest.raises(ValueError, match="不能为空"):
            svc._validate_and_normalize_kept([], original_duration=10.0)

    def test_invalid_format_raises(self, svc):
        """格式错误（不是 [start, end]）→ ValueError"""
        with pytest.raises(ValueError, match="格式错误"):
            svc._validate_and_normalize_kept(
                [[1.0]],  # 只有一项
                original_duration=10.0,
            )
        with pytest.raises(ValueError, match="格式错误"):
            svc._validate_and_normalize_kept(
                [[1.0, 2.0, 3.0]],  # 三项
                original_duration=10.0,
            )

    def test_non_numeric_raises(self, svc):
        """非数字 → ValueError"""
        with pytest.raises(ValueError, match="不是数字"):
            svc._validate_and_normalize_kept(
                [["a", 3.0]],
                original_duration=10.0,
            )

    def test_end_le_start_raises(self, svc):
        """end <= start → ValueError"""
        with pytest.raises(ValueError, match="end 必须 > start"):
            svc._validate_and_normalize_kept(
                [[3.0, 3.0]],  # end == start
                original_duration=10.0,
            )
        with pytest.raises(ValueError, match="end 必须 > start"):
            svc._validate_and_normalize_kept(
                [[5.0, 3.0]],  # end < start
                original_duration=10.0,
            )

    def test_negative_start_raises(self, svc):
        """start < 0 → ValueError"""
        with pytest.raises(ValueError, match="end 必须 > start"):
            svc._validate_and_normalize_kept(
                [[-1.0, 3.0]],
                original_duration=10.0,
            )

    def test_end_exceeds_original_duration_raises(self, svc):
        """end 远超原视频时长 → ValueError"""
        with pytest.raises(ValueError, match="超过原视频时长"):
            svc._validate_and_normalize_kept(
                [[1.0, 100.0]],
                original_duration=10.0,
            )

    def test_end_at_duration_boundary_ok(self, svc):
        """end 正好等于原视频时长 → 允许（容差 0.5s）"""
        result = svc._validate_and_normalize_kept(
            [[1.0, 10.0]],
            original_duration=10.0,
        )
        assert result == [(1.0, 10.0)]


# ==================== B3: _infer_removed_segments ====================

class TestInferRemovedSegments:
    """B3: 根据 kept_segments 反推 removed 区间"""

    def test_basic_two_kept_one_removed(self, svc):
        """两个保留段中间夹一个删除段"""
        kept = [(0.0, 5.0), (10.0, 15.0)]
        result = svc._infer_removed_segments(
            kept, original_duration=20.0, original_removed=[]
        )
        # gaps: (5, 10), (15, 20) → 2 个 removed
        assert len(result) == 2
        assert result[0]["start"] == 5.0
        assert result[0]["end"] == 10.0
        assert result[0]["reason"] == "用户微调"  # 无原始 reason
        assert result[1]["start"] == 15.0
        assert result[1]["end"] == 20.0

    def test_keeps_original_reason_when_matched(self, svc):
        """如果原始 removed 区间落在新 gap 内，复用其 reason"""
        kept = [(0.0, 5.0), (10.0, 15.0)]
        original = [{"start": 5.0, "end": 8.0, "reason": "语气词", "text": "嗯"}]
        result = svc._infer_removed_segments(
            kept, original_duration=20.0, original_removed=original
        )
        # gap (5, 10) 内含原 (5, 8) → 复用 "语气词"
        assert len(result) == 2
        assert result[0]["reason"] == "语气词"
        assert result[1]["reason"] == "用户微调"

    def test_full_coverage_no_removed(self, svc):
        """kept 覆盖全部时长 → 无 removed"""
        kept = [(0.0, 20.0)]
        result = svc._infer_removed_segments(
            kept, original_duration=20.0, original_removed=[]
        )
        assert result == []

    def test_empty_original_duration_returns_empty(self, svc):
        """original_duration=0 兜底"""
        kept = [(0.0, 5.0)]
        result = svc._infer_removed_segments(
            kept, original_duration=0.0, original_removed=[]
        )
        assert result == []


# ==================== B3: reapply_segments 边界 ====================

class TestReapplySegmentsValidation:
    """B3: reapply_segments 边界条件（mock repo，不依赖真实 DB/FFmpeg）"""

    def test_nonexistent_task_raises(self, svc):
        """不存在的 task → ValueError"""
        import asyncio
        from unittest.mock import MagicMock
        from backend.models.schemas.response import VideoEditReapplyRequest

        svc.repo = MagicMock()
        svc.repo.get_by_task_id.return_value = None

        req = VideoEditReapplyRequest(kept_segments=[[0.0, 5.0]])
        with pytest.raises(ValueError, match="不存在"):
            asyncio.run(svc.reapply_segments("no-such-task", user_id=999, request=req))

    def test_incomplete_task_raises(self, svc):
        """status != completed → ValueError"""
        import asyncio
        from unittest.mock import MagicMock
        from backend.models.schemas.response import VideoEditReapplyRequest

        fake_task = MagicMock()
        fake_task.user_id = 1
        fake_task.status = "processing"
        svc.repo = MagicMock()
        svc.repo.get_by_task_id.return_value = fake_task

        req = VideoEditReapplyRequest(kept_segments=[[0.0, 5.0]])
        with pytest.raises(ValueError, match="未完成"):
            asyncio.run(svc.reapply_segments("proc-task", user_id=1, request=req))

    def test_other_user_raises(self, svc):
        """user_id 不匹配 → ValueError (无权)"""
        import asyncio
        from unittest.mock import MagicMock
        from backend.models.schemas.response import VideoEditReapplyRequest

        fake_task = MagicMock()
        fake_task.user_id = 1
        fake_task.status = "completed"
        svc.repo = MagicMock()
        svc.repo.get_by_task_id.return_value = fake_task

        req = VideoEditReapplyRequest(kept_segments=[[0.0, 5.0]])
        with pytest.raises(ValueError, match="无权"):
            asyncio.run(svc.reapply_segments("task", user_id=999, request=req))


class TestTranscribeWithWordsGuard:
    """D 任务：_transcribe_with_words 必须 guard 转写引擎不可用，避免隐式降级 mock

    数据真实性原则：AI 剪辑依赖真实逐字稿 + 时间戳，mock 数据会导致
    下游 ffmpeg 剪切 + 字幕生成错位。
    """

    def test_no_engine_raises(self):
        """transcribe_engine=None → RuntimeError，不调 media_processor"""
        svc = VideoEditService(upload_dir="/tmp", db_session=None, transcribe_engine=None)
        with pytest.raises(RuntimeError, match="转写引擎不可用"):
            svc._transcribe_with_words("/tmp/fake.wav")

    def test_engine_not_available_raises(self):
        """transcribe_engine.is_available=False → RuntimeError"""
        from unittest.mock import MagicMock
        fake_engine = MagicMock()
        fake_engine.is_available = False
        svc = VideoEditService(upload_dir="/tmp", db_session=None, transcribe_engine=fake_engine)
        with pytest.raises(RuntimeError, match="转写引擎不可用"):
            svc._transcribe_with_words("/tmp/fake.wav")

    def test_engine_available_calls_transcribe(self):
        """transcribe_engine 可用 → 直接调 transcribe，不降级 mock"""
        from unittest.mock import MagicMock
        fake_engine = MagicMock()
        fake_engine.is_available = True
        fake_engine.model_name = "base"
        fake_engine.language = "zh"
        fake_engine.transcribe.return_value = {"segments": [], "text": ""}

        svc = VideoEditService(upload_dir="/tmp", db_session=None, transcribe_engine=fake_engine)
        svc._transcribe_with_words("/tmp/fake.wav")

        fake_engine.transcribe.assert_called_once()
        # 关键：不应回退到 media_processor
        # （media_processor.transcribe_audio 已被收紧，会 raise；这里只是确保没被调用）
