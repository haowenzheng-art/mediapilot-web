"""
热点话题聚合与去重
"""
import logging
from typing import List, Dict, Any
from difflib import SequenceMatcher
from datetime import datetime

logger = logging.getLogger(__name__)


class HotTopicAggregator:
    """热点话题聚合器"""

    def __init__(self, similarity_threshold: float = 0.6):
        """
        Args:
            similarity_threshold: 文本相似度阈值，超过此值视为重复
        """
        self.similarity_threshold = similarity_threshold

    def aggregate(
        self,
        topics: List[Dict[str, Any]],
        max_count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        聚合多个平台的热点数据并去重

        Args:
            topics: 原始热点列表
            max_count: 最大返回数量

        Returns:
            去重后的热点列表，按热度排序
        """
        if not topics:
            return []

        # 按平台分组
        grouped = self._group_by_platform(topics)

        # 去重
        deduped = self._deduplicate(grouped)

        # 排序
        sorted_topics = sorted(
            deduped,
            key=lambda x: x.get("heat_value", 0),
            reverse=True
        )

        # 限制数量
        return sorted_topics[:max_count]

    def _group_by_platform(
        self,
        topics: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """按平台分组"""
        grouped = {}
        for topic in topics:
            source = topic.get("source", "未知")
            if source not in grouped:
                grouped[source] = []
            grouped[source].append(topic)
        return grouped

    def _deduplicate(
        self,
        grouped: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        去重逻辑：
        1. 同一平台内按热度去重（保留热度最高的）
        2. 跨平台按标题相似度去重
        """
        # 步骤1：同一平台内去重
        for source, source_topics in grouped.items():
            grouped[source] = self._deduplicate_within_platform(source_topics)

        # 步骤2：跨平台去重
        all_topics = []
        used_titles = []

        # 先添加百度新闻（优先）
        if "百度新闻" in grouped:
            for topic in grouped["百度新闻"]:
                all_topics.append(topic)
                used_titles.append(topic["title"])

        # 添加其他平台的热点，检查与已添加的相似度
        for source in ["微博热搜", "知乎热榜", "抖音热榜", "小红书"]:
            if source not in grouped:
                continue

            for topic in grouped[source]:
                title = topic["title"]
                if self._is_duplicate(title, used_titles):
                    continue
                all_topics.append(topic)
                used_titles.append(title)

        return all_topics

    def _deduplicate_within_platform(
        self,
        topics: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """同一平台内去重，按热度排序保留最高的"""
        if not topics:
            return []

        # 按热度排序
        sorted_topics = sorted(
            topics,
            key=lambda x: x.get("heat_value", 0),
            reverse=True
        )

        # 去重
        deduped = []
        used_titles = []

        for topic in sorted_topics:
            title = topic["title"]
            if self._is_duplicate(title, used_titles):
                continue
            deduped.append(topic)
            used_titles.append(title)

        return deduped

    def _is_duplicate(self, title: str, used_titles: List[str]) -> bool:
        """检查标题是否重复"""
        for used in used_titles:
            similarity = SequenceMatcher(None, title, used).ratio()
            if similarity >= self.similarity_threshold:
                return True
        return False

    def calculate_heat_score(
        self,
        topic: Dict[str, Any],
        platform_weights: Dict[str, float] = None
    ) -> float:
        """
        计算综合热度分数

        Args:
            topic: 话题数据
            platform_weights: 平台权重，默认各平台权重相同

        Returns:
            综合热度分数
        """
        if platform_weights is None:
            platform_weights = {
                "百度新闻": 1.2,   # 权重较高，代表全网热度
                "微博热搜": 1.0,
                "知乎热榜": 0.9,
                "抖音热榜": 1.1,
                "小红书": 0.8,
            }

        base_heat = topic.get("heat_value", 0)
        source = topic.get("source", "")
        weight = platform_weights.get(source, 1.0)

        # 趋向加成
        trend = topic.get("trend_direction", "same")
        trend_bonus = 1.0
        if trend == "up":
            trend_bonus = 1.2
        elif trend == "rising":
            trend_bonus = 1.15

        # 新发布加成（24小时内）
        published_at = topic.get("published_at")
        if published_at and isinstance(published_at, datetime):
            hours_ago = (datetime.now() - published_at).total_seconds() / 3600
            if hours_ago < 24:
                trend_bonus *= 1.1

        return base_heat * weight * trend_bonus

    def merge_duplicate_topics(
        self,
        topics: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        合并相似话题的热度

        Args:
            topics: 原始话题列表

        Returns:
            合并后的列表
        """
        # 按热度排序
        sorted_topics = sorted(
            topics,
            key=lambda x: x.get("heat_value", 0),
            reverse=True
        )

        merged = []
        merged_indices = []

        for i, topic in enumerate(sorted_topics):
            if i in merged_indices:
                continue

            # 查找相似话题并合并
            similar = [topic]
            for j, other in enumerate(sorted_topics[i+1:], i+1):
                if j in merged_indices:
                    continue
                similarity = SequenceMatcher(
                    None,
                    topic["title"],
                    other["title"]
                ).ratio()
                if similarity >= self.similarity_threshold:
                    similar.append(other)
                    merged_indices.append(j)

            if len(similar) > 1:
                # 合并热度
                total_heat = sum(t.get("heat_value", 0) for t in similar)
                avg_heat = total_heat / len(similar)

                # 使用第一个话题的数据，但更新热度
                merged_topic = similar[0].copy()
                merged_topic["heat_value"] = avg_heat
                merged_topic["summary"] = f"来自{len(similar)}个平台的聚合热点"
                merged_topics.append(merged_topic)
                merged_indices.append(i)
            else:
                merged.append(topic)

        return merged