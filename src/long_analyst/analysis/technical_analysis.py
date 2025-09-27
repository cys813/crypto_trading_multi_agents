"""
Technical Analysis Engine optimized for long signals.

This module provides comprehensive technical analysis capabilities specifically
designed for identifying and evaluating long trading opportunities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from enum import Enum

from ..models.market_data import MarketData, OHLCVData, Timeframe
from ..models.analysis_result import AnalysisResult, AnalysisDimension, AnalysisStatus, TechnicalIndicators, AnalysisMetric
from ..utils.indicators import IndicatorCalculator
from ..utils.pattern_recognition import PatternRecognizer


class SignalStrength(Enum):
    """Signal strength levels."""
    WEAK = 0.3
    MODERATE = 0.5
    STRONG = 0.7
    VERY_STRONG = 0.9


class TrendDirection(Enum):
    """Trend direction enumeration."""
    STRONG_UPTREND = "strong_uptrend"
    UPTREND = "uptrend"
    SIDEWAYS = "sideways"
    DOWNTREND = "downtrend"
    STRONG_DOWNTREND = "strong_downtrend"


@dataclass
class TechnicalSignal:
    """Technical trading signal."""
    signal_type: str
    strength: float
    confidence: float
    description: str
    indicators: Dict[str, float]
    timeframe: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class TechnicalAnalysisEngine:
    """
    Advanced technical analysis engine optimized for long signals.

    This engine provides comprehensive technical analysis with focus on
    identifying strong long opportunities through multiple indicators and patterns.
    """

    def __init__(self):
        """Initialize the technical analysis engine."""
        self.logger = logging.getLogger(__name__)
        self.indicator_calculator = IndicatorCalculator()
        self.pattern_recognizer = PatternRecognizer()

        # Configuration for long signal optimization
        self.long_signal_weights = {
            "trend_strength": 0.25,
            "momentum_confirmation": 0.20,
            "volume_confirmation": 0.15,
            "support_resistance": 0.15,
            "pattern_recognition": 0.15,
            "risk_metrics": 0.10
        }

        # Minimum thresholds for long signals
        self.min_rsi = 30.0
        self.max_rsi = 70.0
        self.min_volume_ratio = 1.2
        self.min_trend_strength = 0.6

    async def analyze(self, market_data: MarketData) -> AnalysisResult:
        """
        Perform comprehensive technical analysis.

        Args:
            market_data: Market data to analyze

        Returns:
            Analysis result with technical indicators and signals
        """
        try:
            start_time = asyncio.get_event_loop().time()

            # Validate input data
            if not market_data.ohlcv_data or len(market_data.ohlcv_data) < 50:
                raise ValueError("Insufficient OHLCV data for technical analysis")

            # Convert to DataFrame for analysis
            df = self._prepare_dataframe(market_data.ohlcv_data)

            # Calculate technical indicators
            indicators = await self._calculate_all_indicators(df)

            # Analyze trends and patterns
            trend_analysis = self._analyze_trend(df, indicators)
            momentum_analysis = self._analyze_momentum(df, indicators)
            volume_analysis = self._analyze_volume(df, indicators)
            pattern_analysis = await self._analyze_patterns(df, indicators)

            # Generate long signals
            long_signals = self._generate_long_signals(
                trend_analysis, momentum_analysis, volume_analysis, pattern_analysis
            )

            # Calculate overall technical score
            technical_score = self._calculate_technical_score(
                trend_analysis, momentum_analysis, volume_analysis, pattern_analysis
            )

            # Create analysis result
            result = AnalysisResult(
                symbol=market_data.symbol,
                dimension=AnalysisDimension.TECHNICAL,
                technical_indicators=indicators,
                status=AnalysisStatus.COMPLETED,
                confidence=self._calculate_confidence(trend_analysis, momentum_analysis, volume_analysis),
                score=technical_score,
                timeframe=market_data.timeframe.value if market_data.timeframe else "1h",
                analysis_duration=(asyncio.get_event_loop().time() - start_time)
            )

            # Add metrics and signals
            for signal in long_signals:
                result.add_metric(
                    name=signal.signal_type,
                    value=signal.strength,
                    weight=self.long_signal_weights.get(signal.signal_type, 0.1),
                    confidence=signal.confidence,
                    description=signal.description
                )

            result.signals = [signal.signal_type for signal in long_signals if signal.strength > 0.5]

            self.logger.info(f"Technical analysis completed for {market_data.symbol}: score={technical_score:.2f}")
            return result

        except Exception as e:
            self.logger.error(f"Technical analysis failed for {market_data.symbol}: {e}")
            return AnalysisResult(
                symbol=market_data.symbol,
                dimension=AnalysisDimension.TECHNICAL,
                status=AnalysisStatus.FAILED,
                error_message=str(e)
            )

    def _prepare_dataframe(self, ohlcv_data: List[OHLCVData]) -> pd.DataFrame:
        """Convert OHLCV data to pandas DataFrame."""
        data = []
        for ohlcv in ohlcv_data:
            data.append({
                'timestamp': ohlcv.timestamp,
                'open': ohlcv.open,
                'high': ohlcv.high,
                'low': ohlcv.low,
                'close': ohlcv.close,
                'volume': ohlcv.volume
            })

        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('timestamp', inplace=True)
        return df

    async def _calculate_all_indicators(self, df: pd.DataFrame) -> TechnicalIndicators:
        """Calculate all technical indicators."""
        indicators = TechnicalIndicators()

        # Trend indicators
        indicators.sma_20 = self.indicator_calculator.sma(df['close'], 20)
        indicators.sma_50 = self.indicator_calculator.sma(df['close'], 50)
        indicators.sma_200 = self.indicator_calculator.sma(df['close'], 200)
        indicators.ema_12 = self.indicator_calculator.ema(df['close'], 12)
        indicators.ema_26 = self.indicator_calculator.ema(df['close'], 26)

        # Momentum indicators
        indicators.rsi = self.indicator_calculator.rsi(df['close'], 14)
        macd_data = self.indicator_calculator.macd(df['close'])
        indicators.macd_line = macd_data['macd']
        indicators.macd_signal = macd_data['signal']
        indicators.macd_histogram = macd_data['histogram']
        stochastic_data = self.indicator_calculator.stochastic(df)
        indicators.stochastic_k = stochastic_data['k']
        indicators.stochastic_d = stochastic_data['d']

        # Volatility indicators
        bollinger_data = self.indicator_calculator.bollinger_bands(df['close'])
        indicators.bollinger_upper = bollinger_data['upper']
        indicators.bollinger_middle = bollinger_data['middle']
        indicators.bollinger_lower = bollinger_data['lower']
        indicators.atr = self.indicator_calculator.atr(df)
        indicators.standard_deviation = df['close'].rolling(window=20).std()

        # Volume indicators
        indicators.volume_sma = self.indicator_calculator.sma(df['volume'], 20)
        indicators.on_balance_volume = self.indicator_calculator.obv(df)
        indicators.money_flow_index = self.indicator_calculator.mfi(df)

        # Support and resistance levels
        support_resistance = self.indicator_calculator.support_resistance(df)
        indicators.support_levels = support_resistance['support']
        indicators.resistance_levels = support_resistance['resistance']

        return indicators

    def _analyze_trend(self, df: pd.DataFrame, indicators: TechnicalIndicators) -> Dict[str, Any]:
        """Analyze trend conditions."""
        current_price = df['close'].iloc[-1]
        sma_20 = indicators.sma_20.iloc[-1] if indicators.sma_20 is not None else None
        sma_50 = indicators.sma_50.iloc[-1] if indicators.sma_50 is not None else None
        sma_200 = indicators.sma_200.iloc[-1] if indicators.sma_200 is not None else None

        # Calculate trend strength
        trend_strength = 0.0
        trend_signals = []

        # Price vs SMAs
        if sma_20 and current_price > sma_20:
            trend_strength += 0.2
            trend_signals.append("price_above_sma20")

        if sma_50 and current_price > sma_50:
            trend_strength += 0.2
            trend_signals.append("price_above_sma50")

        if sma_200 and current_price > sma_200:
            trend_strength += 0.3
            trend_signals.append("price_above_sma200")

        # SMA alignment (golden cross pattern)
        if sma_20 and sma_50 and sma_200:
            if sma_20 > sma_50 > sma_200:
                trend_strength += 0.3
                trend_signals.append("sma_alignment_bullish")

        # Determine trend direction
        if trend_strength >= 0.8:
            trend_direction = TrendDirection.STRONG_UPTREND
        elif trend_strength >= 0.5:
            trend_direction = TrendDirection.UPTREND
        elif trend_strength >= 0.2:
            trend_direction = TrendDirection.SIDEWAYS
        else:
            trend_direction = TrendDirection.DOWNTREND

        return {
            "direction": trend_direction,
            "strength": trend_strength,
            "signals": trend_signals,
            "current_price": current_price,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "sma_200": sma_200
        }

    def _analyze_momentum(self, df: pd.DataFrame, indicators: TechnicalIndicators) -> Dict[str, Any]:
        """Analyze momentum conditions."""
        current_rsi = indicators.rsi.iloc[-1] if indicators.rsi is not None else 50
        current_macd = indicators.macd_line.iloc[-1] if indicators.macd_line is not None else 0
        current_macd_signal = indicators.macd_signal.iloc[-1] if indicators.macd_signal is not None else 0
        current_stoch_k = indicators.stochastic_k.iloc[-1] if indicators.stochastic_k is not None else 50

        momentum_score = 0.0
        momentum_signals = []

        # RSI analysis (optimized for long signals)
        if self.min_rsi <= current_rsi <= 60:  # Sweet spot for long entries
            momentum_score += 0.3
            momentum_signals.append("rsi_optimal_long")
        elif current_rsi < self.min_rsi:  # Oversold
            momentum_score += 0.2
            momentum_signals.append("rsi_oversold")

        # MACD analysis
        if current_macd > current_macd_signal:
            momentum_score += 0.3
            momentum_signals.append("macd_bullish")
        if current_macd > 0:  # MACD above zero line
            momentum_score += 0.2
            momentum_signals.append("macd_positive")

        # Stochastic analysis
        if current_stoch_k < 30:  # Oversold
            momentum_score += 0.2
            momentum_signals.append("stochastic_oversold")

        # MACD histogram momentum
        if indicators.macd_histogram is not None:
            hist_current = indicators.macd_histogram.iloc[-1]
            hist_prev = indicators.macd_histogram.iloc[-2]
            if hist_current > hist_prev:
                momentum_score += 0.1
                momentum_signals.append("macd_histogram_increasing")

        return {
            "score": momentum_score,
            "signals": momentum_signals,
            "rsi": current_rsi,
            "macd": current_macd,
            "macd_signal": current_macd_signal,
            "stochastic_k": current_stoch_k
        }

    def _analyze_volume(self, df: pd.DataFrame, indicators: TechnicalIndicators) -> Dict[str, Any]:
        """Analyze volume conditions."""
        current_volume = df['volume'].iloc[-1]
        avg_volume = indicators.volume_sma.iloc[-1] if indicators.volume_sma is not None else current_volume

        volume_score = 0.0
        volume_signals = []

        # Volume ratio analysis
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

        if volume_ratio >= self.min_volume_ratio:
            volume_score += 0.4
            volume_signals.append("volume_above_average")

        if volume_ratio >= 2.0:  # High volume
            volume_score += 0.3
            volume_signals.append("high_volume")

        # Volume trend analysis
        if indicators.on_balance_volume is not None:
            obv_trend = indicators.on_balance_volume.diff().iloc[-5:].mean()
            if obv_trend > 0:
                volume_score += 0.3
                volume_signals.append("obv_increasing")

        # Money Flow Index analysis
        if indicators.money_flow_index is not None:
            mfi_current = indicators.money_flow_index.iloc[-1]
            if mfi_current < 30:  # Oversold
                volume_score += 0.2
                volume_signals.append("mfi_oversold")

        return {
            "score": volume_score,
            "signals": volume_signals,
            "volume_ratio": volume_ratio,
            "current_volume": current_volume,
            "average_volume": avg_volume
        }

    async def _analyze_patterns(self, df: pd.DataFrame, indicators: TechnicalIndicators) -> Dict[str, Any]:
        """Analyze chart patterns."""
        patterns = await self.pattern_recognizer.detect_patterns(df)

        pattern_score = 0.0
        bullish_patterns = []
        bearish_patterns = []

        for pattern in patterns:
            if pattern['type'] == 'bullish':
                pattern_score += 0.2
                bullish_patterns.append(pattern['name'])
            elif pattern['type'] == 'bearish':
                pattern_score -= 0.1
                bearish_patterns.append(pattern['name'])

        return {
            "score": max(0, pattern_score),
            "bullish_patterns": bullish_patterns,
            "bearish_patterns": bearish_patterns,
            "all_patterns": patterns
        }

    def _generate_long_signals(self, trend_analysis: Dict, momentum_analysis: Dict,
                               volume_analysis: Dict, pattern_analysis: Dict) -> List[TechnicalSignal]:
        """Generate long trading signals."""
        signals = []

        # Strong trend signal
        if trend_analysis['strength'] >= self.min_trend_strength:
            signals.append(TechnicalSignal(
                signal_type="strong_trend_long",
                strength=trend_analysis['strength'],
                confidence=0.8,
                description=f"Strong uptrend detected with {len(trend_analysis['signals'])} confirmations",
                indicators={"trend_strength": trend_analysis['strength']},
                timeframe="multi"
            ))

        # Momentum reversal signal
        if momentum_analysis['score'] >= 0.5:
            signals.append(TechnicalSignal(
                signal_type="momentum_long",
                strength=momentum_analysis['score'],
                confidence=0.7,
                description=f"Bullish momentum with {len(momentum_analysis['signals'])} indicators",
                indicators={"momentum_score": momentum_analysis['score'], "rsi": momentum_analysis['rsi']},
                timeframe="multi"
            ))

        # Volume confirmation signal
        if volume_analysis['score'] >= 0.5:
            signals.append(TechnicalSignal(
                signal_type="volume_long",
                strength=volume_analysis['score'],
                confidence=0.6,
                description=f"Volume confirmation with ratio {volume_analysis['volume_ratio']:.2f}",
                indicators={"volume_score": volume_analysis['score'], "volume_ratio": volume_analysis['volume_ratio']},
                timeframe="multi"
            ))

        # Pattern-based signal
        if pattern_analysis['score'] >= 0.4:
            signals.append(TechnicalSignal(
                signal_type="pattern_long",
                strength=pattern_analysis['score'],
                confidence=0.6,
                description=f"Bullish patterns detected: {', '.join(pattern_analysis['bullish_patterns'])}",
                indicators={"pattern_score": pattern_analysis['score']},
                timeframe="multi"
            ))

        # Combined signal (high confidence)
        combined_score = (
            trend_analysis['strength'] * self.long_signal_weights['trend_strength'] +
            momentum_analysis['score'] * self.long_signal_weights['momentum_confirmation'] +
            volume_analysis['score'] * self.long_signal_weights['volume_confirmation'] +
            pattern_analysis['score'] * self.long_signal_weights['pattern_recognition']
        )

        if combined_score >= 0.7:
            signals.append(TechnicalSignal(
                signal_type="combined_long",
                strength=combined_score,
                confidence=0.9,
                description="Combined technical analysis signal for long position",
                indicators={
                    "combined_score": combined_score,
                    "trend_score": trend_analysis['strength'],
                    "momentum_score": momentum_analysis['score'],
                    "volume_score": volume_analysis['score'],
                    "pattern_score": pattern_analysis['score']
                },
                timeframe="multi"
            ))

        return signals

    def _calculate_technical_score(self, trend_analysis: Dict, momentum_analysis: Dict,
                                  volume_analysis: Dict, pattern_analysis: Dict) -> float:
        """Calculate overall technical score."""
        return (
            trend_analysis['strength'] * self.long_signal_weights['trend_strength'] +
            momentum_analysis['score'] * self.long_signal_weights['momentum_confirmation'] +
            volume_analysis['score'] * self.long_signal_weights['volume_confirmation'] +
            pattern_analysis['score'] * self.long_signal_weights['pattern_recognition']
        )

    def _calculate_confidence(self, trend_analysis: Dict, momentum_analysis: Dict,
                             volume_analysis: Dict) -> float:
        """Calculate confidence level for the analysis."""
        # Confidence based on signal consistency and data quality
        consistency_score = 1.0

        # Check if signals are aligned
        trend_bullish = trend_analysis['strength'] > 0.5
        momentum_bullish = momentum_analysis['score'] > 0.5
        volume_bullish = volume_analysis['score'] > 0.5

        aligned_signals = sum([trend_bullish, momentum_bullish, volume_bullish])
        total_signals = 3

        if total_signals > 0:
            consistency_score = aligned_signals / total_signals

        # Additional confidence factors
        volume_confidence = min(1.0, volume_analysis.get('volume_ratio', 1.0) / 2.0)

        return (consistency_score * 0.7) + (volume_confidence * 0.3)

    def get_signal_recommendations(self, technical_score: float, signals: List[TechnicalSignal]) -> List[str]:
        """Generate trading recommendations based on technical analysis."""
        recommendations = []

        if technical_score >= 0.8:
            recommendations.append("Strong buy signal - consider opening long position")
        elif technical_score >= 0.6:
            recommendations.append("Moderate buy signal - wait for confirmation")
        elif technical_score >= 0.4:
            recommendations.append("Weak buy signal - monitor for improvement")
        else:
            recommendations.append("No clear buy signal - avoid long positions")

        # Specific recommendations based on signals
        for signal in signals:
            if signal.signal_type == "strong_trend_long" and signal.strength > 0.8:
                recommendations.append("Trend-following strategy recommended")
            elif signal.signal_type == "momentum_long" and signal.strength > 0.7:
                recommendations.append("Momentum strategy with tight stop-loss")
            elif signal.signal_type == "volume_long" and signal.strength > 0.6:
                recommendations.append("Volume breakout strategy")

        return recommendations