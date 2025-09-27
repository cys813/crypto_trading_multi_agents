"""
Data Flow Manager for Long Analyst Agent.

This module manages the flow of data between different components,
including data reception, processing, storage, and distribution.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import time
from concurrent.futures import ThreadPoolExecutor

from ..models.market_data import MarketData, Timeframe, DataSource
from ..data_processing.data_receiver import DataReceiver, DataReceiverConfig, ProcessedData, DataType
from ..storage.storage_manager import StorageManager
from ..events.event_manager import EventManager
from ..utils.performance_monitor import PerformanceMonitor


class DataFlowState(Enum):
    """Data flow states."""
    IDLE = "idle"
    RECEIVING = "receiving"
    PROCESSING = "processing"
    STORING = "storing"
    DISTRIBUTING = "distributing"
    ERROR = "error"


@dataclass
class DataFlowConfig:
    """Configuration for data flow management."""

    # Flow control
    max_concurrent_flows: int = 100
    flow_timeout_seconds: int = 300
    enable_flow_control: bool = True

    # Queue settings
    max_queue_size: int = 10000
    queue_processing_interval_seconds: float = 0.1

    # Distribution settings
    enable_real_time_distribution: bool = True
    enable_batch_distribution: bool = True
    batch_distribution_interval_seconds: int = 60

    # Quality control
    enable_data_quality_monitoring: bool = True
    min_data_quality_score: float = 0.7
    enable_data_validation: bool = True

    # Retry settings
    max_retry_attempts: int = 3
    retry_delay_seconds: float = 1.0

    # Performance monitoring
    enable_performance_monitoring: bool = True
    metrics_collection_interval_seconds: int = 30


class DataFlowManager:
    """
    Manager for data flow between components.

    This class orchestrates the movement of data through the system,
    from reception through processing to distribution and storage.
    """

    def __init__(self, data_sources: List[str] = None, config: DataFlowConfig = None):
        """Initialize the data flow manager."""
        self.data_sources = data_sources or ["binance", "coinbase", "kraken"]
        self.config = config or DataFlowConfig()
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()

        # Initialize components
        self.data_receiver = DataReceiver(DataReceiverConfig())
        self.storage_manager = StorageManager()
        self.event_manager = EventManager()

        # Thread pool for concurrent processing
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_flows)

        # Data queues
        self.raw_data_queue = asyncio.Queue(maxsize=self.config.max_queue_size)
        self.processed_data_queue = asyncio.Queue(maxsize=self.config.max_queue_size)
        self.distribution_queue = asyncio.Queue(maxsize=self.config.max_queue_size)

        # Flow state management
        self.flow_states = {}
        self.active_flows = 0
        self.total_flows_processed = 0

        # Background tasks
        self.background_tasks = []
        self.is_running = False

        # Metrics
        self.metrics = {
            'total_received': 0,
            'total_processed': 0,
            'total_stored': 0,
            'total_distributed': 0,
            'processing_errors': 0,
            'average_processing_time': 0.0
        }

        self.logger.info("Data flow manager initialized")

    async def start(self):
        """Start the data flow manager."""
        self.logger.info("Starting data flow manager")

        if self.is_running:
            self.logger.warning("Data flow manager is already running")
            return

        # Start data receiver
        await self.data_receiver.start()

        # Start background processing tasks
        self.background_tasks = [
            asyncio.create_task(self._data_processing_loop()),
            asyncio.create_task(self._data_storage_loop()),
            asyncio.create_task(self._data_distribution_loop()),
            asyncio.create_task(self._flow_monitoring_loop())
        ]

        self.is_running = True
        self.logger.info("Data flow manager started")

    async def stop(self):
        """Stop the data flow manager."""
        self.logger.info("Stopping data flow manager")

        if not self.is_running:
            self.logger.warning("Data flow manager is not running")
            return

        self.is_running = False

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)

        # Stop data receiver
        await self.data_receiver.stop()

        # Shutdown thread pool
        self.executor.shutdown(wait=True)

        self.background_tasks.clear()
        self.logger.info("Data flow manager stopped")

    async def get_market_data(self, symbol: str, timeframe: Timeframe,
                            source: DataSource = DataSource.BINANCE,
                            limit: int = 1000) -> Optional[MarketData]:
        """
        Get market data from source.

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe
            source: Data source
            limit: Number of data points

        Returns:
            Market data or None if unavailable
        """
        try:
            # Fetch data from receiver
            processed_data = await self.data_receiver.fetch_market_data(
                symbol, timeframe, source, limit
            )

            if processed_data and processed_data.data is not None:
                # Convert to MarketData format
                market_data = MarketData(
                    symbol=symbol,
                    timeframe=timeframe,
                    source=source,
                    timestamp=time.time(),
                    data=processed_data.data,
                    metadata={
                        'quality': processed_data.quality.value,
                        'processing_time': processed_data.processing_time_ms,
                        'validation_errors': processed_data.validation_errors
                    }
                )

                # Add to processing queue
                await self.raw_data_queue.put(market_data)

                return market_data
            else:
                self.logger.warning(f"No data received for {symbol}")
                return None

        except Exception as e:
            self.logger.error(f"Error getting market data for {symbol}: {e}")
            return None

    async def process_real_time_updates(self):
        """Process real-time data updates."""
        updates_processed = 0

        try:
            # Process updates from queue
            while self.is_running and not self.raw_data_queue.empty():
                try:
                    market_data = await asyncio.wait_for(
                        self.raw_data_queue.get(),
                        timeout=1.0
                    )

                    # Process the update
                    await self._process_market_data(market_data)
                    updates_processed += 1

                except asyncio.TimeoutError:
                    break
                except Exception as e:
                    self.logger.error(f"Error processing real-time update: {e}")
                    self.metrics['processing_errors'] += 1

            return updates_processed

        except Exception as e:
            self.logger.error(f"Error in real-time updates processing: {e}")
            return 0

    async def _process_market_data(self, market_data: MarketData):
        """Process individual market data."""
        start_time = time.time()

        try:
            # Update flow state
            flow_id = f"{market_data.symbol}_{market_data.timeframe.value}_{int(time.time())}"
            self.flow_states[flow_id] = DataFlowState.PROCESSING

            # Validate data quality
            if self.config.enable_data_validation:
                quality_score = self._calculate_data_quality(market_data)
                if quality_score < self.config.min_data_quality_score:
                    self.logger.warning(f"Low quality data for {market_data.symbol}: {quality_score}")
                    self.flow_states[flow_id] = DataFlowState.ERROR
                    return

            # Process data
            processed_data = await self.data_receiver.receive_data(
                market_data.source,
                DataType.MARKET_DATA,
                market_data.data
            )

            if processed_data and processed_data.quality.value != 'invalid':
                # Add to processed queue
                await self.processed_data_queue.put(processed_data)

                # Update metrics
                self.metrics['total_processed'] += 1
                processing_time = (time.time() - start_time) * 1000
                self.metrics['average_processing_time'] = (
                    (self.metrics['average_processing_time'] * (self.metrics['total_processed'] - 1) + processing_time) /
                    self.metrics['total_processed']
                )

                # Update flow state
                self.flow_states[flow_id] = DataFlowState.STORING

            else:
                self.logger.error(f"Failed to process data for {market_data.symbol}")
                self.flow_states[flow_id] = DataFlowState.ERROR
                self.metrics['processing_errors'] += 1

        except Exception as e:
            self.logger.error(f"Error processing market data: {e}")
            self.metrics['processing_errors'] += 1

            # Update flow state
            if flow_id in self.flow_states:
                self.flow_states[flow_id] = DataFlowState.ERROR

    async def _data_processing_loop(self):
        """Background task for data processing."""
        self.logger.info("Starting data processing loop")

        while self.is_running:
            try:
                # Process real-time updates
                updates = await self.process_real_time_updates()

                # Sleep briefly to prevent busy waiting
                await asyncio.sleep(self.config.queue_processing_interval_seconds)

            except Exception as e:
                self.logger.error(f"Error in data processing loop: {e}")
                await asyncio.sleep(5)

        self.logger.info("Data processing loop stopped")

    async def _data_storage_loop(self):
        """Background task for data storage."""
        self.logger.info("Starting data storage loop")

        while self.is_running:
            try:
                # Process items from processed data queue
                if not self.processed_data_queue.empty():
                    processed_data = await asyncio.wait_for(
                        self.processed_data_queue.get(),
                        timeout=1.0
                    )

                    # Store data
                    await self._store_processed_data(processed_data)
                    self.metrics['total_stored'] += 1

                else:
                    await asyncio.sleep(self.config.queue_processing_interval_seconds)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in data storage loop: {e}")
                await asyncio.sleep(5)

        self.logger.info("Data storage loop stopped")

    async def _store_processed_data(self, processed_data: ProcessedData):
        """Store processed data."""
        try:
            # Store in database
            await self.storage_manager.store_market_data(processed_data)

            # Emit storage event
            await self.event_manager.emit("data_stored", {
                "source": processed_data.source.value,
                "data_type": processed_data.data_type.value,
                "quality": processed_data.quality.value,
                "timestamp": processed_data.timestamp
            })

        except Exception as e:
            self.logger.error(f"Error storing processed data: {e}")
            raise

    async def _data_distribution_loop(self):
        """Background task for data distribution."""
        self.logger.info("Starting data distribution loop")

        while self.is_running:
            try:
                # Process items from distribution queue
                if not self.distribution_queue.empty():
                    data = await asyncio.wait_for(
                        self.distribution_queue.get(),
                        timeout=1.0
                    )

                    # Distribute data to consumers
                    await self._distribute_data(data)
                    self.metrics['total_distributed'] += 1

                else:
                    await asyncio.sleep(self.config.queue_processing_interval_seconds)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in data distribution loop: {e}")
                await asyncio.sleep(5)

        self.logger.info("Data distribution loop stopped")

    async def _distribute_data(self, data: Any):
        """Distribute data to interested consumers."""
        try:
            # Emit distribution event
            await self.event_manager.emit("data_distributed", {
                "data_type": type(data).__name__,
                "timestamp": time.time()
            })

        except Exception as e:
            self.logger.error(f"Error distributing data: {e}")
            raise

    async def _flow_monitoring_loop(self):
        """Background task for flow monitoring."""
        self.logger.info("Starting flow monitoring loop")

        while self.is_running:
            try:
                # Monitor flow states
                await self._monitor_flow_states()

                # Collect metrics
                if self.config.enable_performance_monitoring:
                    await self._collect_metrics()

                # Sleep for monitoring interval
                await asyncio.sleep(self.config.metrics_collection_interval_seconds)

            except Exception as e:
                self.logger.error(f"Error in flow monitoring loop: {e}")
                await asyncio.sleep(10)

        self.logger.info("Flow monitoring loop stopped")

    async def _monitor_flow_states(self):
        """Monitor and manage flow states."""
        try:
            # Clean up old flow states
            current_time = time.time()
            expired_flows = []

            for flow_id, state in self.flow_states.items():
                # Remove flows that have been in error state for too long
                if state == DataFlowState.ERROR:
                    expired_flows.append(flow_id)

            for flow_id in expired_flows:
                del self.flow_states[flow_id]

            # Log current state
            state_counts = {}
            for state in self.flow_states.values():
                state_counts[state.value] = state_counts.get(state.value, 0) + 1

            self.logger.debug(f"Flow states: {state_counts}")

        except Exception as e:
            self.logger.error(f"Error monitoring flow states: {e}")

    async def _collect_metrics(self):
        """Collect performance metrics."""
        try:
            # Record queue sizes
            self.performance_monitor.record_metric("raw_queue_size", self.raw_data_queue.qsize())
            self.performance_monitor.record_metric("processed_queue_size", self.processed_data_queue.qsize())
            self.performance_monitor.record_metric("distribution_queue_size", self.distribution_queue.qsize())

            # Record processing metrics
            self.performance_monitor.record_metric("total_received", self.metrics['total_received'])
            self.performance_monitor.record_metric("total_processed", self.metrics['total_processed'])
            self.performance_monitor.record_metric("total_stored", self.metrics['total_stored'])
            self.performance_monitor.record_metric("total_distributed", self.metrics['total_distributed'])
            self.performance_monitor.record_metric("processing_errors", self.metrics['processing_errors'])

        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")

    def _calculate_data_quality(self, market_data: MarketData) -> float:
        """Calculate data quality score."""
        try:
            if not market_data.data or len(market_data.data) == 0:
                return 0.0

            # Check data completeness
            completeness = 1.0 - (market_data.data.isnull().sum().sum() / (len(market_data.data) * len(market_data.data.columns)))

            # Check data freshness
            freshness = 1.0 if time.time() - market_data.timestamp < 300 else 0.5  # 5 minutes

            # Check data consistency
            consistency = self._check_data_consistency(market_data.data)

            return (completeness + freshness + consistency) / 3.0

        except Exception:
            return 0.0

    def _check_data_consistency(self, data: Any) -> float:
        """Check data consistency."""
        try:
            if hasattr(data, 'columns'):
                # Check for price consistency
                if all(col in data.columns for col in ['high', 'low', 'open', 'close']):
                    consistent_rows = (
                        (data['high'] >= data['low']) &
                        (data['high'] >= data['open']) &
                        (data['high'] >= data['close']) &
                        (data['low'] <= data['open']) &
                        (data['low'] <= data['close'])
                    )
                    return consistent_rows.sum() / len(data)
            return 1.0
        except Exception:
            return 0.0

    async def get_metrics(self) -> Dict[str, Any]:
        """Get data flow metrics."""
        return {
            **self.metrics,
            "queue_sizes": {
                "raw": self.raw_data_queue.qsize(),
                "processed": self.processed_data_queue.qsize(),
                "distribution": self.distribution_queue.qsize()
            },
            "flow_states": {state.value: count for state, count in
                          self._count_flow_states().items()},
            "is_running": self.is_running,
            "active_flows": self.active_flows
        }

    def _count_flow_states(self) -> Dict[DataFlowState, int]:
        """Count flow states."""
        counts = {}
        for state in self.flow_states.values():
            counts[state] = counts.get(state, 0) + 1
        return counts

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health_status = {
            "status": "healthy",
            "components": {},
            "metrics": await self.get_metrics()
        }

        try:
            # Check data receiver health
            receiver_health = await self.data_receiver.health_check()
            health_status["components"]["data_receiver"] = receiver_health
            if receiver_health.get("status") != "healthy":
                health_status["status"] = "degraded"

            # Check storage manager health
            storage_health = await self.storage_manager.health_check()
            health_status["components"]["storage_manager"] = storage_health
            if storage_health.get("status") != "healthy":
                health_status["status"] = "degraded"

            # Check queue health
            queue_health = self._check_queue_health()
            health_status["components"]["queues"] = queue_health
            if queue_health.get("status") != "healthy":
                health_status["status"] = "degraded"

        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)

        return health_status

    def _check_queue_health(self) -> Dict[str, Any]:
        """Check queue health."""
        try:
            total_queue_size = (
                self.raw_data_queue.qsize() +
                self.processed_data_queue.qsize() +
                self.distribution_queue.qsize()
            )

            max_queue_capacity = self.config.max_queue_size * 3
            queue_usage = total_queue_size / max_queue_capacity

            if queue_usage > 0.9:
                return {"status": "unhealthy", "reason": "queues nearly full"}
            elif queue_usage > 0.7:
                return {"status": "degraded", "reason": "high queue usage"}
            else:
                return {"status": "healthy", "usage": queue_usage}

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def shutdown(self):
        """Shutdown the data flow manager."""
        await self.stop()