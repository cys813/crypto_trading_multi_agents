"""
Support and Resistance Indicators for Long Analyst Agent.

This module provides advanced support and resistance level detection,
including dynamic levels, Fibonacci retracements, and pattern recognition.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import time
import pandas as pd
import numpy as np
from scipy import signal
from scipy.stats import linregress

from .indicator_engine import IndicatorCalculatorBase, IndicatorType, IndicatorCategory, IndicatorResult
from ..utils.indicators import IndicatorCalculator


class LevelType(Enum):
    """Types of support/resistance levels."""
    SUPPORT = "support"
    RESISTANCE = "resistance"
    DYNAMIC = "dynamic"
    FIBONACCI = "fibonacci"
    PIVOT = "pivot"
    TRENDLINE = "trendline"


class PatternType(Enum):
    """Types of chart patterns."""
    HEAD_AND_SHOULDERS = "head_and_shoulders"
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    TRIANGLE = "triangle"
    WEDGE = "wedge"
    FLAG = "flag"
    PENNANT = "pennant"
    CUP_AND_HANDLE = "cup_and_handle"


class StrengthLevel(Enum):
    """Strength levels for support/resistance."""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


@dataclass
class SupportResistanceLevel:
    """Individual support/resistance level."""
    price: float
    level_type: LevelType
    strength: StrengthLevel
    touches: int
    first_seen: float
    last_seen: float
    confidence: float
    timeframe: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ChartPattern:
    """Chart pattern detection result."""
    pattern_type: PatternType
    pattern_direction: str  # "bullish", "bearish", "neutral"
    confidence: float
    start_time: float
    end_time: float
    price_levels: List[float]
    volume_confirmation: bool
    breakout_level: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}


class SupportResistanceCalculator(IndicatorCalculatorBase):
    """Advanced support and resistance calculator."""

    def __init__(self):
        """Initialize support/resistance calculator."""
        super().__init__("SupportResistance", IndicatorType.SUPPORT_RESISTANCE, IndicatorCategory.SECONDARY)
        self.calculator = IndicatorCalculator()

    async def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> IndicatorResult:
        """Calculate support and resistance levels."""
        start_time = time.time()

        try:
            # Set default parameters
            if parameters is None:
                parameters = self.get_default_parameters()

            lookback_period = parameters.get('lookback_period', 100)
            min_touches = parameters.get('min_touches', 2)
            price_threshold = parameters.get('price_threshold', 0.02)

            # Validate inputs
            if not self.validate_data(data):
                raise ValueError("Invalid input data")

            if not self.validate_parameters(parameters):
                raise ValueError("Invalid parameters")

            # Calculate various types of levels
            static_levels = self._find_static_levels(data, lookback_period, min_touches, price_threshold)
            dynamic_levels = self._calculate_dynamic_levels(data)
            fibonacci_levels = self._calculate_fibonacci_levels(data)
            pivot_levels = self._calculate_pivot_points(data)

            # Combine all levels
            all_levels = static_levels + dynamic_levels + fibonacci_levels + pivot_levels

            # Filter and rank levels by strength
            filtered_levels = self._filter_and_rank_levels(all_levels)

            # Calculate long signals based on levels
            long_signals = self._calculate_long_signals(data, filtered_levels)

            result = IndicatorResult(
                indicator_name=self.name,
                indicator_type=self.indicator_type,
                category=self.category,
                values={
                    'levels': filtered_levels,
                    'long_signals': long_signals,
                    'current_support': self._get_current_support(data, filtered_levels),
                    'current_resistance': self._get_current_resistance(data, filtered_levels),
                    'price_distance_to_support': self._calculate_distance_to_nearest_support(data, filtered_levels),
                    'price_distance_to_resistance': self._calculate_distance_to_nearest_resistance(data, filtered_levels)
                },
                parameters=parameters,
                timestamp=time.time(),
                calculation_time_ms=(time.time() - start_time) * 1000,
                data_points_used=len(data),
                quality_score=self._calculate_quality_score(data, filtered_levels),
                metadata={
                    'description': 'Advanced support and resistance level detection',
                    'total_levels_found': len(filtered_levels),
                    'strong_levels_count': len([l for l in filtered_levels if l.strength in [StrengthLevel.STRONG, StrengthLevel.VERY_STRONG]])
                }
            )

            return result

        except Exception as e:
            self.logger.error(f"Error calculating support/resistance levels: {e}")
            raise

    def get_default_parameters(self) -> Dict[str, Any]:
        """Get default parameters."""
        return {
            'lookback_period': 100,
            'min_touches': 2,
            'price_threshold': 0.02,  # 2% price threshold for level clustering
            'min_strength': StrengthLevel.MODERATE.value,
            'enable_dynamic_levels': True,
            'enable_fibonacci_levels': True,
            'enable_pivot_levels': True
        }

    def _find_static_levels(self, data: pd.DataFrame, lookback_period: int, min_touches: int, price_threshold: float) -> List[SupportResistanceLevel]:
        """Find static support and resistance levels."""
        levels = []
        recent_data = data.tail(lookback_period) if len(data) > lookback_period else data

        # Find local maxima (resistance) and minima (support)
        highs = self._find_local_maxima(recent_data['high'], window=5)
        lows = self._find_local_minima(recent_data['low'], window=5)

        # Cluster nearby levels
        resistance_clusters = self._cluster_levels(highs, price_threshold)
        support_clusters = self._cluster_levels(lows, price_threshold)

        # Create level objects for resistance
        for cluster_price, touches in resistance_clusters.items():
            if touches >= min_touches:
                level = SupportResistanceLevel(
                    price=cluster_price,
                    level_type=LevelType.RESISTANCE,
                    strength=self._calculate_level_strength(touches, len(recent_data)),
                    touches=touches,
                    first_seen=time.time() - lookback_period * 60,  # Approximate
                    last_seen=time.time(),
                    confidence=min(1.0, touches / min_touches),
                    timeframe="static"
                )
                levels.append(level)

        # Create level objects for support
        for cluster_price, touches in support_clusters.items():
            if touches >= min_touches:
                level = SupportResistanceLevel(
                    price=cluster_price,
                    level_type=LevelType.SUPPORT,
                    strength=self._calculate_level_strength(touches, len(recent_data)),
                    touches=touches,
                    first_seen=time.time() - lookback_period * 60,
                    last_seen=time.time(),
                    confidence=min(1.0, touches / min_touches),
                    timeframe="static"
                )
                levels.append(level)

        return levels

    def _calculate_dynamic_levels(self, data: pd.DataFrame) -> List[SupportResistanceLevel]:
        """Calculate dynamic support/resistance levels using moving averages."""
        levels = []

        # Calculate various moving averages
        ma_periods = [20, 50, 100, 200]
        current_price = data['close'].iloc[-1]

        for period in ma_periods:
            if len(data) >= period:
                ma = data['close'].rolling(window=period).mean().iloc[-1]

                # Determine if this MA acts as support or resistance
                if current_price > ma:
                    level_type = LevelType.SUPPORT
                else:
                    level_type = LevelType.RESISTANCE

                level = SupportResistanceLevel(
                    price=ma,
                    level_type=LevelType.DYNAMIC,
                    strength=StrengthLevel.STRONG if period >= 100 else StrengthLevel.MODERATE,
                    touches=period,  # Each data point is a "touch"
                    first_seen=time.time() - period * 60,
                    last_seen=time.time(),
                    confidence=0.8,
                    timeframe=f"MA_{period}",
                    metadata={'period': period}
                )
                levels.append(level)

        return levels

    def _calculate_fibonacci_levels(self, data: pd.DataFrame) -> List[SupportResistanceLevel]:
        """Calculate Fibonacci retracement levels."""
        levels = []
        lookback = 100  # Look back 100 periods

        if len(data) < lookback:
            return levels

        recent_data = data.tail(lookback)
        high = recent_data['high'].max()
        low = recent_data['low'].min()

        # Fibonacci levels
        fib_ratios = [0.236, 0.382, 0.5, 0.618, 0.786]
        price_range = high - low

        for ratio in fib_ratios:
            price_level = high - (price_range * ratio)

            # Determine level type based on current price
            current_price = data['close'].iloc[-1]
            level_type = LevelType.SUPPORT if current_price > price_level else LevelType.RESISTANCE

            level = SupportResistanceLevel(
                price=price_level,
                level_type=LevelType.FIBONACCI,
                strength=StrengthLevel.MODERATE,
                touches=1,  # Fibonacci levels are theoretical
                first_seen=time.time() - lookback * 60,
                last_seen=time.time(),
                confidence=0.7,
                timeframe="fibonacci",
                metadata={'ratio': ratio, 'high': high, 'low': low}
            )
            levels.append(level)

        return levels

    def _calculate_pivot_points(self, data: pd.DataFrame) -> List[SupportResistanceLevel]:
        """Calculate pivot points and support/resistance levels."""
        levels = []

        # Use last completed candle
        if len(data) < 2:
            return levels

        last_candle = data.iloc[-2]
        high = last_candle['high']
        low = last_candle['low']
        close = last_candle['close']

        # Calculate pivot point
        pivot = (high + low + close) / 3

        # Calculate support and resistance levels
        r1 = (2 * pivot) - low
        s1 = (2 * pivot) - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)

        current_price = data['close'].iloc[-1]

        # Create level objects
        for price, level_type, name in [
            (r1, LevelType.RESISTANCE, "R1"),
            (r2, LevelType.RESISTANCE, "R2"),
            (pivot, LevelType.PIVOT, "Pivot"),
            (s1, LevelType.SUPPORT, "S1"),
            (s2, LevelType.SUPPORT, "S2")
        ]:
            level = SupportResistanceLevel(
                price=price,
                level_type=level_type,
                strength=StrengthLevel.MODERATE,
                touches=1,
                first_seen=time.time() - 300,  # 5 minutes ago
                last_seen=time.time(),
                confidence=0.6,
                timeframe="pivot",
                metadata={'pivot_name': name}
            )
            levels.append(level)

        return levels

    def _find_local_maxima(self, prices: pd.Series, window: int) -> List[float]:
        """Find local maxima in price series."""
        maxima = []

        for i in range(window, len(prices) - window):
            window_data = prices.iloc[i-window:i+window+1]
            if prices.iloc[i] == window_data.max():
                maxima.append(prices.iloc[i])

        return maxima

    def _find_local_minima(self, prices: pd.Series, window: int) -> List[float]:
        """Find local minima in price series."""
        minima = []

        for i in range(window, len(prices) - window):
            window_data = prices.iloc[i-window:i+window+1]
            if prices.iloc[i] == window_data.min():
                minima.append(prices.iloc[i])

        return minima

    def _cluster_levels(self, levels: List[float], threshold: float) -> Dict[float, int]:
        """Cluster nearby price levels."""
        if not levels:
            return {}

        # Sort levels
        sorted_levels = sorted(levels)
        clusters = {}

        current_cluster = [sorted_levels[0]]
        cluster_center = sorted_levels[0]

        for level in sorted_levels[1:]:
            # Check if this level belongs to current cluster
            if abs(level - cluster_center) / cluster_center <= threshold:
                current_cluster.append(level)
            else:
                # Finalize current cluster
                avg_price = sum(current_cluster) / len(current_cluster)
                clusters[avg_price] = len(current_cluster)

                # Start new cluster
                current_cluster = [level]
                cluster_center = level

        # Add final cluster
        if current_cluster:
            avg_price = sum(current_cluster) / len(current_cluster)
            clusters[avg_price] = len(current_cluster)

        return clusters

    def _calculate_level_strength(self, touches: int, data_points: int) -> StrengthLevel:
        """Calculate strength level based on touches and data points."""
        touch_ratio = touches / data_points

        if touch_ratio >= 0.1:
            return StrengthLevel.VERY_STRONG
        elif touch_ratio >= 0.05:
            return StrengthLevel.STRONG
        elif touch_ratio >= 0.02:
            return StrengthLevel.MODERATE
        else:
            return StrengthLevel.WEAK

    def _filter_and_rank_levels(self, levels: List[SupportResistanceLevel]) -> List[SupportResistanceLevel]:
        """Filter and rank levels by strength and relevance."""
        # Filter by minimum strength
        min_strength = StrengthLevel.MODERATE
        filtered = [level for level in levels if level.strength.value >= min_strength.value]

        # Sort by strength (descending) and then by confidence (descending)
        filtered.sort(key=lambda x: (x.strength.value, x.confidence), reverse=True)

        # Limit to top 20 levels
        return filtered[:20]

    def _calculate_long_signals(self, data: pd.DataFrame, levels: List[SupportResistanceLevel]) -> pd.Series:
        """Calculate long signals based on support/resistance levels."""
        signals = pd.Series(0.0, index=data.index)
        current_price = data['close'].iloc[-1]

        # Find nearest support and resistance
        support_levels = [level for level in levels if level.level_type == LevelType.SUPPORT]
        resistance_levels = [level for level in levels if level.level_type == LevelType.RESISTANCE]

        if support_levels:
            nearest_support = min(support_levels, key=lambda x: abs(x.price - current_price))
            distance_to_support = (current_price - nearest_support.price) / current_price

            # Strong signal if price is near strong support
            if distance_to_support <= 0.02:  # Within 2% of support
                if nearest_support.strength in [StrengthLevel.STRONG, StrengthLevel.VERY_STRONG]:
                    signals.iloc[-1] = 0.9
                else:
                    signals.iloc[-1] = 0.7

            # Moderate signal if price is approaching support
            elif distance_to_support <= 0.05:  # Within 5% of support
                signals.iloc[-1] = 0.5

        # Check for resistance breakout potential
        if resistance_levels:
            nearest_resistance = min(resistance_levels, key=lambda x: abs(x.price - current_price))
            distance_to_resistance = (nearest_resistance.price - current_price) / current_price

            # If price is approaching resistance with strong momentum, breakout potential
            if distance_to_resistance <= 0.03 and nearest_resistance.strength.value <= 2:  # Weak/moderate resistance
                signals.iloc[-1] = max(signals.iloc[-1], 0.6)

        return signals

    def _get_current_support(self, data: pd.DataFrame, levels: List[SupportResistanceLevel]) -> Optional[float]:
        """Get current nearest support level."""
        current_price = data['close'].iloc[-1]
        support_levels = [level for level in levels if level.level_type == LevelType.SUPPORT and level.price <= current_price]

        if support_levels:
            return max(support_levels, key=lambda x: x.price).price
        return None

    def _get_current_resistance(self, data: pd.DataFrame, levels: List[SupportResistanceLevel]) -> Optional[float]:
        """Get current nearest resistance level."""
        current_price = data['close'].iloc[-1]
        resistance_levels = [level for level in levels if level.level_type == LevelType.RESISTANCE and level.price >= current_price]

        if resistance_levels:
            return min(resistance_levels, key=lambda x: x.price).price
        return None

    def _calculate_distance_to_nearest_support(self, data: pd.DataFrame, levels: List[SupportResistanceLevel]) -> float:
        """Calculate percentage distance to nearest support."""
        current_price = data['close'].iloc[-1]
        support_levels = [level for level in levels if level.level_type == LevelType.SUPPORT]

        if support_levels:
            nearest_support = max(support_levels, key=lambda x: x.price)
            return (current_price - nearest_support.price) / current_price
        return 0.0

    def _calculate_distance_to_nearest_resistance(self, data: pd.DataFrame, levels: List[SupportResistanceLevel]) -> float:
        """Calculate percentage distance to nearest resistance."""
        current_price = data['close'].iloc[-1]
        resistance_levels = [level for level in levels if level.level_type == LevelType.RESISTANCE]

        if resistance_levels:
            nearest_resistance = min(resistance_levels, key=lambda x: x.price)
            return (nearest_resistance.price - current_price) / current_price
        return 0.0

    def _calculate_quality_score(self, data: pd.DataFrame, levels: List[SupportResistanceLevel]) -> float:
        """Calculate quality score for support/resistance calculation."""
        if not levels:
            return 0.0

        # Base score on number and quality of levels found
        level_count_score = min(1.0, len(levels) / 10.0)

        # Score based on strength distribution
        strong_levels = [level for level in levels if level.strength in [StrengthLevel.STRONG, StrengthLevel.VERY_STRONG]]
        strength_score = len(strong_levels) / len(levels) if levels else 0.0

        # Score based on confidence
        avg_confidence = sum(level.confidence for level in levels) / len(levels) if levels else 0.0

        return (level_count_score + strength_score + avg_confidence) / 3.0


class PatternRecognitionCalculator(IndicatorCalculatorBase):
    """Chart pattern recognition calculator."""

    def __init__(self):
        """Initialize pattern recognition calculator."""
        super().__init__("PatternRecognition", IndicatorType.PATTERN, IndicatorCategory.CONFIRMATION)
        self.logger = logging.getLogger(__name__)

    async def calculate(self, data: pd.DataFrame, parameters: Dict[str, Any] = None) -> IndicatorResult:
        """Recognize chart patterns."""
        start_time = time.time()

        try:
            # Set default parameters
            if parameters is None:
                parameters = self.get_default_parameters()

            min_pattern_length = parameters.get('min_pattern_length', 20)
            max_pattern_length = parameters.get('max_pattern_length', 100)

            # Validate inputs
            if not self.validate_data(data):
                raise ValueError("Invalid input data")

            if not self.validate_parameters(parameters):
                raise ValueError("Invalid parameters")

            # Detect various patterns
            patterns = []
            patterns.extend(self._detect_head_and_shoulders(data, min_pattern_length, max_pattern_length))
            patterns.extend(self._detect_double_tops_bottoms(data, min_pattern_length, max_pattern_length))
            patterns.extend(self._detect_triangles(data, min_pattern_length, max_pattern_length))

            # Filter patterns by confidence
            high_confidence_patterns = [p for p in patterns if p.confidence >= 0.7]

            # Calculate long signals based on patterns
            long_signals = self._calculate_long_signals(data, high_confidence_patterns)

            result = IndicatorResult(
                indicator_name=self.name,
                indicator_type=self.indicator_type,
                category=self.category,
                values={
                    'patterns': high_confidence_patterns,
                    'long_signals': long_signals,
                    'bullish_patterns': len([p for p in high_confidence_patterns if p.pattern_direction == 'bullish']),
                    'bearish_patterns': len([p for p in high_confidence_patterns if p.pattern_direction == 'bearish']),
                    'highest_confidence_pattern': max(high_confidence_patterns, key=lambda x: x.confidence) if high_confidence_patterns else None
                },
                parameters=parameters,
                timestamp=time.time(),
                calculation_time_ms=(time.time() - start_time) * 1000,
                data_points_used=len(data),
                quality_score=self._calculate_quality_score(high_confidence_patterns),
                metadata={
                    'description': 'Chart pattern recognition for long signal confirmation',
                    'total_patterns_detected': len(patterns),
                    'high_confidence_patterns': len(high_confidence_patterns)
                }
            )

            return result

        except Exception as e:
            self.logger.error(f"Error detecting patterns: {e}")
            raise

    def get_default_parameters(self) -> Dict[str, Any]:
        """Get default parameters."""
        return {
            'min_pattern_length': 20,
            'max_pattern_length': 100,
            'min_confidence': 0.7,
            'enable_volume_confirmation': True
        }

    def _detect_head_and_shoulders(self, data: pd.DataFrame, min_length: int, max_length: int) -> List[ChartPattern]:
        """Detect head and shoulders patterns."""
        patterns = []

        # Look for patterns in different window sizes
        for window_size in range(min_length, min(max_length, len(data)), 10):
            if len(data) < window_size:
                continue

            # Get recent data window
            window_data = data.tail(window_size)

            # Find peaks and troughs
            peaks = self._find_peaks(window_data['high'])
            troughs = self._find_troughs(window_data['low'])

            if len(peaks) >= 3 and len(troughs) >= 2:
                # Check for head and shoulders pattern
                # Left shoulder, head, right shoulder structure
                for i in range(len(peaks) - 2):
                    left_shoulder = peaks[i]
                    head = peaks[i + 1]
                    right_shoulder = peaks[i + 2]

                    # Head should be higher than shoulders
                    if (head['price'] > left_shoulder['price'] and
                        head['price'] > right_shoulder['price'] and
                        abs(left_shoulder['price'] - right_shoulder['price']) / left_shoulder['price'] < 0.05):  # Shoulders roughly equal

                        # Calculate pattern confidence
                        confidence = self._calculate_hs_confidence(window_data, left_shoulder, head, right_shoulder)

                        if confidence >= 0.7:
                            pattern = ChartPattern(
                                pattern_type=PatternType.HEAD_AND_SHOULDERS,
                                pattern_direction="bearish",
                                confidence=confidence,
                                start_time=left_shoulder['time'],
                                end_time=right_shoulder['time'],
                                price_levels=[left_shoulder['price'], head['price'], right_shoulder['price']],
                                volume_confirmation=self._check_volume_confirmation(window_data, left_shoulder['index'], right_shoulder['index']),
                                breakout_level=min(left_shoulder['price'], right_shoulder['price']),
                                target_price=head['price'] - (head['price'] - min(left_shoulder['price'], right_shoulder['price'])),
                                stop_loss=head['price'] + (head['price'] - min(left_shoulder['price'], right_shoulder['price'])) * 0.1,
                                metadata={'left_shoulder': left_shoulder, 'head': head, 'right_shoulder': right_shoulder}
                            )
                            patterns.append(pattern)

        return patterns

    def _detect_double_tops_bottoms(self, data: pd.DataFrame, min_length: int, max_length: int) -> List[ChartPattern]:
        """Detect double top and double bottom patterns."""
        patterns = []

        for window_size in range(min_length, min(max_length, len(data)), 10):
            if len(data) < window_size:
                continue

            window_data = data.tail(window_size)
            peaks = self._find_peaks(window_data['high'])
            troughs = self._find_troughs(window_data['low'])

            # Double top detection
            if len(peaks) >= 2:
                for i in range(len(peaks) - 1):
                    peak1 = peaks[i]
                    peak2 = peaks[i + 1]

                    # Check if peaks are at similar level
                    if (abs(peak1['price'] - peak2['price']) / peak1['price'] < 0.02 and
                        peak2['index'] - peak1['index'] >= 5):  # Minimum distance between peaks

                        confidence = self._calculate_double_pattern_confidence(window_data, peak1, peak2)

                        if confidence >= 0.7:
                            pattern = ChartPattern(
                                pattern_type=PatternType.DOUBLE_TOP,
                                pattern_direction="bearish",
                                confidence=confidence,
                                start_time=peak1['time'],
                                end_time=peak2['time'],
                                price_levels=[peak1['price'], peak2['price']],
                                volume_confirmation=self._check_volume_confirmation(window_data, peak1['index'], peak2['index']),
                                breakout_level=min(peak1['price'], peak2['price']),
                                target_price=min(peak1['price'], peak2['price']) - (max(peak1['price'], peak2['price']) - min(peak1['price'], peak2['price'])) * 0.1,
                                stop_loss=max(peak1['price'], peak2['price']) + (max(peak1['price'], peak2['price']) - min(peak1['price'], peak2['price'])) * 0.05,
                                metadata={'peak1': peak1, 'peak2': peak2}
                            )
                            patterns.append(pattern)

            # Double bottom detection (similar logic for troughs)
            if len(troughs) >= 2:
                for i in range(len(troughs) - 1):
                    trough1 = troughs[i]
                    trough2 = troughs[i + 1]

                    if (abs(trough1['price'] - trough2['price']) / trough1['price'] < 0.02 and
                        trough2['index'] - trough1['index'] >= 5):

                        confidence = self._calculate_double_pattern_confidence(window_data, trough1, trough2)

                        if confidence >= 0.7:
                            pattern = ChartPattern(
                                pattern_type=PatternType.DOUBLE_BOTTOM,
                                pattern_direction="bullish",  # Bullish signal
                                confidence=confidence,
                                start_time=trough1['time'],
                                end_time=trough2['time'],
                                price_levels=[trough1['price'], trough2['price']],
                                volume_confirmation=self._check_volume_confirmation(window_data, trough1['index'], trough2['index']),
                                breakout_level=max(trough1['price'], trough2['price']),
                                target_price=max(trough1['price'], trough2['price']) + (max(trough1['price'], trough2['price']) - min(trough1['price'], trough2['price'])) * 0.1,
                                stop_loss=min(trough1['price'], trough2['price']) - (max(trough1['price'], trough2['price']) - min(trough1['price'], trough2['price'])) * 0.05,
                                metadata={'trough1': trough1, 'trough2': trough2}
                            )
                            patterns.append(pattern)

        return patterns

    def _detect_triangles(self, data: pd.DataFrame, min_length: int, max_length: int) -> List[ChartPattern]:
        """Detect triangle patterns (ascending, descending, symmetrical)."""
        patterns = []

        for window_size in range(min_length, min(max_length, len(data)), 10):
            if len(data) < window_size:
                continue

            window_data = data.tail(window_size)

            # Find trend lines
            upper_trendline = self._find_trendline(window_data['high'], descending=True)
            lower_trendline = self._find_trendline(window_data['low'], ascending=True)

            if upper_trendline and lower_trendline:
                # Check for convergence (triangle formation)
                convergence_rate = abs(upper_trendline['slope'] - lower_trendline['slope'])

                if convergence_rate > 0.001:  # Significant convergence
                    # Determine triangle type
                    if upper_trendline['slope'] < 0 and lower_trendline['slope'] > 0:
                        triangle_type = "symmetrical"
                        direction = "neutral"
                    elif upper_trendline['slope'] < 0 and lower_trendline['slope'] < 0:
                        triangle_type = "descending"
                        direction = "bearish"
                    elif upper_trendline['slope'] > 0 and lower_trendline['slope'] > 0:
                        triangle_type = "ascending"
                        direction = "bullish"
                    else:
                        continue

                    confidence = self._calculate_triangle_confidence(window_data, upper_trendline, lower_trendline)

                    if confidence >= 0.7:
                        pattern = ChartPattern(
                            pattern_type=PatternType.TRIANGLE,
                            pattern_direction=direction,
                            confidence=confidence,
                            start_time=window_data.index[0],
                            end_time=window_data.index[-1],
                            price_levels=[upper_trendline['intercept'], lower_trendline['intercept']],
                            volume_confirmation=self._check_volume_convergence(window_data),
                            breakout_level=None,  # Will be determined by breakout direction
                            target_price=None,
                            stop_loss=None,
                            metadata={
                                'triangle_type': triangle_type,
                                'upper_trendline': upper_trendline,
                                'lower_trendline': lower_trendline
                            }
                        )
                        patterns.append(pattern)

        return patterns

    def _find_peaks(self, prices: pd.Series) -> List[Dict[str, Any]]:
        """Find significant peaks in price series."""
        peaks = []

        # Use scipy signal processing to find peaks
        peak_indices, _ = signal.find_peaks(prices, distance=5, prominence=0.02)

        for idx in peak_indices:
            peaks.append({
                'index': idx,
                'price': prices.iloc[idx],
                'time': prices.index[idx]
            })

        return peaks

    def _find_troughs(self, prices: pd.Series) -> List[Dict[str, Any]]:
        """Find significant troughs in price series."""
        troughs = []

        # Use scipy signal processing to find troughs (inverted peaks)
        trough_indices, _ = signal.find_peaks(-prices, distance=5, prominence=0.02)

        for idx in trough_indices:
            troughs.append({
                'index': idx,
                'price': prices.iloc[idx],
                'time': prices.index[idx]
            })

        return troughs

    def _find_trendline(self, prices: pd.Series, ascending: bool = False, descending: bool = False) -> Optional[Dict[str, Any]]:
        """Find trend line for price series."""
        if len(prices) < 5:
            return None

        # Use linear regression to find trend
        x = np.arange(len(prices))
        y = prices.values

        slope, intercept, r_value, p_value, std_err = linregress(x, y)

        # Check if trend matches requested direction
        if ascending and slope <= 0:
            return None
        if descending and slope >= 0:
            return None

        # Check if trend is significant
        if abs(r_value) < 0.7:  # Weak correlation
            return None

        return {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_value ** 2,
            'strength': abs(r_value)
        }

    def _calculate_hs_confidence(self, data: pd.DataFrame, left_shoulder: Dict, head: Dict, right_shoulder: Dict) -> float:
        """Calculate confidence for head and shoulders pattern."""
        confidence = 0.5  # Base confidence

        # Head should be significantly higher than shoulders
        head_shoulder_diff = head['price'] - max(left_shoulder['price'], right_shoulder['price'])
        if head_shoulder_diff / head['price'] > 0.05:
            confidence += 0.2

        # Shoulders should be roughly equal
        shoulder_diff = abs(left_shoulder['price'] - right_shoulder['price'])
        if shoulder_diff / left_shoulder['price'] < 0.03:
            confidence += 0.2

        # Volume should decrease on right shoulder
        if self._check_volume_decrease(data, right_shoulder['index']):
            confidence += 0.1

        return min(1.0, confidence)

    def _calculate_double_pattern_confidence(self, data: pd.DataFrame, point1: Dict, point2: Dict) -> float:
        """Calculate confidence for double top/bottom pattern."""
        confidence = 0.5  # Base confidence

        # Points should be at similar levels
        price_diff = abs(point1['price'] - point2['price'])
        if price_diff / point1['price'] < 0.01:
            confidence += 0.3
        elif price_diff / point1['price'] < 0.02:
            confidence += 0.2

        # Minimum distance between points
        if point2['index'] - point1['index'] >= 10:
            confidence += 0.2

        return min(1.0, confidence)

    def _calculate_triangle_confidence(self, data: pd.DataFrame, upper_trendline: Dict, lower_trendline: Dict) -> float:
        """Calculate confidence for triangle pattern."""
        confidence = 0.5  # Base confidence

        # Strong trend line correlation
        if upper_trendline['r_squared'] > 0.8:
            confidence += 0.2
        if lower_trendline['r_squared'] > 0.8:
            confidence += 0.2

        # Convergence rate
        convergence_rate = abs(upper_trendline['slope'] - lower_trendline['slope'])
        if convergence_rate > 0.002:
            confidence += 0.1

        return min(1.0, confidence)

    def _check_volume_confirmation(self, data: pd.DataFrame, start_idx: int, end_idx: int) -> bool:
        """Check if volume confirms the pattern."""
        if 'volume' not in data.columns:
            return False

        # Simple volume confirmation check
        pattern_volume = data['volume'].iloc[start_idx:end_idx+1]
        avg_volume = data['volume'].mean()

        # Volume should be significant
        return pattern_volume.mean() > avg_volume * 0.8

    def _check_volume_convergence(self, data: pd.DataFrame) -> bool:
        """Check if volume shows convergence pattern."""
        if 'volume' not in data.columns:
            return False

        # Check if volume decreases as pattern develops
        volume_trend = np.polyfit(range(len(data)), data['volume'], 1)[0]
        return volume_trend < 0

    def _check_volume_decrease(self, data: pd.DataFrame, end_idx: int) -> bool:
        """Check if volume decreases toward pattern end."""
        if 'volume' not in data.columns or end_idx < 10:
            return False

        recent_volume = data['volume'].iloc[end_idx-10:end_idx+1]
        earlier_volume = data['volume'].iloc[end_idx-20:end_idx-10]

        return recent_volume.mean() < earlier_volume.mean() * 0.8

    def _calculate_long_signals(self, data: pd.DataFrame, patterns: List[ChartPattern]) -> pd.Series:
        """Calculate long signals based on detected patterns."""
        signals = pd.Series(0.0, index=data.index)

        for pattern in patterns:
            if pattern.pattern_direction == "bullish":
                # Strong signal for bullish patterns
                if pattern.confidence >= 0.8:
                    signals.iloc[-1] = max(signals.iloc[-1], 0.9)
                elif pattern.confidence >= 0.7:
                    signals.iloc[-1] = max(signals.iloc[-1], 0.7)

            elif pattern.pattern_direction == "neutral" and pattern.pattern_type == PatternType.TRIANGLE:
                # Moderate signal for neutral triangles (could break either way)
                if pattern.confidence >= 0.8:
                    signals.iloc[-1] = max(signals.iloc[-1], 0.6)

        return signals

    def _calculate_quality_score(self, patterns: List[ChartPattern]) -> float:
        """Calculate quality score for pattern recognition."""
        if not patterns:
            return 0.0

        # Base score on number of high-confidence patterns
        pattern_count_score = min(1.0, len(patterns) / 3.0)

        # Average confidence of detected patterns
        avg_confidence = sum(p.confidence for p in patterns) / len(patterns)

        # Bonus for bullish patterns (good for long signals)
        bullish_ratio = len([p for p in patterns if p.pattern_direction == "bullish"]) / len(patterns)

        return (pattern_count_score + avg_confidence + bullish_ratio) / 3.0