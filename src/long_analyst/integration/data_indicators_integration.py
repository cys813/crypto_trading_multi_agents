"""
Integration module for Data Receiver and Technical Indicators Engine.

This module provides the integration layer between data processing
and technical analysis components for the Long Analyst Agent.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import time
import pandas as pd

from ..data_processing.data_receiver import DataReceiver, DataReceiverConfig, ProcessedData, DataType
from ..indicators.indicator_engine import IndicatorEngine, IndicatorConfig, IndicatorResult
from ..models.market_data import MarketData, Timeframe, DataSource
from ..events.event_manager import EventManager
from ..utils.performance_monitor import PerformanceMonitor


class IntegrationState(Enum):
    """Integration states."""
    IDLE = "idle"
    RECEIVING = "receiving"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class IntegrationConfig:
    """Configuration for data-indicators integration."""

    # Pipeline settings
    enable_real_time_analysis: bool = True
    enable_batch_analysis: bool = True
    analysis_interval_seconds: int = 60

    # Data quality settings
    min_data_quality_score: float = 0.7
    min_data_points: int = 50

    # Analysis settings
    enable_long_signals: bool = True
    enable_detailed_analysis: bool = True
    signal_threshold: float = 0.6

    # Performance settings
    max_concurrent_analyses: int = 10
    enable_caching: bool = True
    cache_ttl_seconds: int = 300

    # Error handling
    max_retry_attempts: int = 3
    retry_delay_seconds: float = 5.0


@dataclass
class AnalysisPipelineResult:
    """Result of the analysis pipeline."""

    success: bool
    symbol: str
    timeframe: Timeframe
    processed_data: Optional[ProcessedData]
    indicator_results: Dict[str, IndicatorResult]
    long_signals: Optional[Dict[str, Any]]
    error_message: Optional[str] = None
    processing_time_ms: float
    timestamp: float

    def __post_init__(self):
        """Initialize default values."""
        if not self.indicator_results:
            self.indicator_results = {}


class DataIndicatorsIntegration:
    """
    Integration layer between data receiver and indicators engine.

    This class orchestrates the flow from data reception through
    processing to technical analysis and signal generation.
    """

    def __init__(self, data_receiver_config: DataReceiverConfig = None,
                 indicator_config: IndicatorConfig = None,
                 integration_config: IntegrationConfig = None):
        """Initialize the integration layer."""
        self.data_receiver_config = data_receiver_config or DataReceiverConfig()
        self.indicator_config = indicator_config or IndicatorConfig()
        self.integration_config = integration_config or IntegrationConfig()

        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()
        self.event_manager = EventManager()

        # Initialize components
        self.data_receiver = DataReceiver(self.data_receiver_config)
        self.indicator_engine = IndicatorEngine(self.indicator_config)

        # Integration state
        self.state = IntegrationState.IDLE
        self.active_pipelines = 0
        self.total_pipelines = 0
        self.successful_pipelines = 0

        # Metrics
        self.metrics = {
            'total_data_received': 0,
            'total_data_processed': 0,
            'total_analyses': 0,
            'total_signals_generated': 0,
            'average_processing_time': 0.0,
            'data_quality_score': 0.0
        }

        # Background tasks
        self.background_tasks = []
        self.is_running = False

        self.logger.info("Data-indicators integration initialized")

    async def start(self):
        """Start the integration layer."""
        self.logger.info("Starting data-indicators integration")

        if self.is_running:
            self.logger.warning("Integration layer is already running")
            return

        # Start data receiver
        await self.data_receiver.start()

        # Start background tasks if enabled
        if self.integration_config.enable_real_time_analysis:
            self.background_tasks.append(
                asyncio.create_task(self._real_time_analysis_loop())
            )

        if self.integration_config.enable_batch_analysis:
            self.background_tasks.append(
                asyncio.create_task(self._batch_analysis_loop())
            )

        self.background_tasks.append(
            asyncio.create_task(self._metrics_collection_loop())
        )

        self.is_running = True
        self.logger.info("Data-indicators integration started")

    async def stop(self):
        """Stop the integration layer."""
        self.logger.info("Stopping data-indicators integration")

        if not self.is_running:
            self.logger.warning("Integration layer is not running")
            return

        self.is_running = False

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)

        # Stop components
        await self.data_receiver.stop()
        await self.indicator_engine.shutdown()

        self.background_tasks.clear()
        self.logger.info("Data-indicators integration stopped")

    async def analyze_market_data(self, symbol: str, timeframe: Timeframe,
                                source: DataSource = DataSource.BINANCE,
                                limit: int = 1000) -> AnalysisPipelineResult:
        """
        Complete analysis pipeline for market data.

        Args:
            symbol: Trading symbol
            timeframe: Data timeframe
            source: Data source
            limit: Number of data points

        Returns:
            Analysis pipeline result
        """
        start_time = time.time()
        pipeline_id = f"{symbol}_{timeframe.value}_{int(start_time)}"

        try:
            self.state = IntegrationState.RECEIVING
            self.active_pipelines += 1
            self.total_pipelines += 1

            # Emit pipeline start event
            await self.event_manager.emit("pipeline_started", {
                "pipeline_id": pipeline_id,
                "symbol": symbol,
                "timeframe": timeframe.value,
                "source": source.value
            })

            # Step 1: Receive and process data
            processed_data = await self._receive_and_process_data(symbol, timeframe, source, limit)

            if not processed_data or processed_data.quality.value == 'invalid':
                return AnalysisPipelineResult(
                    success=False,
                    symbol=symbol,
                    timeframe=timeframe,
                    processed_data=processed_data,
                    indicator_results={},
                    long_signals=None,
                    error_message="Failed to receive or process data",
                    processing_time_ms=(time.time() - start_time) * 1000,
                    timestamp=time.time()
                )

            self.state = IntegrationState.ANALYZING

            # Step 2: Convert processed data to DataFrame format for indicators
            market_data_df = self._convert_to_dataframe(processed_data)

            if market_data_df is None or len(market_data_df) < self.integration_config.min_data_points:
                return AnalysisPipelineResult(
                    success=False,
                    symbol=symbol,
                    timeframe=timeframe,
                    processed_data=processed_data,
                    indicator_results={},
                    long_signals=None,
                    error_message=f"Insufficient data points: {len(market_data_df) if market_data_df is not None else 0}",
                    processing_time_ms=(time.time() - start_time) * 1000,
                    timestamp=time.time()
                )

            # Step 3: Calculate technical indicators
            indicator_results = await self._calculate_indicators(market_data_df)

            # Step 4: Generate long signals if enabled
            long_signals = None
            if self.integration_config.enable_long_signals and indicator_results:
                long_signals = await self.indicator_engine.calculate_long_signals(market_data_df)

            # Update metrics
            self.metrics['total_data_processed'] += 1
            self.metrics['total_analyses'] += 1
            processing_time = (time.time() - start_time) * 1000
            self.metrics['average_processing_time'] = (
                (self.metrics['average_processing_time'] * (self.metrics['total_analyses'] - 1) + processing_time) /
                self.metrics['total_analyses']
            )

            # Update data quality score
            if hasattr(processed_data, 'metadata') and 'quality_score' in processed_data.metadata:
                quality_score = processed_data.metadata['quality_score']
                self.metrics['data_quality_score'] = (
                    (self.metrics['data_quality_score'] * (self.metrics['total_data_processed'] - 1) + quality_score) /
                    self.metrics['total_data_processed']
                )

            if long_signals and long_signals.get('overall_strength', 0) >= self.integration_config.signal_threshold:
                self.metrics['total_signals_generated'] += 1

            self.successful_pipelines += 1
            self.state = IntegrationState.COMPLETED

            # Emit pipeline completion event
            await self.event_manager.emit("pipeline_completed", {
                "pipeline_id": pipeline_id,
                "symbol": symbol,
                "timeframe": timeframe.value,
                "success": True,
                "processing_time_ms": processing_time,
                "signals_generated": long_signals is not None,
                "overall_strength": long_signals.get('overall_strength', 0) if long_signals else 0
            })

            return AnalysisPipelineResult(
                success=True,
                symbol=symbol,
                timeframe=timeframe,
                processed_data=processed_data,
                indicator_results=indicator_results,
                long_signals=long_signals,
                processing_time_ms=processing_time,
                timestamp=time.time()
            )

        except Exception as e:
            self.logger.error(f"Error in analysis pipeline for {symbol}: {e}")
            self.state = IntegrationState.ERROR

            # Emit pipeline error event
            await self.event_manager.emit("pipeline_error", {
                "pipeline_id": pipeline_id,
                "symbol": symbol,
                "timeframe": timeframe.value,
                "error": str(e),
                "processing_time_ms": (time.time() - start_time) * 1000
            })

            return AnalysisPipelineResult(
                success=False,
                symbol=symbol,
                timeframe=timeframe,
                processed_data=None,
                indicator_results={},
                long_signals=None,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000,
                timestamp=time.time()
            )

        finally:
            self.active_pipelines -= 1

    async def batch_analyze_symbols(self, symbols: List[str], timeframes: List[Timeframe],
                                   source: DataSource = DataSource.BINANCE,
                                   limit: int = 1000) -> Dict[str, AnalysisPipelineResult]:
        """
        Batch analyze multiple symbols and timeframes.

        Args:
            symbols: List of symbols to analyze
            timeframes: List of timeframes to analyze
            source: Data source
            limit: Number of data points

        Returns:
            Dictionary mapping symbol_timeframe to analysis results
        """
        results = {}

        # Create analysis tasks
        tasks = []
        task_keys = []

        for symbol in symbols:
            for timeframe in timeframes:
                task = self.analyze_market_data(symbol, timeframe, source, limit)
                tasks.append(task)
                task_keys.append(f"{symbol}_{timeframe.value}")

        # Execute tasks concurrently with limited concurrency
        semaphore = asyncio.Semaphore(self.integration_config.max_concurrent_analyses)

        async def limited_task(task):
            async with semaphore:
                return await task

        # Run all tasks
        task_results = await asyncio.gather(*[limited_task(task) for task in tasks], return_exceptions=True)

        # Process results
        for i, result in enumerate(task_results):
            key = task_keys[i]
            if isinstance(result, Exception):
                self.logger.error(f"Error in batch analysis for {key}: {result}")
                results[key] = AnalysisPipelineResult(
                    success=False,
                    symbol=key.split('_')[0],
                    timeframe=Timeframe(key.split('_')[1]),
                    processed_data=None,
                    indicator_results={},
                    long_signals=None,
                    error_message=str(result),
                    processing_time_ms=0,
                    timestamp=time.time()
                )
            else:
                results[key] = result

        return results

    async def _receive_and_process_data(self, symbol: str, timeframe: Timeframe,
                                      source: DataSource, limit: int) -> Optional[ProcessedData]:
        """Receive and process market data."""
        try:
            # Fetch market data from data receiver
            processed_data = await self.data_receiver.fetch_market_data(symbol, timeframe, source, limit)

            if processed_data and processed_data.quality.value != 'invalid':
                # Update metrics
                self.metrics['total_data_received'] += 1

                # Check data quality
                quality_score = getattr(processed_data, 'metadata', {}).get('quality_score', 0.5)
                if quality_score < self.integration_config.min_data_quality_score:
                    self.logger.warning(f"Low quality data for {symbol}: {quality_score}")

                return processed_data
            else:
                self.logger.warning(f"Failed to get valid data for {symbol}")
                return None

        except Exception as e:
            self.logger.error(f"Error receiving data for {symbol}: {e}")
            return None

    def _convert_to_dataframe(self, processed_data: ProcessedData) -> Optional[pd.DataFrame]:
        """Convert processed data to pandas DataFrame."""
        try:
            if processed_data and processed_data.data is not None:
                if isinstance(processed_data.data, pd.DataFrame):
                    return processed_data.data
                elif isinstance(processed_data.data, dict):
                    # Convert dict to DataFrame
                    return pd.DataFrame(processed_data.data)
                elif isinstance(processed_data.data, list):
                    # Convert list of dicts to DataFrame
                    return pd.DataFrame(processed_data.data)
                else:
                    self.logger.warning(f"Unsupported data format: {type(processed_data.data)}")
                    return None
            else:
                return None

        except Exception as e:
            self.logger.error(f"Error converting data to DataFrame: {e}")
            return None

    async def _calculate_indicators(self, data: pd.DataFrame) -> Dict[str, IndicatorResult]:
        """Calculate technical indicators."""
        try:
            # Get available indicators
            available_indicators = await self.indicator_engine.get_available_indicators()

            # Calculate indicators in batch
            indicator_results = await self.indicator_engine.batch_calculate(available_indicators, data)

            return indicator_results

        except Exception as e:
            self.logger.error(f"Error calculating indicators: {e}")
            return {}

    async def _real_time_analysis_loop(self):
        """Background task for real-time analysis."""
        self.logger.info("Starting real-time analysis loop")

        while self.is_running:
            try:
                # Process real-time updates from data receiver
                if hasattr(self.data_receiver, 'process_real_time_updates'):
                    updates_processed = await self.data_receiver.process_real_time_updates()

                    if updates_processed > 0:
                        self.logger.debug(f"Processed {updates_processed} real-time updates")

                # Sleep for analysis interval
                await asyncio.sleep(self.integration_config.analysis_interval_seconds)

            except Exception as e:
                self.logger.error(f"Error in real-time analysis loop: {e}")
                await asyncio.sleep(5)

        self.logger.info("Real-time analysis loop stopped")

    async def _batch_analysis_loop(self):
        """Background task for batch analysis."""
        self.logger.info("Starting batch analysis loop")

        while self.is_running:
            try:
                # Wait for batch interval
                await asyncio.sleep(self.integration_config.analysis_interval_seconds * 5)  # Longer interval for batch

                if not self.is_running:
                    break

                # Run batch analysis on configured symbols
                symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT']
                timeframes = [Timeframe.H1, Timeframe.H4]

                self.logger.info(f"Running batch analysis on {len(symbols)} symbols")

                results = await self.batch_analyze_symbols(symbols, timeframes)

                # Log batch results
                successful = sum(1 for r in results.values() if r.success)
                self.logger.info(f"Batch analysis completed: {successful}/{len(results)} successful")

            except Exception as e:
                self.logger.error(f"Error in batch analysis loop: {e}")
                await asyncio.sleep(10)

        self.logger.info("Batch analysis loop stopped")

    async def _metrics_collection_loop(self):
        """Background task for collecting integration metrics."""
        self.logger.info("Starting metrics collection loop")

        while self.is_running:
            try:
                # Collect component metrics
                receiver_metrics = await self.data_receiver.get_metrics()
                engine_metrics = await self.indicator_engine.get_metrics()

                # Record integration-specific metrics
                self.performance_monitor.record_metric("active_pipelines", self.active_pipelines)
                self.performance_monitor.record_metric("total_pipelines", self.total_pipelines)
                self.performance_monitor.record_metric("successful_pipelines", self.successful_pipelines)
                self.performance_monitor.record_metric("pipeline_success_rate", self.successful_pipelines / max(1, self.total_pipelines))

                # Record component metrics
                for key, value in receiver_metrics.items():
                    if isinstance(value, (int, float)):
                        self.performance_monitor.record_metric(f"receiver_{key}", value)

                for key, value in engine_metrics.items():
                    if isinstance(value, (int, float)):
                        self.performance_monitor.record_metric(f"engine_{key}", value)

                await asyncio.sleep(30)  # Collect metrics every 30 seconds

            except Exception as e:
                self.logger.error(f"Error in metrics collection loop: {e}")
                await asyncio.sleep(30)

        self.logger.info("Metrics collection loop stopped")

    async def get_metrics(self) -> Dict[str, Any]:
        """Get integration metrics."""
        receiver_metrics = await self.data_receiver.get_metrics()
        engine_metrics = await self.indicator_engine.get_metrics()

        return {
            **self.metrics,
            "pipeline_success_rate": self.successful_pipelines / max(1, self.total_pipelines),
            "active_pipelines": self.active_pipelines,
            "total_pipelines": self.total_pipelines,
            "current_state": self.state.value,
            "is_running": self.is_running,
            "data_receiver_metrics": receiver_metrics,
            "indicator_engine_metrics": engine_metrics
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the integration."""
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

            # Check indicator engine health
            engine_health = await self.indicator_engine.health_check()
            health_status["components"]["indicator_engine"] = engine_health
            if engine_health.get("status") != "healthy":
                health_status["status"] = "degraded"

            # Check pipeline performance
            if self.metrics.get("pipeline_success_rate", 0) < 0.8:
                health_status["status"] = "degraded"
                health_status["components"]["pipeline_performance"] = {
                    "status": "degraded",
                    "success_rate": self.metrics.get("pipeline_success_rate", 0)
                }

        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)

        return health_status

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "timestamp": time.time(),
            "uptime_seconds": time.time() - self.performance_monitor.start_time,
            "state": self.state.value,
            "active_pipelines": self.active_pipelines,
            "total_pipelines_processed": self.total_pipelines,
            "success_rate": self.successful_pipelines / max(1, self.total_pipelines),
            "average_processing_time_ms": self.metrics.get("average_processing_time", 0),
            "total_signals_generated": self.metrics.get("total_signals_generated", 0),
            "data_quality_score": self.metrics.get("data_quality_score", 0),
            "available_indicators": await self.indicator_engine.get_available_indicators(),
            "cache_stats": (await self.indicator_engine.cache.get_cache_stats()) if hasattr(self.indicator_engine, 'cache') else {}
        }