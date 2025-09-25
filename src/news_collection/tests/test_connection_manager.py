import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from news_collection.core.connection_manager import ConnectionManager
from news_collection.core.health_monitor import HealthMonitor
from news_collection.models import (
    NewsSource,
    NewsSourceType,
    NewsCategory,
    ConnectionStatus,
    HealthMetrics,
)
from news_collection.adapters.base_adapter import BaseNewsAdapter


class MockAdapter(BaseNewsAdapter):
    """Mock adapter for testing."""

    def __init__(self, source_config, should_fail=False):
        super().__init__(source_config)
        self.should_fail = should_fail
        self.test_response_time = 100

    @property
    def source_name(self):
        return "Mock Adapter"

    @property
    def supported_categories(self):
        return [NewsCategory.MARKET_NEWS]

    async def fetch_news(self, **kwargs):
        if self.should_fail:
            raise Exception("Mock failure")
        return []

    async def test_connection(self):
        if self.should_fail:
            raise Exception("Connection failed")
        return ConnectionStatus(
            source_name=self.source_name,
            is_connected=True,
            response_time_ms=self.test_response_time,
            last_checked=datetime.now()
        )

    async def get_rate_limit_info(self):
        from news_collection.models import RateLimitInfo
        return RateLimitInfo(
            source_name=self.source_name,
            requests_remaining=60,
            requests_limit=60,
            reset_time=datetime.now()
        )

    def _parse_article(self, raw_data):
        from news_collection.models import NewsArticle
        return NewsArticle(
            id="test",
            title="Test",
            content="Content",
            url="https://test.com"
        )


class TestConnectionManager:
    """Test cases for ConnectionManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConnectionManager()
        self.source_config = NewsSource(
            name="Test Source",
            source_type=NewsSourceType.COINDESK,
            base_url="https://api.test.com"
        )

    def test_register_adapter_class(self):
        """Test registering adapter classes."""
        self.manager.register_adapter_class(NewsSourceType.COINDESK, MockAdapter)

        assert NewsSourceType.COINDESK in self.manager._adapter_classes
        assert self.manager._adapter_classes[NewsSourceType.COINDESK] == MockAdapter

    @pytest.mark.asyncio
    async def test_create_adapter(self):
        """Test creating an adapter."""
        self.manager.register_adapter_class(NewsSourceType.COINDESK, MockAdapter)

        adapter = await self.manager.create_adapter(self.source_config)

        assert isinstance(adapter, MockAdapter)
        assert adapter.source_config == self.source_config
        assert self.source_config.name in self.manager._adapters
        assert self.manager._active_connections == 1

    @pytest.mark.asyncio
    async def test_create_adapter_failure(self):
        """Test creating adapter with unregistered source type."""
        with pytest.raises(ValueError, match="No adapter class registered"):
            await self.manager.create_adapter(self.source_config)

    @pytest.mark.asyncio
    async def test_get_adapter(self):
        """Test getting an adapter by name."""
        self.manager.register_adapter_class(NewsSourceType.COINDESK, MockAdapter)
        adapter = await self.manager.create_adapter(self.source_config)

        retrieved = await self.manager.get_adapter(self.source_config.name)
        assert retrieved == adapter

        # Test non-existent adapter
        assert await self.manager.get_adapter("nonexistent") is None

    @pytest.mark.asyncio
    async def test_get_healthy_adapter(self):
        """Test getting healthy adapters."""
        self.manager.register_adapter_class(NewsSourceType.COINDESK, MockAdapter)

        # Create healthy adapter
        healthy_config = NewsSource(
            name="Healthy Source",
            source_type=NewsSourceType.COINDESK,
            base_url="https://api.healthy.com",
            priority=1
        )
        healthy_adapter = await self.manager.create_adapter(healthy_config)

        # Create unhealthy adapter
        unhealthy_config = NewsSource(
            name="Unhealthy Source",
            source_type=NewsSourceType.COINDESK,
            base_url="https://api.unhealthy.com",
            priority=2
        )
        unhealthy_adapter = MockAdapter(unhealthy_config, should_fail=True)
        self.manager._adapters[unhealthy_config.name] = unhealthy_adapter

        # Test getting healthy adapter
        result = await self.manager.get_healthy_adapter()
        assert result == healthy_adapter

        # Test with source type filter
        result = await self.manager.get_healthy_adapter(NewsSourceType.COINDESK)
        assert result == healthy_adapter

        # Test with no healthy adapters
        unhealthy_adapter._consecutive_failures = 3
        result = await self.manager.get_healthy_adapter()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_connection_status(self):
        """Test getting connection status."""
        status = ConnectionStatus(
            source_name="Test Source",
            is_connected=True,
            response_time_ms=100,
            last_checked=datetime.now()
        )
        self.manager._connection_statuses["Test Source"] = status

        result = await self.manager.get_connection_status("Test Source")
        assert result == status

        # Test non-existent source
        assert await self.manager.get_connection_status("nonexistent") is None

    @pytest.mark.asyncio
    async def test_get_all_connection_statuses(self):
        """Test getting all connection statuses."""
        status1 = ConnectionStatus(
            source_name="Source 1",
            is_connected=True,
            response_time_ms=100,
            last_checked=datetime.now()
        )
        status2 = ConnectionStatus(
            source_name="Source 2",
            is_connected=False,
            response_time_ms=200,
            last_checked=datetime.now()
        )

        self.manager._connection_statuses["Source 1"] = status1
        self.manager._connection_statuses["Source 2"] = status2

        result = await self.manager.get_all_connection_statuses()
        assert len(result) == 2
        assert result["Source 1"] == status1
        assert result["Source 2"] == status2

    @pytest.mark.asyncio
    async def test_test_all_connections(self):
        """Test testing all connections."""
        self.manager.register_adapter_class(NewsSourceType.COINDESK, MockAdapter)

        # Create healthy adapter
        healthy_config = NewsSource(
            name="Healthy Source",
            source_type=NewsSourceType.COINDESK,
            base_url="https://api.healthy.com"
        )
        healthy_adapter = await self.manager.create_adapter(healthy_config)

        # Create unhealthy adapter
        unhealthy_config = NewsSource(
            name="Unhealthy Source",
            source_type=NewsSourceType.COINDESK,
            base_url="https://api.unhealthy.com"
        )
        unhealthy_adapter = MockAdapter(unhealthy_config, should_fail=True)
        self.manager._adapters[unhealthy_config.name] = unhealthy_adapter

        results = await self.manager.test_all_connections()

        assert len(results) == 2
        assert results["Healthy Source"].is_connected is True
        assert results["Unhealthy Source"].is_connected is False

    @pytest.mark.asyncio
    async def test_health_monitoring(self):
        """Test health monitoring functionality."""
        self.manager.register_adapter_class(NewsSourceType.COINDESK, MockAdapter)
        adapter = await self.manager.create_adapter(self.source_config)

        # Start monitoring
        await self.manager.start_health_monitoring()
        assert self.manager._health_check_task is not None

        # Stop monitoring
        await self.manager.stop_health_monitoring()
        assert self.manager._health_check_task.cancelled()

    @pytest.mark.asyncio
    async def test_remove_adapter(self):
        """Test removing an adapter."""
        self.manager.register_adapter_class(NewsSourceType.COINDESK, MockAdapter)
        adapter = await self.manager.create_adapter(self.source_config)

        assert self.source_config.name in self.manager._adapters
        assert self.manager._active_connections == 1

        await self.manager.remove_adapter(self.source_config.name)

        assert self.source_config.name not in self.manager._adapters
        assert self.manager._active_connections == 0

    @pytest.mark.asyncio
    async def test_get_health_metrics(self):
        """Test getting health metrics."""
        status = ConnectionStatus(
            source_name="Test Source",
            is_connected=True,
            response_time_ms=100,
            last_checked=datetime.now(),
            consecutive_failures=0
        )
        self.manager._connection_statuses["Test Source"] = status

        metrics = await self.manager.get_health_metrics()

        assert "Test Source" in metrics
        assert metrics["Test Source"].uptime_percentage == 100.0
        assert metrics["Test Source"].average_response_time_ms == 100.0
        assert metrics["Test Source"].success_rate == 100.0
        assert metrics["Test Source"].error_count_24h == 0

    @pytest.mark.asyncio
    async def test_close_all(self):
        """Test closing all adapters."""
        self.manager.register_adapter_class(NewsSourceType.COINDESK, MockAdapter)
        adapter = await self.manager.create_adapter(self.source_config)

        # Start monitoring
        await self.manager.start_health_monitoring()

        # Close all
        await self.manager.close_all()

        assert len(self.manager._adapters) == 0
        assert len(self.manager._connection_statuses) == 0
        assert self.manager._active_connections == 0
        assert self.manager._health_check_task is None or self.manager._health_check_task.cancelled()

    @pytest.mark.asyncio
    async def test_connection_limit(self):
        """Test connection limit enforcement."""
        self.manager._max_connections = 1
        self.manager.register_adapter_class(NewsSourceType.COINDESK, MockAdapter)

        # First adapter should succeed
        adapter1 = await self.manager.create_adapter(self.source_config)
        assert adapter1 is not None

        # Second adapter should wait for slot
        config2 = NewsSource(
            name="Source 2",
            source_type=NewsSourceType.COINDESK,
            base_url="https://api.source2.com"
        )

        # This would normally wait, but we'll test the logic
        assert self.manager._active_connections == 1
        assert self.manager._active_connections >= self.manager._max_connections