"""
Pattern Detection Algorithms for Long Analyst Agent.

Advanced algorithms for detecting bottom patterns and reversal formations
including head and shoulders, double bottoms, and other bullish patterns.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np
from enum import Enum

from ..signal_detector import SignalDetector, DetectorConfig, DetectionResult
from ...models.signal import SignalType, SignalStrength
from ...models.market_data import MarketData


class PatternType(Enum):
    """Types of chart patterns."""
    HEAD_AND_SHOULDERS_BOTTOM = "head_and_shoulders_bottom"
    DOUBLE_BOTTOM = "double_bottom"
    TRIPLE_BOTTOM = "triple_bottom"
    ROUNDING_BOTTOM = "rounding_bottom"
    BULLISH_ENGULFING = "bullish_engulfing"
    HAMMER = "hammer"
    MORNING_STAR = "morning_star"
    BULL_FLAG = "bull_flag"


@dataclass
class PatternAnalysis:
    """Result of pattern analysis."""
    pattern_detected: bool
    pattern_type: PatternType
    confidence: float  # 0.0 to 1.0
    pattern_start: float
    pattern_end: float
    neckline_level: Optional[float] = None
    breakout_level: Optional[float] = None
    pattern_height: Optional[float] = None
    expected_move: Optional[float] = None
    volume_confirmation: bool = False
    is_completed: bool = False
    key_points: Dict[str, float] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.key_points is None:
            self.key_points = {}
        if self.metadata is None:
            self.metadata = {}


class PatternDetector(SignalDetector):
    """
    Advanced pattern detection algorithm for long trading opportunities.

    This detector identifies bottom patterns and reversal formations using
    sophisticated pattern recognition algorithms.
    """

    def __init__(self, config: DetectorConfig):
        """Initialize the pattern detector."""
        super().__init__(config)
        self.min_confidence = config.parameters.get('min_confidence', 0.8)
        self.lookback_periods = config.parameters.get('lookback_periods', 100)
        self.enable_neckline = config.parameters.get('enable_neckline', True)

    def get_required_indicators(self) -> List[str]:
        """Get required technical indicators."""
        return ['volume_profile', 'bollinger_bands', 'rsi', 'macd']

    async def detect(self, market_data: MarketData) -> List[DetectionResult]:
        """
        Detect pattern-based signals.

        Args:
            market_data: Market data to analyze

        Returns:
            List of detection results
        """
        try:
            # Convert market data to DataFrame
            df = self._market_data_to_dataframe(market_data)
            if df is None or len(df) < 30:
                return []

            # Analyze different types of patterns
            pattern_signals = []

            # Head and shoulders bottom detection
            hns_pattern = await self._detect_head_and_shoulders_bottom(df)
            if hns_pattern.pattern_detected and hns_pattern.confidence >= self.min_confidence:
                signal = self._generate_pattern_signal(hns_pattern, market_data)
                if signal:
                    pattern_signals.append(signal)

            # Double bottom detection
            double_bottom = await self._detect_double_bottom(df)
            if double_bottom.pattern_detected and double_bottom.confidence >= self.min_confidence:
                signal = self._generate_pattern_signal(double_bottom, market_data)
                if signal:
                    pattern_signals.append(signal)

            # Rounding bottom detection
            rounding_bottom = await self._detect_rounding_bottom(df)
            if rounding_bottom.pattern_detected and rounding_bottom.confidence >= self.min_confidence:
                signal = self._generate_pattern_signal(rounding_bottom, market_data)
                if signal:
                    pattern_signals.append(signal)

            # Candlestick patterns
            candlestick_patterns = await self._detect_candlestick_patterns(df)
            for pattern in candlestick_patterns:
                if pattern.confidence >= self.min_confidence:
                    signal = self._generate_pattern_signal(pattern, market_data)
                    if signal:
                        pattern_signals.append(signal)

            return pattern_signals

        except Exception as e:
            self.logger.error(f"Error in pattern detection: {e}")
            return []

    async def _detect_head_and_shoulders_bottom(self, df: pd.DataFrame) -> PatternAnalysis:
        """Detect head and shoulders bottom pattern."""
        try:
            if len(df) < 50:
                return PatternAnalysis(
                    pattern_detected=False,
                    pattern_type=PatternType.HEAD_AND_SHOULDERS_BOTTOM,
                    confidence=0.0,
                    pattern_start=0.0,
                    pattern_end=0.0
                )

            # Simplified H&S bottom detection
            # Look for: left shoulder -> head -> right shoulder structure with lower lows

            # Find potential pattern points
            lows = df['low'].rolling(window=5, center=True).min().dropna()
            highs = df['high'].rolling(window=5, center=True).max().dropna()

            if len(lows) < 30:
                return PatternAnalysis(
                    pattern_detected=False,
                    pattern_type=PatternType.HEAD_AND_SHOULDERS_BOTTOM,
                    confidence=0.0,
                    pattern_start=0.0,
                    pattern_end=0.0
                )

            # Find three major lows (shoulders and head)
            significant_lows = []
            for i in range(5, len(lows) - 5):
                if (lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i+1] and
                    lows.iloc[i] < lows.iloc[i-2] and lows.iloc[i] < lows.iloc[i+2] and
                    lows.iloc[i] < lows.iloc[i-3] and lows.iloc[i] < lows.iloc[i+3]):

                    significant_lows.append((i, lows.iloc[i]))

            if len(significant_lows) < 3:
                return PatternAnalysis(
                    pattern_detected=False,
                    pattern_type=PatternType.HEAD_AND_SHOULDERS_BOTTOM,
                    confidence=0.0,
                    pattern_start=0.0,
                    pattern_end=0.0
                )

            # Take the three most recent significant lows
            recent_lows = significant_lows[-3:]

            # Check H&S structure: head should be lowest, shoulders at similar levels
            left_shoulder_idx, left_shoulder_val = recent_lows[0]
            head_idx, head_val = recent_lows[1]
            right_shoulder_idx, right_shoulder_val = recent_lows[2]

            # Head should be lower than both shoulders
            if not (head_val < left_shoulder_val and head_val < right_shoulder_val):
                return PatternAnalysis(
                    pattern_detected=False,
                    pattern_type=PatternType.HEAD_AND_SHOULDERS_BOTTOM,
                    confidence=0.0,
                    pattern_start=0.0,
                    pattern_end=0.0
                )

            # Shoulders should be at similar levels (within 10%)
            shoulder_diff = abs(left_shoulder_val - right_shoulder_val) / left_shoulder_val
            if shoulder_diff > 0.1:
                return PatternAnalysis(
                    pattern_detected=False,
                    pattern_type=PatternType.HEAD_AND_SHOULDERS_BOTTOM,
                    confidence=0.0,
                    pattern_start=0.0,
                    pattern_end=0.0
                )

            # Find neckline (resistance between shoulders)
            shoulder_start_idx = min(left_shoulder_idx, right_shoulder_idx)
            shoulder_end_idx = max(left_shoulder_idx, right_shoulder_idx)

            # Get highs between shoulders
            pattern_highs = highs.iloc[shoulder_start_idx:shoulder_end_idx+1]
            neckline_level = pattern_highs.max()

            # Calculate pattern height
            pattern_height = neckline_level - head_val

            # Check for volume confirmation (decreasing volume into head, increasing on right shoulder)
            volume_confirmation = self._confirm_pattern_volume(df, [left_shoulder_idx, head_idx, right_shoulder_idx])

            # Check if pattern is completed (price near neckline)
            current_price = df['close'].iloc[-1]
            is_completed = abs(current_price - neckline_level) / neckline_level < 0.05  # 5% tolerance

            # Calculate confidence
            confidence = self._calculate_hs_confidence(
                recent_lows, shoulder_diff, volume_confirmation, is_completed
            )

            return PatternAnalysis(
                pattern_detected=True,
                pattern_type=PatternType.HEAD_AND_SHOULDERS_BOTTOM,
                confidence=confidence,
                pattern_start=df.index[left_shoulder_idx],
                pattern_end=df.index[right_shoulder_idx],
                neckline_level=neckline_level,
                breakout_level=neckline_level,
                pattern_height=pattern_height,
                expected_move=pattern_height,  # Measured move target
                volume_confirmation=volume_confirmation,
                is_completed=is_completed,
                key_points={
                    'left_shoulder': left_shoulder_val,
                    'head': head_val,
                    'right_shoulder': right_shoulder_val,
                    'neckline': neckline_level
                },
                metadata={
                    'structure_valid': True,
                    'shoulder_symmetry': 1.0 - shoulder_diff,
                    'pattern_duration': right_shoulder_idx - left_shoulder_idx
                }
            )

        except Exception as e:
            self.logger.error(f"Error detecting head and shoulders bottom: {e}")
            return PatternAnalysis(
                pattern_detected=False,
                pattern_type=PatternType.HEAD_AND_SHOULDERS_BOTTOM,
                confidence=0.0,
                pattern_start=0.0,
                pattern_end=0.0
            )

    async def _detect_double_bottom(self, df: pd.DataFrame) -> PatternAnalysis:
        """Detect double bottom pattern."""
        try:
            if len(df) < 40:
                return PatternAnalysis(
                    pattern_detected=False,
                    pattern_type=PatternType.DOUBLE_BOTTOM,
                    confidence=0.0,
                    pattern_start=0.0,
                    pattern_end=0.0
                )

            # Find significant lows
            lows = df['low'].rolling(window=5, center=True).min().dropna()
            significant_lows = []

            for i in range(5, len(lows) - 5):
                if (lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i+1] and
                    lows.iloc[i] < lows.iloc[i-2] and lows.iloc[i] < lows.iloc[i+1]):

                    significant_lows.append((i, lows.iloc[i]))

            if len(significant_lows) < 2:
                return PatternAnalysis(
                    pattern_detected=False,
                    pattern_type=PatternType.DOUBLE_BOTTOM,
                    confidence=0.0,
                    pattern_start=0.0,
                    pattern_end=0.0
                )

            # Look for two bottoms at similar levels
            best_pair = None
            best_similarity = float('inf')

            for i in range(len(significant_lows)):
                for j in range(i + 1, len(significant_lows)):
                    idx1, val1 = significant_lows[i]
                    idx2, val2 = significant_lows[j]

                    # Check if bottoms are at similar levels
                    level_diff = abs(val1 - val2) / val1
                    distance = j - i  # Number of periods between bottoms

                    # Optimal distance between bottoms (20-50 periods)
                    distance_score = abs(distance - 35) / 35

                    # Find best pair (similar levels + optimal distance)
                    total_score = level_diff + distance_score * 0.5

                    if total_score < best_similarity:
                        best_similarity = total_score
                        best_pair = (idx1, val1, idx2, val2)

            if not best_pair or best_similarity > 0.15:  # 15% tolerance
                return PatternAnalysis(
                    pattern_detected=False,
                    pattern_type=PatternType.DOUBLE_BOTTOM,
                    confidence=0.0,
                    pattern_start=0.0,
                    pattern_end=0.0
                )

            idx1, val1, idx2, val2 = best_pair

            # Find resistance level between bottoms
            resistance_start = min(idx1, idx2)
            resistance_end = max(idx1, idx2)

            pattern_highs = df['high'].iloc[resistance_start:resistance_end+1]
            resistance_level = pattern_highs.max()

            # Calculate pattern height
            pattern_height = resistance_level - min(val1, val2)

            # Check volume confirmation
            volume_confirmation = self._confirm_pattern_volume(df, [idx1, idx2])

            # Check if pattern is completed (price near resistance)
            current_price = df['close'].iloc[-1]
            is_completed = abs(current_price - resistance_level) / resistance_level < 0.05

            # Calculate confidence
            confidence = self._calculate_double_bottom_confidence(
                best_pair, best_similarity, volume_confirmation, is_completed
            )

            return PatternAnalysis(
                pattern_detected=True,
                pattern_type=PatternType.DOUBLE_BOTTOM,
                confidence=confidence,
                pattern_start=df.index[min(idx1, idx2)],
                pattern_end=df.index[max(idx1, idx2)],
                neckline_level=resistance_level,
                breakout_level=resistance_level,
                pattern_height=pattern_height,
                expected_move=pattern_height,
                volume_confirmation=volume_confirmation,
                is_completed=is_completed,
                key_points={
                    'first_bottom': val1,
                    'second_bottom': val2,
                    'resistance': resistance_level
                },
                metadata={
                    'bottom_similarity': 1.0 - best_similarity,
                    'pattern_duration': abs(idx2 - idx1)
                }
            )

        except Exception as e:
            self.logger.error(f"Error detecting double bottom: {e}")
            return PatternAnalysis(
                pattern_detected=False,
                pattern_type=PatternType.DOUBLE_BOTTOM,
                confidence=0.0,
                pattern_start=0.0,
                pattern_end=0.0
            )

    async def _detect_rounding_bottom(self, df: pd.DataFrame) -> PatternAnalysis:
        """Detect rounding bottom pattern."""
        try:
            if len(df) < 30:
                return PatternAnalysis(
                    pattern_detected=False,
                    pattern_type=PatternType.ROUNDING_BOTTOM,
                    confidence=0.0,
                    pattern_start=0.0,
                    pattern_end=0.0
                )

            # Use polynomial fitting to detect curvature
            recent_data = df.tail(30)
            x = np.arange(len(recent_data))
            y = recent_data['close'].values

            # Fit 2nd degree polynomial
            coeffs = np.polyfit(x, y, 2)
            a, b, c = coeffs

            # Check for U-shape (positive second derivative)
            is_u_shaped = a > 0

            if not is_u_shaped:
                return PatternAnalysis(
                    pattern_detected=False,
                    pattern_type=PatternType.ROUNDING_BOTTOM,
                    confidence=0.0,
                    pattern_start=0.0,
                    pattern_end=0.0
                )

            # Calculate pattern metrics
            vertex_x = -b / (2 * a)
            vertex_y = a * vertex_x**2 + b * vertex_x + c

            # Vertex should be in the middle third of the pattern
            vertex_position = vertex_x / len(recent_data)
            good_vertex_position = 0.33 <= vertex_position <= 0.67

            # Calculate curvature strength
            curvature_strength = min(abs(a) * 1000, 1.0)  # Normalize to 0-1

            # Check price action consistency
            current_price = df['close'].iloc[-1]
            start_price = recent_data['close'].iloc[0]
            price_progress = (current_price - vertex_y) / (start_price - vertex_y) if start_price != vertex_y else 0

            # Pattern is more valid if price has recovered significantly
            recovery_strength = min(price_progress, 1.0) if price_progress > 0 else 0

            # Calculate confidence
            confidence = (curvature_strength * 0.4 + recovery_strength * 0.4 +
                         (1.0 if good_vertex_position else 0.2))

            # Calculate expected move
            pattern_height = start_price - vertex_y
            expected_move = pattern_height * 0.8  # Conservative target

            return PatternAnalysis(
                pattern_detected=True,
                pattern_type=PatternType.ROUNDING_BOTTOM,
                confidence=confidence,
                pattern_start=recent_data.index[0],
                pattern_end=recent_data.index[-1],
                breakout_level=current_price,
                pattern_height=pattern_height,
                expected_move=expected_move,
                is_completed=confidence > 0.7,
                key_points={
                    'vertex_price': vertex_y,
                    'start_price': start_price,
                    'current_price': current_price
                },
                metadata={
                    'curvature': a,
                    'vertex_position': vertex_position,
                    'recovery_progress': recovery_strength
                }
            )

        except Exception as e:
            self.logger.error(f"Error detecting rounding bottom: {e}")
            return PatternAnalysis(
                pattern_detected=False,
                pattern_type=PatternType.ROUNDING_BOTTOM,
                confidence=0.0,
                pattern_start=0.0,
                pattern_end=0.0
            )

    async def _detect_candlestick_patterns(self, df: pd.DataFrame) -> List[PatternAnalysis]:
        """Detect candlestick reversal patterns."""
        patterns = []

        if len(df) < 3:
            return patterns

        # Check recent candles for reversal patterns
        recent_candles = df.tail(3)

        # Bullish engulfing pattern
        engulfing_pattern = self._detect_bullish_engulfing(recent_candles)
        if engulfing_pattern:
            patterns.append(engulfing_pattern)

        # Hammer pattern
        hammer_pattern = self._detect_hammer(recent_candles)
        if hammer_pattern:
            patterns.append(hammer_pattern)

        # Morning star pattern
        morning_star = self._detect_morning_star(recent_candles)
        if morning_star:
            patterns.append(morning_star)

        return patterns

    def _detect_bullish_engulfing(self, candles: pd.DataFrame) -> Optional[PatternAnalysis]:
        """Detect bullish engulfing candlestick pattern."""
        try:
            if len(candles) < 2:
                return None

            # Previous candle (red) and current candle (green)
            prev_candle = candles.iloc[-2]
            curr_candle = candles.iloc[-1]

            # Bullish engulfing conditions
            is_bearish_prev = prev_candle['close'] < prev_candle['open']
            is_bullish_curr = curr_candle['close'] > curr_candle['open']
            engulfs_body = (curr_candle['open'] < prev_candle['close'] and
                           curr_candle['close'] > prev_candle['open'])

            if is_bearish_prev and is_bullish_curr and engulfs_body:
                confidence = 0.7
                # Higher confidence if pattern occurs at support
                if curr_candle['low'] == candles['low'].min():
                    confidence = 0.85

                return PatternAnalysis(
                    pattern_detected=True,
                    pattern_type=PatternType.BULLISH_ENGULFING,
                    confidence=confidence,
                    pattern_start=candles.index[-2],
                    pattern_end=candles.index[-1],
                    breakout_level=curr_candle['close'],
                    expected_move=(curr_candle['close'] - prev_candle['open']) * 1.5,
                    is_completed=True,
                    key_points={
                        'prev_open': prev_candle['open'],
                        'prev_close': prev_candle['close'],
                        'curr_open': curr_candle['open'],
                        'curr_close': curr_candle['close']
                    }
                )

            return None

        except Exception as e:
            self.logger.error(f"Error detecting bullish engulfing: {e}")
            return None

    def _detect_hammer(self, candles: pd.DataFrame) -> Optional[PatternAnalysis]:
        """Detect hammer candlestick pattern."""
        try:
            if len(candles) < 1:
                return None

            candle = candles.iloc[-1]

            # Hammer conditions
            body_size = abs(candle['close'] - candle['open'])
            lower_shadow = candle['open'] - candle['low'] if candle['close'] > candle['open'] else candle['close'] - candle['low']
            upper_shadow = candle['high'] - candle['open'] if candle['close'] > candle['open'] else candle['high'] - candle['close']
            total_range = candle['high'] - candle['low']

            # Hammer has small body, long lower shadow, small upper shadow
            is_hammer = (body_size < total_range * 0.3 and
                        lower_shadow > total_range * 0.6 and
                        upper_shadow < total_range * 0.1)

            if is_hammer:
                confidence = 0.75
                # Higher confidence if at support level
                if candle['low'] == candles['low'].min():
                    confidence = 0.9

                return PatternAnalysis(
                    pattern_detected=True,
                    pattern_type=PatternType.HAMMER,
                    confidence=confidence,
                    pattern_start=candles.index[-1],
                    pattern_end=candles.index[-1],
                    breakout_level=candle['close'],
                    expected_move=lower_shadow * 0.8,
                    is_completed=True,
                    key_points={
                        'open': candle['open'],
                        'close': candle['close'],
                        'high': candle['high'],
                        'low': candle['low']
                    }
                )

            return None

        except Exception as e:
            self.logger.error(f"Error detecting hammer: {e}")
            return None

    def _detect_morning_star(self, candles: pd.DataFrame) -> Optional[PatternAnalysis]:
        """Detect morning star candlestick pattern."""
        try:
            if len(candles) < 3:
                return None

            # Three candles: bearish, small body, bullish
            first = candles.iloc[-3]
            second = candles.iloc[-2]
            third = candles.iloc[-1]

            # Morning star conditions
            first_bearish = first['close'] < first['open']
            third_bullish = third['close'] > third['open']
            small_body_second = abs(second['close'] - second['open']) < (first['high'] - first['low']) * 0.3

            # Third candle closes above first candle's midpoint
            first_midpoint = first['open'] + (first['close'] - first['open']) * 0.5
            third_closes_above = third['close'] > first_midpoint

            if first_bearish and third_bullish and small_body_second and third_closes_above:
                confidence = 0.8

                return PatternAnalysis(
                    pattern_detected=True,
                    pattern_type=PatternType.MORNING_STAR,
                    confidence=confidence,
                    pattern_start=candles.index[-3],
                    pattern_end=candles.index[-1],
                    breakout_level=third['close'],
                    expected_move=(third['close'] - first['close']) * 1.2,
                    is_completed=True,
                    key_points={
                        'first_candle': {'open': first['open'], 'close': first['close']},
                        'second_candle': {'open': second['open'], 'close': second['close']},
                        'third_candle': {'open': third['open'], 'close': third['close']}
                    }
                )

            return None

        except Exception as e:
            self.logger.error(f"Error detecting morning star: {e}")
            return None

    def _confirm_pattern_volume(self, df: pd.DataFrame, key_points: List[int]) -> bool:
        """Confirm pattern with volume analysis."""
        try:
            if 'volume' not in df.columns:
                return True  # Assume confirmed if no volume data

            # Check volume at key points
            volumes = []
            for point_idx in key_points:
                if point_idx < len(df):
                    volumes.append(df['volume'].iloc[point_idx])

            if not volumes:
                return True

            # For reversal patterns, volume should ideally decrease into pattern and increase on completion
            if len(volumes) >= 2:
                volume_trend = volumes[-1] > volumes[0]  # Increasing volume on completion
                return volume_trend

            return True

        except Exception as e:
            self.logger.error(f"Error confirming pattern volume: {e}")
            return True

    def _calculate_hs_confidence(self, lows: List[Tuple[int, float]], shoulder_diff: float,
                               volume_confirmed: bool, is_completed: bool) -> float:
        """Calculate head and shoulders confidence."""
        confidence = 0.6  # Base confidence

        # Structure symmetry bonus
        symmetry_bonus = (1.0 - shoulder_diff) * 0.2
        confidence += symmetry_bonus

        # Volume confirmation bonus
        if volume_confirmed:
            confidence += 0.15

        # Pattern completion bonus
        if is_completed:
            confidence += 0.15

        return min(1.0, confidence)

    def _calculate_double_bottom_confidence(self, bottoms: Tuple[int, float, int, float],
                                          similarity: float, volume_confirmed: bool,
                                          is_completed: bool) -> float:
        """Calculate double bottom confidence."""
        confidence = 0.6  # Base confidence

        # Similarity bonus
        similarity_bonus = (1.0 - similarity) * 0.2
        confidence += similarity_bonus

        # Volume confirmation bonus
        if volume_confirmed:
            confidence += 0.15

        # Pattern completion bonus
        if is_completed:
            confidence += 0.15

        return min(1.0, confidence)

    def _generate_pattern_signal(self, pattern_analysis: PatternAnalysis,
                               market_data: MarketData) -> Optional[DetectionResult]:
        """Generate pattern-based signal."""
        try:
            # Determine signal strength based on pattern confidence
            if pattern_analysis.confidence >= 0.9:
                signal_strength = SignalStrength.VERY_STRONG
            elif pattern_analysis.confidence >= 0.8:
                signal_strength = SignalStrength.STRONG
            elif pattern_analysis.confidence >= 0.7:
                signal_strength = SignalStrength.MODERATE
            else:
                return None  # Don't generate signal for low confidence patterns

            # Determine signal type
            signal_type = SignalType.STRONG_BUY if pattern_analysis.confidence >= 0.85 else SignalType.BUY

            # Confidence equals pattern confidence
            confidence = pattern_analysis.confidence

            # Calculate price targets
            current_price = market_data.get_price()
            price_target = None
            stop_loss = None
            take_profit = None

            if current_price and pattern_analysis.expected_move:
                # Price target based on pattern measured move
                price_target = current_price + pattern_analysis.expected_move

                # Stop loss below pattern low
                pattern_low = min(pattern_analysis.key_points.values()) if pattern_analysis.key_points else current_price * 0.95
                stop_loss = pattern_low * 0.98  # 2% below pattern low

                # Take profit at target
                take_profit = price_target

            # Generate reasoning
            reasoning_parts = []
            reasoning_parts.append(f"{pattern_analysis.pattern_type.value.replace('_', ' ').title()} pattern detected")

            if pattern_analysis.confidence >= 0.9:
                reasoning_parts.append("High confidence pattern with clear structure")

            if pattern_analysis.volume_confirmation:
                reasoning_parts.append("Volume confirms the pattern")

            if pattern_analysis.is_completed:
                reasoning_parts.append("Pattern is completed and ready for breakout")

            if pattern_analysis.expected_move:
                reasoning_parts.append(f"Expected move: {pattern_analysis.expected_move:.2f}")

            reasoning = ". ".join(reasoning_parts) + "." if reasoning_parts else "Chart pattern detected."

            return DetectionResult(
                signal_type=signal_type,
                strength=signal_strength,
                confidence=confidence,
                price_target=price_target,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reasoning=reasoning,
                key_indicators={
                    'pattern_confidence': pattern_analysis.confidence,
                    'pattern_height': pattern_analysis.pattern_height or 0.0,
                    'expected_move': pattern_analysis.expected_move or 0.0
                },
                metadata={
                    'pattern_type': pattern_analysis.pattern_type.value,
                    'is_completed': pattern_analysis.is_completed,
                    'volume_confirmed': pattern_analysis.volume_confirmation,
                    'pattern_key_points': pattern_analysis.key_points
                }
            )

        except Exception as e:
            self.logger.error(f"Error generating pattern signal: {e}")
            return None

    def _market_data_to_dataframe(self, market_data: MarketData) -> Optional[pd.DataFrame]:
        """Convert market data to pandas DataFrame."""
        try:
            if hasattr(market_data, 'ohlcv_data') and market_data.ohlcv_data:
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

            return None

        except Exception as e:
            self.logger.error(f"Error converting market data: {e}")
            return None