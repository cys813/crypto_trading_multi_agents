"""
Decrypt新闻源适配器
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


class DecryptAdapter(NewsSourceAdapter):
    """Decrypt新闻源适配器"""

    def __init__(self, config: NewsSourceConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self._api_base = "https://api.decrypt.co"
        self._web_base = "https://decrypt.co"
        self._graphql_endpoint = "https://api.decrypt.co/graphql"

    @property
    def source_name(self) -> str:
        return "decrypt"

    @property
    def adapter_type(self) -> str:
        return "decrypt"

    async def connect(self) -> bool:
        """建立连接"""
        try:
            # 测试网站连接
            test_url = f"{self._web_base}/"
            response = await self._make_request(test_url)
            return response is not None

        except Exception as e:
            self.logger.error(f"Decrypt连接失败: {e}")
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
            # Decrypt也使用网页抓取
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
            self.logger.error(f"Decrypt获取新闻失败: {e}")

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
            # 从首页获取新闻
            news_url = f"{self._web_base}/"
            articles = await self._scrape_news_page(news_url, limit)

            if len(articles) < limit:
                # 尝试从更多页面获取
                additional_urls = [
                    f"{self._web_base}/news",
                    f"{self._web_base}/markets",
                    f"{self._web_base}/business"
                ]

                for url in additional_urls:
                    if len(articles) >= limit:
                        break
                    additional_articles = await self._scrape_news_page(url, limit - len(articles))
                    articles.extend(additional_articles)

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
                'Referer': 'https://decrypt.co/',
            }

            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_decrypt_html(html, limit)
                else:
                    self.logger.error(f"HTTP错误: {response.status}")
                    return []

        except Exception as e:
            self.logger.error(f"抓取页面失败: {e}")
            return []

    def _parse_decrypt_html(self, html: str, limit: int) -> List[NewsArticle]:
        """解析Decrypt HTML"""
        articles = []
        soup = BeautifulSoup(html, 'html.parser')

        # Decrypt网站可能使用的多种选择器
        article_selectors = [
            'article[data-testid*="article"]',
            '[data-testid*="story"]',
            '.article-card',
            '.story-card',
            '.news-item',
            'a[href*="/story/"]',
            'a[href*="/article/"]'
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
            title_selectors = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', '[class*="title"]', '[data-testid*="title"]']

            for selector in title_selectors:
                title_element = element.select_one(selector)
                if title_element:
                    title = title_element.get_text(strip=True)
                    break

            if not title or len(title) < 10:
                return None

            # 获取摘要
            summary = ""
            summary_selectors = ['[class*="summary"]', '[class*="excerpt"]', '[class*="description"]', 'p']

            for selector in summary_selectors:
                summary_element = element.select_one(selector)
                if summary_element:
                    summary = summary_element.get_text(strip=True)
                    if len(summary) > 20:  # 确保摘要有意义
                        break

            # 获取时间
            published_at = datetime.now()
            time_element = element.find('time')
            if time_element:
                time_str = time_element.get('datetime') or time_element.get_text(strip=True)
                if time_str:
                    published_at = self._parse_time(time_str)

            # 获取作者
            author = None
            author_element = element.find('[class*="author"]')
            if author_element:
                author = author_element.get_text(strip=True)

            # 生成文章ID
            article_id = f"decrypt_{hash(full_url) % 1000000}"

            # 分类
            category = self._categorize_by_title(title)

            # 提取标签
            tags = self._extract_tags(element)

            article = NewsArticle(
                id=article_id,
                title=title,
                content="",
                summary=summary,
                author=author,
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
                "%b %d, %Y",
                "%d %b %Y"
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue

            # 处理相对时间
            relative_patterns = [
                (r'(\d+)\s*hours?\s*ago', lambda x: datetime.now() - timedelta(hours=int(x.group(1)))),
                (r'(\d+)\s*days?\s*ago', lambda x: datetime.now() - timedelta(days=int(x.group(1)))),
                (r'(\d+)\s*minutes?\s*ago', lambda x: datetime.now() - timedelta(minutes=int(x.group(1)))),
            ]

            for pattern, handler in relative_patterns:
                match = re.search(pattern, time_str, re.IGNORECASE)
                if match:
                    return handler(match)

            # 如果都失败了，返回当前时间
            return datetime.now()

        except Exception:
            return datetime.now()

    def _categorize_by_title(self, title: str) -> NewsCategory:
        """根据标题分类"""
        title_lower = title.lower()

        # Decrypt特有的分类规则
        if any(word in title_lower for word in ['price', 'market', 'trading', 'analysis', 'chart', 'price']):
            return NewsCategory.MARKET_ANALYSIS
        elif any(word in title_lower for word in ['regulation', 'sec', 'law', 'legal', 'government', 'policy']):
            return NewsCategory.REGULATION
        elif any(word in title_lower for word in ['hack', 'security', 'breach', 'exploit', 'vulnerability', 'scam']):
            return NewsCategory.SECURITY
        elif any(word in title_lower for word in ['tech', 'development', 'upgrade', 'protocol', 'ethereum', 'bitcoin', 'defi', 'nft']):
            return NewsCategory.TECHNOLOGY
        elif any(word in title_lower for word in ['adoption', 'institutional', 'investment', 'fund', 'etf']):
            return NewsCategory.ADOPTION
        elif any(word in title_lower for word in ['breaking', 'alert', 'urgent', 'just in', 'developing']):
            return NewsCategory.BREAKING
        else:
            return NewsCategory.GENERAL

    def _extract_tags(self, element) -> List[str]:
        """提取标签"""
        tags = []

        # 查找标签元素
        tag_selectors = [
            '[class*="tag"]',
            '[class*="category"]',
            '[class*="topic"]'
        ]

        for selector in tag_selectors:
            tag_elements = element.select(selector)
            for tag_element in tag_elements:
                tag = tag_element.get_text(strip=True)
                if tag and len(tag) > 1 and tag.lower() not in ['read more', 'continue reading']:
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
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
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
NewsSourceAdapterFactory.register_adapter("decrypt", DecryptAdapter)