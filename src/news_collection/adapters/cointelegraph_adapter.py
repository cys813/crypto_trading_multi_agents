"""
CoinTelegraph新闻源适配器
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import aiohttp
import logging
from bs4 import BeautifulSoup
import json
import re

from ..models.base import (
    NewsArticle,
    NewsSourceConfig,
    HealthStatus,
    NewsQuery,
    NewsQueryResult,
    NewsCategory,
    NewsSourceStatus
)
from ..core.adapter import NewsSourceAdapter
from ..core.error_handler import ErrorContext, ErrorType


class CoinTelegraphAdapter(NewsSourceAdapter):
    """CoinTelegraph新闻源适配器"""

    def __init__(self, config: NewsSourceConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self._api_base = "https://cointelegraph.com/api/v1"
        self._web_base = "https://cointelegraph.com"
        self._editor_api = "https://editorial.cointelegraph.com/api"

    @property
    def source_name(self) -> str:
        return "cointelegraph"

    @property
    def adapter_type(self) -> str:
        return "cointelegraph"

    async def connect(self) -> bool:
        """建立连接"""
        try:
            # 测试API连接
            test_url = f"{self._web_base}/"
            response = await self._make_request(test_url)
            return response is not None

        except Exception as e:
            self.logger.error(f"CoinTelegraph连接失败: {e}")
            return False

    async def disconnect(self) -> bool:
        """断开连接"""
        return True

    async def health_check(self) -> HealthStatus:
        """健康检查"""
        start_time = datetime.now()

        try:
            # 测试网站连接
            test_url = f"{self._web_base}/"
            response = await self._make_request(test_url)

            if response:
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                return HealthStatus(
                    is_healthy=True,
                    response_time=response_time,
                    status=NewsSourceStatus.ONLINE,
                    last_check=start_time
                )
            else:
                return HealthStatus(
                    is_healthy=False,
                    response_time=0,
                    status=NewsSourceStatus.OFFLINE,
                    last_check=start_time,
                    error_message="网站请求失败"
                )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            return HealthStatus(
                is_healthy=False,
                response_time=response_time,
                status=NewsSourceStatus.OFFLINE,
                last_check=start_time,
                error_message=str(e)
            )

    async def fetch_news(self, query: NewsQuery) -> NewsQueryResult:
        """获取新闻"""
        start_time = datetime.now()
        articles = []
        errors = []

        try:
            # CoinTelegraph也使用网页抓取
            if query.keywords:
                # 搜索新闻
                search_url = f"{self._web_base}/search?q={'+'.join(query.keywords)}"
                articles = await self._scrape_search_results(search_url, query.limit)
            else:
                # 获取最新新闻
                articles = await self._scrape_latest_news(query.limit)

            # 过滤文章
            filtered_articles = self._filter_articles(articles, query)

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return NewsQueryResult(
                articles=filtered_articles,
                total_count=len(filtered_articles),
                has_more=False,
                query=query,
                execution_time=execution_time,
                sources_used=[self.source_name],
                errors=errors
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            errors.append(f"获取新闻失败: {str(e)}")
            self.logger.error(f"CoinTelegraph获取新闻失败: {e}")

            return NewsQueryResult(
                articles=[],
                total_count=0,
                has_more=False,
                query=query,
                execution_time=execution_time,
                sources_used=[],
                errors=errors
            )

    async def get_latest_news(self, limit: int = 20) -> List[NewsArticle]:
        """获取最新新闻"""
        try:
            query = NewsQuery(limit=limit)
            result = await self.fetch_news(query)
            return result.articles

        except Exception as e:
            self.logger.error(f"获取最新新闻失败: {e}")
            return []

    async def search_news(self, keywords: List[str], limit: int = 50) -> List[NewsArticle]:
        """搜索新闻"""
        try:
            query = NewsQuery(keywords=keywords, limit=limit)
            result = await self.fetch_news(query)
            return result.articles

        except Exception as e:
            self.logger.error(f"搜索新闻失败: {e}")
            return []

    async def _scrape_latest_news(self, limit: int) -> List[NewsArticle]:
        """抓取最新新闻"""
        try:
            # 尝试从首页获取新闻
            news_url = f"{self._web_base}/"
            articles = await self._scrape_news_page(news_url, limit)

            if len(articles) < limit:
                # 如果首页文章不够，尝试从新闻分类页面获取
                category_urls = [
                    f"{self._web_base}/tags/markets",
                    f"{self._web_base}/tags/industry",
                    f"{self._web_base}/tags/regulation"
                ]

                for category_url in category_urls:
                    if len(articles) >= limit:
                        break
                    category_articles = await self._scrape_news_page(category_url, limit - len(articles))
                    articles.extend(category_articles)

            return articles[:limit]

        except Exception as e:
            self.logger.error(f"抓取最新新闻失败: {e}")
            return []

    async def _scrape_search_results(self, search_url: str, limit: int) -> List[NewsArticle]:
        """抓取搜索结果"""
        try:
            return await self._scrape_news_page(search_url, limit)

        except Exception as e:
            self.logger.error(f"抓取搜索结果失败: {e}")
            return []

    async def _scrape_news_page(self, url: str, limit: int) -> List[NewsArticle]:
        """抓取新闻页面"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_cointelegraph_html(html, limit)
                else:
                    self.logger.error(f"HTTP错误: {response.status}")
                    return []

        except Exception as e:
            self.logger.error(f"抓取页面失败: {e}")
            return []

    def _parse_cointelegraph_html(self, html: str, limit: int) -> List[NewsArticle]:
        """解析CoinTelegraph HTML"""
        articles = []
        soup = BeautifulSoup(html, 'html.parser')

        # 尝试查找新闻文章的多种选择器
        article_selectors = [
            'article[data-post-id]',
            '.posts-listing__item',
            '.main-news-item',
            '[class*="news-card"]',
            '[class*="article-item"]',
            'a[href*="/news/"]'
        ]

        for selector in article_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    articles = self._extract_articles_from_elements(elements, limit)
                    break
            except Exception as e:
                self.logger.warning(f"选择器 {selector} 解析失败: {e}")
                continue

        return articles

    def _extract_articles_from_elements(self, elements: List[Any], limit: int) -> List[NewsArticle]:
        """从HTML元素中提取文章"""
        articles = []

        for element in elements[:limit * 2]:
            try:
                article = self._extract_article_from_element(element)
                if article:
                    articles.append(article)
                    if len(articles) >= limit:
                        break
            except Exception as e:
                self.logger.warning(f"提取文章失败: {e}")
                continue

        return articles

    def _extract_article_from_element(self, element) -> Optional[NewsArticle]:
        """从HTML元素中提取单篇文章"""
        try:
            # 获取链接
            link = None
            if element.name == 'a':
                link = element.get('href')
            else:
                link_element = element.find('a')
                if link_element:
                    link = link_element.get('href')

            if not link:
                return None

            # 标准化URL
            full_url = self._normalize_url(link)

            # 获取标题
            title = None
            title_element = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if title_element:
                title = title_element.get_text(strip=True)
            else:
                # 尝试从其他元素获取标题
                title_element = element.find('[class*="title"]')
                if title_element:
                    title = title_element.get_text(strip=True)
                else:
                    title = element.get_text(strip=True)

            if not title or len(title) < 10:
                return None

            # 获取摘要
            summary = ""
            summary_element = element.find('[class*="summary"]')
            if summary_element:
                summary = summary_element.get_text(strip=True)

            # 获取时间
            published_at = datetime.now()
            time_element = element.find('time')
            if time_element:
                time_str = time_element.get('datetime') or time_element.get_text(strip=True)
                if time_str:
                    published_at = self._parse_time(time_str)

            # 生成文章ID
            article_id = f"cointelegraph_{hash(full_url) % 1000000}"

            # 分类
            category = self._categorize_by_title(title)

            # 提取标签
            tags = self._extract_tags(element)

            article = NewsArticle(
                id=article_id,
                title=title,
                content="",
                summary=summary,
                source=self.source_name,
                url=full_url,
                published_at=published_at,
                category=category,
                tags=tags,
                metadata={
                    "scraped_at": datetime.now().isoformat(),
                    "source_url": link
                }
            )

            return article

        except Exception as e:
            self.logger.warning(f"提取文章信息失败: {e}")
            return None

    def _normalize_url(self, href: str) -> str:
        """标准化URL"""
        if href.startswith('http'):
            return href
        elif href.startswith('//'):
            return f"https:{href}"
        elif href.startswith('/'):
            return f"{self._web_base}{href}"
        else:
            return f"{self._web_base}/{href}"

    def _parse_time(self, time_str: str) -> datetime:
        """解析时间字符串"""
        try:
            # 尝试不同的时间格式
            formats = [
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%B %d, %Y",
                "%b %d, %Y"
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue

            # 如果都失败了，返回当前时间
            return datetime.now()

        except Exception:
            return datetime.now()

    def _categorize_by_title(self, title: str) -> NewsCategory:
        """根据标题分类"""
        title_lower = title.lower()

        # CoinTelegraph特有的分类规则
        if any(word in title_lower for word in ['price', 'market', 'trading', 'analysis', 'chart']):
            return NewsCategory.MARKET_ANALYSIS
        elif any(word in title_lower for word in ['regulation', 'sec', 'law', 'legal', 'government']):
            return NewsCategory.REGULATION
        elif any(word in title_lower for word in ['hack', 'security', 'breach', 'exploit', 'vulnerability']):
            return NewsCategory.SECURITY
        elif any(word in title_lower for word in ['tech', 'development', 'upgrade', 'protocol', 'ethereum', 'bitcoin']):
            return NewsCategory.TECHNOLOGY
        elif any(word in title_lower for word in ['adoption', 'institutional', 'investment', 'fund']):
            return NewsCategory.ADOPTION
        elif any(word in title_lower for word in ['breaking', 'alert', 'urgent', 'just in']):
            return NewsCategory.BREAKING
        else:
            return NewsCategory.GENERAL

    def _extract_tags(self, element) -> List[str]:
        """提取标签"""
        tags = []

        # 查找标签元素
        tag_elements = element.find_all(['span', 'div'], class_=lambda x: x and 'tag' in x.lower())
        for tag_element in tag_elements:
            tag = tag_element.get_text(strip=True)
            if tag and len(tag) > 1:
                tags.append(tag)

        return tags

    def _filter_articles(self, articles: List[NewsArticle], query: NewsQuery) -> List[NewsArticle]:
        """过滤文章"""
        filtered = articles

        # 按分类过滤
        if query.categories:
            filtered = [a for a in filtered if a.category in query.categories]

        # 按时间过滤
        if query.start_date:
            filtered = [a for a in filtered if a.published_at and a.published_at >= query.start_date]

        if query.end_date:
            filtered = [a for a in filtered if a.published_at and a.published_at <= query.end_date]

        # 按关键词过滤
        if query.keywords:
            filtered = [a for a in filtered if self._matches_keywords(a, query.keywords)]

        return filtered[:query.limit]

    def _matches_keywords(self, article: NewsArticle, keywords: List[str]) -> bool:
        """检查文章是否匹配关键词"""
        text_to_search = f"{article.title} {article.summary} {article.content} {' '.join(article.tags)}".lower()
        return any(keyword.lower() in text_to_search for keyword in keywords)

    async def _make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[Dict[str, Any]]:
        """重写请求方法"""
        try:
            # 添加更真实的用户代理
            headers = kwargs.get('headers', {})
            headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            })
            kwargs['headers'] = headers

            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    if response.content_type and 'application/json' in response.content_type:
                        return await response.json()
                    else:
                        return {"content": await response.text()}
                else:
                    self.logger.error(f"HTTP错误: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"请求失败: {e}")
            return None


# 注册适配器
NewsSourceAdapterFactory.register_adapter("cointelegraph", CoinTelegraphAdapter)