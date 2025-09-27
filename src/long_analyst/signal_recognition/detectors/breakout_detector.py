"""
Breakout Detection Algorithms for Long Analyst Agent.

Advanced algorithms for detecting resistance breakouts, pattern breakouts,
and false breakout filtering with volume confirmation.
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


class BreakoutType(Enum):
    """Types of breakouts."""
    RESISTANCE_BREAKOUT = "resistance_breakout"
    SUPPORT_BREAKOUT = "support_breakout"
    PATTERN_BREAKOUT = "pattern_breakout"
    RANGE_BREAKOUT = "range_breakout"


class PatternType(Enum):
    """Chart pattern types."""
    TRIANGLE = "triangle"
    RECTANGLE = "rectangle"
    WEDGE = "wedge"
    FLAG = "flag"
    PENNANT = "pennant"


@dataclass
class BreakoutAnalysis:
    """Result of breakout analysis."""
    breakout_detected: bool
    breakout_type: BreakoutType
    breakout_price: float
    breakout_time: float
    resistance_level: Optional[float] = None
    support_level: Optional[float] = None
    volume_confirmation: bool = False
    volume_ratio: float = 0.0
    is_false_breakout: bool = False
    breakout_strength: float = 0.0
    pattern_type: Optional[PatternType] = None
    pattern_height: Optional[float] = None
    expected_move: Optional[float] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}


class BreakoutDetector(SignalDetector):
    """
    Advanced breakout detection algorithm for long trading opportunities.

    This detector identifies resistance breakouts, pattern breakouts, and
    filters false breakouts using volume confirmation and other criteria.
    """

    def __init__(self, config: DetectorConfig):
        """Initialize the breakout detector."""
        super().__init__(config)
        self.lookback_periods = config.parameters.get('lookback_periods', 50)
        self.confirmation_periods = config.parameters.get('confirmation_periods', 3)
        self.volume_multiplier = config.parameters.get('volume_multiplier', 1.5)
        self.false_breakout_filter = config.parameters.get('false_breakout_filter', True)

    def get_required_indicators(self) -> List[str]:
        """Get required technical indicators."""
        return ['volume_profile', 'bollinger_bands', 'atr', 'support_resistance']

    async def detect(self, market_data: MarketData) -> List[DetectionResult]:
        """
        Detect breakout-based signals.

        Args:
            market_data: Market data to analyze

        Returns:
            List of detection results
        """
        try:
            # Convert market data to DataFrame
            df = self._market_data_to_dataframe(market_data)
            if df is None or len(df) < self.lookback_periods:
                return []

            # Analyze different types of breakouts
            breakout_signals = []

            # Resistance breakout detection
            resistance_breakout = await self._detect_resistance_breakout(df)
            if resistance_breakout.breakout_detected:
                signal = self._generate_breakout_signal(resistance_breakout, market_data)
                if signal:
                    breakout_signals.append(signal)

            # Pattern breakout detection
            pattern_breakout = await self._detect_pattern_breakout(df)
            if pattern_breakout.breakout_detected:
                signal = self._generate_breakout_signal(pattern_breakout, market_data)
                if signal:
                    breakout_signals.append(signal)

            # Range breakout detection
            range_breakout = await self._detect_range_breakout(df)
            if range_breakout.breakout_detected:
                signal = self._generate_breakout_signal(range_breakout, market_data)
                if signal:
                    breakout_signals.append(signal)

            return breakout_signals

        except Exception as e:
            self.logger.error(f"Error in breakout detection: {e}")
            return []

    async def _detect_resistance_breakout(self, df: pd.DataFrame) -> BreakoutAnalysis:
        """Detect resistance level breakouts."""
        try:
            # Identify resistance levels
            resistance_levels = self._identify_resistance_levels(df)

            if not resistance_levels:
                return BreakoutAnalysis(
                    breakout_detected=False,
                    breakout_type=BreakoutType.RESISTANCE_BREAKOUT,
                    breakout_price=0.0,
                    breakout_time=0.0
                )

            # Check for breakout at nearest resistance
            nearest_resistance = min(resistance_levels, key=lambda x: abs(x - df['close'].iloc[-1]))
            current_price = df['close'].iloc[-1]

            # Check if price broke through resistance
            breakout_detected = current_price > nearest_resistance

            if not breakout_detected:
                return BreakoutAnalysis(
                    breakout_detected=False,
                    breakout_type=BreakoutType.RESISTANCE_BREAKOUT,
                    breakout_price=current_price,
                    breakout_time=df.index[-1].timestamp() if hasattr(df.index[-1], 'timestamp') else datetime.now().timestamp()
                )

            # Confirm breakout with volume
            volume_confirmation, volume_ratio = self._confirm_breakout_volume(df)

            # Check for false breakout
            is_false_breakout = False
            if self.false_breakout_filter:
                is_false_breakout = self._is_false_breakout(df, nearest_resistance)

            # Calculate breakout strength
            breakout_strength = self._calculate_breakout_strength(
                df, nearest_resistance, volume_ratio, is_false_breakout
            )

            return BreakoutAnalysis(
                breakout_detected=True,
                breakout_type=BreakoutType.RESISTANCE_BREAKOUT,
                breakout_price=current_price,
                breakout_time=df.index[-1].timestamp() if hasattr(df.index[-1], 'timestamp') else datetime.now().timestamp(),
                resistance_level=nearest_resistance,
                volume_confirmation=volume_confirmation,
                volume_ratio=volume_ratio,
                is_false_breakout=is_false_breakout,
                breakout_strength=breakout_strength,
                metadata={
                    'resistance_levels': resistance_levels,
                    'breakout_margin': (current_price - nearest_resistance) / nearest_resistance * 100
                }
            )

        except Exception as e:
            self.logger.error(f"Error detecting resistance breakout: {e}")
            return BreakoutAnalysis(
                breakout_detected=False,
                breakout_type=BreakoutType.RESISTANCE_BREAKOUT,
                breakout_price=0.0,
                breakout_time=0.0
            )

    async def _detect_pattern_breakout(self, df: pd.DataFrame) -> BreakoutAnalysis:
        """Detect pattern-based breakouts."""
        try:
            # Detect chart patterns
            patterns = self._detect_chart_patterns(df)

            if not patterns:
                return BreakoutAnalysis(
                    breakout_detected=False,
                    breakout_type=BreakoutType.PATTERN_BREAKOUT,
                    breakout_price=0.0,
                    breakout_time=0.0
                )

            # Check for breakout from strongest pattern
            best_pattern = max(patterns, key=lambda p: p['confidence'])

            if not best_pattern['breakout_detected']:
                return BreakoutAnalysis(
                    breakout_detected=False,
                    breakout_type=BreakoutType.PATTERN_BREAKOUT,
                    breakout_price=df['close'].iloc[-1],
                    breakout_time=df.index[-1].timestamp() if hasattr(df.index[-1], 'timestamp') else datetime.now().timestamp()
                )

            # Confirm with volume
            volume_confirmation, volume_ratio = self._confirm_breakout_volume(df)

            # Check for false breakout
            is_false_breakout = False
            if self.false_breakout_filter:
                is_false_breakout = self._is_false_breakout(df, best_pattern['breakout_level'])

            return BreakoutAnalysis(
                breakout_detected=True,
                breakout_type=BreakoutType.PATTERN_BREAKOUT,
                breakout_price=df['close'].iloc[-1],
                breakout_time=df.index[-1].timestamp() if hasattr(df.index[-1], 'timestamp') else datetime.now().timestamp(),
                resistance_level=best_pattern['breakout_level'],
                volume_confirmation=volume_confirmation,
                volume_ratio=volume_ratio,
                is_false_breakout=is_false_breakout,
                breakout_strength=best_pattern['confidence'],
                pattern_type=best_pattern['pattern_type'],
                pattern_height=best_pattern.get('height'),
                expected_move=best_pattern.get('expected_move'),
                metadata={
                    'pattern_info': best_pattern,
                    'all_patterns': patterns
                }
            )

        except Exception as e:
            self.logger.error(f"Error detecting pattern breakout: {e}")
            return BreakoutAnalysis(
                breakout_detected=False,
                breakout_type=BreakoutType.PATTERN_BREAKOUT,
                breakout_price=0.0,
                breakout_time=0.0
            )

    async def _detect_range_breakout(self, df: pd.DataFrame) -> BreakoutAnalysis:
        """Detect range-based breakouts."""
        try:
            # Identify trading range
            range_info = self._identify_trading_range(df)

            if not range_info:
                return BreakoutAnalysis(
                    breakout_detected=False,
                    breakout_type=BreakoutType.RANGE_BREAKOUT,
                    breakout_price=0.0,
                    breakout_time=0.0
                )

            current_price = df['close'].iloc[-1]
            upper_bound = range_info['upper_bound']
            lower_bound = range_info['lower_bound']

            # Check for upper range breakout
            breakout_detected = current_price > upper_bound

            if not breakout_detected:
                return BreakoutAnalysis(
                    breakout_detected=False,
                    breakout_type=BreakoutType.RANGE_BREAKOUT,
                    breakout_price=current_price,
                    breakout_time=df.index[-1].timestamp() if hasattr(df.index[-1], 'timestamp') else datetime.now().timestamp()
                )

            # Confirm with volume
            volume_confirmation, volume_ratio = self._confirm_breakout_volume(df)

            # Check for false breakout
            is_false_breakout = False
            if self.false_breakout_filter:
                is_false_breakout = self._is_false_breakout(df, upper_bound)

            # Calculate breakout strength
            breakout_strength = self._calculate_range_breakout_strength(
                df, range_info, volume_ratio, is_false_breakout
            )

            return BreakoutAnalysis(
                breakout_detected=True,
                breakout_type=BreakoutType.RANGE_BREAKOUT,
                breakout_price=current_price,
                breakout_time=df.index[-1].timestamp() if hasattr(df.index[-1], 'timestamp') else datetime.now().timestamp(),
                resistance_level=upper_bound,
                support_level=lower_bound,
                volume_confirmation=volume_confirmation,
                volume_ratio=volume_ratio,
                is_false_breakout=is_false_breakout,
                breakout_strength=breakout_strength,
                expected_move=range_info.get('expected_move'),
                metadata={
                    'range_info': range_info,
                    'range_height': upper_bound - lower_bound
                }
            )

        except Exception as e:
            self.logger.error(f"Error detecting range breakout: {e}")
            return BreakoutAnalysis(
                breakout_detected=False,
                breakout_type=BreakoutType.RANGE_BREAKOUT,
                breakout_price=0.0,
                breakout_time=0.0
            )

    def _identify_resistance_levels(self, df: pd.DataFrame) -> List[float]:
        """Identify resistance levels from price data."""
        resistance_levels = []

        # Use recent highs
        recent_highs = df['high'].rolling(window=5, center=True).max().dropna()

        # Find significant highs (local maxima)
        for i in range(2, len(recent_highs) - 2):
            if (recent_highs.iloc[i] > recent_highs.iloc[i-1] and
                recent_highs.iloc[i] > recent_highs.iloc[i+1] and
                recent_highs.iloc[i] > recent_highs.iloc[i-2] and
                recent_highs.iloc[i] > recent_highs.iloc[i+2]):

                # Group nearby levels
                level = recent_highs.iloc[i]
                found_group = False

                for existing_level in resistance_levels:
                    if abs(level - existing_level) / existing_level < 0.02:  # 2% tolerance
                        found_group = True
                        break

                if not found_group:
                    resistance_levels.append(level)

        return resistance_levels

    def _detect_chart_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect chart patterns that could lead to breakouts."""
        patterns = []

        # Detect triangles
        triangle_patterns = self._detect_triangles(df)
        patterns.extend(triangle_patterns)

        # Detect rectangles
        rectangle_patterns = self._detect_rectangles(df)
        patterns.extend(rectangle_patterns)

        # Detect flags and pennants
        flag_patterns = self._detect_flags_pennants(df)
        patterns.extend(flag_patterns)

        return patterns

    def _detect_triangles(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect triangle patterns."""
        patterns = []

        if len(df) < 30:
            return patterns

        # Simple triangle detection using trendlines
        highs = df['high'].tail(30)
        lows = df['low'].tail(30)

        # Fit descending trendline for highs
        x_high = np.arange(len(highs))
        if len(highs) > 5:
            slope_high, intercept_high = np.polyfit(x_high, highs, 1)

        # Fit ascending trendline for lows
        x_low = np.arange(len(lows))
        if len(lows) > 5:
            slope_low, intercept_low = np.polyfit(x_low, lows, 1)

        # Check for converging trendlines (triangle)
        if 'slope_high' in locals() and 'slope_low' in locals():
            if slope_high < 0 and slope_low > 0:  # Converging triangle
                # Calculate apex
                current_x = len(highs) - 1
                high_line = slope_high * current_x + intercept_high
                low_line = slope_low * current_x + intercept_low

                # Check if price is near apex (breakout zone)
                current_price = df['close'].iloc[-1]
                apex_threshold = abs(high_line - low_line) * 0.1  # 10% of pattern height

                if abs(current_price - high_line) < apex_threshold or abs(current_price - low_line) < apex_threshold:
                    pattern_height = abs(highs.iloc[0] - lows.iloc[0])

                    patterns.append({
                        'pattern_type': PatternType.TRIANGLE,
                        'confidence': min(0.9, 0.5 + abs(slope_high - slope_low) * 10),
                        'breakout_level': high_line,
                        'breakout_detected': current_price > high_line,
                        'height': pattern_height,
                        'expected_move': pattern_height * 0.6,  # Measured move target
                        'slope_high': slope_high,
                        'slope_low': slope_low
                    })

        return patterns

    def _detect_rectangles(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect rectangle patterns."""
        patterns = []

        if len(df) < 20:
            return patterns

        # Look for consolidation zones
        recent_data = df.tail(20)
        price_range = recent_data['high'].max() - recent_data['low'].min()
        avg_range = (df['high'] - df['low']).rolling(20).mean().iloc[-1]

        # Check if price is consolidating (range bound)
        if price_range < avg_range * 1.5:  # Range is relatively tight
            upper_bound = recent_data['high'].max()
            lower_bound = recent_data['low'].min()
            current_price = df['close'].iloc[-1]

            pattern_height = upper_bound - lower_bound

            patterns.append({
                'pattern_type': PatternType.RECTANGLE,
                'confidence': min(0.8, 0.4 + (1.0 - price_range / (avg_range * 2))),
                'breakout_level': upper_bound,
                'breakout_detected': current_price > upper_bound,
                'height': pattern_height,
                'expected_move': pattern_height * 0.8,  # Measured move target
                'upper_bound': upper_bound,
                'lower_bound': lower_bound
            })

        return patterns

    def _detect_flags_pennants(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect flag and pennant patterns."""
        patterns = []

        if len(df) < 25:
            return patterns

        # Look for consolidation after strong move
        recent_data = df.tail(25)
        move_data = recent_data.head(10)  # Prior move
        consolidation_data = recent_data.tail(15)  # Consolidation

        # Check for strong prior move
        prior_move = (move_data['close'].iloc[-1] - move_data['close'].iloc[0]) / move_data['close'].iloc[0]

        if abs(prior_move) > 0.05:  # 5% move
            # Check for tight consolidation
            consolidation_range = consolidation_data['high'].max() - consolidation_data['low'].min()
            avg_range = (df['high'] - df['low']).rolling(20).mean().iloc[-1]

            if consolidation_range < avg_range:  # Tight consolidation
                upper_bound = consolidation_data['high'].max()
                lower_bound = consolidation_data['low'].min()
                current_price = df['close'].iloc[-1]

                pattern_height = consolidation_range

                patterns.append({
                    'pattern_type': PatternType.FLAG if consolidation_range < avg_range * 0.5 else PatternType.PENNANT,
                    'confidence': min(0.9, 0.6 + abs(prior_move) * 5),
                    'breakout_level': upper_bound if prior_move > 0 else lower_bound,
                    'breakout_detected': (current_price > upper_bound) if prior_move > 0 else (current_price < lower_bound),
                    'height': pattern_height,
                    'expected_move': abs(prior_move) * 1.2,  # Flag target = prior move length
                    'prior_move': prior_move,
                    'upper_bound': upper_bound,
                    'lower_bound': lower_bound
                })

        return patterns

    def _identify_trading_range(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Identify trading range boundaries."""
        try:
            recent_data = df.tail(self.lookback_periods)

            # Find support and resistance levels
            support = recent_data['low'].quantile(0.1)  # 10th percentile
            resistance = recent_data['high'].quantile(0.9)  # 90th percentile

            # Check if price has been trading in range
            range_test_period = min(20, len(recent_data))
            in_range_count = 0

            for i in range(-range_test_period, 0):
                if support <= recent_data['close'].iloc[i] <= resistance:
                    in_range_count += 1

            range_compliance = in_range_count / range_test_period

            # Require at least 70% of prices to be within range
            if range_compliance < 0.7:
                return None

            # Calculate expected move (height of range)
            range_height = resistance - support
            expected_move = range_height * 0.8  # Typical breakout target

            return {
                'upper_bound': resistance,
                'lower_bound': support,
                'range_height': range_height,
                'range_compliance': range_compliance,
                'expected_move': expected_move
            }

        except Exception as e:
            self.logger.error(f"Error identifying trading range: {e}")
            return None

    def _confirm_breakout_volume(self, df: pd.DataFrame) -> Tuple[bool, float]:
        """Confirm breakout with volume analysis."""
        try:
            if 'volume' not in df.columns:
                return True, 1.0  # Assume confirmed if no volume data

            # Calculate average volume
            avg_volume = df['volume'].tail(20).mean()
            recent_volume = df['volume'].tail(3).mean()

            if avg_volume == 0:
                return True, 1.0

            volume_ratio = recent_volume / avg_volume
            volume_confirmed = volume_ratio >= self.volume_multiplier

            return volume_confirmed, volume_ratio

        except Exception as e:
            self.logger.error(f"Error confirming breakout volume: {e}")
            return True, 1.0

    def _is_false_breakout(self, df: pd.DataFrame, breakout_level: float) -> bool:
        """Check if breakout is likely false."""
        try:
            # Check if price quickly retreated after breakout
            recent_prices = df['close'].tail(self.confirmation_periods)

            # Look for price closing back below breakout level
            closes_below = sum(1 for price in recent_prices if price < breakout_level)
            false_breakout_ratio = closes_below / len(recent_prices)

            # If more than 50% of recent closes are below, likely false breakout
            return false_breakout_ratio > 0.5

        except Exception as e:
            self.logger.error(f"Error checking false breakout: {e}")
            return False

    def _calculate_breakout_strength(self, df: pd.DataFrame, breakout_level: float,
                                   volume_ratio: float, is_false_breakout: bool) -> float:
        """Calculate breakout strength."""
        strength = 0.0

        # Base strength from volume confirmation
        if volume_ratio >= self.volume_multiplier:
            strength += 0.4
        elif volume_ratio >= 1.0:
            strength += 0.2

        # Strength from breakout margin
        current_price = df['close'].iloc[-1]
        breakout_margin = (current_price - breakout_level) / breakout_level
        strength += min(0.3, breakout_margin * 10)  # Cap at 0.3

        # Penalty for false breakout
        if is_false_breakout:
            strength *= 0.3

        return min(1.0, max(0.0, strength))

    def _calculate_range_breakout_strength(self, df: pd.DataFrame, range_info: Dict[str, Any],
                                         volume_ratio: float, is_false_breakout: bool) -> float:
        """Calculate range breakout strength."""
        strength = 0.0

        # Base strength from volume
        if volume_ratio >= self.volume_multiplier:
            strength += 0.3

        # Strength from range compliance (tighter ranges = stronger breakouts)
        range_compliance = range_info.get('range_compliance', 0.7)
        strength += range_compliance * 0.3

        # Strength from breakout momentum
        recent_momentum = (df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5]
        if recent_momentum > 0:
            strength += min(0.2, recent_momentum * 5)

        # Penalty for false breakout
        if is_false_breakout:
            strength *= 0.3

        return min(1.0, max(0.0, strength))

    def _generate_breakout_signal(self, breakout_analysis: BreakoutAnalysis,
                                market_data: MarketData) -> Optional[DetectionResult]:
        """Generate breakout-based signal."""
        try:
            # Don't generate signal for false breakouts
            if breakout_analysis.is_false_breakout:
                return None

            # Determine signal strength
            if breakout_analysis.breakout_strength >= 0.8:
                signal_strength = SignalStrength.VERY_STRONG
            elif breakout_analysis.breakout_strength >= 0.6:
                signal_strength = SignalStrength.STRONG
            else:
                signal_strength = SignalStrength.MODERATE

            # Determine signal type
            signal_type = SignalType.STRONG_BUY if breakout_analysis.breakout_strength >= 0.7 else SignalType.BUY

            # Calculate confidence
            confidence = breakout_analysis.breakout_strength
            if breakout_analysis.volume_confirmation:
                confidence *= 1.1  # 10% bonus for volume confirmation

            confidence = min(1.0, confidence)

            # Calculate price targets
            current_price = market_data.get_price()
            price_target = None
            stop_loss = None
            take_profit = None

            if current_price and breakout_analysis.expected_move:
                # Price target based on expected move
                price_target = current_price + breakout_analysis.expected_move

                # Stop loss below breakout level
                stop_loss = max(breakout_analysis.resistance_level or current_price * 0.98,
                               current_price * 0.98)

                # Take profit at target
                take_profit = price_target

            # Generate reasoning
            reasoning_parts = []
            if breakout_analysis.breakout_type == BreakoutType.RESISTANCE_BREAKOUT:
                reasoning_parts.append(f"Resistance breakout at {breakout_analysis.resistance_level:.2f}")
            elif breakout_analysis.breakout_type == BreakoutType.PATTERN_BREAKOUT:
                reasoning_parts.append(f"{breakout_analysis.pattern_type.value.title()} pattern breakout")
            elif breakout_analysis.breakout_type == BreakoutType.RANGE_BREAKOUT:
                reasoning_parts.append("Trading range breakout")

            if breakout_analysis.volume_confirmation:
                reasoning_parts.append(f"Volume confirms breakout (ratio: {breakout_analysis.volume_ratio:.1f}x)")

            if not breakout_analysis.is_false_breakout:
                reasoning_parts.append("Breakout appears valid (no false breakout indicators)")

            reasoning = ". ".join(reasoning_parts) + "." if reasoning_parts else "Breakout detected."

            return DetectionResult(
                signal_type=signal_type,
                strength=signal_strength,
                confidence=confidence,
                price_target=price_target,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reasoning=reasoning,
                key_indicators={
                    'breakout_strength': breakout_analysis.breakout_strength,
                    'volume_ratio': breakout_analysis.volume_ratio,
                    'breakout_margin': (breakout_analysis.breakout_price - (breakout_analysis.resistance_level or 0)) / (breakout_analysis.resistance_level or 1) * 100
                },
                metadata={
                    'breakout_type': breakout_analysis.breakout_type.value,
                    'breakout_level': breakout_analysis.resistance_level,
                    'volume_confirmed': breakout_analysis.volume_confirmation,
                    'pattern_type': breakout_analysis.pattern_type.value if breakout_analysis.pattern_type else None
                }
            )

        except Exception as e:
            self.logger.error(f"Error generating breakout signal: {e}")
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