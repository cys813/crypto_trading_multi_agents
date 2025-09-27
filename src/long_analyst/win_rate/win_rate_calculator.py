"""
Win Rate Calculator - Main win rate calculation engine.

This class orchestrates historical matching, probability calculation,
risk assessment, and dynamic adjustment for accurate win rate prediction.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import json

from ..models.signal import Signal, SignalType
from ..models.market_data import MarketData
from ..utils.performance_monitor import PerformanceMonitor
from .win_rate_config import WinRateConfig, ModelConfig, FeatureConfig
from .historical_matcher import HistoricalMatcher, HistoricalCase
from .feature_extractor import FeatureExtractor, FeatureVector
from .probability_model import ProbabilityModel
from .risk_assessor import RiskAssessor
from .dynamic_adjuster import DynamicAdjuster


@dataclass
class WinRateResult:
    """Result of win rate calculation."""
    signal: Signal
    win_rate: float
    confidence: float  # Confidence in the win rate prediction
    risk_score: float  # 0.0 to 1.0, higher is riskier
    expected_return: float  # Expected return percentage
    max_drawdown: float  # Expected maximum drawdown percentage
    position_size_recommendation: float  # Recommended position size (0.0 to 1.0)
    time_horizon: str  # Expected holding period
    success_probability: float  # Probability of success
    confidence_interval: Optional[tuple] = None  # (lower_bound, upper_bound)
    similar_cases: List[HistoricalCase] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}


class WinRateCalculator:
    """
    Advanced win rate calculation engine for long trading signals.

    This calculator uses historical matching, probability models, risk assessment,
    and dynamic adjustment to provide accurate win rate predictions.
    """

    def __init__(self, config: WinRateConfig):
        """Initialize the win rate calculator."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()

        # Initialize components
        self.matcher = HistoricalMatcher(
            max_cases=config.max_historical_cases,
            similarity_threshold=config.similarity_threshold
        )
        self.feature_extractor = FeatureExtractor(FeatureConfig())
        self.probability_model = ProbabilityModel(ModelConfig())
        self.risk_assessor = RiskAssessor(config)
        self.dynamic_adjuster = DynamicAdjuster(config)

        # Thread pool for concurrent processing
        self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_calculations)

        # Calculation cache
        self.calculation_cache: Dict[str, WinRateResult] = {}
        self.cache_ttl = config.cache_ttl_seconds

        # Performance metrics
        self.total_calculations = 0
        self.average_calculation_time = 0.0
        self.prediction_accuracy = 0.0
        self.cache_hits = 0
        self.cache_misses = 0

        # Model state
        self.model_performance_history = []
        self.last_model_update = datetime.now()

        self.logger.info("Win rate calculator initialized")

    async def calculate_winrate(self, signal: Signal, market_data: MarketData) -> WinRateResult:
        """
        Calculate win rate for a trading signal.

        Args:
            signal: Trading signal to evaluate
            market_data: Current market data

        Returns:
            Win rate calculation result
        """
        start_time = datetime.now()

        try:
            # Check cache first
            cache_key = self._generate_cache_key(signal, market_data)
            cached_result = self._get_cached_result(cache_key)

            if cached_result:
                self.cache_hits += 1
                self.logger.debug(f"Cache hit for signal {signal.id[:8]}")
                return cached_result

            self.cache_misses += 1

            # Extract features from signal and market data
            feature_vector = await self.feature_extractor.extract_features(signal, market_data)

            # Find similar historical cases
            similar_cases = await self.matcher.find_similar_cases(signal, feature_vector)

            # Calculate probability using multiple methods
            probability_result = await self.probability_model.calculate_probability(
                similar_cases, feature_vector
            )

            # Assess risk
            risk_assessment = await self.risk_assessor.assess_signal_risk(
                signal, market_data, feature_vector, similar_cases
            )

            # Calculate final win rate with dynamic adjustments
            adjusted_win_rate = await self.dynamic_adjuster.adjust_win_rate(
                probability_result.win_rate,
                signal,
                market_data,
                feature_vector,
                similar_cases
            )

            # Generate position size recommendation
            position_size = self._calculate_position_size_recommendation(
                adjusted_win_rate,
                risk_assessment.risk_score,
                signal,
                market_data
            )

            # Generate recommendations
            recommendations, risk_factors = self._generate_recommendations(
                adjusted_win_rate,
                risk_assessment.risk_score,
                signal,
                similar_cases
            )

            # Calculate confidence intervals
            confidence_interval = None
            if self.config.include_confidence_intervals:
                confidence_interval = self._calculate_confidence_interval(
                    probability_result,
                    similar_cases
                )

            # Create result
            result = WinRateResult(
                signal=signal,
                win_rate=adjusted_win_rate,
                confidence=probability_result.confidence,
                risk_score=risk_assessment.risk_score,
                expected_return=risk_assessment.expected_return,
                max_drawdown=risk_assessment.max_drawdown,
                position_size_recommendation=position_size,
                time_horizon=self._determine_time_horizon(signal, similar_cases),
                success_probability=adjusted_win_rate,
                confidence_interval=confidence_interval,
                similar_cases=similar_cases,
                risk_factors=risk_factors,
                recommendations=recommendations,
                metadata={
                    'calculation_time': datetime.now().isoformat(),
                    'signal_id': signal.id,
                    'symbol': signal.symbol,
                    'method_used': probability_result.method,
                    'similar_cases_count': len(similar_cases),
                    'feature_vector_size': len(feature_vector.technical_features) + len(feature_vector.market_features),
                    'risk_factors_count': len(risk_factors)
                }
            )

            # Cache the result
            self._cache_result(cache_key, result)

            # Update metrics
            self._update_metrics(result, start_time)

            self.logger.info(f"Win rate calculation completed for {signal.symbol}: "
                           f"{adjusted_win_rate:.1%} win rate")

            return result

        except Exception as e:
            self.logger.error(f"Error calculating win rate for {signal.symbol}: {e}")
            calculation_time = (datetime.now() - start_time).total_seconds()

            return WinRateResult(
                signal=signal,
                win_rate=0.5,
                confidence=0.3,
                risk_score=0.8,
                expected_return=0.0,
                max_drawdown=10.0,
                position_size_recommendation=0.1,
                time_horizon="unknown",
                success_probability=0.5,
                metadata={
                    'error': str(e),
                    'calculation_time_ms': calculation_time * 1000
                }
            )

    async def batch_calculate_winrates(self, signals: List[Signal],
                                     market_data_dict: Dict[str, MarketData]) -> List[WinRateResult]:
        """
        Calculate win rates for multiple signals.

        Args:
            signals: List of signals to evaluate
            market_data_dict: Dictionary mapping symbols to market data

        Returns:
            List of win rate results
        """
        tasks = []

        for signal in signals:
            market_data = market_data_dict.get(signal.symbol)
            if market_data:
                task = self.calculate_winrate(signal, market_data)
                tasks.append(task)

        # Execute tasks concurrently
        if self.config.parallel_processing and tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            win_rate_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Error in batch calculation for signal {i}: {result}")
                elif result:
                    win_rate_results.append(result)
        else:
            win_rate_results = []

        return win_rate_results

    async def update_model(self, feedback_data: List[Dict[str, Any]]) -> bool:
        """
        Update the win rate model with new feedback data.

        Args:
            feedback_data: List of feedback data entries

        Returns:
            True if update was successful
        """
        try:
            if not self.config.enable_dynamic_adjustment:
                return False

            # Update historical matcher with new cases
            new_cases = []
            for feedback in feedback_data:
                if self._validate_feedback(feedback):
                    historical_case = self._feedback_to_historical_case(feedback)
                    new_cases.append(historical_case)

            if new_cases:
                await self.matcher.add_historical_cases(new_cases)

            # Update probability model
            await self.probability_model.update_model(feedback_data)

            # Update dynamic adjuster
            await self.dynamic_adjuster.update_parameters(feedback_data)

            # Update performance metrics
            self._update_model_performance(feedback_data)

            self.last_model_update = datetime.now()
            self.logger.info(f"Model updated with {len(new_cases)} new cases")

            return True

        except Exception as e:
            self.logger.error(f"Error updating model: {e}")
            return False

    def _calculate_position_size_recommendation(self, win_rate: float, risk_score: float,
                                              signal: Signal, market_data: MarketData) -> float:
        """Calculate recommended position size."""
        # Base position size on win rate and risk
        base_size = win_rate * (1.0 - risk_score)

        # Adjust based on signal strength
        strength_multiplier = signal.strength.value * 0.5 + 0.5  # 0.5 to 1.0

        # Adjust based on confidence
        confidence_multiplier = signal.confidence * 0.5 + 0.5  # 0.5 to 1.0

        # Calculate final position size
        position_size = base_size * strength_multiplier * confidence_multiplier

        # Apply risk limits
        max_position = 1.0 - (risk_score * 0.5)  # Reduce max size for high risk
        position_size = min(position_size, max_position)

        # Ensure minimum position size for valid signals
        if position_size > 0 and win_rate > 0.6:
            position_size = max(position_size, 0.05)  # Minimum 5%

        return max(0.0, min(1.0, position_size))

    def _determine_time_horizon(self, signal: Signal, similar_cases: List[HistoricalCase]) -> str:
        """Determine expected holding period."""
        if not similar_cases:
            # Default based on signal type
            if signal.signal_type in [SignalType.STRONG_BUY, SignalType.STRONG_SELL]:
                return "medium_term"  # 1-4 weeks
            else:
                return "short_term"  # 1-7 days

        # Use average holding period from similar cases
        holding_periods = [case.holding_period_hours for case in similar_cases if case.holding_period_hours]
        if holding_periods:
            avg_holding_hours = np.mean(holding_periods)

            if avg_holding_hours < 24:
                return "intraday"
            elif avg_holding_hours < 168:  # 1 week
                return "short_term"
            elif avg_holding_hours < 720:  # 1 month
                return "medium_term"
            else:
                return "long_term"

        return "medium_term"

    def _generate_recommendations(self, win_rate: float, risk_score: float,
                                signal: Signal, similar_cases: List[HistoricalCase]) -> Tuple[List[str], List[str]]:
        """Generate recommendations and identify risk factors."""
        recommendations = []
        risk_factors = []

        # Win rate based recommendations
        if win_rate >= 0.8:
            recommendations.append("High probability trade - consider full position size")
        elif win_rate >= 0.7:
            recommendations.append("Good probability trade - consider larger position")
        elif win_rate >= 0.6:
            recommendations.append("Moderate probability - use standard position sizing")
        else:
            recommendations.append("Low probability - consider reducing position size or skipping")

        # Risk based recommendations
        if risk_score >= 0.7:
            risk_factors.append("High risk level detected")
            recommendations.append("Use tight stop-loss and reduce position size")
        elif risk_score >= 0.5:
            risk_factors.append("Moderate risk level")
            recommendations.append("Use standard risk management")
        else:
            recommendations.append("Low risk level - can be more aggressive")

        # Signal strength recommendations
        if signal.strength.value >= 0.8:
            recommendations.append("Strong signal with high conviction")
        elif signal.strength.value <= 0.4:
            risk_factors.append("Weak signal strength")

        # Historical performance recommendations
        if similar_cases:
            avg_return = np.mean([case.actual_return for case in similar_cases if case.actual_return is not None])
            if avg_return > 5.0:
                recommendations.append(f"Similar historical cases showed good returns (avg: {avg_return:.1f}%)")
            elif avg_return < 0:
                risk_factors.append("Similar historical cases showed poor performance")

        # Volume and liquidity recommendations
        if hasattr(signal, 'key_indicators') and 'volume_ratio' in signal.key_indicators:
            volume_ratio = signal.key_indicators['volume_ratio']
            if volume_ratio < 1.0:
                risk_factors.append("Low volume confirmation")
                recommendations.append("Wait for better volume confirmation")

        return recommendations, risk_factors

    def _calculate_confidence_interval(self, probability_result, similar_cases: List[HistoricalCase]) -> Optional[tuple]:
        """Calculate confidence interval for win rate prediction."""
        try:
            if len(similar_cases) < 5:
                return None

            # Calculate standard deviation from similar cases
            outcomes = [1 if case.outcome == "profit" else 0 for case in similar_cases if case.outcome is not None]
            if len(outcomes) < 5:
                return None

            mean_win_rate = np.mean(outcomes)
            std_win_rate = np.std(outcomes)

            # Calculate confidence interval
            import scipy.stats as stats
            confidence_level = self.config.confidence_interval
            margin_of_error = stats.t.ppf((1 + confidence_level) / 2, len(outcomes) - 1) * (std_win_rate / np.sqrt(len(outcomes)))

            lower_bound = max(0.0, mean_win_rate - margin_of_error)
            upper_bound = min(1.0, mean_win_rate + margin_of_error)

            return (lower_bound, upper_bound)

        except Exception as e:
            self.logger.error(f"Error calculating confidence interval: {e}")
            return None

    def _validate_feedback(self, feedback: Dict[str, Any]) -> bool:
        """Validate feedback data."""
        required_fields = ['signal_id', 'outcome', 'actual_return', 'holding_period_hours']
        return all(field in feedback for field in required_fields)

    def _feedback_to_historical_case(self, feedback: Dict[str, Any]) -> HistoricalCase:
        """Convert feedback data to historical case."""
        return HistoricalCase(
            signal_id=feedback['signal_id'],
            symbol=feedback.get('symbol', 'unknown'),
            signal_type=feedback.get('signal_type', SignalType.BUY),
            entry_price=feedback.get('entry_price', 0.0),
            exit_price=feedback.get('exit_price', 0.0),
            outcome=feedback['outcome'],
            actual_return=feedback['actual_return'],
            holding_period_hours=feedback['holding_period_hours'],
            market_conditions=feedback.get('market_conditions', {}),
            timestamp=feedback.get('timestamp', datetime.now().timestamp()),
            features=feedback.get('features', {})
        )

    def _update_model_performance(self, feedback_data: List[Dict[str, Any]]):
        """Update model performance metrics."""
        if not feedback_data:
            return

        # Calculate prediction accuracy
        correct_predictions = 0
        total_predictions = 0

        for feedback in feedback_data:
            if 'predicted_win_rate' in feedback and 'outcome' in feedback:
                predicted_win_rate = feedback['predicted_win_rate']
                actual_outcome = 1 if feedback['outcome'] == 'profit' else 0

                # Check if prediction was directionally correct
                if (predicted_win_rate >= 0.5 and actual_outcome == 1) or \
                   (predicted_win_rate < 0.5 and actual_outcome == 0):
                    correct_predictions += 1

                total_predictions += 1

        if total_predictions > 0:
            accuracy = correct_predictions / total_predictions
            self.model_performance_history.append({
                'timestamp': datetime.now().isoformat(),
                'accuracy': accuracy,
                'samples': total_predictions
            })

            # Keep only recent performance history
            if len(self.model_performance_history) > 100:
                self.model_performance_history = self.model_performance_history[-100:]

            self.prediction_accuracy = accuracy

    def _generate_cache_key(self, signal: Signal, market_data: MarketData) -> str:
        """Generate cache key for win rate calculation."""
        import hashlib
        key_data = f"{signal.id}_{signal.symbol}_{signal.timestamp}_{market_data.timestamp}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cached_result(self, cache_key: str) -> Optional[WinRateResult]:
        """Get cached win rate result."""
        if cache_key in self.calculation_cache:
            cache_entry = self.calculation_cache[cache_key]
            if datetime.now().timestamp() - cache_entry.metadata['calculation_time'] < self.cache_ttl:
                return cache_entry
            else:
                del self.calculation_cache[cache_key]
        return None

    def _cache_result(self, cache_key: str, result: WinRateResult):
        """Cache win rate result."""
        if len(self.calculation_cache) < self.config.max_cache_size:
            self.calculation_cache[cache_key] = result

    def _update_metrics(self, result: WinRateResult, start_time: datetime):
        """Update calculation metrics."""
        self.total_calculations += 1

        # Update average calculation time
        calculation_time = (datetime.now() - start_time).total_seconds()
        self.average_calculation_time = (
            (self.average_calculation_time * (self.total_calculations - 1) + calculation_time) /
            self.total_calculations
        )

        # Record performance metrics
        self.performance_monitor.record_metric("calculation_time", calculation_time)
        self.performance_monitor.record_metric("win_rate_calculated", result.win_rate)

    async def get_statistics(self) -> Dict[str, Any]:
        """Get calculator statistics."""
        return {
            "total_calculations": self.total_calculations,
            "average_calculation_time_ms": self.average_calculation_time * 1000,
            "prediction_accuracy": self.prediction_accuracy,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0.0,
            "model_performance_history": self.model_performance_history[-10:] if self.model_performance_history else [],
            "last_model_update": self.last_model_update.isoformat(),
            "cache_size": len(self.calculation_cache),
            "uptime_seconds": datetime.now().timestamp() - self.performance_monitor.start_time
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on win rate calculator."""
        health_status = {
            "status": "healthy",
            "components": {},
            "statistics": await self.get_statistics()
        }

        try:
            # Check individual components
            components = [
                ("historical_matcher", self.matcher),
                ("probability_model", self.probability_model),
                ("risk_assessor", self.risk_assessor),
                ("dynamic_adjuster", self.dynamic_adjuster)
            ]

            for name, component in components:
                if hasattr(component, "health_check"):
                    component_health = await component.health_check()
                    health_status["components"][name] = component_health
                    if component_health.get("status") != "healthy":
                        health_status["status"] = "degraded"

            # Check cache health
            cache_size = len(self.calculation_cache)
            health_status["components"]["cache"] = {
                "status": "healthy" if cache_size < self.config.max_cache_size * 0.8 else "warning",
                "size": cache_size,
                "max_size": self.config.max_cache_size,
                "hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0.0
            }

        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)

        return health_status

    async def save_model_state(self, filepath: str) -> bool:
        """Save model state to file."""
        try:
            if not self.config.save_model_state:
                return False

            state = {
                "config": self.config.__dict__,
                "statistics": await self.get_statistics(),
                "model_performance_history": self.model_performance_history,
                "last_model_update": self.last_model_update.isoformat(),
                "timestamp": datetime.now().isoformat()
            }

            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2, default=str)

            self.logger.info(f"Model state saved to {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving model state: {e}")
            return False

    async def load_model_state(self, filepath: str) -> bool:
        """Load model state from file."""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)

            # Load performance history
            self.model_performance_history = state.get("model_performance_history", [])
            self.last_model_update = datetime.fromisoformat(state["last_model_update"])

            self.logger.info(f"Model state loaded from {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Error loading model state: {e}")
            return False

    async def shutdown(self):
        """Shutdown the win rate calculator."""
        self.logger.info("Shutting down win rate calculator")

        # Shutdown thread pool
        self.executor.shutdown(wait=True)

        # Clear cache
        self.calculation_cache.clear()

        self.logger.info("Win rate calculator shutdown complete")