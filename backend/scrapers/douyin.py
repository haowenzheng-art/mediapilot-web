"""
抖音热榜爬虫
"""
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re
import logging

from .base import BaseScraper

logger = logging.getLogger(__name__)


class DouyinScraper(BaseScraper):
    """抖音热榜爬虫

    注意：抖音网页版需要动态加载内容，部分数据需要使用 Playwright 获取
    这里先实现基础版本的HTML解析，如果失败则降级到API方式
    """

    HOT_LIST_URL = "https://www.douyin.com/hot"
    SEARCH_URL = "https://www.douyin.com/search"

    async def search(
        self,
        keyword: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        搜索抖音热点

        Args:
            keyword: 搜索关键词
            days: 搜索天数

        Returns:
            热点话题列表
        """
        try:
            # 尝试获取抖音热榜
            topics = await self.get_hot_list()

            # 如果有关键词，筛选相关话题
            if keyword and topics:
                from difflib import SequenceMatcher
                filtered = []
                for topic in topics:
                    title = topic.get("title", "")
                    similarity = SequenceMatcher(None, title, keyword).ratio()
                    if similarity > 0.3 or keyword.lower() in title.lower():
                        filtered.append(topic)
                topics = filtered

            logger.info(f"抖音搜索: {keyword}, 找到 {len(topics)} 条结果")
            return topics[:10]

        except Exception as e:
            logger.error(f"抖音搜索失败: {e}")
            return []

    async def get_hot_list(self) -> List[Dict[str, Any]]:
        """
        获取抖音热榜

        Returns:
            热榜话题列表
        """
        try:
            headers = self._get_headers()
            headers.update({
                "Referer": "https://www.douyin.com/",
                "Cookie": ""  # 可能需要Cookie
            })

            # 尝试直接获取
            response = await self.client.get(
                self.HOT_LIST_URL,
                headers=headers
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            topics = self._parse_hot_list_from_html(soup)

            # 如果HTML解析失败，尝试从SSR数据中获取
            if not topics:
                topics = self._parse_ssr_data(soup)

            logger.info(f"抖音热榜: 找到 {len(topics)} 条结果")
            return topics

        except Exception as e:
            logger.error(f"获取抖音热榜失败: {e}")
            return []

    def _parse_hot_list_from_html(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """从HTML中解析抖音热榜"""
        topics = []

        try:
            # 抖音热榜常见的DOM结构
            items = soup.select("div.hotword-content div.word")

            for idx, item in enumerate(items[:10]):
                try:
                    title = item.get_text(strip=True)
                    if title:
                        topic = {
                            "title": title,
                            "summary": f"抖音热榜第{idx+1}名",
                            "source": "抖音热榜",
                            "source_url": f"https://www.douyin.com/search/{title}",
                            "category": "短视频",
                            "heat_value": 100000.0 - idx * 5000,
                            "trend_direction": "same",
                            "published_at": datetime.now(),
                            "image_url": "",
                        }
                        topics.append(self._normalize_topic(topic))

                except Exception as e:
                    logger.debug(f"解析热榜条目失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"从HTML解析热榜失败: {e}")

        return topics

    def _parse_ssr_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        从抖音SSR数据中解析热榜

        抖音网页版会将初始数据嵌入到script标签中
        """
        topics = []

        try:
            # 查找包含初始数据的script标签
            for script in soup.find_all("script"):
                text = script.string or ""
                # 抖音的SSR数据通常包含在特定的script标签中
                if "hotList" in text or "wordList" in text or "aweme_list" in text:
                    try:
                        # 尝试提取JSON数据
                        data = self._extract_json_from_script(text)
                        if data:
                            topics = self._parse_data_from_json(data)
                            if topics:
                                break
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.debug(f"解析SSR数据失败: {e}")
                        continue

        except Exception as e:
            logger.error(f"从SSR数据解析热榜失败: {e}")

        return topics

    def _extract_json_from_script(self, text: str) -> dict:
        """从script标签中提取JSON数据"""
        # 尝试多种模式提取
        patterns = [
            r'self\.__pace_f\.push\(\[.*?"(.*)"\]\)',
            r'window\.__INIT_PROPS__\s*=\s*({.*?})\s*;?\s*</script>',
            r'window\._SSR_DATA__\s*=\s*({.*?})\s*;?\s*</script>',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    json_str = match.group(1)
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue

        return {}

    def _parse_data_from_json(self, data: dict) -> List[Dict[str, Any]]:
        """从JSON数据中解析热点"""
        topics = []

        # 尝试多种数据结构
        hot_lists = [
            data.get("hotList", []),
            data.get("wordList", []),
            data.get("aweme_list", []),
        ]

        for hot_list in hot_lists:
            if not hot_list or not isinstance(hot_list, list):
                continue

            for idx, item in enumerate(hot_list[:10]):
                try:
                    if isinstance(item, dict):
                        title = item.get("word", item.get("title", item.get("sentence_tag", "")))
                        hot_value = item.get("hot_value", item.get("heatValue", 0))
                        url = item.get("url", "")
                        image_url = item.get("cover", item.get("poster", ""))

                        if isinstance(hot_value, str):
                            hot_value = self._extract_heat_value(hot_value) or 0

                        if title:
                            topic = {
                                "title": title,
                                "summary": f"抖音热榜第{idx+1}名",
                                "source": "抖音热榜",
                                "source_url": url or f"https://www.douyin.com/search/{title}",
                                "category": "短视频",
                                "heat_value": float(hot_value),
                                "trend_direction": "same",
                                "published_at": datetime.now(),
                                "image_url": image_url,
                            }
                            topics.append(self._normalize_topic(topic))

                except Exception as e:
                    logger.debug(f"解析热点条目失败: {e}")
                    continue

            if topics:
                break

        return topics

    async def search_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        通过关键词搜索抖音内容

        Args:
            keyword: 搜索关键词

        Returns:
            相关话题列表
        """
        try:
            headers = self._get_headers()
            headers["Referer"] = "https://www.douyin.com/"

            params = {
                "keyword": keyword,
                "type": "general"
            }

            response = await self.client.get(
                self.SEARCH_URL,
                params=params,
                headers=headers
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            topics = self._parse_search_results(soup)

            logger.info(f"抖音关键词搜索: {keyword}, 找到 {len(topics)} 条结果")
            return topics

        except Exception as e:
            logger.error(f"抖音关键词搜索失败: {e}")
            return []

    def _parse_search_results(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """解析抖音搜索结果"""
        topics = []

        # 抖音搜索结果也是动态加载的，尝试从SSR数据获取
        topics = self._parse_ssr_data(soup)

        return topics