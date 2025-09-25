"""
Tests for the ExchangeManager class.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from ..core.exchange_manager import ExchangeManager
from ..config.settings import Settings


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        EXCHANGE_CONFIGS={
            "binance": {
                "apiKey": "test_key",
                "secret": "test_secret",
                "sandbox": True,
                "enableRateLimit": True,
                "rateLimit": 100,
                "timeout": 5000,
                "options": {"defaultType": "spot"}
            }
        },
        MAX_RETRIES=2,
        RETRY_DELAY=100
    )


@pytest.fixture
def exchange_manager(settings):
    """Create an ExchangeManager instance for testing."""
    with patch('src.data_collection.core.exchange_manager.get_settings', return_value=settings):
        manager = ExchangeManager()
        return manager


@pytest.fixture
def mock_exchange():
    """Create a mock exchange."""
    exchange = AsyncMock()
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
        [1640995200000, 50000.0, 51000.0, 49000.0, 50500.0, 100.0],
        [1640995260000, 50500.0, 51500.0, 49500.0, 51000.0, 150.0]
    ])
    exchange.fetch_order_book = AsyncMock(return_value={
        "bids": [[49900.0, 1.0], [49800.0, 2.0]],
        "asks": [[50100.0, 1.0], [50200.0, 2.0]]
    })
    exchange.fetch_trades = AsyncMock(return_value=[
        {"timestamp": 1640995200000, "price": 50000.0, "amount": 1.0, "side": "buy"},
        {"timestamp": 1640995210000, "price": 50100.0, "amount": 0.5, "side": "sell"}
    ])
    exchange.fetch_balance = AsyncMock(return_value={
        "USDT": {"free": 10000.0, "used": 1000.0, "total": 11000.0}
    })
    exchange.fetch_positions = AsyncMock(return_value=[])
    exchange.fetch_open_orders = AsyncMock(return_value=[])
    exchange.close = AsyncMock()
    return exchange


class TestExchangeManager:
    """Test cases for ExchangeManager."""

    @pytest.mark.asyncio
    async def test_initialization(self, exchange_manager):
        """Test ExchangeManager initialization."""
        assert "binance" in exchange_manager.exchanges
        assert "binance" in exchange_manager.rate_limiter
        assert "binance" in exchange_manager.exchange_status
        assert "binance" in exchange_manager.connection_pools

    @pytest.mark.asyncio
    async def test_get_exchanges(self, exchange_manager):
        """Test getting list of exchanges."""
        exchanges = await exchange_manager.get_all_exchanges()
        assert "binance" in exchanges

    @pytest.mark.asyncio
    async def test_get_exchange_status(self, exchange_manager):
        """Test getting exchange status."""
        status = await exchange_manager.get_exchange_status("binance")
        assert "status" in status
        assert "success_rate" in status
        assert "healthy" in status

    @pytest.mark.asyncio
    async def test_get_markets(self, exchange_manager, mock_exchange):
        """Test getting markets from exchange."""
        with patch.object(exchange_manager, 'get_exchange', return_value=mock_exchange):
            markets = await exchange_manager.get_markets("binance")
            assert len(markets) == 2
            assert markets[0]["symbol"] == "BTC/USDT"

    @pytest.mark.asyncio
    async def test_get_ticker(self, exchange_manager, mock_exchange):
        """Test getting ticker data."""
        with patch.object(exchange_manager, 'get_exchange', return_value=mock_exchange):
            ticker = await exchange_manager.get_ticker("binance", "BTC/USDT")
            assert ticker["symbol"] == "BTC/USDT"
            assert ticker["last"] == 50000.0

    @pytest.mark.asyncio
    async def test_get_ohlcv(self, exchange_manager, mock_exchange):
        """Test getting OHLCV data."""
        with patch.object(exchange_manager, 'get_exchange', return_value=mock_exchange):
            ohlcv = await exchange_manager.get_ohlcv("binance", "BTC/USDT", "1h")
            assert len(ohlcv) == 2
            assert ohlcv[0][1] == 50000.0  # open price

    @pytest.mark.asyncio
    async def test_get_order_book(self, exchange_manager, mock_exchange):
        """Test getting order book data."""
        with patch.object(exchange_manager, 'get_exchange', return_value=mock_exchange):
            orderbook = await exchange_manager.get_order_book("binance", "BTC/USDT")
            assert "bids" in orderbook
            assert "asks" in orderbook
            assert len(orderbook["bids"]) == 2

    @pytest.mark.asyncio
    async def test_get_trades(self, exchange_manager, mock_exchange):
        """Test getting trades data."""
        with patch.object(exchange_manager, 'get_exchange', return_value=mock_exchange):
            trades = await exchange_manager.get_trades("binance", "BTC/USDT")
            assert len(trades) == 2
            assert trades[0]["side"] == "buy"

    @pytest.mark.asyncio
    async def test_rate_limiting(self, exchange_manager, mock_exchange):
        """Test rate limiting functionality."""
        # Set rate limit very low for testing
        exchange_manager.rate_limiter["binance"]["limit"] = 1
        exchange_manager.rate_limiter["binance"]["requests"] = 1

        with patch.object(exchange_manager, 'get_exchange', return_value=mock_exchange):
            # First request should work
            result1 = await exchange_manager.get_ticker("binance", "BTC/USDT")
            assert result1 is not None

            # Second request should be rate limited
            with pytest.raises(Exception):  # Should raise timeout or similar
                await exchange_manager.get_ticker("binance", "BTC/USDT")

    @pytest.mark.asyncio
    async def test_error_handling(self, exchange_manager):
        """Test error handling and retries."""
        mock_exchange = AsyncMock()
        mock_exchange.fetch_ticker.side_effect = Exception("Network error")

        with patch.object(exchange_manager, 'get_exchange', return_value=mock_exchange):
            # Should retry and eventually fail
            with pytest.raises(Exception):
                await exchange_manager.get_ticker("binance", "BTC/USDT")

    @pytest.mark.asyncio
    async def test_health_check(self, exchange_manager, mock_exchange):
        """Test health check functionality."""
        with patch.object(exchange_manager, 'get_exchange', return_value=mock_exchange):
            await exchange_manager.health_check("binance")

            status = await exchange_manager.get_exchange_status("binance")
            assert status["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_close(self, exchange_manager, mock_exchange):
        """Test closing exchange manager."""
        # Add a mock exchange to the manager
        exchange_manager.exchanges["binance"] = mock_exchange
        exchange_manager.connection_pools["binance"] = [mock_exchange]

        await exchange_manager.close()

        assert mock_exchange.close.called
        assert len(exchange_manager.exchanges) == 0
        assert len(exchange_manager.connection_pools) == 0

    @pytest.mark.asyncio
    async def test_connection_pool(self, exchange_manager, mock_exchange):
        """Test connection pool functionality."""
        # Add multiple exchanges to pool
        exchange_manager.connection_pools["binance"] = [mock_exchange, mock_exchange]

        # Get exchange from pool
        exchange = await exchange_manager.get_exchange("binance")
        assert exchange == mock_exchange

        # Pool should be empty now
        assert len(exchange_manager.connection_pools["binance"]) == 1

        # Return exchange to pool
        await exchange_manager.return_exchange("binance", exchange)
        assert len(exchange_manager.connection_pools["binance"]) == 2

    @pytest.mark.asyncio
    async def test_metrics_collection(self, exchange_manager, mock_exchange):
        """Test metrics collection."""
        with patch.object(exchange_manager, 'get_exchange', return_value=mock_exchange):
            # Make a successful request
            await exchange_manager.get_ticker("binance", "BTC/USDT")

            # Check metrics were recorded
            assert len(exchange_manager.metrics.request_metrics) > 0
            assert exchange_manager.metrics.request_metrics[-1].success
            assert exchange_manager.metrics.request_metrics[-1].exchange == "binance"
            assert exchange_manager.metrics.request_metrics[-1].method == "fetch_ticker"