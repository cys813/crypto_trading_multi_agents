"""
Comprehensive tests for the Data Collector system.

This module tests all major components of the data collection system
including collectors, caching, quality monitoring, and performance optimization.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import tempfile
import os

from src.data_collection.core.data_collector import DataCollector, CollectionTask, LoadBalancer, DataQualityMonitor
from src.data_collection.collectors.orderbook_collector import OrderBookCollector, OrderBookCollectionTask
from src.data_collection.collectors.trades_collector import TradesCollector, TradesCollectionTask
from src.data_collection.storage.redis import RedisStorage
from src.data_collection.utils.performance import PerformanceMonitor, CircuitBreaker, RateLimiter
from src.data_collection.utils.validation import DataValidator, ValidationReport
from src.data_collection.models.market_data import OHLCVData, OrderBookData, TradeData, TickerData


class TestDataCollector:
    """Test cases for the main DataCollector class."""

    @pytest.fixture
    def data_collector(self):
        """Create a DataCollector instance for testing."""
        with patch('src.data_collection.core.data_collector.ExchangeManager'), \
             patch('src.data_collection.core.data_collector.DataProcessor'), \
             patch('src.data_collection.core.data_collector.MetricsCollector'), \
             patch('src.data_collection.core.data_collector.DataValidator'), \
             patch('src.data_collection.core.data_collector.RedisStorage'):

            collector = DataCollector()
            return collector

    @pytest.mark.asyncio
    async def test_data_collector_initialization(self, data_collector):
        """Test DataCollector initialization."""
        assert data_collector is not None
        assert data_collector.tasks == {}
        assert data_collector.running_tasks == {}
        assert data_collector.orderbook_collector is not None
        assert data_collector.trades_collector is not None
        assert data_collector.load_balancer is not None
        assert data_collector.quality_monitor is not None

    @pytest.mark.asyncio
    async def test_add_collection_task(self, data_collector):
        """Test adding a collection task."""
        task_id = await data_collector.add_collection_task(
            task_id="test_task",
            exchange="binance",
            symbol="BTC/USDT",
            data_type="ohlcv",
            interval=60
        )

        assert task_id == "test_task"
        assert task_id in data_collector.tasks
        assert data_collector.tasks[task_id].exchange == "binance"
        assert data_collector.tasks[task_id].symbol == "BTC/USDT"
        assert data_collector.tasks[task_id].data_type == "ohlcv"

    @pytest.mark.asyncio
    async def test_remove_collection_task(self, data_collector):
        """Test removing a collection task."""
        # Add a task first
        task_id = await data_collector.add_collection_task(
            task_id="test_task",
            exchange="binance",
            symbol="BTC/USDT",
            data_type="ohlcv",
            interval=60
        )

        # Remove the task
        await data_collector.remove_collection_task(task_id)

        assert task_id not in data_collector.tasks

    @pytest.mark.asyncio
    async def test_get_incremental_ohlcv(self, data_collector):
        """Test incremental OHLCV data fetching."""
        with patch.object(data_collector.exchange_manager, 'get_ohlcv') as mock_get_ohlcv, \
             patch.object(data_collector.redis, 'get') as mock_redis_get, \
             patch.object(data_collector.redis, 'set') as mock_redis_set:

            # Mock Redis returning a last timestamp
            mock_redis_get.return_value = "1640995200000"  # Jan 1, 2022

            # Mock exchange returning OHLCV data
            mock_ohlcv_data = [
                [1640995200000, 47000.0, 47500.0, 46900.0, 47400.0, 1000.0],
                [1640995260000, 47400.0, 47600.0, 47300.0, 47500.0, 800.0]
            ]
            mock_get_ohlcv.return_value = mock_ohlcv_data

            result = await data_collector.get_incremental_ohlcv(
                exchange="binance",
                symbol="BTC/USDT",
                timeframe="1m"
            )

            assert len(result) == 2
            assert result[0][0] == 1640995200000
            mock_redis_get.assert_called_once()
            mock_redis_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_task_prioritization(self, data_collector):
        """Test intelligent task prioritization."""
        # Add tasks with different priorities
        await data_collector.add_collection_task(
            task_id="ticker_task",
            exchange="binance",
            symbol="BTC/USDT",
            data_type="ticker",
            interval=5
        )

        await data_collector.add_collection_task(
            task_id="ohlcv_task",
            exchange="binance",
            symbol="BTC/USDT",
            data_type="ohlcv",
            interval=300
        )

        with patch.object(data_collector.exchange_manager, 'get_exchange_health') as mock_health:
            mock_health.return_value = {'healthy': True}

            await data_collector.prioritize_tasks()

            # Check that tasks are assigned to priority queues
            assert len(data_collector.priority_queues['high']) > 0 or \
                   len(data_collector.priority_queues['medium']) > 0 or \
                   len(data_collector.priority_queues['low']) > 0


class TestOrderBookCollector:
    """Test cases for the OrderBookCollector class."""

    @pytest.fixture
    def orderbook_collector(self):
        """Create an OrderBookCollector instance for testing."""
        with patch('src.data_collection.collectors.orderbook_collector.ExchangeManager'), \
             patch('src.data_collection.collectors.orderbook_collector.DataProcessor'):

            exchange_manager = Mock()
            data_processor = Mock()
            collector = OrderBookCollector(exchange_manager, data_processor)
            return collector

    @pytest.mark.asyncio
    async def test_orderbook_collector_initialization(self, orderbook_collector):
        """Test OrderBookCollector initialization."""
        assert orderbook_collector is not None
        assert orderbook_collector.tasks == {}
        assert orderbook_collector.max_concurrent_collections == 20

    @pytest.mark.asyncio
    async def test_add_orderbook_task(self, orderbook_collector):
        """Test adding an order book collection task."""
        with patch.object(orderbook_collector, '_initialize_default_tasks'):
            await orderbook_collector.add_collection_task(
                exchange="binance",
                symbol="BTC/USDT",
                depth=20,
                interval=1.0
            )

            task_id = "binance_BTC_USDT_orderbook"
            assert task_id in orderbook_collector.tasks
            assert orderbook_collector.tasks[task_id].exchange == "binance"
            assert orderbook_collector.tasks[task_id].symbol == "BTC/USDT"
            assert orderbook_collector.tasks[task_id].depth == 20

    @pytest.mark.asyncio
    async def test_collect_orderbook(self, orderbook_collector):
        """Test order book data collection."""
        with patch.object(orderbook_collector.exchange_manager, 'get_order_book') as mock_get_orderbook, \
             patch.object(orderbook_collector.data_processor, 'process_orderbook') as mock_process, \
             patch.object(orderbook_collector.validator, 'validate_orderbook') as mock_validate, \
             patch.object(orderbook_collector, '_store_orderbook_data') as mock_store, \
             patch.object(orderbook_collector, '_cache_orderbook_data') as mock_cache:

            # Mock exchange data
            mock_orderbook_data = {
                'bids': [[47000.0, 1.0], [46900.0, 2.0]],
                'asks': [[47100.0, 1.5], [47200.0, 1.0]],
                'timestamp': 1640995200000
            }
            mock_get_orderbook.return_value = mock_orderbook_data

            # Mock processed data
            mock_processed = Mock()
            mock_processed.quality_score = 0.95
            mock_process.return_value = mock_processed

            # Mock validation
            mock_validation = Mock()
            mock_validation.overall_score = 0.95
            mock_validate.return_value = mock_validation

            # Create and execute task
            task = OrderBookCollectionTask(
                exchange="binance",
                symbol="BTC/USDT",
                depth=20,
                interval=1.0
            )

            result = await orderbook_collector._execute_orderbook_collection(task)

            assert result == mock_processed
            mock_get_orderbook.assert_called_once()
            mock_process.assert_called_once()
            mock_store.assert_called_once()
            mock_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_orderbook_snapshot(self, orderbook_collector):
        """Test getting order book snapshot with market metrics."""
        with patch.object(orderbook_collector, 'get_latest_orderbook') as mock_get_latest:
            mock_latest = {
                'bids': [[47000.0, 1.0], [46900.0, 2.0]],
                'asks': [[47100.0, 1.5], [47200.0, 1.0]]
            }
            mock_get_latest.return_value = mock_latest

            snapshot = await orderbook_collector.get_orderbook_snapshot("binance", "BTC/USDT")

            assert snapshot is not None
            assert 'bid_depth_10' in snapshot
            assert 'ask_depth_10' in snapshot
            assert 'total_liquidity' in snapshot


class TestTradesCollector:
    """Test cases for the TradesCollector class."""

    @pytest.fixture
    def trades_collector(self):
        """Create a TradesCollector instance for testing."""
        with patch('src.data_collection.collectors.trades_collector.ExchangeManager'), \
             patch('src.data_collection.collectors.trades_collector.DataProcessor'):

            exchange_manager = Mock()
            data_processor = Mock()
            collector = TradesCollector(exchange_manager, data_processor)
            return collector

    @pytest.mark.asyncio
    async def test_trades_collector_initialization(self, trades_collector):
        """Test TradesCollector initialization."""
        assert trades_collector is not None
        assert trades_collector.tasks == {}
        assert trades_collector.max_concurrent_collections == 30

    @pytest.mark.asyncio
    async def test_add_trades_task(self, trades_collector):
        """Test adding a trades collection task."""
        with patch.object(trades_collector, '_initialize_default_tasks'):
            await trades_collector.add_collection_task(
                exchange="binance",
                symbol="BTC/USDT",
                limit=1000,
                interval=5.0,
                incremental_mode=True
            )

            task_id = "binance_BTC_USDT_trades"
            assert task_id in trades_collector.tasks
            assert trades_collector.tasks[task_id].exchange == "binance"
            assert trades_collector.tasks[task_id].symbol == "BTC/USDT"
            assert trades_collector.tasks[task_id].incremental_mode is True

    @pytest.mark.asyncio
    async def test_incremental_trades_fetch(self, trades_collector):
        """Test incremental trades fetching."""
        with patch.object(trades_collector.exchange_manager, 'get_trades_since') as mock_get_since, \
             patch.object(trades_collector.data_processor, 'process_trades') as mock_process, \
             patch.object(trades_collector.validator, 'validate_trades') as mock_validate, \
             patch.object(trades_collector, '_store_trades_data') as mock_store, \
             patch.object(trades_collector, '_cache_trades_data') as mock_cache:

            # Mock exchange data
            mock_trades_data = [
                {'id': '12345', 'timestamp': 1640995200000, 'price': 47000.0, 'amount': 1.0, 'side': 'buy'},
                {'id': '12346', 'timestamp': 1640995260000, 'price': 47100.0, 'amount': 0.5, 'side': 'sell'}
            ]
            mock_get_since.return_value = mock_trades_data

            # Mock processed data
            mock_processed = [
                Mock(trade_id='12345', quality_score=0.95),
                Mock(trade_id='12346', quality_score=0.96)
            ]
            mock_process.return_value = mock_processed

            # Mock validation
            mock_validation = Mock()
            mock_validation.overall_score = 0.95
            mock_validate.return_value = mock_validation

            # Create and execute task
            task = TradesCollectionTask(
                exchange="binance",
                symbol="BTC/USDT",
                limit=1000,
                interval=5.0,
                last_trade_id='12344'
            )

            result = await trades_collector._fetch_incremental_trades(task)

            assert len(result) == 2
            mock_get_since.assert_called_once()
            mock_process.assert_called_once()
            assert task.last_trade_id == '12346'

    @pytest.mark.asyncio
    async def test_get_trade_statistics(self, trades_collector):
        """Test getting trade statistics."""
        with patch('src.data_collection.collectors.trades_collector.get_timescaledb_session') as mock_get_session:
            # Mock database session
            mock_session = Mock()
            mock_get_session.return_value.__enter__.return_value = mock_session

            # Mock query result
            mock_stats = Mock()
            mock_stats.total_trades = 100
            mock_stats.total_volume = 5000000.0
            mock_stats.avg_price = 47000.0
            mock_stats.min_price = 46000.0
            mock_stats.max_price = 48000.0
            mock_stats.buy_volume = 3000000.0
            mock_stats.sell_volume = 2000000.0
            mock_session.query.return_value.filter.return_value.first.return_value = mock_stats

            stats = await trades_collector.get_trade_statistics("binance", "BTC/USDT", "1h")

            assert stats is not None
            assert stats['total_trades'] == 100
            assert stats['total_volume'] == 5000000.0
            assert stats['buy_ratio'] == 0.6  # 3M / 5M


class TestRedisStorage:
    """Test cases for the RedisStorage class."""

    @pytest.fixture
    def redis_storage(self):
        """Create a RedisStorage instance for testing."""
        with patch('aioredis.from_url'):
            storage = RedisStorage()
            storage.redis = Mock()
            return storage

    @pytest.mark.asyncio
    async def test_redis_initialization(self, redis_storage):
        """Test Redis initialization."""
        with patch('aioredis.from_url') as mock_from_url:
            mock_redis = Mock()
            mock_from_url.return_value = mock_redis

            await redis_storage.initialize()

            mock_from_url.assert_called_once()
            mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_and_get(self, redis_storage):
        """Test basic set and get operations."""
        redis_storage.redis.set.return_value = True
        redis_storage.redis.get.return_value = "test_value"

        await redis_storage.set("test_key", "test_value")
        result = await redis_storage.get("test_key")

        assert result == "test_value"
        redis_storage.redis.set.assert_called_once()
        redis_storage.redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_and_get_json(self, redis_storage):
        """Test JSON operations."""
        test_data = {"key": "value", "number": 123}
        redis_storage.redis.set.return_value = True
        redis_storage.redis.get.return_value = json.dumps(test_data)

        await redis_storage.set_json("test_json", test_data)
        result = await redis_storage.get_json("test_json")

        assert result == test_data

    @pytest.mark.asyncio
    async def test_cache_market_data(self, redis_storage):
        """Test market data caching."""
        test_data = {"price": 47000.0, "volume": 1000.0}
        redis_storage.redis.set.return_value = True

        await redis_storage.cache_market_data("ticker", "binance", "BTC/USDT", test_data)

        redis_storage.redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cached_market_data(self, redis_storage):
        """Test getting cached market data."""
        test_data = {"price": 47000.0, "volume": 1000.0}
        redis_storage.redis.get.return_value = json.dumps(test_data)

        result = await redis_storage.get_cached_market_data("ticker", "binance", "BTC/USDT")

        assert result == test_data


class TestPerformanceMonitor:
    """Test cases for the PerformanceMonitor class."""

    @pytest.fixture
    def performance_monitor(self):
        """Create a PerformanceMonitor instance for testing."""
        return PerformanceMonitor(max_samples=100)

    def test_start_operation(self, performance_monitor):
        """Test starting an operation."""
        operation_id = performance_monitor.start_operation("test_operation", data_points=10)

        assert operation_id is not None
        assert operation_id in performance_monitor.active_operations
        assert performance_monitor.active_operations[operation_id].operation == "test_operation"
        assert performance_monitor.active_operations[operation_id].data_points == 10

    def test_end_operation(self, performance_monitor):
        """Test ending an operation."""
        operation_id = performance_monitor.start_operation("test_operation")

        # Wait a bit to simulate operation duration
        import time
        time.sleep(0.01)

        metrics = performance_monitor.end_operation(operation_id, success=True)

        assert metrics is not None
        assert metrics.success is True
        assert metrics.duration is not None
        assert metrics.duration > 0
        assert operation_id not in performance_monitor.active_operations

    def test_get_operation_stats(self, performance_monitor):
        """Test getting operation statistics."""
        # Add some test operations
        for i in range(5):
            operation_id = performance_monitor.start_operation("test_operation")
            performance_monitor.end_operation(operation_id, success=i < 4)  # 4 success, 1 failure

        stats = performance_monitor.get_operation_stats("test_operation")

        assert stats['total_operations'] == 5
        assert stats['success_rate'] == 0.8  # 4/5
        assert stats['avg_duration'] > 0

    def test_cache_stats(self, performance_monitor):
        """Test cache statistics."""
        # Record some cache hits and misses
        for _ in range(7):
            performance_monitor.record_cache_hit()
        for _ in range(3):
            performance_monitor.record_cache_miss()

        cache_stats = performance_monitor.get_cache_stats()

        assert cache_stats['hits'] == 7
        assert cache_stats['misses'] == 3
        assert cache_stats['hit_rate'] == 0.7


class TestCircuitBreaker:
    """Test cases for the CircuitBreaker class."""

    @pytest.fixture
    def circuit_breaker(self):
        """Create a CircuitBreaker instance for testing."""
        return CircuitBreaker(failure_threshold=3, recovery_timeout=60)

    @pytest.mark.asyncio
    async def test_successful_operation(self, circuit_breaker):
        """Test successful operation through circuit breaker."""
        async def successful_operation():
            return "success"

        result = await circuit_breaker.call(successful_operation)

        assert result == "success"
        assert circuit_breaker.state == 'closed'
        assert circuit_breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_failed_operation(self, circuit_breaker):
        """Test failed operation through circuit breaker."""
        async def failed_operation():
            raise Exception("Operation failed")

        with pytest.raises(Exception):
            await circuit_breaker.call(failed_operation)

        assert circuit_breaker.failure_count == 1
        assert circuit_breaker.state == 'closed'

    @pytest.mark.asyncio
    async def test_circuit_breaker_trips(self, circuit_breaker):
        """Test circuit breaker tripping after threshold."""
        async def failed_operation():
            raise Exception("Operation failed")

        # Fail enough times to trip the circuit breaker
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failed_operation)

        assert circuit_breaker.failure_count == 3
        assert circuit_breaker.state == 'open'

        # Next call should fail immediately
        with pytest.raises(Exception) as exc_info:
            await circuit_breaker.call(failed_operation)

        assert "Circuit breaker is open" in str(exc_info.value)


class TestRateLimiter:
    """Test cases for the RateLimiter class."""

    @pytest.fixture
    def rate_limiter(self):
        """Create a RateLimiter instance for testing."""
        return RateLimiter(max_requests=5, time_window=10)

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests(self, rate_limiter):
        """Test rate limiter allows requests under limit."""
        # Should allow 5 requests
        for i in range(5):
            result = await rate_limiter.acquire()
            assert result is True

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_requests(self, rate_limiter):
        """Test rate limiter blocks requests over limit."""
        # Use up all requests
        for _ in range(5):
            await rate_limiter.acquire()

        # Next request should be blocked
        result = await rate_limiter.acquire()
        assert result is False

    @pytest.mark.asyncio
    async def test_rate_limiter_resets_after_window(self, rate_limiter):
        """Test rate limiter resets after time window."""
        # Use up all requests
        for _ in range(5):
            await rate_limiter.acquire()

        # Mock time passing beyond the window
        with patch('time.time') as mock_time:
            mock_time.return_value = time.time() + 11  # 11 seconds later

            # Should allow requests again
            result = await rate_limiter.acquire()
            assert result is True


class TestDataValidator:
    """Test cases for the DataValidator class."""

    @pytest.fixture
    def data_validator(self):
        """Create a DataValidator instance for testing."""
        return DataValidator()

    def test_validate_ohlcv_valid_data(self, data_validator):
        """Test OHLCV validation with valid data."""
        ohlcv_data = [
            [1640995200000, 47000.0, 47500.0, 46900.0, 47400.0, 1000.0],
            [1640995260000, 47400.0, 47600.0, 47300.0, 47500.0, 800.0]
        ]

        report = data_validator.validate_ohlcv(ohlcv_data, "binance", "BTC/USDT")

        assert report is not None
        assert report.data_type == "ohlcv"
        assert report.exchange == "binance"
        assert report.symbol == "BTC/USDT"
        assert report.result.value in ["valid", "warning"]  # Should be valid or warning

    def test_validate_ohlcv_invalid_data(self, data_validator):
        """Test OHLCV validation with invalid data."""
        # Invalid data: negative price
        ohlcv_data = [
            [1640995200000, -47000.0, 47500.0, 46900.0, 47400.0, 1000.0]
        ]

        report = data_validator.validate_ohlcv(ohlcv_data, "binance", "BTC/USDT")

        assert report is not None
        assert report.overall_score < 0.5  # Should have low score due to invalid data

    def test_validate_orderbook_valid_data(self, data_validator):
        """Test order book validation with valid data."""
        orderbook_data = {
            'bids': [[47000.0, 1.0], [46900.0, 2.0]],
            'asks': [[47100.0, 1.5], [47200.0, 1.0]],
            'timestamp': 1640995200000
        }

        report = data_validator.validate_orderbook(orderbook_data, "binance", "BTC/USDT")

        assert report is not None
        assert report.data_type == "orderbook"
        assert report.overall_score > 0.8  # Should have high score for valid data

    def test_validate_orderbook_invalid_data(self, data_validator):
        """Test order book validation with invalid data."""
        # Invalid data: bids >= asks (inverted spread)
        orderbook_data = {
            'bids': [[47100.0, 1.0], [47200.0, 2.0]],
            'asks': [[47000.0, 1.5], [46900.0, 1.0]]
        }

        report = data_validator.validate_orderbook(orderbook_data, "binance", "BTC/USDT")

        assert report is not None
        assert report.overall_score < 0.5  # Should have low score due to invalid spread


class TestLoadBalancer:
    """Test cases for the LoadBalancer class."""

    @pytest.fixture
    def load_balancer(self):
        """Create a LoadBalancer instance for testing."""
        return LoadBalancer()

    @pytest.mark.asyncio
    async def test_get_exchange_load(self, load_balancer):
        """Test getting exchange load."""
        load = await load_balancer.get_exchange_load("binance")

        assert load == 0.0  # Initial load should be 0

    @pytest.mark.asyncio
    async def test_update_exchange_load(self, load_balancer):
        """Test updating exchange load."""
        await load_balancer.update_exchange_load("binance", 0.5)

        load = await load_balancer.get_exchange_load("binance")
        assert load == 0.5

    @pytest.mark.asyncio
    async def test_get_best_exchange(self, load_balancer):
        """Test getting best exchange based on load."""
        # Set different loads for exchanges
        await load_balancer.update_exchange_load("binance", 0.8)
        await load_balancer.update_exchange_load("okx", 0.3)

        best_exchange = await load_balancer.get_best_exchange(["binance", "okx"])

        assert best_exchange == "okx"  # Should return exchange with lower load

    @pytest.mark.asyncio
    async def test_can_handle_task(self, load_balancer):
        """Test checking if exchange can handle task."""
        await load_balancer.update_exchange_load("binance", 0.8)

        # Should be able to handle small task
        can_handle = await load_balancer.can_handle_task("binance", 0.1)
        assert can_handle is True

        # Should not be able to handle large task
        can_handle = await load_balancer.can_handle_task("binance", 0.3)
        assert can_handle is False


class TestDataQualityMonitor:
    """Test cases for the DataQualityMonitor class."""

    @pytest.fixture
    def data_quality_monitor(self):
        """Create a DataQualityMonitor instance for testing."""
        with patch('src.data_collection.core.data_collector.DataCollector') as mock_collector:
            collector = Mock()
            monitor = DataQualityMonitor(collector)
            return monitor

    def test_quality_alert_creation(self, data_quality_monitor):
        """Test quality alert creation."""
        data_quality_monitor._add_quality_alert("Test alert", 0.85, "accuracy")

        assert len(data_quality_monitor.quality_alerts) == 1
        alert = data_quality_monitor.quality_alerts[0]
        assert alert['message'] == "Test alert"
        assert alert['value'] == 0.85
        assert alert['type'] == "accuracy"
        assert alert['severity'] == "warning"  # 0.85 > 0.8 threshold

    def test_quality_alert_critical(self, data_quality_monitor):
        """Test critical quality alert creation."""
        data_quality_monitor._add_quality_alert("Critical alert", 0.75, "accuracy")

        assert len(data_quality_monitor.quality_alerts) == 1
        alert = data_quality_monitor.quality_alerts[0]
        assert alert['severity'] == "critical"  # 0.75 < 0.8 threshold

    def test_get_quality_summary(self, data_quality_monitor):
        """Test getting quality summary."""
        # Add some alerts
        data_quality_monitor._add_quality_alert("Warning alert", 0.85, "accuracy")
        data_quality_monitor._add_quality_alert("Critical alert", 0.75, "completeness")

        summary = data_quality_monitor.get_quality_summary()

        assert summary['total_alerts'] == 2
        assert summary['critical_alerts'] == 1
        assert summary['warning_alerts'] == 1
        assert len(summary['recent_alerts']) == 2

    def test_quality_alerts_limit(self, data_quality_monitor):
        """Test quality alerts limit."""
        # Add more than 100 alerts
        for i in range(150):
            data_quality_monitor._add_quality_alert(f"Alert {i}", 0.8, "accuracy")

        # Should keep only last 100 alerts
        assert len(data_quality_monitor.quality_alerts) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])