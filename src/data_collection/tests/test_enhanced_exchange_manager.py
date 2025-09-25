"""
Comprehensive test suite for the Enhanced Exchange Manager.

This test suite covers all aspects of the enhanced exchange manager including:
- Connection management and load balancing
- Rate limiting and health monitoring
- Connection pooling and failover
- Performance and reliability
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime, timedelta
from typing import Dict, Any

from ..core.enhanced_exchange_manager import (
    ExchangeManager, ExchangeConnection, ExchangeStatus, ConnectionStrategy,
    Priority, RateLimiter, ConnectionPool, RateLimitInfo
)
from ..core.exceptions import (
    ExchangeConnectionError, RateLimitExceededError, ExchangeUnavailableError,
    ExchangeError, ErrorCode
)
from ..utils.metrics import MetricsCollector
from ..core.config import get_config


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = Mock()
    config.exchanges = {
        "binance": Mock(
            enabled=True,
            api_key="test_key",
            api_secret="test_secret",
            passphrase=None,
            sandbox=True,
            enable_rate_limit=True,
            timeout=10000,
            rate_limit=100,
            options={"defaultType": "spot"}
        ),
        "okx": Mock(
            enabled=True,
            api_key="test_key",
            api_secret="test_secret",
            passphrase="test_pass",
            sandbox=True,
            enable_rate_limit=True,
            timeout=10000,
            rate_limit=80,
            options={"defaultType": "spot"}
        )
    }
    config.redis = Mock(
        host="localhost",
        port=6379,
        password="",
        database=0
    )
    return config


@pytest.fixture
def mock_exchange():
    """Mock CCXT exchange."""
    exchange = Mock()
    exchange.fetch_markets = AsyncMock(return_value=[
        {"symbol": "BTC/USDT", "active": True},
        {"symbol": "ETH/USDT", "active": True}
    ])
    exchange.fetch_ticker = AsyncMock(return_value={
        "symbol": "BTC/USDT",
        "last": 50000.0,
        "bid": 49900.0,
        "ask": 50100.0
    })
    exchange.fetch_ohlcv = AsyncMock(return_value=[
        [1640995200000, 50000.0, 51000.0, 49000.0, 50500.0, 100.0]
    ])
    exchange.fetch_order_book = AsyncMock(return_value={
        "bids": [[49900.0, 1.0]],
        "asks": [[50100.0, 1.0]]
    })
    exchange.fetch_trades = AsyncMock(return_value=[
        {"timestamp": 1640995200000, "price": 50000.0, "amount": 1.0, "side": "buy"}
    ])
    exchange.fetch_balance = AsyncMock(return_value={
        "USDT": {"free": 10000.0, "used": 1000.0, "total": 11000.0}
    })
    exchange.fetch_positions = AsyncMock(return_value=[])
    exchange.fetch_orders = AsyncMock(return_value=[])
    exchange.ping = AsyncMock()
    exchange.fetch_time = AsyncMock(return_value=time.time() * 1000)
    exchange.close = AsyncMock()
    exchange.timeout = 10000
    return exchange


@pytest.fixture
def mock_session():
    """Mock aiohttp session."""
    session = Mock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def exchange_manager(mock_config):
    """Create ExchangeManager instance for testing."""
    with patch('src.data_collection.core.enhanced_exchange_manager.get_config', return_value=mock_config):
        manager = ExchangeManager()
        return manager


class TestExchangeConnection:
    """Test ExchangeConnection class."""

    def test_connection_initialization(self, mock_exchange, mock_session):
        """Test connection initialization."""
        connection = ExchangeConnection(
            exchange_id="binance",
            exchange=mock_exchange,
            status=ExchangeStatus.HEALTHY,
            session=mock_session,
            weight=100
        )

        assert connection.exchange_id == "binance"
        assert connection.status == ExchangeStatus.HEALTHY
        assert connection.weight == 100
        assert connection.success_count == 0
        assert connection.error_count == 0
        assert connection.health_score == 1.0

    def test_update_success(self, mock_exchange, mock_session):
        """Test success update."""
        connection = ExchangeConnection(
            exchange_id="binance",
            exchange=mock_exchange,
            status=ExchangeStatus.HEALTHY,
            session=mock_session
        )

        connection.update_success(150.0)

        assert connection.success_count == 1
        assert connection.total_requests == 1
        assert connection.latency == 150.0
        assert connection.consecutive_errors == 0
        assert connection.health_score == 1.0

    def test_update_success_latency_smoothing(self, mock_exchange, mock_session):
        """Test latency smoothing with multiple updates."""
        connection = ExchangeConnection(
            exchange_id="binance",
            exchange=mock_exchange,
            status=ExchangeStatus.HEALTHY,
            session=mock_session,
            latency=100.0
        )

        connection.update_success(200.0)
        expected_latency = 100.0 * 0.8 + 200.0 * 0.2  # 120.0
        assert abs(connection.latency - expected_latency) < 0.01

    def test_update_error(self, mock_exchange, mock_session):
        """Test error update."""
        connection = ExchangeConnection(
            exchange_id="binance",
            exchange=mock_exchange,
            status=ExchangeStatus.HEALTHY,
            session=mock_session
        )

        connection.update_error("Network error")

        assert connection.error_count == 1
        assert connection.total_requests == 1
        assert connection.consecutive_errors == 1
        assert connection.last_error == "Network error"
        assert connection.health_score == 0.9

    def test_get_success_rate(self, mock_exchange, mock_session):
        """Test success rate calculation."""
        connection = ExchangeConnection(
            exchange_id="binance",
            exchange=mock_exchange,
            status=ExchangeStatus.HEALTHY,
            session=mock_session
        )

        # No requests
        assert connection.get_success_rate() == 0.0

        # Add some requests
        connection.success_count = 8
        connection.error_count = 2
        assert connection.get_success_rate() == 0.8

    def test_is_healthy(self, mock_exchange, mock_session):
        """Test health check."""
        connection = ExchangeConnection(
            exchange_id="binance",
            exchange=mock_exchange,
            status=ExchangeStatus.HEALTHY,
            session=mock_session
        )

        # Initially healthy
        assert connection.is_healthy()

        # Too many consecutive errors
        connection.consecutive_errors = 6
        assert not connection.is_healthy()

        # Low health score
        connection.consecutive_errors = 0
        connection.health_score = 0.2
        assert not connection.is_healthy()

        # Offline status
        connection.status = ExchangeStatus.OFFLINE
        connection.health_score = 1.0
        assert not connection.is_healthy()


class TestRateLimiter:
    """Test RateLimiter class."""

    @pytest.fixture
    def rate_limiter(self):
        """Create RateLimiter instance."""
        return RateLimiter()

    def test_local_rate_limiting_initialization(self, rate_limiter):
        """Test rate limiter initialization."""
        assert not rate_limiter.use_redis
        assert rate_limiter.local_limits == {}

    @pytest.mark.asyncio
    async def test_acquire_permit_local(self, rate_limiter):
        """Test local permit acquisition."""
        key = "binance:fetch_ticker"
        result = await rate_limiter.acquire_permit("binance", "fetch_ticker", Priority.NORMAL)
        assert result is True

        # Should be within limit
        assert len(rate_limiter.local_limits[key].requests) == 1

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, rate_limiter):
        """Test rate limit exceeded scenario."""
        key = "binance:fetch_ticker"

        # Fill up the limit
        for _ in range(100):
            await rate_limiter.acquire_permit("binance", "fetch_ticker", Priority.NORMAL)

        # Next request should be blocked
        result = await rate_limiter.acquire_permit("binance", "fetch_ticker", Priority.NORMAL)
        assert result is False

    @pytest.mark.asyncio
    async def test_priority_access(self, rate_limiter):
        """Test priority-based access."""
        key = "binance:fetch_ticker"

        # Fill up the limit
        for _ in range(100):
            await rate_limiter.acquire_permit("binance", "fetch_ticker", Priority.NORMAL)

        # High priority should still work
        result = await rate_limiter.acquire_permit("binance", "fetch_ticker", Priority.HIGH)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_remaining_requests(self, rate_limiter):
        """Test getting remaining requests."""
        # Initially should return default
        remaining = await rate_limiter.get_remaining_requests("binance", "fetch_ticker")
        assert remaining == 100

        # Make some requests
        for _ in range(30):
            await rate_limiter.acquire_permit("binance", "fetch_ticker", Priority.NORMAL)

        remaining = await rate_limiter.get_remaining_requests("binance", "fetch_ticker")
        assert remaining == 70

    @pytest.mark.asyncio
    async def test_rate_limit_cleanup(self, rate_limiter):
        """Test cleanup of expired requests."""
        key = "binance:fetch_ticker"

        # Make requests
        for _ in range(50):
            await rate_limiter.acquire_permit("binance", "fetch_ticker", Priority.NORMAL)

        # Simulate time passing
        rate_limiter.local_limits[key].requests = deque([time.time() - 120] * 50)

        # Make new request - should clean up old ones
        await rate_limiter.acquire_permit("binance", "fetch_ticker", Priority.NORMAL)

        assert len(rate_limiter.local_limits[key].requests) == 1


class TestConnectionPool:
    """Test ConnectionPool class."""

    @pytest.fixture
    def connection_pool(self):
        """Create ConnectionPool instance."""
        return ConnectionPool(max_size=5, idle_timeout=300)

    @pytest.fixture
    def mock_connection(self, mock_exchange, mock_session):
        """Create mock connection."""
        return ExchangeConnection(
            exchange_id="binance",
            exchange=mock_exchange,
            status=ExchangeStatus.HEALTHY,
            session=mock_session
        )

    @pytest.mark.asyncio
    async def test_get_connection_from_pool(self, connection_pool, mock_connection):
        """Test getting connection from pool."""
        # Add connection to pool
        connection_pool.connections["binance"] = [mock_connection]

        # Get connection
        manager = Mock()
        result = await connection_pool.get_connection("binance", manager)

        assert result == mock_connection
        assert connection_pool.active_connections["binance"] == 1
        assert len(connection_pool.connections["binance"]) == 0

    @pytest.mark.asyncio
    async def test_return_connection_to_pool(self, connection_pool, mock_connection):
        """Test returning connection to pool."""
        manager = Mock()
        connection_pool.active_connections["binance"] = 1

        # Return healthy connection
        await connection_pool.return_connection(mock_connection)

        assert connection_pool.active_connections["binance"] == 0
        assert len(connection_pool.connections["binance"]) == 1

    @pytest.mark.asyncio
    async def test_return_unhealthy_connection(self, connection_pool, mock_connection):
        """Test returning unhealthy connection."""
        manager = Mock()
        mock_connection.status = ExchangeStatus.OFFLINE
        connection_pool.active_connections["binance"] = 1

        # Return unhealthy connection
        await connection_pool.return_connection(mock_connection)

        assert connection_pool.active_connections["binance"] == 0
        assert len(connection_pool.connections["binance"]) == 0
        # Manager should close the connection
        manager._close_connection.assert_called_once_with(mock_connection)


class TestExchangeManager:
    """Test ExchangeManager class."""

    @pytest.mark.asyncio
    async def test_initialization(self, exchange_manager, mock_config, mock_exchange, mock_session):
        """Test exchange manager initialization."""
        with patch('src.data_collection.core.enhanced_exchange_manager.ccxt.binance', return_value=mock_exchange):
            with patch('src.data_collection.core.enhanced_exchange_manager.aiohttp.ClientSession', return_value=mock_session):
                await exchange_manager.initialize()

                assert len(exchange_manager.connections) == 2
                assert "binance" in exchange_manager.connections
                assert "okx" in exchange_manager.connections
                assert exchange_manager._running is True

    @pytest.mark.asyncio
    async def test_execute_request_success(self, exchange_manager, mock_exchange, mock_session):
        """Test successful request execution."""
        with patch('src.data_collection.core.enhanced_exchange_manager.ccxt.binance', return_value=mock_exchange):
            with patch('src.data_collection.core.enhanced_exchange_manager.aiohttp.ClientSession', return_value=mock_session):
                await exchange_manager.initialize()

                # Mock connection pool
                connection = exchange_manager.connections["binance"]
                with patch.object(exchange_manager.connection_pool, 'get_connection', return_value=connection):
                    with patch.object(exchange_manager.connection_pool, 'return_connection'):
                        result = await exchange_manager.execute_request('fetch_ticker', 'BTC/USDT')

                        assert result == mock_exchange.fetch_ticker.return_value
                        assert connection.success_count == 1
                        assert connection.total_requests == 1

    @pytest.mark.asyncio
    async def test_execute_request_rate_limit_error(self, exchange_manager, mock_exchange, mock_session):
        """Test request execution with rate limit error."""
        mock_exchange.fetch_ticker.side_effect = Exception("Rate limit exceeded")

        with patch('src.data_collection.core.enhanced_exchange_manager.ccxt.binance', return_value=mock_exchange):
            with patch('src.data_collection.core.enhanced_exchange_manager.aiohttp.ClientSession', return_value=mock_session):
                await exchange_manager.initialize()

                connection = exchange_manager.connections["binance"]
                with patch.object(exchange_manager.connection_pool, 'get_connection', return_value=connection):
                    with patch.object(exchange_manager.connection_pool, 'return_connection'):
                        with pytest.raises(ExchangeConnectionError):
                            await exchange_manager.execute_request('fetch_ticker', 'BTC/USDT')

                        assert connection.error_count == 1
                        assert connection.total_requests == 1

    @pytest.mark.asyncio
    async def test_load_balancing_strategies(self, exchange_manager, mock_exchange, mock_session):
        """Test different load balancing strategies."""
        with patch('src.data_collection.core.enhanced_exchange_manager.ccxt.binance', return_value=mock_exchange):
            with patch('src.data_collection.core.enhanced_exchange_manager.ccxt.okx', return_value=mock_exchange):
                with patch('src.data_collection.core.enhanced_exchange_manager.aiohttp.ClientSession', return_value=mock_session):
                    await exchange_manager.initialize()

                    # Test weighted round-robin
                    exchange_manager.strategy = ConnectionStrategy.WEIGHTED_ROUND_ROBIN
                    connection = await exchange_manager._get_connection_by_strategy(Priority.NORMAL)
                    assert connection is not None

                    # Test least latency
                    exchange_manager.connections["binance"].latency = 100.0
                    exchange_manager.connections["okx"].latency = 200.0
                    exchange_manager.strategy = ConnectionStrategy.LEAST_LATENCY
                    connection = await exchange_manager._get_connection_by_strategy(Priority.NORMAL)
                    assert connection.exchange_id == "binance"

    @pytest.mark.asyncio
    async def test_health_monitoring(self, exchange_manager, mock_exchange, mock_session):
        """Test health monitoring functionality."""
        with patch('src.data_collection.core.enhanced_exchange_manager.ccxt.binance', return_value=mock_exchange):
            with patch('src.data_collection.core.enhanced_exchange_manager.aiohttp.ClientSession', return_value=mock_session):
                await exchange_manager.initialize()

                # Perform health check
                await exchange_manager._check_connection_health(exchange_manager.connections["binance"])

                connection = exchange_manager.connections["binance"]
                assert connection.status == ExchangeStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_exchange_status_reporting(self, exchange_manager, mock_exchange, mock_session):
        """Test exchange status reporting."""
        with patch('src.data_collection.core.enhanced_exchange_manager.ccxt.binance', return_value=mock_exchange):
            with patch('src.data_collection.core.enhanced_exchange_manager.aiohttp.ClientSession', return_value=mock_session):
                await exchange_manager.initialize()

                # Get all statuses
                statuses = await exchange_manager.get_exchange_status()
                assert "binance" in statuses
                assert "okx" in statuses

                # Get specific exchange status
                binance_status = await exchange_manager.get_exchange_status("binance")
                assert binance_status["exchange_id"] == "binance"
                assert "status" in binance_status
                assert "latency" in binance_status
                assert "success_rate" in binance_status

    @pytest.mark.asyncio
    async def test_connection_context_manager(self, exchange_manager, mock_exchange, mock_session):
        """Test connection context manager."""
        with patch('src.data_collection.core.enhanced_exchange_manager.ccxt.binance', return_value=mock_exchange):
            with patch('src.data_collection.core.enhanced_exchange_manager.aiohttp.ClientSession', return_value=mock_session):
                await exchange_manager.initialize()

                connection = exchange_manager.connections["binance"]
                with patch.object(exchange_manager.connection_pool, 'get_connection', return_value=connection):
                    with patch.object(exchange_manager.connection_pool, 'return_connection') as mock_return:
                        async with exchange_manager.get_connection("binance") as conn:
                            assert conn == connection

                        # Should return connection after context exits
                        mock_return.assert_called_once_with(connection)

    @pytest.mark.asyncio
    async def test_failover_mechanism(self, exchange_manager, mock_exchange, mock_session):
        """Test failover mechanism."""
        with patch('src.data_collection.core.enhanced_exchange_manager.ccxt.binance', return_value=mock_exchange):
            with patch('src.data_collection.core.enhanced_exchange_manager.ccxt.okx', return_value=mock_exchange):
                with patch('src.data_collection.core.enhanced_exchange_manager.aiohttp.ClientSession', return_value=mock_session):
                    await exchange_manager.initialize()

                    # Mark one exchange as unhealthy
                    exchange_manager.connections["binance"].status = ExchangeStatus.OFFLINE

                    # Should get the healthy exchange
                    connection = await exchange_manager._get_connection_by_strategy(Priority.NORMAL)
                    assert connection.exchange_id == "okx"

    @pytest.mark.asyncio
    async def test_metrics_collection(self, exchange_manager, mock_exchange, mock_session):
        """Test metrics collection."""
        with patch('src.data_collection.core.enhanced_exchange_manager.ccxt.binance', return_value=mock_exchange):
            with patch('src.data_collection.core.enhanced_exchange_manager.aiohttp.ClientSession', return_value=mock_session):
                await exchange_manager.initialize()

                # Perform some requests to generate metrics
                connection = exchange_manager.connections["binance"]
                with patch.object(exchange_manager.connection_pool, 'get_connection', return_value=connection):
                    with patch.object(exchange_manager.connection_pool, 'return_connection'):
                        await exchange_manager.execute_request('fetch_ticker', 'BTC/USDT')

                # Collect metrics
                await exchange_manager._collect_metrics()

                # Check that metrics were collected
                assert len(exchange_manager.request_times["binance"]) > 0

    @pytest.mark.asyncio
    async def test_manager_shutdown(self, exchange_manager, mock_exchange, mock_session):
        """Test manager shutdown."""
        with patch('src.data_collection.core.enhanced_exchange_manager.ccxt.binance', return_value=mock_exchange):
            with patch('src.data_collection.core.enhanced_exchange_manager.aiohttp.ClientSession', return_value=mock_session):
                await exchange_manager.initialize()

                # Close manager
                await exchange_manager.close()

                assert exchange_manager._running is False
                assert len(exchange_manager.connections) == 0


class TestIntegration:
    """Integration tests for the complete system."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, exchange_manager, mock_config):
        """Test complete workflow with real exchange-like behavior."""
        # Create more realistic mock exchange
        mock_exchange = AsyncMock()
        mock_exchange.fetch_markets.return_value = [
            {"symbol": "BTC/USDT", "active": True},
            {"symbol": "ETH/USDT", "active": True}
        ]
        mock_exchange.fetch_ticker.return_value = {
            "symbol": "BTC/USDT", "last": 50000.0, "bid": 49900.0, "ask": 50100.0
        }
        mock_exchange.ping = AsyncMock()
        mock_exchange.fetch_time = AsyncMock(return_value=time.time() * 1000)
        mock_exchange.close = AsyncMock()
        mock_exchange.timeout = 10000

        mock_session = AsyncMock()
        mock_session.close = AsyncMock()

        with patch('src.data_collection.core.enhanced_exchange_manager.ccxt.binance', return_value=mock_exchange):
            with patch('src.data_collection.core.enhanced_exchange_manager.aiohttp.ClientSession', return_value=mock_session):
                with patch('src.data_collection.core.enhanced_exchange_manager.redis.asyncio.Redis'):

                    # Initialize
                    await exchange_manager.initialize()

                    # Execute multiple requests
                    tasks = []
                    for _ in range(10):
                        task = exchange_manager.execute_request('fetch_ticker', 'BTC/USDT')
                        tasks.append(task)

                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    # All requests should succeed
                    assert all(not isinstance(r, Exception) for r in results)

                    # Check metrics
                    connection = exchange_manager.connections["binance"]
                    assert connection.success_count == 10
                    assert connection.error_count == 0
                    assert connection.get_success_rate() == 1.0

                    # Get status
                    status = await exchange_manager.get_exchange_status("binance")
                    assert status["status"] == "healthy"
                    assert status["success_rate"] == 1.0

                    # Close
                    await exchange_manager.close()

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, exchange_manager, mock_config):
        """Test error handling and recovery mechanisms."""
        mock_exchange = AsyncMock()
        mock_exchange.fetch_ticker.side_effect = [
            Exception("Network error"),
            Exception("Rate limit exceeded"),
            {"symbol": "BTC/USDT", "last": 50000.0}  # Success
        ]
        mock_exchange.ping = AsyncMock()
        mock_exchange.fetch_time = AsyncMock(return_value=time.time() * 1000)
        mock_exchange.close = AsyncMock()
        mock_exchange.timeout = 10000

        mock_session = AsyncMock()
        mock_session.close = AsyncMock()

        with patch('src.data_collection.core.enhanced_exchange_manager.ccxt.binance', return_value=mock_exchange):
            with patch('src.data_collection.core.enhanced_exchange_manager.aiohttp.ClientSession', return_value=mock_session):
                await exchange_manager.initialize()

                # Test error handling
                connection = exchange_manager.connections["binance"]
                with patch.object(exchange_manager.connection_pool, 'get_connection', return_value=connection):
                    with patch.object(exchange_manager.connection_pool, 'return_connection'):
                        # First request should fail
                        with pytest.raises(ExchangeConnectionError):
                            await exchange_manager.execute_request('fetch_ticker', 'BTC/USDT')

                        assert connection.error_count == 1
                        assert connection.health_score < 1.0

                        # Health score should gradually recover
                        initial_score = connection.health_score
                        connection.update_success(100.0)
                        assert connection.health_score > initial_score

    @pytest.mark.asyncio
    async def test_performance_under_load(self, exchange_manager, mock_config):
        """Test performance under high load."""
        mock_exchange = AsyncMock()
        mock_exchange.fetch_ticker.return_value = {"symbol": "BTC/USDT", "last": 50000.0}
        mock_exchange.ping = AsyncMock()
        mock_exchange.fetch_time = AsyncMock(return_value=time.time() * 1000)
        mock_exchange.close = AsyncMock()
        mock_exchange.timeout = 10000

        mock_session = AsyncMock()
        mock_session.close = AsyncMock()

        with patch('src.data_collection.core.enhanced_exchange_manager.ccxt.binance', return_value=mock_exchange):
            with patch('src.data_collection.core.enhanced_exchange_manager.aiohttp.ClientSession', return_value=mock_session):
                await exchange_manager.initialize()

                # Generate high load
                start_time = time.time()
                tasks = []

                for _ in range(100):  # 100 concurrent requests
                    task = exchange_manager.execute_request('fetch_ticker', 'BTC/USDT')
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()

                # Performance assertions
                assert (end_time - start_time) < 10.0  # Should complete within 10 seconds
                assert all(not isinstance(r, Exception) for r in results)  # All should succeed

                # Check connection health
                connection = exchange_manager.connections["binance"]
                assert connection.success_count == 100
                assert connection.is_healthy()

    @pytest.mark.asyncio
    async def test_configuration_reloading(self, exchange_manager, mock_config):
        """Test configuration reloading capabilities."""
        # This would test configuration reloading if implemented
        # For now, just verify the manager can be initialized and closed multiple times
        mock_exchange = AsyncMock()
        mock_exchange.ping = AsyncMock()
        mock_exchange.fetch_time = AsyncMock(return_value=time.time() * 1000)
        mock_exchange.close = AsyncMock()
        mock_exchange.timeout = 10000

        mock_session = AsyncMock()
        mock_session.close = AsyncMock()

        with patch('src.data_collection.core.enhanced_exchange_manager.ccxt.binance', return_value=mock_exchange):
            with patch('src.data_collection.core.enhanced_exchange_manager.aiohttp.ClientSession', return_value=mock_session):
                # Initialize and close multiple times
                for _ in range(3):
                    await exchange_manager.initialize()
                    await exchange_manager.close()

                    assert not exchange_manager._running
                    assert len(exchange_manager.connections) == 0