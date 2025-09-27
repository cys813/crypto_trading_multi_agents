"""
Technical Indicators Calculation Engine for Long Analyst Agent.

This module provides a high-performance technical indicator calculation engine
optimized for long signal detection with caching and parallel processing.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union, Type
from dataclasses import dataclass, asdict
from enum import Enum
import time
import hashlib
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from abc import ABC, abstractmethod
import redis.asyncio as redis
from functools import lru_cache

from ..models.market_data import MarketData, Timeframe
from ..utils.performance_monitor import PerformanceMonitor
from ..utils.indicators import IndicatorCalculator
from .support_resistance import SupportResistanceCalculator, PatternRecognitionCalculator


class IndicatorType(Enum):
    """Types of technical indicators."""
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    SUPPORT_RESISTANCE = "support_resistance"
    PATTERN = "pattern"


class IndicatorCategory(Enum):
    """Categories of indicators for long signal optimization."""
    PRIMARY = "primary"      # Core indicators for long signals
    SECONDARY = "secondary"  # Supporting indicators
    CONFIRMATION = "confirmation"  # Confirmation indicators
    FILTER = "filter"        # Filter indicators


@dataclass
class IndicatorConfig:
    """Configuration for technical indicators."""

    # Performance settings
    max_concurrent_calculations: int = 50
    calculation_timeout_ms: int = 200
    cache_ttl_seconds: int = 300
    enable_parallel_processing: bool = True

    # Indicator settings
    rsi_long_threshold: tuple = (30, 60)  # Optimal RSI range for long entries
    rsi_oversold_threshold: int = 30
    rsi_overbought_threshold: int = 70
    macd_fast_period: int = 12
    macd_slow_period: int = 26
    macd_signal_period: int = 9
    bollinger_period: int = 20
    bollinger_std_dev: float = 2.0

    # Quality settings
    min_data_points: int = 50
    max_missing_data_ratio: float = 0.05
    enable_data_validation: bool = True

    # Caching settings
    enable_redis_cache: bool = True
    redis_url: str = "redis://localhost:6379"
    enable_memory_cache: bool = True
    memory_cache_size: int = 1000


@dataclass
class IndicatorResult:
    """Result of indicator calculation."""

    indicator_name: str
    indicator_type: IndicatorType
    category: IndicatorCategory
    values: Union[pd.Series, Dict[str, pd.Series], Dict[str, float]]
    parameters: Dict[str, Any]
    timestamp: float
    calculation_time_ms: float
    data_points_used: int
    quality_score: float
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}


class IndicatorCache:
    """High-performance caching system for indicator calculations."""

    def __init__(self, config: IndicatorConfig):
        """Initialize the indicator cache."""
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize Redis cache if enabled
        self.redis_client = None
        if config.enable_redis_cache:
            try:
                self.redis_client = redis.from_url(config.redis_url)
                self.logger.info("Redis cache initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Redis cache: {e}")

        # Initialize memory cache
        self.memory_cache = {}
        self.memory_cache_size = config.memory_cache_size

        # Cache statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_errors = 0

    def _generate_cache_key(self, indicator_name: str, data_hash: str, parameters: Dict[str, Any]) -> str:
        """Generate cache key for indicator calculation."""
        param_str = json.dumps(sorted(parameters.items()), sort_keys=True)
        key_data = f"{indicator_name}:{data_hash}:{param_str}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_data_hash(self, data: pd.DataFrame) -> str:
        """Generate hash for data to detect changes."""
        # Use last few rows and data shape for hash
        sample_size = min(10, len(data))
        sample_data = data.tail(sample_size).to_string()
        shape_info = f"{data.shape[0]}_{data.shape[1]}"
        hash_input = f"{shape_info}:{sample_data}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    async def get(self, indicator_name: str, data: pd.DataFrame, parameters: Dict[str, Any]) -> Optional[IndicatorResult]:
        """Get cached indicator result."""
        try:
            data_hash = self._get_data_hash(data)
            cache_key = self._generate_cache_key(indicator_name, data_hash, parameters)

            # Check memory cache first
            if cache_key in self.memory_cache:
                cached_result = self.memory_cache[cache_key]
                # Check if still valid based on TTL
                if time.time() - cached_result.timestamp < self.config.cache_ttl_seconds:
                    self.cache_hits += 1
                    return cached_result
                else:
                    # Remove expired entry
                    del self.memory_cache[cache_key]

            # Check Redis cache
            if self.redis_client:
                try:
                    cached_data = await self.redis_client.get(cache_key)
                    if cached_data:
                        result_dict = json.loads(cached_data)
                        # Reconstruct IndicatorResult
                        result = IndicatorResult(**result_dict)
                        self.cache_hits += 1

                        # Update memory cache
                        if len(self.memory_cache) < self.memory_cache_size:
                            self.memory_cache[cache_key] = result

                        return result
                except Exception as e:
                    self.logger.warning(f"Redis cache error: {e}")
                    self.cache_errors += 1

            self.cache_misses += 1
            return None

        except Exception as e:
            self.logger.error(f"Cache retrieval error: {e}")
            self.cache_errors += 1
            return None

    async def set(self, result: IndicatorResult, data: pd.DataFrame, parameters: Dict[str, Any]) -> bool:
        """Set cached indicator result."""
        try:
            data_hash = self._get_data_hash(data)
            cache_key = self._generate_cache_key(result.indicator_name, data_hash, parameters)

            # Store in memory cache
            if len(self.memory_cache) < self.memory_cache_size:
                self.memory_cache[cache_key] = result

            # Store in Redis cache
            if self.redis_client:
                try:
                    result_dict = asdict(result)
                    await self.redis_client.setex(
                        cache_key,
                        self.config.cache_ttl_seconds,
                        json.dumps(result_dict, default=str)
                    )
                    return True
                except Exception as e:
                    self.logger.warning(f"Redis cache set error: {e}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Cache storage error: {e}")
            return False

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0.0

        return {
            "memory_cache_size": len(self.memory_cache),
            "memory_cache_max_size": self.memory_cache_size,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_errors": self.cache_errors,
            "hit_rate": hit_rate,
            "redis_enabled": self.redis_client is not None
        }


class IndicatorCalculatorBase(ABC):
    """Base class for indicator calculators."""

    def __init__(self, name: str, indicator_type: IndicatorType, category: IndicatorCategory):
        """Initialize indicator calculator."""
        self.name = name
        self.indicator_type = indicator_type
        self.category = category
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    async def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> IndicatorResult:
        """Calculate indicator values."""
        pass

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate calculation parameters."""
        return True

    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate input data."""
        return len(data) > 0 and not data.empty

    def get_default_parameters(self) -> Dict[str, Any]:
        """Get default parameters for the indicator."""
        return {}


class RSICalculator(IndicatorCalculatorBase):
    """RSI calculator optimized for long signals."""

    def __init__(self):
        """Initialize RSI calculator."""
        super().__init__("RSI", IndicatorType.MOMENTUM, IndicatorCategory.PRIMARY)
        self.calculator = IndicatorCalculator()

    async def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> IndicatorResult:
        """Calculate RSI values."""
        start_time = time.time()

        try:
            # Set default parameters
            if parameters is None:
                parameters = self.get_default_parameters()

            period = parameters.get('period', 14)

            # Validate inputs
            if not self.validate_data(data):
                raise ValueError("Invalid input data")

            if not self.validate_parameters(parameters):
                raise ValueError("Invalid parameters")

            # Calculate RSI
            rsi_values = self.calculator.rsi(data['close'], period)

            # Calculate long signal strength based on RSI optimization
            long_signals = self._calculate_long_signals(rsi_values)

            result = IndicatorResult(
                indicator_name=self.name,
                indicator_type=self.indicator_type,
                category=self.category,
                values={
                    'rsi': rsi_values,
                    'long_signals': long_signals,
                    'current_rsi': rsi_values.iloc[-1] if len(rsi_values) > 0 else None
                },
                parameters=parameters,
                timestamp=time.time(),
                calculation_time_ms=(time.time() - start_time) * 1000,
                data_points_used=len(data),
                quality_score=self._calculate_quality_score(data, rsi_values),
                metadata={
                    'description': 'RSI optimized for long signal detection',
                    'long_optimization': True,
                    'optimal_range': (30, 60)
                }
            )

            return result

        except Exception as e:
            self.logger.error(f"Error calculating RSI: {e}")
            raise

    def get_default_parameters(self) -> Dict[str, Any]:
        """Get default RSI parameters."""
        return {
            'period': 14,
            'long_optimization': True
        }

    def _calculate_long_signals(self, rsi_values: pd.Series) -> pd.Series:
        """Calculate long signals based on RSI optimization."""
        signals = pd.Series(0.0, index=rsi_values.index)

        # Optimal range for long entries (30-60)
        optimal_mask = (rsi_values >= 30) & (rsi_values <= 60)
        signals[optimal_mask] = 0.8

        # Oversold condition (strong buy signal)
        oversold_mask = (rsi_values < 30) & (rsi_values >= 20)
        signals[oversold_mask] = 0.9

        # Extremely oversold (very strong buy signal)
        extreme_oversold = rsi_values < 20
        signals[extreme_oversold] = 1.0

        # Neutral to slightly bullish
        neutral_mask = (rsi_values > 60) & (rsi_values <= 70)
        signals[neutral_mask] = 0.4

        return signals

    def _calculate_quality_score(self, data: pd.DataFrame, rsi_values: pd.Series) -> float:
        """Calculate quality score for RSI calculation."""
        # Based on data completeness and RSI distribution
        completeness = 1.0 - (rsi_values.isna().sum() / len(rsi_values))

        # Check if RSI values are in expected range
        valid_range = ((rsi_values >= 0) & (rsi_values <= 100)).sum() / len(rsi_values)

        return (completeness + valid_range) / 2


class MACDCalculator(IndicatorCalculatorBase):
    """MACD calculator optimized for trend following."""

    def __init__(self):
        """Initialize MACD calculator."""
        super().__init__("MACD", IndicatorType.TREND, IndicatorCategory.PRIMARY)
        self.calculator = IndicatorCalculator()

    async def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> IndicatorResult:
        """Calculate MACD values."""
        start_time = time.time()

        try:
            # Set default parameters
            if parameters is None:
                parameters = self.get_default_parameters()

            fast = parameters.get('fast', 12)
            slow = parameters.get('slow', 26)
            signal = parameters.get('signal', 9)

            # Validate inputs
            if not self.validate_data(data):
                raise ValueError("Invalid input data")

            if not self.validate_parameters(parameters):
                raise ValueError("Invalid parameters")

            # Calculate MACD
            macd_data = self.calculator.macd(data['close'], fast, slow, signal)

            # Calculate long signals
            long_signals = self._calculate_long_signals(macd_data)

            result = IndicatorResult(
                indicator_name=self.name,
                indicator_type=self.indicator_type,
                category=self.category,
                values={
                    **macd_data,
                    'long_signals': long_signals,
                    'current_macd': macd_data['macd'].iloc[-1] if len(macd_data['macd']) > 0 else None,
                    'current_signal': macd_data['signal'].iloc[-1] if len(macd_data['signal']) > 0 else None,
                    'current_histogram': macd_data['histogram'].iloc[-1] if len(macd_data['histogram']) > 0 else None
                },
                parameters=parameters,
                timestamp=time.time(),
                calculation_time_ms=(time.time() - start_time) * 1000,
                data_points_used=len(data),
                quality_score=self._calculate_quality_score(data, macd_data),
                metadata={
                    'description': 'MACD optimized for long trend following',
                    'trend_strength': self._calculate_trend_strength(macd_data)
                }
            )

            return result

        except Exception as e:
            self.logger.error(f"Error calculating MACD: {e}")
            raise

    def get_default_parameters(self) -> Dict[str, Any]:
        """Get default MACD parameters."""
        return {
            'fast': 12,
            'slow': 26,
            'signal': 9
        }

    def _calculate_long_signals(self, macd_data: Dict[str, pd.Series]) -> pd.Series:
        """Calculate long signals based on MACD."""
        signals = pd.Series(0.0, index=macd_data['macd'].index)

        # Bullish crossover (MACD crosses above signal)
        macd_above_signal = macd_data['macd'] > macd_data['signal']
        crossover = macd_above_signal & ~macd_above_signal.shift(1).fillna(False)
        signals[crossover] = 1.0

        # MACD above zero line (bullish trend)
        positive_macd = macd_data['macd'] > 0
        signals[positive_macd] = 0.6

        # Increasing histogram (strengthening bullish momentum)
        increasing_histogram = macd_data['histogram'] > macd_data['histogram'].shift(1)
        signals[increasing_histogram] = 0.7

        return signals

    def _calculate_trend_strength(self, macd_data: Dict[str, pd.Series]) -> float:
        """Calculate trend strength based on MACD."""
        try:
            # Use histogram magnitude as trend strength indicator
            current_histogram = macd_data['histogram'].iloc[-1]
            max_histogram = macd_data['histogram'].abs().max()

            if max_histogram > 0:
                strength = abs(current_histogram) / max_histogram
                return min(1.0, strength)
            return 0.0
        except Exception:
            return 0.0

    def _calculate_quality_score(self, data: pd.DataFrame, macd_data: Dict[str, pd.Series]) -> float:
        """Calculate quality score for MACD calculation."""
        # Based on data completeness and signal quality
        completeness = 1.0 - (macd_data['macd'].isna().sum() / len(macd_data['macd']))

        # Check for valid MACD values
        valid_values = (~macd_data['macd'].isna()).sum() / len(macd_data['macd'])

        return (completeness + valid_values) / 2


class BollingerBandsCalculator(IndicatorCalculatorBase):
    """Bollinger Bands calculator for volatility analysis."""

    def __init__(self):
        """Initialize Bollinger Bands calculator."""
        super().__init__("BollingerBands", IndicatorType.VOLATILITY, IndicatorCategory.SECONDARY)
        self.calculator = IndicatorCalculator()

    async def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> IndicatorResult:
        """Calculate Bollinger Bands."""
        start_time = time.time()

        try:
            # Set default parameters
            if parameters is None:
                parameters = self.get_default_parameters()

            period = parameters.get('period', 20)
            std_dev = parameters.get('std_dev', 2.0)

            # Validate inputs
            if not self.validate_data(data):
                raise ValueError("Invalid input data")

            if not self.validate_parameters(parameters):
                raise ValueError("Invalid parameters")

            # Calculate Bollinger Bands
            bb_data = self.calculator.bollinger_bands(data['close'], period, std_dev)

            # Calculate long signals
            long_signals = self._calculate_long_signals(data['close'], bb_data)

            result = IndicatorResult(
                indicator_name=self.name,
                indicator_type=self.indicator_type,
                category=self.category,
                values={
                    **bb_data,
                    'long_signals': long_signals,
                    'current_position': self._get_current_position(data['close'], bb_data)
                },
                parameters=parameters,
                timestamp=time.time(),
                calculation_time_ms=(time.time() - start_time) * 1000,
                data_points_used=len(data),
                quality_score=self._calculate_quality_score(data, bb_data),
                metadata={
                    'description': 'Bollinger Bands for volatility-based long signals',
                    'bandwidth': self._calculate_bandwidth(bb_data)
                }
            )

            return result

        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands: {e}")
            raise

    def get_default_parameters(self) -> Dict[str, Any]:
        """Get default Bollinger Bands parameters."""
        return {
            'period': 20,
            'std_dev': 2.0
        }

    def _calculate_long_signals(self, close_prices: pd.Series, bb_data: Dict[str, pd.Series]) -> pd.Series:
        """Calculate long signals based on Bollinger Bands."""
        signals = pd.Series(0.0, index=close_prices.index)

        # Price near or below lower band (oversold)
        near_lower_band = close_prices <= bb_data['lower'] * 1.05  # Within 5% of lower band
        signals[near_lower_band] = 0.8

        # Price below lower band (very oversold)
        below_lower_band = close_prices < bb_data['lower']
        signals[below_lower_band] = 1.0

        # Price between lower band and middle band (good entry zone)
        in_lower_half = (close_prices > bb_data['lower']) & (close_prices <= bb_data['middle'])
        signals[in_lower_half] = 0.6

        return signals

    def _get_current_position(self, close_prices: pd.Series, bb_data: Dict[str, pd.Series]) -> str:
        """Get current price position relative to bands."""
        try:
            current_price = close_prices.iloc[-1]
            current_upper = bb_data['upper'].iloc[-1]
            current_lower = bb_data['lower'].iloc[-1]
            current_middle = bb_data['middle'].iloc[-1]

            if current_price > current_upper:
                return "above_upper"
            elif current_price > current_middle:
                return "upper_half"
            elif current_price > current_lower:
                return "lower_half"
            else:
                return "below_lower"
        except Exception:
            return "unknown"

    def _calculate_bandwidth(self, bb_data: Dict[str, pd.Series]) -> float:
        """Calculate Bollinger Band bandwidth."""
        try:
            bandwidth = (bb_data['upper'] - bb_data['lower']) / bb_data['middle']
            return bandwidth.iloc[-1] if len(bandwidth) > 0 else 0.0
        except Exception:
            return 0.0

    def _calculate_quality_score(self, data: pd.DataFrame, bb_data: Dict[str, pd.Series]) -> float:
        """Calculate quality score for Bollinger Bands calculation."""
        # Based on data completeness and band validity
        completeness = 1.0 - (bb_data['upper'].isna().sum() / len(bb_data['upper']))

        # Check for valid band values (upper > middle > lower)
        valid_bands = (bb_data['upper'] > bb_data['middle']) & (bb_data['middle'] > bb_data['lower'])
        valid_ratio = valid_bands.sum() / len(bb_data['upper'])

        return (completeness + valid_ratio) / 2


class IndicatorEngine:
    """
    High-performance technical indicators calculation engine.

    This engine provides optimized calculations for 50+ technical indicators
    specifically optimized for long signal detection in cryptocurrency trading.
    """

    def __init__(self, config: IndicatorConfig):
        """Initialize the indicator engine."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()

        # Initialize cache
        self.cache = IndicatorCache(config)

        # Initialize thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_calculations)

        # Initialize indicator calculators
        self.calculators = self._init_calculators()

        # Metrics
        self.total_calculations = 0
        self.total_calculation_time = 0.0
        self.average_calculation_time = 0.0
        self.cache_hits = 0
        self.cache_misses = 0

        self.logger.info("Indicator engine initialized")

    def _init_calculators(self) -> Dict[str, IndicatorCalculatorBase]:
        """Initialize all indicator calculators."""
        calculators = {
            # Primary indicators
            'rsi': RSICalculator(),
            'macd': MACDCalculator(),
            'bollinger_bands': BollingerBandsCalculator(),

            # Support and resistance indicators
            'support_resistance': SupportResistanceCalculator(),
            'pattern_recognition': PatternRecognitionCalculator(),
        }

        # Add more calculators in the future
        # calculators['stochastic'] = StochasticCalculator()
        # calculators['adx'] = ADXCalculator()
        # calculators['atr'] = ATRCalculator()
        # calculators['obv'] = OBVCalculator()

        return calculators

    async def calculate(self, indicator_name: str, data: pd.DataFrame,
                       parameters: Dict[str, Any] = None) -> Optional[IndicatorResult]:
        """
        Calculate a single indicator.

        Args:
            indicator_name: Name of the indicator
            data: Market data as DataFrame
            parameters: Calculation parameters

        Returns:
            Indicator result or None if calculation failed
        """
        start_time = time.time()

        try:
            # Check cache first
            cached_result = await self.cache.get(indicator_name, data, parameters or {})
            if cached_result:
                self.cache_hits += 1
                return cached_result

            # Get calculator
            calculator = self.calculators.get(indicator_name.lower())
            if not calculator:
                raise ValueError(f"Unknown indicator: {indicator_name}")

            # Validate data
            if not self._validate_data(data):
                raise ValueError("Invalid market data")

            # Calculate indicator
            result = await calculator.calculate(data, parameters)

            # Cache result
            await self.cache.set(result, data, parameters or {})

            # Update metrics
            self.total_calculations += 1
            calculation_time = (time.time() - start_time) * 1000
            self.total_calculation_time += calculation_time
            self.average_calculation_time = (
                self.total_calculation_time / self.total_calculations
            )

            self.cache_misses += 1

            # Record performance metrics
            self.performance_monitor.record_metric("calculation_time", calculation_time)
            self.performance_monitor.record_metric("indicator_calculated", indicator_name)

            return result

        except Exception as e:
            self.logger.error(f"Error calculating {indicator_name}: {e}")
            self.performance_monitor.record_error(f"indicator_calculation_error: {indicator_name}")
            return None

    async def batch_calculate(self, indicators: List[str], data: pd.DataFrame,
                            parameters: Dict[str, Dict[str, Any]] = None) -> Dict[str, IndicatorResult]:
        """
        Calculate multiple indicators in parallel.

        Args:
            indicators: List of indicator names
            data: Market data as DataFrame
            parameters: Parameters for each indicator

        Returns:
            Dictionary mapping indicator names to results
        """
        if parameters is None:
            parameters = {}

        # Create calculation tasks
        tasks = []
        for indicator in indicators:
            indicator_params = parameters.get(indicator)
            task = self.calculate(indicator, data, indicator_params)
            tasks.append(task)

        # Execute tasks concurrently
        if self.config.enable_parallel_processing:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            results = []
            for task in tasks:
                try:
                    result = await task
                    results.append(result)
                except Exception as e:
                    results.append(e)

        # Process results
        indicator_results = {}
        for i, result in enumerate(results):
            indicator_name = indicators[i]
            if isinstance(result, Exception):
                self.logger.error(f"Error in batch calculation for {indicator_name}: {result}")
                self.performance_monitor.record_error(f"batch_calculation_error: {indicator_name}")
            elif result is not None:
                indicator_results[indicator_name] = result

        return indicator_results

    async def calculate_long_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate comprehensive long signals using multiple indicators.

        Args:
            data: Market data as DataFrame

        Returns:
            Dictionary containing long signals and analysis
        """
        try:
            # Define key indicators for long signal detection
            long_indicators = ['rsi', 'macd', 'bollinger_bands', 'support_resistance', 'pattern_recognition']

            # Calculate indicators
            results = await self.batch_calculate(long_indicators, data)

            # Aggregate signals
            aggregated_signals = self._aggregate_long_signals(results)

            # Calculate overall signal strength
            overall_strength = self._calculate_overall_strength(aggregated_signals)

            # Generate detailed analysis
            detailed_analysis = self._generate_detailed_analysis(results, overall_strength)

            return {
                'signals': aggregated_signals,
                'overall_strength': overall_strength,
                'indicator_results': results,
                'recommendation': self._generate_recommendation(overall_strength),
                'detailed_analysis': detailed_analysis,
                'timestamp': time.time()
            }

        except Exception as e:
            self.logger.error(f"Error calculating long signals: {e}")
            return {
                'signals': {},
                'overall_strength': 0.0,
                'indicator_results': {},
                'recommendation': 'HOLD',
                'detailed_analysis': {'error': str(e)},
                'timestamp': time.time(),
                'error': str(e)
            }

    def _validate_data(self, data: pd.DataFrame) -> bool:
        """Validate market data for indicator calculation."""
        if data is None or data.empty:
            return False

        if len(data) < self.config.min_data_points:
            return False

        # Check for required columns
        required_columns = ['close']
        for col in required_columns:
            if col not in data.columns:
                return False

        # Check data quality
        missing_ratio = data.isnull().sum().sum() / (len(data) * len(data.columns))
        if missing_ratio > self.config.max_missing_data_ratio:
            return False

        return True

    def _aggregate_long_signals(self, results: Dict[str, IndicatorResult]) -> Dict[str, pd.Series]:
        """Aggregate long signals from multiple indicators."""
        aggregated = {}

        for indicator_name, result in results.items():
            if hasattr(result, 'values') and 'long_signals' in result.values:
                aggregated[indicator_name] = result.values['long_signals']

        return aggregated

    def _calculate_overall_strength(self, signals: Dict[str, pd.Series]) -> float:
        """Calculate overall long signal strength."""
        if not signals:
            return 0.0

        # Get current signal values
        current_signals = {}
        for indicator_name, signal_series in signals.items():
            if len(signal_series) > 0:
                current_signals[indicator_name] = signal_series.iloc[-1]

        if not current_signals:
            return 0.0

        # Weighted average based on indicator importance
        weights = {
            'rsi': 0.4,
            'macd': 0.4,
            'bollinger_bands': 0.2
        }

        weighted_sum = 0.0
        total_weight = 0.0

        for indicator_name, signal_value in current_signals.items():
            weight = weights.get(indicator_name, 0.1)
            weighted_sum += signal_value * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _generate_recommendation(self, strength: float) -> str:
        """Generate trading recommendation based on signal strength."""
        if strength >= 0.8:
            return "STRONG_BUY"
        elif strength >= 0.6:
            return "BUY"
        elif strength >= 0.4:
            return "WEAK_BUY"
        elif strength >= 0.2:
            return "HOLD"
        else:
            return "WAIT"

    def _generate_detailed_analysis(self, results: Dict[str, IndicatorResult], overall_strength: float) -> Dict[str, Any]:
        """Generate detailed analysis of indicator results."""
        analysis = {
            'overall_assessment': self._generate_recommendation(overall_strength),
            'confidence': overall_strength,
            'indicator_signals': {},
            'risk_factors': [],
            'opportunities': [],
            'technical_summary': ''
        }

        # Analyze each indicator
        for indicator_name, result in results.items():
            if result is None:
                continue

            signal_strength = 0.0
            indicator_analysis = {}

            if indicator_name == 'rsi' and 'current_rsi' in result.values:
                rsi_value = result.values['current_rsi']
                indicator_analysis['rsi_value'] = rsi_value
                if 30 <= rsi_value <= 60:
                    signal_strength = 0.8
                    analysis['opportunities'].append(f"RSI in optimal range ({rsi_value:.1f}) for long entry")
                elif rsi_value < 30:
                    signal_strength = 0.9
                    analysis['opportunities'].append(f"RSI oversold ({rsi_value:.1f}) - strong buy signal")

            elif indicator_name == 'macd' and 'current_macd' in result.values:
                macd_value = result.values['current_macd']
                signal_value = result.values['current_signal']
                indicator_analysis['macd_value'] = macd_value
                indicator_analysis['signal_value'] = signal_value

                if macd_value > signal_value:
                    signal_strength = 0.8
                    analysis['opportunities'].append("MACD bullish crossover detected")

            elif indicator_name == 'bollinger_bands' and 'current_position' in result.values:
                position = result.values['current_position']
                indicator_analysis['bb_position'] = position
                if position in ['lower_half', 'below_lower']:
                    signal_strength = 0.8
                    analysis['opportunities'].append(f"Price near lower Bollinger Band ({position})")

            elif indicator_name == 'support_resistance':
                if 'current_support' in result.values and result.values['current_support']:
                    support_level = result.values['current_support']
                    indicator_analysis['support_level'] = support_level
                    signal_strength = 0.7
                    analysis['opportunities'].append(f"Price approaching support level at {support_level:.2f}")

            elif indicator_name == 'pattern_recognition':
                bullish_patterns = result.values.get('bullish_patterns', 0)
                if bullish_patterns > 0:
                    signal_strength = 0.8
                    analysis['opportunities'].append(f"Detected {bullish_patterns} bullish chart patterns")

            analysis['indicator_signals'][indicator_name] = {
                'signal_strength': signal_strength,
                'analysis': indicator_analysis
            }

        # Generate technical summary
        if analysis['opportunities']:
            analysis['technical_summary'] = "Multiple bullish indicators detected. "
            if overall_strength >= 0.8:
                analysis['technical_summary'] += "Strong buy signal with high confidence."
            elif overall_strength >= 0.6:
                analysis['technical_summary'] += "Good buying opportunity with moderate risk."
            else:
                analysis['technical_summary'] += "Wait for stronger confirmation signals."
        else:
            analysis['technical_summary'] = "No clear long signals detected at this time."

        # Identify risk factors
        if overall_strength < 0.4:
            analysis['risk_factors'].append("Weak overall signal strength")

        return analysis

    async def get_available_indicators(self) -> List[str]:
        """Get list of available indicators."""
        return list(self.calculators.keys())

    async def get_metrics(self) -> Dict[str, Any]:
        """Get engine performance metrics."""
        cache_stats = await self.cache.get_cache_stats()

        return {
            "total_calculations": self.total_calculations,
            "average_calculation_time_ms": self.average_calculation_time,
            "cache_stats": cache_stats,
            "available_indicators": len(self.calculators),
            "uptime_seconds": time.time() - self.performance_monitor.start_time,
            "error_rate": self.performance_monitor.get_error_rate()
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the indicator engine."""
        health_status = {
            "status": "healthy",
            "components": {},
            "metrics": await self.get_metrics()
        }

        # Check cache health
        try:
            cache_stats = await self.cache.get_cache_stats()
            health_status["components"]["cache"] = {
                "status": "healthy",
                "stats": cache_stats
            }
        except Exception as e:
            health_status["components"]["cache"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"

        # Check calculator availability
        available_calculators = len(self.calculators)
        health_status["components"]["calculators"] = {
            "status": "healthy",
            "available": available_calculators
        }

        return health_status

    async def shutdown(self):
        """Shutdown the indicator engine."""
        self.logger.info("Shutting down indicator engine")

        # Shutdown thread pool
        self.executor.shutdown(wait=True)

        # Close Redis connection
        if self.cache.redis_client:
            await self.cache.redis_client.close()

        self.logger.info("Indicator engine shutdown complete")