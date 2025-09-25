"""
CoinDesk新闻源适配器
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import aiohttp
import logging
from bs4 import BeautifulSoup

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


class CoinDeskAdapter(NewsSourceAdapter):
    """CoinDesk新闻源适配器"""

    def __init__(self, config: NewsSourceConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self._api_base = "https://api.coindesk.com/v1"
        self._web_base = "https://www.coindesk.com"

    @property
    def source_name(self) -> str:
        return "coindesk"

    @property
    def adapter_type(self) -> str:
        return "coindesk"

    async def connect(self) -> bool:
        """建立连接"""
        try:
            # 测试API连接
            test_url = f"{self._api_base}/bpi/currentprice.json"
            response = await self._make_request(test_url)
            return response is not None

        except Exception as e:
            self.logger.error(f"CoinDesk连接失败: {e}")
            return False

    async def disconnect(self) -> bool:
        """断开连接"""
        # CoinDesk适配器不需要特殊的断开操作
        return True

    async def health_check(self) -> HealthStatus:
        """健康检查"""
        start_time = datetime.now()

        try:
            # 测试基本连接
            test_url = f"{self._api_base}/bpi/currentprice.json"
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
                    error_message="API请求失败"
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
            # CoinDesk的API有限制，这里使用网页抓取作为示例
            # 实际使用时应该申请官方API
            news_url = f"{self._web_base}/"

            # 获取新闻列表
            if query.keywords:
                # 如果有关键词，尝试搜索
                search_url = f"{self._web_base}/search?q={'+'.join(query.keywords)}"
                articles = await self._scrape_news_page(search_url, query.limit)
            else:
                # 获取最新新闻
                articles = await self._scrape_news_page(news_url, query.limit)

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
            self.logger.error(f"CoinDesk获取新闻失败: {e}")

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

    async def _scrape_news_page(self, url: str, limit: int) -> List[NewsArticle]:
        """抓取新闻页面"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_news_html(html, limit)
                else:
                    self.logger.error(f"HTTP错误: {response.status}")
                    return []

        except Exception as e:
            self.logger.error(f"抓取页面失败: {e}")
            return []

    def _parse_news_html(self, html: str, limit: int) -> List[NewsArticle]:
        """解析新闻HTML"""
        articles = []
        soup = BeautifulSoup(html, 'html.parser')

        # CoinDesk网站结构可能变化，这里提供基本的解析逻辑
        # 查找新闻文章链接
        news_links = soup.find_all('a', href=True)

        for link in news_links[:limit * 2]:  # 获取更多链接然后过滤
            href = link.get('href', '')
            title = link.get_text(strip=True)

            # 过滤新闻链接
            if self._is_news_link(href) and title and len(title) > 20:
                # 生成文章ID
                article_id = f"coindesk_{hash(href) % 1000000}"

                article = NewsArticle(
                    id=article_id,
                    title=title,
                    content="",
                    source=self.source_name,
                    url=self._normalize_url(href),
                    published_at=datetime.now(),
                    category=self._categorize_by_title(title),
                    metadata={
                        "scraped_url": href,
                        "scraped_at": datetime.now().isoformat()
                    }
                )

                articles.append(article)

                if len(articles) >= limit:
                    break

        return articles

    def _is_news_link(self, href: str) -> bool:
        """判断是否为新闻链接"""
        if not href or href.startswith('#'):
            return False

        # 排除非新闻页面
        excluded_paths = ['/search', '/author', '/tag', '/category', '/video', '/podcast']
        for path in excluded_paths:
            if path in href:
                return False

        # 包含新闻相关的路径
        news_keywords = ['2024', '2023', 'bitcoin', 'crypto', 'ethereum', 'blockchain', 'defi', 'nft']
        return any(keyword in href.lower() for keyword in news_keywords)

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

    def _categorize_by_title(self, title: str) -> NewsCategory:
        """根据标题分类"""
        title_lower = title.lower()

        if any(word in title_lower for word in ['hack', 'security', 'breach', 'exploit']):
            return NewsCategory.SECURITY
        elif any(word in title_lower for word in ['price', 'market', 'trading', 'analysis']):
            return NewsCategory.MARKET_ANALYSIS
        elif any(word in title_lower for word in ['regulation', 'law', 'legal', 'government']):
            return NewsCategory.REGULATION
        elif any(word in title_lower for word in ['tech', 'development', 'upgrade', 'protocol']):
            return NewsCategory.TECHNOLOGY
        elif any(word in title_lower for word in ['adoption', 'institutional', 'investment']):
            return NewsCategory.ADOPTION
        elif any(word in title_lower for word in ['breaking', 'alert', 'urgent']):
            return NewsCategory.BREAKING
        else:
            return NewsCategory.GENERAL

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
        text_to_search = f"{article.title} {article.content} {' '.join(article.tags)}".lower()
        return any(keyword.lower() in text_to_search for keyword in keywords)

    async def _make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[Dict[str, Any]]:
        """重写请求方法以适配CoinDesk"""
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    if response.content_type == 'application/json':
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
NewsSourceAdapterFactory.register_adapter("coindesk", CoinDeskAdapter)