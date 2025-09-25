"""
Data Collector for collecting market data from multiple exchanges.

This module provides functionality for collecting various types of market data
including OHLCV data, order book data, trade data, and ticker data from
multiple cryptocurrency exchanges with automatic scheduling and error handling.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
import uuid
from dataclasses import dataclass

from .exchange_manager import ExchangeManager
from .data_processor import DataProcessor
from ..config.settings import get_settings
from ..models.database import get_timescaledb_session, get_session
from ..models.market_data import MarketData, OHLCVData, OrderBookData, TradeData, TickerData
from ..utils.metrics import MetricsCollector
from ..utils.validation import DataValidator, ValidationReport
from ..utils.helpers import format_timestamp, normalize_symbol, get_timeframe_seconds
from ..collectors.orderbook_collector import OrderBookCollector
from ..collectors.trades_collector import TradesCollector
from ..storage.redis import RedisStorage


@dataclass
class CollectionTask:
    """Represents a data collection task."""
    id: str
    exchange: str
    symbol: str
    data_type: str
    interval: int
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    is_active: bool = True
    parameters: Dict[str, Any] = None
    callback: Optional[Callable] = None


class DataCollector:
    """Main data collection engine."""

    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.exchange_manager = ExchangeManager()
        self.data_processor = DataProcessor()
        self.metrics = MetricsCollector()
        self.validator = DataValidator()
        self.redis = RedisStorage()

        # Collection tasks
        self.tasks: Dict[str, CollectionTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}

        # Specialized collectors
        self.orderbook_collector = OrderBookCollector(self.exchange_manager, self.data_processor)
        self.trades_collector = TradesCollector(self.exchange_manager, self.data_processor)

        # Collection statistics
        self.stats = {
            'total_collections': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'data_points_collected': 0,
            'last_collection_time': None,
            'ohlcv_collections': 0,
            'ticker_collections': 0,
            'orderbook_collections': 0,
            'trades_collections': 0
        }

        # Rate limiting and scheduling
        self.collection_interval = self.settings.DATA_COLLECTION_INTERVAL
        self.max_concurrent_collections = 50

        # Intelligent scheduling
        self.priority_queues = {
            'high': [],
            'medium': [],
            'low': []
        }
        self.load_balancer = LoadBalancer()
        self.quality_monitor = DataQualityMonitor(self)

        # Background tasks
        self.scheduler_task = None
        self.monitor_task = None
        self.quality_task = None

    async def start(self):
        """Start the data collection system."""
        self.logger.info("Starting data collection system")

        # Initialize exchange manager
        await self.exchange_manager.start_health_monitoring()

        # Start metrics cleanup
        await self.metrics.start_cleanup_task()

        # Start scheduler
        await self.start_scheduler()

        # Start monitoring
        await self.start_monitoring()

        # Start specialized collectors
        await self.orderbook_collector.start()
        await self.trades_collector.start()

        # Start quality monitoring
        await self.start_quality_monitoring()

        # Initialize default collection tasks
        await self.initialize_default_tasks()

        self.logger.info("Data collection system started successfully")

    async def stop(self):
        """Stop the data collection system."""
        self.logger.info("Stopping data collection system")

        # Cancel running tasks
        for task in self.running_tasks.values():
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)

        # Stop background tasks
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass

        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        # Stop exchange manager
        await self.exchange_manager.close()

        # Stop metrics cleanup
        await self.metrics.stop_cleanup_task()

        # Stop specialized collectors
        await self.orderbook_collector.stop()
        await self.trades_collector.stop()

        # Stop quality monitoring
        await self.stop_quality_monitoring()

        self.logger.info("Data collection system stopped")

    async def initialize_default_tasks(self):
        """Initialize default collection tasks."""
        # Get available exchanges
        exchanges = await self.exchange_manager.get_all_exchanges()

        # Default symbols to collect
        default_symbols = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
            'DOT/USDT', 'DOGE/USDT', 'AVAX/USDT', 'MATIC/USDT', 'LINK/USDT'
        ]

        for exchange in exchanges:
            try:
                # Get available markets for exchange
                markets = await self.exchange_manager.get_markets(exchange)

                # Filter available symbols
                available_symbols = [
                    market['symbol'] for market in markets
                    if market.get('symbol') in default_symbols and market.get('active', False)
                ]

                # Create collection tasks for each symbol
                for symbol in available_symbols[:5]:  # Limit to 5 symbols per exchange for demo
                    # OHLCV collection tasks
                    for timeframe in self.settings.OHLCV_TIMEFRAMES[:3]:  # Limit timeframes
                        task_id = f"{exchange}_{symbol.replace('/', '_')}_ohlcv_{timeframe}"
                        await self.add_collection_task(
                            task_id=task_id,
                            exchange=exchange,
                            symbol=symbol,
                            data_type='ohlcv',
                            interval=get_timeframe_seconds(timeframe),
                            parameters={'timeframe': timeframe, 'limit': 100}
                        )

                    # Order book collection task
                    orderbook_task_id = f"{exchange}_{symbol.replace('/', '_')}_orderbook"
                    await self.add_collection_task(
                        task_id=orderbook_task_id,
                        exchange=exchange,
                        symbol=symbol,
                        data_type='orderbook',
                        interval=30,  # Every 30 seconds
                        parameters={'limit': self.settings.ORDER_BOOK_DEPTH}
                    )

                    # Trades collection task
                    trades_task_id = f"{exchange}_{symbol.replace('/', '_')}_trades"
                    await self.add_collection_task(
                        task_id=trades_task_id,
                        exchange=exchange,
                        symbol=symbol,
                        data_type='trades',
                        interval=60,  # Every minute
                        parameters={'limit': self.settings.TRADE_LIMIT}
                    )

                    # Ticker collection task
                    ticker_task_id = f"{exchange}_{symbol.replace('/', '_')}_ticker"
                    await self.add_collection_task(
                        task_id=ticker_task_id,
                        exchange=exchange,
                        symbol=symbol,
                        data_type='ticker',
                        interval=60,  # Every minute
                        parameters={}
                    )

                self.logger.info(f"Initialized default tasks for {exchange}: {len(available_symbols)} symbols")

            except Exception as e:
                self.logger.error(f"Failed to initialize tasks for {exchange}: {e}")

    async def add_collection_task(self, task_id: str, exchange: str, symbol: str, data_type: str,
                                 interval: int, parameters: Dict[str, Any] = None,
                                 callback: Optional[Callable] = None) -> str:
        """Add a new collection task."""
        if task_id in self.tasks:
            raise ValueError(f"Task with ID '{task_id}' already exists")

        task = CollectionTask(
            id=task_id,
            exchange=exchange,
            symbol=symbol,
            data_type=data_type,
            interval=interval,
            next_run=datetime.now(),
            parameters=parameters or {},
            callback=callback
        )

        self.tasks[task_id] = task
        self.logger.info(f"Added collection task: {task_id} ({exchange}/{symbol}/{data_type})")

        return task_id

    async def remove_collection_task(self, task_id: str):
        """Remove a collection task."""
        if task_id in self.tasks:
            # Cancel running task if any
            if task_id in self.running_tasks:
                task = self.running_tasks[task_id]
                if not task.done():
                    task.cancel()
                del self.running_tasks[task_id]

            # Remove task
            del self.tasks[task_id]
            self.logger.info(f"Removed collection task: {task_id}")

    async def start_scheduler(self):
        """Start the task scheduler."""
        async def scheduler():
            while True:
                try:
                    await self.run_pending_tasks()
                    await asyncio.sleep(1)  # Check every second
                except Exception as e:
                    self.logger.error(f"Scheduler error: {e}")
                    await asyncio.sleep(5)  # Wait before retrying

        self.scheduler_task = asyncio.create_task(scheduler())

    async def start_monitoring(self):
        """Start system monitoring."""
        async def monitor():
            while True:
                try:
                    await self.check_system_health()
                    await self.log_statistics()
                    await asyncio.sleep(60)  # Monitor every minute
                except Exception as e:
                    self.logger.error(f"Monitor error: {e}")
                    await asyncio.sleep(30)  # Wait before retrying

        self.monitor_task = asyncio.create_task(monitor())

    async def run_pending_tasks(self):
        """Run all pending collection tasks."""
        now = datetime.now()

        # Get tasks that need to run
        pending_tasks = [
            task for task in self.tasks.values()
            if task.is_active and task.next_run and task.next_run <= now
        ]

        if not pending_tasks:
            return

        # Limit concurrent collections
        available_slots = self.max_concurrent_collections - len(self.running_tasks)
        tasks_to_run = pending_tasks[:available_slots]

        for task in tasks_to_run:
            asyncio.create_task(self.run_collection_task(task))

    async def run_collection_task(self, task: CollectionTask):
        """Run a single collection task."""
        task_id = task.id

        # Check if task is already running
        if task_id in self.running_tasks and not self.running_tasks[task_id].done():
            self.logger.warning(f"Task {task_id} is already running")
            return

        # Create collection task
        collection_task = asyncio.create_task(self._execute_collection(task))
        self.running_tasks[task_id] = collection_task

        try:
            await collection_task
        except asyncio.CancelledError:
            self.logger.info(f"Task {task_id} was cancelled")
        except Exception as e:
            self.logger.error(f"Task {task_id} failed: {e}")
        finally:
            # Clean up completed task
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    async def _execute_collection(self, task: CollectionTask):
        """Execute the actual data collection."""
        start_time = datetime.now()
        self.logger.debug(f"Executing collection task: {task.id}")

        try:
            # Update task status
            task.last_run = start_time
            task.next_run = start_time + timedelta(seconds=task.interval)

            # Collect data based on type
            if task.data_type == 'ohlcv':
                data = await self._collect_ohlcv(task)
            elif task.data_type == 'orderbook':
                data = await self._collect_orderbook(task)
            elif task.data_type == 'trades':
                data = await self._collect_trades(task)
            elif task.data_type == 'ticker':
                data = await self._collect_ticker(task)
            else:
                raise ValueError(f"Unknown data type: {task.data_type}")

            # Update statistics
            self.stats['total_collections'] += 1
            self.stats['successful_collections'] += 1
            self.stats['last_collection_time'] = start_time

            if data:
                data_points = len(data) if isinstance(data, list) else 1
                self.stats['data_points_collected'] += data_points

                # Update type-specific statistics
                if task.data_type == 'ohlcv':
                    self.stats['ohlcv_collections'] += 1
                elif task.data_type == 'ticker':
                    self.stats['ticker_collections'] += 1
                elif task.data_type == 'orderbook':
                    self.stats['orderbook_collections'] += 1
                elif task.data_type == 'trades':
                    self.stats['trades_collections'] += 1

            # Execute callback if provided
            if task.callback:
                await task.callback(task, data)

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self.logger.debug(f"Task {task.id} completed in {execution_time:.2f}ms")

        except Exception as e:
            # Update statistics
            self.stats['total_collections'] += 1
            self.stats['failed_collections'] += 1

            self.logger.error(f"Collection task {task.id} failed: {e}")

            # Update next run time (with exponential backoff)
            backoff_time = min(task.interval * 2, 300)  # Max 5 minutes backoff
            task.next_run = datetime.now() + timedelta(seconds=backoff_time)

    async def _collect_ohlcv(self, task: CollectionTask) -> Optional[List[List]]:
        """Collect OHLCV data."""
        exchange = task.exchange
        symbol = task.symbol
        timeframe = task.parameters.get('timeframe', '1m')
        limit = task.parameters.get('limit', 100)

        try:
            # Fetch OHLCV data
            ohlcv_data = await self.exchange_manager.get_ohlcv(
                exchange, symbol, timeframe, limit=limit
            )

            if not ohlcv_data:
                self.logger.warning(f"No OHLCV data for {exchange}/{symbol}/{timeframe}")
                return None

            # Validate and process data
            validation_report = self.validator.validate_ohlcv(ohlcv_data, exchange, symbol)

            # Store valid data
            if validation_report.overall_score >= self.settings.DATA_QUALITY_THRESHOLD:
                processed_data = await self.data_processor.process_ohlcv(
                    ohlcv_data, exchange, symbol, timeframe
                )

                # Store in database
                await self._store_ohlcv_data(processed_data)

                # Record metrics
                self.metrics.record_data_quality(
                    exchange, symbol, 'ohlcv',
                    validation_report.accuracy_score,
                    validation_report.completeness_score,
                    validation_report.timeliness_score
                )

                return ohlcv_data
            else:
                self.logger.warning(f"OHLCV data quality too low for {exchange}/{symbol}/{timeframe}: {validation_report.overall_score:.3f}")
                return None

        except Exception as e:
            self.logger.error(f"Failed to collect OHLCV data for {exchange}/{symbol}/{timeframe}: {e}")
            return None

    async def _collect_orderbook(self, task: CollectionTask) -> Optional[Dict]:
        """Collect order book data."""
        exchange = task.exchange
        symbol = task.symbol
        limit = task.parameters.get('limit', 20)

        try:
            # Fetch order book data
            orderbook_data = await self.exchange_manager.get_order_book(
                exchange, symbol, limit=limit
            )

            if not orderbook_data:
                self.logger.warning(f"No order book data for {exchange}/{symbol}")
                return None

            # Validate and process data
            validation_report = self.validator.validate_orderbook(orderbook_data, exchange, symbol)

            # Store valid data
            if validation_report.overall_score >= self.settings.DATA_QUALITY_THRESHOLD:
                processed_data = await self.data_processor.process_orderbook(
                    orderbook_data, exchange, symbol
                )

                # Store in database
                await self._store_orderbook_data(processed_data)

                # Record metrics
                self.metrics.record_data_quality(
                    exchange, symbol, 'orderbook',
                    validation_report.accuracy_score,
                    validation_report.completeness_score,
                    validation_report.timeliness_score
                )

                return orderbook_data
            else:
                self.logger.warning(f"Order book data quality too low for {exchange}/{symbol}: {validation_report.overall_score:.3f}")
                return None

        except Exception as e:
            self.logger.error(f"Failed to collect order book data for {exchange}/{symbol}: {e}")
            return None

    async def _collect_trades(self, task: CollectionTask) -> Optional[List[Dict]]:
        """Collect trades data."""
        exchange = task.exchange
        symbol = task.symbol
        limit = task.parameters.get('limit', 100)

        try:
            # Fetch trades data
            trades_data = await self.exchange_manager.get_trades(
                exchange, symbol, limit=limit
            )

            if not trades_data:
                self.logger.warning(f"No trades data for {exchange}/{symbol}")
                return None

            # Validate and process data
            validation_report = self.validator.validate_trades(trades_data, exchange, symbol)

            # Store valid data
            if validation_report.overall_score >= self.settings.DATA_QUALITY_THRESHOLD:
                processed_data = await self.data_processor.process_trades(
                    trades_data, exchange, symbol
                )

                # Store in database
                await self._store_trades_data(processed_data)

                # Record metrics
                self.metrics.record_data_quality(
                    exchange, symbol, 'trades',
                    validation_report.accuracy_score,
                    validation_report.completeness_score,
                    validation_report.timeliness_score
                )

                return trades_data
            else:
                self.logger.warning(f"Trades data quality too low for {exchange}/{symbol}: {validation_report.overall_score:.3f}")
                return None

        except Exception as e:
            self.logger.error(f"Failed to collect trades data for {exchange}/{symbol}: {e}")
            return None

    async def _collect_ticker(self, task: CollectionTask) -> Optional[Dict]:
        """Collect ticker data."""
        exchange = task.exchange
        symbol = task.symbol

        try:
            # Fetch ticker data
            ticker_data = await self.exchange_manager.get_ticker(exchange, symbol)

            if not ticker_data:
                self.logger.warning(f"No ticker data for {exchange}/{symbol}")
                return None

            # Validate and process data
            validation_report = self.validator.validate_ticker(ticker_data, exchange, symbol)

            # Store valid data
            if validation_report.overall_score >= self.settings.DATA_QUALITY_THRESHOLD:
                processed_data = await self.data_processor.process_ticker(
                    ticker_data, exchange, symbol
                )

                # Store in database
                await self._store_ticker_data(processed_data)

                # Record metrics
                self.metrics.record_data_quality(
                    exchange, symbol, 'ticker',
                    validation_report.accuracy_score,
                    validation_report.completeness_score,
                    validation_report.timeliness_score
                )

                return ticker_data
            else:
                self.logger.warning(f"Ticker data quality too low for {exchange}/{symbol}: {validation_report.overall_score:.3f}")
                return None

        except Exception as e:
            self.logger.error(f"Failed to collect ticker data for {exchange}/{symbol}: {e}")
            return None

    async def _store_ohlcv_data(self, ohlcv_data: List[OHLCVData]):
        """Store OHLCV data in database."""
        try:
            session = get_timescaledb_session()
            try:
                for ohlcv in ohlcv_data:
                    session.add(ohlcv)
                session.commit()
                session.close()
            except Exception as e:
                session.rollback()
                raise e
        except Exception as e:
            self.logger.error(f"Failed to store OHLCV data: {e}")

    async def _store_orderbook_data(self, orderbook_data: OrderBookData):
        """Store order book data in database."""
        try:
            session = get_timescaledb_session()
            try:
                session.add(orderbook_data)
                session.commit()
                session.close()
            except Exception as e:
                session.rollback()
                raise e
        except Exception as e:
            self.logger.error(f"Failed to store order book data: {e}")

    async def _store_trades_data(self, trades_data: List[TradeData]):
        """Store trades data in database."""
        try:
            session = get_timescaledb_session()
            try:
                for trade in trades_data:
                    session.add(trade)
                session.commit()
                session.close()
            except Exception as e:
                session.rollback()
                raise e
        except Exception as e:
            self.logger.error(f"Failed to store trades data: {e}")

    async def _store_ticker_data(self, ticker_data: TickerData):
        """Store ticker data in database."""
        try:
            session = get_timescaledb_session()
            try:
                session.add(ticker_data)
                session.commit()
                session.close()
            except Exception as e:
                session.rollback()
                raise e
        except Exception as e:
            self.logger.error(f"Failed to store ticker data: {e}")

    async def check_system_health(self):
        """Check overall system health."""
        try:
            # Check exchange health
            exchanges = await self.exchange_manager.get_all_exchanges()
            healthy_exchanges = 0

            for exchange in exchanges:
                status = await self.exchange_manager.get_exchange_status(exchange)
                if status.get('healthy', False):
                    healthy_exchanges += 1

            # Check collection tasks
            active_tasks = sum(1 for task in self.tasks.values() if task.is_active)
            running_tasks = len(self.running_tasks)

            # Log health status
            self.logger.info(f"System health: {healthy_exchanges}/{len(exchanges)} exchanges healthy, "
                           f"{active_tasks} active tasks, {running_tasks} running tasks")

            # Calculate system metrics
            total_collections = self.stats['total_collections']
            if total_collections > 0:
                success_rate = self.stats['successful_collections'] / total_collections
                self.logger.info(f"Collection success rate: {success_rate:.2%}")

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")

    async def log_statistics(self):
        """Log collection statistics."""
        try:
            stats = self.stats.copy()

            # Calculate rates
            if stats['total_collections'] > 0:
                stats['success_rate'] = stats['successful_collections'] / stats['total_collections']
                stats['failure_rate'] = stats['failed_collections'] / stats['total_collections']

            # Log key metrics
            self.logger.info(f"Collection stats: {stats['total_collections']} total, "
                           f"{stats['successful_collections']} successful, "
                           f"{stats['data_points_collected']} data points")

            # Log task status
            active_tasks = len([t for t in self.tasks.values() if t.is_active])
            running_tasks = len(self.running_tasks)
            self.logger.info(f"Task status: {active_tasks} active, {running_tasks} running")

        except Exception as e:
            self.logger.error(f"Failed to log statistics: {e}")

    def get_collection_status(self) -> Dict[str, Any]:
        """Get current collection status."""
        return {
            'is_running': self.scheduler_task is not None and not self.scheduler_task.done(),
            'total_tasks': len(self.tasks),
            'active_tasks': len([t for t in self.tasks.values() if t.is_active]),
            'running_tasks': len(self.running_tasks),
            'statistics': self.stats.copy(),
            'exchanges': self.exchange_manager.get_exchange_status if self.exchange_manager else {},
            'tasks': [
                {
                    'id': task.id,
                    'exchange': task.exchange,
                    'symbol': task.symbol,
                    'data_type': task.data_type,
                    'interval': task.interval,
                    'is_active': task.is_active,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'next_run': task.next_run.isoformat() if task.next_run else None,
                }
                for task in self.tasks.values()
            ]
        }

    async def start_quality_monitoring(self):
        """Start data quality monitoring."""
        async def quality_monitor():
            while True:
                try:
                    await self.quality_monitor.check_data_quality()
                    await asyncio.sleep(60)  # Check every minute
                except Exception as e:
                    self.logger.error(f"Quality monitoring error: {e}")
                    await asyncio.sleep(30)

        self.quality_task = asyncio.create_task(quality_monitor())

    async def stop_quality_monitoring(self):
        """Stop data quality monitoring."""
        if self.quality_task:
            self.quality_task.cancel()
            try:
                await self.quality_task
            except asyncio.CancelledError:
                pass

    async def get_incremental_ohlcv(self, exchange: str, symbol: str, timeframe: str,
                                  since: Optional[int] = None) -> List[List]:
        """Get incremental OHLCV data since last timestamp."""
        try:
            # Try to get last timestamp from cache
            cache_key = f"last_timestamp:{exchange}:{symbol}:{timeframe}"
            last_timestamp = await self.redis.get(cache_key)

            # Use provided timestamp or cached timestamp
            since_timestamp = since or (int(last_timestamp) if last_timestamp else None)

            # Fetch OHLCV data
            ohlcv_data = await self.exchange_manager.get_ohlcv(
                exchange, symbol, timeframe, since=since_timestamp, limit=1000
            )

            if ohlcv_data:
                # Update last timestamp in cache
                latest_timestamp = ohlcv_data[-1][0]  # First element is timestamp
                await self.redis.set(cache_key, str(latest_timestamp), ttl=86400)  # 24 hour TTL

            return ohlcv_data

        except Exception as e:
            self.logger.error(f"Failed to get incremental OHLCV data: {e}")
            return []

    async def prioritize_tasks(self):
        """Intelligent task prioritization based on multiple factors."""
        current_time = datetime.now()

        for task in self.tasks.values():
            if not task.is_active:
                continue

            # Calculate priority score based on multiple factors
            priority_score = 0

            # Base priority from data type
            if task.data_type == 'ticker':
                priority_score += 30  # High priority for real-time price
            elif task.data_type == 'orderbook':
                priority_score += 25  # High priority for liquidity data
            elif task.data_type == 'trades':
                priority_score += 20  # Medium priority for trade data
            elif task.data_type == 'ohlcv':
                priority_score += 10  # Lower priority for historical data

            # Priority from collection interval (more frequent = higher priority)
            if task.interval <= 5:
                priority_score += 20
            elif task.interval <= 30:
                priority_score += 15
            elif task.interval <= 300:
                priority_score += 10

            # Priority from data freshness
            if task.last_run:
                time_since_run = (current_time - task.last_run).total_seconds()
                if time_since_run > task.interval * 2:
                    priority_score += 15  # Overdue tasks get higher priority
                elif time_since_run > task.interval:
                    priority_score += 10

            # Priority from error rate
            if hasattr(task, 'error_count') and task.error_count > 3:
                priority_score -= 10  # Reduce priority for error-prone tasks

            # Priority from exchange health
            exchange_health = await self.exchange_manager.get_exchange_health(task.exchange)
            if exchange_health.get('healthy', True):
                priority_score += 5  # Prefer healthy exchanges

            # Assign to priority queue
            if priority_score >= 50:
                self.priority_queues['high'].append(task)
            elif priority_score >= 30:
                self.priority_queues['medium'].append(task)
            else:
                self.priority_queues['low'].append(task)

        # Sort each queue by priority score
        for queue in self.priority_queues.values():
            queue.sort(key=lambda t: self._calculate_task_priority(t), reverse=True)

    def _calculate_task_priority(self, task: CollectionTask) -> float:
        """Calculate priority score for a task."""
        current_time = datetime.now()
        score = 0.0

        # Data type priority
        type_priority = {
            'ticker': 30,
            'orderbook': 25,
            'trades': 20,
            'ohlcv': 10
        }
        score += type_priority.get(task.data_type, 5)

        # Interval priority
        if task.interval <= 5:
            score += 20
        elif task.interval <= 30:
            score += 15
        elif task.interval <= 300:
            score += 10

        # Freshness priority
        if task.last_run:
            time_since_run = (current_time - task.last_run).total_seconds()
            if time_since_run > task.interval * 2:
                score += 15
            elif time_since_run > task.interval:
                score += 10

        return score


class LoadBalancer:
    """Load balancer for distributing collection tasks across exchanges."""

    def __init__(self):
        self.exchange_loads = {}
        self.exchange_capacities = {}
        self.logger = logging.getLogger(__name__)

    async def get_exchange_load(self, exchange: str) -> float:
        """Get current load for an exchange."""
        return self.exchange_loads.get(exchange, 0.0)

    async def update_exchange_load(self, exchange: str, load_change: float):
        """Update load for an exchange."""
        current_load = self.exchange_loads.get(exchange, 0.0)
        self.exchange_loads[exchange] = max(0.0, current_load + load_change)

    async def get_best_exchange(self, exchanges: List[str]) -> Optional[str]:
        """Get the exchange with lowest current load."""
        if not exchanges:
            return None

        # Get loads for all exchanges
        exchange_loads = {}
        for exchange in exchanges:
            load = await self.get_exchange_load(exchange)
            capacity = self.exchange_capacities.get(exchange, 1.0)
            exchange_loads[exchange] = load / capacity if capacity > 0 else float('inf')

        # Return exchange with lowest load
        return min(exchange_loads, key=exchange_loads.get)

    async def can_handle_task(self, exchange: str, task_weight: float = 1.0) -> bool:
        """Check if exchange can handle additional load."""
        current_load = await self.get_exchange_load(exchange)
        capacity = self.exchange_capacities.get(exchange, 1.0)
        return (current_load + task_weight) <= capacity


class DataQualityMonitor:
    """Real-time data quality monitoring."""

    def __init__(self, data_collector):
        self.data_collector = data_collector
        self.logger = logging.getLogger(__name__)
        self.quality_alerts = []
        self.quality_thresholds = {
            'accuracy': 0.95,
            'completeness': 0.95,
            'timeliness': 0.90,
            'consistency': 0.90
        }

    async def check_data_quality(self):
        """Check overall data quality across all collections."""
        try:
            # Check OHLCV data quality
            await self._check_ohlcv_quality()

            # Check ticker data quality
            await self._check_ticker_quality()

            # Check order book quality
            await self._check_orderbook_quality()

            # Check trades data quality
            await self._check_trades_quality()

            # Log quality summary
            await self._log_quality_summary()

        except Exception as e:
            self.logger.error(f"Data quality check failed: {e}")

    async def _check_ohlcv_quality(self):
        """Check OHLCV data quality."""
        try:
            # Get recent OHLCV quality metrics
            recent_metrics = self.data_collector.metrics.get_recent_metrics('ohlcv')

            if not recent_metrics:
                return

            # Calculate average quality scores
            avg_accuracy = sum(m.get('accuracy_score', 0) for m in recent_metrics) / len(recent_metrics)
            avg_completeness = sum(m.get('completeness_score', 0) for m in recent_metrics) / len(recent_metrics)
            avg_timeliness = sum(m.get('timeliness_score', 0) for m in recent_metrics) / len(recent_metrics)

            # Check against thresholds
            if avg_accuracy < self.quality_thresholds['accuracy']:
                self._add_quality_alert('OHLCV accuracy low', avg_accuracy, 'accuracy')

            if avg_completeness < self.quality_thresholds['completeness']:
                self._add_quality_alert('OHLCV completeness low', avg_completeness, 'completeness')

            if avg_timeliness < self.quality_thresholds['timeliness']:
                self._add_quality_alert('OHLCV timeliness low', avg_timeliness, 'timeliness')

        except Exception as e:
            self.logger.error(f"OHLCV quality check failed: {e}")

    async def _check_ticker_quality(self):
        """Check ticker data quality."""
        try:
            # Get recent ticker quality metrics
            recent_metrics = self.data_collector.metrics.get_recent_metrics('ticker')

            if not recent_metrics:
                return

            # Calculate average quality scores
            avg_accuracy = sum(m.get('accuracy_score', 0) for m in recent_metrics) / len(recent_metrics)

            # Check against thresholds
            if avg_accuracy < self.quality_thresholds['accuracy']:
                self._add_quality_alert('Ticker accuracy low', avg_accuracy, 'accuracy')

        except Exception as e:
            self.logger.error(f"Ticker quality check failed: {e}")

    async def _check_orderbook_quality(self):
        """Check order book data quality."""
        try:
            # Get order book collector stats
            orderbook_stats = self.data_collector.orderbook_collector.get_collection_stats()

            # Check success rate
            if orderbook_stats['statistics']['total_collections'] > 0:
                success_rate = (orderbook_stats['statistics']['successful_collections'] /
                               orderbook_stats['statistics']['total_collections'])

                if success_rate < self.quality_thresholds['accuracy']:
                    self._add_quality_alert('Order book collection success rate low', success_rate, 'collection_rate')

        except Exception as e:
            self.logger.error(f"Order book quality check failed: {e}")

    async def _check_trades_quality(self):
        """Check trades data quality."""
        try:
            # Get trades collector stats
            trades_stats = self.data_collector.trades_collector.get_collection_stats()

            # Check success rate
            if trades_stats['statistics']['total_collections'] > 0:
                success_rate = (trades_stats['statistics']['successful_collections'] /
                               trades_stats['statistics']['total_collections'])

                if success_rate < self.quality_thresholds['accuracy']:
                    self._add_quality_alert('Trades collection success rate low', success_rate, 'collection_rate')

        except Exception as e:
            self.logger.error(f"Trades quality check failed: {e}")

    def _add_quality_alert(self, message: str, value: float, alert_type: str):
        """Add a quality alert."""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'value': value,
            'type': alert_type,
            'severity': 'warning' if value > 0.8 else 'critical'
        }

        self.quality_alerts.append(alert)

        # Keep only recent alerts (last 100)
        if len(self.quality_alerts) > 100:
            self.quality_alerts = self.quality_alerts[-100:]

        # Log alert
        self.logger.warning(f"Quality Alert: {message} - Value: {value:.3f}")

    async def _log_quality_summary(self):
        """Log quality summary."""
        try:
            total_alerts = len(self.quality_alerts)
            critical_alerts = len([a for a in self.quality_alerts if a['severity'] == 'critical'])

            if total_alerts > 0:
                self.logger.info(f"Quality Summary: {total_alerts} alerts, {critical_alerts} critical")

            # Log alerts by type
            alert_types = {}
            for alert in self.quality_alerts[-10:]:  # Last 10 alerts
                alert_type = alert['type']
                alert_types[alert_type] = alert_types.get(alert_type, 0) + 1

            for alert_type, count in alert_types.items():
                self.logger.info(f"  {alert_type}: {count} alerts")

        except Exception as e:
            self.logger.error(f"Failed to log quality summary: {e}")

    def get_quality_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent quality alerts."""
        return self.quality_alerts[-limit:]

    def get_quality_summary(self) -> Dict[str, Any]:
        """Get quality summary statistics."""
        total_alerts = len(self.quality_alerts)
        critical_alerts = len([a for a in self.quality_alerts if a['severity'] == 'critical'])
        warning_alerts = len([a for a in self.quality_alerts if a['severity'] == 'warning'])

        return {
            'total_alerts': total_alerts,
            'critical_alerts': critical_alerts,
            'warning_alerts': warning_alerts,
            'recent_alerts': self.get_quality_alerts(10),
            'thresholds': self.quality_thresholds.copy()
        }