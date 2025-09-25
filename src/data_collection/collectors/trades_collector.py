"""
Trades Data Collector for real-time trade data collection.

This module implements a specialized collector for trade data with
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
from ..models.market_data import TradeData
from ..utils.metrics import MetricsCollector
from ..utils.validation import DataValidator
from ..storage.redis import RedisStorage


@dataclass
class TradesCollectionTask:
    """Represents a trades collection task."""
    exchange: str
    symbol: str
    limit: int
    interval: float
    priority: int = 1
    last_trade_id: Optional[str] = None
    last_update: Optional[datetime] = None
    next_update: Optional[datetime] = None
    is_active: bool = True
    error_count: int = 0
    last_error: Optional[str] = None
    incremental_mode: bool = True


class TradesCollector:
    """Specialized collector for trade data."""

    def __init__(self, exchange_manager: ExchangeManager, data_processor: DataProcessor):
        self.exchange_manager = exchange_manager
        self.data_processor = data_processor
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.metrics = MetricsCollector()
        self.validator = DataValidator()
        self.redis = RedisStorage()

        # Collection tasks
        self.tasks: Dict[str, TradesCollectionTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}

        # Collection statistics
        self.stats = {
            'total_collections': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'trades_collected': 0,
            'average_collection_time': 0,
            'last_collection_time': None,
            'incremental_updates': 0,
            'full_fetches': 0
        }

        # Rate limiting
        self.max_concurrent_collections = 30
        self.collection_semaphore = asyncio.Semaphore(self.max_concurrent_collections)

        # Background tasks
        self.scheduler_task = None
        self._running = False

    async def start(self):
        """Start the trades collector."""
        self._running = True
        self.logger.info("Starting Trades Collector")

        # Start scheduler
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())

        # Initialize default tasks
        await self._initialize_default_tasks()

    async def stop(self):
        """Stop the trades collector."""
        self._running = False
        self.logger.info("Stopping Trades Collector")

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

    async def add_collection_task(self, exchange: str, symbol: str, limit: int = 1000,
                                interval: float = 5.0, priority: int = 1,
                                incremental_mode: bool = True) -> str:
        """Add a trades collection task."""
        task_id = f"{exchange}_{symbol.replace('/', '_')}_trades"

        if task_id in self.tasks:
            self.logger.warning(f"Trades task {task_id} already exists")
            return task_id

        task = TradesCollectionTask(
            exchange=exchange,
            symbol=symbol,
            limit=limit,
            interval=interval,
            priority=priority,
            next_update=datetime.now(),
            incremental_mode=incremental_mode
        )

        self.tasks[task_id] = task
        self.logger.info(f"Added trades collection task: {task_id}")

        return task_id

    async def remove_collection_task(self, task_id: str):
        """Remove a trades collection task."""
        if task_id in self.tasks:
            # Cancel running task if any
            if task_id in self.running_tasks:
                task = self.running_tasks[task_id]
                if not task.done():
                    task.cancel()
                del self.running_tasks[task_id]

            # Remove task
            del self.tasks[task_id]
            self.logger.info(f"Removed trades collection task: {task_id}")

    async def _initialize_default_tasks(self):
        """Initialize default trades collection tasks."""
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
                        limit=self.settings.TRADE_LIMIT,
                        interval=5.0,  # 5 second intervals
                        priority=1,
                        incremental_mode=True
                    )

                self.logger.info(f"Initialized trades tasks for {exchange}: {len(available_symbols)} symbols")

            except Exception as e:
                self.logger.error(f"Failed to initialize trades tasks for {exchange}: {e}")

    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                await self._execute_pending_tasks()
                await asyncio.sleep(0.5)  # Check every 500ms
            except Exception as e:
                self.logger.error(f"Trades scheduler error: {e}")
                await asyncio.sleep(1)

    async def _execute_pending_tasks(self):
        """Execute pending trades collection tasks."""
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
            task_id = f"{task.exchange}_{task.symbol.replace('/', '_')}_trades"
            asyncio.create_task(self._collect_trades(task_id, task))

    async def _collect_trades(self, task_id: str, task: TradesCollectionTask):
        """Collect trade data for a specific task."""
        async with self.collection_semaphore:
            start_time = time.time()

            try:
                # Update task status
                task.last_update = datetime.now()
                task.next_update = task.last_update + timedelta(seconds=task.interval)

                # Check if task is already running
                if task_id in self.running_tasks and not self.running_tasks[task_id].done():
                    self.logger.warning(f"Trades task {task_id} is already running")
                    return

                # Create collection task
                collection_task = asyncio.create_task(self._execute_trades_collection(task))
                self.running_tasks[task_id] = collection_task

                try:
                    trades_data = await collection_task

                    # Update statistics
                    self.stats['total_collections'] += 1
                    self.stats['successful_collections'] += 1
                    self.stats['trades_collected'] += len(trades_data) if trades_data else 0
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
                        backoff_time = min(task.interval * (2 ** min(task.error_count - 3, 5)), 300)
                        task.next_update = datetime.now() + timedelta(seconds=backoff_time)
                        self.logger.warning(f"Trades task {task_id} backoff: {backoff_time}s")

                    self.logger.error(f"Trades collection failed for {task_id}: {e}")

            except Exception as e:
                self.logger.error(f"Error in trades task {task_id}: {e}")

            finally:
                # Clean up completed task
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]

    async def _execute_trades_collection(self, task: TradesCollectionTask) -> List[TradeData]:
        """Execute the actual trade data collection."""
        try:
            # Determine fetch mode (incremental or full)
            if task.incremental_mode and task.last_trade_id:
                # Try incremental fetch first
                new_trades = await self._fetch_incremental_trades(task)
                if new_trades:
                    self.stats['incremental_updates'] += 1
                    return new_trades

            # Fall back to full fetch
            self.stats['full_fetches'] += 1
            return await self._fetch_full_trades(task)

        except Exception as e:
            self.logger.error(f"Failed to collect trades for {task.exchange}/{task.symbol}: {e}")
            raise

    async def _fetch_incremental_trades(self, task: TradesCollectionTask) -> Optional[List[TradeData]]:
        """Fetch new trades incrementally since last trade ID."""
        try:
            # Fetch trades since last trade ID
            raw_trades = await self.exchange_manager.get_trades_since(
                task.exchange, task.symbol, since=task.last_trade_id, limit=task.limit
            )

            if not raw_trades:
                return []

            # Process trade data
            processed_trades = await self.data_processor.process_trades(
                raw_trades, task.exchange, task.symbol
            )

            if not processed_trades:
                return []

            # Validate trade data
            validation_report = self.validator.validate_trades(
                raw_trades, task.exchange, task.symbol
            )

            # Filter trades by quality
            valid_trades = []
            for i, trade in enumerate(processed_trades):
                # Calculate quality score for individual trade
                trade_quality = self._calculate_trade_quality(trade, raw_trades[i] if i < len(raw_trades) else {})
                trade.quality_score = trade_quality

                if trade_quality >= self.settings.DATA_QUALITY_THRESHOLD:
                    valid_trades.append(trade)

            if valid_trades:
                # Store trades
                await self._store_trades_data(valid_trades)

                # Cache latest trades
                await self._cache_trades_data(task.exchange, task.symbol, valid_trades)

                # Update last trade ID
                latest_trade = max(valid_trades, key=lambda x: x.timestamp)
                task.last_trade_id = latest_trade.trade_id

                # Record metrics
                self.metrics.record_data_quality(
                    task.exchange, task.symbol, 'trades',
                    validation_report.accuracy_score,
                    validation_report.completeness_score,
                    validation_report.timeliness_score
                )

                return valid_trades

            return []

        except Exception as e:
            self.logger.debug(f"Incremental trade fetch failed for {task.exchange}/{task.symbol}: {e}")
            return None  # Fall back to full fetch

    async def _fetch_full_trades(self, task: TradesCollectionTask) -> List[TradeData]:
        """Fetch full trade data set."""
        try:
            # Fetch recent trades
            raw_trades = await self.exchange_manager.get_trades(
                task.exchange, task.symbol, limit=task.limit
            )

            if not raw_trades:
                return []

            # Process trade data
            processed_trades = await self.data_processor.process_trades(
                raw_trades, task.exchange, task.symbol
            )

            if not processed_trades:
                return []

            # Validate trade data
            validation_report = self.validator.validate_trades(
                raw_trades, task.exchange, task.symbol
            )

            # Filter trades by quality
            valid_trades = []
            for i, trade in enumerate(processed_trades):
                # Calculate quality score for individual trade
                trade_quality = self._calculate_trade_quality(trade, raw_trades[i] if i < len(raw_trades) else {})
                trade.quality_score = trade_quality

                if trade_quality >= self.settings.DATA_QUALITY_THRESHOLD:
                    valid_trades.append(trade)

            if valid_trades:
                # Store trades
                await self._store_trades_data(valid_trades)

                # Cache latest trades
                await self._cache_trades_data(task.exchange, task.symbol, valid_trades)

                # Update last trade ID
                latest_trade = max(valid_trades, key=lambda x: x.timestamp)
                task.last_trade_id = latest_trade.trade_id

                # Record metrics
                self.metrics.record_data_quality(
                    task.exchange, task.symbol, 'trades',
                    validation_report.accuracy_score,
                    validation_report.completeness_score,
                    validation_report.timeliness_score
                )

                return valid_trades

            return []

        except Exception as e:
            self.logger.error(f"Full trade fetch failed for {task.exchange}/{task.symbol}: {e}")
            raise

    def _calculate_trade_quality(self, trade: TradeData, raw_trade: Dict) -> float:
        """Calculate quality score for a single trade."""
        quality_score = 1.0

        # Check for required fields
        required_fields = ['price', 'amount', 'side']
        for field in required_fields:
            if getattr(trade, field) is None:
                quality_score -= 0.3

        # Check price validity
        if trade.price <= 0:
            quality_score -= 0.4

        # Check amount validity
        if trade.amount <= 0:
            quality_score -= 0.3

        # Check side validity
        if trade.side not in ['buy', 'sell']:
            quality_score -= 0.2

        # Check timestamp reasonableness
        trade_age = (datetime.now() - trade.timestamp).total_seconds()
        if trade_age > 3600:  # Older than 1 hour
            quality_score -= 0.1

        return max(0.0, quality_score)

    async def _store_trades_data(self, trades: List[TradeData]):
        """Store trade data in database."""
        try:
            from ..models.database import get_timescaledb_session

            session = get_timescaledb_session()
            try:
                for trade in trades:
                    session.add(trade)
                session.commit()
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()

        except Exception as e:
            self.logger.error(f"Failed to store trade data: {e}")

    async def _cache_trades_data(self, exchange: str, symbol: str, trades: List[TradeData]):
        """Cache trade data in Redis."""
        try:
            cache_key = f"trades:{exchange}:{symbol}"

            # Convert to cacheable format
            cache_data = []
            for trade in trades[-100:]:  # Keep last 100 trades
                cache_data.append({
                    'timestamp': trade.timestamp.isoformat(),
                    'trade_id': trade.trade_id,
                    'price': trade.price,
                    'amount': trade.amount,
                    'side': trade.side,
                    'value': trade.value,
                    'quality_score': trade.quality_score
                })

            await self.redis.set_json(cache_key, cache_data, ttl=60)  # 1 minute cache

        except Exception as e:
            self.logger.error(f"Failed to cache trade data: {e}")

    async def get_recent_trades(self, exchange: str, symbol: str, limit: int = 50) -> List[Dict]:
        """Get recent trade data."""
        try:
            cache_key = f"trades:{exchange}:{symbol}"
            cached_data = await self.redis.get_json(cache_key)

            if cached_data:
                return cached_data[-limit:]

            # If not in cache, try to fetch from database
            return await self._get_recent_trades_from_db(exchange, symbol, limit)

        except Exception as e:
            self.logger.error(f"Failed to get recent trades: {e}")
            return []

    async def _get_recent_trades_from_db(self, exchange: str, symbol: str, limit: int) -> List[Dict]:
        """Get recent trades from database."""
        try:
            from ..models.database import get_timescaledb_session
            from sqlalchemy import desc

            session = get_timescaledb_session()
            try:
                # Query recent trades
                recent_trades = session.query(TradeData)\
                    .filter(TradeData.exchange == exchange)\
                    .filter(TradeData.symbol == symbol)\
                    .order_by(desc(TradeData.timestamp))\
                    .limit(limit)\
                    .all()

                trades_data = [trade.to_dict() for trade in recent_trades]
                return trades_data

            finally:
                session.close()

        except Exception as e:
            self.logger.error(f"Failed to get trades from database: {e}")
            return []

    async def get_trade_statistics(self, exchange: str, symbol: str,
                                 timeframe: str = '1h') -> Optional[Dict]:
        """Get trade statistics for a specific timeframe."""
        try:
            from ..models.database import get_timescaledb_session
            from sqlalchemy import func, and_
            from datetime import datetime, timedelta

            session = get_timescaledb_session()
            try:
                # Calculate time range
                if timeframe == '1h':
                    start_time = datetime.now() - timedelta(hours=1)
                elif timeframe == '24h':
                    start_time = datetime.now() - timedelta(days=1)
                elif timeframe == '7d':
                    start_time = datetime.now() - timedelta(days=7)
                else:
                    return None

                # Query trade statistics
                stats = session.query(
                    func.count(TradeData.trade_id).label('total_trades'),
                    func.sum(TradeData.value).label('total_volume'),
                    func.avg(TradeData.price).label('avg_price'),
                    func.min(TradeData.price).label('min_price'),
                    func.max(TradeData.price).label('max_price'),
                    func.sum(func.case([(TradeData.side == 'buy', TradeData.amount)], else_=0)).label('buy_volume'),
                    func.sum(func.case([(TradeData.side == 'sell', TradeData.amount)], else_=0)).label('sell_volume')
                ).filter(
                    and_(
                        TradeData.exchange == exchange,
                        TradeData.symbol == symbol,
                        TradeData.timestamp >= start_time
                    )
                ).first()

                if not stats or stats.total_trades == 0:
                    return None

                # Calculate additional metrics
                buy_ratio = stats.buy_volume / (stats.buy_volume + stats.sell_volume) if (stats.buy_volume + stats.sell_volume) > 0 else 0
                price_range = stats.max_price - stats.min_price
                price_volatility = (price_range / stats.avg_price) * 100 if stats.avg_price > 0 else 0

                return {
                    'timeframe': timeframe,
                    'total_trades': stats.total_trades,
                    'total_volume': float(stats.total_volume or 0),
                    'avg_price': float(stats.avg_price or 0),
                    'min_price': float(stats.min_price or 0),
                    'max_price': float(stats.max_price or 0),
                    'buy_volume': float(stats.buy_volume or 0),
                    'sell_volume': float(stats.sell_volume or 0),
                    'buy_ratio': buy_ratio,
                    'price_range': float(price_range),
                    'price_volatility_percent': float(price_volatility),
                    'timestamp': datetime.now().isoformat()
                }

            finally:
                session.close()

        except Exception as e:
            self.logger.error(f"Failed to get trade statistics: {e}")
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
                    'limit': task.limit,
                    'interval': task.interval,
                    'priority': task.priority,
                    'incremental_mode': task.incremental_mode,
                    'is_active': task.is_active,
                    'last_trade_id': task.last_trade_id,
                    'last_update': task.last_update.isoformat() if task.last_update else None,
                    'next_update': task.next_update.isoformat() if task.next_update else None,
                    'error_count': task.error_count,
                    'last_error': task.last_error
                }
                for task in self.tasks.values()
            ]
        }