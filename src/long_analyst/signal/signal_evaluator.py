"""
Signal Evaluation Engine for the Long Analyst Agent.

Provides comprehensive signal evaluation, quality assessment,
and win rate calculation capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
import numpy as np

from ..models.signal import Signal, SignalType, SignalStrength, SignalSource, SignalCategory
from ..models.market_data import MarketData
from ..models.analysis_result import AnalysisResult, AnalysisDimension
from ..models.performance_metrics import WinRateCalculator, SignalPerformance
from ..utils.performance_monitor import PerformanceMonitor


@dataclass
class EvaluationCriteria:
    """Criteria for signal evaluation."""
    min_strength: float = 0.6
    min_confidence: float = 0.7
    min_win_rate: float = 0.65
    max_risk_level: float = 0.8
    require_volume_confirmation: bool = True
    require_multiple_confirmations: bool = True
    min_confirmation_count: int = 2


@dataclass
class EvaluationResult:
    """Result of signal evaluation."""
    signal: Signal
    quality_score: float
    confidence_score: float
    should_execute: bool
    reasoning: str
    risk_factors: List[str]
    recommendations: List[str]
    expected_win_rate: float
    risk_reward_ratio: Optional[float] = None


class SignalEvaluator:
    """
    Advanced signal evaluation engine.

    This engine provides comprehensive evaluation of trading signals
    based on multiple criteria including technical indicators,
    market conditions, and historical performance.
    """

    def __init__(self, min_strength: float = 0.6, confidence_threshold: float = 0.7):
        """Initialize the signal evaluator."""
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()

        # Evaluation criteria
        self.criteria = EvaluationCriteria(
            min_strength=min_strength,
            min_confidence=confidence_threshold
        )

        # Win rate calculator
        self.win_rate_calculator = WinRateCalculator()

        # Evaluation cache
        self.evaluation_cache: Dict[str, EvaluationResult] = {}
        self.cache_ttl = 300  # 5 minutes

        # Metrics
        self.total_evaluations = 0
        self.average_evaluation_time = 0.0
        self.approval_rate = 0.0

        self.logger.info("Signal evaluator initialized")

    async def evaluate_signals(self, analysis_results: List[AnalysisResult], market_data: MarketData) -> List[Signal]:
        """
        Evaluate analysis results and generate trading signals.

        Args:
            analysis_results: Analysis results from different dimensions
            market_data: Current market data

        Returns:
            List of evaluated trading signals
        """
        start_time = datetime.now()

        try:
            # Generate initial signals from analysis results
            raw_signals = await self._generate_raw_signals(analysis_results, market_data)

            # Evaluate each signal
            evaluated_signals = []
            for signal in raw_signals:
                evaluation_result = await self.evaluate_signal(signal, market_data)
                if evaluation_result.should_execute:
                    evaluated_signals.append(evaluation_result.signal)

            # Filter and rank signals
            filtered_signals = await self._filter_and_rank_signals(evaluated_signals, market_data)

            # Update metrics
            self.total_evaluations += 1
            evaluation_time = (datetime.now() - start_time).total_seconds()
            self.average_evaluation_time = (
                (self.average_evaluation_time * (self.total_evaluations - 1) + evaluation_time) /
                self.total_evaluations
            )

            self.approval_rate = len(filtered_signals) / len(raw_signals) if raw_signals else 0.0

            self.performance_monitor.record_metric("signal_evaluation_time", evaluation_time)
            self.performance_monitor.record_metric("signals_generated", len(filtered_signals))

            self.logger.info(f"Signal evaluation completed: {len(filtered_signals)}/{len(raw_signals)} signals approved")
            return filtered_signals

        except Exception as e:
            self.logger.error(f"Signal evaluation failed: {e}")
            return []

    async def evaluate_signal(self, signal: Signal, market_data: MarketData) -> EvaluationResult:
        """
        Evaluate a single trading signal.

        Args:
            signal: Signal to evaluate
            market_data: Current market data

        Returns:
            Evaluation result
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key(signal, market_data)
            cached_result = self._get_cached_evaluation(cache_key)

            if cached_result:
                return cached_result

            # Evaluate signal strength
            strength_score = self._evaluate_signal_strength(signal)

            # Evaluate signal confidence
            confidence_score = self._evaluate_signal_confidence(signal, market_data)

            # Evaluate signal quality
            quality_score = self._evaluate_signal_quality(signal, market_data)

            # Check execution criteria
            should_execute = self._check_execution_criteria(signal, market_data, strength_score, confidence_score, quality_score)

            # Generate reasoning and recommendations
            reasoning, risk_factors, recommendations = self._generate_evaluation_reasoning(
                signal, market_data, strength_score, confidence_score, quality_score
            )

            # Calculate expected win rate
            expected_win_rate = self._calculate_expected_win_rate(signal, market_data)

            # Calculate risk/reward ratio
            risk_reward_ratio = self._calculate_risk_reward_ratio(signal, market_data)

            # Create evaluation result
            evaluation_result = EvaluationResult(
                signal=signal,
                quality_score=quality_score,
                confidence_score=confidence_score,
                should_execute=should_execute,
                reasoning=reasoning,
                risk_factors=risk_factors,
                recommendations=recommendations,
                expected_win_rate=expected_win_rate,
                risk_reward_ratio=risk_reward_ratio
            )

            # Cache the result
            self._cache_evaluation(cache_key, evaluation_result)

            return evaluation_result

        except Exception as e:
            self.logger.error(f"Signal evaluation failed for {signal.symbol}: {e}")
            return EvaluationResult(
                signal=signal,
                quality_score=0.3,
                confidence_score=0.3,
                should_execute=False,
                reasoning=f"Evaluation failed: {str(e)}",
                risk_factors=["Evaluation error"],
                recommendations=["Manual review required"],
                expected_win_rate=0.3
            )

    async def _generate_raw_signals(self, analysis_results: List[AnalysisResult], market_data: MarketData) -> List[Signal]:
        """Generate raw signals from analysis results."""
        raw_signals = []

        for result in analysis_results:
            if not result.is_successful:
                continue

            # Generate signal based on analysis score
            if result.score >= self.criteria.min_strength:
                signal_type = self._determine_signal_type(result.score)
                signal_strength = self._determine_signal_strength(result.score)

                signal = Signal(
                    symbol=market_data.symbol,
                    signal_type=signal_type,
                    strength=signal_strength,
                    timestamp=result.timestamp,
                    confidence=result.confidence,
                    combined_score=result.score,
                    technical_score=result.technical_score,
                    fundamental_score=result.fundamental_score,
                    sentiment_score=result.sentiment_score,
                    llm_score=result.llm_score,
                    timeframe=result.timeframe
                )

                # Add analysis sources
                self._add_analysis_sources(signal, result)

                # Set targets if available
                self._set_signal_targets(signal, result, market_data)

                raw_signals.append(signal)

        return raw_signals

    def _evaluate_signal_strength(self, signal: Signal) -> float:
        """Evaluate signal strength."""
        strength_score = 0.0

        # Base strength
        strength_score += signal.strength.value * 0.4

        # Combined score
        strength_score += signal.combined_score * 0.3

        # Individual dimension scores
        dimension_scores = [
            signal.technical_score,
            signal.fundamental_score,
            signal.sentiment_score,
            signal.llm_score
        ]
        strength_score += max(dimension_scores) * 0.2

        # Source consistency
        if signal.sources:
            avg_source_confidence = statistics.mean([s.confidence for s in signal.sources])
            strength_score += avg_source_confidence * 0.1

        return min(1.0, strength_score)

    def _evaluate_signal_confidence(self, signal: Signal, market_data: MarketData) -> float:
        """Evaluate signal confidence."""
        confidence_score = 0.0

        # Base confidence
        confidence_score += signal.confidence * 0.3

        # Source count and quality
        if signal.sources:
            source_count = len(signal.sources)
            source_quality = statistics.mean([s.confidence for s in signal.sources])
            confidence_score += min(source_count / 5, 1.0) * 0.3
            confidence_score += source_quality * 0.2

        # Market data quality
        confidence_score += market_data.quality_score * 0.1

        # Signal freshness
        signal_age = (datetime.now().timestamp() - signal.timestamp) / 60  # minutes
        if signal_age < 5:
            confidence_score += 0.1
        elif signal_age < 15:
            confidence_score += 0.05

        return min(1.0, confidence_score)

    def _evaluate_signal_quality(self, signal: Signal, market_data: MarketData) -> float:
        """Evaluate overall signal quality."""
        quality_score = 0.0

        # Risk assessment
        risk_penalty = signal.risk_level * 0.2
        quality_score -= risk_penalty

        # Volume confirmation
        if self.criteria.require_volume_confirmation:
            volume_score = self._evaluate_volume_confirmation(signal, market_data)
            quality_score += volume_score * 0.3

        # Multiple confirmations
        if self.criteria.require_multiple_confirmations:
            confirmation_score = self._evaluate_multiple_confirmations(signal)
            quality_score += confirmation_score * 0.3

        # Market conditions
        market_score = self._evaluate_market_conditions(signal, market_data)
        quality_score += market_score * 0.2

        return max(0.0, min(1.0, quality_score))

    def _check_execution_criteria(self, signal: Signal, market_data: MarketData,
                                 strength_score: float, confidence_score: float, quality_score: float) -> bool:
        """Check if signal meets execution criteria."""
        # Basic thresholds
        if strength_score < self.criteria.min_strength:
            return False

        if confidence_score < self.criteria.min_confidence:
            return False

        if quality_score < 0.5:
            return False

        if signal.risk_level > self.criteria.max_risk_level:
            return False

        # Win rate requirement
        historical_win_rate = self._get_historical_win_rate(signal.signal_type)
        if historical_win_rate < self.criteria.min_win_rate:
            return False

        return True

    def _generate_evaluation_reasoning(self, signal: Signal, market_data: MarketData,
                                    strength_score: float, confidence_score: float, quality_score: float) -> Tuple[str, List[str], List[str]]:
        """Generate evaluation reasoning, risk factors, and recommendations."""
        reasoning_parts = []
        risk_factors = []
        recommendations = []

        # Strength assessment
        if strength_score >= 0.8:
            reasoning_parts.append("Signal shows exceptional strength across multiple dimensions")
        elif strength_score >= 0.6:
            reasoning_parts.append("Signal demonstrates good strength")
        else:
            reasoning_parts.append("Signal strength is below optimal levels")

        # Confidence assessment
        if confidence_score >= 0.8:
            reasoning_parts.append("High confidence in signal reliability")
        elif confidence_score >= 0.6:
            reasoning_parts.append("Moderate confidence in signal")
        else:
            reasoning_parts.append("Low confidence requires caution")

        # Risk factors
        if signal.risk_level > 0.7:
            risk_factors.append("High risk level detected")
        if signal.win_probability < 0.6:
            risk_factors.append("Low historical win probability")
        if market_data.age_seconds > 300:
            risk_factors.append("Stale market data")

        # Recommendations
        if strength_score >= 0.8 and confidence_score >= 0.8:
            recommendations.append("Consider full position size")
        elif strength_score >= 0.6:
            recommendations.append("Consider partial position with stop-loss")
        else:
            recommendations.append("Wait for better signal confirmation")

        # Volume-based recommendations
        if self.criteria.require_volume_confirmation:
            recommendations.append("Confirm with volume analysis")

        reasoning = ". ".join(reasoning_parts) + "."
        return reasoning, risk_factors, recommendations

    def _calculate_expected_win_rate(self, signal: Signal, market_data: MarketData) -> float:
        """Calculate expected win rate for the signal."""
        # Historical win rate for signal type
        historical_win_rate = self._get_historical_win_rate(signal.signal_type)

        # Adjust based on signal strength
        strength_adjustment = (signal.strength.value - 0.5) * 0.2

        # Adjust based on confidence
        confidence_adjustment = (signal.confidence - 0.5) * 0.2

        # Adjust based on market conditions
        market_adjustment = self._get_market_condition_adjustment(market_data)

        expected_win_rate = historical_win_rate + strength_adjustment + confidence_adjustment + market_adjustment
        return max(0.0, min(1.0, expected_win_rate))

    def _calculate_risk_reward_ratio(self, signal: Signal, market_data: MarketData) -> Optional[float]:
        """Calculate risk/reward ratio."""
        current_price = market_data.get_price()
        if not current_price or not signal.stop_loss or not signal.take_profit:
            return None

        if signal.signal_type in [SignalType.BUY, SignalType.MODERATE_BUY, SignalType.STRONG_BUY]:
            risk = current_price - signal.stop_loss
            reward = signal.take_profit - current_price
        else:
            risk = signal.stop_loss - current_price
            reward = current_price - signal.take_profit

        return reward / risk if risk > 0 else None

    def _determine_signal_type(self, score: float) -> SignalType:
        """Determine signal type based on score."""
        if score >= 0.8:
            return SignalType.STRONG_BUY
        elif score >= 0.7:
            return SignalType.BUY
        elif score >= 0.6:
            return SignalType.MODERATE_BUY
        else:
            return SignalType.HOLD

    def _determine_signal_strength(self, score: float) -> SignalStrength:
        """Determine signal strength based on score."""
        if score >= 0.8:
            return SignalStrength.VERY_STRONG
        elif score >= 0.7:
            return SignalStrength.STRONG
        elif score >= 0.6:
            return SignalStrength.MODERATE
        elif score >= 0.4:
            return SignalStrength.WEAK
        else:
            return SignalStrength.VERY_WEAK

    def _add_analysis_sources(self, signal: Signal, result: AnalysisResult):
        """Add analysis sources to signal."""
        # Add technical source if available
        if result.technical_indicators:
            signal.sources.append(SignalSource(
                category=SignalCategory.TECHNICAL,
                name="technical_analysis",
                confidence=result.technical_score,
                weight=0.4
            ))

        # Add fundamental source if available
        if result.fundamental_metrics:
            signal.sources.append(SignalSource(
                category=SignalCategory.FUNDAMENTAL,
                name="fundamental_analysis",
                confidence=result.fundamental_score,
                weight=0.3
            ))

        # Add sentiment source if available
        if result.sentiment_metrics:
            signal.sources.append(SignalSource(
                category=SignalCategory.SENTIMENT,
                name="sentiment_analysis",
                confidence=result.sentiment_score,
                weight=0.2
            ))

        # Add LLM source if available
        if result.llm_analysis:
            signal.sources.append(SignalSource(
                category=SignalCategory.LLM_ENHANCED,
                name="llm_analysis",
                confidence=result.llm_score,
                weight=0.1
            ))

    def _set_signal_targets(self, signal: Signal, result: AnalysisResult, market_data: MarketData):
        """Set signal price targets based on analysis."""
        current_price = market_data.get_price()
        if not current_price:
            return

        # Set price target based on expected return
        if signal.expected_return > 0:
            signal.price_target = current_price * (1 + signal.expected_return / 100)

        # Set stop-loss and take-profit based on risk management
        if signal.signal_type in [SignalType.BUY, SignalType.MODERATE_BUY, SignalType.STRONG_BUY]:
            # Conservative stop-loss at 2% below entry
            signal.stop_loss = current_price * 0.98
            # Take-profit at 2x expected return
            signal.take_profit = current_price * (1 + signal.expected_return / 50)
        else:
            # For other signals, use tighter stops
            signal.stop_loss = current_price * 0.99
            signal.take_profit = current_price * (1 + signal.expected_return / 100)

    async def _filter_and_rank_signals(self, signals: List[Signal], market_data: MarketData) -> List[Signal]:
        """Filter and rank signals."""
        # Filter by minimum strength and confidence
        filtered_signals = [
            signal for signal in signals
            if signal.strength.value >= self.criteria.min_strength
            and signal.confidence >= self.criteria.min_confidence
        ]

        # Rank signals by quality score
        ranked_signals = sorted(
            filtered_signals,
            key=lambda s: (s.strength.value * 0.4 + s.confidence * 0.3 + s.win_probability * 0.3),
            reverse=True
        )

        # Limit to top signals per symbol
        top_signals = []
        symbol_counts = {}
        max_signals_per_symbol = 3

        for signal in ranked_signals:
            symbol_count = symbol_counts.get(signal.symbol, 0)
            if symbol_count < max_signals_per_symbol:
                top_signals.append(signal)
                symbol_counts[signal.symbol] = symbol_count + 1

        return top_signals

    def _evaluate_volume_confirmation(self, signal: Signal, market_data: MarketData) -> float:
        """Evaluate volume confirmation for signal."""
        if not market_data.ohlcv_data:
            return 0.5

        # Simple volume analysis - compare recent volume to average
        recent_volume = market_data.ohlcv_data[-1].volume
        avg_volume = statistics.mean([ohlcv.volume for ohlcv in market_data.ohlcv_data[-10:]])

        if avg_volume > 0:
            volume_ratio = recent_volume / avg_volume
            return min(1.0, volume_ratio / 2.0)  # Normalize to 0-1

        return 0.5

    def _evaluate_multiple_confirmations(self, signal: Signal) -> float:
        """Evaluate multiple confirmations for signal."""
        confirmation_count = len([s for s in signal.sources if s.confidence > 0.6])

        if confirmation_count >= self.criteria.min_confirmation_count:
            return 1.0
        elif confirmation_count >= 1:
            return 0.5
        else:
            return 0.0

    def _evaluate_market_conditions(self, signal: Signal, market_data: MarketData) -> float:
        """Evaluate market conditions for signal."""
        # Simple market condition evaluation
        conditions_score = 0.5

        # Check data freshness
        if market_data.age_seconds < 60:
            conditions_score += 0.3
        elif market_data.age_seconds < 300:
            conditions_score += 0.1

        # Check data quality
        conditions_score += market_data.quality_score * 0.2

        return min(1.0, conditions_score)

    def _get_historical_win_rate(self, signal_type: SignalType) -> float:
        """Get historical win rate for signal type."""
        # In a real implementation, this would query historical performance data
        # For now, return default values
        default_win_rates = {
            SignalType.STRONG_BUY: 0.75,
            SignalType.BUY: 0.65,
            SignalType.MODERATE_BUY: 0.60,
            SignalType.HOLD: 0.50,
            SignalType.SELL: 0.45,
            SignalType.STRONG_SELL: 0.40
        }
        return default_win_rates.get(signal_type, 0.50)

    def _get_market_condition_adjustment(self, market_data: MarketData) -> float:
        """Get market condition adjustment for win rate."""
        # Simple adjustment based on data quality and freshness
        adjustment = 0.0

        if market_data.quality_score > 0.8:
            adjustment += 0.05

        if market_data.age_seconds < 60:
            adjustment += 0.05

        return adjustment

    def _generate_cache_key(self, signal: Signal, market_data: MarketData) -> str:
        """Generate cache key for evaluation."""
        return f"{signal.id}_{market_data.timestamp}_{signal.symbol}"

    def _get_cached_evaluation(self, cache_key: str) -> Optional[EvaluationResult]:
        """Get cached evaluation result."""
        if cache_key in self.evaluation_cache:
            cache_entry = self.evaluation_cache[cache_key]
            if datetime.now().timestamp() - cache_entry["timestamp"] < self.cache_ttl:
                return cache_entry["result"]
            else:
                del self.evaluation_cache[cache_key]
        return None

    def _cache_evaluation(self, cache_key: str, result: EvaluationResult):
        """Cache evaluation result."""
        self.evaluation_cache[cache_key] = {
            "timestamp": datetime.now().timestamp(),
            "result": result
        }

    async def get_metrics(self) -> Dict[str, Any]:
        """Get evaluator metrics."""
        return {
            "total_evaluations": self.total_evaluations,
            "average_evaluation_time": self.average_evaluation_time,
            "approval_rate": self.approval_rate,
            "cache_size": len(self.evaluation_cache),
            "min_strength": self.criteria.min_strength,
            "min_confidence": self.criteria.min_confidence
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on signal evaluator."""
        return {
            "status": "healthy",
            "metrics": await self.get_metrics(),
            "cache_status": "normal" if len(self.evaluation_cache) < 1000 else "warning",
            "win_rate_calculator_status": "operational"
        }