"""
Risk-reward analyzer for comprehensive risk assessment
"""

import asyncio
from typing import Dict, List, Optional, Any
import numpy as np
import math
from dataclasses import dataclass
from datetime import datetime, timedelta

from .models import RiskRewardAnalysis, StrategyRecommendation


class RiskRewardAnalyzer:
    """Risk-reward analyzer for comprehensive risk assessment"""

    def __init__(self):
        """Initialize risk-reward analyzer"""
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        self.confidence_intervals = [0.68, 0.95, 0.99]  # Standard deviation intervals

    async def analyze(self, strategy_recommendation: StrategyRecommendation, analysis_data: Dict[str, Any]) -> RiskRewardAnalysis:
        """
        Perform comprehensive risk-reward analysis

        Args:
            strategy_recommendation: Strategy recommendation
            analysis_data: Analysis data

        Returns:
            Risk-reward analysis results
        """
        # Calculate expected return
        expected_return = await self._calculate_expected_return(strategy_recommendation, analysis_data)

        # Calculate maximum drawdown
        max_drawdown = await self._calculate_max_drawdown(strategy_recommendation, analysis_data)

        # Calculate Sharpe ratio
        sharpe_ratio = await self._calculate_sharpe_ratio(strategy_recommendation, analysis_data)

        # Calculate win probability
        win_probability = await self._calculate_win_probability(strategy_recommendation, analysis_data)

        # Calculate risk-reward ratio
        risk_reward_ratio = strategy_recommendation.risk_management.risk_reward_ratio

        # Calculate breakeven points
        breakeven_points = await self._calculate_breakeven_points(strategy_recommendation, analysis_data)

        # Perform sensitivity analysis
        sensitivity_analysis = await self._perform_sensitivity_analysis(strategy_recommendation, analysis_data)

        return RiskRewardAnalysis(
            expected_return=expected_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_probability=win_probability,
            risk_reward_ratio=risk_reward_ratio,
            breakeven_points=breakeven_points,
            sensitivity_analysis=sensitivity_analysis
        )

    async def _calculate_expected_return(self, strategy_recommendation: StrategyRecommendation, analysis_data: Dict[str, Any]) -> float:
        """Calculate expected return"""
        entry_price = strategy_recommendation.entry_recommendation.price
        stop_loss = strategy_recommendation.risk_management.stop_loss
        take_profit = strategy_recommendation.risk_management.take_profit_levels[0]  # Use first target

        # Base calculation
        risk_amount = entry_price - stop_loss
        reward_amount = take_profit - entry_price
        base_return = reward_amount / entry_price

        # Adjust for win rate
        win_rate = strategy_recommendation.expected_win_rate
        loss_rate = 1 - win_rate

        # Expected return = (win_rate * reward) - (loss_rate * risk)
        expected_return = (win_rate * base_return) - (loss_rate * (risk_amount / entry_price))

        # Adjust for market conditions
        market_adjustment = self._calculate_market_adjustment(analysis_data)
        expected_return += market_adjustment

        return expected_return

    def _calculate_market_adjustment(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate market condition adjustment"""
        adjustment = 0

        # Technical analysis adjustment
        if 'technical_analysis' in analysis_data:
            tech_analysis = analysis_data['technical_analysis']
            if "STRONG_UPTREND" in tech_analysis.trend:
                adjustment += 0.02  # +2% in strong uptrend
            elif "STRONG_DOWNTREND" in tech_analysis.trend:
                adjustment -= 0.02  # -2% in strong downtrend

        # Sentiment analysis adjustment
        if 'sentiment_analysis' in analysis_data:
            sent_analysis = analysis_data['sentiment_analysis']
            sentiment_adjustment = (sent_analysis.news_sentiment + sent_analysis.social_sentiment + sent_analysis.market_sentiment) / 3
            adjustment += sentiment_adjustment * 0.01  # Sentiment impact scaled

        # Volatility adjustment (higher volatility = lower expected return)
        if 'technical_analysis' in analysis_data:
            tech_analysis = analysis_data['technical_analysis']
            volatility_penalty = tech_analysis.volatility * 0.05  # 5% penalty per unit of volatility
            adjustment -= volatility_penalty

        return adjustment

    async def _calculate_max_drawdown(self, strategy_recommendation: StrategyRecommendation, analysis_data: Dict[str, Any]) -> float:
        """Calculate maximum drawdown estimate"""
        entry_price = strategy_recommendation.entry_recommendation.price
        stop_loss = strategy_recommendation.risk_management.stop_loss

        # Base drawdown (stop loss)
        base_drawdown = (entry_price - stop_loss) / entry_price

        # Adjust for volatility
        volatility_multiplier = 1.0
        if 'technical_analysis' in analysis_data:
            tech_analysis = analysis_data['technical_analysis']
            if tech_analysis.volatility > 0.3:
                volatility_multiplier = 1.5  # Higher potential drawdown in high volatility
            elif tech_analysis.volatility < 0.1:
                volatility_multiplier = 0.8  # Lower potential drawdown in low volatility

        # Adjust for market conditions
        market_multiplier = self._get_drawdown_market_multiplier(analysis_data)

        # Calculate final max drawdown
        max_drawdown = base_drawdown * volatility_multiplier * market_multiplier

        return min(max_drawdown, 0.5)  # Cap at 50% max drawdown

    def _get_drawdown_market_multiplier(self, analysis_data: Dict[str, Any]) -> float:
        """Get market condition multiplier for drawdown"""
        multiplier = 1.0

        # Bear market multiplier
        if 'sentiment_analysis' in analysis_data:
            sent_analysis = analysis_data['sentiment_analysis']
            if "BEARISH" in sent_analysis.overall_sentiment:
                multiplier = 1.3  # Higher drawdown potential in bear market
            elif "BULLISH" in sent_analysis.overall_sentiment:
                multiplier = 0.8  # Lower drawdown potential in bull market

        # Trend strength multiplier
        if 'technical_analysis' in analysis_data:
            tech_analysis = analysis_data['technical_analysis']
            if "STRONG_DOWNTREND" in tech_analysis.trend:
                multiplier *= 1.4  # Much higher drawdown in strong downtrend
            elif "STRONG_UPTREND" in tech_analysis.trend:
                multiplier *= 0.7  # Lower drawdown in strong uptrend

        return multiplier

    async def _calculate_sharpe_ratio(self, strategy_recommendation: StrategyRecommendation, analysis_data: Dict[str, Any]) -> float:
        """Calculate Sharpe ratio"""
        expected_return = await self._calculate_expected_return(strategy_recommendation, analysis_data)

        # Estimate volatility
        volatility = self._estimate_volatility(analysis_data)

        # Calculate Sharpe ratio
        if volatility > 0:
            sharpe_ratio = (expected_return - self.risk_free_rate) / volatility
        else:
            sharpe_ratio = 0

        return sharpe_ratio

    def _estimate_volatility(self, analysis_data: Dict[str, Any]) -> float:
        """Estimate annualized volatility"""
        # Use technical analysis volatility if available
        if 'technical_analysis' in analysis_data:
            tech_analysis = analysis_data['technical_analysis']
            if tech_analysis.volatility > 0:
                # Convert to annualized volatility (assuming daily data)
                return tech_analysis.volatility * math.sqrt(252)

        # Estimate from market data
        if 'market_data' in analysis_data and analysis_data['market_data']:
            market_data = analysis_data['market_data']
            if len(market_data) >= 20:  # Need at least 20 data points
                returns = []
                for i in range(1, len(market_data)):
                    ret = (market_data[i].close - market_data[i-1].close) / market_data[i-1].close
                    returns.append(ret)

                if returns:
                    std_dev = np.std(returns)
                    return std_dev * math.sqrt(252)  # Annualize

        # Default volatility
        return 0.5  # 50% annual volatility for crypto

    async def _calculate_win_probability(self, strategy_recommendation: StrategyRecommendation, analysis_data: Dict[str, Any]) -> float:
        """Calculate win probability"""
        # Base win rate from strategy recommendation
        base_win_rate = strategy_recommendation.expected_win_rate

        # Adjust for market conditions
        market_adjustment = self._calculate_win_probability_adjustment(analysis_data)

        # Calculate final win probability
        win_probability = base_win_rate + market_adjustment

        return max(0.1, min(0.9, win_probability))  # Clamp between 10% and 90%

    def _calculate_win_probability_adjustment(self, analysis_data: Dict[str, Any]) -> float:
        """Calculate win probability adjustment based on market conditions"""
        adjustment = 0

        # Trend adjustment
        if 'technical_analysis' in analysis_data:
            tech_analysis = analysis_data['technical_analysis']
            if "UPTREND" in tech_analysis.trend:
                adjustment += 0.1  # +10% in uptrend
            elif "DOWNTREND" in tech_analysis.trend:
                adjustment -= 0.1  # -10% in downtrend

        # Sentiment adjustment
        if 'sentiment_analysis' in analysis_data:
            sent_analysis = analysis_data['sentiment_analysis']
            sentiment_score = (sent_analysis.news_sentiment + sent_analysis.social_sentiment + sent_analysis.market_sentiment) / 3
            adjustment += sentiment_score * 0.15  # Sentiment impact

        # Volatility adjustment (higher volatility = lower win probability)
        if 'technical_analysis' in analysis_data:
            tech_analysis = analysis_data['technical_analysis']
            volatility_penalty = tech_analysis.volatility * 0.1  # 10% penalty per unit of volatility
            adjustment -= volatility_penalty

        return adjustment

    async def _calculate_breakeven_points(self, strategy_recommendation: StrategyRecommendation, analysis_data: Dict[str, Any]) -> List[float]:
        """Calculate breakeven points"""
        entry_price = strategy_recommendation.entry_recommendation.price
        stop_loss = strategy_recommendation.risk_management.stop_loss
        win_rate = strategy_recommendation.expected_win_rate

        # Simple breakeven calculation
        # Win Rate * Win Amount = (1 - Win Rate) * Loss Amount
        # Win Amount = ((1 - Win Rate) / Win Rate) * Loss Amount

        loss_amount = entry_price - stop_loss
        win_amount = ((1 - win_rate) / win_rate) * loss_amount

        # Breakeven price
        breakeven_price = entry_price + win_amount

        # Multiple breakeven points based on confidence intervals
        breakeven_points = []

        # Base breakeven
        breakeven_points.append(breakeven_price)

        # Conservative breakeven (higher win rate required)
        conservative_win_rate = win_rate + 0.1  # +10% win rate
        conservative_win_amount = ((1 - conservative_win_rate) / conservative_win_rate) * loss_amount
        conservative_breakeven = entry_price + conservative_win_amount
        breakeven_points.append(conservative_breakeven)

        # Aggressive breakeven (lower win rate acceptable)
        aggressive_win_rate = win_rate - 0.1  # -10% win rate
        aggressive_win_amount = ((1 - aggressive_win_rate) / aggressive_win_rate) * loss_amount
        aggressive_breakeven = entry_price + aggressive_win_amount
        breakeven_points.append(aggressive_breakeven)

        return breakeven_points

    async def _perform_sensitivity_analysis(self, strategy_recommendation: StrategyRecommendation, analysis_data: Dict[str, Any]) -> Dict[str, float]:
        """Perform sensitivity analysis on key parameters"""
        sensitivity_results = {}

        # Test sensitivity to entry price
        entry_sensitivity = await self._test_entry_price_sensitivity(strategy_recommendation, analysis_data)
        sensitivity_results['entry_price'] = entry_sensitivity

        # Test sensitivity to stop loss
        stop_loss_sensitivity = await self._test_stop_loss_sensitivity(strategy_recommendation, analysis_data)
        sensitivity_results['stop_loss'] = stop_loss_sensitivity

        # Test sensitivity to win rate
        win_rate_sensitivity = await self._test_win_rate_sensitivity(strategy_recommendation, analysis_data)
        sensitivity_results['win_rate'] = win_rate_sensitivity

        # Test sensitivity to volatility
        volatility_sensitivity = await self._test_volatility_sensitivity(strategy_recommendation, analysis_data)
        sensitivity_results['volatility'] = volatility_sensitivity

        return sensitivity_results

    async def _test_entry_price_sensitivity(self, strategy_recommendation: StrategyRecommendation, analysis_data: Dict[str, Any]) -> float:
        """Test sensitivity to entry price changes"""
        base_expected_return = await self._calculate_expected_return(strategy_recommendation, analysis_data)

        # Test 5% higher entry price
        higher_entry_strategy = self._modify_entry_price(strategy_recommendation, 1.05)
        higher_return = await self._calculate_expected_return(higher_entry_strategy, analysis_data)

        # Test 5% lower entry price
        lower_entry_strategy = self._modify_entry_price(strategy_recommendation, 0.95)
        lower_return = await self._calculate_expected_return(lower_entry_strategy, analysis_data)

        # Calculate sensitivity (average change in return per 1% change in entry price)
        sensitivity = abs(higher_return - base_expected_return) / 0.05
        sensitivity += abs(lower_return - base_expected_return) / 0.05
        sensitivity /= 2

        return sensitivity

    async def _test_stop_loss_sensitivity(self, strategy_recommendation: StrategyRecommendation, analysis_data: Dict[str, Any]) -> float:
        """Test sensitivity to stop loss changes"""
        base_expected_return = await self._calculate_expected_return(strategy_recommendation, analysis_data)

        # Test 10% wider stop loss
        wider_stop_strategy = self._modify_stop_loss(strategy_recommendation, 1.10)
        wider_return = await self._calculate_expected_return(wider_stop_strategy, analysis_data)

        # Test 10% tighter stop loss
        tighter_stop_strategy = self._modify_stop_loss(strategy_recommendation, 0.90)
        tighter_return = await self._calculate_expected_return(tighter_stop_strategy, analysis_data)

        # Calculate sensitivity
        sensitivity = abs(wider_return - base_expected_return) / 0.10
        sensitivity += abs(tighter_return - base_expected_return) / 0.10
        sensitivity /= 2

        return sensitivity

    async def _test_win_rate_sensitivity(self, strategy_recommendation: StrategyRecommendation, analysis_data: Dict[str, Any]) -> float:
        """Test sensitivity to win rate changes"""
        base_win_rate = strategy_recommendation.expected_win_rate

        # Test win rate scenarios
        win_rates = [base_win_rate - 0.1, base_win_rate, base_win_rate + 0.1]
        returns = []

        for win_rate in win_rates:
            modified_strategy = self._modify_win_rate(strategy_recommendation, win_rate)
            expected_return = await self._calculate_expected_return(modified_strategy, analysis_data)
            returns.append(expected_return)

        # Calculate sensitivity (change in return per 1% change in win rate)
        sensitivity = abs(returns[2] - returns[0]) / 0.20  # Change over 20% range

        return sensitivity

    async def _test_volatility_sensitivity(self, strategy_recommendation: StrategyRecommendation, analysis_data: Dict[str, Any]) -> float:
        """Test sensitivity to volatility changes"""
        base_expected_return = await self._calculate_expected_return(strategy_recommendation, analysis_data)

        # Test different volatility scenarios
        volatility_multipliers = [0.5, 1.0, 1.5, 2.0]
        returns = []

        for multiplier in volatility_multipliers:
            modified_analysis = self._modify_volatility(analysis_data, multiplier)
            expected_return = await self._calculate_expected_return(strategy_recommendation, modified_analysis)
            returns.append(expected_return)

        # Calculate sensitivity (average change in return per 1% change in volatility)
        base_return = returns[1]  # 1.0 multiplier
        sensitivity_changes = []

        for i, multiplier in enumerate(volatility_multipliers):
            if i != 1:  # Skip base case
                change = abs(returns[i] - base_return)
                volatility_change = abs(multiplier - 1.0)
                sensitivity_changes.append(change / volatility_change)

        sensitivity = sum(sensitivity_changes) / len(sensitivity_changes) if sensitivity_changes else 0

        return sensitivity

    def _modify_entry_price(self, strategy: StrategyRecommendation, multiplier: float) -> StrategyRecommendation:
        """Modify entry price by multiplier"""
        modified_strategy = StrategyRecommendation(
            action=strategy.action,
            symbol=strategy.symbol,
            entry_recommendation=StrategyRecommendation.EntryRecommendation(
                price=strategy.entry_recommendation.price * multiplier,
                timing=strategy.entry_recommendation.timing,
                confidence=strategy.entry_recommendation.confidence,
                reasoning=strategy.entry_recommendation.reasoning,
                risk_level=strategy.entry_recommendation.risk_level
            ),
            risk_management=strategy.risk_management,
            reasoning=strategy.reasoning,
            expected_win_rate=strategy.expected_win_rate,
            time_horizon=strategy.time_horizon,
            confidence=strategy.confidence
        )
        return modified_strategy

    def _modify_stop_loss(self, strategy: StrategyRecommendation, multiplier: float) -> StrategyRecommendation:
        """Modify stop loss by multiplier"""
        modified_strategy = StrategyRecommendation(
            action=strategy.action,
            symbol=strategy.symbol,
            entry_recommendation=strategy.entry_recommendation,
            risk_management=StrategyRecommendation.RiskManagement(
                stop_loss=strategy.risk_management.stop_loss * multiplier,
                take_profit_levels=strategy.risk_management.take_profit_levels,
                position_size=strategy.risk_management.position_size,
                risk_per_trade=strategy.risk_management.risk_per_trade,
                risk_reward_ratio=strategy.risk_management.risk_reward_ratio
            ),
            reasoning=strategy.reasoning,
            expected_win_rate=strategy.expected_win_rate,
            time_horizon=strategy.time_horizon,
            confidence=strategy.confidence
        )
        return modified_strategy

    def _modify_win_rate(self, strategy: StrategyRecommendation, win_rate: float) -> StrategyRecommendation:
        """Modify win rate"""
        modified_strategy = StrategyRecommendation(
            action=strategy.action,
            symbol=strategy.symbol,
            entry_recommendation=strategy.entry_recommendation,
            risk_management=strategy.risk_management,
            reasoning=strategy.reasoning,
            expected_win_rate=win_rate,
            time_horizon=strategy.time_horizon,
            confidence=strategy.confidence
        )
        return modified_strategy

    def _modify_volatility(self, analysis_data: Dict[str, Any], multiplier: float) -> Dict[str, Any]:
        """Modify volatility in analysis data"""
        modified_data = analysis_data.copy()

        if 'technical_analysis' in modified_data:
            tech_analysis = modified_data['technical_analysis']
            # This is a simplified modification - in practice you'd need to modify the actual volatility value
            pass

        return modified_data

    async def calculate_portfolio_metrics(self, strategies: List[StrategyRecommendation], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate portfolio-level risk metrics"""
        portfolio_metrics = {}

        # Individual position analyses
        position_analyses = []
        for strategy in strategies:
            analysis = await self.analyze(strategy, analysis_data)
            position_analyses.append(analysis)

        # Portfolio expected return
        portfolio_metrics['expected_return'] = np.mean([pos.expected_return for pos in position_analyses])

        # Portfolio max drawdown
        portfolio_metrics['max_drawdown'] = np.mean([pos.max_drawdown for pos in position_analyses])

        # Portfolio win probability
        portfolio_metrics['win_probability'] = np.mean([pos.win_probability for pos in position_analyses])

        # Portfolio Sharpe ratio
        portfolio_metrics['sharpe_ratio'] = np.mean([pos.sharpe_ratio for pos in position_analyses])

        # Diversification benefit
        portfolio_metrics['diversification_benefit'] = self._calculate_diversification_benefit(position_analyses)

        return portfolio_metrics

    def _calculate_diversification_benefit(self, position_analyses: List[RiskRewardAnalysis]) -> float:
        """Calculate diversification benefit"""
        if len(position_analyses) < 2:
            return 0.0

        # Simple diversification calculation based on correlation of expected returns
        returns = [pos.expected_return for pos in position_analyses]
        risks = [pos.max_drawdown for pos in position_analyses]

        # Calculate weighted average risk
        weighted_avg_risk = np.mean(risks)

        # Calculate portfolio risk (simplified)
        portfolio_risk = np.std(returns)

        # Diversification benefit
        diversification_benefit = (weighted_avg_risk - portfolio_risk) / weighted_avg_risk

        return max(0, diversification_benefit)