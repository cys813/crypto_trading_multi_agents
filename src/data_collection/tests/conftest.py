"""
Configuration file for pytest tests.
"""

import pytest
import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings for all tests."""
    with pytest.MonkeyPatch.context() as m:
        # Mock environment variables
        m.setenv("POSTGRES_HOST", "localhost")
        m.setenv("POSTGRES_PORT", "5432")
        m.setenv("POSTGRES_USER", "test_user")
        m.setenv("POSTGRES_PASSWORD", "test_password")
        m.setenv("POSTGRES_DB", "test_db")
        m.setenv("REDIS_HOST", "localhost")
        m.setenv("REDIS_PORT", "6379")
        m.setenv("LOG_LEVEL", "DEBUG")
        yield


@pytest.fixture
def sample_ohlcv_data():
    """Sample OHLCV data for testing."""
    return [
        [1640995200000, 50000.0, 51000.0, 49000.0, 50500.0, 100.0],
        [1640995260000, 50500.0, 51500.0, 49500.0, 51000.0, 150.0],
        [1640995320000, 51000.0, 52000.0, 50000.0, 51500.0, 200.0]
    ]


@pytest.fixture
def sample_orderbook_data():
    """Sample order book data for testing."""
    return {
        "bids": [[49900.0, 1.0], [49800.0, 2.0], [49700.0, 1.5]],
        "asks": [[50100.0, 1.0], [50200.0, 2.0], [50300.0, 1.5]]
    }


@pytest.fixture
def sample_trades_data():
    """Sample trades data for testing."""
    return [
        {"id": "1", "timestamp": 1640995200000, "price": 50000.0, "amount": 1.0, "side": "buy"},
        {"id": "2", "timestamp": 1640995210000, "price": 50100.0, "amount": 0.5, "side": "sell"},
        {"id": "3", "timestamp": 1640995220000, "price": 50050.0, "amount": 0.8, "side": "buy"}
    ]


@pytest.fixture
def sample_ticker_data():
    """Sample ticker data for testing."""
    return {
        "symbol": "BTC/USDT",
        "last": 50000.0,
        "bid": 49900.0,
        "ask": 50100.0,
        "high": 51000.0,
        "low": 49000.0,
        "volume": 1000.0,
        "quoteVolume": 50000000.0,
        "open": 49500.0,
        "close": 50000.0,
        "change": 500.0,
        "percentage": 1.01
    }