"""
做空胜率优化引擎

该模块实现了基于历史数据和机器学习的胜率优化策略生成。
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import statistics
import math as math_lib
from dataclasses import dataclass

from .win_rate_models import (
    OptimizationRecommendation, TradeResult, WinRateAnalysis,
    PerformanceMetrics, ShortSignalType, ShortSignalStrength
)
from ..models.short_signal import ShortSignal


class OptimizationEngine:
    """胜率优化引擎"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化优化引擎

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.min_backtest_period = self.config.get('min_backtest_period', 30)  # 最少30天数据
        self.optimization_targets = ['win_rate', 'profit_factor', 'sharpe_ratio']
        self.parameter_ranges = self._initialize_parameter_ranges()

    async def generate_optimization_recommendations(
        self,
        trade_history: List[TradeResult],
        signal_history: List[ShortSignal],
        current_metrics: PerformanceMetrics,
        target_metrics: List[str] = None
    ) -> List[OptimizationRecommendation]:
        """
        生成优化建议

        Args:
            trade_history: 交易历史
            signal_history: 信号历史
            current_metrics: 当前绩效指标
            target_metrics: 目标优化指标

        Returns:
            List[OptimizationRecommendation]: 优化建议列表
        """
        if target_metrics is None:
            target_metrics = self.optimization_targets

        if len(trade_history) < self.min_backtest_period:
            return self._create_insufficient_data_recommendation()

        recommendations = []

        # 针对每个目标指标生成优化建议
        for target in target_metrics:
            recommendation = await self._optimize_for_target(
                target, trade_history, signal_history, current_metrics
            )
            if recommendation:
                recommendations.append(recommendation)

        # 排序并返回最重要的建议
        recommendations.sort(key=lambda x: x.expected_improvement, reverse=True)
        return recommendations[:5]  # 返回前5个最重要的建议

    async def _optimize_for_target(
        self,
        target: str,
        trade_history: List[TradeResult],
        signal_history: List[ShortSignal],
        current_metrics: PerformanceMetrics
    ) -> Optional[OptimizationRecommendation]:
        """针对特定目标进行优化"""
        current_value = getattr(current_metrics, target, 0)

        if target == 'win_rate':
            return await self._optimize_win_rate(trade_history, signal_history, current_value)
        elif target == 'profit_factor':
            return await self._optimize_profit_factor(trade_history, signal_history, current_value)
        elif target == 'sharpe_ratio':
            return await self._optimize_sharpe_ratio(trade_history, signal_history, current_value)
        else:
            return None

    async def _optimize_win_rate(
        self,
        trade_history: List[TradeResult],
        signal_history: List[ShortSignal],
        current_win_rate: float
    ) -> OptimizationRecommendation:
        """优化胜率"""
        recommendation = OptimizationRecommendation(
            optimization_target='win_rate',
            current_value=current_win_rate,
            priority='high'
        )

        # 分析不同信号类型的胜率
        type_performance = self._analyze_signal_type_performance(trade_history)

        # 找出表现最好的信号类型
        if type_performance:
            best_type = max(type_performance.items(), key=lambda x: x[1]['win_rate'])
            worst_type = min(type_performance.items(), key=lambda x: x[1]['win_rate'])
        else:
            return await self._optimize_by_signal_strength(trade_history, current_win_rate)

        # 生成优化策略
        if best_type[1]['win_rate'] > current_win_rate * 1.2:  # 比当前高20%以上
            improvement = best_type[1]['win_rate'] - current_win_rate

            recommendation.strategy = f"专注于{best_type[0]}信号类型"
            recommendation.expected_improvement = improvement
            recommendation.confidence_level = min(0.8, improvement * 2)  # 基于改进幅度计算置信度

            recommendation.implementation_steps = [
                f"提高{best_type[0]}信号的权重",
                f"减少或暂停{worst_type[0]}信号的交易",
                f"为{best_type[0]}信号设置专门的风险管理规则"
            ]

            recommendation.parameter_changes = {
                'signal_weights': {best_type[0]: 0.8, worst_type[0]: 0.1},
                'min_confidence_threshold': 0.65,
                'max_position_size': 0.15
            }

            # 计算回测结果
            backtest_result = self._simulate_signal_type_filtering(trade_history, best_type[0])
            recommendation.backtest_results = backtest_result

            # 预期影响
            recommendation.expected_win_rate_change = improvement
            recommendation.expected_risk_change = -0.1  # 降低风险
            recommendation.expected_return_change = improvement * 0.5

            # 成本分析
            recommendation.implementation_cost = 0.1  # 低成本
            recommendation.expected_roi = improvement * 5
            recommendation.payback_period = 30  # 30天回本

            recommendation.validation_metrics = ['win_rate', 'profit_factor', 'max_drawdown']

        else:
            # 如果没有明显的最佳信号类型，尝试其他优化策略
            recommendation = await self._optimize_by_signal_strength(trade_history, current_win_rate)

        return recommendation

    async def _optimize_profit_factor(
        self,
        trade_history: List[TradeResult],
        signal_history: List[ShortSignal],
        current_profit_factor: float
    ) -> OptimizationRecommendation:
        """优化盈亏比"""
        recommendation = OptimizationRecommendation(
            optimization_target='profit_factor',
            current_value=current_profit_factor,
            priority='medium'
        )

        # 分析盈亏分布
        profitable_trades = [t for t in trade_history if t.is_successful]
        losing_trades = [t for t in trade_history if not t.is_successful]

        if profitable_trades and losing_trades:
            avg_profit = statistics.mean([t.profit_loss_pct for t in profitable_trades])
            avg_loss = statistics.mean([t.profit_loss_pct for t in losing_trades])

            # 策略：优化止损设置
            if abs(avg_loss) > avg_profit * 0.5:  # 亏损过大
                new_stop_loss = avg_profit * 0.3  # 将止损设置为平均盈利的30%
                improvement_factor = avg_profit / abs(new_stop_loss)

                recommendation.strategy = "优化止损设置以提高盈亏比"
                recommendation.expected_improvement = improvement_factor - current_profit_factor
                recommendation.confidence_level = 0.6

                recommendation.implementation_steps = [
                    "将止损距离调整为盈利目标的30%",
                    "实施跟踪止损机制",
                    "为不同信号类型设置差异化止损"
                ]

                recommendation.parameter_changes = {
                    'stop_loss_distance': 0.03,  # 3%
                    'trailing_stop_enabled': True,
                    'trailing_stop_distance': 0.02  # 2%
                }

                # 模拟优化结果
                simulated_result = self._simulate_optimized_stops(trade_history, new_stop_loss)
                recommendation.backtest_results = simulated_result

                recommendation.expected_win_rate_change = -0.05  # 可能略微降低胜率
                recommendation.expected_risk_change = -0.2  # 显著降低风险
                recommendation.expected_return_change = 0.1

                recommendation.implementation_cost = 0.2
                recommendation.expected_roi = 2.0
                recommendation.payback_period = 45

                recommendation.validation_metrics = ['profit_factor', 'win_rate', 'sharpe_ratio']

        return recommendation

    async def _optimize_sharpe_ratio(
        self,
        trade_history: List[TradeResult],
        signal_history: List[ShortSignal],
        current_sharpe: float
    ) -> OptimizationRecommendation:
        """优化夏普比率"""
        recommendation = OptimizationRecommendation(
            optimization_target='sharpe_ratio',
            current_value=current_sharpe,
            priority='medium'
        )

        # 分析风险调整收益
        returns = [t.profit_loss_pct for t in trade_history]
        if len(returns) > 1:
            volatility = statistics.stdev(returns)

            # 策略：优化仓位管理
            optimal_position_size = self._calculate_optimal_position_size(returns, volatility)

            if optimal_position_size < 1.0:  # 建议降低仓位
                recommendation.strategy = "通过仓位管理优化风险调整收益"
                recommendation.expected_improvement = min(0.5, current_sharpe * 0.3)
                recommendation.confidence_level = 0.7

                recommendation.implementation_steps = [
                    f"实施凯利准则仓位管理",
                    "根据市场波动率动态调整仓位",
                    "设置最大风险敞口限制"
                ]

                recommendation.parameter_changes = {
                    'max_position_size': optimal_position_size,
                    'risk_per_trade': 0.02,  # 每笔交易风险2%
                    'max_portfolio_risk': 0.1  # 组合最大风险10%
                }

                # 模拟结果
                simulated_result = self._simulate_position_sizing(trade_history, optimal_position_size)
                recommendation.backtest_results = simulated_result

                recommendation.expected_win_rate_change = 0.0
                recommendation.expected_risk_change = -0.3  # 大幅降低风险
                recommendation.expected_return_change = -0.1  # 可能略微降低收益

                recommendation.implementation_cost = 0.3
                recommendation.expected_roi = 1.5
                recommendation.payback_period = 60

                recommendation.validation_metrics = ['sharpe_ratio', 'sortino_ratio', 'max_drawdown']

        return recommendation

    async def _optimize_by_signal_strength(
        self,
        trade_history: List[TradeResult],
        current_win_rate: float
    ) -> OptimizationRecommendation:
        """基于信号强度优化"""
        recommendation = OptimizationRecommendation(
            optimization_target='win_rate',
            current_value=current_win_rate,
            priority='medium'
        )

        # 分析不同强度信号的表现
        strength_performance = self._analyze_strength_performance(trade_history)

        # 找出最佳强度阈值
        best_threshold = self._find_optimal_strength_threshold(strength_performance)
        improvement = self._calculate_threshold_improvement(trade_history, best_threshold)

        if improvement > 0.05:  # 改进超过5%才值得实施
            recommendation.strategy = f"设置信号强度阈值为{best_threshold}"
            recommendation.expected_improvement = improvement
            recommendation.confidence_level = 0.65

            recommendation.implementation_steps = [
                f"只交易强度≥{best_threshold}的信号",
                "降低交易频率，提高信号质量",
                "重新评估强度计算方法"
            ]

            recommendation.parameter_changes = {
                'min_signal_strength': best_threshold,
                'signal_quality_threshold': 0.7,
                'max_daily_trades': 5
            }

            # 模拟结果
            simulated_result = self._simulate_strength_threshold(trade_history, best_threshold)
            recommendation.backtest_results = simulated_result

            recommendation.expected_win_rate_change = improvement
            recommendation.expected_risk_change = -0.15
            recommendation.expected_return_change = improvement * 0.8

            recommendation.implementation_cost = 0.15
            recommendation.expected_roi = improvement * 10
            recommendation.payback_period = 40

            recommendation.validation_metrics = ['win_rate', 'total_trades', 'average_profit']

        return recommendation

    def _analyze_signal_type_performance(self, trades: List[TradeResult]) -> Dict[str, Dict[str, float]]:
        """分析信号类型表现"""
        type_stats = {}

        for signal_type in ShortSignalType:
            type_trades = [t for t in trades if t.signal_type == signal_type]
            if type_trades:
                successful = [t for t in type_trades if t.is_successful]
                win_rate = len(successful) / len(type_trades)

                type_stats[signal_type.value] = {
                    'win_rate': win_rate,
                    'total_trades': len(type_trades),
                    'avg_profit': statistics.mean([t.profit_loss_pct for t in successful]) if successful else 0,
                    'avg_loss': statistics.mean([t.profit_loss_pct for t in type_trades if not t.is_successful]) if len([t for t in type_trades if not t.is_successful]) > 0 else 0
                }

        return type_stats

    def _analyze_strength_performance(self, trades: List[TradeResult]) -> Dict[str, Dict[str, float]]:
        """分析强度表现"""
        strength_stats = {}

        for strength in ShortSignalStrength:
            strength_trades = [t for t in trades if t.signal_strength == strength]
            if strength_trades:
                successful = [t for t in strength_trades if t.is_successful]
                win_rate = len(successful) / len(strength_trades)

                strength_stats[strength.value] = {
                    'win_rate': win_rate,
                    'total_trades': len(strength_trades),
                    'avg_profit': statistics.mean([t.profit_loss_pct for t in successful]) if successful else 0,
                    'strength_value': strength.value
                }

        return strength_stats

    def _find_optimal_strength_threshold(self, strength_performance: Dict[str, Dict[str, float]]) -> int:
        """找到最佳强度阈值"""
        # 按强度值排序
        sorted_strengths = sorted(strength_performance.items(), key=lambda x: x[1]['strength_value'])

        best_threshold = 1
        best_combined_score = 0

        # 测试不同的阈值
        for threshold in [1, 2, 3]:
            included_trades = sum([data['total_trades'] for strength, data in sorted_strengths if data['strength_value'] >= threshold])
            included_wins = sum([data['win_rate'] * data['total_trades'] for strength, data in sorted_strengths if data['strength_value'] >= threshold])

            if included_trades > 0:
                win_rate = included_wins / included_trades
                trade_factor = included_trades / sum([data['total_trades'] for data in strength_performance.values()])
                combined_score = win_rate * trade_factor

                if combined_score > best_combined_score:
                    best_combined_score = combined_score
                    best_threshold = threshold

        return best_threshold

    def _calculate_threshold_improvement(self, trades: List[TradeResult], threshold: int) -> float:
        """计算阈值改进效果"""
        filtered_trades = [t for t in trades if t.signal_strength and t.signal_strength >= threshold]

        if not filtered_trades:
            return 0

        current_win_rate = len([t for t in trades if t.is_successful]) / len(trades) if trades else 0
        new_win_rate = len([t for t in filtered_trades if t.is_successful]) / len(filtered_trades)

        return new_win_rate - current_win_rate

    def _calculate_optimal_position_size(self, returns: List[float], volatility: float) -> float:
        """使用凯利准则计算最优仓位"""
        if len(returns) < 2 or volatility == 0:
            return 0.1  # 默认10%

        avg_return = statistics.mean(returns)
        win_rate = len([r for r in returns if r > 0]) / len(returns)

        # 简化的凯利公式
        kelly_fraction = (win_rate * avg_return - (1 - win_rate) * abs(avg_return)) / (volatility ** 2)

        # 限制在合理范围内
        return max(0.05, min(0.25, kelly_fraction))

    def _simulate_signal_type_filtering(self, trades: List[TradeResult], signal_type: str) -> Dict[str, float]:
        """模拟信号类型过滤"""
        filtered_trades = [t for t in trades if t.signal_type and t.signal_type.value == signal_type]

        if not filtered_trades:
            return {'win_rate': 0, 'total_trades': 0, 'profit_factor': 0}

        successful = [t for t in filtered_trades if t.is_successful]
        win_rate = len(successful) / len(filtered_trades)

        profits = [t.profit_loss_pct for t in successful]
        losses = [t.profit_loss_pct for t in filtered_trades if not t.is_successful]

        profit_factor = abs(sum(profits) / sum(losses)) if losses and sum(losses) != 0 else 0

        return {
            'win_rate': win_rate,
            'total_trades': len(filtered_trades),
            'profit_factor': profit_factor,
            'avg_profit': statistics.mean(profits) if profits else 0,
            'avg_loss': statistics.mean(losses) if losses else 0
        }

    def _simulate_optimized_stops(self, trades: List[TradeResult], new_stop_loss: float) -> Dict[str, float]:
        """模拟优化止损"""
        # 简化模拟，假设优化止损会减少亏损幅度
        original_losses = [t.profit_loss_pct for t in trades if not t.is_successful]
        optimized_losses = [max(l, -new_stop_loss) for l in original_losses]

        profitable_trades = [t for t in trades if t.is_successful]
        win_rate = len(profitable_trades) / len(trades)

        total_profit = sum([t.profit_loss_pct for t in profitable_trades])
        total_loss = sum(optimized_losses)

        profit_factor = abs(total_profit / total_loss) if total_loss != 0 else 0

        return {
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_loss': statistics.mean(optimized_losses),
            'max_loss': min(optimized_losses)
        }

    def _simulate_position_sizing(self, trades: List[TradeResult], position_size: float) -> Dict[str, float]:
        """模拟仓位管理"""
        # 假设所有交易使用相同仓位大小
        scaled_returns = [r * position_size for r in [t.profit_loss_pct for t in trades]]

        if len(scaled_returns) > 1:
            volatility = statistics.stdev(scaled_returns)
            sharpe_ratio = statistics.mean(scaled_returns) / volatility if volatility > 0 else 0
        else:
            sharpe_ratio = 0

        return {
            'sharpe_ratio': sharpe_ratio,
            'volatility': volatility,
            'avg_return': statistics.mean(scaled_returns),
            'max_return': max(scaled_returns),
            'min_return': min(scaled_returns)
        }

    def _simulate_strength_threshold(self, trades: List[TradeResult], threshold: int) -> Dict[str, float]:
        """模拟强度阈值"""
        filtered_trades = [t for t in trades if t.signal_strength and t.signal_strength >= threshold]

        if not filtered_trades:
            return {'win_rate': 0, 'total_trades': 0}

        successful = [t for t in filtered_trades if t.is_successful]
        win_rate = len(successful) / len(filtered_trades)

        return {
            'win_rate': win_rate,
            'total_trades': len(filtered_trades),
            'avg_profit': statistics.mean([t.profit_loss_pct for t in successful]) if successful else 0,
            'profit_factor': self._calculate_profit_factor(filtered_trades)
        }

    def _calculate_profit_factor(self, trades: List[TradeResult]) -> float:
        """计算盈亏比"""
        profitable_trades = [t for t in trades if t.is_successful]
        losing_trades = [t for t in trades if not t.is_successful]

        if not losing_trades:
            return float('inf')

        total_profit = sum([t.profit_loss_pct for t in profitable_trades])
        total_loss = sum([t.profit_loss_pct for t in losing_trades])

        return abs(total_profit / total_loss) if total_loss != 0 else 0

    def _create_insufficient_data_recommendation(self) -> List[OptimizationRecommendation]:
        """创建数据不足的建议"""
        recommendation = OptimizationRecommendation(
            optimization_target='data_collection',
            current_value=0,
            expected_improvement=0,
            confidence_level=0,
            strategy="收集更多交易数据",
            implementation_steps=[
                "继续正常交易以积累数据",
                "确保记录完整的交易信息",
                "等待至少30天数据后再进行优化"
            ],
            priority='low',
            status='proposed'
        )

        return [recommendation]

    async def generate_signal_quality_report(
        self,
        signal_history: List[ShortSignal],
        trade_history: List[TradeResult]
    ) -> Dict[str, Any]:
        """生成信号质量报告"""
        report = {
            'report_time': datetime.now().isoformat(),
            'total_signals': len(signal_history),
            'executed_trades': len(trade_history),
            'signal_types': {},
            'strength_distribution': {},
            'quality_trends': {},
            'recommendations': []
        }

        # 信号类型分析
        type_counts = {}
        for signal in signal_history:
            signal_type = signal.signal_type.value
            type_counts[signal_type] = type_counts.get(signal_type, 0) + 1
        report['signal_types'] = type_counts

        # 强度分布分析
        strength_counts = {}
        for signal in signal_history:
            strength = signal.strength.value
            strength_counts[strength] = strength_counts.get(strength, 0) + 1
        report['strength_distribution'] = strength_counts

        # 质量趋势分析（如果时间序列数据足够）
        if len(signal_history) > 30:
            # 按月份分组分析
            monthly_quality = self._analyze_monthly_quality(signal_history)
            report['quality_trends'] = monthly_quality

        return report

    def _analyze_monthly_quality(self, signals: List[ShortSignal]) -> Dict[str, Dict[str, float]]:
        """分析月度质量趋势"""
        monthly_stats = {}

        for signal in signals:
            month_key = signal.detected_at.strftime('%Y-%m')
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    'total_signals': 0,
                    'total_confidence': 0,
                    'avg_strength': 0,
                    'high_quality_signals': 0
                }

            monthly_stats[month_key]['total_signals'] += 1
            monthly_stats[month_key]['total_confidence'] += signal.confidence_score
            monthly_stats[month_key]['avg_strength'] += signal.strength.value

            if signal.confidence_score > 0.7:
                monthly_stats[month_key]['high_quality_signals'] += 1

        # 计算平均值
        for month, stats in monthly_stats.items():
            stats['avg_confidence'] = stats['total_confidence'] / stats['total_signals']
            stats['avg_strength'] = stats['avg_strength'] / stats['total_signals']
            stats['quality_ratio'] = stats['high_quality_signals'] / stats['total_signals']

        return monthly_stats

    def _initialize_parameter_ranges(self) -> Dict[str, Tuple[float, float]]:
        """初始化参数范围"""
        return {
            'min_confidence_threshold': (0.5, 0.9),
            'min_signal_strength': (1, 3),
            'max_position_size': (0.05, 0.3),
            'stop_loss_distance': (0.01, 0.05),
            'take_profit_distance': (0.02, 0.1),
            'max_leverage': (1.0, 5.0)
        }