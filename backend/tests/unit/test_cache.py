"""
v3 冲刺单测 — 热点搜索 TTLCache

直接测试 TTLCache 的：
- 命中 / miss / 过期
- invalidate 单条 / 全清
- 命中率统计
"""
import asyncio
import time

import pytest

from backend.scrapers.cache import TTLCache, make_cache_key


def _run(coro):
    return asyncio.run(coro)


class TestTTLCache:
    def test_miss_returns_none(self):
        cache = TTLCache(default_ttl=60)
        assert _run(cache.get("nope")) is None

    def test_set_and_get_roundtrip(self):
        cache = TTLCache(default_ttl=60)
        _run(cache.set("k1", ["a", "b", "c"]))
        assert _run(cache.get("k1")) == ["a", "b", "c"]

    def test_overwrite(self):
        cache = TTLCache(default_ttl=60)
        _run(cache.set("k1", "first"))
        _run(cache.set("k1", "second"))
        assert _run(cache.get("k1")) == "second"

    def test_expired_returns_none(self):
        cache = TTLCache(default_ttl=1)  # 1 秒
        _run(cache.set("k1", "v"))
        # 不 sleep 就读 → 应该命中
        assert _run(cache.get("k1")) == "v"
        # 等过期
        time.sleep(1.2)
        assert _run(cache.get("k1")) is None

    def test_custom_ttl_overrides_default(self):
        cache = TTLCache(default_ttl=60)
        _run(cache.set("k_short", "x", ttl=1))
        time.sleep(1.2)
        assert _run(cache.get("k_short")) is None

    def test_invalidate_single_key(self):
        cache = TTLCache(default_ttl=60)
        _run(cache.set("k1", "v1"))
        _run(cache.set("k2", "v2"))
        _run(cache.invalidate("k1"))
        assert _run(cache.get("k1")) is None
        assert _run(cache.get("k2")) == "v2"

    def test_invalidate_all(self):
        cache = TTLCache(default_ttl=60)
        _run(cache.set("k1", "v1"))
        _run(cache.set("k2", "v2"))
        _run(cache.invalidate())
        assert _run(cache.get("k1")) is None
        assert _run(cache.get("k2")) is None

    def test_stats_tracks_hits_and_misses(self):
        cache = TTLCache(default_ttl=60)
        _run(cache.set("k1", "v"))
        _run(cache.get("k1"))   # hit
        _run(cache.get("k1"))   # hit
        _run(cache.get("nope"))  # miss
        stats = cache.stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == round(2 / 3, 3)
        assert stats["size"] == 1

    def test_stats_hit_rate_zero_when_empty(self):
        cache = TTLCache()
        stats = cache.stats()
        assert stats["hit_rate"] == 0.0
        assert stats["total_requests"] == 0

    def test_expired_increments_miss(self):
        cache = TTLCache(default_ttl=1)
        _run(cache.set("k", "v"))
        time.sleep(1.2)
        # 过期 → miss
        _run(cache.get("k"))
        stats = cache.stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1


class TestMakeCacheKey:
    def test_key_format(self):
        assert make_cache_key("weibo", "AI 写作", 7) == "weibo::AI 写作::7"

    def test_none_keyword_becomes_empty_string(self):
        # None 不能参与 key 拼接，统一转空串
        assert make_cache_key("weibo", None, 7) == "weibo::::7"

    def test_different_endpoints_different_keys(self):
        k1 = make_cache_key("weibo", "AI", 7)
        k2 = make_cache_key("zhihu", "AI", 7)
        assert k1 != k2

    def test_different_days_different_keys(self):
        k1 = make_cache_key("weibo", "AI", 7)
        k2 = make_cache_key("weibo", "AI", 30)
        assert k1 != k2