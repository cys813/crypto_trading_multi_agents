import asyncio
import logging
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from .core import ConnectionManager, HealthMonitor, HealthAlert
from .adapters import (
    BaseNewsAdapter,
    CoinDeskAdapter,
    CoinTelegraphAdapter,
    DecryptAdapter,
)
from .models import (
    NewsArticle,
    NewsSource,
    NewsSourceType,
    NewsCategory,
    ConnectionStatus,
    HealthMetrics,
)
from .utils.rate_limiter import RateLimiter

# Load environment variables
load_dotenv()


class NewsCollectionManager:
    """Main manager for news collection from multiple sources."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connection_manager = ConnectionManager()
        self.health_monitor = HealthMonitor(self.connection_manager)
        self._adapters: Dict[str, BaseNewsAdapter] = {}
        self._sources: Dict[str, NewsSource] = {}
        self._is_initialized = False
        self._collection_interval = 300  # 5 minutes
        self._collection_task: Optional[asyncio.Task] = None
        self._latest_articles: List[NewsArticle] = []
        self._article_history: List[NewsArticle] = []
        self._max_history_size = 10000

    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the news collection manager.

        Args:
            config: Configuration dictionary with news sources
        """
        if self._is_initialized:
            return

        self.logger.info("Initializing News Collection Manager")

        # Register adapter classes
        self._register_adapters()

        # Load configuration
        await self._load_configuration(config)

        # Create adapters for configured sources
        await self._create_adapters()

        # Set up health monitoring
        self.health_monitor.add_alert_callback(self._handle_health_alert)

        # Start health monitoring
        await self.health_monitor.start_monitoring()

        self._is_initialized = True
        self.logger.info("News Collection Manager initialized successfully")

    def _register_adapters(self) -> None:
        """Register all available adapter classes."""
        self.connection_manager.register_adapter_class(
            NewsSourceType.COINDESK, CoinDeskAdapter
        )
        self.connection_manager.register_adapter_class(
            NewsSourceType.COINTELEGRAPH, CoinTelegraphAdapter
        )
        self.connection_manager.register_adapter_class(
            NewsSourceType.DECRYPT, DecryptAdapter
        )

    async def _load_configuration(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Load news source configuration."""
        if config is None:
            config = self._get_default_configuration()

        for source_config in config.get("sources", []):
            source = NewsSource(**source_config)
            self._sources[source.name] = source

        self.logger.info(f"Loaded configuration for {len(self._sources)} news sources")

    def _get_default_configuration(self) -> Dict[str, Any]:
        """Get default configuration from environment variables."""
        return {
            "sources": [
                {
                    "name": "CoinDesk",
                    "source_type": NewsSourceType.COINDESK,
                    "base_url": "https://api.coindesk.com/v1",
                    "api_key": os.getenv("COINDESK_API_KEY"),
                    "rate_limit_per_minute": int(os.getenv("COINDESK_RATE_LIMIT", "60")),
                    "timeout_seconds": int(os.getenv("COINDESK_TIMEOUT", "30")),
                    "enabled": os.getenv("COINDESK_ENABLED", "true").lower() == "true",
                    "priority": 1,
                },
                {
                    "name": "CoinTelegraph",
                    "source_type": NewsSourceType.COINTELEGRAPH,
                    "base_url": "https://cointelegraph.com/api/v1",
                    "api_key": os.getenv("COINTELEGRAPH_API_KEY"),
                    "rate_limit_per_minute": int(os.getenv("COINTELEGRAPH_RATE_LIMIT", "60")),
                    "timeout_seconds": int(os.getenv("COINTELEGRAPH_TIMEOUT", "30")),
                    "enabled": os.getenv("COINTELEGRAPH_ENABLED", "true").lower() == "true",
                    "priority": 2,
                },
                {
                    "name": "Decrypt",
                    "source_type": NewsSourceType.DECRYPT,
                    "base_url": "https://api.decrypt.co/v1",
                    "api_key": os.getenv("DECRYPT_API_KEY"),
                    "rate_limit_per_minute": int(os.getenv("DECRYPT_RATE_LIMIT", "60")),
                    "timeout_seconds": int(os.getenv("DECRYPT_TIMEOUT", "30")),
                    "enabled": os.getenv("DECRYPT_ENABLED", "true").lower() == "true",
                    "priority": 3,
                },
            ]
        }

    async def _create_adapters(self) -> None:
        """Create adapters for enabled news sources."""
        for source_name, source_config in self._sources.items():
            if not source_config.enabled:
                self.logger.info(f"Skipping disabled source: {source_name}")
                continue

            try:
                adapter = await self.connection_manager.create_adapter(source_config)
                self._adapters[source_name] = adapter
                self.logger.info(f"Created adapter for {source_name}")
            except Exception as e:
                self.logger.error(f"Failed to create adapter for {source_name}: {str(e)}")

    async def start_collection(self, interval_seconds: Optional[int] = None) -> None:
        """
        Start automated news collection.

        Args:
            interval_seconds: Collection interval in seconds
        """
        if interval_seconds:
            self._collection_interval = interval_seconds

        if self._collection_task and not self._collection_task.done():
            self.logger.warning("Collection already running")
            return

        self._collection_task = asyncio.create_task(self._collection_loop())
        self.logger.info(f"Started news collection with {self._collection_interval}s interval")

    async def stop_collection(self) -> None:
        """Stop automated news collection."""
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
            self.logger.info("Stopped news collection")

    async def _collection_loop(self) -> None:
        """Main collection loop."""
        while True:
            try:
                await asyncio.sleep(self._collection_interval)
                await self._collect_all_news()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Collection loop error: {str(e)}")

    async def _collect_all_news(self) -> None:
        """Collect news from all sources."""
        try:
            # Get healthy adapters
            healthy_adapters = [
                adapter for adapter in self._adapters.values()
                if adapter.is_healthy()
            ]

            if not healthy_adapters:
                self.logger.warning("No healthy adapters available")
                return

            # Collect news from all sources
            tasks = []
            for adapter in healthy_adapters:
                task = asyncio.create_task(self._collect_from_source(adapter))
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            new_articles = []
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Collection error: {str(result)}")
                elif result:
                    new_articles.extend(result)

            # Update article lists
            if new_articles:
                self._latest_articles = new_articles[:50]  # Keep latest 50
                self._article_history.extend(new_articles)

                # Limit history size
                if len(self._article_history) > self._max_history_size:
                    self._article_history = self._article_history[-self._max_history_size:]

                self.logger.info(f"Collected {len(new_articles)} new articles")

        except Exception as e:
            self.logger.error(f"Error in news collection: {str(e)}")

    async def _collect_from_source(self, adapter: BaseNewsAdapter) -> List[NewsArticle]:
        """Collect news from a single source."""
        try:
            # Get articles from last 24 hours or reasonable default
            since = datetime.now() - timedelta(hours=24)
            articles = await adapter.fetch_news(limit=20, since=since)
            return articles
        except Exception as e:
            self.logger.error(f"Error collecting from {adapter.source_name}: {str(e)}")
            return []

    def _handle_health_alert(self, alert: HealthAlert) -> None:
        """Handle health alerts from the health monitor."""
        self.logger.warning(f"Health Alert: {alert.severity.upper()} - {alert.source_name} - {alert.message}")

        # You could add more sophisticated alert handling here
        # For example: send notifications, trigger failover, etc.

    async def fetch_news(
        self,
        limit: int = 10,
        sources: Optional[List[str]] = None,
        categories: Optional[List[NewsCategory]] = None,
        keywords: Optional[List[str]] = None,
        since: Optional[datetime] = None,
    ) -> List[NewsArticle]:
        """
        Fetch news articles with filtering.

        Args:
            limit: Maximum number of articles to return
            sources: Filter by source names
            categories: Filter by categories
            keywords: Filter by keywords
            since: Filter by publication date

        Returns:
            Filtered list of news articles
        """
        # Start with latest articles
        articles = self._latest_articles.copy()

        # If we need more articles, include from history
        if len(articles) < limit:
            needed = limit - len(articles)
            articles.extend(self._article_history[-needed:])

        # Apply filters
        filtered_articles = []

        for article in articles:
            # Source filter
            if sources and article.source.value not in sources:
                continue

            # Category filter
            if categories and article.category not in categories:
                continue

            # Keywords filter
            if keywords:
                text_to_search = f"{article.title} {article.content} {' '.join(article.tags)}".lower()
                keyword_matches = any(
                    keyword.lower() in text_to_search
                    for keyword in keywords
                )
                if not keyword_matches:
                    continue

            # Time filter
            if since and article.published_at:
                if article.published_at < since:
                    continue

            filtered_articles.append(article)

        return filtered_articles[:limit]

    async def search_news(self, query: str, limit: int = 10) -> List[NewsArticle]:
        """
        Search for news articles by query.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            Search results
        """
        # Search in both latest articles and history
        all_articles = self._latest_articles + self._article_history

        # Remove duplicates
        seen_ids = set()
        unique_articles = []
        for article in all_articles:
            if article.id not in seen_ids:
                seen_ids.add(article.id)
                unique_articles.append(article)

        # Search by query
        query_lower = query.lower()
        results = []

        for article in unique_articles:
            searchable_text = f"{article.title} {article.content} {' '.join(article.tags)}".lower()
            if query_lower in searchable_text:
                results.append(article)

        return results[:limit]

    async def get_connection_status(self) -> Dict[str, ConnectionStatus]:
        """Get connection status for all sources."""
        return await self.connection_manager.get_all_connection_statuses()

    async def get_health_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get health summary for all sources."""
        return await self.health_monitor.get_health_summary()

    async def get_health_metrics(self) -> Dict[str, HealthMetrics]:
        """Get detailed health metrics for all sources."""
        return await self.health_monitor.get_health_metrics()

    def get_active_alerts(self) -> List[HealthAlert]:
        """Get active health alerts."""
        return self.health_monitor.get_active_alerts()

    async def test_source_connection(self, source_name: str) -> Optional[ConnectionStatus]:
        """Test connection to a specific source."""
        adapter = await self.connection_manager.get_adapter(source_name)
        if adapter:
            return await adapter.test_connection()
        return None

    async def restart_source(self, source_name: str) -> bool:
        """
        Restart a news source adapter.

        Args:
            source_name: Name of the source to restart

        Returns:
            True if restart was successful
        """
        try:
            # Remove existing adapter
            await self.connection_manager.remove_adapter(source_name)

            # Create new adapter
            if source_name in self._sources:
                source_config = self._sources[source_name]
                adapter = await self.connection_manager.create_adapter(source_config)
                self._adapters[source_name] = adapter

                # Test connection
                status = await adapter.test_connection()
                return status.is_connected

        except Exception as e:
            self.logger.error(f"Failed to restart {source_name}: {str(e)}")
            return False

    async def close(self) -> None:
        """Clean up resources."""
        await self.stop_collection()
        await self.health_monitor.stop_monitoring()
        await self.connection_manager.close_all()

        self._is_initialized = False
        self.logger.info("News Collection Manager closed")

    @property
    def is_initialized(self) -> bool:
        """Check if manager is initialized."""
        return self._is_initialized

    @property
    def available_sources(self) -> List[str]:
        """Get list of available source names."""
        return list(self._adapters.keys())

    @property
    def latest_articles(self) -> List[NewsArticle]:
        """Get latest collected articles."""
        return self._latest_articles.copy()

    @property
    def total_articles_collected(self) -> int:
        """Get total number of articles collected."""
        return len(self._article_history)