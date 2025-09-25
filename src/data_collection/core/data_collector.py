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

        # Collection tasks
        self.tasks: Dict[str, CollectionTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}

        # Collection statistics
        self.stats = {
            'total_collections': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'data_points_collected': 0,
            'last_collection_time': None
        }

        # Rate limiting and scheduling
        self.collection_interval = self.settings.DATA_COLLECTION_INTERVAL
        self.max_concurrent_collections = 50

        # Background tasks
        self.scheduler_task = None
        self.monitor_task = None

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
                self.stats['data_points_collected'] += len(data) if isinstance(data, list) else 1

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