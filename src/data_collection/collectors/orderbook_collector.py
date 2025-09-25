"""
Order Book Data Collector for real-time order book collection.

This module implements a specialized collector for order book data with
incremental updates, intelligent scheduling, and quality monitoring.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from ..core.exchange_manager import ExchangeManager
from ..core.data_processor import DataProcessor
from ..config.settings import get_settings
from ..models.market_data import OrderBookData
from ..utils.metrics import MetricsCollector
from ..utils.validation import DataValidator
from ..storage.redis import RedisStorage


@dataclass
class OrderBookCollectionTask:
    """Represents an order book collection task."""
    exchange: str
    symbol: str
    depth: int
    interval: float
    priority: int = 1
    last_update: Optional[datetime] = None
    next_update: Optional[datetime] = None
    is_active: bool = True
    error_count: int = 0
    last_error: Optional[str] = None


class OrderBookCollector:
    """Specialized collector for order book data."""

    def __init__(self, exchange_manager: ExchangeManager, data_processor: DataProcessor):
        self.exchange_manager = exchange_manager
        self.data_processor = data_processor
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.metrics = MetricsCollector()
        self.validator = DataValidator()
        self.redis = RedisStorage()

        # Collection tasks
        self.tasks: Dict[str, OrderBookCollectionTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}

        # Collection statistics
        self.stats = {
            'total_collections': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'orderbooks_collected': 0,
            'average_collection_time': 0,
            'last_collection_time': None
        }

        # Rate limiting
        self.max_concurrent_collections = 20
        self.collection_semaphore = asyncio.Semaphore(self.max_concurrent_collections)

        # Background tasks
        self.scheduler_task = None
        self._running = False

    async def start(self):
        """Start the order book collector."""
        self._running = True
        self.logger.info("Starting Order Book Collector")

        # Start scheduler
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())

        # Initialize default tasks
        await self._initialize_default_tasks()

    async def stop(self):
        """Stop the order book collector."""
        self._running = False
        self.logger.info("Stopping Order Book Collector")

        # Cancel running tasks
        for task in self.running_tasks.values():
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)

        # Cancel scheduler
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass

    async def add_collection_task(self, exchange: str, symbol: str, depth: int = 20,
                                interval: float = 1.0, priority: int = 1) -> str:
        """Add an order book collection task."""
        task_id = f"{exchange}_{symbol.replace('/', '_')}_orderbook"

        if task_id in self.tasks:
            self.logger.warning(f"Order book task {task_id} already exists")
            return task_id

        task = OrderBookCollectionTask(
            exchange=exchange,
            symbol=symbol,
            depth=depth,
            interval=interval,
            priority=priority,
            next_update=datetime.now()
        )

        self.tasks[task_id] = task
        self.logger.info(f"Added order book collection task: {task_id}")

        return task_id

    async def remove_collection_task(self, task_id: str):
        """Remove an order book collection task."""
        if task_id in self.tasks:
            # Cancel running task if any
            if task_id in self.running_tasks:
                task = self.running_tasks[task_id]
                if not task.done():
                    task.cancel()
                del self.running_tasks[task_id]

            # Remove task
            del self.tasks[task_id]
            self.logger.info(f"Removed order book collection task: {task_id}")

    async def _initialize_default_tasks(self):
        """Initialize default order book collection tasks."""
        # Get available exchanges
        exchanges = await self.exchange_manager.get_available_exchanges()

        # Default symbols to collect
        default_symbols = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT'
        ]

        for exchange in exchanges[:3]:  # Limit to 3 exchanges for demo
            try:
                # Get available markets for exchange
                markets = await self.exchange_manager.get_markets(exchange)

                # Filter available symbols
                available_symbols = [
                    market['symbol'] for market in markets
                    if market.get('symbol') in default_symbols and market.get('active', False)
                ]

                # Create collection tasks for each symbol
                for symbol in available_symbols[:3]:  # Limit to 3 symbols per exchange
                    await self.add_collection_task(
                        exchange=exchange,
                        symbol=symbol,
                        depth=self.settings.ORDER_BOOK_DEPTH,
                        interval=1.0,  # 1 second intervals
                        priority=1
                    )

                self.logger.info(f"Initialized order book tasks for {exchange}: {len(available_symbols)} symbols")

            except Exception as e:
                self.logger.error(f"Failed to initialize order book tasks for {exchange}: {e}")

    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                await self._execute_pending_tasks()
                await asyncio.sleep(0.1)  # Check every 100ms for real-time data
            except Exception as e:
                self.logger.error(f"Order book scheduler error: {e}")
                await asyncio.sleep(1)

    async def _execute_pending_tasks(self):
        """Execute pending order book collection tasks."""
        now = datetime.now()

        # Get tasks that need to run
        pending_tasks = [
            task for task in self.tasks.values()
            if task.is_active and task.next_update and task.next_update <= now
        ]

        if not pending_tasks:
            return

        # Sort by priority
        pending_tasks.sort(key=lambda x: x.priority)

        # Limit concurrent collections
        available_slots = self.max_concurrent_collections - len(self.running_tasks)
        tasks_to_run = pending_tasks[:available_slots]

        for task in tasks_to_run:
            task_id = f"{task.exchange}_{task.symbol.replace('/', '_')}_orderbook"
            asyncio.create_task(self._collect_orderbook(task_id, task))

    async def _collect_orderbook(self, task_id: str, task: OrderBookCollectionTask):
        """Collect order book data for a specific task."""
        async with self.collection_semaphore:
            start_time = time.time()

            try:
                # Update task status
                task.last_update = datetime.now()
                task.next_update = task.last_update + timedelta(seconds=task.interval)

                # Check if task is already running
                if task_id in self.running_tasks and not self.running_tasks[task_id].done():
                    self.logger.warning(f"Order book task {task_id} is already running")
                    return

                # Create collection task
                collection_task = asyncio.create_task(self._execute_orderbook_collection(task))
                self.running_tasks[task_id] = collection_task

                try:
                    orderbook_data = await collection_task

                    # Update statistics
                    self.stats['total_collections'] += 1
                    self.stats['successful_collections'] += 1
                    self.stats['orderbooks_collected'] += 1
                    self.stats['last_collection_time'] = task.last_update

                    # Update average collection time
                    collection_time = time.time() - start_time
                    self.stats['average_collection_time'] = (
                        self.stats['average_collection_time'] * 0.9 + collection_time * 0.1
                    )

                    # Reset error count on success
                    task.error_count = 0
                    task.last_error = None

                except Exception as e:
                    # Update statistics
                    self.stats['total_collections'] += 1
                    self.stats['failed_collections'] += 1

                    # Update task error count
                    task.error_count += 1
                    task.last_error = str(e)

                    # Exponential backoff for errors
                    if task.error_count > 3:
                        backoff_time = min(task.interval * (2 ** min(task.error_count - 3, 5)), 60)
                        task.next_update = datetime.now() + timedelta(seconds=backoff_time)
                        self.logger.warning(f"Order book task {task_id} backoff: {backoff_time}s")

                    self.logger.error(f"Order book collection failed for {task_id}: {e}")

            except Exception as e:
                self.logger.error(f"Error in order book task {task_id}: {e}")

            finally:
                # Clean up completed task
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]

    async def _execute_orderbook_collection(self, task: OrderBookCollectionTask) -> Optional[OrderBookData]:
        """Execute the actual order book collection."""
        try:
            # Fetch order book data from exchange
            raw_orderbook = await self.exchange_manager.get_order_book(
                task.exchange, task.symbol, limit=task.depth
            )

            if not raw_orderbook:
                self.logger.warning(f"No order book data for {task.exchange}/{task.symbol}")
                return None

            # Process order book data
            processed_orderbook = await self.data_processor.process_orderbook(
                raw_orderbook, task.exchange, task.symbol
            )

            if not processed_orderbook:
                self.logger.warning(f"Order book processing failed for {task.exchange}/{task.symbol}")
                return None

            # Validate order book data
            validation_report = self.validator.validate_orderbook(
                raw_orderbook, task.exchange, task.symbol
            )

            # Set quality score
            processed_orderbook.quality_score = validation_report.overall_score

            # Store data if quality is acceptable
            if validation_report.overall_score >= self.settings.DATA_QUALITY_THRESHOLD:
                await self._store_orderbook_data(processed_orderbook)

                # Cache in Redis for real-time access
                await self._cache_orderbook_data(processed_orderbook)

                # Record metrics
                self.metrics.record_data_quality(
                    task.exchange, task.symbol, 'orderbook',
                    validation_report.accuracy_score,
                    validation_report.completeness_score,
                    validation_report.timeliness_score
                )

                return processed_orderbook
            else:
                self.logger.warning(f"Order book quality too low for {task.exchange}/{task.symbol}: {validation_report.overall_score:.3f}")
                return None

        except Exception as e:
            self.logger.error(f"Failed to collect order book for {task.exchange}/{task.symbol}: {e}")
            raise

    async def _store_orderbook_data(self, orderbook: OrderBookData):
        """Store order book data in database."""
        try:
            from ..models.database import get_timescaledb_session

            session = get_timescaledb_session()
            try:
                session.add(orderbook)
                session.commit()
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()

        except Exception as e:
            self.logger.error(f"Failed to store order book data: {e}")

    async def _cache_orderbook_data(self, orderbook: OrderBookData):
        """Cache order book data in Redis."""
        try:
            cache_key = f"orderbook:{orderbook.exchange}:{orderbook.symbol}"
            cache_data = {
                'timestamp': orderbook.timestamp.isoformat(),
                'bids': orderbook.bids,
                'asks': orderbook.asks,
                'best_bid': orderbook.best_bid,
                'best_ask': orderbook.best_ask,
                'spread': orderbook.spread,
                'spread_percent': orderbook.spread_percent,
                'mid_price': orderbook.mid_price,
                'quality_score': orderbook.quality_score
            }

            await self.redis.set_json(cache_key, cache_data, ttl=30)  # 30 second cache

        except Exception as e:
            self.logger.error(f"Failed to cache order book data: {e}")

    async def get_latest_orderbook(self, exchange: str, symbol: str) -> Optional[Dict]:
        """Get latest order book data from cache."""
        try:
            cache_key = f"orderbook:{exchange}:{symbol}"
            cached_data = await self.redis.get_json(cache_key)

            if cached_data:
                return cached_data

            # If not in cache, try to fetch from database
            return await self._get_latest_orderbook_from_db(exchange, symbol)

        except Exception as e:
            self.logger.error(f"Failed to get latest order book: {e}")
            return None

    async def _get_latest_orderbook_from_db(self, exchange: str, symbol: str) -> Optional[Dict]:
        """Get latest order book from database."""
        try:
            from ..models.database import get_timescaledb_session
            from sqlalchemy import desc

            session = get_timescaledb_session()
            try:
                # Query latest order book
                latest_orderbook = session.query(OrderBookData)\
                    .filter(OrderBookData.exchange == exchange)\
                    .filter(OrderBookData.symbol == symbol)\
                    .order_by(desc(OrderBookData.timestamp))\
                    .first()

                if latest_orderbook:
                    return latest_orderbook.to_dict()

                return None

            finally:
                session.close()

        except Exception as e:
            self.logger.error(f"Failed to get order book from database: {e}")
            return None

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        return {
            'is_running': self._running,
            'total_tasks': len(self.tasks),
            'active_tasks': len([t for t in self.tasks.values() if t.is_active]),
            'running_tasks': len(self.running_tasks),
            'statistics': self.stats.copy(),
            'tasks': [
                {
                    'exchange': task.exchange,
                    'symbol': task.symbol,
                    'depth': task.depth,
                    'interval': task.interval,
                    'priority': task.priority,
                    'is_active': task.is_active,
                    'last_update': task.last_update.isoformat() if task.last_update else None,
                    'next_update': task.next_update.isoformat() if task.next_update else None,
                    'error_count': task.error_count,
                    'last_error': task.last_error
                }
                for task in self.tasks.values()
            ]
        }

    async def get_orderbook_snapshot(self, exchange: str, symbol: str) -> Optional[Dict]:
        """Get current order book snapshot with market metrics."""
        try:
            # Get latest order book
            orderbook_data = await self.get_latest_orderbook(exchange, symbol)

            if not orderbook_data:
                return None

            # Calculate additional metrics
            snapshot = orderbook_data.copy()

            # Calculate order book depth
            bids = orderbook_data.get('bids', [])
            asks = orderbook_data.get('asks', [])

            if bids and asks:
                # Calculate cumulative depth
                bid_depth = sum(float(bid[1]) for bid in bids[:10])  # Top 10 levels
                ask_depth = sum(float(ask[1]) for ask in asks[:10])

                # Calculate price levels
                bid_levels = [float(bid[0]) for bid in bids[:5]]
                ask_levels = [float(ask[0]) for ask in asks[:5]]

                # Calculate liquidity measures
                total_bid_value = sum(float(bid[0]) * float(bid[1]) for bid in bids)
                total_ask_value = sum(float(ask[0]) * float(ask[1]) for ask in asks)

                snapshot.update({
                    'bid_depth_10': bid_depth,
                    'ask_depth_10': ask_depth,
                    'bid_levels': bid_levels,
                    'ask_levels': ask_levels,
                    'total_bid_value': total_bid_value,
                    'total_ask_value': total_ask_value,
                    'total_liquidity': total_bid_value + total_ask_value,
                    'timestamp': datetime.now().isoformat()
                })

            return snapshot

        except Exception as e:
            self.logger.error(f"Failed to get order book snapshot: {e}")
            return None