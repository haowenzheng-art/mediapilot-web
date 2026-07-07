"""
视频剪辑服务（AI 自动去除口播视频磕巴片段）

三层删除架构：
  第1层 句子级：filler 句识别 + 口吃识别 + 无效开头/结尾 + LLM 补充
  第2层 停顿修剪：保留段之间停顿 > 阈值 → 压缩到 0.3s
  第3层 词级精细：保留段内部 filler 词 + 口吃词 + LLM 补充

所有删减行为由 VideoEditConfig 控制，用户可选择预设或自定义参数。
"""
import asyncio
import json
import logging
import os
import re
import subprocess
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple, Set

from sqlalchemy.orm import Session

from backend.core.ai_service import ai_manager
from backend.core.media_processor import MediaProcessor
from backend.core.transcribe_engine import TranscribeEngineManager
from backend.models.schemas.response import (
    VideoEditResponse,
    VideoEditSegment,
)
from backend.repository.video_edit_repo import VideoEditRepository
from backend.config.database import SessionLocal

logger = logging.getLogger(__name__)


# =============================================================================
# 删减配置
# =============================================================================

@dataclass
class VideoEditConfig:
    """
    视频剪辑配置，控制各维度删减行为。

    Attributes:
        filler_level: 语气词删减  off/minimal/normal
        stutter_level: 口吃重复处理  off/2（连续2次触发）
        pause_threshold: 停顿修剪阈值（秒），0=关闭
        edge_level: 无效开头/结尾处理  off/conservative/normal
        llm_mode: LLM 辅助模式  off/auxiliary/primary
        sentence_silence_gap: 切句时的停顿阈值（秒）
        segment_gap: 保留段之间的最小间隙（秒），0=不留间隙
        sentence_max_chars: 单句最大字符数（触发强制切分）
    """
    filler_level: str = "normal"       # off / minimal / normal / aggressive
    stutter_level: int = 0             # 0=关闭, 2=连续2次触发
    pause_threshold: float = 1.5      # 秒，0=关闭
    edge_level: str = "off"           # off / conservative / normal
    llm_mode: str = "auxiliary"       # off / auxiliary / primary
    sentence_silence_gap: float = 0.5
    segment_gap: float = 0.0          # 0=不留间隙（直接拼接）
    sentence_max_chars: int = 30
    # aggressive 专属：句中更短的 filler 词阈值
    intra_sentence_filler_min_len: int = 2  # 句中国际判 filler 的最小词长

    @classmethod
    def from_params(
        cls,
        strength: str = "medium",
        config_override: Optional[Dict[str, Any]] = None,
    ) -> "VideoEditConfig":
        """从预设 strength 或自定义 config 生成配置对象。"""
        presets = {
            "conservative": cls(
                filler_level="minimal",
                stutter_level=0,
                pause_threshold=2.0,
                edge_level="off",
                llm_mode="auxiliary",
            ),
            "medium": cls(
                filler_level="normal",
                stutter_level=2,
                pause_threshold=1.5,
                edge_level="off",
                llm_mode="auxiliary",
            ),
            "aggressive": cls(
                filler_level="aggressive",
                stutter_level=2,
                pause_threshold=1.0,
                edge_level="normal",
                llm_mode="primary",
            ),
        }
        cfg = presets.get(strength, presets["medium"])
        if config_override:
            for k, v in config_override.items():
                if hasattr(cfg, k) and v is not None:
                    setattr(cfg, k, v)
        return cfg


# =============================================================================
# Filler 词库（分层）
# =============================================================================

# 语气词：最核心的纯填充音
CORE_FILLER_WORDS: Set[str] = {"嗯", "啊", "呃", "哦", "哎", "唉", "欸", "嗯嗯", "啊啊", "呃呃"}

# 扩展 filler 词：单独成句时无信息量
EXTENDED_FILLER_PHRASES: Set[str] = {
    "那个", "就是", "然后", "其实", "反正", "是的", "对的",
    "好吧", "算了", "就是说", "反正就是", "那个那个",
    "好吧好吧", "等等等等", "对对对",
    "好吧", "哈", "哈喽", "嗨", "喂",
    "这个", "那个", "的话", "的话", "然后呢",
}

# 句末语气词（单独成句时倾向删）
SENTENCE_END_FILLERS: Set[str] = {
    "的吧", "呀", "嘛", "咧", "哦", "哈", "呢",
}

# 合并全量 filler（用于词级判断）
ALL_FILLER_WORDS: Set[str] = CORE_FILLER_WORDS | EXTENDED_FILLER_PHRASES | SENTENCE_END_FILLERS

# 无效开头词：视频开头出现这些词 + 后面有长停顿 → 倾向删
EDGE_OPENING_WORDS: Set[str] = {
    "好", "那", "嗯好", "各位", "大家好", "hello", "hi",
    "今天", "我们", "各位好", "朋友们",
}

# 无效结尾词：视频结尾出现这些短词 + 前后有停顿 → 倾向删
EDGE_CLOSING_WORDS: Set[str] = {
    "好", "谢谢", "感谢", "拜拜", "再见", "各位", "好的",
}

# aggressive 模式额外删减的填充词（在句中单独出现时视为 filler）
AGGRESSIVE_EXTRA_WORDS: Set[str] = {
    "基本上", "可能", "应该", "大概", "感觉",
    "说实话", "老实说", "事实上",
    "你懂的", "大家都知道", "不用说了",
    "好吧", "行吧", "那行", "行",
}

# =============================================================================
# LLM 批处理参数
# =============================================================================

LLM_BATCH_SIZE = 25
LLM_CONTEXT_TAIL = 2

# =============================================================================
# FFmpeg 参数
# =============================================================================

SEGMENT_MERGE_GAP = 0.5       # 相邻保留段合并阈值（秒）
SRT_MAX_DURATION = 6.0        # SRT 单条字幕最大时长（秒）
SRT_MAX_CHARS = 80             # SRT 单条字幕最大字符数


# =============================================================================
# 服务主体
# =============================================================================

class VideoEditService:
    """视频剪辑服务"""

    def __init__(
        self,
        upload_dir: str,
        db_session: Session,
        transcribe_engine: Optional[TranscribeEngineManager] = None,
        subtitle_format: str = "srt",
        config: Optional[VideoEditConfig] = None,
    ):
        self.upload_dir = upload_dir
        self.db = db_session
        self.subtitle_format = subtitle_format
        self.transcribe_engine = transcribe_engine
        self.media_processor = MediaProcessor(upload_dir, transcribe_engine)
        self.repo = VideoEditRepository(db_session)
        self.config = config or VideoEditConfig()

    # ==================== 入口 ====================

    async def upload_and_process(
        self,
        file_content: bytes,
        filename: str,
        user_id: int,
        edit_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """上传视频，异步处理。edit_config 可选 strength 或完整 config dict。"""
        task_id = str(uuid.uuid4())

        # 解析配置
        cfg = VideoEditConfig.from_params(
            strength=edit_config.get("strength") if isinstance(edit_config, dict) else "medium",
            config_override=edit_config if isinstance(edit_config, dict) else None,
        )

        self.repo.create_task(
            task_id=task_id,
            source_video_path="",
            user_id=user_id,
            source_video_name=filename,
            edit_config=edit_config,
        )

        file_path = self.media_processor.save_uploaded_file(file_content, filename)
        from backend.models.database.tables import VideoEditTaskTable
        task = self.db.query(VideoEditTaskTable).filter(
            VideoEditTaskTable.task_id == task_id
        ).first()
        if task:
            task.source_video_path = file_path
            self.db.commit()

        asyncio.create_task(
            self._process_video_edit_bg(task_id, file_path, user_id, cfg)
        )
        return {"task_id": task_id, "status": "processing"}

    async def _process_video_edit_bg(
        self, task_id: str, video_path: str, user_id: int, cfg: VideoEditConfig
    ):
        db = SessionLocal()
        try:
            repo = VideoEditRepository(db)
            repo.update_status(task_id, "processing")
            try:
                await self._do_edit_pipeline(task_id, video_path, repo, user_id, cfg)
                logger.info(f"视频剪辑任务完成: {task_id}")
            except Exception as e:
                logger.error(f"视频剪辑任务失败 {task_id}: {e}", exc_info=True)
                repo.update_status(task_id, "failed", error=str(e)[:1000])
        finally:
            db.close()

    async def _do_edit_pipeline(
        self,
        task_id: str,
        video_path: str,
        repo: VideoEditRepository,
        user_id: int,
        cfg: VideoEditConfig,
    ) -> Dict[str, Any]:
        """剪辑主流程（三层删减）"""
        self.config = cfg  # 运行时使用配置

        # 1. 提取音频
        audio_path = self.media_processor.extract_audio_from_video(video_path)

        # 2. Whisper 转写
        transcribe_result = self._transcribe_with_words(audio_path)
        transcript = transcribe_result.get("transcript", "")
        word_timestamps = transcribe_result.get("word_timestamps") or []

        if not word_timestamps:
            raise RuntimeError("转写未返回逐字时间戳，无法继续剪辑")

        original_duration = float(word_timestamps[-1][2])

        repo.update_status(
            task_id,
            "processing",
            transcript=transcript,
            word_timestamps=word_timestamps,
            original_duration=original_duration,
        )

        # =================================================================
        # 第0层：音频级死沉默检测（Whisper 未转写的空白区域）
        # =================================================================
        dead_silence_removed: List[Dict[str, Any]] = []
        if cfg.pause_threshold > 0:
            dead_silence_removed = self._detect_dead_silence(word_timestamps, original_duration, cfg)
            logger.info(f"检测到 {len(dead_silence_removed)} 段死沉默: {[(r['start'], r['end']) for r in dead_silence_removed]}")

        # =================================================================
        # 第1层：句子级删除
        # =================================================================
        sentences = self._split_sentences(word_timestamps)
        if not sentences:
            raise RuntimeError("未能从转写结果中切出任何句子")

        delete_ids, llm_reasoning = await self._sentence_level_detection(sentences, cfg)

        kept_segments, removed_segments = self._convert_to_segments(sentences, delete_ids)

        if not kept_segments:
            raise RuntimeError("所有内容都被删除，没有可保留的片段")

        # =================================================================
        # 第2层：停顿修剪
        # =================================================================
        if cfg.pause_threshold > 0:
            kept_segments, pause_removed = self._trim_silences(kept_segments)
            removed_segments.extend(pause_removed)
            removed_segments.extend(dead_silence_removed)
            # 从 kept_segments 中精确剔除死沉默时间区域
            kept_segments = self._subtract_removed_from_kept(kept_segments, dead_silence_removed)

        # =================================================================
        # 第3层：词级精细删除
        # =================================================================
        if cfg.filler_level != "off" or cfg.stutter_level > 0 or cfg.llm_mode != "off":
            kept_segments, word_removed = await self._word_level_detection(
                kept_segments, word_timestamps, cfg
            )
            removed_segments.extend(word_removed)

        if not kept_segments:
            raise RuntimeError("词级别精细删减后没有可保留片段")

        # =================================================================
        # 段间留间隙（可选）
        # =================================================================
        if cfg.segment_gap > 0:
            kept_segments = self._apply_segment_gap(kept_segments)

        # =================================================================
        # FFmpeg 剪切拼接
        # =================================================================
        output_filename = f"edited_{task_id}.mp4"
        output_video_path = os.path.join(self.upload_dir, output_filename)
        cut_ok = await asyncio.to_thread(
            self._ffmpeg_cut_concat, video_path, kept_segments, output_video_path
        )
        if not cut_ok:
            raise RuntimeError("FFmpeg 剪切拼接失败")

        # =================================================================
        # 360p 预览生成（v3 改造：避免用户白下载不满意的视频）
        # =================================================================
        preview_dir = os.path.join(self.upload_dir, "preview")
        os.makedirs(preview_dir, exist_ok=True)
        preview_filename = f"preview_{task_id}.mp4"
        preview_video_path = os.path.join(preview_dir, preview_filename)
        preview_ok = await asyncio.to_thread(
            self._ffmpeg_make_preview, output_video_path, preview_video_path
        )
        preview_size = None
        if preview_ok:
            try:
                preview_size = os.path.getsize(preview_video_path)
            except OSError:
                pass
        else:
            logger.warning(f"Preview 生成失败: {task_id}，主任务仍 completed")
            preview_video_path = None

        # =================================================================
        # 字幕生成
        # =================================================================
        subtitle_filename = f"subtitle_{task_id}.{self.subtitle_format}"
        subtitle_path = os.path.join(self.upload_dir, subtitle_filename)
        srt_ok = await asyncio.to_thread(
            self._generate_subtitle,
            word_timestamps, kept_segments, subtitle_path, self.subtitle_format
        )
        if not srt_ok:
            logger.warning(f"字幕生成失败: {task_id}")

        final_duration = sum(end - start for start, end in kept_segments)

        repo.update_status(
            task_id,
            "completed",
            kept_segments=[[s, e] for s, e in kept_segments],
            removed_segments=removed_segments,
            llm_reasoning=llm_reasoning,
            output_video_path=output_video_path,
            preview_video_path=preview_video_path,
            preview_size_bytes=preview_size,
            subtitle_path=subtitle_path if srt_ok else None,
            subtitle_format=self.subtitle_format if srt_ok else None,
            final_duration=final_duration,
        )
        return {"status": "completed"}

    # ==================== 第1层：句子级 ====================

    async def _sentence_level_detection(
        self, sentences: List[Dict[str, Any]], cfg: VideoEditConfig
    ) -> Tuple[List[int], List[Dict[str, Any]]]:
        """
        句子级删除检测：规则识别 + LLM 辅助判断。
        返回：(delete_ids, llm_reasoning)
        """
        delete_ids: List[int] = []
        reasoning: List[Dict[str, Any]] = []

        # ---- 规则层：filler 句、口吃、无效开头/结尾 ----
        for s in sentences:
            reason = self._sentence_filler_reason(s, cfg)
            if reason:
                delete_ids.append(s["id"])
                reasoning.append({
                    "batch_start_id": s["id"],
                    "batch_end_id": s["id"],
                    "delete_ids": [s["id"]],
                    "reasons": {str(s["id"]): reason},
                    "source": "rule",
                })

        # ---- LLM 辅助判断 ----
        if cfg.llm_mode != "off":
            remaining = [s for s in sentences if s["id"] not in delete_ids]
            llm_ids, llm_r = await self._llm_detect_invalid_sentences(remaining, cfg)
            delete_ids.extend(llm_ids)
            reasoning.extend(llm_r)

        return sorted(set(delete_ids)), reasoning

    def _sentence_filler_reason(self, s: Dict[str, Any], cfg: VideoEditConfig) -> Optional[str]:
        """判断句子是否为 filler，是则返回原因。"""
        text = s["text"].strip().rstrip("。！？.!?;；,，")
        if not text:
            return None

        duration = s["end"] - s["start"]
        char_count = len(text)

        # ---- 语气词水平判断 ----
        if cfg.filler_level == "minimal":
            # 只删纯语气词（核心集）
            if text in CORE_FILLER_WORDS:
                return f"语气词（{text}）"
        elif cfg.filler_level in ("normal", "aggressive"):
            # 核心 + 扩展 filler
            if text in ALL_FILLER_WORDS:
                return f"语气词/填充词（{text}）"
            # aggressive 额外：句中短 filler 单独成句时也删
            if cfg.filler_level == "aggressive" and text in AGGRESSIVE_EXTRA_WORDS:
                return f"填充词（{text}）"

        # ---- 口吃重复判断 ----
        if cfg.stutter_level > 0:
            # 连续重复检测
            if char_count >= 2 and len(set(text)) == 1:
                return f"口吃重复（{text}）"
            # 两字词重复：检测 "那个那个" 模式
            if char_count >= 4:
                half = char_count // 2
                if text[:half] == text[half:] and len(set(text[:half])) <= 2:
                    return f"口吃重复（{text}）"

        # ---- 无效开头判断 ----
        if cfg.edge_level != "off":
            if self._is_invalid_opening(s):
                if cfg.edge_level == "normal" or (cfg.edge_level == "conservative" and duration < 1.0):
                    return f"无效开头（{text}）"

        # ---- 无效结尾判断 ----
        if cfg.edge_level == "normal":
            if self._is_invalid_closing(s):
                return f"无效结尾（{text}）"

        return None

    def _is_invalid_opening(self, s: Dict[str, Any]) -> bool:
        """判断是否为无效开头句：开头位置 + 短句 + 以 filler 词开头"""
        if s["start"] > 5.0:
            return False  # 不在开头
        text = s["text"].strip().rstrip("。！？.!?;；,，")
        if len(text) > 8:
            return False  # 太长，一般不是开场语气
        # 以 filler 词开头
        if text[:2] in CORE_FILLER_WORDS or text[:2] in {"那个", "就是", "然后"}:
            return True
        # 以边缘词开头
        if text in EDGE_OPENING_WORDS or any(text.startswith(w) for w in {"好", "那", "嗯", "哈"}):
            if len(text) < 5:
                return True
        return False

    def _is_invalid_closing(self, s: Dict[str, Any]) -> bool:
        """判断是否为无效结尾句：结尾位置 + 短句 + filler"""
        text = s["text"].strip().rstrip("。！？.!?;；,，")
        if len(text) > 10:
            return False
        # 以谢谢/拜拜/再见/好的 结尾
        if text in {"好", "谢谢", "感谢", "拜拜", "再见", "各位", "好的", "okay", "ok"}:
            return True
        return False

    # ==================== 第0层：音频级死沉默检测 ====================

    def _detect_dead_silence(
        self,
        word_timestamps: List[List[Any]],
        original_duration: float,
        cfg: VideoEditConfig,
    ) -> List[Dict[str, Any]]:
        """
        检测 Whisper 未转写的空白区域（死沉默）。
        思路：word_timestamps 覆盖的时间轴如果有 gap >= pause_threshold，
        说明这段时间 Whisper 没识别出任何词（静音或噪音），应该删除。
        """
        removed: List[Dict[str, Any]] = []
        if not word_timestamps:
            return removed

        # 构建已覆盖时间区间（合并相邻/重叠的词）
        covered: List[Tuple[float, float]] = []
        for w in word_timestamps:
            w_start, w_end = float(w[1]), float(w[2])
            if covered and w_start <= covered[-1][1] + 0.1:
                # 重叠或极近，合并
                covered[-1] = (covered[-1][0], max(covered[-1][1], w_end))
            else:
                covered.append((w_start, w_end))

        threshold = cfg.pause_threshold
        if threshold <= 0:
            return removed

        # 检查首部沉默
        first_start = covered[0][0] if covered else 0
        if first_start >= threshold:
            removed.append({
                "start": 0.0,
                "end": first_start,
                "text": "（沉默）",
                "reason": f"首部死沉默 {first_start:.1f}s",
            })

        # 检查词之间的大间隙
        for i in range(len(covered) - 1):
            gap_start = covered[i][1]
            gap_end = covered[i + 1][0]
            gap = gap_end - gap_start
            if gap >= threshold:
                removed.append({
                    "start": gap_start,
                    "end": gap_end,
                    "text": "（沉默）",
                    "reason": f"死沉默 {gap:.1f}s",
                })

        # 检查尾部沉默
        last_end = covered[-1][1] if covered else original_duration
        tail_silence = original_duration - last_end
        if tail_silence >= threshold:
            removed.append({
                "start": last_end,
                "end": original_duration,
                "text": "（沉默）",
                "reason": f"尾部死沉默 {tail_silence:.1f}s",
            })

        return removed

    def _subtract_removed_from_kept(
        self,
        kept_segments: List[Tuple[float, float]],
        removed_list: List[Dict[str, Any]],
    ) -> List[Tuple[float, float]]:
        """
        从 kept_segments 中精确剔除 removed 时间区域。
        用于死沉默检测后：从句子级结果中挖掉 Whisper 未转写的空白区域。
        """
        if not removed_list:
            return kept_segments

        # 将 removed 转为区间
        removed_ranges = sorted([(r["start"], r["end"]) for r in removed_list], key=lambda x: x[0])
        result: List[Tuple[float, float]] = []

        for seg_start, seg_end in kept_segments:
            # 从当前段中剔除所有与之重叠的 removed 区间
            remaining_start = seg_start
            for r_start, r_end in removed_ranges:
                if r_end <= remaining_start:
                    # removed 在当前段左侧，不影响
                    continue
                if r_start >= seg_end:
                    # removed 在当前段右侧，停止处理此 removed
                    break
                # removed 与当前段有重叠
                if r_start > remaining_start:
                    # 保留左侧部分
                    result.append((remaining_start, r_start))
                # 从 remaining_start 开始裁掉 removed 区域
                remaining_start = max(remaining_start, r_end)
            # 处理剩余的右侧部分
            if remaining_start < seg_end:
                result.append((remaining_start, seg_end))

        return result

    # ==================== 第2层：停顿修剪 ====================

    def _trim_silences(
        self, kept_segments: List[Tuple[float, float]]
    ) -> Tuple[List[Tuple[float, float]], List[Dict[str, Any]]]:
        """修剪保留段之间的死停顿，压缩到 0.3s"""
        SILENCE_KEEP = 0.3
        threshold = self.config.pause_threshold

        if len(kept_segments) < 2 or threshold <= 0:
            return kept_segments, []

        trimmed: List[Tuple[float, float]] = [kept_segments[0]]
        removed: List[Dict[str, Any]] = []

        for i in range(1, len(kept_segments)):
            prev_start, prev_end = trimmed[-1]
            cur_start, cur_end = kept_segments[i]
            gap = cur_start - prev_end

            if gap > threshold:
                new_start = prev_end + SILENCE_KEEP
                removed.append({
                    "start": new_start,
                    "end": cur_start,
                    "text": "(死停顿)",
                    "reason": f"修剪 {gap:.1f}s 死停顿（>{threshold}s）",
                })
                trimmed.append((new_start, cur_end))
            else:
                trimmed.append((cur_start, cur_end))

        return trimmed, removed

    def _apply_segment_gap(
        self, kept_segments: List[Tuple[float, float]]
    ) -> List[Tuple[float, float]]:
        """在相邻保留段之间留出间隙（向后延伸前段 + 向前偏移后段）"""
        gap = self.config.segment_gap
        if len(kept_segments) < 2 or gap <= 0:
            return kept_segments

        result = [kept_segments[0]]
        for i in range(1, len(kept_segments)):
            prev_s, prev_e = result[-1]
            cur_s, cur_e = kept_segments[i]
            # 前段末尾延 gap，后段起始推 gap
            new_prev_e = prev_e + gap
            new_cur_s = cur_s - gap
            if new_cur_s > new_prev_e:  # 确保不重叠
                result[-1] = (prev_s, new_prev_e)
                result.append((new_cur_s, cur_e))
            else:
                result.append((cur_s, cur_e))
        return result

    # ==================== 第3层：词级精细 ====================

    async def _word_level_detection(
        self,
        kept_segments: List[Tuple[float, float]],
        word_timestamps: List[List[Any]],
        cfg: VideoEditConfig,
    ) -> Tuple[List[Tuple[float, float]], List[Dict[str, Any]]]:
        """词级精细删除检测"""
        if not kept_segments or not word_timestamps:
            return kept_segments, []

        all_removed: List[Dict[str, Any]] = []

        for seg_start, seg_end in kept_segments:
            seg_words = [
                (i, w) for i, w in enumerate(word_timestamps)
                if float(w[1]) >= seg_start and float(w[2]) <= seg_end
            ]
            if not seg_words:
                continue

            seg_duration = seg_end - seg_start
            if seg_duration < 0.5 or len(seg_words) < 3:
                continue

            # 规则层：词级别 filler + 口吃
            rule_removed = self._word_filler_rule(seg_words)
            all_removed.extend(rule_removed)

            # LLM 层（auxiliary / primary）
            if cfg.llm_mode in ("auxiliary", "primary"):
                try:
                    llm_removed = await self._llm_identify_word_fillers(seg_words)
                    all_removed.extend(llm_removed)
                except Exception as e:
                    logger.warning(f"词级 LLM 判断失败: {e}")

        if not all_removed:
            return kept_segments, []

        # 合并相邻被删词（间隔 < 0.2s 视为连续）
        all_removed.sort(key=lambda x: x["start"])
        merged: List[Dict[str, Any]] = []
        for r in all_removed:
            if merged and r["start"] - merged[-1]["end"] < 0.2:
                merged[-1]["end"] = r["end"]
                merged[-1]["text"] += r["text"]
            else:
                merged.append({**r})

        # 计算新的保留段
        new_kept = self._split_kept_by_removed(kept_segments, merged)
        return new_kept, merged

    def _word_filler_rule(
        self, seg_words: List[Tuple[int, List[Any]]]
    ) -> List[Dict[str, Any]]:
        """词级规则 filler 检测"""
        removed: List[Dict[str, Any]] = []
        cfg = self.config
        prev_word: Optional[str] = None
        repeat_count = 0

        for i, (global_idx, w) in enumerate(seg_words):
            word = w[0]
            w_start, w_end = float(w[1]), float(w[2])

            # 口吃重复
            if cfg.stutter_level > 0:
                if word == prev_word and len(word) <= 3:
                    repeat_count += 1
                    if repeat_count >= cfg.stutter_level:
                        removed.append({
                            "start": w_start,
                            "end": w_end,
                            "text": word,
                            "reason": "口吃重复",
                        })
                else:
                    repeat_count = 1

            # Filler 词
            if cfg.filler_level == "minimal":
                if word in CORE_FILLER_WORDS:
                    removed.append({
                        "start": w_start,
                        "end": w_end,
                        "text": word,
                        "reason": f"语气词（{word}）",
                    })
            elif cfg.filler_level == "normal":
                if word in ALL_FILLER_WORDS:
                    removed.append({
                        "start": w_start,
                        "end": w_end,
                        "text": word,
                        "reason": f"填充词（{word}）",
                    })
            elif cfg.filler_level == "aggressive":
                # aggressive：ALL_FILLER_WORDS + AGGRESSIVE_EXTRA_WORDS
                # 额外逻辑：短词（1-2字）夹在两个长词之间 → 视为 filler 停顿
                if word in ALL_FILLER_WORDS or word in AGGRESSIVE_EXTRA_WORDS:
                    removed.append({
                        "start": w_start,
                        "end": w_end,
                        "text": word,
                        "reason": f"填充词（{word}）",
                    })
                # 检测句中短 filler：在两个较长的实词之间
                if len(word) <= 2 and len(word) > 0:
                    prev_w = seg_words[i - 1][1][0] if i > 0 else ""
                    next_w = seg_words[i + 1][1][0] if i < len(seg_words) - 1 else ""
                    if (len(prev_w) > 2 and len(next_w) > 2 and
                            word in {"嗯", "啊", "呃", "哦", "哎", "唉", "欸", "这个", "那个", "然后", "就是"}):
                        removed.append({
                            "start": w_start,
                            "end": w_end,
                            "text": word,
                            "reason": f"句中填充（{word}）",
                        })

            prev_word = word

        return removed

    async def _llm_identify_word_fillers(
        self, seg_words: List[Tuple[int, List[Any]]]
    ) -> List[Dict[str, Any]]:
        """让 LLM 识别一段词中的 filler 词"""
        word_list = [
            {
                "idx": global_idx,
                "word": w[0],
                "start": round(float(w[1]), 2),
                "end": round(float(w[2]), 2),
            }
            for global_idx, w in seg_words
        ]

        prompt = f"""你是口播视频剪辑专家。以下是一段连续口播词的列表（按时间顺序）。

你的任务是找出其中应该删除的词。删除标准：
- 语气词：嗯、啊、呃、哦、哎、唉、欸、哈、嗨
- 口头禅/无意义填充：那个、就是、然后（单独作停顿使用时）、其实、反正
- 口吃重复：连续出现 2 次以上的相同单字

注意：
- 有实际意义的词不要删（如"然后"在句中作连词、"那个"在句中作代词）
- 只删真正无意义的填充词，不要过度删除
- 如果整段都很自然流畅，返回空列表

词列表：
{json.dumps(word_list, ensure_ascii=False, indent=2)}

请直接返回 JSON（不要 markdown 代码块），格式：
{{"remove_indices": [3, 7, 12]}}
（返回需要删除的词的 idx 列表）
"""
        raw = await ai_manager.generate(prompt, max_tokens=500)
        result = self._parse_llm_json(raw)
        indices = result.get("remove_indices", [])
        valid_global_indices = {idx for idx, _ in seg_words}
        to_remove = [int(x) for x in indices if int(x) in valid_global_indices]

        idx_map = {global_idx: wd for global_idx, wd in seg_words}
        removed: List[Dict[str, Any]] = []
        for global_idx in to_remove:
            if global_idx not in idx_map:
                continue
            w = idx_map[global_idx]
            removed.append({
                "start": round(float(w[1]), 3),
                "end": round(float(w[2]), 3),
                "text": w[0],
                "reason": "LLM 识别为 filler",
            })
        return removed

    def _split_kept_by_removed(
        self,
        kept_segments: List[Tuple[float, float]],
        removed_word_segments: List[Dict[str, Any]],
    ) -> List[Tuple[float, float]]:
        """根据被删词的时间段，重新切保留段"""
        if not removed_word_segments:
            return kept_segments

        removed_ranges = [(r["start"], r["end"]) for r in removed_word_segments]
        removed_ranges.sort()

        new_kept: List[Tuple[float, float]] = []
        for seg_start, seg_end in kept_segments:
            cursor = seg_start
            for r_start, r_end in removed_ranges:
                if r_end <= seg_start or r_start >= seg_end:
                    continue
                if r_start > cursor:
                    new_kept.append((cursor, r_start))
                cursor = max(cursor, r_end)
            if cursor < seg_end:
                new_kept.append((cursor, seg_end))

        return [(s, e) for s, e in new_kept if e - s >= 0.1]

    # ==================== LLM 句子级判断 ====================

    async def _llm_detect_invalid_sentences(
        self, sentences: List[Dict[str, Any]], cfg: VideoEditConfig
    ) -> Tuple[List[int], List[Dict[str, Any]]]:
        """分批调用 LLM 判断句子删除"""
        all_delete_ids: List[int] = []
        reasoning: List[Dict[str, Any]] = []

        i = 0
        while i < len(sentences):
            batch = sentences[i: i + LLM_BATCH_SIZE]
            context = sentences[max(0, i - LLM_CONTEXT_TAIL): i]
            try:
                delete_ids, batch_reason = await self._llm_judge_batch(batch, context, cfg)
                all_delete_ids.extend(delete_ids)
                reasoning.append({
                    "batch_start_id": batch[0]["id"],
                    "batch_end_id": batch[-1]["id"],
                    "delete_ids": delete_ids,
                    "reasons": batch_reason,
                    "source": "llm",
                })
            except Exception as e:
                logger.error(f"LLM 判断失败: {e}")
                reasoning.append({
                    "batch_start_id": batch[0]["id"],
                    "batch_end_id": batch[-1]["id"],
                    "error": str(e)[:200],
                    "delete_ids": [],
                })
            i += LLM_BATCH_SIZE

        return sorted(set(all_delete_ids)), reasoning

    async def _llm_judge_batch(
        self,
        batch: List[Dict[str, Any]],
        context: List[Dict[str, Any]],
        cfg: VideoEditConfig,
    ) -> Tuple[List[int], Dict[int, str]]:
        """让 LLM 判断一批句子"""
        sentences_payload = [
            {
                "id": s["id"],
                "text": s["text"],
                "start": round(s["start"], 2),
                "end": round(s["end"], 2),
                "duration": round(s["end"] - s["start"], 2),
                "char_count": len(s["text"]),
            }
            for s in batch
        ]
        context_payload = [{"id": s["id"], "text": s["text"]} for s in context]

        # aggressive 模式：prompt 更激进，temperature 更高
        is_aggressive = cfg.llm_mode == "primary"
        tone = "**严格删除**" if is_aggressive else "**建议删除**"

        prompt = f"""你是口播视频剪辑专家。以下是视频转写后按停顿切出的短句列表（每条带 ID、时间戳、字数）。

请判断哪些句子应该删除（耗时且无信息量）。

{tone}的情况：
- 只有 1-3 个字、单独成句的（如 "嗯。"、"啊。"、"那个。"、"就是。"、"好吧。"）
- 明显卡壳/重复（如 "那个那个"、"对对对"、"我我"）
- 长停顿后的开场词（如长停顿后单独一个 "好"、"那"）
- 思考犹豫词（如 "怎么说呢"、"你知道吧"、"说实话"）

**不要删除**的情况：
- 包含实质内容词（动词、名词、形容词）的句子
- 衔接词单独出现（"然后"、"所以"、"因为"用作逻辑连接）
- 上下文衔接片段

**判断策略**：
- aggressive 模式：宁可误删，不可漏删。1-5 字且语义单薄 → 倾向删除；含实质内容 → 永远保留
- normal 模式：1-3 字且语义独立 → 倾向删除；含实质内容 → 永远保留

{('【上下文片段（不要删）】' + chr(10) + json.dumps(context_payload, ensure_ascii=False, indent=2)) if context_payload else ''}

【待判断句子】
{json.dumps(sentences_payload, ensure_ascii=False, indent=2)}

请直接返回 JSON：
{{
  "delete_ids": [3, 7, 12],
  "reasons": {{"3": "语气词", "7": "卡壳重复"}}
}}
"""
        # aggressive 模式用更高 temperature，让模型更"大胆"
        temperature = 0.7 if is_aggressive else 0.3
        raw = await ai_manager.generate(prompt, max_tokens=2000, temperature=temperature)
        result = self._parse_llm_json(raw)
        delete_ids = result.get("delete_ids", [])
        valid_ids = {s["id"] for s in batch}
        delete_ids = [int(x) for x in delete_ids if int(x) in valid_ids]
        reasons = {int(k): str(v) for k, v in result.get("reasons", {}).items()}
        return delete_ids, reasons

    def _parse_llm_json(self, raw: str) -> Dict[str, Any]:
        """从 LLM 输出提取 JSON"""
        text = raw.strip()
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            text = m.group(1)
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            text = m.group(0)
        try:
            return json.loads(text)
        except Exception as e:
            logger.warning(f"LLM JSON 解析失败: {e}")
            return {"delete_ids": [], "reasons": {}}

    # ==================== 切句 ====================

    def _split_sentences(
        self, word_timestamps: List[List[Any]]
    ) -> List[Dict[str, Any]]:
        """
        按标点 + 停顿 + 单句字数限制切句。
        触发切句的条件（满足任一）：
        1. 标点（。！？.!?;；,，）
        2. 停顿 > sentence_silence_gap
        3. 当前句字数 > sentence_max_chars
        """
        SENTENCE_PUNCT = set("。！？.!?;；,，")
        sentences = []
        current_words: List[List[Any]] = []
        sentence_id = 1
        last_word_end: Optional[float] = None

        def flush():
            nonlocal sentence_id, current_words
            if current_words:
                sentences.append(self._build_sentence(sentence_id, current_words))
                sentence_id += 1
                current_words = []

        for entry in word_timestamps:
            word, start, end = entry[0], float(entry[1]), float(entry[2])
            has_punct = any(p in word for p in SENTENCE_PUNCT) or word in ["\n", "\r\n"]
            long_silence = (
                last_word_end is not None
                and (start - last_word_end) > self.config.sentence_silence_gap
            )
            current_text_len = sum(len(w[0]) for w in current_words) + len(word)
            too_long = current_text_len > self.config.sentence_max_chars

            if has_punct:
                current_words.append(entry)
                flush()
                last_word_end = end
                continue
            elif current_words and (long_silence or too_long):
                flush()

            current_words.append(entry)
            last_word_end = end

        if current_words:
            flush()

        return sentences

    def _build_sentence(
        self, sentence_id: int, words: List[List[Any]]
    ) -> Dict[str, Any]:
        text = "".join(w[0] for w in words).strip()
        return {
            "id": sentence_id,
            "text": text,
            "start": float(words[0][1]),
            "end": float(words[-1][2]),
            "words": words,
        }

    # ==================== 片段转换 ====================

    def _convert_to_segments(
        self,
        sentences: List[Dict[str, Any]],
        delete_ids: List[int],
    ) -> Tuple[List[Tuple[float, float]], List[Dict[str, Any]]]:
        """
        把句子级删除结果转成 kept/removed 片段。
        相邻同状态（kept/removed）段合并，跨 0.2s 以上停顿时断开。
        """
        if not sentences:
            return [], []

        delete_set = set(delete_ids)

        # 构建 (start, end, state) 段
        segments: List[Tuple[float, float, str]] = []
        for s in sentences:
            state = "removed" if s["id"] in delete_set else "kept"
            if segments and segments[-1][2] == state:
                _, prev_end, _ = segments[-1]
                if s["start"] - prev_end < 0.2:  # 时间连续才合并
                    segments[-1] = (segments[-1][0], s["end"], state)
                    continue
            segments.append((s["start"], s["end"], state))

        kept: List[Tuple[float, float]] = []
        removed_ranges: List[Tuple[float, float]] = []
        for s, e, st in segments:
            if st == "kept":
                kept.append((s, e))
            else:
                removed_ranges.append((s, e))

        # 合并 removed 相邻段
        removed_segments: List[Dict[str, Any]] = []
        for s, e in removed_ranges:
            if removed_segments and (s - removed_segments[-1]["end"]) <= SEGMENT_MERGE_GAP:
                removed_segments[-1]["end"] = e
            else:
                removed_segments.append({
                    "start": s, "end": e, "text": "",
                    "reason": "句子级删除",
                })

        kept = [(s, e) for s, e in kept if e - s >= 0.1]
        return kept, removed_segments

    # ==================== FFmpeg ====================

    def _ffmpeg_make_preview(
        self,
        input_video: str,
        output_video: str,
        timeout: int = 180,
    ) -> bool:
        """生成 360p 低码率预览视频（v3 改造）

        规格：min(640, iw) 等比缩放（横屏 640x360 / 竖屏 360x640）
        CRF 28 + b:v 600kbps + aac 64k + faststart（边下边播关键）
        10min 视频 ≈ 50MB，可在浏览器秒开 + seek
        """
        cmd = [
            "ffmpeg", "-y",
            "-i", input_video,
            "-vf", "scale='min(640,iw)':'-2',scale='trunc(iw/2)*2':'trunc(ih/2)*2'",
            "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "28",
            "-b:v", "600k",
            "-maxrate", "800k",
            "-bufsize", "1200k",
            "-c:a", "aac", "-b:a", "64k",
            "-movflags", "+faststart",
            output_video,
        ]
        try:
            result = subprocess.run(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=timeout
            )
            if result.returncode != 0:
                err = result.stderr.decode(errors='ignore')[:500]
                logger.error(f"Preview FFmpeg 失败: {err}")
                return False
            return True
        except subprocess.TimeoutExpired:
            logger.error(f"Preview FFmpeg 超时: {input_video}")
            return False
        except Exception as e:
            logger.error(f"Preview FFmpeg 异常: {e}", exc_info=True)
            return False

    def _ffmpeg_cut_concat(
        self,
        input_video: str,
        kept_segments: List[Tuple[float, float]],
        output_video: str,
    ) -> bool:
        """FFmpeg 逐段剪切 + concat 拼接"""
        if not kept_segments:
            return False
        temp_dir = os.path.join(self.upload_dir, f"temp_{uuid.uuid4().hex[:8]}")
        os.makedirs(temp_dir, exist_ok=True)
        try:
            segment_files = []
            for idx, (start, end) in enumerate(kept_segments):
                seg_path = os.path.join(temp_dir, f"seg_{idx:04d}.mp4")
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", f"{start:.3f}",
                    "-to", f"{end:.3f}",
                    "-i", input_video,
                    "-c:v", "libx264", "-preset", "fast",
                    "-c:a", "aac",
                    "-avoid_negative_ts", "make_zero",
                    seg_path,
                ]
                result = subprocess.run(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=300
                )
                if result.returncode != 0:
                    logger.error(f"FFmpeg 剪切失败 idx={idx}: {result.stderr.decode(errors='ignore')[:300]}")
                    return False
                segment_files.append(seg_path)

            # concat demuxer：list 里写 basename，ffmpeg 自动去同目录找
            list_file = os.path.join(temp_dir, "concat_list.txt")
            with open(list_file, "w", encoding="utf-8") as f:
                for p in segment_files:
                    f.write(f"file '{os.path.basename(p)}'\n")

            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", list_file,
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac",
                output_video,
            ]
            result = subprocess.run(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=600
            )
            if result.returncode != 0:
                full_err = result.stderr.decode(errors='ignore')
                logger.error(f"FFmpeg 拼接失败: {full_err[:500]}")
                return False
            return True
        except Exception as e:
            logger.error(f"FFmpeg 处理异常: {e}", exc_info=True)
            return False
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    # ==================== 字幕 ====================

    def _generate_subtitle(
        self,
        word_timestamps: List[List[Any]],
        kept_segments: List[Tuple[float, float]],
        output_path: str,
        fmt: str = "srt",
    ) -> bool:
        """生成 SRT 字幕"""
        kept_words: List[List[Any]] = []
        for entry in word_timestamps:
            _, start, end = entry[0], float(entry[1]), float(entry[2])
            for seg_s, seg_e in kept_segments:
                if start >= seg_s and end <= seg_e:
                    kept_words.append(entry)
                    break

        if not kept_words:
            return False

        chunks = self._chunk_words_for_subtitle(kept_words)

        def fmt_time(sec: float) -> str:
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = int(sec % 60)
            ms = int((sec % 1) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                for idx, chunk in enumerate(chunks, 1):
                    start = float(chunk[0][1])
                    end = float(chunk[-1][2])
                    text = "".join(w[0] for w in chunk).strip()
                    if not text:
                        continue
                    f.write(f"{idx}\n")
                    f.write(f"{fmt_time(start)} --> {fmt_time(end)}\n")
                    f.write(f"{text}\n\n")
            return True
        except Exception as e:
            logger.error(f"字幕生成失败: {e}")
            return False

    def _chunk_words_for_subtitle(
        self, words: List[List[Any]]
    ) -> List[List[List[Any]]]:
        """按 SRT_MAX_DURATION 和 SRT_MAX_CHARS 切字幕块"""
        chunks: List[List[List[Any]]] = []
        current: List[List[Any]] = []
        current_text = ""
        SENT_PUNCT = set("。！？.!?;；,，")

        for entry in words:
            word = entry[0]
            if not current:
                current.append(entry)
                current_text = word
                continue

            duration = float(entry[2]) - float(current[0][1])
            need_split = (
                duration > SRT_MAX_DURATION
                or len(current_text) >= SRT_MAX_CHARS
                or any(p in word for p in SENT_PUNCT)
            )
            if need_split:
                chunks.append(current)
                current = [entry]
                current_text = word
            else:
                current.append(entry)
                current_text += word

        if current:
            chunks.append(current)
        return chunks

    # ==================== 查询 ====================

    async def get_result(self, task_id: str, user_id: int) -> VideoEditResponse:
        task = self.repo.get_by_task_id(task_id)
        if not task:
            raise ValueError(f"任务 {task_id} 不存在")
        if task.user_id != user_id:
            raise ValueError("无权访问该任务")
        return self._build_response(task)

    # ==================== 转写 ====================

    def _transcribe_with_words(self, audio_path: str) -> Dict[str, Any]:
        """
        使用 Whisper 转写音频，返回带逐字时间戳的结果。
        优先用 transcribe_engine（Whisper），否则用 media_processor 的 mock。
        """
        if self.transcribe_engine and self.transcribe_engine.is_available:
            try:
                return self.transcribe_engine.transcribe(
                    audio_path,
                    word_timestamps=True,
                    model=self.transcribe_engine.model_name,
                    language=self.transcribe_engine.language,
                )
            except Exception as e:
                logger.warning(f"TranscribeEngine 转写失败，降级到 media_processor: {e}")

        # 降级：走 media_processor（MockMediaProcessor）
        return self.media_processor.transcribe_audio(
            audio_path,
            word_timestamps=True,
        )

    def task_exists(self, task_id: str) -> bool:
        return self.repo.task_exists(task_id)

    def get_task_owned_by(self, task_id: str, user_id: int) -> Optional[Any]:
        task = self.repo.get_by_task_id(task_id)
        if task and task.user_id == user_id:
            return task
        return None

    def _build_response(self, task: Any) -> VideoEditResponse:
        kept = None
        if task.kept_segments:
            kept = [VideoEditSegment(start=s, end=e) for s, e in task.kept_segments]
        removed = None
        if task.removed_segments:
            removed = [
                VideoEditSegment(
                    start=seg.get("start", 0),
                    end=seg.get("end", 0),
                    text=seg.get("text"),
                    reason=seg.get("reason"),
                )
                for seg in task.removed_segments
            ]
        return VideoEditResponse(
            task_id=task.task_id,
            status=task.status,
            source_video_name=task.source_video_name,
            transcript=task.transcript if task.status == "completed" else None,
            kept_segments=kept,
            removed_segments=removed,
            output_video_path=task.output_video_path if task.status == "completed" else None,
            preview_video_path=task.preview_video_path if task.status == "completed" else None,
            preview_size_bytes=task.preview_size_bytes if task.status == "completed" else None,
            subtitle_path=task.subtitle_path,
            subtitle_format=task.subtitle_format,
            original_duration=task.original_duration,
            final_duration=task.final_duration,
            error=task.error,
        )
