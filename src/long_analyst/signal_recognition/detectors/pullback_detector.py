"""
Pullback Detection Algorithms for Long Analyst Agent.

Advanced algorithms for identifying pullback/buy-on-dip opportunities
using Fibonacci retracements, moving averages, and support levels.
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


class PullbackType(Enum):
    """Types of pullbacks."""
    FIBONACCI_PULLBACK = "fibonacci_pullback"
    MA_PULLBACK = "ma_pullback"
    SUPPORT_PULLBACK = "support_pullback"
    VOLUME_BASED_PULLBACK = "volume_based_pullback"


@dataclass
class PullbackAnalysis:
    """Result of pullback analysis."""
    pullback_detected: bool
    pullback_type: PullbackType
    pullback_depth: float  # Percentage
    pullback_level: float
    current_price: float
    trend_strength: float
    fibonacci_level: Optional[float] = None
    ma_period: Optional[int] = None
    support_level: Optional[float] = None
    volume_profile: Optional[str] = None
    bounce_strength: float = 0.0
    risk_reward_ratio: Optional[float] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}


class PullbackDetector(SignalDetector):
    """
    Advanced pullback detection algorithm for long trading opportunities.

    This detector identifies pullback opportunities using Fibonacci retracements,
    moving average support, and other technical analysis methods.
    """

    def __init__(self, config: DetectorConfig):
        """Initialize the pullback detector."""
        super().__init__(config)
        self.fibonacci_levels = config.parameters.get('fibonacci_levels', [0.382, 0.5, 0.618])
        self.ma_periods = config.parameters.get('ma_periods', [20, 50])
        self.max_depth = config.parameters.get('max_depth', 0.3)  # 30% max pullback

    def get_required_indicators(self) -> List[str]:
        """Get required technical indicators."""
        return ['ema', 'sma', 'rsi', 'macd', 'volume_profile', 'atr']

    async def detect(self, market_data: MarketData) -> List[DetectionResult]:
        """
        Detect pullback-based signals.

        Args:
            market_data: Market data to analyze

        Returns:
            List of detection results
        """
        try:
            # Convert market data to DataFrame
            df = self._market_data_to_dataframe(market_data)
            if df is None or len(df) < 50:
                return []

            # Analyze different types of pullbacks
            pullback_signals = []

            # Fibonacci pullback detection
            fib_pullback = await self._detect_fibonacci_pullback(df)
            if fib_pullback.pullback_detected:
                signal = self._generate_pullback_signal(fib_pullback, market_data)
                if signal:
                    pullback_signals.append(signal)

            # Moving average pullback detection
            ma_pullback = await self._detect_ma_pullback(df)
            if ma_pullback.pullback_detected:
                signal = self._generate_pullback_signal(ma_pullback, market_data)
                if signal:
                    pullback_signals.append(signal)

            # Support level pullback detection
            support_pullback = await self._detect_support_pullback(df)
            if support_pullback.pullback_detected:
                signal = self._generate_pullback_signal(support_pullback, market_data)
                if signal:
                    pullback_signals.append(signal)

            return pullback_signals

        except Exception as e:
            self.logger.error(f"Error in pullback detection: {e}")
            return []

    async def _detect_fibonacci_pullback(self, df: pd.DataFrame) -> PullbackAnalysis:
        """Detect Fibonacci-based pullbacks."""
        try:
            # Identify recent swing high and low
            swing_high, swing_low = self._identify_swing_points(df)

            if swing_high is None or swing_low is None:
                return PullbackAnalysis(
                    pullback_detected=False,
                    pullback_type=PullbackType.FIBONACCI_PULLBACK,
                    pullback_depth=0.0,
                    pullback_level=0.0,
                    current_price=df['close'].iloc[-1],
                    trend_strength=0.0
                )

            current_price = df['close'].iloc[-1]
            total_move = swing_high - swing_low

            # Calculate Fibonacci retracement levels
            fib_levels = {}
            for ratio in self.fibonacci_levels:
                fib_levels[ratio] = swing_high - (total_move * ratio)

            # Find which Fibonacci level price is near
            best_level = None
            best_distance = float('inf')

            for ratio, level in fib_levels.items():
                distance = abs(current_price - level)
                if distance < best_distance:
                    best_distance = distance
                    best_level = ratio
                    best_level_price = level

            # Check if pullback depth is acceptable
            pullback_depth = (swing_high - current_price) / total_move
            if pullback_depth > self.max_depth:
                return PullbackAnalysis(
                    pullback_detected=False,
                    pullback_type=PullbackType.FIBONACCI_PULLBACK,
                    pullback_depth=pullback_depth,
                    pullback_level=0.0,
                    current_price=current_price,
                    trend_strength=0.0
                )

            # Check if price is within tolerance of Fibonacci level
            tolerance = total_move * 0.05  # 5% tolerance
            is_at_fib_level = best_distance <= tolerance

            # Analyze bounce strength
            bounce_strength = self._analyze_bounce_strength(df, best_level_price)

            # Calculate trend strength
            trend_strength = self._calculate_trend_strength(df)

            return PullbackAnalysis(
                pullback_detected=is_at_fib_level,
                pullback_type=PullbackType.FIBONACCI_PULLBACK,
                pullback_depth=pullback_depth * 100,  # Convert to percentage
                pullback_level=best_level_price,
                current_price=current_price,
                trend_strength=trend_strength,
                fibonacci_level=best_level,
                bounce_strength=bounce_strength,
                metadata={
                    'swing_high': swing_high,
                    'swing_low': swing_low,
                    'all_fib_levels': fib_levels,
                    'tolerance_used': tolerance
                }
            )

        except Exception as e:
            self.logger.error(f"Error detecting Fibonacci pullback: {e}")
            return PullbackAnalysis(
                pullback_detected=False,
                pullback_type=PullbackType.FIBONACCI_PULLBACK,
                pullback_depth=0.0,
                pullback_level=0.0,
                current_price=df['close'].iloc[-1],
                trend_strength=0.0
            )

    async def _detect_ma_pullback(self, df: pd.DataFrame) -> PullbackAnalysis:
        """Detect moving average-based pullbacks."""
        try:
            current_price = df['close'].iloc[-1]
            best_ma_pullback = None
            best_distance = float('inf')

            # Check each moving average period
            for period in self.ma_periods:
                if len(df) >= period:
                    ma = df['close'].rolling(window=period).mean()
                    ma_value = ma.iloc[-1]

                    # Check if price pulled back to MA
                    distance = abs(current_price - ma_value)
                    relative_distance = distance / ma_value

                    # Use the closest MA
                    if relative_distance < best_distance:
                        best_distance = relative_distance
                        best_ma_pullback = {
                            'period': period,
                            'ma_value': ma_value,
                            'distance': distance
                        }

            if not best_ma_pullback or best_distance > 0.05:  # 5% tolerance
                return PullbackAnalysis(
                    pullback_detected=False,
                    pullback_type=PullbackType.MA_PULLBACK,
                    pullback_depth=0.0,
                    pullback_level=0.0,
                    current_price=current_price,
                    trend_strength=0.0
                )

            # Calculate pullback depth
            recent_high = df['high'].tail(20).max()
            pullback_depth = (recent_high - current_price) / recent_high

            if pullback_depth > self.max_depth:
                return PullbackAnalysis(
                    pullback_detected=False,
                    pullback_type=PullbackType.MA_PULLBACK,
                    pullback_depth=pullback_depth * 100,
                    pullback_level=0.0,
                    current_price=current_price,
                    trend_strength=0.0
                )

            # Analyze bounce strength
            bounce_strength = self._analyze_bounce_strength(df, best_ma_pullback['ma_value'])

            # Calculate trend strength
            trend_strength = self._calculate_trend_strength(df)

            return PullbackAnalysis(
                pullback_detected=True,
                pullback_type=PullbackType.MA_PULLBACK,
                pullback_depth=pullback_depth * 100,
                pullback_level=best_ma_pullback['ma_value'],
                current_price=current_price,
                trend_strength=trend_strength,
                ma_period=best_ma_pullback['period'],
                bounce_strength=bounce_strength,
                metadata={
                    'ma_distance': best_distance,
                    'recent_high': recent_high
                }
            )

        except Exception as e:
            self.logger.error(f"Error detecting MA pullback: {e}")
            return PullbackAnalysis(
                pullback_detected=False,
                pullback_type=PullbackType.MA_PULLBACK,
                pullback_depth=0.0,
                pullback_level=0.0,
                current_price=df['close'].iloc[-1],
                trend_strength=0.0
            )

    async def _detect_support_pullback(self, df: pd.DataFrame) -> PullbackAnalysis:
        """Detect support level-based pullbacks."""
        try:
            # Identify support levels
            support_levels = self._identify_support_levels(df)

            if not support_levels:
                return PullbackAnalysis(
                    pullback_detected=False,
                    pullback_type=PullbackType.SUPPORT_PULLBACK,
                    pullback_depth=0.0,
                    pullback_level=0.0,
                    current_price=df['close'].iloc[-1],
                    trend_strength=0.0
                )

            current_price = df['close'].iloc[-1]
            nearest_support = min(support_levels, key=lambda x: abs(x - current_price))

            # Check if price is near support
            tolerance = current_price * 0.02  # 2% tolerance
            distance_to_support = abs(current_price - nearest_support)

            if distance_to_support > tolerance:
                return PullbackAnalysis(
                    pullback_detected=False,
                    pullback_type=PullbackType.SUPPORT_PULLBACK,
                    pullback_depth=0.0,
                    pullback_level=nearest_support,
                    current_price=current_price,
                    trend_strength=0.0
                )

            # Calculate pullback depth
            recent_high = df['high'].tail(20).max()
            pullback_depth = (recent_high - current_price) / recent_high

            if pullback_depth > self.max_depth:
                return PullbackAnalysis(
                    pullback_detected=False,
                    pullback_type=PullbackType.SUPPORT_PULLBACK,
                    pullback_depth=pullback_depth * 100,
                    pullback_level=nearest_support,
                    current_price=current_price,
                    trend_strength=0.0
                )

            # Analyze bounce strength
            bounce_strength = self._analyze_bounce_strength(df, nearest_support)

            # Calculate trend strength
            trend_strength = self._calculate_trend_strength(df)

            return PullbackAnalysis(
                pullback_detected=True,
                pullback_type=PullbackType.SUPPORT_PULLBACK,
                pullback_depth=pullback_depth * 100,
                pullback_level=nearest_support,
                current_price=current_price,
                trend_strength=trend_strength,
                support_level=nearest_support,
                bounce_strength=bounce_strength,
                metadata={
                    'all_support_levels': support_levels,
                    'distance_to_support': distance_to_support,
                    'tolerance_used': tolerance
                }
            )

        except Exception as e:
            self.logger.error(f"Error detecting support pullback: {e}")
            return PullbackAnalysis(
                pullback_detected=False,
                pullback_type=PullbackType.SUPPORT_PULLBACK,
                pullback_depth=0.0,
                pullback_level=0.0,
                current_price=df['close'].iloc[-1],
                trend_strength=0.0
            )

    def _identify_swing_points(self, df: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
        """Identify recent swing high and low points."""
        try:
            lookback_period = min(50, len(df))
            recent_data = df.tail(lookback_period)

            # Find swing high (local maximum)
            swing_high = None
            for i in range(5, len(recent_data) - 5):
                if (recent_data['high'].iloc[i] > recent_data['high'].iloc[i-1] and
                    recent_data['high'].iloc[i] > recent_data['high'].iloc[i+1] and
                    recent_data['high'].iloc[i] > recent_data['high'].iloc[i-2] and
                    recent_data['high'].iloc[i] > recent_data['high'].iloc[i+2] and
                    recent_data['high'].iloc[i] > recent_data['high'].iloc[i-3] and
                    recent_data['high'].iloc[i] > recent_data['high'].iloc[i+3]):

                    swing_high = recent_data['high'].iloc[i]
                    break

            # Find swing low (local minimum)
            swing_low = None
            for i in range(5, len(recent_data) - 5):
                if (recent_data['low'].iloc[i] < recent_data['low'].iloc[i-1] and
                    recent_data['low'].iloc[i] < recent_data['low'].iloc[i+1] and
                    recent_data['low'].iloc[i] < recent_data['low'].iloc[i-2] and
                    recent_data['low'].iloc[i] < recent_data['low'].iloc[i+2] and
                    recent_data['low'].iloc[i] < recent_data['low'].iloc[i-3] and
                    recent_data['low'].iloc[i] < recent_data['low'].iloc[i+3]):

                    swing_low = recent_data['low'].iloc[i]
                    break

            return swing_high, swing_low

        except Exception as e:
            self.logger.error(f"Error identifying swing points: {e}")
            return None, None

    def _identify_support_levels(self, df: pd.DataFrame) -> List[float]:
        """Identify support levels from price data."""
        support_levels = []

        try:
            # Use recent lows
            recent_lows = df['low'].rolling(window=5, center=True).min().dropna()

            # Find significant lows (local minima)
            for i in range(2, len(recent_lows) - 2):
                if (recent_lows.iloc[i] < recent_lows.iloc[i-1] and
                    recent_lows.iloc[i] < recent_lows.iloc[i+1] and
                    recent_lows.iloc[i] < recent_lows.iloc[i-2] and
                    recent_lows.iloc[i] < recent_lows.iloc[i+1]):

                    # Group nearby levels
                    level = recent_lows.iloc[i]
                    found_group = False

                    for existing_level in support_levels:
                        if abs(level - existing_level) / existing_level < 0.02:  # 2% tolerance
                            found_group = True
                            break

                    if not found_group:
                        support_levels.append(level)

        except Exception as e:
            self.logger.error(f"Error identifying support levels: {e}")

        return support_levels

    def _analyze_bounce_strength(self, df: pd.DataFrame, support_level: float) -> float:
        """Analyze bounce strength at support level."""
        try:
            if len(df) < 10:
                return 0.5

            # Look for recent price action near support
            recent_data = df.tail(10)
            bounces = 0
            tests = 0

            for i in range(len(recent_data)):
                low_price = recent_data['low'].iloc[i]
                close_price = recent_data['close'].iloc[i]

                # Check if price tested support
                if abs(low_price - support_level) / support_level < 0.02:  # 2% tolerance
                    tests += 1
                    # Check if price bounced (closed above support)
                    if close_price > support_level:
                        bounces += 1

            if tests == 0:
                return 0.5

            bounce_ratio = bounces / tests
            return min(1.0, bounce_ratio)

        except Exception as e:
            self.logger.error(f"Error analyzing bounce strength: {e}")
            return 0.5

    def _calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """Calculate overall trend strength."""
        try:
            if len(df) < 20:
                return 0.5

            # Simple trend strength using moving averages
            ma_20 = df['close'].rolling(window=20).mean().iloc[-1]
            ma_50 = df['close'].rolling(window=50).mean().iloc[-1] if len(df) >= 50 else ma_20

            current_price = df['close'].iloc[-1]

            # Check price position relative to MAs
            ma_score = 0.0
            if current_price > ma_20:
                ma_score += 0.5
            if current_price > ma_50:
                ma_score += 0.5

            # Check MA alignment (bullish if shorter MA above longer MA)
            if ma_20 > ma_50:
                ma_score += 0.3

            return min(1.0, ma_score)

        except Exception as e:
            self.logger.error(f"Error calculating trend strength: {e}")
            return 0.5

    def _generate_pullback_signal(self, pullback_analysis: PullbackAnalysis,
                                market_data: MarketData) -> Optional[DetectionResult]:
        """Generate pullback-based signal."""
        try:
            # Determine signal strength based on pullback analysis
            strength_factors = [
                pullback_analysis.trend_strength * 0.3,
                pullback_analysis.bounce_strength * 0.3,
                (1.0 - min(pullback_analysis.pullback_depth / 50, 1.0)) * 0.2,  # Deeper pullbacks are riskier
                0.2  # Base strength
            ]

            overall_strength = sum(strength_factors)

            if overall_strength >= 0.8:
                signal_strength = SignalStrength.STRONG
            elif overall_strength >= 0.6:
                signal_strength = SignalStrength.MODERATE
            else:
                signal_strength = SignalStrength.WEAK

            # Determine signal type
            signal_type = SignalType.BUY if overall_strength >= 0.6 else SignalType.MODERATE_BUY

            # Calculate confidence
            confidence = overall_strength
            if pullback_analysis.pullback_type == PullbackType.FIBONACCI_PULLBACK and pullback_analysis.fibonacci_level:
                # Fibonacci levels have higher reliability
                if pullback_analysis.fibonacci_level in [0.5, 0.618]:  # Major fib levels
                    confidence *= 1.1

            confidence = min(1.0, confidence)

            # Calculate price targets
            current_price = market_data.get_price()
            price_target = None
            stop_loss = None
            take_profit = None

            if current_price:
                # Conservative price target (recover part of pullback)
                recovery_target = pullback_analysis.pullback_depth * 0.6  # Recover 60% of pullback
                price_target = current_price * (1 + recovery_target / 100)

                # Stop loss below pullback level
                stop_loss = pullback_analysis.pullback_level * 0.98  # 2% below support

                # Take profit at target
                take_profit = price_target

                # Calculate risk/reward ratio
                if stop_loss and take_profit:
                    risk = current_price - stop_loss
                    reward = take_profit - current_price
                    if risk > 0:
                        pullback_analysis.risk_reward_ratio = reward / risk

            # Generate reasoning
            reasoning_parts = []
            if pullback_analysis.pullback_type == PullbackType.FIBONACCI_PULLBACK:
                reasoning_parts.append(f"Fibonacci pullback to {pullback_analysis.fibonacci_level:.1%} level")
            elif pullback_analysis.pullback_type == PullbackType.MA_PULLBACK:
                reasoning_parts.append(f"Pullback to {pullback_analysis.ma_period}-period moving average")
            elif pullback_analysis.pullback_type == PullbackType.SUPPORT_PULLBACK:
                reasoning_parts.append("Pullback to established support level")

            reasoning_parts.append(f"Pullback depth: {pullback_analysis.pullback_depth:.1f}%")

            if pullback_analysis.trend_strength > 0.6:
                reasoning_parts.append("Strong underlying trend supports bounce")

            if pullback_analysis.bounce_strength > 0.7:
                reasoning_parts.append("Historical bounce strength at this level")

            reasoning = ". ".join(reasoning_parts) + "." if reasoning_parts else "Pullback opportunity detected."

            return DetectionResult(
                signal_type=signal_type,
                strength=signal_strength,
                confidence=confidence,
                price_target=price_target,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reasoning=reasoning,
                key_indicators={
                    'pullback_depth': pullback_analysis.pullback_depth,
                    'trend_strength': pullback_analysis.trend_strength,
                    'bounce_strength': pullback_analysis.bounce_strength,
                    'risk_reward_ratio': pullback_analysis.risk_reward_ratio or 0.0
                },
                metadata={
                    'pullback_type': pullback_analysis.pullback_type.value,
                    'pullback_level': pullback_analysis.pullback_level,
                    'fibonacci_level': pullback_analysis.fibonacci_level,
                    'ma_period': pullback_analysis.ma_period
                }
            )

        except Exception as e:
            self.logger.error(f"Error generating pullback signal: {e}")
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

    async def calculate_pullback_depth(self, market_data: MarketData) -> float:
        """
        Calculate current pullback depth.

        Args:
            market_data: Market data to analyze

        Returns:
            Pullback depth as percentage
        """
        try:
            df = self._market_data_to_dataframe(market_data)
            if df is None or len(df) < 20:
                return 0.0

            recent_high = df['high'].tail(20).max()
            current_price = df['close'].iloc[-1]

            pullback_depth = (recent_high - current_price) / recent_high * 100
            return max(0.0, pullback_depth)

        except Exception as e:
            self.logger.error(f"Error calculating pullback depth: {e}")
            return 0.0