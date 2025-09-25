import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone, timedelta
import os

from news_collection.news_manager import NewsCollectionManager
from news_collection.models import (
    NewsSource,
    NewsSourceType,
    NewsCategory,
    NewsArticle,
    ConnectionStatus,
    HealthMetrics,
)


class MockAdapter:
    """Mock adapter for testing."""

    def __init__(self, source_config, should_fail=False):
        self.source_config = source_config
        self.should_fail = should_fail
        self.test_articles = [
            NewsArticle(
                id=f"test_{source_config.name}_1",
                title=f"Test Article 1 from {source_config.name}",
                content=f"Content from {source_config.name}",
                url=f"https://{source_config.name}.com/article1",
                source=source_config.source_type,
                category=NewsCategory.MARKET_NEWS,
                published_at=datetime.now(timezone.utc) - timedelta(hours=1),
                tags=["test", source_config.name.lower()]
            ),
            NewsArticle(
                id=f"test_{source_config.name}_2",
                title=f"Test Article 2 from {source_config.name}",
                content=f"More content from {source_config.name}",
                url=f"https://{source_config.name}.com/article2",
                source=source_config.source_type,
                category=NewsCategory.TECHNOLOGY,
                published_at=datetime.now(timezone.utc) - timedelta(hours=2),
                tags=["test", "technology"]
            )
        ]

    @property
    def source_name(self):
        return self.source_config.name

    def is_healthy(self):
        return not self.should_fail

    async def fetch_news(self, **kwargs):
        if self.should_fail:
            raise Exception("Mock adapter failure")
        return self.test_articles

    async def test_connection(self):
        if self.should_fail:
            raise Exception("Connection failed")
        return ConnectionStatus(
            source_name=self.source_name,
            is_connected=True,
            response_time_ms=100,
            last_checked=datetime.now()
        )

    async def close(self):
        pass


class TestNewsCollectionManager:
    """Test cases for NewsCollectionManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = NewsCollectionManager()

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test manager initialization."""
        config = {
            "sources": [
                {
                    "name": "Test Source",
                    "source_type": NewsSourceType.COINDESK,
                    "base_url": "https://api.test.com",
                    "enabled": True,
                    "priority": 1
                }
            ]
        }

        # Mock the adapter creation
        with patch.object(self.manager, '_create_adapters') as mock_create:
            mock_create.return_value = None
            await self.manager.initialize(config)

            assert self.manager._is_initialized
            assert len(self.manager._sources) == 1
            assert "Test Source" in self.manager._sources

    @pytest.mark.asyncio
    async def test_initialization_without_config(self):
        """Test manager initialization with default config."""
        # Set environment variables
        os.environ["COINDESK_ENABLED"] = "true"
        os.environ["COINTELEGRAPH_ENABLED"] = "false"
        os.environ["DECRYPT_ENABLED"] = "true"

        with patch.object(self.manager, '_create_adapters') as mock_create:
            mock_create.return_value = None
            await self.manager.initialize()

            # Should load default configuration
            assert self.manager._is_initialized
            # Should have CoinDesk and Decrypt enabled, CoinTelegraph disabled

        # Clean up
        del os.environ["COINDESK_ENABLED"]
        del os.environ["COINTELEGRAPH_ENABLED"]
        del os.environ["DECRYPT_ENABLED"]

    @pytest.mark.asyncio
    async def test_create_adapters(self):
        """Test creating adapters for configured sources."""
        # Register mock adapter
        self.manager.connection_manager.register_adapter_class(
            NewsSourceType.COINDESK, MockAdapter
        )

        # Add source configuration
        source_config = NewsSource(
            name="Test Source",
            source_type=NewsSourceType.COINDESK,
            base_url="https://api.test.com",
            enabled=True
        )
        self.manager._sources["Test Source"] = source_config

        await self.manager._create_adapters()

        assert "Test Source" in self.manager._adapters
        assert isinstance(self.manager._adapters["Test Source"], MockAdapter)

    @pytest.mark.asyncio
    async def test_start_stop_collection(self):
        """Test starting and stopping news collection."""
        await self.manager.initialize()

        # Start collection
        await self.manager.start_collection(interval_seconds=1)
        assert self.manager._collection_task is not None

        # Stop collection
        await self.manager.stop_collection()
        assert self.manager._collection_task.cancelled()

    @pytest.mark.asyncio
    async def test_fetch_news(self):
        """Test fetching news with filters."""
        # Add mock articles
        now = datetime.now(timezone.utc)
        articles = [
            NewsArticle(
                id="test_1",
                title="Bitcoin News",
                content="Bitcoin price analysis",
                url="https://test.com/bitcoin",
                source=NewsSourceType.COINDESK,
                category=NewsCategory.MARKET_NEWS,
                published_at=now - timedelta(hours=1),
                tags=["bitcoin", "market"]
            ),
            NewsArticle(
                id="test_2",
                title="Ethereum Tech",
                content="Ethereum technology update",
                url="https://test.com/ethereum",
                source=NewsSourceType.COINTELEGRAPH,
                category=NewsCategory.TECHNOLOGY,
                published_at=now - timedelta(hours=2),
                tags=["ethereum", "technology"]
            ),
            NewsArticle(
                id="test_3",
                title="Old News",
                content="This is old news",
                url="https://test.com/old",
                source=NewsSourceType.DECRYPT,
                category=NewsCategory.MARKET_NEWS,
                published_at=now - timedelta(days=2),
                tags=["old"]
            )
        ]

        self.manager._latest_articles = articles

        # Test no filters
        result = await self.manager.fetch_news(limit=10)
        assert len(result) == 3

        # Test source filter
        result = await self.manager.fetch_news(sources=["coindesk"])
        assert len(result) == 1
        assert result[0].source == NewsSourceType.COINDESK

        # Test category filter
        result = await self.manager.fetch_news(categories=[NewsCategory.TECHNOLOGY])
        assert len(result) == 1
        assert result[0].category == NewsCategory.TECHNOLOGY

        # Test keywords filter
        result = await self.manager.fetch_news(keywords=["bitcoin"])
        assert len(result) == 1
        assert "bitcoin" in result[0].title.lower()

        # Test time filter
        result = await self.manager.fetch_news(since=now - timedelta(hours=12))
        assert len(result) == 2  # Should exclude the old news

        # Test limit
        result = await self.manager.fetch_news(limit=1)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_news(self):
        """Test searching news articles."""
        articles = [
            NewsArticle(
                id="test_1",
                title="Bitcoin Price Analysis",
                content="Detailed analysis of Bitcoin price movements",
                url="https://test.com/bitcoin",
                source=NewsSourceType.COINDESK,
                category=NewsCategory.MARKET_NEWS,
                tags=["bitcoin", "price", "analysis"]
            ),
            NewsArticle(
                id="test_2",
                title="Ethereum Technology Update",
                content="Latest developments in Ethereum technology",
                url="https://test.com/ethereum",
                source=NewsSourceType.COINTELEGRAPH,
                category=NewsCategory.TECHNOLOGY,
                tags=["ethereum", "technology", "update"]
            )
        ]

        self.manager._latest_articles = articles

        # Search for "bitcoin"
        result = await self.manager.search_news("bitcoin")
        assert len(result) == 1
        assert "bitcoin" in result[0].title.lower()

        # Search for "technology"
        result = await self.manager.search_news("technology")
        assert len(result) == 1
        assert "technology" in result[0].title.lower()

        # Search for "update"
        result = await self.manager.search_news("update")
        assert len(result) == 1
        assert "update" in result[0].content.lower()

        # Search for non-existent term
        result = await self.manager.search_news("nonexistent")
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_collection_from_source(self):
        """Test collecting news from a single source."""
        source_config = NewsSource(
            name="Test Source",
            source_type=NewsSourceType.COINDESK,
            base_url="https://api.test.com"
        )
        adapter = MockAdapter(source_config)

        result = await self.manager._collect_from_source(adapter)
        assert len(result) == 2
        assert all(article.source == NewsSourceType.COINDESK for article in result)

    @pytest.mark.asyncio
    async def test_collection_from_failing_source(self):
        """Test collecting news from a failing source."""
        source_config = NewsSource(
            name="Failing Source",
            source_type=NewsSourceType.COINDESK,
            base_url="https://api.failing.com"
        )
        adapter = MockAdapter(source_config, should_fail=True)

        result = await self.manager._collect_from_source(adapter)
        assert len(result) == 0  # Should return empty list on failure

    @pytest.mark.asyncio
    async def test_get_connection_status(self):
        """Test getting connection status."""
        # Mock connection manager
        mock_status = ConnectionStatus(
            source_name="Test Source",
            is_connected=True,
            response_time_ms=100,
            last_checked=datetime.now()
        )
        self.manager.connection_manager.get_all_connection_statuses = AsyncMock(return_value={
            "Test Source": mock_status
        })

        result = await self.manager.get_connection_status()
        assert len(result) == 1
        assert result["Test Source"] == mock_status

    @pytest.mark.asyncio
    async def test_get_health_summary(self):
        """Test getting health summary."""
        mock_summary = {
            "Test Source": {
                "is_connected": True,
                "uptime_percentage": 99.5,
                "average_response_time_ms": 100,
                "active_alerts": 0,
                "consecutive_failures": 0,
                "last_checked": datetime.now().isoformat()
            }
        }
        self.manager.health_monitor.get_health_summary = AsyncMock(return_value=mock_summary)

        result = await self.manager.get_health_summary()
        assert result == mock_summary

    @pytest.mark.asyncio
    async def test_get_health_metrics(self):
        """Test getting health metrics."""
        mock_metrics = {
            "Test Source": HealthMetrics(
                source_name="Test Source",
                uptime_percentage=99.5,
                average_response_time_ms=100,
                success_rate=98.0,
                requests_per_minute=45,
                error_count_24h=2,
                last_updated=datetime.now()
            )
        }
        self.manager.health_monitor.get_health_metrics = AsyncMock(return_value=mock_metrics)

        result = await self.manager.get_health_metrics()
        assert result == mock_metrics

    @pytest.mark.asyncio
    async def test_test_source_connection(self):
        """Test testing source connection."""
        source_config = NewsSource(
            name="Test Source",
            source_type=NewsSourceType.COINDESK,
            base_url="https://api.test.com"
        )
        adapter = MockAdapter(source_config)

        self.manager.connection_manager.get_adapter = AsyncMock(return_value=adapter)

        result = await self.manager.test_source_connection("Test Source")
        assert result is not None
        assert result.is_connected is True

    @pytest.mark.asyncio
    async def test_restart_source(self):
        """Test restarting a source."""
        # Set up mock source
        source_config = NewsSource(
            name="Test Source",
            source_type=NewsSourceType.COINDESK,
            base_url="https://api.test.com"
        )
        self.manager._sources["Test Source"] = source_config

        # Mock the connection manager
        self.manager.connection_manager.register_adapter_class(
            NewsSourceType.COINDESK, MockAdapter
        )
        self.manager.connection_manager.create_adapter = AsyncMock()
        self.manager.connection_manager.remove_adapter = AsyncMock()

        # Mock the created adapter
        mock_adapter = MockAdapter(source_config)
        self.manager.connection_manager.create_adapter.return_value = mock_adapter

        result = await self.manager.restart_source("Test Source")
        assert result is True
        assert self.manager.connection_manager.remove_adapter.called
        assert self.manager.connection_manager.create_adapter.called

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the manager."""
        await self.manager.initialize()

        # Start some services
        await self.manager.start_collection(interval_seconds=1)

        # Close
        await self.manager.close()

        assert self.manager._is_initialized is False
        assert self.manager._collection_task is None

    def test_properties(self):
        """Test manager properties."""
        assert self.manager.is_initialized is False
        assert self.manager.available_sources == []
        assert self.manager.latest_articles == []
        assert self.manager.total_articles_collected == 0

    @pytest.mark.asyncio
    async def test_handle_health_alert(self):
        """Test handling health alerts."""
        from news_collection.core.health_monitor import HealthAlert

        alert = HealthAlert(
            source_name="Test Source",
            alert_type="connection_failed",
            message="Connection failed",
            severity="high",
            timestamp=datetime.now()
        )

        # This should not raise an exception
        self.manager._handle_health_alert(alert)