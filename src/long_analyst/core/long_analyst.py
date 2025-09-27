"""
Long Analyst Agent - Main agent class for multi-dimensional analysis.

This class orchestrates all analysis components and provides the main interface
 for generating cryptocurrency long signals.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import time
from datetime import datetime, timedelta

from .architecture import MultiDimensionalAnalysisEngine, ArchitectureConfig, AnalysisMode
from .data_flow import DataFlowManager
from .orchestrator import AnalysisOrchestrator
from ..models.signal import Signal, SignalStrength, SignalType
from ..models.market_data import MarketData, Timeframe, DataSource
from ..models.analysis_result import AnalysisResult, AnalysisDimension
from ..utils.config_loader import ConfigLoader


@dataclass
class LongAnalystConfig:
    """Configuration for the Long Analyst Agent."""
    architecture_config: ArchitectureConfig
    data_sources: List[str] = None
    analysis_timeframes: List[Timeframe] = None
    symbols: List[str] = None
    max_signals_per_symbol: int = 5
    signal_expiry_hours: int = 24
    enable_real_time_processing: bool = True
    batch_processing_interval_seconds: int = 300

    def __post_init__(self):
        """Initialize default values."""
        if self.data_sources is None:
            self.data_sources = ["binance", "coinbase", "kraken"]
        if self.analysis_timeframes is None:
            self.analysis_timeframes = [Timeframe.M1, Timeframe.M5, Timeframe.M15, Timeframe.H1, Timeframe.H4]
        if self.symbols is None:
            self.symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "ADA/USDT"]


class LongAnalystAgent:
    """
    Main Long Analyst Agent for multi-dimensional cryptocurrency analysis.

    This agent integrates technical, fundamental, and sentiment analysis
    with LLM-powered evaluation to generate high-quality long signals.
    """

    def __init__(self, config: LongAnalystConfig):
        """Initialize the Long Analyst Agent."""
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize core components
        self.analysis_engine = MultiDimensionalAnalysisEngine(config.architecture_config)
        self.data_flow_manager = DataFlowManager(config.data_sources)
        self.orchestrator = AnalysisOrchestrator(config.analysis_timeframes)

        # State management
        self.active_signals: Dict[str, List[Signal]] = {}
        self.analysis_history: List[AnalysisResult] = []
        self.performance_stats = {}

        # Background tasks
        self.background_tasks = []
        self.is_running = False

        self.logger.info("Long Analyst Agent initialized")

    async def start(self):
        """Start the Long Analyst Agent."""
        self.logger.info("Starting Long Analyst Agent")

        if self.is_running:
            self.logger.warning("Agent is already running")
            return

        self.is_running = True

        # Start background tasks
        if self.config.enable_real_time_processing:
            self.background_tasks.append(
                asyncio.create_task(self._real_time_processing_loop())
            )

        # Start batch processing
        self.background_tasks.append(
            asyncio.create_task(self._batch_processing_loop())
        )

        # Start signal expiry monitoring
        self.background_tasks.append(
            asyncio.create_task(self._signal_expiry_monitor())
        )

        self.logger.info("Long Analyst Agent started successfully")

    async def stop(self):
        """Stop the Long Analyst Agent."""
        self.logger.info("Stopping Long Analyst Agent")

        if not self.is_running:
            self.logger.warning("Agent is not running")
            return

        self.is_running = False

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)

        # Shutdown components
        await self.analysis_engine.shutdown()
        await self.data_flow_manager.shutdown()
        await self.orchestrator.shutdown()

        self.background_tasks.clear()
        self.logger.info("Long Analyst Agent stopped successfully")

    async def analyze_symbol(self, symbol: str, timeframe: Timeframe = Timeframe.H1) -> List[Signal]:
        """
        Analyze a specific symbol and timeframe.

        Args:
            symbol: Trading symbol to analyze
            timeframe: Timeframe for analysis

        Returns:
            List of generated signals
        """
        self.logger.info(f"Analyzing {symbol} on {timeframe.value} timeframe")

        try:
            # Get market data
            market_data = await self.data_flow_manager.get_market_data(symbol, timeframe)
            if not market_data:
                self.logger.warning(f"No market data available for {symbol}")
                return []

            # Run analysis
            signals = await self.analysis_engine.analyze_market_data(market_data)

            # Filter and store signals
            filtered_signals = await self._filter_signals(signals, symbol)
            await self._store_signals(symbol, filtered_signals)

            self.logger.info(f"Generated {len(filtered_signals)} signals for {symbol}")
            return filtered_signals

        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            return []

    async def analyze_all_symbols(self) -> Dict[str, List[Signal]]:
        """
        Analyze all configured symbols.

        Returns:
            Dictionary mapping symbols to their signals
        """
        self.logger.info("Starting analysis of all configured symbols")

        results = {}

        # Create analysis tasks for all symbols
        tasks = []
        for symbol in self.config.symbols:
            for timeframe in self.config.analysis_timeframes:
                task = asyncio.create_task(self.analyze_symbol(symbol, timeframe))
                tasks.append((symbol, task))

        # Execute tasks concurrently
        for symbol, task in tasks:
            try:
                signals = await task
                if signals:
                    if symbol not in results:
                        results[symbol] = []
                    results[symbol].extend(signals)
            except Exception as e:
                self.logger.error(f"Error in analysis task for {symbol}: {e}")

        self.logger.info(f"Analysis complete. Generated signals for {len(results)} symbols")
        return results

    async def get_active_signals(self, symbol: Optional[str] = None) -> Union[List[Signal], Dict[str, List[Signal]]]:
        """
        Get active signals, optionally filtered by symbol.

        Args:
            symbol: Optional symbol to filter by

        Returns:
            Signals for the specified symbol or all active signals
        """
        if symbol:
            return self.active_signals.get(symbol, [])
        return self.active_signals

    async def get_signal_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Signal]:
        """
        Get historical signals.

        Args:
            symbol: Optional symbol to filter by
            limit: Maximum number of signals to return

        Returns:
            List of historical signals
        """
        all_signals = []
        for signals in self.active_signals.values():
            all_signals.extend(signals)

        if symbol:
            all_signals = [s for s in all_signals if s.symbol == symbol]

        # Sort by timestamp (newest first)
        all_signals.sort(key=lambda x: x.timestamp, reverse=True)
        return all_signals[:limit]

    async def get_performance_report(self) -> Dict[str, Any]:
        """
        Get comprehensive performance report.

        Returns:
            Performance metrics and statistics
        """
        engine_metrics = await self.analysis_engine.get_performance_metrics()
        orchestrator_metrics = await self.orchestrator.get_metrics()
        data_flow_metrics = await self.data_flow_manager.get_metrics()

        # Calculate signal statistics
        total_signals = sum(len(signals) for signals in self.active_signals.values())
        avg_signal_strength = 0.0

        if total_signals > 0:
            all_strengths = [s.strength.value for signals in self.active_signals.values() for s in signals]
            avg_signal_strength = sum(all_strengths) / len(all_strengths)

        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - self._get_start_time(),
            "is_running": self.is_running,
            "total_active_signals": total_signals,
            "average_signal_strength": avg_signal_strength,
            "symbols_tracked": len(self.config.symbols),
            "analysis_engine": engine_metrics,
            "orchestrator": orchestrator_metrics,
            "data_flow": data_flow_metrics,
            "background_tasks": len(self.background_tasks)
        }

    async def _real_time_processing_loop(self):
        """Background task for real-time processing."""
        self.logger.info("Starting real-time processing loop")

        while self.is_running:
            try:
                # Process real-time data updates
                await self.data_flow_manager.process_real_time_updates()

                # Check for new analysis triggers
                triggered_symbols = await self.orchestrator.get_triggered_symbols()
                if triggered_symbols:
                    for symbol, timeframe in triggered_symbols:
                        await self.analyze_symbol(symbol, timeframe)

                # Sleep for short interval
                await asyncio.sleep(1)

            except Exception as e:
                self.logger.error(f"Error in real-time processing loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying

        self.logger.info("Real-time processing loop stopped")

    async def _batch_processing_loop(self):
        """Background task for batch processing."""
        self.logger.info("Starting batch processing loop")

        while self.is_running:
            try:
                # Wait for next batch interval
                await asyncio.sleep(self.config.batch_processing_interval_seconds)

                if not self.is_running:
                    break

                # Run batch analysis
                await self.analyze_all_symbols()

                # Clean up old data
                await self._cleanup_old_data()

            except Exception as e:
                self.logger.error(f"Error in batch processing loop: {e}")

        self.logger.info("Batch processing loop stopped")

    async def _signal_expiry_monitor(self):
        """Background task to monitor and expire old signals."""
        self.logger.info("Starting signal expiry monitor")

        while self.is_running:
            try:
                current_time = time.time()
                expiry_time = current_time - (self.config.signal_expiry_hours * 3600)

                # Remove expired signals
                for symbol in list(self.active_signals.keys()):
                    active_signals = self.active_signals[symbol]
                    self.active_signals[symbol] = [
                        s for s in active_signals if s.timestamp > expiry_time
                    ]

                    # Remove empty lists
                    if not self.active_signals[symbol]:
                        del self.active_signals[symbol]

                # Sleep for 5 minutes
                await asyncio.sleep(300)

            except Exception as e:
                self.logger.error(f"Error in signal expiry monitor: {e}")
                await asyncio.sleep(60)

        self.logger.info("Signal expiry monitor stopped")

    async def _filter_signals(self, signals: List[Signal], symbol: str) -> List[Signal]:
        """Filter signals based on various criteria."""
        if not signals:
            return []

        # Limit number of signals per symbol
        if len(signals) > self.config.max_signals_per_symbol:
            # Sort by strength and keep top signals
            signals.sort(key=lambda x: x.strength.value, reverse=True)
            signals = signals[:self.config.max_signals_per_symbol]

        return signals

    async def _store_signals(self, symbol: str, signals: List[Signal]):
        """Store signals in active signals dictionary."""
        if not signals:
            return

        if symbol not in self.active_signals:
            self.active_signals[symbol] = []

        self.active_signals[symbol].extend(signals)

        # Remove duplicates
        unique_signals = []
        seen = set()
        for signal in self.active_signals[symbol]:
            signal_key = (signal.type.value, signal.timestamp)
            if signal_key not in seen:
                seen.add(signal_key)
                unique_signals.append(signal)

        self.active_signals[symbol] = unique_signals

    async def _cleanup_old_data(self):
        """Clean up old analysis data and results."""
        try:
            # Keep only recent analysis history
            cutoff_time = time.time() - (24 * 3600)  # 24 hours
            self.analysis_history = [
                result for result in self.analysis_history
                if result.timestamp > cutoff_time
            ]

            self.logger.debug("Cleanup of old data completed")

        except Exception as e:
            self.logger.error(f"Error in data cleanup: {e}")

    def _get_start_time(self) -> float:
        """Get agent start time."""
        # This is a placeholder - in a real implementation,
        # you'd track the actual start time
        return time.time()

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health_status = {
            "agent": "healthy",
            "components": {},
            "timestamp": datetime.now().isoformat()
        }

        try:
            # Check analysis engine
            engine_health = await self.analysis_engine.health_check()
            health_status["components"]["analysis_engine"] = engine_health
            if engine_health.get("overall") != "healthy":
                health_status["agent"] = "degraded"

            # Check data flow manager
            if hasattr(self.data_flow_manager, "health_check"):
                data_flow_health = await self.data_flow_manager.health_check()
                health_status["components"]["data_flow"] = data_flow_health
                if data_flow_health.get("status") != "healthy":
                    health_status["agent"] = "degraded"

            # Check orchestrator
            if hasattr(self.orchestrator, "health_check"):
                orchestrator_health = await self.orchestrator.health_check()
                health_status["components"]["orchestrator"] = orchestrator_health
                if orchestrator_health.get("status") != "healthy":
                    health_status["agent"] = "degraded"

            # Check background tasks
            active_tasks = [task for task in self.background_tasks if not task.done()]
            health_status["components"]["background_tasks"] = {
                "total": len(self.background_tasks),
                "active": len(active_tasks),
                "completed": len(self.background_tasks) - len(active_tasks)
            }

        except Exception as e:
            health_status["agent"] = "unhealthy"
            health_status["error"] = str(e)

        return health_status