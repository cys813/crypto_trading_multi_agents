"""
Report analyzer for analyzing various data and generating insights
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from .models import (
    TechnicalAnalysis,
    FundamentalAnalysis,
    SentimentAnalysis,
    TechnicalIndicator,
    ReportSummary,
    SignalStrength,
    ConfidenceLevel,
    MarketDataPoint
)


class ReportAnalyzer:
    """Report analyzer for analyzing market data and generating insights"""

    def __init__(self):
        """Initialize report analyzer"""
        self.indicator_weights = {
            'rsi': 0.15,
            'macd': 0.20,
            'bollinger': 0.15,
            'volume': 0.10,
            'moving_average': 0.20,
            'stochastic': 0.10,
            'williams': 0.10
        }

    def analyze_technical_indicators(self, technical_data: Dict[str, Any]) -> TechnicalAnalysis:
        """
        Analyze technical indicators

        Args:
            technical_data: Technical indicator data

        Returns:
            Technical analysis summary
        """
        indicators = []

        # Process RSI
        if 'rsi' in technical_data:
            rsi_value = technical_data['rsi']
            rsi_signal = self._get_rsi_signal(rsi_value)
            indicators.append(TechnicalIndicator(
                name='RSI',
                value=rsi_value,
                signal=rsi_signal,
                confidence=self._calculate_rsi_confidence(rsi_value),
                timestamp=datetime.now()
            ))

        # Process MACD
        if 'macd' in technical_data:
            macd_data = technical_data['macd']
            macd_signal = self._get_macd_signal(macd_data)
            indicators.append(TechnicalIndicator(
                name='MACD',
                value=macd_data.get('macd', 0),
                signal=macd_signal,
                confidence=self._calculate_macd_confidence(macd_data),
                timestamp=datetime.now()
            ))

        # Process Bollinger Bands
        if 'bollinger' in technical_data:
            bb_data = technical_data['bollinger']
            bb_signal = self._get_bollinger_signal(bb_data)
            indicators.append(TechnicalIndicator(
                name='Bollinger Bands',
                value=bb_data.get('position', 0),
                signal=bb_signal,
                confidence=self._calculate_bollinger_confidence(bb_data),
                timestamp=datetime.now()
            ))

        # Process Moving Averages
        if 'moving_averages' in technical_data:
            ma_data = technical_data['moving_averages']
            ma_signal = self._get_ma_signal(ma_data)
            indicators.append(TechnicalIndicator(
                name='Moving Averages',
                value=ma_data.get('spread', 0),
                signal=ma_signal,
                confidence=self._calculate_ma_confidence(ma_data),
                timestamp=datetime.now()
            ))

        # Process Volume
        if 'volume' in technical_data:
            volume_data = technical_data['volume']
            volume_signal = self._get_volume_signal(volume_data)
            indicators.append(TechnicalIndicator(
                name='Volume',
                value=volume_data.get('volume_ratio', 0),
                signal=volume_signal,
                confidence=self._calculate_volume_confidence(volume_data),
                timestamp=datetime.now()
            ))

        # Process Stochastic
        if 'stochastic' in technical_data:
            stoch_data = technical_data['stochastic']
            stoch_signal = self._get_stochastic_signal(stoch_data)
            indicators.append(TechnicalIndicator(
                name='Stochastic',
                value=stoch_data.get('k', 0),
                signal=stoch_signal,
                confidence=self._calculate_stochastic_confidence(stoch_data),
                timestamp=datetime.now()
            ))

        # Process Williams %R
        if 'williams' in technical_data:
            williams_data = technical_data['williams']
            williams_signal = self._get_williams_signal(williams_data)
            indicators.append(TechnicalIndicator(
                name='Williams %R',
                value=williams_data.get('williams_r', 0),
                signal=williams_signal,
                confidence=self._calculate_williams_confidence(williams_data),
                timestamp=datetime.now()
            ))

        # Analyze trend
        trend = self._analyze_trend(indicators)

        # Extract support and resistance levels
        support_levels, resistance_levels = self._extract_support_resistance(technical_data)

        # Calculate momentum and volatility
        momentum = self._calculate_momentum(indicators)
        volatility = self._calculate_volatility(technical_data)

        return TechnicalAnalysis(
            trend=trend,
            key_indicators=indicators,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            momentum=momentum,
            volatility=volatility
        )

    def analyze_fundamental_data(self, fundamental_data: Dict[str, Any]) -> FundamentalAnalysis:
        """
        Analyze fundamental data

        Args:
            fundamental_data: Fundamental market data

        Returns:
            Fundamental analysis summary
        """
        return FundamentalAnalysis(
            market_cap=fundamental_data.get('market_cap', 0),
            volume_24h=fundamental_data.get('volume_24h', 0),
            price_change_24h=fundamental_data.get('price_change_24h', 0),
            market_dominance=fundamental_data.get('market_dominance', 0),
            key_metrics=self._extract_key_metrics(fundamental_data)
        )

    def analyze_sentiment_data(self, sentiment_data: Dict[str, Any]) -> SentimentAnalysis:
        """
        Analyze sentiment data

        Args:
            sentiment_data: Sentiment analysis data

        Returns:
            Sentiment analysis summary
        """
        news_sentiment = sentiment_data.get('news_sentiment', 0)
        social_sentiment = sentiment_data.get('social_sentiment', 0)
        market_sentiment = sentiment_data.get('market_sentiment', 0)

        # Calculate overall sentiment
        overall_sentiment = self._calculate_overall_sentiment(news_sentiment, social_sentiment, market_sentiment)

        # Calculate confidence based on data sources
        confidence = self._calculate_sentiment_confidence(sentiment_data)

        return SentimentAnalysis(
            overall_sentiment=overall_sentiment,
            news_sentiment=news_sentiment,
            social_sentiment=social_sentiment,
            market_sentiment=market_sentiment,
            confidence=confidence
        )

    def generate_summary(self, analyses: Dict[str, Any]) -> ReportSummary:
        """
        Generate report summary

        Args:
            analyses: Dictionary containing all analysis results

        Returns:
            Report summary
        """
        # Calculate signal strength
        signal_strength = self._calculate_signal_strength(analyses)

        # Extract key findings
        key_findings = self._extract_key_findings(analyses)

        # Generate main recommendations
        main_recommendations = self._generate_main_recommendations(analyses)

        # Identify primary risks
        primary_risks = self._identify_primary_risks(analyses)

        # Overall assessment
        overall_assessment = self._generate_overall_assessment(analyses)

        # Confidence score
        confidence_score = self._calculate_confidence_score(analyses)

        return ReportSummary(
            signal_strength=signal_strength,
            key_findings=key_findings,
            main_recommendations=main_recommendations,
            primary_risks=primary_risks,
            overall_assessment=overall_assessment,
            confidence_score=confidence_score
        )

    def _get_rsi_signal(self, rsi_value: float) -> str:
        """Get RSI trading signal"""
        if rsi_value < 30:
            return "BUY"
        elif rsi_value > 70:
            return "SELL"
        else:
            return "HOLD"

    def _calculate_rsi_confidence(self, rsi_value: float) -> float:
        """Calculate RSI confidence"""
        if rsi_value < 20 or rsi_value > 80:
            return 0.9
        elif rsi_value < 30 or rsi_value > 70:
            return 0.7
        else:
            return 0.3

    def _get_macd_signal(self, macd_data: Dict[str, float]) -> str:
        """Get MACD trading signal"""
        macd = macd_data.get('macd', 0)
        signal = macd_data.get('signal', 0)
        histogram = macd_data.get('histogram', 0)

        if histogram > 0 and macd > signal:
            return "BUY"
        elif histogram < 0 and macd < signal:
            return "SELL"
        else:
            return "HOLD"

    def _calculate_macd_confidence(self, macd_data: Dict[str, float]) -> float:
        """Calculate MACD confidence"""
        histogram = abs(macd_data.get('histogram', 0))
        return min(histogram / 2.0, 1.0)

    def _get_bollinger_signal(self, bb_data: Dict[str, float]) -> str:
        """Get Bollinger Bands trading signal"""
        position = bb_data.get('position', 0)  # Position within bands (-1 to 1)

        if position < -0.8:
            return "BUY"
        elif position > 0.8:
            return "SELL"
        else:
            return "HOLD"

    def _calculate_bollinger_confidence(self, bb_data: Dict[str, float]) -> float:
        """Calculate Bollinger Bands confidence"""
        position = abs(bb_data.get('position', 0))
        return min(position * 1.25, 1.0)

    def _get_ma_signal(self, ma_data: Dict[str, float]) -> str:
        """Get Moving Average trading signal"""
        spread = ma_data.get('spread', 0)  # Price vs MA spread

        if spread > 0.02:  # Price 2% above MA
            return "BUY"
        elif spread < -0.02:  # Price 2% below MA
            return "SELL"
        else:
            return "HOLD"

    def _calculate_ma_confidence(self, ma_data: Dict[str, float]) -> float:
        """Calculate Moving Average confidence"""
        spread = abs(ma_data.get('spread', 0))
        return min(spread * 25, 1.0)

    def _get_volume_signal(self, volume_data: Dict[str, float]) -> str:
        """Get Volume trading signal"""
        volume_ratio = volume_data.get('volume_ratio', 1.0)

        if volume_ratio > 1.5:
            return "BUY"
        elif volume_ratio < 0.5:
            return "SELL"
        else:
            return "HOLD"

    def _calculate_volume_confidence(self, volume_data: Dict[str, float]) -> float:
        """Calculate Volume confidence"""
        volume_ratio = volume_data.get('volume_ratio', 1.0)
        return min(abs(volume_ratio - 1.0) * 2, 1.0)

    def _get_stochastic_signal(self, stoch_data: Dict[str, float]) -> str:
        """Get Stochastic trading signal"""
        k = stoch_data.get('k', 50)
        d = stoch_data.get('d', 50)

        if k < 20 and d < 20:
            return "BUY"
        elif k > 80 and d > 80:
            return "SELL"
        else:
            return "HOLD"

    def _calculate_stochastic_confidence(self, stoch_data: Dict[str, float]) -> float:
        """Calculate Stochastic confidence"""
        k = stoch_data.get('k', 50)
        return 1.0 - min(abs(k - 50) / 50.0, 1.0)

    def _get_williams_signal(self, williams_data: Dict[str, float]) -> str:
        """Get Williams %R trading signal"""
        williams_r = williams_data.get('williams_r', -50)

        if williams_r < -80:
            return "BUY"
        elif williams_r > -20:
            return "SELL"
        else:
            return "HOLD"

    def _calculate_williams_confidence(self, williams_data: Dict[str, float]) -> float:
        """Calculate Williams %R confidence"""
        williams_r = williams_data.get('williams_r', -50)
        return min(abs(williams_r + 50) / 30.0, 1.0)

    def _analyze_trend(self, indicators: List[TechnicalIndicator]) -> str:
        """Analyze overall trend"""
        buy_signals = sum(1 for ind in indicators if ind.signal == "BUY")
        sell_signals = sum(1 for ind in indicators if ind.signal == "SELL")
        total_signals = len(indicators)

        if total_signals == 0:
            return "NEUTRAL"

        buy_ratio = buy_signals / total_signals
        sell_ratio = sell_signals / total_signals

        if buy_ratio > 0.6:
            return "STRONG_UPTREND"
        elif buy_ratio > 0.4:
            return "UPTREND"
        elif sell_ratio > 0.6:
            return "STRONG_DOWNTREND"
        elif sell_ratio > 0.4:
            return "DOWNTREND"
        else:
            return "SIDEWAYS"

    def _extract_support_resistance(self, technical_data: Dict[str, Any]) -> Tuple[List[float], List[float]]:
        """Extract support and resistance levels"""
        support_levels = []
        resistance_levels = []

        if 'support_resistance' in technical_data:
            sr_data = technical_data['support_resistance']
            support_levels = sr_data.get('support', [])
            resistance_levels = sr_data.get('resistance', [])

        return support_levels, resistance_levels

    def _calculate_momentum(self, indicators: List[TechnicalIndicator]) -> str:
        """Calculate momentum"""
        momentum_score = 0
        count = 0

        for indicator in indicators:
            if indicator.signal == "BUY":
                momentum_score += indicator.confidence
            elif indicator.signal == "SELL":
                momentum_score -= indicator.confidence
            count += 1

        if count == 0:
            return "NEUTRAL"

        avg_momentum = momentum_score / count

        if avg_momentum > 0.5:
            return "STRONG_BULLISH"
        elif avg_momentum > 0.2:
            return "BULLISH"
        elif avg_momentum < -0.5:
            return "STRONG_BEARISH"
        elif avg_momentum < -0.2:
            return "BEARISH"
        else:
            return "NEUTRAL"

    def _calculate_volatility(self, technical_data: Dict[str, Any]) -> float:
        """Calculate volatility"""
        if 'volatility' in technical_data:
            return technical_data['volatility']
        return 0.0

    def _extract_key_metrics(self, fundamental_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract key fundamental metrics"""
        metrics = {}

        # Add common fundamental metrics
        common_metrics = [
            'pe_ratio', 'pb_ratio', 'dividend_yield', 'roe', 'roa',
            'debt_to_equity', 'current_ratio', 'quick_ratio'
        ]

        for metric in common_metrics:
            if metric in fundamental_data:
                metrics[metric] = fundamental_data[metric]

        return metrics

    def _calculate_overall_sentiment(self, news: float, social: float, market: float) -> str:
        """Calculate overall sentiment"""
        avg_sentiment = (news + social + market) / 3

        if avg_sentiment > 0.6:
            return "VERY_BULLISH"
        elif avg_sentiment > 0.3:
            return "BULLISH"
        elif avg_sentiment < -0.6:
            return "VERY_BEARISH"
        elif avg_sentiment < -0.3:
            return "BEARISH"
        else:
            return "NEUTRAL"

    def _calculate_sentiment_confidence(self, sentiment_data: Dict[str, Any]) -> float:
        """Calculate sentiment confidence"""
        data_sources = 0
        total_confidence = 0

        if 'news_sentiment' in sentiment_data:
            data_sources += 1
            total_confidence += 0.8

        if 'social_sentiment' in sentiment_data:
            data_sources += 1
            total_confidence += 0.6

        if 'market_sentiment' in sentiment_data:
            data_sources += 1
            total_confidence += 0.9

        if data_sources == 0:
            return 0.0

        return total_confidence / data_sources

    def _calculate_signal_strength(self, analyses: Dict[str, Any]) -> SignalStrength:
        """Calculate overall signal strength"""
        technical_score = 0
        fundamental_score = 0
        sentiment_score = 0

        # Calculate technical score
        if 'technical_analysis' in analyses:
            tech_analysis = analyses['technical_analysis']
            buy_signals = sum(1 for ind in tech_analysis.key_indicators if ind.signal == "BUY")
            total_signals = len(tech_analysis.key_indicators)
            if total_signals > 0:
                technical_score = (buy_signals / total_signals) * 10

        # Calculate fundamental score
        if 'fundamental_analysis' in analyses:
            fund_analysis = analyses['fundamental_analysis']
            # Simple scoring based on price change and volume
            if fund_analysis.price_change_24h > 0:
                fundamental_score = min(abs(fund_analysis.price_change_24h) * 10, 10)
            else:
                fundamental_score = 0

        # Calculate sentiment score
        if 'sentiment_analysis' in analyses:
            sent_analysis = analyses['sentiment_analysis']
            sentiment_score = (sent_analysis.news_sentiment + sent_analysis.social_sentiment + sent_analysis.market_sentiment) * 5

        # Calculate overall score
        overall_score = (technical_score + fundamental_score + sentiment_score) / 3
        overall_score = max(0, min(10, overall_score))

        # Determine confidence level
        if overall_score >= 8:
            confidence = ConfidenceLevel.VERY_HIGH
        elif overall_score >= 6:
            confidence = ConfidenceLevel.HIGH
        elif overall_score >= 4:
            confidence = ConfidenceLevel.MEDIUM
        elif overall_score >= 2:
            confidence = ConfidenceLevel.LOW
        else:
            confidence = ConfidenceLevel.VERY_LOW

        return SignalStrength(
            overall_score=overall_score,
            technical_score=technical_score,
            fundamental_score=fundamental_score,
            sentiment_score=sentiment_score,
            confidence=confidence
        )

    def _extract_key_findings(self, analyses: Dict[str, Any]) -> List[str]:
        """Extract key findings from analyses"""
        findings = []

        if 'technical_analysis' in analyses:
            tech_analysis = analyses['technical_analysis']
            findings.append(f"技术趋势: {tech_analysis.trend}")
            findings.append(f"动量: {tech_analysis.momentum}")
            findings.append(f"波动率: {tech_analysis.volatility:.2%}")

        if 'fundamental_analysis' in analyses:
            fund_analysis = analyses['fundamental_analysis']
            findings.append(f"24小时涨跌: {fund_analysis.price_change_24h:.2%}")
            findings.append(f"24小时成交量: ${fund_analysis.volume_24h:,.0f}")

        if 'sentiment_analysis' in analyses:
            sent_analysis = analyses['sentiment_analysis']
            findings.append(f"市场情绪: {sent_analysis.overall_sentiment}")

        return findings

    def _generate_main_recommendations(self, analyses: Dict[str, Any]) -> List[str]:
        """Generate main recommendations"""
        recommendations = []

        if 'technical_analysis' in analyses:
            tech_analysis = analyses['technical_analysis']
            if "UPTREND" in tech_analysis.trend:
                recommendations.append("技术面显示上涨趋势，建议考虑做多")
            elif "DOWNTREND" in tech_analysis.trend:
                recommendations.append("技术面显示下跌趋势，建议谨慎观望")

        if 'sentiment_analysis' in analyses:
            sent_analysis = analyses['sentiment_analysis']
            if "BULLISH" in sent_analysis.overall_sentiment:
                recommendations.append("市场情绪积极，支持做多策略")

        return recommendations

    def _identify_primary_risks(self, analyses: Dict[str, Any]) -> List[str]:
        """Identify primary risks"""
        risks = []

        if 'technical_analysis' in analyses:
            tech_analysis = analyses['technical_analysis']
            if tech_analysis.volatility > 0.3:
                risks.append("市场波动率较高，需谨慎管理仓位")

        if 'sentiment_analysis' in analyses:
            sent_analysis = analyses['sentiment_analysis']
            if sent_analysis.confidence < 0.5:
                risks.append("情绪分析置信度较低，建议结合其他指标")

        risks.append("市场存在突发性风险，建议设置止损")
        risks.append("加密货币市场风险较高，投资需谨慎")

        return risks

    def _generate_overall_assessment(self, analyses: Dict[str, Any]) -> str:
        """Generate overall assessment"""
        signal_strength = self._calculate_signal_strength(analyses)

        if signal_strength.overall_score >= 7:
            return "强烈做多信号，技术面、基本面和情绪面均支持做多策略"
        elif signal_strength.overall_score >= 5:
            return "中等做多信号，部分指标支持做多，需结合风险管理"
        elif signal_strength.overall_score >= 3:
            return "弱做多信号，建议观望或谨慎建仓"
        else:
            return "无明显做多信号，建议观望或考虑其他策略"

    def _calculate_confidence_score(self, analyses: Dict[str, Any]) -> float:
        """Calculate overall confidence score"""
        scores = []

        # Technical confidence
        if 'technical_analysis' in analyses:
            tech_analysis = analyses['technical_analysis']
            if tech_analysis.key_indicators:
                avg_confidence = sum(ind.confidence for ind in tech_analysis.key_indicators) / len(tech_analysis.key_indicators)
                scores.append(avg_confidence)

        # Fundamental confidence
        if 'fundamental_analysis' in analyses:
            scores.append(0.7)  # Fundamental data is generally reliable

        # Sentiment confidence
        if 'sentiment_analysis' in analyses:
            sent_analysis = analyses['sentiment_analysis']
            scores.append(sent_analysis.confidence)

        if not scores:
            return 0.0

        return sum(scores) / len(scores)