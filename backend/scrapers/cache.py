"""
热点搜索缓存层

60s-api 数据本身更新慢、第三方不稳定，用 TTL 缓存抗抖动 + 减少 API 调用。
进程内 dict，不进 DB（项目单实例部署，无需考虑多实例共享）。

key 设计："{endpoint}::{keyword}::{days}"
- endpoint: 60s-api 的端点（weibo/zhihu/douyin/toutiao/rednote）
- keyword: 搜索关键词
- days: 时间范围（虽然 60s-api 不支持，但 key 加上以备将来扩展）

并发：asyncio.Lock 保护 dict 读写。单实例下 asyncio 协程调度串行安全；
跨实例场景应改用 Redis（当前规模不需要）。
"""
import asyncio
import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TTLCache:
    """线程/协程安全的内存 TTL 缓存

    简单实现：dict 存 (expires_at_epoch, value) 元组。
    - get 时检查过期，懒清理
    - set 时覆盖（不重复）
    - invalidate(key) 主动失效单条；invalidate() 不传 key 清空所有
    """

    def __init__(self, default_ttl: int = 1800):
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()
        self.default_ttl = default_ttl
        # 简单指标：方便热点/前端观察缓存命中率
        self.hits = 0
        self.misses = 0

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self.misses += 1
                return None
            expires_at, value = entry
            if time.time() > expires_at:
                self._store.pop(key, None)
                self.misses += 1
                return None
            self.hits += 1
            return value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        async with self._lock:
            self._store[key] = (time.time() + (ttl or self.default_ttl), value)

    async def invalidate(self, key: Optional[str] = None) -> None:
        async with self._lock:
            if key:
                self._store.pop(key, None)
            else:
                self._store.clear()

    def stats(self) -> dict:
        """命中统计（同步读取，不加锁 — 读不精确无所谓）"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0
        return {
            "size": len(self._store),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 3),
            "total_requests": total,
        }


# 全局单例：热点搜索专用
trending_cache = TTLCache()


def make_cache_key(endpoint: str, keyword: str, days: int) -> str:
    """生成缓存 key。空 keyword 统一用空串占位，避免 None 类型差异"""
    return f"{endpoint}::{keyword or ''}::{days}"