"""
Tests for the DataCollector class.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from ..core.data_collector import DataCollector, CollectionTask
from ..config.settings import Settings


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        DATA_COLLECTION_INTERVAL=1000,
        MAX_CONCURRENT_CONNECTIONS=10,
        DATA_QUALITY_THRESHOLD=0.95
    )


@pytest.fixture
def data_collector(settings):
    """Create a DataCollector instance for testing."""
    with patch('src.data_collection.core.data_collector.get_settings', return_value=settings):
        with patch('src.data_collection.core.data_collector.ExchangeManager') as mock_em:
            with patch('src.data_collection.core.data_collector.DataProcessor') as mock_dp:
                with patch('src.data_collection.core.data_collector.MetricsCollector') as mock_mc:
                    collector = DataCollector()
                    collector.exchange_manager = mock_em.return_value
                    collector.data_processor = mock_dp.return_value
                    collector.metrics = mock_mc.return_value
                    return collector


@pytest.fixture
def mock_exchange_manager():
    """Create a mock exchange manager."""
    manager = AsyncMock()
    manager.get_all_exchanges.return_value = ["binance", "okx"]
    manager.get_markets.return_value = [
        {"symbol": "BTC/USDT", "active": True},
        {"symbol": "ETH/USDT", "active": True}
    ]
    return manager


@pytest.fixture
def mock_data_processor():
    """Create a mock data processor."""
    processor = AsyncMock()
    processor.process_ohlcv.return_value = []
    processor.process_orderbook.return_value = None
    processor.process_trades.return_value = []
    processor.process_ticker.return_value = None
    return processor


class TestDataCollector:
    """Test cases for DataCollector."""

    @pytest.mark.asyncio
    async def test_initialization(self, data_collector):
        """Test DataCollector initialization."""
        assert data_collector.tasks == {}
        assert data_collector.running_tasks == {}
        assert data_collector.stats['total_collections'] == 0

    @pytest.mark.asyncio
    async def test_add_collection_task(self, data_collector):
        """Test adding a collection task."""
        task_id = await data_collector.add_collection_task(
            "test_task",
            "binance",
            "BTC/USDT",
            "ohlcv",
            60,
            {"timeframe": "1h"}
        )

        assert task_id == "test_task"
        assert task_id in data_collector.tasks
        assert data_collector.tasks[task_id].exchange == "binance"
        assert data_collector.tasks[task_id].symbol == "BTC/USDT"
        assert data_collector.tasks[task_id].data_type == "ohlcv"

    @pytest.mark.asyncio
    async def test_add_duplicate_task(self, data_collector):
        """Test adding a duplicate collection task."""
        # Add first task
        await data_collector.add_collection_task(
            "test_task",
            "binance",
            "BTC/USDT",
            "ohlcv",
            60
        )

        # Try to add duplicate task
        with pytest.raises(ValueError, match="Task with ID 'test_task' already exists"):
            await data_collector.add_collection_task(
                "test_task",
                "binance",
                "ETH/USDT",
                "ohlcv",
                60
            )

    @pytest.mark.asyncio
    async def test_remove_collection_task(self, data_collector):
        """Test removing a collection task."""
        # Add task first
        await data_collector.add_collection_task(
            "test_task",
            "binance",
            "BTC/USDT",
            "ohlcv",
            60
        )

        # Remove task
        await data_collector.remove_collection_task("test_task")
        assert "test_task" not in data_collector.tasks

    @pytest.mark.asyncio
    async def test_remove_nonexistent_task(self, data_collector):
        """Test removing a nonexistent task."""
        # Should not raise an error
        await data_collector.remove_collection_task("nonexistent_task")

    @pytest.mark.asyncio
    async def test_run_pending_tasks(self, data_collector):
        """Test running pending collection tasks."""
        # Add tasks with different next_run times
        now = datetime.now()

        task1 = CollectionTask(
            id="task1",
            exchange="binance",
            symbol="BTC/USDT",
            data_type="ohlcv",
            interval=60,
            next_run=now - timedelta(seconds=1)  # Should run
        )

        task2 = CollectionTask(
            id="task2",
            exchange="binance",
            symbol="ETH/USDT",
            data_type="ohlcv",
            interval=60,
            next_run=now + timedelta(seconds=1)  # Should not run
        )

        data_collector.tasks["task1"] = task1
        data_collector.tasks["task2"] = task2

        # Mock the execution method
        data_collector._execute_collection = AsyncMock()

        # Run pending tasks
        await data_collector.run_pending_tasks()

        # Only task1 should have been executed
        assert data_collector._execute_collection.call_count == 1
        data_collector._execute_collection.assert_called_with(task1)

    @pytest.mark.asyncio
    async def test_collect_ohlcv_data(self, data_collector):
        """Test collecting OHLCV data."""
        # Mock exchange manager response
        ohlcv_data = [
            [1640995200000, 50000.0, 51000.0, 49000.0, 50500.0, 100.0],
            [1640995260000, 50500.0, 51500.0, 49500.0, 51000.0, 150.0]
        ]

        data_collector.exchange_manager.get_ohlcv = AsyncMock(return_value=ohlcv_data)

        # Mock data processor response
        processed_data = [MagicMock()]
        data_collector.data_processor.process_ohlcv = AsyncMock(return_value=processed_data)

        # Mock data storage
        data_collector._store_ohlcv_data = AsyncMock()

        # Mock validation
        data_collector.validator.validate_ohlcv = MagicMock(return_value=MagicMock(
            overall_score=0.99,
            accuracy_score=0.99,
            completeness_score=0.99,
            timeliness_score=0.99
        ))

        # Create and execute task
        task = CollectionTask(
            id="test_task",
            exchange="binance",
            symbol="BTC/USDT",
            data_type="ohlcv",
            interval=60,
            parameters={"timeframe": "1h", "limit": 100}
        )

        result = await data_collector._collect_ohlcv(task)

        # Verify the data was collected and processed
        assert result == ohlcv_data
        data_collector.exchange_manager.get_ohlcv.assert_called_once_with(
            "binance", "BTC/USDT", "1h", limit=100
        )
        data_collector.data_processor.process_ohlcv.assert_called_once()
        data_collector._store_ohlcv_data.assert_called_once_with(processed_data)

    @pytest.mark.asyncio
    async def test_collect_orderbook_data(self, data_collector):
        """Test collecting order book data."""
        # Mock exchange manager response
        orderbook_data = {
            "bids": [[49900.0, 1.0], [49800.0, 2.0]],
            "asks": [[50100.0, 1.0], [50200.0, 2.0]]
        }

        data_collector.exchange_manager.get_order_book = AsyncMock(return_value=orderbook_data)

        # Mock data processor response
        processed_data = MagicMock()
        data_collector.data_processor.process_orderbook = AsyncMock(return_value=processed_data)

        # Mock data storage
        data_collector._store_orderbook_data = AsyncMock()

        # Mock validation
        data_collector.validator.validate_orderbook = MagicMock(return_value=MagicMock(
            overall_score=0.99,
            accuracy_score=0.99,
            completeness_score=0.99,
            timeliness_score=0.99
        ))

        # Create and execute task
        task = CollectionTask(
            id="test_task",
            exchange="binance",
            symbol="BTC/USDT",
            data_type="orderbook",
            interval=30,
            parameters={"limit": 20}
        )

        result = await data_collector._collect_orderbook(task)

        # Verify the data was collected and processed
        assert result == orderbook_data
        data_collector.exchange_manager.get_order_book.assert_called_once_with(
            "binance", "BTC/USDT", limit=20
        )
        data_collector.data_processor.process_orderbook.assert_called_once()
        data_collector._store_orderbook_data.assert_called_once_with(processed_data)

    @pytest.mark.asyncio
    async def test_collect_trades_data(self, data_collector):
        """Test collecting trades data."""
        # Mock exchange manager response
        trades_data = [
            {"timestamp": 1640995200000, "price": 50000.0, "amount": 1.0, "side": "buy"},
            {"timestamp": 1640995210000, "price": 50100.0, "amount": 0.5, "side": "sell"}
        ]

        data_collector.exchange_manager.get_trades = AsyncMock(return_value=trades_data)

        # Mock data processor response
        processed_data = [MagicMock(), MagicMock()]
        data_collector.data_processor.process_trades = AsyncMock(return_value=processed_data)

        # Mock data storage
        data_collector._store_trades_data = AsyncMock()

        # Mock validation
        data_collector.validator.validate_trades = MagicMock(return_value=MagicMock(
            overall_score=0.99,
            accuracy_score=0.99,
            completeness_score=0.99,
            timeliness_score=0.99
        ))

        # Create and execute task
        task = CollectionTask(
            id="test_task",
            exchange="binance",
            symbol="BTC/USDT",
            data_type="trades",
            interval=60,
            parameters={"limit": 100}
        )

        result = await data_collector._collect_trades(task)

        # Verify the data was collected and processed
        assert result == trades_data
        data_collector.exchange_manager.get_trades.assert_called_once_with(
            "binance", "BTC/USDT", limit=100
        )
        data_collector.data_processor.process_trades.assert_called_once()
        data_collector._store_trades_data.assert_called_once_with(processed_data)

    @pytest.mark.asyncio
    async def test_collect_ticker_data(self, data_collector):
        """Test collecting ticker data."""
        # Mock exchange manager response
        ticker_data = {
            "symbol": "BTC/USDT",
            "last": 50000.0,
            "bid": 49900.0,
            "ask": 50100.0,
            "volume": 1000.0
        }

        data_collector.exchange_manager.get_ticker = AsyncMock(return_value=ticker_data)

        # Mock data processor response
        processed_data = MagicMock()
        data_collector.data_processor.process_ticker = AsyncMock(return_value=processed_data)

        # Mock data storage
        data_collector._store_ticker_data = AsyncMock()

        # Mock validation
        data_collector.validator.validate_ticker = MagicMock(return_value=MagicMock(
            overall_score=0.99,
            accuracy_score=0.99,
            completeness_score=0.99,
            timeliness_score=0.99
        ))

        # Create and execute task
        task = CollectionTask(
            id="test_task",
            exchange="binance",
            symbol="BTC/USDT",
            data_type="ticker",
            interval=60,
            parameters={}
        )

        result = await data_collector._collect_ticker(task)

        # Verify the data was collected and processed
        assert result == ticker_data
        data_collector.exchange_manager.get_ticker.assert_called_once_with(
            "binance", "BTC/USDT"
        )
        data_collector.data_processor.process_ticker.assert_called_once()
        data_collector._store_ticker_data.assert_called_once_with(processed_data)

    @pytest.mark.asyncio
    async def test_error_handling(self, data_collector):
        """Test error handling during data collection."""
        # Mock exchange manager to raise an error
        data_collector.exchange_manager.get_ohlcv = AsyncMock(side_effect=Exception("Network error"))

        # Create and execute task
        task = CollectionTask(
            id="test_task",
            exchange="binance",
            symbol="BTC/USDT",
            data_type="ohlcv",
            interval=60,
            parameters={"timeframe": "1h", "limit": 100}
        )

        result = await data_collector._collect_ohlcv(task)

        # Should return None on error
        assert result is None

        # Stats should reflect the error
        assert data_collector.stats['total_collections'] == 1
        assert data_collector.stats['failed_collections'] == 1

    @pytest.mark.asyncio
    async def test_low_quality_data_handling(self, data_collector):
        """Test handling of low quality data."""
        # Mock exchange manager response
        ohlcv_data = [
            [1640995200000, 50000.0, 51000.0, 49000.0, 50500.0, 100.0]
        ]

        data_collector.exchange_manager.get_ohlcv = AsyncMock(return_value=ohlcv_data)

        # Mock validation to return low quality score
        data_collector.validator.validate_ohlcv = MagicMock(return_value=MagicMock(
            overall_score=0.8,  # Below threshold
            accuracy_score=0.8,
            completeness_score=0.8,
            timeliness_score=0.8
        ))

        # Create and execute task
        task = CollectionTask(
            id="test_task",
            exchange="binance",
            symbol="BTC/USDT",
            data_type="ohlcv",
            interval=60,
            parameters={"timeframe": "1h", "limit": 100}
        )

        result = await data_collector._collect_ohlcv(task)

        # Should return None due to low quality
        assert result is None

    @pytest.mark.asyncio
    async def test_get_collection_status(self, data_collector):
        """Test getting collection status."""
        # Add some tasks
        await data_collector.add_collection_task("task1", "binance", "BTC/USDT", "ohlcv", 60)
        await data_collector.add_collection_task("task2", "binance", "ETH/USDT", "ohlcv", 60)

        # Make one task active
        data_collector.tasks["task1"].is_active = True

        status = data_collector.get_collection_status()

        assert status['total_tasks'] == 2
        assert status['active_tasks'] == 1
        assert status['running_tasks'] == 0
        assert 'tasks' in status
        assert len(status['tasks']) == 2

    @pytest.mark.asyncio
    async def test_callback_execution(self, data_collector):
        """Test that callbacks are executed correctly."""
        callback_called = False
        callback_data = None

        async def test_callback(task, data):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = data

        # Add task with callback
        await data_collector.add_collection_task(
            "test_task",
            "binance",
            "BTC/USDT",
            "ohlcv",
            60,
            callback=test_callback
        )

        # Mock successful data collection
        ohlcv_data = [
            [1640995200000, 50000.0, 51000.0, 49000.0, 50500.0, 100.0]
        ]
        data_collector.exchange_manager.get_ohlcv = AsyncMock(return_value=ohlcv_data)
        data_collector.data_processor.process_ohlcv = AsyncMock(return_value=[MagicMock()])
        data_collector._store_ohlcv_data = AsyncMock()
        data_collector.validator.validate_ohlcv = MagicMock(return_value=MagicMock(
            overall_score=0.99,
            accuracy_score=0.99,
            completeness_score=0.99,
            timeliness_score=0.99
        ))

        # Execute task
        task = data_collector.tasks["test_task"]
        await data_collector._execute_collection(task)

        # Verify callback was called
        assert callback_called
        assert callback_data == ohlcv_data