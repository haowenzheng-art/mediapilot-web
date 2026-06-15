"""
百度新闻爬虫
"""
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import logging
from urllib.parse import urlencode, quote
from datetime import datetime, timedelta

from .base import BaseScraper

logger = logging.getLogger(__name__)


class BaiduNewsScraper(BaseScraper):
    """百度新闻爬虫"""

    BASE_URL = "https://www.baidu.com/s"
    NEWS_API_URL = "https://news.baidu.com/ns"

    async def search(self, keyword: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        搜索百度新闻
        """
        try:
            url = self.BASE_URL
            params = {
                "wd": keyword,
                "tn": "news",
                "rtt": "1",
                "bsst": "1",
                "cl": "2",
                "xword": keyword
            }

            response = await self.client.get(
                url,
                params=params,
                headers=self._get_headers()
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            topics = await self._parse_search_results(soup, keyword)

            logger.info(f"百度新闻搜索: {keyword}, 找到 {len(topics)} 条结果")
            return topics

        except Exception as e:
            logger.error(f"百度新闻搜索失败: {e}")
            return []

    async def _parse_search_results(self, soup: BeautifulSoup, keyword: str) -> List[Dict[str, Any]]:
        """解析搜索结果页面"""
        topics = []
        try:
            result_items = soup.find_all("div", class_=["result", "c-container"])
            for item in result_items[:15]:
                try:
                    title_elem = item.find("a")
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)
                    url = title_elem.get("href", "")
                    
                    summary = ""
                    for selector in ["div.c-abstract", "div.abstract", "p.c-abstract", "p.abstract"]:
                        summary_elem = item.find(selector)
                        if summary_elem:
                            summary = summary_elem.get_text(strip=True)
                            if summary:
                                break
                    
                    source = "百度新闻"
                    published_at = None
                    heat_value = 50000.0

                    if not title or title.startswith("广告"):
                        continue
                    if not url:
                        url = f"https://www.baidu.com/s?wd={quote(title)}"
                    
                    topic = {
                        "title": title,
                        "summary": summary,
                        "source": source,
                        "source_url": url,
                        "category": "新闻",
                        "heat_value": heat_value,
                        "trend_direction": "same",
                        "published_at": published_at,
                        "image_url": "",
                    }
                    topics.append(self._normalize_topic(topic))
                except Exception as e:
                    logger.debug(f"解析单条结果失败: {e}")
                    continue
        except Exception as e:
            logger.error(f"解析搜索结果失败: {e}")
        
        if len(topics) < 3:
            logger.warning(f"搜索结果不足，尝试获取热搜榜")
            hot_topics = await self.get_hot_search()
            topics.extend(hot_topics)
        
        return topics

    def _parse_source_time(self, text: str) -> tuple[str, Optional]:
        if not text:
            return "", None
        text = text.strip()
        return "百度新闻", None

    def _extract_heat_from_item(self, item) -> float:
        try:
            related_elem = item.find("span", string=lambda x: x and "%" in x)
            if related_elem:
                heat_text = related_elem.get_text(strip=True)
                return self._extract_heat_value(heat_text) or 50000.0
            return 50000.0
        except:
            return 50000.0

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
