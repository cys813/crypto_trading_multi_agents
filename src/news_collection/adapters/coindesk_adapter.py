import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import re

from .base_adapter import BaseNewsAdapter
from ..models import NewsArticle, NewsCategory, ConnectionStatus, RateLimitInfo, NewsSourceType


class CoinDeskAdapter(BaseNewsAdapter):
    """CoinDesk news adapter implementation."""

    def __init__(self, source_config):
        super().__init__(source_config)
        self.api_base_url = "https://api.coindesk.com/v1"
        self.news_endpoint = "/latest headlines"

    @property
    def source_name(self) -> str:
        return "CoinDesk"

    @property
    def supported_categories(self) -> List[NewsCategory]:
        return [
            NewsCategory.MARKET_NEWS,
            NewsCategory.TECHNOLOGY,
            NewsCategory.REGULATION,
            NewsCategory.SECURITY,
            NewsCategory.ADOPTION,
            NewsCategory.DEFI,
            NewsCategory.NFT,
            NewsCategory.EXCHANGE,
            NewsCategory.MINING,
            NewsCategory.TRADING,
        ]

    async def fetch_news(
        self,
        limit: int = 10,
        category: Optional[NewsCategory] = None,
        keywords: Optional[List[str]] = None,
        since: Optional[datetime] = None,
    ) -> List[NewsArticle]:
        """
        Fetch news articles from CoinDesk.

        Args:
            limit: Maximum number of articles to fetch
            category: Filter by news category
            keywords: Filter by keywords
            since: Fetch articles published since this time

        Returns:
            List of news articles
        """
        try:
            # CoinDesk API endpoint for headlines
            url = f"{self.api_base_url}{self.news_endpoint}"

            params = {
                "limit": min(limit, 50),  # CoinDesk might have a limit
            }

            # Add category filter if specified
            if category:
                category_mapping = self._get_category_mapping()
                if category in category_mapping:
                    params["category"] = category_mapping[category]

            # Add keywords filter if specified
            if keywords:
                params["q"] = " OR ".join(keywords)

            # Add time filter if specified
            if since:
                params["since"] = since.isoformat()

            self.logger.debug(f"Fetching news from CoinDesk with params: {params}")

            # Make the request
            data = await self._make_request(url, params=params)

            # Parse articles
            articles = []
            if data and "data" in data and "items" in data["data"]:
                for item in data["data"]["items"][:limit]:
                    try:
                        article = self._parse_article(item)
                        if self._should_include_article(article, category, keywords, since):
                            articles.append(article)
                    except Exception as e:
                        self.logger.error(f"Error parsing article: {str(e)}")
                        continue

            self.logger.info(f"Fetched {len(articles)} articles from CoinDesk")
            return articles

        except Exception as e:
            self.logger.error(f"Error fetching news from CoinDesk: {str(e)}")
            raise

    async def test_connection(self) -> ConnectionStatus:
        """Test connection to CoinDesk API."""
        start_time = datetime.now()
        try:
            # Test with a simple request
            test_url = f"{self.api_base_url}{self.news_endpoint}"
            params = {"limit": 1}

            await self._make_request(test_url, params=params)

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            return ConnectionStatus(
                source_name=self.source_name,
                is_connected=True,
                response_time_ms=response_time,
                last_checked=datetime.now(),
            )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            return ConnectionStatus(
                source_name=self.source_name,
                is_connected=False,
                response_time_ms=response_time,
                last_checked=datetime.now(),
                error_message=str(e),
                consecutive_failures=self.get_failure_count(),
            )

    async def get_rate_limit_info(self) -> RateLimitInfo:
        """Get current rate limit information."""
        # CoinDesk doesn't provide rate limit info in headers
        # Return default values
        return RateLimitInfo(
            source_name=self.source_name,
            requests_remaining=self.source_config.rate_limit_per_minute,
            requests_limit=self.source_config.rate_limit_per_minute,
            reset_time=datetime.now(),
        )

    def _parse_article(self, raw_data: Dict[str, Any]) -> NewsArticle:
        """Parse raw CoinDesk article data."""
        # Extract basic fields
        title = raw_data.get("title", "")
        content = raw_data.get("body", "")
        url = raw_data.get("url", "")
        author = raw_data.get("author", {}).get("name") if raw_data.get("author") else None

        # Parse publication date
        published_at = self._parse_date(raw_data.get("published_at"))

        # Extract summary
        summary = raw_data.get("summary", "") or raw_data.get("description", "")

        # Extract tags
        tags = []
        if "tags" in raw_data and isinstance(raw_data["tags"], list):
            tags = [tag.get("name", "") for tag in raw_data["tags"] if tag.get("name")]

        # Determine category
        category = self._determine_category(raw_data)

        # Generate ID
        article_id = f"coindesk_{raw_data.get('id', '') or hash(title + url)}"

        return NewsArticle(
            id=article_id,
            title=title,
            content=content,
            summary=summary,
            url=url,
            author=author,
            published_at=published_at,
            source=NewsSourceType.COINDESK,
            category=category,
            tags=tags,
            metadata={
                "raw_data": raw_data,
                "source_specific": {
                    "image_url": raw_data.get("image_url"),
                    "video_url": raw_data.get("video_url"),
                    "reading_time": raw_data.get("reading_time"),
                },
            },
        )

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string from CoinDesk API."""
        if not date_str:
            return None

        try:
            # CoinDesk typically uses ISO format
            if "T" in date_str:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(date_str)

            # Ensure timezone
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            return dt

        except Exception as e:
            self.logger.error(f"Error parsing date '{date_str}': {str(e)}")
            return None

    def _determine_category(self, raw_data: Dict[str, Any]) -> NewsCategory:
        """Determine article category based on content."""
        title = raw_data.get("title", "").lower()
        content = raw_data.get("body", "").lower()
        tags = raw_data.get("tags", [])

        # Extract tag names
        tag_names = []
        if isinstance(tags, list):
            tag_names = [tag.get("name", "").lower() for tag in tags if isinstance(tag, dict)]

        text_to_analyze = f"{title} {content} {' '.join(tag_names)}"

        # Category keywords
        category_keywords = {
            NewsCategory.MARKET_NEWS: [
                "market", "price", "trading", "bull", "bear", "analysis", "chart", "investment"
            ],
            NewsCategory.TECHNOLOGY: [
                "technology", "tech", "blockchain", "protocol", "development", "innovation", "upgrade"
            ],
            NewsCategory.REGULATION: [
                "regulation", "regulator", "law", "legal", "compliance", "sec", "government"
            ],
            NewsCategory.SECURITY: [
                "security", "hack", "breach", "vulnerability", "exploit", "malware", "safety"
            ],
            NewsCategory.ADOPTION: [
                "adoption", "mainstream", "institutional", "enterprise", "corporate", "business"
            ],
            NewsCategory.DEFI: [
                "defi", "decentralized finance", "yield", "liquidity", "pool", "lending", "borrowing"
            ],
            NewsCategory.NFT: [
                "nft", "non-fungible", "digital art", "collectible", "metaverse", "web3"
            ],
            NewsCategory.EXCHANGE: [
                "exchange", "listing", "delisting", "trading platform", "binance", "coinbase"
            ],
            NewsCategory.MINING: [
                "mining", "miner", "hashrate", "proof of work", "pow", "asic", "gpu"
            ],
        }

        # Count matches for each category
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_to_analyze)
            if score > 0:
                category_scores[category] = score

        # Return category with highest score
        if category_scores:
            return max(category_scores, key=category_scores.get)

        return NewsCategory.MARKET_NEWS  # Default

    def _get_category_mapping(self) -> Dict[NewsCategory, str]:
        """Get mapping of internal categories to CoinDesk categories."""
        return {
            NewsCategory.MARKET_NEWS: "markets",
            NewsCategory.TECHNOLOGY: "tech",
            NewsCategory.REGULATION: "policy",
            NewsCategory.SECURITY: "security",
            NewsCategory.DEFI: "defi",
            NewsCategory.NFT: "nft",
        }

    def _should_include_article(
        self,
        article: NewsArticle,
        category: Optional[NewsCategory],
        keywords: Optional[List[str]],
        since: Optional[datetime],
    ) -> bool:
        """Check if article should be included based on filters."""
        # Category filter
        if category and article.category != category:
            return False

        # Keywords filter
        if keywords:
            text_to_search = f"{article.title} {article.content} {' '.join(article.tags)}".lower()
            keyword_matches = any(
                keyword.lower() in text_to_search
                for keyword in keywords
            )
            if not keyword_matches:
                return False

        # Time filter
        if since and article.published_at:
            if article.published_at < since:
                return False

        return True

    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for CoinDesk API."""
        # CoinDesk doesn't require authentication for basic news access
        return {}

    async def fetch_by_category(self, category: NewsCategory, limit: int = 10) -> List[NewsArticle]:
        """Fetch articles by specific category."""
        return await self.fetch_news(limit=limit, category=category)

    async def search_news(self, query: str, limit: int = 10) -> List[NewsArticle]:
        """Search for news articles."""
        return await self.fetch_news(limit=limit, keywords=[query])