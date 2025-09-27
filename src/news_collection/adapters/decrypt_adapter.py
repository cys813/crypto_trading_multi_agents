import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import re

from .base_adapter import BaseNewsAdapter
from ..models import NewsArticle, NewsCategory, ConnectionStatus, RateLimitInfo, NewsSourceType


class DecryptAdapter(BaseNewsAdapter):
    """Decrypt news adapter implementation."""

    def __init__(self, source_config):
        super().__init__(source_config)
        self.api_base_url = "https://api.decrypt.co/v1"
        self.news_endpoint = "/articles"

    @property
    def source_name(self) -> str:
        return "Decrypt"

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
        Fetch news articles from Decrypt.

        Args:
            limit: Maximum number of articles to fetch
            category: Filter by news category
            keywords: Filter by keywords
            since: Fetch articles published since this time

        Returns:
            List of news articles
        """
        try:
            # Decrypt API endpoint for articles
            url = f"{self.api_base_url}{self.news_endpoint}"

            params = {
                "limit": min(limit, 50),  # Respect API limits
                "sort": "published_at",
                "order": "desc",
            }

            # Add category filter if specified
            if category:
                category_mapping = self._get_category_mapping()
                if category in category_mapping:
                    params["category"] = category_mapping[category]

            # Add keywords filter if specified
            if keywords:
                params["search"] = " ".join(keywords)

            # Add time filter if specified
            if since:
                params["from"] = since.isoformat()

            self.logger.debug(f"Fetching news from Decrypt with params: {params}")

            # Make the request
            data = await self._make_request(url, params=params)

            # Parse articles
            articles = []
            if data and isinstance(data, dict) and "data" in data:
                article_list = data["data"]
                if isinstance(article_list, list):
                    for item in article_list[:limit]:
                        try:
                            article = self._parse_article(item)
                            if self._should_include_article(article, category, keywords, since):
                                articles.append(article)
                        except Exception as e:
                            self.logger.error(f"Error parsing article: {str(e)}")
                            continue

            self.logger.info(f"Fetched {len(articles)} articles from Decrypt")
            return articles

        except Exception as e:
            self.logger.error(f"Error fetching news from Decrypt: {str(e)}")
            raise

    async def test_connection(self) -> ConnectionStatus:
        """Test connection to Decrypt API."""
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
        # Decrypt doesn't provide rate limit info in headers
        # Return default values
        return RateLimitInfo(
            source_name=self.source_name,
            requests_remaining=self.source_config.rate_limit_per_minute,
            requests_limit=self.source_config.rate_limit_per_minute,
            reset_time=datetime.now(),
        )

    def _parse_article(self, raw_data: Dict[str, Any]) -> NewsArticle:
        """Parse raw Decrypt article data."""
        # Extract basic fields
        title = raw_data.get("title", "")
        content = raw_data.get("content", "") or raw_data.get("body", "")
        url = raw_data.get("url", "") or raw_data.get("permalink", "")

        # Extract author information
        author = None
        if "author" in raw_data:
            if isinstance(raw_data["author"], dict):
                author = raw_data["author"].get("name")
            elif isinstance(raw_data["author"], str):
                author = raw_data["author"]

        # Parse publication date
        published_at = self._parse_date(raw_data.get("published_at") or raw_data.get("date"))

        # Extract summary/excerpt
        summary = raw_data.get("excerpt", "") or raw_data.get("summary", "")
        if not summary and len(content) > 200:
            summary = content[:200] + "..."

        # Extract tags
        tags = []
        if "tags" in raw_data:
            if isinstance(raw_data["tags"], list):
                tags = [tag if isinstance(tag, str) else tag.get("name", "")
                       for tag in raw_data["tags"] if tag]

        # Extract categories
        if "categories" in raw_data and isinstance(raw_data["categories"], list):
            category_names = [cat if isinstance(cat, str) else cat.get("name", "")
                             for cat in raw_data["categories"] if cat]
            tags.extend(category_names)

        # Determine category
        category = self._determine_category(raw_data)

        # Generate ID
        article_id = f"decrypt_{raw_data.get('id', '') or hash(title + url)}"

        return NewsArticle(
            id=article_id,
            title=title,
            content=content,
            summary=summary,
            url=url,
            author=author,
            published_at=published_at,
            source=NewsSourceType.DECRYPT,
            category=category,
            tags=tags,
            metadata={
                "raw_data": raw_data,
                "source_specific": {
                    "featured_image": raw_data.get("featured_image"),
                    "reading_time": raw_data.get("reading_time"),
                    "word_count": raw_data.get("word_count"),
                    "slug": raw_data.get("slug"),
                    "status": raw_data.get("status"),
                },
            },
        )

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string from Decrypt API."""
        if not date_str:
            return None

        try:
            # Try different date formats
            formats = [
                "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO with microseconds
                "%Y-%m-%dT%H:%M:%SZ",     # ISO without microseconds
                "%Y-%m-%d %H:%M:%S",      # Standard datetime
                "%Y-%m-%d",               # Date only
            ]

            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except ValueError:
                    continue

            # If no format matches, try fromisoformat
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt

        except Exception as e:
            self.logger.error(f"Error parsing date '{date_str}': {str(e)}")
            return None

    def _determine_category(self, raw_data: Dict[str, Any]) -> NewsCategory:
        """Determine article category based on content."""
        title = raw_data.get("title", "").lower()
        content = raw_data.get("content", "") or raw_data.get("body", "")
        content = content.lower()

        # Check for explicit category in the data
        if "category" in raw_data:
            category_data = raw_data["category"]
            if isinstance(category_data, dict):
                category_name = category_data.get("name", "").lower()
            elif isinstance(category_data, str):
                category_name = category_data.lower()
            else:
                category_name = ""

            category_mapping = {
                "markets": NewsCategory.MARKET_NEWS,
                "technology": NewsCategory.TECHNOLOGY,
                "regulation": NewsCategory.REGULATION,
                "security": NewsCategory.SECURITY,
                "adoption": NewsCategory.ADOPTION,
                "defi": NewsCategory.DEFI,
                "nft": NewsCategory.NFT,
                "exchanges": NewsCategory.EXCHANGE,
                "mining": NewsCategory.MINING,
                "trading": NewsCategory.TRADING,
                "business": NewsCategory.ADOPTION,
                "policy": NewsCategory.REGULATION,
            }

            for key, value in category_mapping.items():
                if key in category_name:
                    return value

        # Check categories array
        if "categories" in raw_data and isinstance(raw_data["categories"], list):
            for category in raw_data["categories"]:
                if isinstance(category, dict):
                    category_name = category.get("name", "").lower()
                else:
                    category_name = str(category).lower()

                category_mapping = {
                    "markets": NewsCategory.MARKET_NEWS,
                    "technology": NewsCategory.TECHNOLOGY,
                    "regulation": NewsCategory.REGULATION,
                    "security": NewsCategory.SECURITY,
                    "adoption": NewsCategory.ADOPTION,
                    "defi": NewsCategory.DEFI,
                    "nft": NewsCategory.NFT,
                    "exchanges": NewsCategory.EXCHANGE,
                    "mining": NewsCategory.MINING,
                    "trading": NewsCategory.TRADING,
                }

                for key, value in category_mapping.items():
                    if key in category_name:
                        return value

        # Fallback to content analysis
        tags = raw_data.get("tags", [])
        tag_names = []
        if isinstance(tags, list):
            tag_names = [tag if isinstance(tag, str) else tag.get("name", "").lower()
                        for tag in tags if tag]

        text_to_analyze = f"{title} {content} {' '.join(tag_names)}"

        # Category keywords
        category_keywords = {
            NewsCategory.MARKET_NEWS: [
                "market", "price", "trading", "bull", "bear", "analysis", "chart",
                "investment", "crypto market", "market analysis", "price prediction"
            ],
            NewsCategory.TECHNOLOGY: [
                "technology", "tech", "blockchain", "protocol", "development",
                "innovation", "upgrade", "blockchain technology", "smart contract", "web3"
            ],
            NewsCategory.REGULATION: [
                "regulation", "regulator", "law", "legal", "compliance", "sec",
                "government", "policy", "legal framework", "regulatory"
            ],
            NewsCategory.SECURITY: [
                "security", "hack", "breach", "vulnerability", "exploit", "malware",
                "safety", "cybersecurity", "security breach", "crypto security"
            ],
            NewsCategory.ADOPTION: [
                "adoption", "mainstream", "institutional", "enterprise", "corporate",
                "business", "mass adoption", "corporate adoption", "institutional investment"
            ],
            NewsCategory.DEFI: [
                "defi", "decentralized finance", "yield", "liquidity", "pool",
                "lending", "borrowing", "decentralized", "defi protocol", "yield farming"
            ],
            NewsCategory.NFT: [
                "nft", "non-fungible", "digital art", "collectible", "metaverse",
                "web3", "nfts", "digital collectibles", "nft marketplace"
            ],
            NewsCategory.EXCHANGE: [
                "exchange", "listing", "delisting", "trading platform", "binance",
                "coinbase", "crypto exchange", "exchange listing", "trading platform"
            ],
            NewsCategory.MINING: [
                "mining", "miner", "hashrate", "proof of work", "pow", "asic",
                "gpu", "crypto mining", "bitcoin mining", "mining rig"
            ],
            NewsCategory.TRADING: [
                "trading", "trade", "order", "volume", "liquidity", "exchange",
                "broker", "crypto trading", "day trading", "swing trading"
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
        """Get mapping of internal categories to Decrypt categories."""
        return {
            NewsCategory.MARKET_NEWS: "markets",
            NewsCategory.TECHNOLOGY: "technology",
            NewsCategory.REGULATION: "regulation",
            NewsCategory.SECURITY: "security",
            NewsCategory.ADOPTION: "adoption",
            NewsCategory.DEFI: "defi",
            NewsCategory.NFT: "nft",
            NewsCategory.EXCHANGE: "exchanges",
            NewsCategory.MINING: "mining",
            NewsCategory.TRADING: "trading",
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
        """Get authentication headers for Decrypt API."""
        # Decrypt doesn't require authentication for basic news access
        return {}

    async def fetch_by_category(self, category: NewsCategory, limit: int = 10) -> List[NewsArticle]:
        """Fetch articles by specific category."""
        return await self.fetch_news(limit=limit, category=category)

    async def search_news(self, query: str, limit: int = 10) -> List[NewsArticle]:
        """Search for news articles."""
        return await self.fetch_news(limit=limit, keywords=[query])

    async def fetch_latest_news(self, limit: int = 10) -> List[NewsArticle]:
        """Fetch latest news articles."""
        return await self.fetch_news(limit=limit)

    async def fetch_featured_news(self, limit: int = 10) -> List[NewsArticle]:
        """Fetch featured news articles."""
        url = f"{self.api_base_url}{self.news_endpoint}"
        params = {
            "limit": min(limit, 50),
            "featured": "true",
            "sort": "published_at",
            "order": "desc",
        }

        data = await self._make_request(url, params=params)

        articles = []
        if data and isinstance(data, dict) and "data" in data:
            article_list = data["data"]
            if isinstance(article_list, list):
                for item in article_list[:limit]:
                    try:
                        article = self._parse_article(item)
                        articles.append(article)
                    except Exception as e:
                        self.logger.error(f"Error parsing featured article: {str(e)}")
                        continue

        return articles