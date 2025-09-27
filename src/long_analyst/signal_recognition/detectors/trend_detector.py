"""
Trend Detection Algorithms for Long Analyst Agent.

Specialized algorithms for detecting uptrends, momentum confirmation,
and trend strength analysis optimized for long trading opportunities.
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


class TrendState(Enum):
    """Trend state enumeration."""
    STRONG_UPTREND = "strong_uptrend"
    UPTREND = "uptrend"
    NEUTRAL = "neutral"
    DOWNTREND = "downtrend"
    STRONG_DOWNTREND = "strong_downtrend"


@dataclass
class TrendAnalysis:
    """Result of trend analysis."""
    state: TrendState
    strength: float  # 0.0 to 1.0
    momentum: float  # -1.0 to 1.0
    higher_highs: bool
    higher_lows: bool
    adx_value: Optional[float] = None
    ma_alignment: float = 0.0  # -1.0 to 1.0
    price_above_ma: bool = False
    volume_confirmation: bool = False
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}


class TrendDetector(SignalDetector):
    """
    Advanced trend detection algorithm for long trading opportunities.

    This detector identifies uptrends using multiple methods including
    higher highs/lows analysis, moving average alignment, ADX, and
    volume confirmation.
    """

    def __init__(self, config: DetectorConfig):
        """Initialize the trend detector."""
        super().__init__(config)
        self.min_period = config.parameters.get('min_period', 20)
        self.strength_threshold = config.parameters.get('strength_threshold', 0.6)
        self.require_volume = config.parameters.get('require_volume', True)
        self.min_volume_ratio = config.parameters.get('min_volume_ratio', 1.2)

        # Moving average periods for trend analysis
        self.ma_periods = [10, 20, 50, 200]

    def get_required_indicators(self) -> List[str]:
        """Get required technical indicators."""
        return ['sma', 'ema', 'adx', 'rsi', 'macd', 'volume_profile']

    async def detect(self, market_data: MarketData) -> List[DetectionResult]:
        """
        Detect trend-based signals.

        Args:
            market_data: Market data to analyze

        Returns:
            List of detection results
        """
        try:
            # Convert market data to DataFrame
            df = self._market_data_to_dataframe(market_data)
            if df is None or len(df) < self.min_period:
                return []

            # Perform comprehensive trend analysis
            trend_analysis = await self._analyze_trend(df)

            # Generate signals based on trend analysis
            signals = []
            if self._is_uptrend(trend_analysis):
                signal_result = self._generate_trend_signal(trend_analysis, market_data)
                if signal_result:
                    signals.append(signal_result)

            return signals

        except Exception as e:
            self.logger.error(f"Error in trend detection: {e}")
            return []

    async def _analyze_trend(self, df: pd.DataFrame) -> TrendAnalysis:
        """Perform comprehensive trend analysis."""
        # Higher highs and higher lows analysis
        higher_highs, higher_lows = self._analyze_price_structure(df)

        # Moving average analysis
        ma_alignment, price_above_ma = self._analyze_moving_averages(df)

        # Momentum analysis
        momentum = self._analyze_momentum(df)

        # Trend strength using ADX
        adx_value = self._calculate_adx(df)

        # Volume confirmation
        volume_confirmation = self._confirm_volume_trend(df)

        # Determine overall trend state
        trend_state = self._determine_trend_state(
            higher_highs, higher_lows, ma_alignment, momentum, adx_value
        )

        # Calculate overall trend strength
        strength = self._calculate_trend_strength(
            trend_state, ma_alignment, momentum, adx_value, volume_confirmation
        )

        return TrendAnalysis(
            state=trend_state,
            strength=strength,
            momentum=momentum,
            higher_highs=higher_highs,
            higher_lows=higher_lows,
            adx_value=adx_value,
            ma_alignment=ma_alignment,
            price_above_ma=price_above_ma,
            volume_confirmation=volume_confirmation,
            metadata={
                'analysis_time': datetime.now().isoformat(),
                'data_points': len(df),
                'ma_periods': self.ma_periods
            }
        )

    def _analyze_price_structure(self, df: pd.DataFrame) -> Tuple[bool, bool]:
        """Analyze price structure for higher highs and higher lows."""
        if len(df) < 5:
            return False, False

        # Get recent highs and lows
        recent_highs = df['high'].rolling(window=5, center=True).max()
        recent_lows = df['low'].rolling(window=5, center=True).min()

        # Check for higher highs
        higher_highs = False
        if len(recent_highs) >= 3:
            higher_highs = (
                recent_highs.iloc[-1] > recent_highs.iloc[-2] and
                recent_highs.iloc[-2] > recent_highs.iloc[-3]
            )

        # Check for higher lows
        higher_lows = False
        if len(recent_lows) >= 3:
            higher_lows = (
                recent_lows.iloc[-1] > recent_lows.iloc[-2] and
                recent_lows.iloc[-2] > recent_lows.iloc[-3]
            )

        return higher_highs, higher_lows

    def _analyze_moving_averages(self, df: pd.DataFrame) -> Tuple[float, bool]:
        """Analyze moving average alignment and price position."""
        ma_values = {}
        price_above_ma_count = 0

        for period in self.ma_periods:
            if len(df) >= period:
                ma = df['close'].rolling(window=period).mean()
                ma_values[period] = ma.iloc[-1]

                # Check if price is above MA
                if df['close'].iloc[-1] > ma.iloc[-1]:
                    price_above_ma_count += 1

        # Calculate MA alignment score
        alignment_score = 0.0
        if len(ma_values) >= 2:
            # Check if shorter MAs are above longer MAs (bullish alignment)
            ma_periods_sorted = sorted(ma_values.keys())
            for i in range(len(ma_periods_sorted) - 1):
                short_period = ma_periods_sorted[i]
                long_period = ma_periods_sorted[i + 1]
                if ma_values[short_period] > ma_values[long_period]:
                    alignment_score += 1.0

            alignment_score /= (len(ma_values) - 1)

        price_above_ma = price_above_ma_count / len(self.ma_periods) > 0.5

        return alignment_score, price_above_ma

    def _analyze_momentum(self, df: pd.DataFrame) -> float:
        """Analyze price momentum."""
        if len(df) < 10:
            return 0.0

        # Rate of change (ROC)
        roc = (df['close'].iloc[-1] / df['close'].iloc[-10] - 1) * 100

        # Simple momentum based on recent price action
        recent_returns = df['close'].pct_change().dropna()
        momentum_score = np.mean(recent_returns.tail(10))

        # Normalize momentum score
        normalized_momentum = np.tanh(momentum_score * 10)  # Normalize to -1, 1

        return normalized_momentum

    def _calculate_adx(self, df: pd.DataFrame) -> Optional[float]:
        """Calculate Average Directional Index (ADX)."""
        try:
            if len(df) < 20:
                return None

            # Calculate True Range
            df['tr'] = np.maximum(
                df['high'] - df['low'],
                np.maximum(
                    abs(df['high'] - df['close'].shift(1)),
                    abs(df['low'] - df['close'].shift(1))
                )
            )

            # Calculate Directional Movement
            df['plus_dm'] = np.where(
                (df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']),
                np.maximum(df['high'] - df['high'].shift(1), 0),
                0
            )

            df['minus_dm'] = np.where(
                (df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)),
                np.maximum(df['low'].shift(1) - df['low'], 0),
                0
            )

            # Calculate Smoothed True Range and Directional Movement
            df['atr'] = df['tr'].rolling(window=14).mean()
            df['plus_di'] = 100 * (df['plus_dm'].rolling(window=14).mean() / df['atr'])
            df['minus_di'] = 100 * (df['minus_dm'].rolling(window=14).mean() / df['atr'])

            # Calculate DX and ADX
            df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
            adx = df['dx'].rolling(window=14).mean()

            return adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else None

        except Exception as e:
            self.logger.error(f"Error calculating ADX: {e}")
            return None

    def _confirm_volume_trend(self, df: pd.DataFrame) -> bool:
        """Confirm trend with volume analysis."""
        if not self.require_volume or 'volume' not in df.columns:
            return True

        try:
            # Calculate volume ratios
            recent_volume = df['volume'].tail(10).mean()
            historical_volume = df['volume'].tail(50).mean()

            if historical_volume > 0:
                volume_ratio = recent_volume / historical_volume
                return volume_ratio >= self.min_volume_ratio

            return False

        except Exception as e:
            self.logger.error(f"Error in volume confirmation: {e}")
            return False

    def _determine_trend_state(self, higher_highs: bool, higher_lows: bool,
                             ma_alignment: float, momentum: float,
                             adx_value: Optional[float]) -> TrendState:
        """Determine overall trend state."""
        # Strong uptrend conditions
        if (higher_highs and higher_lows and
            ma_alignment > 0.7 and momentum > 0.3 and
            (adx_value is None or adx_value > 25)):
            return TrendState.STRONG_UPTREND

        # Uptrend conditions
        elif ((higher_highs or higher_lows) and
              ma_alignment > 0.3 and momentum > 0.1 and
              (adx_value is None or adx_value > 20)):
            return TrendState.UPTREND

        # Downtrend conditions
        elif (ma_alignment < -0.3 and momentum < -0.1 and
              (adx_value is None or adx_value > 20)):
            return TrendState.DOWNTREND

        # Strong downtrend conditions
        elif (ma_alignment < -0.7 and momentum < -0.3 and
              (adx_value is None or adx_value > 25)):
            return TrendState.STRONG_DOWNTREND

        # Default to neutral
        else:
            return TrendState.NEUTRAL

    def _calculate_trend_strength(self, trend_state: TrendState, ma_alignment: float,
                               momentum: float, adx_value: Optional[float],
                               volume_confirmation: bool) -> float:
        """Calculate overall trend strength."""
        strength = 0.0

        # Base strength from trend state
        state_strength = {
            TrendState.STRONG_UPTREND: 0.9,
            TrendState.UPTREND: 0.7,
            TrendState.NEUTRAL: 0.5,
            TrendState.DOWNTREND: 0.3,
            TrendState.STRONG_DOWNTREND: 0.1
        }
        strength += state_strength.get(trend_state, 0.5)

        # Add MA alignment contribution
        if ma_alignment > 0:  # Bullish alignment
            strength += ma_alignment * 0.2

        # Add momentum contribution
        if momentum > 0:  # Positive momentum
            strength += momentum * 0.2

        # Add ADX contribution
        if adx_value is not None:
            adx_contribution = min(adx_value / 50, 1.0) * 0.2
            strength += adx_contribution

        # Volume confirmation bonus
        if volume_confirmation:
            strength += 0.1

        return min(1.0, max(0.0, strength))

    def _is_uptrend(self, trend_analysis: TrendAnalysis) -> bool:
        """Check if trend analysis indicates an uptrend."""
        return (trend_analysis.state in [TrendState.STRONG_UPTREND, TrendState.UPTREND] and
                trend_analysis.strength >= self.strength_threshold)

    def _generate_trend_signal(self, trend_analysis: TrendAnalysis,
                             market_data: MarketData) -> Optional[DetectionResult]:
        """Generate trend-based signal."""
        try:
            # Determine signal type and strength based on trend analysis
            if trend_analysis.state == TrendState.STRONG_UPTREND:
                signal_type = SignalType.STRONG_BUY
                signal_strength = SignalStrength.VERY_STRONG
            elif trend_analysis.state == TrendState.UPTREND:
                signal_type = SignalType.BUY
                signal_strength = SignalStrength.STRONG
            else:
                return None

            # Calculate confidence
            confidence = trend_analysis.strength

            # Calculate price targets
            current_price = market_data.get_price()
            price_target = None
            stop_loss = None
            take_profit = None

            if current_price:
                # Conservative price target based on trend strength
                expected_return = trend_analysis.strength * 0.1  # 1-10% expected return
                price_target = current_price * (1 + expected_return)

                # Stop loss at 2% below current price
                stop_loss = current_price * 0.98

                # Take profit at 2x expected return
                take_profit = current_price * (1 + expected_return * 2)

            # Generate reasoning
            reasoning_parts = []
            if trend_analysis.higher_highs and trend_analysis.higher_lows:
                reasoning_parts.append("Strong price structure with higher highs and higher lows")

            if trend_analysis.ma_alignment > 0.5:
                reasoning_parts.append("Bullish moving average alignment")

            if trend_analysis.momentum > 0.2:
                reasoning_parts.append("Positive price momentum")

            if trend_analysis.volume_confirmation:
                reasoning_parts.append("Volume confirms the trend")

            if trend_analysis.adx_value and trend_analysis.adx_value > 25:
                reasoning_parts.append(f"Strong trend strength (ADX: {trend_analysis.adx_value:.1f})")

            reasoning = ". ".join(reasoning_parts) + "." if reasoning_parts else "Uptrend detected."

            return DetectionResult(
                signal_type=signal_type,
                strength=signal_strength,
                confidence=confidence,
                price_target=price_target,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reasoning=reasoning,
                key_indicators={
                    'trend_strength': trend_analysis.strength,
                    'momentum': trend_analysis.momentum,
                    'ma_alignment': trend_analysis.ma_alignment,
                    'adx': trend_analysis.adx_value or 0.0
                },
                metadata={
                    'trend_state': trend_analysis.state.value,
                    'higher_highs': trend_analysis.higher_highs,
                    'higher_lows': trend_analysis.higher_lows,
                    'volume_confirmation': trend_analysis.volume_confirmation
                }
            )

        except Exception as e:
            self.logger.error(f"Error generating trend signal: {e}")
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

    async def detect_trend_strength(self, market_data: MarketData) -> float:
        """
        Detect trend strength without generating signals.

        Args:
            market_data: Market data to analyze

        Returns:
            Trend strength between 0.0 and 1.0
        """
        try:
            df = self._market_data_to_dataframe(market_data)
            if df is None or len(df) < self.min_period:
                return 0.0

            trend_analysis = await self._analyze_trend(df)
            return trend_analysis.strength

        except Exception as e:
            self.logger.error(f"Error detecting trend strength: {e}")
            return 0.0