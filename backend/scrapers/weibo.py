"""
DEPRECATED — 2026/07 起被 SixtysWeiboScraper（backend/scrapers/sixtys.py）替代，
不再被 backend/core/platform_api.py import。保留仅作历史参考，
下一个清理周期可删除（建议保留至 2026/12）。
原微博热搜爬虫
"""
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import logging
from urllib.parse import quote

from .base import BaseScraper

logger = logging.getLogger(__name__)


class WeiboScraper(BaseScraper):
    """微博热搜爬虫"""

    HOT_SEARCH_URL = "https://s.weibo.com/top/summary"

    async def search(
        self,
        keyword: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        搜索微博热点

        Args:
            keyword: 搜索关键词
            days: 搜索天数

        Returns:
            热点话题列表
        """
        try:
            # 获取微博热搜榜
            topics = await self.get_hot_search()

            # 如果有关键词，筛选相关话题
            if keyword:
                from difflib import SequenceMatcher
                filtered = []
                for topic in topics:
                    title = topic.get("title", "")
                    similarity = SequenceMatcher(None, title, keyword).ratio()
                    if similarity > 0.3 or keyword.lower() in title.lower():
                        filtered.append(topic)
                topics = filtered

            logger.info(f"微博搜索: {keyword}, 找到 {len(topics)} 条结果")
            return topics[:10]

        except Exception as e:
            logger.error(f"微博搜索失败: {e}")
            return []

    async def get_hot_search(self) -> List[Dict[str, Any]]:
        """
        获取微博热搜榜

        Returns:
            热搜话题列表
        """
        try:
            # 添加更多请求头，避免被反爬
            headers = self._get_headers()
            headers.update({
                "Referer": "https://weibo.com/",
                "Cookie": ""  # 实际使用时可能需要添加Cookie
            })

            response = await self.client.get(
                self.HOT_SEARCH_URL,
                headers=headers
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            topics = self._parse_hot_search(soup)

            logger.info(f"微博热搜榜: 找到 {len(topics)} 条结果")
            return topics

        except Exception as e:
            logger.error(f"获取微博热搜榜失败: {e}")
            return []

    def _parse_hot_search(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """解析微博热搜榜页面"""
        topics = []

        try:
            # 微博热搜榜的常见结构
            # tbody > tr
            rows = soup.select("#pl_top_realtimehot table tbody tr")

            for row in rows:
                try:
                    # 排名
                    rank_elem = row.select_one("td td.rank")
                    rank = rank_elem.get_text(strip=True) if rank_elem else ""

                    # 标题和链接
                    link_elem = row.select_one("a")
                    title = link_elem.get_text(strip=True) if link_elem else ""
                    url = "https://s.weibo.com" + link_elem.get("href", "") if link_elem else ""

                    # 热度
                    hot_elem = row.select_one("td span.icon-hot")
                    if not hot_elem:
                        hot_elem = row.select_one("td span")
                    hot_text = hot_elem.get_text(strip=True) if hot_elem else ""
                    heat_value = self._extract_heat_value(hot_text) or 0

                    # 分类（热搜/热词/新晋）
                    category_elem = row.select_one("td span.c-icon")
                    category = "热搜"
                    if category_elem:
                        cat_text = category_elem.get_text(strip=True)
                        if "热" in cat_text:
                            category = "热搜"
                        elif "新" in cat_text:
                            category = "新晋"
                        elif "沸" in cat_text:
                            category = "沸点"

                    # 跳过广告和无效条目
                    if title and not title.startswith("广告"):
                        topic = {
                            "title": title,
                            "summary": f"微博热搜第{rank}名",
                            "source": "微博热搜",
                            "source_url": url,
                            "category": category,
                            "heat_value": heat_value,
                            "trend_direction": "same",
                            "published_at": datetime.now(),
                            "image_url": "",
                        }
                        topics.append(self._normalize_topic(topic))

                    if len(topics) >= 10:
                        break

                except Exception as e:
                    logger.debug(f"解析热搜条目失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"解析热搜榜失败: {e}")

        return topics

    async def search_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        通过关键词搜索微博内容

        Args:
            keyword: 搜索关键词

        Returns:
            相关话题列表
        """
        try:
            url = "https://s.weibo.com/weibo"
            params = {
                "q": keyword,
                "Refer": "weibo_weibo"
            }

            headers = self._get_headers()
            headers["Referer"] = "https://weibo.com/"

            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            topics = self._parse_search_results(soup, keyword)

            logger.info(f"微博关键词搜索: {keyword}, 找到 {len(topics)} 条结果")
            return topics

        except Exception as e:
            logger.error(f"微博关键词搜索失败: {e}")
            return []

    def _parse_search_results(
        self,
        soup: BeautifulSoup,
        keyword: str
    ) -> List[Dict[str, Any]]:
        """解析微博搜索结果页面"""
        topics = []

        try:
            # 微博搜索结果结构
            cards = soup.select("div.card-wrap")

            for card in cards[:10]:
                try:
                    # 标题/内容
                    content_elem = card.select_one("div[node-type=feed_list_content]")
                    title = content_elem.get_text(strip=True)[:100] if content_elem else ""

                    # 链接
                    link_elem = card.select_one("a.from")
                    url = link_elem.get("href", "") if link_elem else ""

                    # 发布时间
                    time_elem = card.select_one("a[node-type=feed_list_item_date]")
                    time_text = time_elem.get_text(strip=True) if time_elem else ""
                    published_at = self._parse_time(time_text)

                    # 发布者
                    author_elem = card.select_one("a.name")
                    author = author_elem.get_text(strip=True) if author_elem else ""

                    # 转发/评论/点赞数作为热度参考
                    action_links = card.select("a[node-type]")
                    heat_value = 0
                    for link in action_links:
                        text = link.get_text(strip=True)
                        if "万" in text:
                            heat_value += float(text.replace("万", "")) * 10000
                        elif "千" in text:
                            heat_value += float(text.replace("千", "")) * 1000
                        elif text.isdigit():
                            heat_value += int(text)

                    if title:
                        topic = {
                            "title": title,
                            "summary": f"@{author}",
                            "source": "微博",
                            "source_url": url,
                            "category": "微博",
                            "heat_value": heat_value or 5000.0,
                            "trend_direction": "same",
                            "published_at": published_at,
                            "image_url": "",
                        }
                        topics.append(self._normalize_topic(topic))

                except Exception as e:
                    logger.debug(f"解析搜索条目失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"解析搜索结果失败: {e}")

        return topics

    def _parse_time(self, text: str) -> datetime:
        """解析时间文本"""
        now = datetime.now()

        if not text:
            return now

        # 今天 HH:MM
        match = re.search(r"今天\s*(\d{2}):(\d{2})", text)
        if match:
            hour, minute = int(match.group(1)), int(match.group(2))
            return datetime(now.year, now.month, now.day, hour, minute)

        # XX分钟前
        match = re.search(r"(\d+)分钟前", text)
        if match:
            return now - timedelta(minutes=int(match.group(1)))

        # XX小时前
        match = re.search(r"(\d+)小时前", text)
        if match:
            return now - timedelta(hours=int(match.group(1)))

        # XX天前
        match = re.search(r"(\d+)天前", text)
        if match:
            return now - timedelta(days=int(match.group(1)))

        # MM-DD
        match = re.search(r"(\d{2})-(\d{2})", text)
        if match:
            month, day = int(match.group(1)), int(match.group(2))
            year = now.year
            if month > now.month:
                year -= 1
            return datetime(year, month, day)

        return now