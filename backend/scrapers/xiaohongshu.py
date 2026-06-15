"""
小红书趋势爬虫
"""
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re
import logging

from .base import BaseScraper

logger = logging.getLogger(__name__)


class XiaohongshuScraper(BaseScraper):
    """小红书趋势爬虫

    注意：小红书反爬较为严格，大部分内容需要登录才能查看
    这里实现基础版本，实际使用时可能需要配置Cookie
    """

    EXPLORE_URL = "https://www.xiaohongshu.com/explore"
    SEARCH_URL = "https://www.xiaohongshu.com/search_result"

    async def search(
        self,
        keyword: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        搜索小红书热点

        Args:
            keyword: 搜索关键词
            days: 搜索天数

        Returns:
            热点话题列表
        """
        try:
            if keyword:
                topics = await self.search_by_keyword(keyword)
            else:
                topics = await self.get_trending()

            logger.info(f"小红书搜索: {keyword}, 找到 {len(topics)} 条结果")
            return topics[:10]

        except Exception as e:
            logger.error(f"小红书搜索失败: {e}")
            return []

    async def get_trending(self) -> List[Dict[str, Any]]:
        """
        获取小红书趋势/发现页

        Returns:
            趋势话题列表
        """
        try:
            headers = self._get_headers()
            headers.update({
                "Referer": "https://www.xiaohongshu.com/",
                "Cookie": ""  # 可能需要Cookie
            })

            response = await self.client.get(
                self.EXPLORE_URL,
                headers=headers
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            topics = self._parse_explore_page(soup)

            logger.info(f"小红书趋势: 找到 {len(topics)} 条结果")
            return topics

        except Exception as e:
            logger.error(f"获取小红书趋势失败: {e}")
            return []

    def _parse_explore_page(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """解析小红书发现页"""
        topics = []

        try:
            # 小红书发现页笔记卡片
            cards = soup.select("section.note-item")

            for idx, card in enumerate(cards[:10]):
                try:
                    # 标题
                    title_elem = card.select_one("div.title span")
                    title = title_elem.get_text(strip=True) if title_elem else ""

                    # 链接
                    link_elem = card.select_one("a.cover")
                    url = link_elem.get("href", "") if link_elem else ""
                    if url and not url.startswith("http"):
                        url = "https://www.xiaohongshu.com" + url

                    # 封面图
                    img_elem = card.select_one("img")
                    image_url = img_elem.get("src", "") if img_elem else ""

                    # 点赞数
                    like_elem = card.select_one("span.like-wrapper span.count")
                    like_text = like_elem.get_text(strip=True) if like_elem else ""
                    heat_value = self._extract_heat_value(like_text) or 1000.0

                    if title:
                        topic = {
                            "title": title,
                            "summary": f"小红书热门笔记",
                            "source": "小红书",
                            "source_url": url,
                            "category": "生活",
                            "heat_value": heat_value,
                            "trend_direction": "same",
                            "published_at": datetime.now(),
                            "image_url": image_url,
                        }
                        topics.append(self._normalize_topic(topic))

                except Exception as e:
                    logger.debug(f"解析笔记条目失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"解析发现页失败: {e}")

        # 如果HTML解析失败，尝试从SSR数据获取
        if not topics:
            topics = self._parse_ssr_data(soup)

        return topics

    def _parse_ssr_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        从小红书SSR数据中解析内容

        小红书会将初始数据嵌入到script标签中
        """
        topics = []

        try:
            # 查找初始状态数据
            for script in soup.find_all("script"):
                text = script.string or ""
                if "__INITIAL_STATE__" in text:
                    try:
                        # 提取JSON
                        match = re.search(
                            r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*</script>',
                            text,
                            re.DOTALL
                        )
                        if match:
                            json_str = match.group(1)
                            # 小红书的JSON可能有undefined值，需要替换
                            json_str = re.sub(r'\bundefined\b', 'null', json_str)
                            data = json.loads(json_str)

                            # 解析笔记数据
                            notes = data.get("notes", {})
                            if isinstance(notes, dict):
                                for note_id, note in list(notes.items())[:10]:
                                    try:
                                        title = note.get("title", "")
                                        desc = note.get("desc", "")
                                        url = f"https://www.xiaohongshu.com/explore/{note_id}"
                                        image_url = ""
                                        if note.get("imageList"):
                                            image_url = note["imageList"][0].get("url", "")
                                        likes = note.get("interactInfo", {}).get("likedCount", "0")
                                        heat_value = self._extract_heat_value(likes) or 1000.0

                                        if title or desc:
                                            topic = {
                                                "title": title or desc[:50],
                                                "summary": desc[:200] if desc else "",
                                                "source": "小红书",
                                                "source_url": url,
                                                "category": "生活",
                                                "heat_value": heat_value,
                                                "trend_direction": "same",
                                                "published_at": datetime.now(),
                                                "image_url": image_url,
                                            }
                                            topics.append(self._normalize_topic(topic))

                                    except Exception as e:
                                        logger.debug(f"解析笔记数据失败: {e}")
                                        continue

                    except (json.JSONDecodeError, KeyError) as e:
                        logger.debug(f"解析SSR数据失败: {e}")
                        continue

        except Exception as e:
            logger.error(f"从SSR数据解析内容失败: {e}")

        return topics

    async def search_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        通过关键词搜索小红书

        Args:
            keyword: 搜索关键词

        Returns:
            相关话题列表
        """
        try:
            headers = self._get_headers()
            headers["Referer"] = "https://www.xiaohongshu.com/"

            params = {
                "keyword": keyword,
                "source": "web_search_result_notes"
            }

            response = await self.client.get(
                self.SEARCH_URL,
                params=params,
                headers=headers
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            topics = self._parse_search_results(soup)

            logger.info(f"小红书关键词搜索: {keyword}, 找到 {len(topics)} 条结果")
            return topics

        except Exception as e:
            logger.error(f"小红书关键词搜索失败: {e}")
            return []

    def _parse_search_results(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """解析搜索结果"""
        topics = []

        try:
            # 尝试从HTML解析
            cards = soup.select("div.note-item, section.note-item")

            for idx, card in enumerate(cards[:10]):
                try:
                    title_elem = card.select_one("div.title, a.title")
                    title = title_elem.get_text(strip=True) if title_elem else ""

                    link_elem = card.select_one("a")
                    url = link_elem.get("href", "") if link_elem else ""

                    img_elem = card.select_one("img")
                    image_url = img_elem.get("src", "") if img_elem else ""

                    if title:
                        topic = {
                            "title": title,
                            "summary": f"小红书搜索结果",
                            "source": "小红书",
                            "source_url": url,
                            "category": "生活",
                            "heat_value": 5000.0,
                            "trend_direction": "same",
                            "published_at": datetime.now(),
                            "image_url": image_url,
                        }
                        topics.append(self._normalize_topic(topic))

                except Exception as e:
                    logger.debug(f"解析搜索条目失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"解析搜索结果失败: {e}")

        # 如果HTML解析失败，尝试SSR数据
        if not topics:
            topics = self._parse_ssr_data(soup)

        return topics