"""
今日头条搜索爬虫 — so.toutiao.com/search?keyword=xxx&pd=information

匿名可访问，返回真实关键词命中。用于补足微博/知乎/抖音/小红书反爬不可用时的真实搜索结果。
"""
import logging
import re
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import quote

from .base import BaseScraper

logger = logging.getLogger(__name__)


class ToutiaoSearchScraper(BaseScraper):
    """今日头条关键词搜索（真实搜索页 HTML 解析）"""

    BASE_URL = "https://so.toutiao.com/search"

    async def search(self, keyword: str, days: int = 7) -> List[Dict[str, Any]]:
        if not keyword:
            return []
        try:
            r = await self.client.get(
                self.BASE_URL,
                params={"keyword": keyword, "pd": "information", "source": "input"},
                headers=self._get_headers(),
                follow_redirects=True,
                timeout=12,
            )
            r.raise_for_status()
            html = r.text
        except Exception as e:
            logger.warning(f"头条搜索 [{keyword}] 失败: {e}")
            return []

        topics = self._parse(html, keyword)
        logger.info(f"头条搜索 [{keyword}] 找到 {len(topics)} 条")
        return topics

    def _parse(self, html: str, keyword: str) -> List[Dict[str, Any]]:
        """从搜索结果 HTML 中抽 title + url。

        头条搜索结果是 SSR JSON-in-HTML，title/article_url 配对出现：
          "title":"<em>军事</em> | xxx", ..., "article_url":"https://toutiao.com/..."
        关键词高亮用 \\u003cem\\u003e ... \\u003c/em\\u003e 转义字符串包裹。
        """
        results: List[Dict[str, Any]] = []
        seen_titles = set()

        # 1) 抓出 (title, article_url) 配对：title 在前，紧随其后的 article_url 是配套的
        title_iter = list(re.finditer(r'"title"\s*:\s*"([^"]{5,200})"', html))
        url_iter = list(re.finditer(r'"article_url"\s*:\s*"([^"]+)"', html))

        # 按出现位置配对（每个 title 紧跟的 article_url 就是它的链接）
        for t_match in title_iter:
            title_pos = t_match.start()
            # 找到第一个出现在 title 之后的 article_url
            next_url = None
            for u in url_iter:
                if u.start() > title_pos:
                    next_url = u.group(1)
                    break

            if not next_url:
                continue

            title = self._clean_text(t_match.group(1))
            url = self._clean_text(next_url)

            # 必须真正命中关键词
            if keyword.lower() not in title.lower():
                continue
            if title in seen_titles:
                continue
            seen_titles.add(title)

            if not url.startswith("http"):
                continue

            topic = {
                "title": title[:200],
                "summary": title[:200],
                "source": "今日头条",
                "source_url": url,
                "category": "搜索",
                "heat_value": 30000.0,  # 头条搜索无热度字段，给固定中等值
                "trend_direction": "same",
                "published_at": datetime.now(),
                "image_url": "",
                "keywords": keyword,
            }
            results.append(self._normalize_topic(topic))
            if len(results) >= 15:
                break

        return results

    @staticmethod
    def _clean_text(s: str) -> str:
        # 只解 \\uXXXX 转义，不动 UTF-8 实字符（避免把 UTF-8 字节误当 latin-1 解码出乱码）
        def _u(m):
            try:
                return chr(int(m.group(1), 16))
            except ValueError:
                return m.group(0)
        s = re.sub(r"\\u([0-9a-fA-F]{4})", _u, s)
        # 去 <em> 高亮标签
        s = re.sub(r"</?em>", "", s)
        return s.strip()
