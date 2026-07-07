"""
DEPRECATED — 2026/07 起被 SixtysZhihuScraper（backend/scrapers/sixtys.py）替代，
不再被 backend/core/platform_api.py import。保留仅作历史参考，
下一个清理周期可删除（建议保留至 2026/12）。
原知乎热榜爬虫
"""
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import json
import logging

from .base import BaseScraper

logger = logging.getLogger(__name__)


class ZhihuScraper(BaseScraper):
    """知乎热榜爬虫"""

    HOT_LIST_URL = "https://www.zhihu.com/hot"
    SEARCH_URL = "https://www.zhihu.com/search"

    async def search(
        self,
        keyword: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        搜索知乎热点

        Args:
            keyword: 搜索关键词
            days: 搜索天数

        Returns:
            热点话题列表
        """
        try:
            # 如果有关键词，先搜索
            if keyword:
                topics = await self.search_by_keyword(keyword)
            else:
                topics = await self.get_hot_list()

            logger.info(f"知乎搜索: {keyword}, 找到 {len(topics)} 条结果")
            return topics[:10]

        except Exception as e:
            logger.error(f"知乎搜索失败: {e}")
            return []

    async def get_hot_list(self) -> List[Dict[str, Any]]:
        """
        获取知乎热榜

        Returns:
            热榜话题列表
        """
        try:
            headers = self._get_headers()
            headers.update({
                "Referer": "https://www.zhihu.com/",
            })

            response = await self.client.get(
                self.HOT_LIST_URL,
                headers=headers
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            topics = self._parse_hot_list(soup)

            logger.info(f"知乎热榜: 找到 {len(topics)} 条结果")
            return topics

        except Exception as e:
            logger.error(f"获取知乎热榜失败: {e}")
            return []

    def _parse_hot_list(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """解析知乎热榜页面"""
        topics = []

        try:
            # 知乎热榜结构
            items = soup.select("div.HotList-list div.HotItem")

            for item in items[:10]:
                try:
                    # 标题
                    title_elem = item.select_one("h2.HotItem-title")
                    title = title_elem.get_text(strip=True) if title_elem else ""

                    # 摘要
                    excerpt_elem = item.select_one("p.HotItem-excerpt")
                    summary = excerpt_elem.get_text(strip=True) if excerpt_elem else ""

                    # 热度
                    hot_elem = item.select_one("div.HotItem-metrics")
                    hot_text = hot_elem.get_text(strip=True) if hot_elem else ""
                    heat_value = self._extract_heat_value(hot_text) or 0

                    # 链接
                    link_elem = item.select_one("a.HotItem-content")
                    url = link_elem.get("href", "") if link_elem else ""

                    # 图片
                    img_elem = item.select_one("img.HotItem-img")
                    image_url = img_elem.get("src", "") if img_elem else ""

                    if title:
                        topic = {
                            "title": title,
                            "summary": summary,
                            "source": "知乎热榜",
                            "source_url": url,
                            "category": "知识",
                            "heat_value": heat_value,
                            "trend_direction": "same",
                            "published_at": datetime.now(),
                            "image_url": image_url,
                        }
                        topics.append(self._normalize_topic(topic))

                except Exception as e:
                    logger.debug(f"解析热榜条目失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"解析热榜失败: {e}")

        # 如果解析失败，尝试从初始状态数据中获取
        if not topics:
            topics = self._parse_initial_data(soup)

        return topics

    def _parse_initial_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        从知乎页面的初始状态JSON数据中解析热榜

        知乎会在页面中嵌入initialData JSON
        """
        topics = []

        try:
            script_tags = soup.find_all("script", id="js-initialData")
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    hot_list = data.get("initialState", {}).get("topstory", {}).get("hotList", [])

                    for item in hot_list[:10]:
                        target = item.get("target", {})
                        title = target.get("title", "")
                        excerpt = target.get("excerpt", "")
                        url = target.get("url", "")
                        image_url = target.get("thumbnail", "")
                        heat_value = item.get("detail_text", "")
                        heat = self._extract_heat_value(heat_value) or 0

                        if title:
                            topic = {
                                "title": title,
                                "summary": excerpt,
                                "source": "知乎热榜",
                                "source_url": url,
                                "category": "知识",
                                "heat_value": heat,
                                "trend_direction": "same",
                                "published_at": datetime.now(),
                                "image_url": image_url,
                            }
                            topics.append(self._normalize_topic(topic))

                except (json.JSONDecodeError, KeyError) as e:
                    logger.debug(f"解析初始数据失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"从初始数据解析热榜失败: {e}")

        return topics

    async def search_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        通过关键词搜索知乎

        Args:
            keyword: 搜索关键词

        Returns:
            相关话题列表
        """
        try:
            headers = self._get_headers()
            headers["Referer"] = "https://www.zhihu.com/"

            params = {
                "q": keyword,
                "type": "content"
            }

            response = await self.client.get(
                self.SEARCH_URL,
                params=params,
                headers=headers
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            topics = self._parse_search_results(soup, keyword)

            logger.info(f"知乎关键词搜索: {keyword}, 找到 {len(topics)} 条结果")
            return topics

        except Exception as e:
            logger.error(f"知乎关键词搜索失败: {e}")
            return []

    def _parse_search_results(
        self,
        soup: BeautifulSoup,
        keyword: str
    ) -> List[Dict[str, Any]]:
        """解析知乎搜索结果页面"""
        topics = []

        try:
            # 搜索结果卡片
            cards = soup.select("div.SearchResult-Card")

            for card in cards[:10]:
                try:
                    # 标题
                    title_elem = card.select_one("h2.ContentItem-title a")
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    url = title_elem.get("href", "") if title_elem else ""

                    # 内容摘要
                    content_elem = card.select_one("span.RichText")
                    summary = content_elem.get_text(strip=True)[:200] if content_elem else ""

                    # 作者
                    author_elem = card.select_one("meta[itemprop=name]")
                    author = author_elem.get("content", "") if author_elem else ""

                    # 点赞数作为热度
                    vote_elem = card.select_one("button.VoteButton--up")
                    vote_text = vote_elem.get_text(strip=True) if vote_elem else ""
                    heat_value = self._extract_heat_value(vote_text) or 1000.0

                    if title:
                        topic = {
                            "title": title,
                            "summary": summary,
                            "source": "知乎",
                            "source_url": url,
                            "category": "知识",
                            "heat_value": heat_value,
                            "trend_direction": "same",
                            "published_at": datetime.now(),
                            "image_url": "",
                        }
                        topics.append(self._normalize_topic(topic))

                except Exception as e:
                    logger.debug(f"解析搜索条目失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"解析搜索结果失败: {e}")

        # 如果普通解析失败，尝试从初始数据获取
        if not topics:
            topics = self._parse_search_initial_data(soup, keyword)

        return topics

    def _parse_search_initial_data(
        self,
        soup: BeautifulSoup,
        keyword: str
    ) -> List[Dict[str, Any]]:
        """从搜索页面初始数据中解析结果"""
        topics = []

        try:
            script_tags = soup.find_all("script", id="js-initialData")
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    search_data = (
                        data.get("initialState", {})
                        .get("search", {})
                    )

                    # 搜索结果可能在不同key下
                    results = search_data.get("results", {})
                    if isinstance(results, dict):
                        results = results.get("hits", [])

                    for item in results[:10]:
                        if isinstance(item, dict):
                            target = item.get("target", item)
                            title = target.get("title", "")
                            excerpt = target.get("excerpt", "")
                            url = target.get("url", "")

                            if title:
                                topic = {
                                    "title": title,
                                    "summary": excerpt,
                                    "source": "知乎",
                                    "source_url": url,
                                    "category": "知识",
                                    "heat_value": 1000.0,
                                    "trend_direction": "same",
                                    "published_at": datetime.now(),
                                    "image_url": "",
                                }
                                topics.append(self._normalize_topic(topic))

                except (json.JSONDecodeError, KeyError) as e:
                    logger.debug(f"解析搜索初始数据失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"从初始数据解析搜索结果失败: {e}")

        return topics