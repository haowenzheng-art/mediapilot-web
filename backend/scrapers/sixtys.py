"""
60s 聚合热点 API 适配器

数据源: https://60s-api.viki.moe (vikiboss/60s, Cloudflare Workers)
覆盖平台: 微博 / 知乎 / 抖音 / 今日头条
关键词搜索: API 不支持 keyword 参数，全量拉取后客户端过滤

v3 改造：接入 TTLCache 抗 60s-api 抖动，缓存 30 分钟（settings.TRENDING_CACHE_TTL_SECONDS）
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging

import httpx

from backend.scrapers.base import BaseScraper
from backend.scrapers.cache import trending_cache, make_cache_key
from backend.config.settings import settings

logger = logging.getLogger(__name__)

SIXTYS_BASE_URL = "https://60s-api.viki.moe/v2"
SIXTYS_TIMEOUT = 12  # 单次拉榜的超时


class _SixtysBaseScraper(BaseScraper):
    """60s API 通用基类"""

    endpoint: str = ""           # weibo/zhihu/douyin/toutiao/rednote
    source_name: str = ""        # 中文来源标签，进 aggregator 用
    default_topn: int = 50
    # fallback_when_empty=True：关键词 0 命中时退回 TOP 榜并打"今日热点"
    # 用于抖音/小红书 — 它们没有真实关键词搜索源，否则冷门词永远 0 结果
    # 微博/知乎/头条同样无真实关键词检索，但已有 baidu/toutiao 兜底关键词，
    # 这里保持 False 避免污染搜索结果
    fallback_when_empty: bool = False

    async def _fetch_list(self) -> List[Dict[str, Any]]:
        url = f"{SIXTYS_BASE_URL}/{self.endpoint}"
        try:
            r = await self.client.get(url, timeout=SIXTYS_TIMEOUT)
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise RuntimeError(f"60s {self.endpoint} 请求失败: {e}") from e
        try:
            payload = r.json()
        except ValueError as e:
            raise RuntimeError(f"60s {self.endpoint} 响应不是 JSON") from e
        if payload.get("code") != 200:
            raise RuntimeError(f"60s {self.endpoint} 返回非 200: {payload.get('message')}")
        return payload.get("data") or []

    def _filter_by_keyword(
        self,
        items: List[Dict[str, Any]],
        keyword: str,
    ) -> List[Dict[str, Any]]:
        if not keyword:
            return items
        kw = keyword.lower().strip()
        if not kw:
            return items
        return [it for it in items if kw in (it.get("title") or "").lower()]

    async def search(
        self,
        keyword: str,
        days: int = 7,
    ) -> List[Dict[str, Any]]:
        # 1. 查缓存：命中直接返回，跳过 60s-api 调用
        if settings.TRENDING_CACHE_ENABLED:
            cache_key = make_cache_key(self.endpoint, keyword, days)
            cached = await trending_cache.get(cache_key)
            if cached is not None:
                logger.debug(f"60s {self.endpoint} cache hit [{keyword}@{days}]")
                return cached

        items = await self._fetch_list()
        matched = self._filter_by_keyword(items, keyword)

        result: List[Dict[str, Any]]
        if not matched:
            # 抖音/小红书没有真实关键词搜索源，0 命中时退回 TOP 榜
            # 加 "今日热点" 标签让前端知道这不是关键词命中
            if self.fallback_when_empty and items:
                logger.info(
                    f"60s {self.endpoint} 关键词 [{keyword}] 未命中，"
                    f"fallback 到 TOP {min(len(items), 15)} 热榜"
                )
                fallback = items[:15]
                result = [
                    self._normalize_topic({**self._to_topic(it), "category": "今日热点"})
                    for it in fallback
                ]
            else:
                logger.info(
                    f"60s {self.endpoint} 关键词 [{keyword}] 未命中，返回空（共扫描 {len(items)} 条）"
                )
                result = []
        else:
            result = [self._normalize_topic(self._to_topic(it)) for it in matched]

        # 2. 写缓存：成功结果缓存，0 命中也缓存（避免热门空词反复打 API）
        if settings.TRENDING_CACHE_ENABLED:
            await trending_cache.set(cache_key, result)
            logger.debug(f"60s {self.endpoint} cached [{keyword}@{days}] size={len(result)}")

        return result

    def _to_topic(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """子类重写：把 60s 原始字段映射到统一字段"""
        return {
            "title": item.get("title", ""),
            "summary": item.get("detail") or item.get("title", ""),
            "source": self.source_name,
            "source_url": item.get("link", ""),
            "heat_value": float(item.get("hot_value") or 0),
            "trend_direction": "same",
            "image_url": item.get("cover", ""),
            "category": "",
            "keywords": "",
        }


class SixtysWeiboScraper(_SixtysBaseScraper):
    endpoint = "weibo"
    source_name = "微博热搜"


class SixtysDouyinScraper(_SixtysBaseScraper):
    endpoint = "douyin"
    source_name = "抖音热榜"
    fallback_when_empty = True  # 抖音无真实关键词搜索，0 命中退回 TOP 榜

    def _to_topic(self, item: Dict[str, Any]) -> Dict[str, Any]:
        topic = super()._to_topic(item)
        # 抖音返回 event_time_at（10位秒级时间戳）
        ts = item.get("event_time_at") or item.get("active_time_at")
        if isinstance(ts, (int, float)) and ts > 0:
            try:
                topic["published_at"] = datetime.fromtimestamp(ts)
            except (OSError, ValueError):
                pass
        return topic


class SixtysToutiaoScraper(_SixtysBaseScraper):
    """今日头条 — 用作 baidu 不可用时的全网新闻补充源"""
    endpoint = "toutiao"
    source_name = "今日头条"


class SixtysZhihuScraper(_SixtysBaseScraper):
    endpoint = "zhihu"
    source_name = "知乎热榜"

    def _to_topic(self, item: Dict[str, Any]) -> Dict[str, Any]:
        topic = super()._to_topic(item)
        # 知乎热度是字符串："1173 万热度"，提取数字部分
        hv_desc = item.get("hot_value_desc") or ""
        parsed = self._extract_heat_value(hv_desc)
        if parsed is not None:
            topic["heat_value"] = parsed
        # created_at 是毫秒时间戳
        ts_ms = item.get("created_at")
        if isinstance(ts_ms, (int, float)) and ts_ms > 0:
            try:
                topic["published_at"] = datetime.fromtimestamp(ts_ms / 1000)
            except (OSError, ValueError):
                pass
        # detail 经常是 [图片] 这种占位，回退用 title 当 summary
        detail = (item.get("detail") or "").strip()
        if not detail or detail in ("[图片]", "[视频]"):
            topic["summary"] = item.get("title", "")
        else:
            topic["summary"] = detail
        return topic


class SixtysXiaohongshuScraper(_SixtysBaseScraper):
    """小红书热搜榜 — 60s /v2/rednote 端点，无真实关键词搜索，0 命中退回 TOP 榜"""
    endpoint = "rednote"
    source_name = "小红书"
    fallback_when_empty = True

    def _to_topic(self, item: Dict[str, Any]) -> Dict[str, Any]:
        # rednote 字段：rank/title/score("926.4w")/word_type/link
        score_str = item.get("score") or ""
        heat = self._extract_heat_value(score_str) or 0.0
        return {
            "title": item.get("title", ""),
            "summary": item.get("title", ""),
            "source": self.source_name,
            "source_url": item.get("link", ""),
            "heat_value": float(heat),
            "trend_direction": "same",
            "image_url": item.get("work_type_icon", ""),
            "category": "",
            "keywords": "",
        }
