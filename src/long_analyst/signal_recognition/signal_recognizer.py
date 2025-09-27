"""
Signal Recognizer - Main signal detection and recognition engine.

This class orchestrates multiple signal detectors and provides
comprehensive signal recognition capabilities optimized for long trading.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from ..models.signal import Signal, SignalType, SignalStrength
from ..models.market_data import MarketData
from ..indicators.indicator_engine import IndicatorEngine, IndicatorConfig, IndicatorResult
from ..utils.performance_monitor import PerformanceMonitor
from .signal_config import SignalConfig, DetectionMode
from .signal_detector import SignalDetector, CompositeDetector, DetectorConfig, DetectionResult
from .signal_evaluator import SignalEvaluator
from .multi_timeframe_analyzer import MultiTimeframeAnalyzer


@dataclass
class RecognitionResult:
    """Result of signal recognition process."""
    signals: List[Signal]
    processing_time_ms: float
    total_detections: int
    successful_detections: int
    timeframe_consistency: float
    market_conditions: Dict[str, Any]
    metadata: Dict[str, Any]


class SignalRecognizer:
    """
    Advanced signal recognition engine for long trading opportunities.

    This engine integrates multiple detection algorithms, multi-timeframe analysis,
    and comprehensive signal evaluation to generate high-quality long signals.
    """

    def __init__(self, config: SignalConfig):
        """Initialize the signal recognizer."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()

        # Initialize indicator engine
        indicator_config = IndicatorConfig(
            max_concurrent_calculations=config.max_concurrent_detections,
            calculation_timeout_ms=config.detection_timeout_ms,
            enable_redis_cache=config.enable_caching,
            cache_ttl_seconds=config.cache_ttl_seconds
        )
        self.indicator_engine = IndicatorEngine(indicator_config)

        # Initialize detectors
        self.detectors = self._init_detectors()

        # Initialize signal evaluator
        self.signal_evaluator = SignalEvaluator(
            min_strength=config.min_signal_strength,
            confidence_threshold=config.min_confidence
        )

        # Initialize multi-timeframe analyzer
        if config.enable_multi_timeframe:
            self.multi_timeframe_analyzer = MultiTimeframeAnalyzer(config)
        else:
            self.multi_timeframe_analyzer = None

        # Thread pool for concurrent processing
        self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_detections)

        # Recognition cache
        self.recognition_cache: Dict[str, RecognitionResult] = {}
        self.cache_ttl = config.cache_ttl_seconds

        # Metrics
        self.total_recognitions = 0
        self.total_signals_generated = 0
        self.average_processing_time = 0.0
        self.cache_hits = 0
        self.cache_misses = 0

        self.logger.info("Signal recognizer initialized")

    def _init_detectors(self) -> Dict[str, SignalDetector]:
        """Initialize all signal detectors."""
        detectors = {}

        # Import detector implementations
        try:
            from .detectors.trend_detector import TrendDetector
            from .detectors.breakout_detector import BreakoutDetector
            from .detectors.pullback_detector import PullbackDetector
            from .detectors.pattern_detector import PatternDetector

            # Initialize detectors based on configuration
            if self.config.enable_trend_detection:
                detectors['trend'] = TrendDetector(
                    DetectorConfig(
                        name="trend_detector",
                        enabled=True,
                        priority=DetectorConfig.__annotations__['priority'].type.HIGH,
                        weight=0.4,
                        min_confidence=0.6,
                        parameters={
                            'min_period': self.config.trend_min_period,
                            'strength_threshold': self.config.trend_strength_threshold,
                            'require_volume': self.config.require_volume_confirmation,
                            'min_volume_ratio': self.config.min_volume_ratio
                        }
                    )
                )

            if self.config.enable_breakout_detection:
                detectors['breakout'] = BreakoutDetector(
                    DetectorConfig(
                        name="breakout_detector",
                        enabled=True,
                        priority=DetectorConfig.__annotations__['priority'].type.HIGH,
                        weight=0.3,
                        min_confidence=0.7,
                        parameters={
                            'lookback_periods': self.config.breakout_lookback_periods,
                            'confirmation_periods': self.config.breakout_confirmation_periods,
                            'volume_multiplier': self.config.breakout_volume_multiplier,
                            'false_breakout_filter': self.config.false_breakout_filter
                        }
                    )
                )

            if self.config.enable_pullback_detection:
                detectors['pullback'] = PullbackDetector(
                    DetectorConfig(
                        name="pullback_detector",
                        enabled=True,
                        priority=DetectorConfig.__annotations__['priority'].type.MEDIUM,
                        weight=0.2,
                        min_confidence=0.6,
                        parameters={
                            'fibonacci_levels': self.config.pullback_fibonacci_levels,
                            'ma_periods': self.config.pullback_ma_periods,
                            'max_depth': self.config.max_pullback_depth
                        }
                    )
                )

            if self.config.enable_pattern_recognition:
                detectors['pattern'] = PatternDetector(
                    DetectorConfig(
                        name="pattern_detector",
                        enabled=True,
                        priority=DetectorConfig.__annotations__['priority'].type.MEDIUM,
                        weight=0.1,
                        min_confidence=0.8,
                        parameters={
                            'min_confidence': self.config.pattern_min_confidence,
                            'lookback_periods': self.config.pattern_lookback_periods,
                            'enable_neckline': self.config.enable_neckline_breakout
                        }
                    )
                )

        except ImportError as e:
            self.logger.warning(f"Could not import detectors: {e}")
            self.logger.info("Using placeholder detectors")

        return detectors

    async def recognize_signals(self, market_data: MarketData,
                              mode: DetectionMode = DetectionMode.REAL_TIME) -> RecognitionResult:
        """
        Recognize trading signals from market data.

        Args:
            market_data: Market data to analyze
            mode: Detection mode

        Returns:
            Recognition result with signals and metadata
        """
        start_time = datetime.now()

        try:
            # Check cache first
            cache_key = self._generate_cache_key(market_data)
            cached_result = self._get_cached_result(cache_key)

            if cached_result:
                self.cache_hits += 1
                self.logger.debug(f"Cache hit for {market_data.symbol}")
                return cached_result

            self.cache_misses += 1

            # Validate market data
            if not self._validate_market_data(market_data):
                raise ValueError("Invalid market data provided")

            # Convert market data to DataFrame for analysis
            df = self._market_data_to_dataframe(market_data)
            if df is None or df.empty:
                raise ValueError("Could not convert market data to DataFrame")

            # Get required indicators for all detectors
            required_indicators = self._get_required_indicators()
            indicator_results = await self.indicator_engine.batch_calculate(required_indicators, df)

            # Detect signals using all detectors
            all_signals = await self._detect_signals(market_data, indicator_results)

            # Apply multi-timeframe analysis if enabled
            if self.multi_timeframe_analyzer and len(all_signals) > 0:
                all_signals = await self._apply_multi_timeframe_analysis(all_signals, market_data)

            # Filter and rank signals
            filtered_signals = await self._filter_and_rank_signals(all_signals, market_data)

            # Evaluate signals
            evaluated_signals = []
            for signal in filtered_signals:
                evaluation_result = await self.signal_evaluator.evaluate_signal(signal, market_data)
                if evaluation_result.should_execute:
                    evaluated_signals.append(evaluation_result.signal)

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Analyze market conditions
            market_conditions = self._analyze_market_conditions(market_data, indicator_results)

            # Calculate timeframe consistency
            timeframe_consistency = self._calculate_timeframe_consistency(evaluated_signals)

            # Create recognition result
            result = RecognitionResult(
                signals=evaluated_signals,
                processing_time_ms=processing_time,
                total_detections=len(all_signals),
                successful_detections=len(evaluated_signals),
                timeframe_consistency=timeframe_consistency,
                market_conditions=market_conditions,
                metadata={
                    'mode': mode.value,
                    'timestamp': datetime.now().isoformat(),
                    'symbol': market_data.symbol,
                    'timeframe': getattr(market_data, 'timeframe', 'unknown'),
                    'detectors_used': len([d for d in self.detectors.values() if d.config.enabled]),
                    'indicator_results_count': len(indicator_results)
                }
            )

            # Cache the result
            self._cache_result(cache_key, result)

            # Update metrics
            self._update_metrics(result)

            self.logger.info(f"Signal recognition completed for {market_data.symbol}: "
                           f"{len(evaluated_signals)} signals generated")

            return result

        except Exception as e:
            self.logger.error(f"Signal recognition failed for {market_data.symbol}: {e}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return RecognitionResult(
                signals=[],
                processing_time_ms=processing_time,
                total_detections=0,
                successful_detections=0,
                timeframe_consistency=0.0,
                market_conditions={},
                metadata={'error': str(e)}
            )

    async def validate_signals(self, signals: List[Signal],
                             market_data: MarketData) -> List[Signal]:
        """
        Validate and filter signals based on current market conditions.

        Args:
            signals: List of signals to validate
            market_data: Current market data

        Returns:
            List of validated signals
        """
        validated_signals = []

        for signal in signals:
            try:
                # Check if signal is still valid
                if not self._is_signal_valid(signal, market_data):
                    continue

                # Evaluate signal quality
                evaluation_result = await self.signal_evaluator.evaluate_signal(signal, market_data)
                if evaluation_result.should_execute:
                    validated_signals.append(evaluation_result.signal)

            except Exception as e:
                self.logger.error(f"Error validating signal {signal.id}: {e}")

        return validated_signals

    async def _detect_signals(self, market_data: MarketData,
                           indicator_results: Dict[str, IndicatorResult]) -> List[Signal]:
        """Detect signals using all enabled detectors."""
        detection_tasks = []

        for detector_name, detector in self.detectors.items():
            if detector.config.enabled:
                task = detector.detect_and_validate(market_data, indicator_results)
                detection_tasks.append((detector_name, task))

        # Run detections concurrently
        all_signals = []
        if detection_tasks:
            results = await asyncio.gather(*[task for _, task in detection_tasks], return_exceptions=True)

            # Process results
            for (detector_name, _), result in zip(detection_tasks, results):
                if isinstance(result, Exception):
                    self.logger.error(f"Error in {detector_name}: {result}")
                elif result:
                    all_signals.extend(result)

        return all_signals

    async def _apply_multi_timeframe_analysis(self, signals: List[Signal],
                                           market_data: MarketData) -> List[Signal]:
        """Apply multi-timeframe analysis to signals."""
        if not self.multi_timeframe_analyzer:
            return signals

        try:
            # Analyze signal consistency across timeframes
            consistency_scores = await self.multi_timeframe_analyzer.analyze_signal_consistency(
                signals, self.config.timeframes
            )

            # Filter signals based on consistency requirements
            filtered_signals = []
            for signal, consistency_score in zip(signals, consistency_scores):
                if (not self.config.require_timeframe_consistency or
                    consistency_score >= 0.5 or
                    len(self.multi_timeframe_analyzer.get_consistent_timeframes(signal)) >= self.config.min_consistent_timeframes):

                    # Update signal confidence based on consistency
                    signal.confidence *= (0.5 + 0.5 * consistency_score)
                    filtered_signals.append(signal)

            return filtered_signals

        except Exception as e:
            self.logger.error(f"Error in multi-timeframe analysis: {e}")
            return signals

    async def _filter_and_rank_signals(self, signals: List[Signal],
                                     market_data: MarketData) -> List[Signal]:
        """Filter and rank signals based on quality and relevance."""
        if not signals:
            return []

        # Filter by minimum strength and confidence
        filtered_signals = [
            signal for signal in signals
            if signal.strength.value >= self.config.min_signal_strength
            and signal.confidence >= self.config.min_confidence
        ]

        # Rank signals by composite score
        ranked_signals = sorted(
            filtered_signals,
            key=lambda s: (
                s.strength.value * 0.4 +
                s.confidence * 0.3 +
                s.win_probability * 0.3
            ),
            reverse=True
        )

        # Limit signals per symbol
        if self.config.max_signals_per_symbol:
            symbol_counts = {}
            final_signals = []

            for signal in ranked_signals:
                count = symbol_counts.get(signal.symbol, 0)
                if count < self.config.max_signals_per_symbol:
                    final_signals.append(signal)
                    symbol_counts[signal.symbol] = count + 1

            return final_signals

        return ranked_signals

    def _validate_market_data(self, market_data: MarketData) -> bool:
        """Validate market data for signal recognition."""
        if not market_data.symbol:
            return False

        # Check data freshness
        data_age = datetime.now().timestamp() - market_data.timestamp
        if data_age > 300:  # 5 minutes
            self.logger.warning(f"Stale market data for {market_data.symbol}")
            return False

        return True

    def _market_data_to_dataframe(self, market_data: MarketData) -> Optional[pd.DataFrame]:
        """Convert market data to pandas DataFrame."""
        try:
            if hasattr(market_data, 'ohlcv_data') and market_data.ohlcv_data:
                # Convert OHLCV data to DataFrame
                data_list = []
                for ohlcv in market_data.ohlcv_data:
                    data_list.append({
                        'timestamp': ohlcv.timestamp,
                        'open': ohlcv.open,
                        'high': ohlcv.high,
                        'low': ohlcv.low,
                        'close': ohlcv.close,
                        'volume': ohlcv.volume
                    })

                df = pd.DataFrame(data_list)
                df.set_index('timestamp', inplace=True)
                return df

            elif hasattr(market_data, 'data') and isinstance(market_data.data, pd.DataFrame):
                return market_data.data

            else:
                self.logger.warning("No usable market data format found")
                return None

        except Exception as e:
            self.logger.error(f"Error converting market data to DataFrame: {e}")
            return None

    def _get_required_indicators(self) -> List[str]:
        """Get list of required indicators from all detectors."""
        indicators = set()
        for detector in self.detectors.values():
            if detector.config.enabled:
                indicators.update(detector.get_required_indicators())
        return list(indicators)

    def _analyze_market_conditions(self, market_data: MarketData,
                                  indicator_results: Dict[str, IndicatorResult]) -> Dict[str, Any]:
        """Analyze current market conditions."""
        conditions = {
            'market_state': 'unknown',
            'volatility': 'moderate',
            'trend': 'neutral',
            'liquidity': 'normal'
        }

        try:
            # Analyze trend from indicators
            if 'rsi' in indicator_results:
                rsi_result = indicator_results['rsi']
                if 'current_rsi' in rsi_result.values:
                    rsi = rsi_result.values['current_rsi']
                    if rsi > 70:
                        conditions['trend'] = 'bullish'
                    elif rsi < 30:
                        conditions['trend'] = 'bearish'

            # Analyze volatility
            if 'bollinger_bands' in indicator_results:
                bb_result = indicator_results['bollinger_bands']
                if 'bandwidth' in bb_result.metadata:
                    bandwidth = bb_result.metadata['bandwidth']
                    if bandwidth > 0.1:
                        conditions['volatility'] = 'high'
                    elif bandwidth < 0.05:
                        conditions['volatility'] = 'low'

        except Exception as e:
            self.logger.error(f"Error analyzing market conditions: {e}")

        return conditions

    def _calculate_timeframe_consistency(self, signals: List[Signal]) -> float:
        """Calculate timeframe consistency score."""
        if not signals:
            return 0.0

        # Simple consistency calculation based on signal types
        signal_types = [s.signal_type for s in signals]
        if len(set(signal_types)) == 1:
            return 1.0  # All signals agree
        elif len(set(signal_types)) <= 2:
            return 0.7  # Mostly agree
        else:
            return 0.3  # Divergent signals

    def _is_signal_valid(self, signal: Signal, market_data: MarketData) -> bool:
        """Check if a signal is still valid."""
        # Check expiry
        if signal.is_expired:
            return False

        # Check if signal was already triggered
        if signal.was_triggered:
            return False

        # Check if signal is still active
        if not signal.is_active:
            return False

        return True

    def _generate_cache_key(self, market_data: MarketData) -> str:
        """Generate cache key for recognition result."""
        timeframe = getattr(market_data, 'timeframe', 'unknown')
        return f"{market_data.symbol}_{timeframe}_{int(market_data.timestamp)}"

    def _get_cached_result(self, cache_key: str) -> Optional[RecognitionResult]:
        """Get cached recognition result."""
        if cache_key in self.recognition_cache:
            cache_entry = self.recognition_cache[cache_key]
            if datetime.now().timestamp() - cache_entry.metadata['timestamp'] < self.cache_ttl:
                return cache_entry
            else:
                del self.recognition_cache[cache_key]
        return None

    def _cache_result(self, cache_key: str, result: RecognitionResult):
        """Cache recognition result."""
        if len(self.recognition_cache) < 1000:  # Limit cache size
            self.recognition_cache[cache_key] = result

    def _update_metrics(self, result: RecognitionResult):
        """Update recognition metrics."""
        self.total_recognitions += 1
        self.total_signals_generated += len(result.signals)

        # Update average processing time
        if self.total_recognitions > 0:
            self.average_processing_time = (
                (self.average_processing_time * (self.total_recognitions - 1) + result.processing_time_ms) /
                self.total_recognitions
            )

        # Record performance metrics
        self.performance_monitor.record_metric("recognition_time", result.processing_time_ms)
        self.performance_monitor.record_metric("signals_generated", len(result.signals))

    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive recognition statistics."""
        detector_stats = {}
        for name, detector in self.detectors.items():
            detector_stats[name] = detector.get_statistics()

        return {
            "total_recognitions": self.total_recognitions,
            "total_signals_generated": self.total_signals_generated,
            "average_processing_time_ms": self.average_processing_time,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0.0,
            "detector_statistics": detector_stats,
            "uptime_seconds": datetime.now().timestamp() - self.performance_monitor.start_time,
            "error_rate": self.performance_monitor.get_error_rate()
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health_status = {
            "status": "healthy",
            "components": {},
            "statistics": await self.get_statistics()
        }

        # Check individual components
        try:
            # Check indicator engine
            indicator_health = await self.indicator_engine.health_check()
            health_status["components"]["indicator_engine"] = indicator_health
            if indicator_health.get("status") != "healthy":
                health_status["status"] = "degraded"

            # Check detectors
            for name, detector in self.detectors.items():
                detector_health = await detector.health_check()
                health_status["components"][f"detector_{name}"] = detector_health
                if detector_health.get("status") != "healthy":
                    health_status["status"] = "degraded"

            # Check cache health
            cache_size = len(self.recognition_cache)
            health_status["components"]["cache"] = {
                "status": "healthy" if cache_size < 1000 else "warning",
                "size": cache_size,
                "hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0.0
            }

        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)

        return health_status

    async def shutdown(self):
        """Shutdown the signal recognizer."""
        self.logger.info("Shutting down signal recognizer")

        # Shutdown thread pool
        self.executor.shutdown(wait=True)

        # Shutdown indicator engine
        await self.indicator_engine.shutdown()

        # Clear cache
        self.recognition_cache.clear()

        self.logger.info("Signal recognizer shutdown complete")