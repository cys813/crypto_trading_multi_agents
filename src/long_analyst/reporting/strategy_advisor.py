"""
Strategy advisor for generating trading recommendations
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass

from .models import (
    StrategyRecommendation,
    EntryRecommendation,
    RiskManagement,
    ConfidenceLevel
)


class StrategyAdvisor:
    """Strategy advisor for generating trading recommendations"""

    def __init__(self):
        """Initialize strategy advisor"""
        self.risk_per_trade_default = 0.02  # 2% risk per trade
        self.max_position_size = 0.10  # 10% max position size

    async def generate_recommendation(self, analyses: Dict[str, Any], symbol: str, custom_params: Dict[str, Any] = None) -> StrategyRecommendation:
        """
        Generate complete strategy recommendation

        Args:
            analyses: Dictionary containing all analysis results
            symbol: Trading symbol
            custom_params: Custom parameters for recommendation

        Returns:
            Strategy recommendation
        """
        # Determine action (BUY, HOLD, SELL)
        action = self._determine_action(analyses)

        # Generate entry recommendation
        entry_recommendation = await self._generate_entry_recommendation(analyses, symbol)

        # Generate risk management parameters
        risk_management = await self._generate_risk_management(
            analyses, entry_recommendation, custom_params
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(analyses, action)

        # Calculate expected win rate
        expected_win_rate = self._calculate_expected_win_rate(analyses)

        # Determine time horizon
        time_horizon = self._determine_time_horizon(analyses)

        # Calculate confidence
        confidence = self._calculate_confidence(analyses)

        return StrategyRecommendation(
            action=action,
            symbol=symbol,
            entry_recommendation=entry_recommendation,
            risk_management=risk_management,
            reasoning=reasoning,
            expected_win_rate=expected_win_rate,
            time_horizon=time_horizon,
            confidence=confidence
        )

    def _determine_action(self, analyses: Dict[str, Any]) -> str:
        """Determine trading action"""
        buy_signals = 0
        sell_signals = 0
        total_signals = 0

        # Technical analysis signals
        if 'technical_analysis' in analyses:
            tech_analysis = analyses['technical_analysis']
            for indicator in tech_analysis.key_indicators:
                total_signals += 1
                if indicator.signal == "BUY":
                    buy_signals += 1
                elif indicator.signal == "SELL":
                    sell_signals += 1

        # Sentiment analysis signals
        if 'sentiment_analysis' in analyses:
            sent_analysis = analyses['sentiment_analysis']
            total_signals += 1
            if "BULLISH" in sent_analysis.overall_sentiment:
                buy_signals += 1
            elif "BEARISH" in sent_analysis.overall_sentiment:
                sell_signals += 1

        # Fundamental analysis signals
        if 'fundamental_analysis' in analyses:
            fund_analysis = analyses['fundamental_analysis']
            total_signals += 1
            if fund_analysis.price_change_24h > 0:
                buy_signals += 1
            elif fund_analysis.price_change_24h < 0:
                sell_signals += 1

        if total_signals == 0:
            return "HOLD"

        buy_ratio = buy_signals / total_signals
        sell_ratio = sell_signals / total_signals

        if buy_ratio > 0.6:
            return "BUY"
        elif sell_ratio > 0.6:
            return "SELL"
        else:
            return "HOLD"

    async def _generate_entry_recommendation(self, analyses: Dict[str, Any], symbol: str) -> EntryRecommendation:
        """Generate entry recommendation"""
        # Get current price from analyses
        current_price = self._get_current_price(analyses)

        # Calculate entry price
        entry_price = await self._calculate_entry_price(analyses, current_price)

        # Determine timing
        timing = self._determine_entry_timing(analyses)

        # Calculate confidence
        confidence = self._calculate_entry_confidence(analyses)

        # Generate reasoning
        reasoning = self._generate_entry_reasoning(analyses)

        # Determine risk level
        risk_level = self._determine_risk_level(analyses)

        return EntryRecommendation(
            price=entry_price,
            timing=timing,
            confidence=confidence,
            reasoning=reasoning,
            risk_level=risk_level
        )

    def _get_current_price(self, analyses: Dict[str, Any]) -> float:
        """Get current price from analyses"""
        # Try to get price from market data
        if 'market_data' in analyses and analyses['market_data']:
            latest_data = analyses['market_data'][-1]  # Get latest data point
            return latest_data.close

        # Try to get from fundamental analysis
        if 'fundamental_analysis' in analyses:
            # This would typically come from market data
            pass

        # Default price
        return 50000.0  # Default BTC price for demo

    async def _calculate_entry_price(self, analyses: Dict[str, Any], current_price: float) -> float:
        """Calculate optimal entry price"""
        # Simple strategy: entry slightly below current price for better risk-reward
        discount_factor = 0.01  # 1% discount

        # Adjust discount based on technical analysis
        if 'technical_analysis' in analyses:
            tech_analysis = analyses['technical_analysis']
            if "UPTREND" in tech_analysis.trend:
                discount_factor = 0.005  # Smaller discount in uptrend
            elif "DOWNTREND" in tech_analysis.trend:
                discount_factor = 0.02  # Larger discount in downtrend

        return current_price * (1 - discount_factor)

    def _determine_entry_timing(self, analyses: Dict[str, Any]) -> str:
        """Determine entry timing"""
        # Check technical indicators for timing
        if 'technical_analysis' in analyses:
            tech_analysis = analyses['technical_analysis']

            # Look for oversold conditions
            for indicator in tech_analysis.key_indicators:
                if indicator.name == "RSI" and indicator.value < 30:
                    return "立即入场 - RSI超卖"
                elif indicator.name == "RSI" and indicator.value < 35:
                    return "近期入场 - RSI接近超卖"

        # Check sentiment for timing
        if 'sentiment_analysis' in analyses:
            sent_analysis = analyses['sentiment_analysis']
            if sent_analysis.news_sentiment < -0.5:
                return "观望等待 - 情绪过度悲观"

        return "建议入场 - 条件良好"

    def _calculate_entry_confidence(self, analyses: Dict[str, Any]) -> ConfidenceLevel:
        """Calculate entry confidence"""
        confidence_score = 0
        factors = 0

        # Technical confidence
        if 'technical_analysis' in analyses:
            tech_analysis = analyses['technical_analysis']
            buy_signals = sum(1 for ind in tech_analysis.key_indicators if ind.signal == "BUY")
            total_signals = len(tech_analysis.key_indicators)
            if total_signals > 0:
                confidence_score += (buy_signals / total_signals) * 0.4
            factors += 0.4

        # Sentiment confidence
        if 'sentiment_analysis' in analyses:
            sent_analysis = analyses['sentiment_analysis']
            sentiment_score = (sent_analysis.news_sentiment + sent_analysis.social_sentiment + sent_analysis.market_sentiment) / 3
            confidence_score += max(0, sentiment_score) * 0.3
            factors += 0.3

        # Fundamental confidence
        if 'fundamental_analysis' in analyses:
            fund_analysis = analyses['fundamental_analysis']
            if fund_analysis.price_change_24h > 0:
                confidence_score += 0.3
            factors += 0.3

        if factors == 0:
            return ConfidenceLevel.LOW

        overall_confidence = confidence_score / factors

        if overall_confidence >= 0.8:
            return ConfidenceLevel.VERY_HIGH
        elif overall_confidence >= 0.6:
            return ConfidenceLevel.HIGH
        elif overall_confidence >= 0.4:
            return ConfidenceLevel.MEDIUM
        elif overall_confidence >= 0.2:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def _generate_entry_reasoning(self, analyses: Dict[str, Any]) -> List[str]:
        """Generate entry reasoning"""
        reasoning = []

        # Technical reasons
        if 'technical_analysis' in analyses:
            tech_analysis = analyses['technical_analysis']
            if "UPTREND" in tech_analysis.trend:
                reasoning.append("技术面显示上涨趋势")
            if tech_analysis.momentum in ["BULLISH", "STRONG_BULLISH"]:
                reasoning.append("动量指标显示积极信号")

        # Sentiment reasons
        if 'sentiment_analysis' in analyses:
            sent_analysis = analyses['sentiment_analysis']
            if "BULLISH" in sent_analysis.overall_sentiment:
                reasoning.append("市场情绪支持做多")
            if sent_analysis.confidence > 0.7:
                reasoning.append("情绪分析置信度较高")

        # Fundamental reasons
        if 'fundamental_analysis' in analyses:
            fund_analysis = analyses['fundamental_analysis']
            if fund_analysis.price_change_24h > 0:
                reasoning.append("基本面显示价格上涨")
            if fund_analysis.volume_24h > fund_analysis.market_cap * 0.05:
                reasoning.append("成交量活跃，流动性充足")

        return reasoning if reasoning else ["市场条件适合考虑做多机会"]

    def _determine_risk_level(self, analyses: Dict[str, Any]) -> str:
        """Determine risk level"""
        risk_factors = 0

        # Technical risk
        if 'technical_analysis' in analyses:
            tech_analysis = analyses['technical_analysis']
            if tech_analysis.volatility > 0.3:
                risk_factors += 1
            if "DOWNTREND" in tech_analysis.trend:
                risk_factors += 1

        # Sentiment risk
        if 'sentiment_analysis' in analyses:
            sent_analysis = analyses['sentiment_analysis']
            if "BEARISH" in sent_analysis.overall_sentiment:
                risk_factors += 1
            if sent_analysis.confidence < 0.5:
                risk_factors += 1

        if risk_factors >= 3:
            return "HIGH"
        elif risk_factors >= 1:
            return "MEDIUM"
        else:
            return "LOW"

    async def _generate_risk_management(self, analyses: Dict[str, Any], entry_recommendation: EntryRecommendation, custom_params: Dict[str, Any] = None) -> RiskManagement:
        """Generate risk management parameters"""
        entry_price = entry_recommendation.price

        # Calculate stop loss
        stop_loss = await self._calculate_stop_loss(analyses, entry_price)

        # Calculate take profit levels
        take_profit_levels = await self._calculate_take_profit_levels(analyses, entry_price, stop_loss)

        # Calculate position size
        position_size = self._calculate_position_size(entry_price, stop_loss, custom_params)

        # Calculate risk per trade
        risk_per_trade = self._calculate_risk_per_trade(custom_params)

        # Calculate risk-reward ratio
        risk_reward_ratio = self._calculate_risk_reward_ratio(entry_price, stop_loss, take_profit_levels[0])

        return RiskManagement(
            stop_loss=stop_loss,
            take_profit_levels=take_profit_levels,
            position_size=position_size,
            risk_per_trade=risk_per_trade,
            risk_reward_ratio=risk_reward_ratio
        )

    async def _calculate_stop_loss(self, analyses: Dict[str, Any], entry_price: float) -> float:
        """Calculate stop loss price"""
        # Default stop loss at 5% below entry
        stop_loss_percentage = 0.05

        # Adjust based on technical analysis
        if 'technical_analysis' in analyses:
            tech_analysis = analyses['technical_analysis']

            # Use support levels if available
            if tech_analysis.support_levels:
                nearest_support = max(tech_analysis.support_levels)
                if nearest_support < entry_price:
                    return nearest_support

            # Adjust based on volatility
            if tech_analysis.volatility > 0.3:
                stop_loss_percentage = 0.08  # Wider stop loss for high volatility
            elif tech_analysis.volatility < 0.1:
                stop_loss_percentage = 0.03  # Tighter stop loss for low volatility

        # Adjust based on confidence
        if entry_recommendation.confidence in [ConfidenceLevel.VERY_HIGH, ConfidenceLevel.HIGH]:
            stop_loss_percentage *= 0.8  # Tighter stop loss for high confidence

        return entry_price * (1 - stop_loss_percentage)

    async def _calculate_take_profit_levels(self, analyses: Dict[str, Any], entry_price: float, stop_loss: float) -> List[float]:
        """Calculate take profit levels"""
        risk_distance = entry_price - stop_loss

        # Multiple take profit levels
        take_profit_levels = []

        # First target: 1.5x risk
        take_profit_levels.append(entry_price + risk_distance * 1.5)

        # Second target: 2.5x risk
        take_profit_levels.append(entry_price + risk_distance * 2.5)

        # Third target: 4x risk
        take_profit_levels.append(entry_price + risk_distance * 4)

        # Adjust based on technical analysis
        if 'technical_analysis' in analyses:
            tech_analysis = analyses['technical_analysis']

            # Use resistance levels if available
            if tech_analysis.resistance_levels:
                nearest_resistance = min(tech_analysis.resistance_levels)
                if nearest_resistance > entry_price:
                    take_profit_levels[0] = min(take_profit_levels[0], nearest_resistance)

        # Adjust based on trend strength
        if 'technical_analysis' in analyses:
            tech_analysis = analyses['technical_analysis']
            if "STRONG_UPTREND" in tech_analysis.trend:
                # More aggressive targets in strong uptrend
                take_profit_levels = [entry_price + risk_distance * 2, entry_price + risk_distance * 3.5, entry_price + risk_distance * 6]

        return take_profit_levels

    def _calculate_position_size(self, entry_price: float, stop_loss: float, custom_params: Dict[str, Any] = None) -> float:
        """Calculate position size"""
        # Get account size (would come from portfolio management)
        account_size = custom_params.get('account_size', 100000) if custom_params else 100000

        # Get risk per trade
        risk_per_trade = custom_params.get('risk_per_trade', self.risk_per_trade_default) if custom_params else self.risk_per_trade_default

        # Calculate risk amount
        risk_amount = account_size * risk_per_trade

        # Calculate position size
        risk_per_unit = entry_price - stop_loss
        position_size = risk_amount / risk_per_unit

        # Apply maximum position size limit
        max_position_value = account_size * self.max_position_size
        max_position_size = max_position_value / entry_price

        position_size = min(position_size, max_position_size)

        # Return as percentage of account size
        return (position_size * entry_price) / account_size

    def _calculate_risk_per_trade(self, custom_params: Dict[str, Any] = None) -> float:
        """Calculate risk per trade percentage"""
        return custom_params.get('risk_per_trade', self.risk_per_trade_default) if custom_params else self.risk_per_trade_default

    def _calculate_risk_reward_ratio(self, entry_price: float, stop_loss: float, take_profit: float) -> float:
        """Calculate risk-reward ratio"""
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
        return reward / risk if risk > 0 else 0

    def _generate_reasoning(self, analyses: Dict[str, Any], action: str) -> List[str]:
        """Generate overall reasoning"""
        reasoning = []

        if action == "BUY":
            # Technical reasons
            if 'technical_analysis' in analyses:
                tech_analysis = analyses['technical_analysis']
                if "UPTREND" in tech_analysis.trend:
                    reasoning.append("技术面确认上涨趋势")
                if tech_analysis.momentum in ["BULLISH", "STRONG_BULLISH"]:
                    reasoning.append("动量指标支持上涨")

            # Sentiment reasons
            if 'sentiment_analysis' in analyses:
                sent_analysis = analyses['sentiment_analysis']
                if "BULLISH" in sent_analysis.overall_sentiment:
                    reasoning.append("市场情绪积极")
                if sent_analysis.confidence > 0.7:
                    reasoning.append("情绪分析可靠性高")

            # Fundamental reasons
            if 'fundamental_analysis' in analyses:
                fund_analysis = analyses['fundamental_analysis']
                if fund_analysis.price_change_24h > 0:
                    reasoning.append("价格动量积极")
                if fund_analysis.volume_24h > fund_analysis.market_cap * 0.05:
                    reasoning.append("交易活跃，流动性充足")

        elif action == "SELL":
            reasoning.append("当前条件下建议谨慎，可能考虑减仓")
        else:  # HOLD
            reasoning.append("建议观望等待更明确信号")

        return reasoning if reasoning else ["需要更多数据确认趋势"]

    def _calculate_expected_win_rate(self, analyses: Dict[str, Any]) -> float:
        """Calculate expected win rate"""
        win_rate_factors = []
        weights = []

        # Technical win rate
        if 'technical_analysis' in analyses:
            tech_analysis = analyses['technical_analysis']
            buy_signals = sum(1 for ind in tech_analysis.key_indicators if ind.signal == "BUY")
            total_signals = len(tech_analysis.key_indicators)
            if total_signals > 0:
                win_rate_factors.append(buy_signals / total_signals)
                weights.append(0.4)

        # Sentiment win rate
        if 'sentiment_analysis' in analyses:
            sent_analysis = analyses['sentiment_analysis']
            sentiment_score = (sent_analysis.news_sentiment + sent_analysis.social_sentiment + sent_analysis.market_sentiment) / 3
            sentiment_win_rate = (sentiment_score + 1) / 2  # Convert from [-1,1] to [0,1]
            win_rate_factors.append(sentiment_win_rate)
            weights.append(0.3)

        # Fundamental win rate
        if 'fundamental_analysis' in analyses:
            fund_analysis = analyses['fundamental_analysis']
            if fund_analysis.price_change_24h > 0:
                win_rate_factors.append(0.6)
            else:
                win_rate_factors.append(0.4)
            weights.append(0.3)

        if not win_rate_factors:
            return 0.5  # Default 50% win rate

        # Calculate weighted average
        weighted_sum = sum(wr * weight for wr, weight in zip(win_rate_factors, weights))
        total_weight = sum(weights)

        return weighted_sum / total_weight if total_weight > 0 else 0.5

    def _determine_time_horizon(self, analyses: Dict[str, Any]) -> str:
        """Determine trading time horizon"""
        # Default to medium term
        time_horizon = "中期 (1-4周)"

        # Adjust based on trend strength
        if 'technical_analysis' in analyses:
            tech_analysis = analyses['technical_analysis']
            if "STRONG_UPTREND" in tech_analysis.trend:
                time_horizon = "长期 (1-3个月)"
            elif "SHORT_TERM" in tech_analysis.trend:
                time_horizon = "短期 (1-7天)"

        # Adjust based on volatility
        if 'technical_analysis' in analyses:
            tech_analysis = analyses['technical_analysis']
            if tech_analysis.volatility > 0.4:
                time_horizon = "短期 (1-7天)"  # Shorter horizon for high volatility

        return time_horizon

    def _calculate_confidence(self, analyses: Dict[str, Any]) -> ConfidenceLevel:
        """Calculate overall confidence"""
        confidence_score = 0
        factors = 0

        # Technical confidence
        if 'technical_analysis' in analyses:
            tech_analysis = analyses['technical_analysis']
            if tech_analysis.key_indicators:
                avg_confidence = sum(ind.confidence for ind in tech_analysis.key_indicators) / len(tech_analysis.key_indicators)
                confidence_score += avg_confidence * 0.4
                factors += 0.4

        # Sentiment confidence
        if 'sentiment_analysis' in analyses:
            sent_analysis = analyses['sentiment_analysis']
            confidence_score += sent_analysis.confidence * 0.3
            factors += 0.3

        # Fundamental confidence
        if 'fundamental_analysis' in analyses:
            confidence_score += 0.7 * 0.3  # Fundamental data is generally reliable
            factors += 0.3

        if factors == 0:
            return ConfidenceLevel.LOW

        overall_confidence = confidence_score / factors

        if overall_confidence >= 0.8:
            return ConfidenceLevel.VERY_HIGH
        elif overall_confidence >= 0.6:
            return ConfidenceLevel.HIGH
        elif overall_confidence >= 0.4:
            return ConfidenceLevel.MEDIUM
        elif overall_confidence >= 0.2:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW