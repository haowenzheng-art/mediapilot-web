"""
百度新闻爬虫

v4 改造：解析 s-data JSON 里的 dispTime（相对时间"X小时前"/"X天前"/绝对日期）
实现 days 过滤——之前 days 参数形同虚设，返回结果可能跨多年
"""
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
import logging
from urllib.parse import quote

from .base import BaseScraper

logger = logging.getLogger(__name__)


class BaiduNewsScraper(BaseScraper):
    """百度新闻爬虫"""

    BASE_URL = "https://www.baidu.com/s"
    NEWS_API_URL = "https://news.baidu.com/ns"

    async def search(self, keyword: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        搜索百度新闻

        v4 改造：days 真正生效——解析 s-data 里的 dispTime，过滤掉早于 days 天的结果。
        无法解析时间的条目保留（不漏数据，但前端不展示日期）。
        """
        try:
            url = self.BASE_URL
            params = {
                "wd": keyword,
                "tn": "news",
                "rtt": "1",
                "bsst": "1",
                "cl": "2",
                "xword": keyword,
            }

            response = await self.client.get(
                url,
                params=params,
                headers=self._get_headers(),
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            topics, parsed_count = await self._parse_search_results(soup, keyword)

            # days 过滤：保留 published_at >= cutoff 或 published_at 为 None 的
            cutoff = datetime.now() - timedelta(days=days)
            before_filter = len(topics)
            filtered = []
            for t in topics:
                pub = t.get("published_at")
                if pub is None or pub >= cutoff:
                    filtered.append(t)
            dropped = before_filter - len(filtered)
            if dropped:
                logger.info(
                    f"百度时间窗过滤: keyword={keyword} days={days} "
                    f"保留 {len(filtered)} 条，过滤 {dropped} 条（早于 {cutoff.strftime('%Y-%m-%d')}）"
                )
            else:
                logger.info(
                    f"百度新闻搜索: {keyword} days={days} 解析 {parsed_count} 条，"
                    f"全部保留 {len(filtered)} 条"
                )
            return filtered

        except Exception as e:
            logger.error(f"百度新闻搜索失败: {e}")
            return []

    async def _parse_search_results(
        self, soup: BeautifulSoup, keyword: str
    ) -> tuple[List[Dict[str, Any]], int]:
        """解析搜索结果页面

        v4 改造：从 <!--s-data:{...}--> 注释里抽 JSON 拿 dispTime。
        旧版（class 匹配）拿不到时间，published_at 永远 None，days 形同虚设。
        """
        topics: List[Dict[str, Any]] = []
        parsed_count = 0
        try:
            # 百度新闻结果用 s-data 注释携带 JSON 数据
            for item in soup.find_all("div", class_=["result", "c-container"]):
                try:
                    topic = self._extract_from_sdata(item, keyword)
                    if topic is None:
                        continue
                    parsed_count += 1
                    topics.append(topic)
                except Exception as e:
                    logger.debug(f"解析单条结果失败: {e}")
                    continue
        except Exception as e:
            logger.error(f"解析搜索结果失败: {e}")

        if len(topics) < 3:
            logger.warning(f"搜索结果不足（{len(topics)} 条），尝试获取热搜榜")
            hot_topics = await self.get_hot_search()
            topics.extend(hot_topics)

        return topics, parsed_count

    def _extract_from_sdata(self, item, keyword: str) -> Optional[Dict[str, Any]]:
        """从 result item 的 <!--s-data:...--> 注释里抽 JSON 字段。"""
        sdata = item.find(string=lambda s: s and isinstance(s, str) and s.strip().startswith("s-data:"))
        if not sdata:
            return None
        try:
            # s-data 后的 JSON
            raw = sdata.strip()
            if raw.startswith("s-data:"):
                raw = raw[len("s-data:"):].strip()
            # 注释可能被 BS 拆成多段 text node，这里假设百度是单段（实测是这样）
            data = json.loads(raw)
        except (ValueError, TypeError):
            return None

        title_raw = (data.get("title") or "").strip()
        if not title_raw:
            return None
        # 去 <em> 高亮
        title = re.sub(r"</?em>", "", title_raw)
        if title.startswith("广告"):
            return None

        url = data.get("titleUrl") or data.get("url") or ""
        if not url:
            url = f"https://www.baidu.com/s?wd={quote(title)}"

        # summary
        summary = re.sub(r"</?em>", "", data.get("summary") or "")
        summary = summary.strip()[:500]

        # 来源
        source = data.get("sourceName") or "百度新闻"

        # 时间：dispTime + 兜底 publishedAt
        disp_time = (data.get("dispTime") or "").strip()
        published_at = self._parse_disp_time(disp_time) if disp_time else None

        topic = {
            "title": title[:200],
            "summary": summary,
            "source": source,
            "source_url": url,
            "category": "新闻",
            "heat_value": 50000.0,
            "trend_direction": "same",
            "published_at": published_at,
            "image_url": "",
        }
        return self._normalize_topic(topic)

    @staticmethod
    def _parse_disp_time(text: str) -> Optional[datetime]:
        """把百度 dispTime 解析成 datetime。

        支持格式：
        - "X分钟前" / "X秒前" / "X小时前" / "X天前"（相对）
        - "昨天 HH:MM" / "前天 HH:MM"
        - "YYYY年M月D日" / "YYYY年M月D日 HH:MM"（绝对）
        - "M月D日"（当年）
        - "刚刚"（now）
        - 解析不了 → None
        """
        if not text:
            return None
        s = text.strip()
        now = datetime.now()
        try:
            if s == "刚刚" or s == "刚刚":
                return now
            # 相对时间
            m = re.match(r"^(\d+)\s*秒前", s)
            if m:
                return now - timedelta(seconds=int(m.group(1)))
            m = re.match(r"^(\d+)\s*分钟前", s)
            if m:
                return now - timedelta(minutes=int(m.group(1)))
            m = re.match(r"^(\d+)\s*小时前", s)
            if m:
                return now - timedelta(hours=int(m.group(1)))
            m = re.match(r"^(\d+)\s*天前", s)
            if m:
                return now - timedelta(days=int(m.group(1)))
            # 昨天 / 前天
            m = re.match(r"^昨天\s*(\d{1,2}):(\d{1,2})$", s)
            if m:
                d = now - timedelta(days=1)
                return d.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
            m = re.match(r"^前天\s*(\d{1,2}):(\d{1,2})$", s)
            if m:
                d = now - timedelta(days=2)
                return d.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
            # 绝对日期
            m = re.match(r"^(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2}):(\d{1,2})$", s)
            if m:
                return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                                int(m.group(4)), int(m.group(5)))
            m = re.match(r"^(\d{4})年(\d{1,2})月(\d{1,2})日$", s)
            if m:
                return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            # 当年 M月D日
            m = re.match(r"^(\d{1,2})月(\d{1,2})日\s*(\d{1,2}):(\d{1,2})$", s)
            if m:
                return datetime(now.year, int(m.group(1)), int(m.group(2)),
                                int(m.group(3)), int(m.group(4)))
            m = re.match(r"^(\d{1,2})月(\d{1,2})日$", s)
            if m:
                return datetime(now.year, int(m.group(1)), int(m.group(2)))
        except (ValueError, AttributeError):
            return None
        return None

    async def get_hot_search(self) -> List[Dict[str, Any]]:
        """获取百度热搜榜"""
        try:
            url = "https://top.baidu.com/board?tab=realtime"
            response = await self.client.get(url, headers=self._get_headers())
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            topics = self._parse_hot_search(soup)
            logger.info(f"百度热搜榜: 找到 {len(topics)} 条结果")
            return topics
        except Exception as e:
            logger.error(f"获取百度热搜榜失败: {e}")
            return []

    def _parse_hot_search(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """解析百度热搜榜页面"""
        topics = []
        try:
            items = soup.select(".category-wrap_iQLoo.horizontal_1eKyQ")
            for idx, item in enumerate(items[:10]):
                try:
                    title_elem = item.select_one("div.content_1YWBm")
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    hot_elem = item.select_one("div.hot-index_1Bl1a")
                    hot_text = hot_elem.get_text(strip=True) if hot_elem else ""
                    heat_value = self._extract_heat_value(hot_text) or 100000.0
                    url = f"https://www.baidu.com/s?wd={quote(title)}" if title else ""
                    if title:
                        topic = {
                            "title": title,
                            "summary": f"百度热搜第{idx+1}名",
                            "source": "百度热搜",
                            "source_url": url,
                            "category": "热搜",
                            "heat_value": heat_value,
                            "trend_direction": "same",
                            "published_at": datetime.now(),
                            "image_url": "",
                        }
                        topics.append(self._normalize_topic(topic))
                except Exception as e:
                    logger.debug(f"解析热搜条目失败: {e}")
                    continue
        except Exception as e:
            logger.error(f"解析热搜榜失败: {e}")
        return topics

    async def get_article_content(self, url: str) -> str:
        """获取文章全文"""
        try:
            headers = self._get_headers()
            headers["Referer"] = "https://www.baidu.com/"
            response = await self.client.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            for selector in ["div.article-content", "div.article", "div.content", "div.post-content", "div.news-content", "article", "div.main-content"]:
                content_elem = soup.select_one(selector)
                if content_elem:
                    for elem in content_elem.find_all(["script", "style", "iframe", "noscript"]):
                        elem.decompose()
                    return content_elem.get_text(strip=True)
            paragraphs = soup.find_all("p")
            if paragraphs:
                return "\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            return ""
        except Exception as e:
            logger.error(f"获取文章内容失败: {e}")
            return ""
