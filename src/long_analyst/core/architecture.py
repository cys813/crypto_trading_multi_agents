"""
Multi-dimensional Analysis Architecture for Long Analyst Agent.

This module provides the core architecture for integrating technical,
fundamental, and sentiment analysis with LLM-powered signal evaluation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..analysis.technical_analysis import TechnicalAnalysisEngine
from ..analysis.fundamental_analysis import FundamentalAnalysisEngine
from ..analysis.sentiment_analysis import SentimentAnalysisEngine
from ..llm.llm_integration import LLMAnalysisEngine
from ..signal.signal_evaluator import SignalEvaluator
from ..events.event_manager import EventManager
from ..storage.storage_manager import StorageManager
from ..models.signal import Signal, SignalStrength, SignalType
from ..models.market_data import MarketData
from ..models.analysis_result import AnalysisResult, AnalysisDimension
from ..utils.performance_monitor import PerformanceMonitor


class AnalysisMode(Enum):
    """Analysis execution modes."""
    REAL_TIME = "real_time"
    BATCH = "batch"
    BACKTEST = "backtest"


@dataclass
class ArchitectureConfig:
    """Configuration for the multi-dimensional analysis architecture."""

    # Performance settings
    max_concurrent_requests: int = 1000
    target_latency_ms: int = 500
    cache_ttl_seconds: int = 300

    # Analysis settings
    enable_technical_analysis: bool = True
    enable_fundamental_analysis: bool = True
    enable_sentiment_analysis: bool = True
    enable_llm_analysis: bool = True

    # Quality settings
    min_signal_strength: float = 0.6
    confidence_threshold: float = 0.7
    win_rate_threshold: float = 0.65

    # Scaling settings
    auto_scale: bool = True
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3

    # Integration settings
    integration_timeout_seconds: int = 30
    retry_attempts: int = 3
    backoff_factor: float = 2.0


class MultiDimensionalAnalysisEngine:
    """
    Core architecture for multi-dimensional analysis of cryptocurrency long signals.

    This engine orchestrates technical, fundamental, and sentiment analysis
    with LLM-powered evaluation and real-time event processing.
    """

    def __init__(self, config: ArchitectureConfig):
        """Initialize the analysis engine with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize performance monitoring
        self.performance_monitor = PerformanceMonitor()

        # Initialize event system
        self.event_manager = EventManager()

        # Initialize storage layer
        self.storage_manager = StorageManager()

        # Initialize analysis engines
        self.technical_engine = TechnicalAnalysisEngine() if config.enable_technical_analysis else None
        self.fundamental_engine = FundamentalAnalysisEngine() if config.enable_fundamental_analysis else None
        self.sentiment_engine = SentimentAnalysisEngine() if config.enable_sentiment_analysis else None
        self.llm_engine = LLMAnalysisEngine() if config.enable_llm_analysis else None

        # Initialize signal evaluator
        self.signal_evaluator = SignalEvaluator(
            min_strength=config.min_signal_strength,
            confidence_threshold=config.confidence_threshold
        )

        # Thread pool for concurrent processing
        self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_requests)

        # Initialize metrics
        self.total_signals_processed = 0
        self.average_processing_time = 0.0
        self.success_rate = 0.0

        self.logger.info("Multi-dimensional analysis engine initialized")

    async def analyze_market_data(self, market_data: MarketData, mode: AnalysisMode = AnalysisMode.REAL_TIME) -> List[Signal]:
        """
        Analyze market data using multi-dimensional approach.

        Args:
            market_data: Market data to analyze
            mode: Analysis execution mode

        Returns:
            List of generated signals
        """
        start_time = time.time()

        try:
            # Validate input data
            if not await self._validate_market_data(market_data):
                raise ValueError("Invalid market data provided")

            # Emit analysis start event
            await self.event_manager.emit("analysis_started", {
                "symbol": market_data.symbol,
                "timestamp": market_data.timestamp,
                "mode": mode.value
            })

            # Execute multi-dimensional analysis
            analysis_tasks = []

            if self.technical_engine:
                analysis_tasks.append(self._run_technical_analysis(market_data))

            if self.fundamental_engine:
                analysis_tasks.append(self._run_fundamental_analysis(market_data))

            if self.sentiment_engine:
                analysis_tasks.append(self._run_sentiment_analysis(market_data))

            # Run analysis concurrently
            analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

            # Filter out exceptions and process results
            valid_results = []
            for result in analysis_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Analysis error: {result}")
                    continue
                valid_results.append(result)

            # LLM-powered evaluation
            llm_enhanced_results = []
            if self.llm_engine and valid_results:
                llm_enhanced_results = await self._run_llm_evaluation(valid_results, market_data)

            # Signal evaluation and filtering
            signals = await self.signal_evaluator.evaluate_signals(
                llm_enhanced_results or valid_results,
                market_data
            )

            # Update performance metrics
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            await self._update_performance_metrics(signals, processing_time)

            # Store results
            await self.storage_manager.store_analysis_results(signals, market_data)

            # Emit analysis completion event
            await self.event_manager.emit("analysis_completed", {
                "symbol": market_data.symbol,
                "signals_count": len(signals),
                "processing_time_ms": processing_time,
                "success": True
            })

            return signals

        except Exception as e:
            self.logger.error(f"Analysis failed for {market_data.symbol}: {e}")

            # Emit error event
            await self.event_manager.emit("analysis_error", {
                "symbol": market_data.symbol,
                "error": str(e),
                "processing_time_ms": (time.time() - start_time) * 1000
            })

            raise

    async def _validate_market_data(self, market_data: MarketData) -> bool:
        """Validate market data before analysis."""
        if not market_data.symbol or not market_data.data:
            return False

        # Check data freshness
        current_time = time.time()
        if current_time - market_data.timestamp > 300:  # 5 minutes
            self.logger.warning(f"Stale market data for {market_data.symbol}")
            return False

        return True

    async def _run_technical_analysis(self, market_data: MarketData) -> AnalysisResult:
        """Run technical analysis on market data."""
        return await self.technical_engine.analyze(market_data)

    async def _run_fundamental_analysis(self, market_data: MarketData) -> AnalysisResult:
        """Run fundamental analysis on market data."""
        return await self.fundamental_engine.analyze(market_data)

    async def _run_sentiment_analysis(self, market_data: MarketData) -> AnalysisResult:
        """Run sentiment analysis on market data."""
        return await self.sentiment_engine.analyze(market_data)

    async def _run_llm_evaluation(self, analysis_results: List[AnalysisResult], market_data: MarketData) -> List[AnalysisResult]:
        """Run LLM evaluation on analysis results."""
        return await self.llm_engine.enhance_analysis(analysis_results, market_data)

    async def _update_performance_metrics(self, signals: List[Signal], processing_time: float):
        """Update performance metrics."""
        self.total_signals_processed += len(signals)

        # Update average processing time
        if self.total_signals_processed > 0:
            self.average_processing_time = (
                (self.average_processing_time * (self.total_signals_processed - len(signals)) + processing_time) /
                self.total_signals_processed
            )

        # Update success rate (signals with strength > threshold)
        successful_signals = len([s for s in signals if s.strength.value >= self.config.min_signal_strength])
        self.success_rate = successful_signals / len(signals) if signals else 0.0

        # Log performance metrics
        self.performance_monitor.record_metric("processing_time", processing_time)
        self.performance_monitor.record_metric("signals_generated", len(signals))
        self.performance_monitor.record_metric("success_rate", self.success_rate)

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return {
            "total_signals_processed": self.total_signals_processed,
            "average_processing_time_ms": self.average_processing_time,
            "success_rate": self.success_rate,
            "current_load": len(self.executor._threads) / self.config.max_concurrent_requests,
            "uptime_seconds": time.time() - self.performance_monitor.start_time,
            "error_rate": self.performance_monitor.get_error_rate()
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components."""
        health_status = {
            "overall": "healthy",
            "components": {},
            "performance": await self.get_performance_metrics()
        }

        # Check individual components
        components = [
            ("technical_engine", self.technical_engine),
            ("fundamental_engine", self.fundamental_engine),
            ("sentiment_engine", self.sentiment_engine),
            ("llm_engine", self.llm_engine),
            ("signal_evaluator", self.signal_evaluator),
            ("storage_manager", self.storage_manager),
            ("event_manager", self.event_manager)
        ]

        for name, component in components:
            try:
                if component and hasattr(component, "health_check"):
                    component_health = await component.health_check()
                    health_status["components"][name] = component_health
                    if component_health.get("status") != "healthy":
                        health_status["overall"] = "degraded"
                else:
                    health_status["components"][name] = {"status": "healthy"}
            except Exception as e:
                health_status["components"][name] = {"status": "unhealthy", "error": str(e)}
                health_status["overall"] = "unhealthy"

        return health_status

    async def shutdown(self):
        """Gracefully shutdown the analysis engine."""
        self.logger.info("Shutting down multi-dimensional analysis engine")

        # Shutdown thread pool
        self.executor.shutdown(wait=True)

        # Shutdown storage manager
        if hasattr(self.storage_manager, "shutdown"):
            await self.storage_manager.shutdown()

        # Shutdown event manager
        if hasattr(self.event_manager, "shutdown"):
            await self.event_manager.shutdown()

        self.logger.info("Multi-dimensional analysis engine shutdown complete")