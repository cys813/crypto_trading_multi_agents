"""
Tests for the DataProcessor class.
"""

import pytest
import numpy as np
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from ..core.data_processor import DataProcessor, ProcessingResult
from ..models.market_data import OHLCVData, OrderBookData, TradeData, TickerData
from ..config.settings import Settings


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        DATA_QUALITY_THRESHOLD=0.95
    )


@pytest.fixture
def data_processor(settings):
    """Create a DataProcessor instance for testing."""
    with patch('src.data_collection.core.data_processor.get_settings', return_value=settings):
        return DataProcessor()


class TestDataProcessor:
    """Test cases for DataProcessor."""

    @pytest.mark.asyncio
    async def test_process_ohlcv_valid_data(self, data_processor):
        """Test processing valid OHLCV data."""
        raw_data = [
            [1640995200000, 50000.0, 51000.0, 49000.0, 50500.0, 100.0],
            [1640995260000, 50500.0, 51500.0, 49500.0, 51000.0, 150.0]
        ]

        result = await data_processor.process_ohlcv(raw_data, "binance", "BTC/USDT", "1h")

        assert len(result) == 2
        assert result[0].exchange == "binance"
        assert result[0].symbol == "BTC/USDT"
        assert result[0].timeframe == "1h"
        assert result[0].open == 50000.0
        assert result[0].close == 50500.0
        assert result[0].volume == 100.0

    @pytest.mark.asyncio
    async def test_process_ohlcv_empty_data(self, data_processor):
        """Test processing empty OHLCV data."""
        result = await data_processor.process_ohlcv([], "binance", "BTC/USDT", "1h")
        assert result == []

    @pytest.mark.asyncio
    async def test_process_ohlcv_invalid_data(self, data_processor):
        """Test processing invalid OHLCV data."""
        # Invalid timestamp
        raw_data = [["invalid", 50000.0, 51000.0, 49000.0, 50500.0, 100.0]]

        result = await data_processor.process_ohlcv(raw_data, "binance", "BTC/USDT", "1h")
        assert result == []

    @pytest.mark.asyncio
    async def test_process_ohlcv_price_anomaly(self, data_processor):
        """Test processing OHLCV data with price anomaly."""
        raw_data = [
            [1640995200000, 50000.0, 51000.0, 49000.0, 50500.0, 100.0],
            [1640995260000, 50500.0, 100000.0, 49500.0, 51000.0, 150.0],  # Anomalous high
            [1640995320000, 51000.0, 51500.0, 50500.0, 51200.0, 120.0]
        ]

        with patch.object(data_processor, '_detect_price_anomalies', return_value=[1]):
            result = await data_processor.process_ohlcv(raw_data, "binance", "BTC/USDT", "1h")

            assert len(result) == 3
            assert data_processor.stats['anomalies_detected'] > 0

    @pytest.mark.asyncio
    async def test_process_orderbook_valid_data(self, data_processor):
        """Test processing valid order book data."""
        raw_data = {
            "bids": [[49900.0, 1.0], [49800.0, 2.0]],
            "asks": [[50100.0, 1.0], [50200.0, 2.0]]
        }

        result = await data_processor.process_orderbook(raw_data, "binance", "BTC/USDT")

        assert result is not None
        assert result.exchange == "binance"
        assert result.symbol == "BTC/USDT"
        assert result.best_bid == 49900.0
        assert result.best_ask == 50100.0
        assert result.spread == 200.0

    @pytest.mark.asyncio
    async def test_process_orderbook_empty_data(self, data_processor):
        """Test processing empty order book data."""
        result = await data_processor.process_orderbook({}, "binance", "BTC/USDT")
        assert result is None

    @pytest.mark.asyncio
    async def test_process_orderbook_inverted_spread(self, data_processor):
        """Test processing order book with inverted spread."""
        raw_data = {
            "bids": [[50100.0, 1.0], [50200.0, 2.0]],  # Higher than asks
            "asks": [[49900.0, 1.0], [49800.0, 2.0]]
        }

        result = await data_processor.process_orderbook(raw_data, "binance", "BTC/USDT")

        # Should still process but calculate negative spread
        assert result is not None
        assert result.spread < 0

    @pytest.mark.asyncio
    async def test_process_trades_valid_data(self, data_processor):
        """Test processing valid trades data."""
        raw_data = [
            {"timestamp": 1640995200000, "price": 50000.0, "amount": 1.0, "side": "buy"},
            {"timestamp": 1640995210000, "price": 50100.0, "amount": 0.5, "side": "sell"}
        ]

        result = await data_processor.process_trades(raw_data, "binance", "BTC/USDT")

        assert len(result) == 2
        assert result[0].exchange == "binance"
        assert result[0].symbol == "BTC/USDT"
        assert result[0].price == 50000.0
        assert result[0].side == "buy"
        assert result[0].value == 50000.0

    @pytest.mark.asyncio
    async def test_process_trades_empty_data(self, data_processor):
        """Test processing empty trades data."""
        result = await data_processor.process_trades([], "binance", "BTC/USDT")
        assert result == []

    @pytest.mark.asyncio
    async def test_process_trades_large_trade_detection(self, data_processor):
        """Test processing trades with large trade detection."""
        raw_data = [
            {"timestamp": 1640995200000, "price": 50000.0, "amount": 1.0, "side": "buy"},
            {"timestamp": 1640995210000, "price": 50100.0, "amount": 1000.0, "side": "sell"}  # Large trade
        ]

        result = await data_processor.process_trades(raw_data, "binance", "BTC/USDT")

        assert len(result) == 2
        assert result[1].is_large_trade

    @pytest.mark.asyncio
    async def test_process_ticker_valid_data(self, data_processor):
        """Test processing valid ticker data."""
        raw_data = {
            "symbol": "BTC/USDT",
            "last": 50000.0,
            "bid": 49900.0,
            "ask": 50100.0,
            "high": 51000.0,
            "low": 49000.0,
            "volume": 1000.0,
            "quoteVolume": 50000000.0
        }

        result = await data_processor.process_ticker(raw_data, "binance", "BTC/USDT")

        assert result is not None
        assert result.exchange == "binance"
        assert result.symbol == "BTC/USDT"
        assert result.last == 50000.0
        assert result.bid == 49900.0
        assert result.ask == 50100.0

    @pytest.mark.asyncio
    async def test_process_ticker_empty_data(self, data_processor):
        """Test processing empty ticker data."""
        result = await data_processor.process_ticker({}, "binance", "BTC/USDT")
        assert result is None

    @pytest.mark.asyncio
    async def test_process_ticker_change_calculation(self, data_processor):
        """Test processing ticker with change calculation."""
        raw_data = {
            "symbol": "BTC/USDT",
            "last": 51000.0,
            "bid": 50900.0,
            "ask": 51100.0,
            "open": 50000.0,
            "close": 51000.0,
            "volume": 1000.0
        }

        result = await data_processor.process_ticker(raw_data, "binance", "BTC/USDT")

        assert result is not None
        assert result.change == 1000.0  # 51000 - 50000
        assert result.change_percent == 2.0  # (1000 / 50000) * 100

    def test_detect_price_anomalies(self, data_processor):
        """Test price anomaly detection."""
        prices = [50000.0, 50100.0, 50200.0, 100000.0, 50300.0]  # Anomaly at index 3

        anomalies = data_processor._detect_price_anomalies(prices, threshold=2.0)

        assert 3 in anomalies  # Should detect the anomalous price

    def test_detect_volume_anomalies(self, data_processor):
        """Test volume anomaly detection."""
        volumes = [100.0, 150.0, 120.0, 10000.0, 130.0]  # Anomaly at index 3

        anomalies = data_processor._detect_volume_anomalies(volumes, threshold=2.0)

        assert 3 in anomalies  # Should detect the anomalous volume

    @pytest.mark.asyncio
    async def test_clean_ohlcv_data(self, data_processor):
        """Test OHLCV data cleaning."""
        # Create OHLCV data with outlier
        ohlcv_data = [
            OHLCVData(
                exchange="binance",
                symbol="BTC/USDT",
                timeframe="1h",
                timestamp=datetime.now(timezone.utc),
                open=50000.0,
                high=51000.0,
                low=49000.0,
                close=50500.0,
                volume=100.0
            ),
            OHLCVData(
                exchange="binance",
                symbol="BTC/USDT",
                timeframe="1h",
                timestamp=datetime.now(timezone.utc),
                open=50500.0,
                high=100000.0,  # Outlier
                low=49500.0,
                close=51000.0,
                volume=150.0
            ),
            OHLCVData(
                exchange="binance",
                symbol="BTC/USDT",
                timeframe="1h",
                timestamp=datetime.now(timezone.utc),
                open=51000.0,
                high=51500.0,
                low=50500.0,
                close=51200.0,
                volume=120.0
            )
        ]

        cleaned_data, warnings = await data_processor.clean_ohlcv_data(ohlcv_data)

        assert len(cleaned_data) == 3
        assert len(warnings) > 0
        assert data_processor.stats['outliers_corrected'] > 0

    @pytest.mark.asyncio
    async def test_aggregate_ohlcv_data(self, data_processor):
        """Test OHLCV data aggregation."""
        # Create 1-minute OHLCV data
        ohlcv_data = []
        base_time = datetime(2022, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        for i in range(5):
            ohlcv_data.append(OHLCVData(
                exchange="binance",
                symbol="BTC/USDT",
                timeframe="1m",
                timestamp=base_time + timedelta(minutes=i),
                open=50000.0 + i * 100,
                high=50000.0 + i * 100 + 50,
                low=50000.0 + i * 100 - 50,
                close=50000.0 + i * 100 + 25,
                volume=100.0 + i * 10
            ))

        # Aggregate to 5-minute
        aggregated = await data_processor.aggregate_ohlcv_data(ohlcv_data, "5m")

        assert len(aggregated) == 1
        assert aggregated[0].timeframe == "5m"
        assert aggregated[0].open == 50000.0
        assert aggregated[0].high == 50200.0  # Max of all highs
        assert aggregated[0].low == 49950.0   # Min of all lows
        assert aggregated[0].close == 50125.0  # Last close
        assert aggregated[0].volume == 550.0   # Sum of all volumes

    def test_update_stats(self, data_processor):
        """Test statistics updating."""
        data_processor._update_stats(True, 10, 2, datetime.now())

        assert data_processor.stats['total_processed'] == 1
        assert data_processor.stats['successful_processes'] == 1
        assert data_processor.stats['data_points_processed'] == 10

    def test_reset_stats(self, data_processor):
        """Test statistics reset."""
        # Add some stats
        data_processor.stats['total_processed'] = 10
        data_processor.stats['successful_processes'] = 8

        data_processor.reset_stats()

        assert data_processor.stats['total_processed'] == 0
        assert data_processor.stats['successful_processes'] == 0
        assert data_processor.stats['data_points_processed'] == 0

    def test_get_processing_stats(self, data_processor):
        """Test getting processing statistics."""
        # Add some stats
        data_processor.stats['total_processed'] = 10
        data_processor.stats['successful_processes'] = 8
        data_processor.stats['data_points_processed'] = 100

        stats = data_processor.get_processing_stats()

        assert stats['total_processed'] == 10
        assert stats['successful_processes'] == 8
        assert stats['success_rate'] == 0.8
        assert stats['failure_rate'] == 0.2