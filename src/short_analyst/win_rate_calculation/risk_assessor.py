"""
做空风险评估引擎

该模块实现了针对做空交易的全面风险评估系统。
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import statistics
import math as math_lib

from .win_rate_models import (
    RiskAssessment, RiskCategory, TradeResult, ShortSignal
)


class RiskAssessor:
    """风险评估引擎"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化风险评估引擎

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.confidence_level = self.config.get('confidence_level', 0.95)
        self.var_confidence_levels = [0.95, 0.99]
        self.stress_scenarios = self._initialize_stress_scenarios()
        self.risk_weights = self._initialize_risk_weights()

    async def assess_risk(
        self,
        current_signals: List[ShortSignal],
        trade_history: List[TradeResult],
        market_data: Optional[Dict[str, Any]] = None
    ) -> RiskAssessment:
        """
        评估整体风险

        Args:
            current_signals: 当前信号列表
            trade_history: 交易历史
            market_data: 市场数据

        Returns:
            RiskAssessment: 风险评估结果
        """
        assessment = RiskAssessment(
            symbol=current_signals[0].symbol if current_signals else "",
            assessment_time=datetime.now()
        )

        # 计算各类风险
        await self._assess_market_risk(assessment, current_signals, trade_history, market_data)
        await self._assess_liquidity_risk(assessment, current_signals, market_data)
        await self._assess_volatility_risk(assessment, current_signals, trade_history)
        await self._assess_leverage_risk(assessment, current_signals)
        await self._assess_short_squeeze_risk(assessment, current_signals, market_data)
        await self._assess_regulatory_risk(assessment, market_data)
        await self._assess_systemic_risk(assessment, market_data)

        # 计算整体风险评分
        assessment.overall_risk_score = self._calculate_overall_risk_score(assessment)
        assessment.risk_level = self._classify_risk_level(assessment.overall_risk_score)

        # 计算风险指标
        await self._calculate_risk_metrics(assessment, trade_history)

        # 生成风险控制建议
        await self._generate_risk_recommendations(assessment)

        # 执行压力测试
        await self._run_stress_tests(assessment, current_signals, trade_history)

        # 生成风险预警
        await self._generate_risk_warnings(assessment)

        return assessment

    async def _assess_market_risk(
        self,
        assessment: RiskAssessment,
        signals: List[ShortSignal],
        trade_history: List[TradeResult],
        market_data: Optional[Dict[str, Any]] = None
    ):
        """评估市场风险"""
        market_risk_factors = 0

        # 基于历史交易表现
        if trade_history:
            returns = [t.profit_loss_pct for t in trade_history]
            volatility = statistics.stdev(returns) if len(returns) > 1 else 0
            market_risk_factors += min(volatility * 10, 0.3)  # 波动率风险

        # 基于信号强度
        if signals:
            avg_strength = sum([s.strength for s in signals]) / len(signals)
            if avg_strength < 2:  # 弱信号较多
                market_risk_factors += 0.2

        # 基于市场数据
        if market_data:
            # 市场趋势风险
            if market_data.get('trend') == 'strong_uptrend':
                market_risk_factors += 0.4  # 逆势做空风险

            # 相关性风险
            correlation_with_btc = market_data.get('correlation_with_btc', 0)
            if abs(correlation_with_btc) > 0.8:
                market_risk_factors += 0.2

        assessment.market_risk_score = min(market_risk_factors, 1.0)

    async def _assess_liquidity_risk(
        self,
        assessment: RiskAssessment,
        signals: List[ShortSignal],
        market_data: Optional[Dict[str, Any]] = None
    ):
        """评估流动性风险"""
        liquidity_risk_score = 0

        # 基于信号中的流动性评估
        if signals:
            avg_liquidity_risk = sum([s.liquidity_risk for s in signals]) / len(signals)
            liquidity_risk_score += avg_liquidity_risk * 0.6

        # 基于市场数据
        if market_data:
            volume_24h = market_data.get('volume_24h', 0)
            market_cap = market_data.get('market_cap', 0)

            if market_cap > 0:
                volume_to_market_cap_ratio = volume_24h / market_cap
                if volume_to_market_cap_ratio < 0.02:  # 低流动性
                    liquidity_risk_score += 0.3

            # 订单簿深度
            order_book_depth = market_data.get('order_book_depth', 0)
            if order_book_depth < 1000000:  # 100万美元以下
                liquidity_risk_score += 0.2

        assessment.liquidity_risk_score = min(liquidity_risk_score, 1.0)

    async def _assess_volatility_risk(
        self,
        assessment: RiskAssessment,
        signals: List[ShortSignal],
        trade_history: List[TradeResult]
    ):
        """评估波动率风险"""
        volatility_risk_score = 0

        # 基于历史交易数据
        if trade_history:
            returns = [t.profit_loss_pct for t in trade_history]
            if len(returns) > 1:
                volatility = statistics.stdev(returns)

                # 波动率过高风险
                if volatility > 0.1:  # 日波动率超过10%
                    volatility_risk_score += 0.4
                elif volatility > 0.05:  # 日波动率超过5%
                    volatility_risk_score += 0.2

                # 波动率聚类风险
                recent_volatility = statistics.stdev(returns[-10:]) if len(returns) >= 10 else volatility
                if recent_volatility > volatility * 1.5:
                    volatility_risk_score += 0.3

        # 基于信号中的风险等级
        if signals:
            high_risk_signals = [s for s in signals if s.risk_level >= 4]
            if len(high_risk_signals) / len(signals) > 0.3:
                volatility_risk_score += 0.2

        assessment.volatility_risk_score = min(volatility_risk_score, 1.0)

    async def _assess_leverage_risk(
        self,
        assessment: RiskAssessment,
        signals: List[ShortSignal]
    ):
        """评估杠杆风险"""
        leverage_risk_score = 0

        # 基于信号数量和集中度
        signal_count = len(signals)
        if signal_count > 10:
            leverage_risk_score += 0.3  # 过度分散
        elif signal_count > 5:
            leverage_risk_score += 0.1

        # 基于单个信号的大小
        if signals:
            avg_risk_level = sum([s.risk_level for s in signals]) / len(signals)
            if avg_risk_level > 3.5:
                leverage_risk_score += 0.4
            elif avg_risk_level > 2.5:
                leverage_risk_score += 0.2

        # 检查是否有高风险信号
        high_leverage_signals = [s for s in signals if s.metadata.get('leverage', 1) > 3]
        if len(high_leverage_signals) > 0:
            leverage_risk_score += 0.3

        assessment.leverage_risk_score = min(leverage_risk_score, 1.0)

    async def _assess_short_squeeze_risk(
        self,
        assessment: RiskAssessment,
        signals: List[ShortSignal],
        market_data: Optional[Dict[str, Any]] = None
    ):
        """评估轧空风险"""
        squeeze_risk_score = 0

        # 基于信号中的轧空风险评估
        if signals:
            avg_squeeze_risk = sum([s.short_squeeze_risk for s in signals]) / len(signals)
            squeeze_risk_score += avg_squeeze_risk * 0.5

        # 基于市场数据
        if market_data:
            # 短期持仓比例
            short_interest_ratio = market_data.get('short_interest_ratio', 0)
            if short_interest_ratio > 0.3:  # 超过30%
                squeeze_risk_score += 0.4
            elif short_interest_ratio > 0.2:
                squeeze_risk_score += 0.2

            # 融资利率
            funding_rate = market_data.get('funding_rate', 0)
            if abs(funding_rate) > 0.001:  # 超过0.1%
                squeeze_risk_score += 0.2

            # 多空比
            long_short_ratio = market_data.get('long_short_ratio', 1)
            if long_short_ratio > 3:  # 多头过多
                squeeze_risk_score += 0.3

        assessment.short_squeeze_risk_score = min(squeeze_risk_score, 1.0)
        assessment.short_squeeze_probability = squeeze_risk_score

    async def _assess_regulatory_risk(
        self,
        assessment: RiskAssessment,
        market_data: Optional[Dict[str, Any]] = None
    ):
        """评估监管风险"""
        regulatory_risk_score = 0

        # 基于市场数据
        if market_data:
            # 监管新闻
            regulatory_news = market_data.get('regulatory_news', [])
            if len(regulatory_news) > 0:
                regulatory_risk_score += 0.3

            # 地区监管风险
            regulatory_region = market_data.get('regulatory_region', '')
            if regulatory_region in ['US', 'EU', 'CN']:
                regulatory_risk_score += 0.2

            # 合规状态
            compliance_status = market_data.get('compliance_status', '')
            if compliance_status == 'high_risk':
                regulatory_risk_score += 0.4

        assessment.regulatory_risk_score = min(regulatory_risk_score, 1.0)

    async def _assess_systemic_risk(
        self,
        assessment: RiskAssessment,
        market_data: Optional[Dict[str, Any]] = None
    ):
        """评估系统性风险"""
        systemic_risk_score = 0

        # 基于市场数据
        if market_data:
            # 市场恐慌指数
            fear_greed_index = market_data.get('fear_greed_index', 50)
            if fear_greed_index < 20 or fear_greed_index > 80:  # 极端情绪
                systemic_risk_score += 0.3

            # 市场波动性
            market_volatility = market_data.get('market_volatility', 0)
            if market_volatility > 0.05:  # 高波动
                systemic_risk_score += 0.2

            # 系统相关性
            system_correlation = market_data.get('system_correlation', 0)
            if system_correlation > 0.8:  # 高相关
                systemic_risk_score += 0.3

        assessment.systemic_risk_score = min(systemic_risk_score, 1.0)

    def _calculate_overall_risk_score(self, assessment: RiskAssessment) -> float:
        """计算整体风险评分"""
        risk_scores = [
            assessment.market_risk_score,
            assessment.liquidity_risk_score,
            assessment.volatility_risk_score,
            assessment.leverage_risk_score,
            assessment.short_squeeze_risk_score,
            assessment.regulatory_risk_score,
            assessment.systemic_risk_score
        ]

        # 加权计算
        weighted_sum = sum(score * weight for score, weight in zip(risk_scores, self.risk_weights.values()))
        return min(weighted_sum, 1.0)

    def _classify_risk_level(self, risk_score: float) -> str:
        """分类风险等级"""
        if risk_score >= 0.8:
            return "extreme"
        elif risk_score >= 0.6:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        else:
            return "low"

    async def _calculate_risk_metrics(self, assessment: RiskAssessment, trade_history: List[TradeResult]):
        """计算风险指标"""
        if not trade_history:
            return

        returns = [t.profit_loss_pct for t in trade_history]

        # 计算VaR
        assessment.var_95 = self._calculate_var(returns, 0.95)
        assessment.var_99 = self._calculate_var(returns, 0.99)

        # 计算期望损失
        assessment.expected_shortfall = self._calculate_expected_shortfall(returns, 0.95)

        # 计算贝塔系数（简化实现）
        market_returns = [0.001] * len(returns)  # 假设市场日收益率0.1%
        if len(returns) > 1 and len(market_returns) > 1:
            covariance = self._calculate_covariance(returns, market_returns)
            market_variance = statistics.variance(market_returns)
            assessment.beta = covariance / market_variance if market_variance > 0 else 0

        # 计算与市场的相关性
        if len(returns) > 1:
            correlation = self._calculate_correlation(returns, market_returns)
            assessment.correlation_with_market = correlation if not math_lib.isnan(correlation) else 0

        # 计算清算风险
        assessment.liquidation_risk = assessment.leverage_risk_score * assessment.volatility_risk_score

        # 计算对手方风险（简化）
        assessment.counterparty_risk = 0.1  # 默认低风险

    def _calculate_var(self, returns: List[float], confidence: float) -> float:
        """计算风险价值(VaR)"""
        if not returns:
            return 0

        alpha = 1 - confidence
        var_index = int(len(returns) * alpha)
        sorted_returns = sorted(returns)
        return -sorted_returns[var_index] if var_index < len(sorted_returns) else 0

    def _calculate_expected_shortfall(self, returns: List[float], confidence: float) -> float:
        """计算期望损失(ES)"""
        if not returns:
            return 0

        alpha = 1 - confidence
        var_index = int(len(returns) * alpha)
        sorted_returns = sorted(returns)
        tail_returns = sorted_returns[:var_index]

        return -statistics.mean(tail_returns) if tail_returns else 0

    async def _generate_risk_recommendations(self, assessment: RiskAssessment):
        """生成风险控制建议"""
        risk_score = assessment.overall_risk_score

        # 仓位限制
        if risk_score >= 0.8:
            assessment.position_size_limit = 0.05  # 5%
        elif risk_score >= 0.6:
            assessment.position_size_limit = 0.1   # 10%
        elif risk_score >= 0.4:
            assessment.position_size_limit = 0.15  # 15%
        else:
            assessment.position_size_limit = 0.2   # 20%

        # 止损距离
        assessment.stop_loss_distance = 0.02 + (risk_score * 0.03)  # 2%-5%

        # 对冲比率
        if assessment.short_squeeze_risk_score > 0.5:
            assessment.hedge_ratio = 0.3  # 30%对冲
        else:
            assessment.hedge_ratio = 0.1  # 10%对冲

        # 杠杆限制
        if risk_score >= 0.6:
            assessment.leverage_limit = 1.0  # 无杠杆
        elif risk_score >= 0.4:
            assessment.leverage_limit = 2.0  # 2倍杠杆
        else:
            assessment.leverage_limit = 3.0  # 3倍杠杆

    async def _run_stress_tests(
        self,
        assessment: RiskAssessment,
        signals: List[ShortSignal],
        trade_history: List[TradeResult]
    ):
        """执行压力测试"""
        stress_results = {}

        for scenario_name, scenario_params in self.stress_scenarios.items():
            result = self._simulate_stress_scenario(signals, trade_history, scenario_params)
            stress_results[scenario_name] = result

        assessment.stress_test_results = stress_results

    def _simulate_stress_scenario(
        self,
        signals: List[ShortSignal],
        trade_history: List[TradeResult],
        scenario_params: Dict[str, float]
    ) -> float:
        """模拟压力测试场景"""
        if not trade_history:
            return 0

        # 基于历史数据模拟场景
        base_returns = [t.profit_loss_pct for t in trade_history]

        # 应用场景参数
        shock_multiplier = scenario_params.get('price_shock', 1.0)
        vol_multiplier = scenario_params.get('volatility_multiplier', 1.0)
        liquidity_impact = scenario_params.get('liquidity_impact', 0)

        simulated_returns = [r * shock_multiplier for r in base_returns]

        # 计算场景下的最大损失
        max_loss = min(simulated_returns)

        # 考虑流动性影响
        max_loss -= liquidity_impact

        return max_loss

    async def _generate_risk_warnings(self, assessment: RiskAssessment):
        """生成风险预警"""
        warnings = []
        alert_triggers = []

        # 整体风险预警
        if assessment.overall_risk_score >= 0.8:
            warnings.append("整体风险极高，建议立即停止新开仓位")
            alert_triggers.append("EXTREME_RISK")

        # 各类风险预警
        if assessment.short_squeeze_risk_score >= 0.7:
            warnings.append("轧空风险高，注意市场情绪变化")
            alert_triggers.append("HIGH_SQUEEZE_RISK")

        if assessment.liquidity_risk_score >= 0.6:
            warnings.append("流动性不足，注意出入场时机")
            alert_triggers.append("LIQUIDITY_WARNING")

        if assessment.volatility_risk_score >= 0.7:
            warnings.append("市场波动剧烈，谨慎加杠杆")
            alert_triggers.append("VOLATILITY_WARNING")

        if assessment.leverage_risk_score >= 0.6:
            warnings.append("杠杆过高，降低仓位")
            alert_triggers.append("LEVERAGE_WARNING")

        # 连续亏损预警
        # 这里可以添加基于历史交易的连续亏损检查

        assessment.risk_warnings = warnings
        assessment.alert_triggers = alert_triggers

    def _initialize_stress_scenarios(self) -> Dict[str, Dict[str, float]]:
        """初始化压力测试场景"""
        return {
            'market_crash': {
                'price_shock': 2.0,      # 价格翻倍（做空有利）
                'volatility_multiplier': 3.0,
                'liquidity_impact': 0.05
            },
            'short_squeeze': {
                'price_shock': -3.0,     # 价格暴跌3倍（做空不利）
                'volatility_multiplier': 4.0,
                'liquidity_impact': 0.15
            },
            'liquidity_crisis': {
                'price_shock': 1.5,
                'volatility_multiplier': 2.5,
                'liquidity_impact': 0.25
            },
            'regulatory_shock': {
                'price_shock': -2.0,
                'volatility_multiplier': 3.5,
                'liquidity_impact': 0.20
            },
            'black_swan': {
                'price_shock': -5.0,      # 极端情况
                'volatility_multiplier': 5.0,
                'liquidity_impact': 0.30
            }
        }

    def _initialize_risk_weights(self) -> Dict[str, float]:
        """初始化风险权重"""
        return {
            'market_risk': 0.25,
            'liquidity_risk': 0.20,
            'volatility_risk': 0.15,
            'leverage_risk': 0.15,
            'short_squeeze_risk': 0.15,
            'regulatory_risk': 0.05,
            'systemic_risk': 0.05
        }

    async def assess_individual_signal_risk(
        self,
        signal: ShortSignal,
        market_data: Optional[Dict[str, Any]] = None
    ) -> RiskAssessment:
        """评估单个信号的风险"""
        return await self.assess_risk([signal], [], market_data)

    async def calculate_portfolio_risk(
        self,
        signals: List[ShortSignal],
        correlations: Optional[Dict[str, float]] = None
    ) -> float:
        """计算组合风险"""
        if not signals:
            return 0

        # 简化的组合风险计算
        individual_risks = [s.overall_score for s in signals]

        if correlations is None:
            # 假设中等相关性
            avg_correlation = 0.5
        else:
            correlation_values = list(correlations.values())
            avg_correlation = statistics.mean(correlation_values) if correlation_values else 0.5

        # 计算组合风险（简化公式）
        portfolio_variance = sum(r**2 for r in individual_risks) + \
                           avg_correlation * sum(r1 * r2 for i, r1 in enumerate(individual_risks)
                                                for r2 in individual_risks[i+1:])

        return math.sqrt(portfolio_variance)

    def get_risk_thresholds(self) -> Dict[str, float]:
        """获取风险阈值"""
        return {
            'low_risk': 0.4,
            'medium_risk': 0.6,
            'high_risk': 0.8,
            'extreme_risk': 0.9
        }

    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """计算皮尔逊相关系数"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)
        sum_y2 = sum(yi ** 2 for yi in y)

        numerator = n * sum_xy - sum_x * sum_y
        denominator_term1 = n * sum_x2 - sum_x ** 2
        denominator_term2 = n * sum_y2 - sum_y ** 2

        if denominator_term1 <= 0 or denominator_term2 <= 0:
            return 0.0

        denominator = math_lib.sqrt(denominator_term1 * denominator_term2)

        return numerator / denominator if denominator != 0 else 0.0

    def _calculate_covariance(self, x: List[float], y: List[float]) -> float:
        """计算协方差"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)

        covariance = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)) / (n - 1)
        return covariance