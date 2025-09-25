"""
Data Collector - Handles automated data collection from exchanges.

This module manages the collection of market data (OHLCV, orderbook, trades, tickers)
from multiple exchanges with intelligent scheduling and quality control.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from enum import Enum

from .exchange_manager import ExchangeManager

logger = logging.getLogger(__name__)


class DataType(Enum):
    """Types of market data that can be collected."""
    OHLCV = "ohlcv"
    TICKER = "ticker"
    ORDERBOOK = "orderbook"
    TRADES = "trades"


@dataclass
class CollectionTask:
    """Represents a data collection task."""
    exchange_name: str
    symbol: str
    data_type: DataType
    timeframe: Optional[str] = None
    interval: int = 60  # seconds between collections
    priority: int = 1  # 1=high, 5=low
    enabled: bool = True
    last_collected: Optional[datetime] = None
    next_collection: Optional[datetime] = None


class DataCollector:
    """Manages automated data collection from multiple exchanges."""

    def __init__(self, exchange_manager: ExchangeManager):
        self.exchange_manager = exchange_manager
        self.tasks: Dict[str, CollectionTask] = {}
        self.collectors: Dict[str, asyncio.Task] = {}
        self.data_callbacks: Dict[DataType, List[Callable]] = {}
        self.is_running = False
        self.stats = {
            'total_collections': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'last_collection_time': None
        }

    def add_data_callback(self, data_type: DataType, callback: Callable):
        """Add a callback function to be called when data is collected."""
        if data_type not in self.data_callbacks:
            self.data_callbacks[data_type] = []
        self.data_callbacks[data_type].append(callback)

    def add_collection_task(self, task: CollectionTask) -> str:
        """Add a new collection task."""
        task_id = f"{task.exchange_name}_{task.symbol}_{task.data_type.value}"
        if task.timeframe:
            task_id += f"_{task.timeframe}"

        self.tasks[task_id] = task
        logger.info(f"Added collection task: {task_id}")

        if self.is_running:
            self._start_task_collector(task_id)

        return task_id

    def remove_collection_task(self, task_id: str):
        """Remove a collection task."""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False

            if task_id in self.collectors:
                self.collectors[task_id].cancel()
                del self.collectors[task_id]

            del self.tasks[task_id]
            logger.info(f"Removed collection task: {task_id}")

    async def start(self):
        """Start all collection tasks."""
        logger.info("Starting data collector...")

        if self.is_running:
            logger.warning("Data collector is already running")
            return

        self.is_running = True

        # Start all enabled tasks
        for task_id in self.tasks:
            if self.tasks[task_id].enabled:
                self._start_task_collector(task_id)

        logger.info(f"Data collector started with {len(self.collectors)} active tasks")

    def _start_task_collector(self, task_id: str):
        """Start a collector task for a specific task."""
        if task_id in self.collectors:
            self.collectors[task_id].cancel()

        task = self.tasks[task_id]
        collector = asyncio.create_task(self._collect_data(task_id))
        self.collectors[task_id] = collector

    async def stop(self):
        """Stop all collection tasks."""
        logger.info("Stopping data collector...")

        self.is_running = False

        # Cancel all collector tasks
        for task_id, collector in self.collectors.items():
            collector.cancel()

        # Wait for all tasks to complete
        if self.collectors:
            await asyncio.gather(*self.collectors.values(), return_exceptions=True)

        self.collectors.clear()
        logger.info("Data collector stopped")

    async def _collect_data(self, task_id: str):
        """Collect data for a specific task."""
        task = self.tasks[task_id]

        while task.enabled and self.is_running:
            try:
                # Wait until next collection time
                if task.next_collection:
                    wait_time = (task.next_collection - datetime.now()).total_seconds()
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)

                # Collect data
                data = await self._fetch_data(task)

                # Update stats
                self.stats['total_collections'] += 1
                self.stats['successful_collections'] += 1
                self.stats['last_collection_time'] = datetime.now()

                # Update task timing
                task.last_collected = datetime.now()
                task.next_collection = task.last_collected + timedelta(seconds=task.interval)

                # Process data through callbacks
                await self._process_data_callbacks(task.data_type, data, task)

                logger.debug(f"Successfully collected {task.data_type.value} for {task.symbol} on {task.exchange_name}")

            except Exception as e:
                self.stats['failed_collections'] += 1
                logger.error(f"Failed to collect data for task {task_id}: {e}")

                # Schedule retry
                task.next_collection = datetime.now() + timedelta(seconds=min(task.interval, 30))

                if task.enabled and self.is_running:
                    await asyncio.sleep(min(task.interval, 30))

    async def _fetch_data(self, task: CollectionTask) -> Any:
        """Fetch data from exchange based on task configuration."""
        if task.data_type == DataType.OHLCV:
            return await self.exchange_manager.get_ohlcv(
                task.exchange_name, task.symbol, task.timeframe, limit=100
            )
        elif task.data_type == DataType.TICKER:
            return await self.exchange_manager.get_ticker(task.exchange_name, task.symbol)
        elif task.data_type == DataType.ORDERBOOK:
            return await self.exchange_manager.get_orderbook(task.exchange_name, task.symbol, limit=50)
        elif task.data_type == DataType.TRADES:
            return await self.exchange_manager.get_trades(task.exchange_name, task.symbol, limit=100)
        else:
            raise ValueError(f"Unsupported data type: {task.data_type}")

    async def _process_data_callbacks(self, data_type: DataType, data: Any, task: CollectionTask):
        """Process collected data through registered callbacks."""
        if data_type not in self.data_callbacks:
            return

        enriched_data = {
            'data': data,
            'exchange': task.exchange_name,
            'symbol': task.symbol,
            'data_type': data_type.value,
            'timestamp': datetime.now().isoformat(),
            'task_id': f"{task.exchange_name}_{task.symbol}_{task.data_type.value}"
        }

        if task.timeframe:
            enriched_data['timeframe'] = task.timeframe

        # Call all callbacks for this data type
        for callback in self.data_callbacks[data_type]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(enriched_data)
                else:
                    callback(enriched_data)
            except Exception as e:
                logger.error(f"Error in data callback: {e}")

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        active_tasks = len([t for t in self.tasks.values() if t.enabled])
        return {
            **self.stats,
            'total_tasks': len(self.tasks),
            'active_tasks': active_tasks,
            'is_running': self.is_running
        }

    def get_task_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all collection tasks."""
        status = {}
        for task_id, task in self.tasks.items():
            status[task_id] = {
                'exchange': task.exchange_name,
                'symbol': task.symbol,
                'data_type': task.data_type.value,
                'timeframe': task.timeframe,
                'interval': task.interval,
                'priority': task.priority,
                'enabled': task.enabled,
                'last_collected': task.last_collected.isoformat() if task.last_collected else None,
                'next_collection': task.next_collection.isoformat() if task.next_collection else None
            }
        return status

    def add_default_tasks(self, symbols: List[str], exchanges: List[str]):
        """Add default collection tasks for common market data."""
        for exchange in exchanges:
            for symbol in symbols:
                # High priority: 1m OHLCV data
                self.add_collection_task(CollectionTask(
                    exchange_name=exchange,
                    symbol=symbol,
                    data_type=DataType.OHLCV,
                    timeframe='1m',
                    interval=60,
                    priority=1
                ))

                # Medium priority: 5m OHLCV data
                self.add_collection_task(CollectionTask(
                    exchange_name=exchange,
                    symbol=symbol,
                    data_type=DataType.OHLCV,
                    timeframe='5m',
                    interval=300,
                    priority=2
                ))

                # High priority: Ticker data
                self.add_collection_task(CollectionTask(
                    exchange_name=exchange,
                    symbol=symbol,
                    data_type=DataType.TICKER,
                    interval=10,
                    priority=1
                ))

                # Low priority: Orderbook data
                self.add_collection_task(CollectionTask(
                    exchange_name=exchange,
                    symbol=symbol,
                    data_type=DataType.ORDERBOOK,
                    interval=30,
                    priority=3
                ))

        logger.info(f"Added default collection tasks for {len(symbols)} symbols on {len(exchanges)} exchanges")