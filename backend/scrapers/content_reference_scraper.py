"""
AI文案参考爬虫
从微博/百度/知乎获取相关内容作为AI生成文案的参考素材
"""
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import httpx
from fake_useragent import UserAgent
from urllib.parse import quote

logger = logging.getLogger(__name__)


class ContentReferenceScraper:
    """AI文案参考爬虫"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.ua = UserAgent()
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self._get_headers(),
            follow_redirects=True
        )

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive"
        }

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

    async def get_reference_content(
        self,
        keyword: str,
        platforms: Optional[List[str]] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        获取AI文案参考内容

        Args:
            keyword: 关键词/话题
            platforms: 平台列表，默认全部
            max_results: 每个平台最大结果数

        Returns:
            {
                "keyword": str,
                "weibo": List[Dict],
                "baidu": List[Dict],
                "zhihu": List[Dict],
                "summary": str
            }
        """
        if platforms is None:
            platforms = ["weibo", "baidu", "zhihu"]

        results = {
            "keyword": keyword,
            "weibo": [],
            "baidu": [],
            "zhihu": [],
            "summary": ""
        }

        try:
            if "weibo" in platforms:
                results["weibo"] = await self._scrape_weibo(keyword, max_results)

            if "baidu" in platforms:
                results["baidu"] = await self._scrape_baidu(keyword, max_results)

            if "zhihu" in platforms:
                results["zhihu"] = await self._scrape_zhihu(keyword, max_results)

            # 生成参考摘要
            results["summary"] = self._generate_reference_summary(results)

            logger.info(f"文案参考爬取: {keyword}, 微博{len(results['weibo'])}条, "
                       f"百度{len(results['baidu'])}条, 知乎{len(results['zhihu'])}条")

            return results

        except Exception as e:
            logger.error(f"获取文案参考失败: {e}")
            return results

    async def _scrape_weibo(self, keyword: str, max_results: int) -> List[Dict[str, Any]]:
        """爬取微博内容"""
        try:
            url = "https://s.weibo.com/weibo"
            params = {
                "q": keyword,
                "Refer": "weibo_weibo",
                "page": 1
            }

            headers = self._get_headers()
            headers["Referer"] = "https://weibo.com/"

            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            return self._parse_weibo_cards(soup, max_results)

        except Exception as e:
            logger.warning(f"微博爬取失败: {e}")
            return []

    def _parse_weibo_cards(self, soup: BeautifulSoup, max_results: int) -> List[Dict[str, Any]]:
        """解析微博内容卡片"""
        results = []

        try:
            # 微博内容卡片
            cards = soup.select("div.WB_feed_3")

            for card in cards[:max_results]:
                try:
                    # 发布者
                    author_elem = card.select_one("a.WB_name")
                    author = author_elem.get_text(strip=True) if author_elem else "匿名"

                    # 内容文本
                    content_elem = card.select_one("div.WB_text")
                    content = content_elem.get_text(strip=True) if content_elem else ""

                    # 去除话题标签
                    content = self._clean_hashtags(content)

                    if len(content) > 20:
                        results.append({
                            "source": "微博",
                            "author": author,
                            "content": content,
                            "type": "social_post"
                        })

                except Exception as e:
                    logger.debug(f"解析微博卡片失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"解析微博内容失败: {e}")

        return results

    async def _scrape_baidu(self, keyword: str, max_results: int) -> List[Dict[str, Any]]:
        """爬取百度新闻内容"""
        try:
            url = "https://www.baidu.com/s"
            params = {
                "wd": keyword,
                "tn": "news",
                "rtt": "1",
                "bsst": "1",
                "cl": "2"
            }

            response = await self.client.get(url, params=params, headers=self._get_headers())
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            results = self._parse_baidu_news(soup, max_results)

            # 获取部分文章详情
            detailed_results = []
            for item in results[:3]:
                try:
                    if item.get("source_url"):
                        detail = await self._get_article_detail(item["source_url"])
                        if detail:
                            item["detail"] = detail
                    detailed_results.append(item)
                except Exception as e:
                    detailed_results.append(item)
                    continue

            return detailed_results

        except Exception as e:
            logger.warning(f"百度爬取失败: {e}")
            return []

    def _parse_baidu_news(self, soup: BeautifulSoup, max_results: int) -> List[Dict[str, Any]]:
        """解析百度新闻"""
        results = []

        try:
            result_items = soup.find_all("div", class_=["result", "c-container"])

            for item in result_items[:max_results]:
                try:
                    title_elem = item.find("a")
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    url = title_elem.get("href", "")

                    # 摘要
                    summary_elem = item.find("div", class_="c-abstract")
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""

                    # 来源
                    source_elem = item.find("span", class_="c-color-gray")
                    source = source_elem.get_text(strip=True) if source_elem else "新闻"

                    if title and not title.startswith("广告"):
                        results.append({
                            "source": f"百度-{source}",
                            "title": title,
                            "summary": summary,
                            "source_url": url,
                            "type": "news_article"
                        })

                except Exception as e:
                    logger.debug(f"解析百度新闻条目失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"解析百度新闻失败: {e}")

        return results

    async def _get_article_detail(self, url: str) -> Optional[str]:
        """获取文章详情"""
        try:
            headers = self._get_headers()
            headers["Referer"] = "https://www.baidu.com/"

            response = await self.client.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, "lxml")

            # 尝试多种内容选择器
            content_selectors = [
                "div.article-content",
                "div.article",
                "div.content",
                "div.post-content",
                "div.news-content",
                "article",
                "div.main-content",
                "div.article-body",
                "div#article-content"
            ]

            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 移除脚本、样式等
                    for elem in content_elem.find_all(["script", "style", "iframe", "noscript", "ad"]):
                        elem.decompose()

                    content = content_elem.get_text(strip=True)
                    if len(content) > 100:
                        return self._clean_content(content)

            # 尝试段落
            paragraphs = soup.find_all("p")
            if paragraphs:
                content = "\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 10])
                if len(content) > 100:
                    return self._clean_content(content)

            return None

        except Exception as e:
            logger.debug(f"获取文章详情失败: {e}")
            return None

    async def _scrape_zhihu(self, keyword: str, max_results: int) -> List[Dict[str, Any]]:
        """爬取知乎内容"""
        try:
            url = "https://www.zhihu.com/search"
            params = {
                "q": keyword,
                "type": "content"
            }

            headers = self._get_headers()
            headers["Referer"] = "https://www.zhihu.com/"

            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            return self._parse_zhihu_answers(soup, max_results)

        except Exception as e:
            logger.warning(f"知乎爬取失败: {e}")
            return []

    def _parse_zhihu_answers(self, soup: BeautifulSoup, max_results: int) -> List[Dict[str, Any]]:
        """解析知乎回答"""
        results = []

        try:
            # 知乎搜索结果卡片
            cards = soup.select("div.SearchResult-Card")

            for card in cards[:max_results]:
                try:
                    # 标题/问题
                    title_elem = card.select_one("h2.ContentItem-title a")
                    title = title_elem.get_text(strip=True) if title_elem else ""

                    # 回答内容
                    content_elem = card.select_one("span.RichText")
                    content = content_elem.get_text(strip=True) if content_elem else ""

                    # 作者
                    author_elem = card.select_one("meta[itemprop=name]")
                    author = author_elem.get("content", "") if author_elem else ""

                    # 赞同数
                    vote_elem = card.select_one("button.VoteButton--up")
                    vote_text = vote_elem.get_text(strip=True) if vote_elem else ""

                    if content and len(content) > 30:
                        results.append({
                            "source": "知乎",
                            "title": title,
                            "author": author,
                            "content": content,
                            "votes": vote_text,
                            "type": "q_answer"
                        })

                except Exception as e:
                    logger.debug(f"解析知乎回答失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"解析知乎内容失败: {e}")

        return results

    def _clean_hashtags(self, text: str) -> str:
        """移除话题标签"""
        import re
        # 移除 #话题#
        text = re.sub(r'#[^\s#]+#', '', text)
        # 移除 @用户
        text = re.sub(r'@[\w\-_]+', '', text)
        return text.strip()

    def _clean_content(self, text: str) -> str:
        """清理内容"""
        # 移除多余空白
        import re
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊符号
        text = re.sub(r'[^一-鿿\w\s,.!?;:，。！？；：""'']', '', text)
        return text.strip()

    def _generate_reference_summary(self, results: Dict[str, Any]) -> str:
        """生成参考内容摘要"""
        parts = []

        # 微博观点
        if results["weibo"]:
            weibo_samples = results["weibo"][:2]
            parts.append("【微博观点】")
            for item in weibo_samples:
                parts.append(f"- {item['author']}: {item['content'][:100]}...")

        # 百度新闻
        if results["baidu"]:
            parts.append("【新闻视角】")
            for item in results["baidu"][:2]:
                parts.append(f"- {item['title']}: {item['summary'][:80]}...")

        # 知乎分析
        if results["zhihu"]:
            parts.append("【知乎观点】")
            for item in results["zhihu"][:2]:
                parts.append(f"- {item['author']}: {item['content'][:80]}...")

        return "\n".join(parts) if parts else "暂无相关参考内容"


# 全局实例
content_reference_scraper = ContentReferenceScraper()