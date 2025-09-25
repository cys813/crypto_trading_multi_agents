from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import logging
from ..models import (
    NewsArticle,
    NewsSource,
    NewsCategory,
    ConnectionStatus,
    RateLimitInfo,
)


class BaseNewsAdapter(ABC):
    """Base class for all news source adapters."""

    def __init__(self, source_config: NewsSource):
        self.source_config = source_config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._session = None
        self._rate_limiter = None
        self._last_request_time = None
        self._consecutive_failures = 0
        self._is_healthy = True

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of the news source."""
        pass

    @property
    @abstractmethod
    def supported_categories(self) -> List[NewsCategory]:
        """Return list of supported news categories."""
        pass

    @abstractmethod
    async def fetch_news(
        self,
        limit: int = 10,
        category: Optional[NewsCategory] = None,
        keywords: Optional[List[str]] = None,
        since: Optional[datetime] = None,
    ) -> List[NewsArticle]:
        """
        Fetch news articles from the source.

        Args:
            limit: Maximum number of articles to fetch
            category: Filter by news category
            keywords: Filter by keywords
            since: Fetch articles published since this time

        Returns:
            List of news articles
        """
        pass

    @abstractmethod
    async def test_connection(self) -> ConnectionStatus:
        """
        Test the connection to the news source.

        Returns:
            Connection status information
        """
        pass

    @abstractmethod
    async def get_rate_limit_info(self) -> RateLimitInfo:
        """
        Get current rate limit information.

        Returns:
            Rate limit information
        """
        pass

    @abstractmethod
    def _parse_article(self, raw_data: Dict[str, Any]) -> NewsArticle:
        """
        Parse raw article data into a NewsArticle object.

        Args:
            raw_data: Raw article data from API

        Returns:
            Parsed NewsArticle
        """
        pass

    async def initialize(self) -> None:
        """Initialize the adapter with necessary setup."""
        self.logger.info(f"Initializing {self.source_name} adapter")
        await self._setup_session()
        await self._setup_rate_limiter()

    async def close(self) -> None:
        """Clean up resources."""
        if self._session:
            await self._session.close()
        self.logger.info(f"Closed {self.source_name} adapter")

    async def _setup_session(self) -> None:
        """Set up HTTP session."""
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=self.source_config.timeout_seconds)
        headers = await self._get_headers()

        self._session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers,
        )

    async def _setup_rate_limiter(self) -> None:
        """Set up rate limiting."""
        from ..utils.rate_limiter import RateLimiter
        self._rate_limiter = RateLimiter(
            max_requests=self.source_config.rate_limit_per_minute,
            time_window=60,  # 1 minute
        )

    async def _get_headers(self) -> Dict[str, str]:
        """Get headers for HTTP requests."""
        headers = {
            "User-Agent": "CryptoTradingMultiAgents/1.0",
            "Accept": "application/json",
        }

        if self.source_config.api_key:
            headers.update(await self._get_auth_headers())

        return headers

    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers. Override in subclasses."""
        return {}

    async def _make_request(
        self,
        url: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with rate limiting and error handling.

        Args:
            url: Request URL
            method: HTTP method
            params: Query parameters
            **kwargs: Additional request arguments

        Returns:
            Response data as dictionary

        Raises:
            Exception: If request fails
        """
        if not self._session:
            await self.initialize()

        # Apply rate limiting
        if self._rate_limiter:
            await self._rate_limiter.acquire()

        try:
            start_time = datetime.now()
            async with self._session.request(method, url, params=params, **kwargs) as response:
                response.raise_for_status()
                data = await response.json()

                # Update success metrics
                self._consecutive_failures = 0
                self._is_healthy = True

                response_time = (datetime.now() - start_time).total_seconds() * 1000
                self.logger.debug(f"Request to {url} completed in {response_time:.2f}ms")

                return data

        except Exception as e:
            self._consecutive_failures += 1
            self._is_healthy = False
            self.logger.error(f"Request failed for {url}: {str(e)}")
            raise

    def is_healthy(self) -> bool:
        """Check if the adapter is healthy."""
        return self._is_healthy and self._consecutive_failures < 3

    def get_failure_count(self) -> int:
        """Get consecutive failure count."""
        return self._consecutive_failures