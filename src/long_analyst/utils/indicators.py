"""
Technical indicator calculations for the Long Analyst Agent.

Provides comprehensive technical indicator calculations optimized
for long signal identification and evaluation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import logging


class IndicatorCalculator:
    """
    Comprehensive technical indicator calculator.

    This class provides optimized calculations for various technical
    indicators commonly used in cryptocurrency trading analysis.
    """

    def __init__(self):
        """Initialize the indicator calculator."""
        self.logger = logging.getLogger(__name__)

    def sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average."""
        return prices.rolling(window=period).mean()

    def ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return prices.ewm(span=period, adjust=False).mean()

    def rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        ema_fast = self.ema(prices, fast)
        ema_slow = self.ema(prices, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self.ema(macd_line, signal)
        histogram = macd_line - signal_line

        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }

    def bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands."""
        middle_band = self.sma(prices, period)
        std = prices.rolling(window=period).std()
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)

        return {
            'upper': upper_band,
            'middle': middle_band,
            'lower': lower_band,
            'width': upper_band - lower_band
        }

    def stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Calculate Stochastic Oscillator."""
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        k_percent = 100 * ((df['close'] - low_min) / (high_max - low_min))
        d_percent = k_percent.rolling(window=d_period).mean()

        return {
            'k': k_percent,
            'd': d_percent
        }

    def atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr

    def adx(self, df: pd.DataFrame, period: int = 14) -> Dict[str, pd.Series]:
        """Calculate Average Directional Index."""
        high_diff = df['high'].diff()
        low_diff = df['low'].diff()

        plus_dm = np.where((high_diff > 0) & (high_diff > low_diff), high_diff, 0)
        minus_dm = np.where((low_diff > 0) & (low_diff > high_diff), low_diff, 0)

        plus_dm = pd.Series(plus_dm, index=df.index).rolling(window=period).mean()
        minus_dm = pd.Series(minus_dm, index=df.index).rolling(window=period).mean()

        atr_values = self.atr(df, period)

        plus_di = 100 * (plus_dm / atr_values)
        minus_di = 100 * (minus_dm / atr_values)

        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        return {
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di
        }

    def cci(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculate Commodity Channel Index."""
        tp = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: np.fabs(x - x.mean()).mean())
        cci = (tp - sma_tp) / (0.015 * mad)
        return cci

    def williams_r(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Williams %R."""
        highest_high = df['high'].rolling(window=period).max()
        lowest_low = df['low'].rolling(window=period).min()
        williams_r = -100 * (highest_high - df['close']) / (highest_high - lowest_low)
        return williams_r

    def obv(self, df: pd.DataFrame) -> pd.Series:
        """Calculate On-Balance Volume."""
        obv = np.where(df['close'] > df['close'].shift(), df['volume'],
                      np.where(df['close'] < df['close'].shift(), -df['volume'], 0))
        return pd.Series(obv, index=df.index).cumsum()

    def mfi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Money Flow Index."""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        money_flow = typical_price * df['volume']

        positive_flow = np.where(typical_price > typical_price.shift(), money_flow, 0)
        negative_flow = np.where(typical_price < typical_price.shift(), money_flow, 0)

        positive_mf = pd.Series(positive_flow, index=df.index).rolling(window=period).sum()
        negative_mf = pd.Series(negative_flow, index=df.index).rolling(window=period).sum()

        money_ratio = positive_mf / negative_mf
        mfi = 100 - (100 / (1 + money_ratio))

        return mfi

    def vwap(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Volume Weighted Average Price."""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        return vwap

    def ichimoku(self, df: pd.DataFrame, conversion_periods: int = 9, base_periods: int = 26,
                 lagging_span: int = 26, displacement: int = 26) -> Dict[str, pd.Series]:
        """Calculate Ichimoku Cloud."""
        # Conversion Line (Tenkan-sen)
        conversion_line = (df['high'].rolling(window=conversion_periods).max() +
                          df['low'].rolling(window=conversion_periods).min()) / 2

        # Base Line (Kijun-sen)
        base_line = (df['high'].rolling(window=base_periods).max() +
                    df['low'].rolling(window=base_periods).min()) / 2

        # Leading Span A (Senkou Span A)
        leading_span_a = ((conversion_line + base_line) / 2).shift(displacement)

        # Leading Span B (Senkou Span B)
        leading_span_b = ((df['high'].rolling(window=lagging_span * 2).max() +
                          df['low'].rolling(window=lagging_span * 2).min()) / 2).shift(displacement)

        # Lagging Span (Chikou Span)
        lagging_span = df['close'].shift(-displacement)

        return {
            'conversion_line': conversion_line,
            'base_line': base_line,
            'leading_span_a': leading_span_a,
            'leading_span_b': leading_span_b,
            'lagging_span': lagging_span
        }

    def fibonacci_retracement(self, df: pd.DataFrame, period: int = 100) -> Dict[str, float]:
        """Calculate Fibonacci retracement levels."""
        high = df['high'].rolling(window=period).max().iloc[-1]
        low = df['low'].rolling(window=period).min().iloc[-1]
        diff = high - low

        levels = {
            '0%': high,
            '23.6%': high - (diff * 0.236),
            '38.2%': high - (diff * 0.382),
            '50%': high - (diff * 0.5),
            '61.8%': high - (diff * 0.618),
            '78.6%': high - (diff * 0.786),
            '100%': low
        }

        return levels

    def support_resistance(self, df: pd.DataFrame, window: int = 20, threshold: float = 0.02) -> Dict[str, List[float]]:
        """Calculate support and resistance levels."""
        highs = df['high'].rolling(window=window).max()
        lows = df['low'].rolling(window=window).min()

        # Find resistance levels (local highs)
        resistance_candidates = []
        for i in range(1, len(highs) - 1):
            if highs.iloc[i] >= highs.iloc[i-1] and highs.iloc[i] >= highs.iloc[i+1]:
                resistance_candidates.append(highs.iloc[i])

        # Find support levels (local lows)
        support_candidates = []
        for i in range(1, len(lows) - 1):
            if lows.iloc[i] <= lows.iloc[i-1] and lows.iloc[i] <= lows.iloc[i+1]:
                support_candidates.append(lows.iloc[i])

        # Cluster similar levels
        resistance = self._cluster_levels(resistance_candidates, threshold)
        support = self._cluster_levels(support_candidates, threshold)

        return {
            'resistance': sorted(resistance, reverse=True)[:5],  # Top 5 resistance levels
            'support': sorted(support)[:5]  # Top 5 support levels
        }

    def pivot_points(self, df: pd.DataFrame, method: str = 'standard') -> Dict[str, float]:
        """Calculate pivot points."""
        high = df['high'].iloc[-1]
        low = df['low'].iloc[-1]
        close = df['close'].iloc[-1]

        if method == 'standard':
            pivot = (high + low + close) / 3
            r1 = (2 * pivot) - low
            s1 = (2 * pivot) - high
            r2 = pivot + (high - low)
            s2 = pivot - (high - low)
            r3 = high + 2 * (pivot - low)
            s3 = low - 2 * (high - pivot)

        elif method == 'fibonacci':
            pivot = (high + low + close) / 3
            r1 = pivot + 0.382 * (high - low)
            s1 = pivot - 0.382 * (high - low)
            r2 = pivot + 0.618 * (high - low)
            s2 = pivot - 0.618 * (high - low)
            r3 = pivot + 1.0 * (high - low)
            s3 = pivot - 1.0 * (high - low)

        elif method == 'woodie':
            pivot = (high + low + 2 * close) / 4
            r1 = (2 * pivot) - low
            s1 = (2 * pivot) - high
            r2 = pivot + (high - low)
            s2 = pivot - (high - low)

        else:
            raise ValueError(f"Unknown pivot point method: {method}")

        return {
            'pivot': pivot,
            'r1': r1,
            'r2': r2,
            'r3': r3,
            's1': s1,
            's2': s2,
            's3': s3
        }

    def volume_profile(self, df: pd.DataFrame, bins: int = 50) -> Dict[str, Union[List[float], List[int]]]:
        """Calculate Volume Profile."""
        price_range = df['high'].max() - df['low'].min()
        bin_width = price_range / bins

        price_levels = []
        volume_at_level = []

        for i in range(bins):
            lower_price = df['low'].min() + (i * bin_width)
            upper_price = lower_price + bin_width

            # Filter data for this price range
            mask = (df['close'] >= lower_price) & (df['close'] <= upper_price)
            volume_in_range = df.loc[mask, 'volume'].sum()

            price_levels.append((lower_price + upper_price) / 2)
            volume_at_level.append(volume_in_range)

        return {
            'price_levels': price_levels,
            'volume_at_level': volume_at_level
        }

    def _cluster_levels(self, levels: List[float], threshold: float) -> List[float]:
        """Cluster similar price levels."""
        if not levels:
            return []

        levels.sort()
        clusters = []
        current_cluster = [levels[0]]

        for level in levels[1:]:
            if abs(level - current_cluster[-1]) / current_cluster[-1] <= threshold:
                current_cluster.append(level)
            else:
                clusters.append(np.mean(current_cluster))
                current_cluster = [level]

        clusters.append(np.mean(current_cluster))
        return clusters

    def calculate_all_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate all available indicators for comprehensive analysis."""
        indicators = {}

        # Trend indicators
        indicators['sma_20'] = self.sma(df['close'], 20)
        indicators['sma_50'] = self.sma(df['close'], 50)
        indicators['sma_200'] = self.sma(df['close'], 200)
        indicators['ema_12'] = self.ema(df['close'], 12)
        indicators['ema_26'] = self.ema(df['close'], 26)

        # Momentum indicators
        indicators['rsi'] = self.rsi(df['close'])
        macd_data = self.macd(df['close'])
        indicators.update(macd_data)

        stochastic_data = self.stochastic(df)
        indicators.update(stochastic_data)

        indicators['cci'] = self.cci(df)
        indicators['williams_r'] = self.williams_r(df)

        # Volatility indicators
        bollinger_data = self.bollinger_bands(df['close'])
        indicators.update(bollinger_data)

        indicators['atr'] = self.atr(df)

        adx_data = self.adx(df)
        indicators.update(adx_data)

        # Volume indicators
        indicators['volume_sma'] = self.sma(df['volume'], 20)
        indicators['obv'] = self.obv(df)
        indicators['mfi'] = self.mfi(df)
        indicators['vwap'] = self.vwap(df)

        # Ichimoku cloud
        ichimoku_data = self.ichimoku(df)
        indicators.update(ichimoku_data)

        return indicators

    def get_signal_strength(self, indicators: Dict[str, pd.Series], current_index: int = -1) -> Dict[str, float]:
        """Calculate signal strength based on multiple indicators."""
        if current_index == -1:
            current_index = len(list(indicators.values())[0]) - 1

        signal_strengths = {}

        # RSI signal strength
        if 'rsi' in indicators:
            rsi_value = indicators['rsi'].iloc[current_index]
            if 30 <= rsi_value <= 60:  # Optimal for long entries
                signal_strengths['rsi'] = 0.8
            elif rsi_value < 30:  # Oversold
                signal_strengths['rsi'] = 0.6
            elif rsi_value < 40:  # Slightly oversold
                signal_strengths['rsi'] = 0.4
            else:
                signal_strengths['rsi'] = 0.1

        # MACD signal strength
        if 'macd' in indicators and 'signal' in indicators:
            macd_value = indicators['macd'].iloc[current_index]
            signal_value = indicators['signal'].iloc[current_index]
            histogram_value = indicators['histogram'].iloc[current_index]

            if macd_value > signal_value and histogram_value > 0:
                signal_strengths['macd'] = 0.8
            elif macd_value > signal_value:
                signal_strengths['macd'] = 0.6
            elif histogram_value > 0:
                signal_strengths['macd'] = 0.4
            else:
                signal_strengths['macd'] = 0.1

        # Trend signal strength
        if 'sma_20' in indicators and 'sma_50' in indicators and 'sma_200' in indicators:
            close_price = indicators['sma_20'].iloc[current_index]  # Using close price from SMA calculation
            sma_20 = indicators['sma_20'].iloc[current_index]
            sma_50 = indicators['sma_50'].iloc[current_index]
            sma_200 = indicators['sma_200'].iloc[current_index]

            trend_score = 0
            if close_price > sma_20:
                trend_score += 0.3
            if close_price > sma_50:
                trend_score += 0.3
            if close_price > sma_200:
                trend_score += 0.4

            signal_strengths['trend'] = trend_score

        # Volume signal strength
        if 'volume_sma' in indicators:
            current_volume = indicators['volume_sma'].iloc[current_index]
            avg_volume = indicators['volume_sma'].mean()
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

            if volume_ratio >= 2.0:
                signal_strengths['volume'] = 0.8
            elif volume_ratio >= 1.5:
                signal_strengths['volume'] = 0.6
            elif volume_ratio >= 1.2:
                signal_strengths['volume'] = 0.4
            else:
                signal_strengths['volume'] = 0.1

        return signal_strengths