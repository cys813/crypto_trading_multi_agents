"""
做空胜率计算引擎

该模块实现了基于历史交易数据的胜率计算和统计分析功能。
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
import statistics
import math as math_lib
from typing import Tuple as TupleType
from dataclasses import dataclass

from .win_rate_models import (
    TradeResult, WinRateAnalysis, PerformanceMetrics,
    WinRateMetric, ShortSignalType, ShortSignalStrength
)
from ..models.short_signal import ShortSignal


class WinRateCalculator:
    """胜率计算引擎"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化胜率计算引擎

        Args:
            config: 配置参数
        """
        self.config = config or {}
        self.min_sample_size = self.config.get('min_sample_size', 30)
        self.confidence_level = self.config.get('confidence_level', 0.95)
        self.max_history_days = self.config.get('max_history_days', 365)

        # 缓存计算结果
        self.cache = {}
        self.cache_ttl = self.config.get('cache_ttl', 300)  # 5分钟

    async def calculate_win_rate(
        self,
        trade_history: List[TradeResult],
        signal_history: List[ShortSignal],
        metrics: List[WinRateMetric] = None,
        period: str = "30d"
    ) -> WinRateAnalysis:
        """
        计算胜率分析

        Args:
            trade_history: 交易历史
            signal_history: 信号历史
            metrics: 要计算的指标列表
            period: 分析时间段

        Returns:
            WinRateAnalysis: 胜率分析结果
        """
        if metrics is None:
            metrics = [
                WinRateMetric.OVERALL_SUCCESS_RATE,
                WinRateMetric.SIGNAL_TYPE_SUCCESS,
                WinRateMetric.TIME_PERIOD_SUCCESS,
                WinRateMetric.STRENGTH_CORRELATION
            ]

        # 过滤时间段内的交易
        filtered_trades = self._filter_trades_by_period(trade_history, period)

        if len(filtered_trades) < self.min_sample_size:
            return self._create_insufficient_data_analysis(filtered_trades, period)

        # 创建分析结果
        analysis = WinRateAnalysis(
            symbol=filtered_trades[0].symbol if filtered_trades else "",
            time_period=period,
            total_signals=len(filtered_trades)
        )

        # 计算各项指标
        await self._calculate_overall_success_rate(analysis, filtered_trades)
        await self._calculate_signal_type_analysis(analysis, filtered_trades)
        await self._calculate_strength_correlation(analysis, filtered_trades)
        await self._calculate_time_period_analysis(analysis, filtered_trades)
        await self._calculate_market_condition_analysis(analysis, filtered_trades)
        await self._calculate_profit_loss_metrics(analysis, filtered_trades)
        await self._calculate_risk_adjusted_metrics(analysis, filtered_trades)
        await self._calculate_statistical_significance(analysis, filtered_trades)
        await self._generate_insights_and_suggestions(analysis, filtered_trades)

        return analysis

    async def calculate_performance_metrics(
        self,
        trade_history: List[TradeResult],
        period: str = "30d",
        benchmark_return: float = 0.0
    ) -> PerformanceMetrics:
        """
        计算绩效指标

        Args:
            trade_history: 交易历史
            period: 分析时间段
            benchmark_return: 基准收益率

        Returns:
            PerformanceMetrics: 绩效指标集合
        """
        filtered_trades = self._filter_trades_by_period(trade_history, period)

        if not filtered_trades:
            return self._create_empty_performance_metrics(period)

        metrics = PerformanceMetrics(
            symbol=filtered_trades[0].symbol if filtered_trades else "",
            period=period
        )

        # 基础统计
        winning_trades = [t for t in filtered_trades if t.is_successful]
        losing_trades = [t for t in filtered_trades if not t.is_successful]

        metrics.total_trades = len(filtered_trades)
        metrics.winning_trades = len(winning_trades)
        metrics.losing_trades = len(losing_trades)
        metrics.breakeven_trades = len([t for t in filtered_trades if abs(t.profit_loss_pct) < 0.001])

        # 胜率指标
        metrics.win_rate = len(winning_trades) / len(filtered_trades) if filtered_trades else 0
        metrics.win_rate_weighted = self._calculate_weighted_win_rate(filtered_trades)
        metrics.win_rate_volume = self._calculate_volume_weighted_win_rate(filtered_trades)

        # 盈亏统计
        profits = [t.profit_loss_pct for t in winning_trades]
        losses = [t.profit_loss_pct for t in losing_trades]

        metrics.total_profit = sum(profits)
        metrics.total_loss = sum(losses)
        metrics.net_profit = metrics.total_profit + metrics.total_loss  # losses are negative
        metrics.average_profit = statistics.mean(profits) if profits else 0
        metrics.average_loss = statistics.mean(losses) if losses else 0
        metrics.profit_factor = abs(metrics.total_profit / metrics.total_loss) if metrics.total_loss != 0 else 0

        # 风险调整收益
        returns = [t.profit_loss_pct for t in filtered_trades]
        if len(returns) > 1:
            risk_free_rate = 0.02 / 252  # 假设日无风险利率
            excess_returns = [r - risk_free_rate for r in returns]

            metrics.sharpe_ratio = statistics.mean(excess_returns) / statistics.stdev(excess_returns) if statistics.stdev(excess_returns) > 0 else 0

            negative_returns = [r for r in excess_returns if r < 0]
            if negative_returns:
                downside_std = statistics.stdev(negative_returns)
                metrics.sortino_ratio = statistics.mean(excess_returns) / downside_std if downside_std > 0 else 0

            if metrics.max_drawdown != 0:
                metrics.calmar_ratio = metrics.net_profit / abs(metrics.max_drawdown)

        # 回撤统计
        metrics.max_drawdown = self._calculate_max_drawdown(filtered_trades)
        metrics.max_drawdown_duration = self._calculate_max_drawdown_duration(filtered_trades)
        metrics.average_drawdown = self._calculate_average_drawdown(filtered_trades)
        metrics.recovery_time = self._calculate_average_recovery_time(filtered_trades)

        # 连续统计
        consecutive_wins, consecutive_losses = self._calculate_consecutive_trades(filtered_trades)
        metrics.max_consecutive_wins = max(consecutive_wins) if consecutive_wins else 0
        metrics.max_consecutive_losses = max(consecutive_losses) if consecutive_losses else 0
        metrics.average_consecutive_wins = statistics.mean(consecutive_wins) if consecutive_wins else 0
        metrics.average_consecutive_losses = statistics.mean(consecutive_losses) if consecutive_losses else 0

        # 时间统计
        holding_times = [t.holding_period for t in filtered_trades if t.holding_period > 0]
        if holding_times:
            metrics.average_holding_time = statistics.mean(holding_times)
            metrics.median_holding_time = statistics.median(holding_times)

        # 按分类统计
        metrics.performance_by_signal_type = self._calculate_performance_by_signal_type(filtered_trades)
        metrics.performance_by_strength = self._calculate_performance_by_strength(filtered_trades)

        # 统计指标
        if len(profits) > 1:
            metrics.profit_std_dev = statistics.stdev(profits)
        if len(losses) > 1:
            metrics.loss_std_dev = statistics.stdev(losses)

        metrics.profit_skewness = self._calculate_skewness(profits) if len(profits) > 2 else 0
        metrics.loss_skewness = self._calculate_skewness(losses) if len(losses) > 2 else 0
        metrics.kurtosis = self._calculate_kurtosis(returns) if len(returns) > 3 else 0

        # 效率指标
        metrics.trade_efficiency = self._calculate_trade_efficiency(filtered_trades)
        metrics.capital_efficiency = self._calculate_capital_efficiency(filtered_trades)
        metrics.time_efficiency = self._calculate_time_efficiency(filtered_trades)

        # 基准比较
        metrics.benchmark_performance = benchmark_return
        metrics.alpha = metrics.net_profit - benchmark_return
        if len(returns) > 1:
            correlation = self._calculate_correlation(returns, [benchmark_return] * len(returns))
            metrics.beta = correlation * (statistics.stdev(returns) / statistics.stdev([benchmark_return])) if len([benchmark_return]) > 1 and statistics.stdev([benchmark_return]) > 0 else 0
            metrics.r_squared = correlation ** 2

        return metrics

    def _filter_trades_by_period(self, trades: List[TradeResult], period: str) -> List[TradeResult]:
        """按时间段过滤交易"""
        if not trades:
            return []

        now = datetime.now()
        period_days = self._parse_period(period)
        cutoff_date = now - timedelta(days=period_days)

        return [t for t in trades if t.entry_time >= cutoff_date]

    def _parse_period(self, period: str) -> int:
        """解析时间段字符串"""
        if period.endswith('d'):
            return int(period[:-1])
        elif period.endswith('w'):
            return int(period[:-1]) * 7
        elif period.endswith('m'):
            return int(period[:-1]) * 30
        elif period.endswith('y'):
            return int(period[:-1]) * 365
        else:
            return 30  # 默认30天

    async def _calculate_overall_success_rate(self, analysis: WinRateAnalysis, trades: List[TradeResult]):
        """计算整体成功率"""
        successful_trades = [t for t in trades if t.is_successful]
        analysis.successful_signals = len(successful_trades)
        analysis.failed_signals = len(trades) - len(successful_trades)
        analysis.overall_success_rate = len(successful_trades) / len(trades) if trades else 0

        # 计算置信区间
        if len(trades) > 0:
            z_score = 1.96  # 95%置信度
            margin_of_error = z_score * math.sqrt((analysis.overall_success_rate * (1 - analysis.overall_success_rate)) / len(trades))
            analysis.confidence_interval = (
                max(0, analysis.overall_success_rate - margin_of_error),
                min(1, analysis.overall_success_rate + margin_of_error)
            )

    async def _calculate_signal_type_analysis(self, analysis: WinRateAnalysis, trades: List[TradeResult]):
        """计算信号类型分析"""
        signal_type_stats = {}

        for signal_type in ShortSignalType:
            type_trades = [t for t in trades if t.signal_type == signal_type]
            if type_trades:
                success_rate = len([t for t in type_trades if t.is_successful]) / len(type_trades)
                signal_type_stats[signal_type.value] = success_rate
                analysis.volume_by_signal_type[signal_type.value] = len(type_trades)

        analysis.success_by_signal_type = signal_type_stats

    async def _calculate_strength_correlation(self, analysis: WinRateAnalysis, trades: List[TradeResult]):
        """计算强度相关性"""
        strength_stats = {}
        strength_values = []
        success_values = []

        for strength in ShortSignalStrength:
            strength_trades = [t for t in trades if t.signal_strength == strength]
            if strength_trades:
                success_rate = len([t for t in strength_trades if t.is_successful]) / len(strength_trades)
                strength_stats[strength.value] = success_rate

                # 为相关性分析准备数据
                strength_values.extend([strength.value] * len(strength_trades))
                success_values.extend([1 if t.is_successful else 0 for t in strength_trades])

        analysis.success_by_strength = strength_stats

        # 计算相关性
        if len(strength_values) > 1:
            correlation = self._calculate_correlation(strength_values, success_values)
            analysis.strength_correlation = correlation if not math_lib.isnan(correlation) else 0

    async def _calculate_time_period_analysis(self, analysis: WinRateAnalysis, trades: List[TradeResult]):
        """计算时间段分析"""
        if not trades:
            return

        # 按月份分组
        monthly_stats = {}
        for trade in trades:
            month_key = trade.entry_time.strftime('%Y-%m')
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {'wins': 0, 'total': 0}
            monthly_stats[month_key]['total'] += 1
            if trade.is_successful:
                monthly_stats[month_key]['wins'] += 1

        # 计算每月成功率
        for month, stats in monthly_stats.items():
            success_rate = stats['wins'] / stats['total']
            analysis.success_by_time_period[month] = success_rate

        # 分析趋势
        months = sorted(monthly_stats.keys())
        if len(months) >= 3:
            recent_rates = [monthly_stats[m]['wins'] / monthly_stats[m]['total'] for m in months[-3:]]
            early_rates = [monthly_stats[m]['wins'] / monthly_stats[m]['total'] for m in months[:3]]

            if statistics.mean(recent_rates) > statistics.mean(early_rates):
                analysis.performance_trend = "improving"
            elif statistics.mean(recent_rates) < statistics.mean(early_rates):
                analysis.performance_trend = "declining"
            else:
                analysis.performance_trend = "stable"

    async def _calculate_market_condition_analysis(self, analysis: WinRateAnalysis, trades: List[TradeResult]):
        """计算市场条件分析"""
        condition_stats = {}

        for trade in trades:
            # 简化的市场条件判断
            volatility_level = self._classify_volatility(trade.volatility_at_entry)

            if volatility_level not in condition_stats:
                condition_stats[volatility_level] = {'wins': 0, 'total': 0}

            condition_stats[volatility_level]['total'] += 1
            if trade.is_successful:
                condition_stats[volatility_level]['wins'] += 1

        # 计算各种市场条件下的成功率
        for condition, stats in condition_stats.items():
            if stats['total'] > 5:  # 只考虑样本充足的条件
                success_rate = stats['wins'] / stats['total']
                analysis.success_by_market_condition[condition] = success_rate

        # 找出最佳和最差市场条件
        sorted_conditions = sorted(
            analysis.success_by_market_condition.items(),
            key=lambda x: x[1],
            reverse=True
        )

        if sorted_conditions:
            analysis.best_market_conditions = [c[0] for c in sorted_conditions[:3]]
            analysis.worst_market_conditions = [c[0] for c in sorted_conditions[-3:]]

    async def _calculate_profit_loss_metrics(self, analysis: WinRateAnalysis, trades: List[TradeResult]):
        """计算盈亏统计"""
        profitable_trades = [t for t in trades if t.is_successful]
        losing_trades = [t for t in trades if not t.is_successful]

        if profitable_trades:
            analysis.average_profit = statistics.mean([t.profit_loss_pct for t in profitable_trades])
        if losing_trades:
            analysis.average_loss = statistics.mean([t.profit_loss_pct for t in losing_trades])

        total_profit = sum([t.profit_loss_pct for t in profitable_trades])
        total_loss = sum([t.profit_loss_pct for t in losing_trades])

        analysis.profit_factor = abs(total_profit / total_loss) if total_loss != 0 else 0

        # 计算连续统计
        consecutive_wins, consecutive_losses = self._calculate_consecutive_trades(trades)
        analysis.max_consecutive_wins = max(consecutive_wins) if consecutive_wins else 0
        analysis.max_consecutive_losses = max(consecutive_losses) if consecutive_losses else 0

    async def _calculate_risk_adjusted_metrics(self, analysis: WinRateAnalysis, trades: List[TradeResult]):
        """计算风险调整指标"""
        returns = [t.profit_loss_pct for t in trades]

        if len(returns) > 1:
            # 计算夏普比率
            risk_free_rate = 0.02 / 252  # 日无风险利率
            excess_returns = [r - risk_free_rate for r in returns]

            if statistics.stdev(excess_returns) > 0:
                analysis.sharpe_ratio = statistics.mean(excess_returns) / statistics.stdev(excess_returns)

            # 计算索提诺比率
            negative_returns = [r for r in excess_returns if r < 0]
            if negative_returns:
                downside_std = statistics.stdev(negative_returns)
                analysis.sortino_ratio = statistics.mean(excess_returns) / downside_std if downside_std > 0 else 0

        # 计算最大回撤
        analysis.max_drawdown = self._calculate_max_drawdown(trades)

        # 计算恢复因子
        if analysis.max_drawdown != 0:
            total_profit = sum([t.profit_loss_pct for t in trades if t.is_successful])
            analysis.recovery_factor = total_profit / abs(analysis.max_drawdown)

    async def _calculate_statistical_significance(self, analysis: WinRateAnalysis, trades: List[TradeResult]):
        """计算统计显著性"""
        if len(trades) < 10:
            return

        # 二项检验
        n = len(trades)
        k = analysis.successful_signals
        p = 0.5  # 假设零假设为50%成功率

        # 计算p值（简化实现）
        p_value = self._calculate_binomial_p_value(k, n, p)
        analysis.p_value = p_value
        analysis.is_statistically_significant = p_value < 0.05

    async def _generate_insights_and_suggestions(self, analysis: WinRateAnalysis, trades: List[TradeResult]):
        """生成洞察和建议"""
        insights = []
        suggestions = []

        # 整体表现洞察
        if analysis.overall_success_rate > 0.6:
            insights.append(f"整体成功率较高 ({analysis.overall_success_rate:.1%})")
        elif analysis.overall_success_rate < 0.4:
            insights.append(f"整体成功率较低 ({analysis.overall_success_rate:.1%})，需要改进")

        # 信号类型洞察
        if analysis.success_by_signal_type:
            best_type = max(analysis.success_by_signal_type.items(), key=lambda x: x[1])
            worst_type = min(analysis.success_by_signal_type.items(), key=lambda x: x[1])
            insights.append(f"最佳信号类型: {best_type[0]} ({best_type[1]:.1%})")
            insights.append(f"最差信号类型: {worst_type[0]} ({worst_type[1]:.1%})")

        # 强度相关性洞察
        if analysis.strength_correlation > 0.5:
            insights.append(f"信号强度与成功率高度正相关 (r={analysis.strength_correlation:.3f})")
            suggestions.append("重点关注高强度信号，可考虑提高信号强度阈值")
        elif analysis.strength_correlation < 0:
            insights.append("信号强度与成功率呈负相关，需要重新评估强度计算方法")

        # 市场条件洞察
        if analysis.best_market_conditions:
            best_condition = analysis.best_market_conditions[0]
            insights.append(f"最佳市场条件: {best_condition}")
            suggestions.append(f"在{best_condition}市场条件下可增加交易频率")

        # 风险调整洞察
        if analysis.sharpe_ratio > 1.0:
            insights.append(f"风险调整收益良好 (夏普比率={analysis.sharpe_ratio:.3f})")
        elif analysis.sharpe_ratio < 0:
            insights.append("风险调整收益为负，需要重新评估策略")

        # 连续亏损洞察
        if analysis.max_consecutive_losses > 3:
            insights.append(f"最大连续亏损次数较多 ({analysis.max_consecutive_losses}次)")
            suggestions.append("设置最大连续亏损限制，避免情绪化交易")

        analysis.key_insights = insights
        analysis.improvement_suggestions = suggestions

    def _classify_volatility(self, volatility: float) -> str:
        """分类波动率水平"""
        if volatility < 0.02:
            return "low_volatility"
        elif volatility < 0.05:
            return "medium_volatility"
        else:
            return "high_volatility"

    def _calculate_weighted_win_rate(self, trades: List[TradeResult]) -> float:
        """计算加权胜率"""
        if not trades:
            return 0

        total_weight = 0
        weighted_success = 0

        for trade in trades:
            weight = abs(trade.profit_loss_pct)  # 按盈亏比例加权
            total_weight += weight
            if trade.is_successful:
                weighted_success += weight

        return weighted_success / total_weight if total_weight > 0 else 0

    def _calculate_volume_weighted_win_rate(self, trades: List[TradeResult]) -> float:
        """计算成交量加权胜率"""
        if not trades:
            return 0

        total_volume = sum([t.volume_at_entry for t in trades])
        if total_volume == 0:
            return 0

        volume_weighted_success = 0
        for trade in trades:
            if trade.is_successful:
                volume_weighted_success += trade.volume_at_entry

        return volume_weighted_success / total_volume

    def _calculate_max_drawdown(self, trades: List[TradeResult]) -> float:
        """计算最大回撤"""
        if not trades:
            return 0

        cumulative_returns = []
        running_total = 0

        for trade in sorted(trades, key=lambda x: x.entry_time):
            running_total += trade.profit_loss_pct
            cumulative_returns.append(running_total)

        peak = cumulative_returns[0]
        max_dd = 0

        for value in cumulative_returns:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_dd = max(max_dd, drawdown)

        return max_dd

    def _calculate_max_drawdown_duration(self, trades: List[TradeResult]) -> float:
        """计算最大回撤持续时间"""
        # 简化实现，返回0
        return 0

    def _calculate_average_drawdown(self, trades: List[TradeResult]) -> float:
        """计算平均回撤"""
        # 简化实现，返回0
        return 0

    def _calculate_average_recovery_time(self, trades: List[TradeResult]) -> float:
        """计算平均恢复时间"""
        # 简化实现，返回0
        return 0

    def _calculate_consecutive_trades(self, trades: List[TradeResult]) -> Tuple[List[int], List[int]]:
        """计算连续交易统计"""
        if not trades:
            return [], []

        consecutive_wins = []
        consecutive_losses = []

        current_wins = 0
        current_losses = 0

        for trade in sorted(trades, key=lambda x: x.entry_time):
            if trade.is_successful:
                current_wins += 1
                if current_losses > 0:
                    consecutive_losses.append(current_losses)
                    current_losses = 0
            else:
                current_losses += 1
                if current_wins > 0:
                    consecutive_wins.append(current_wins)
                    current_wins = 0

        # 添加最后一个序列
        if current_wins > 0:
            consecutive_wins.append(current_wins)
        if current_losses > 0:
            consecutive_losses.append(current_losses)

        return consecutive_wins, consecutive_losses

    def _calculate_performance_by_signal_type(self, trades: List[TradeResult]) -> Dict[str, Dict[str, float]]:
        """按信号类型计算绩效"""
        type_stats = {}

        for signal_type in ShortSignalType:
            type_trades = [t for t in trades if t.signal_type == signal_type]
            if type_trades:
                stats = self._calculate_basic_stats(type_trades)
                type_stats[signal_type.value] = stats

        return type_stats

    def _calculate_performance_by_strength(self, trades: List[TradeResult]) -> Dict[str, Dict[str, float]]:
        """按强度计算绩效"""
        strength_stats = {}

        for strength in ShortSignalStrength:
            strength_trades = [t for t in trades if t.signal_strength == strength]
            if strength_trades:
                stats = self._calculate_basic_stats(strength_trades)
                strength_stats[strength.value] = stats

        return strength_stats

    def _calculate_basic_stats(self, trades: List[TradeResult]) -> Dict[str, float]:
        """计算基础统计"""
        if not trades:
            return {}

        successful_trades = [t for t in trades if t.is_successful]
        total_trades = len(trades)

        return {
            'win_rate': len(successful_trades) / total_trades,
            'total_trades': total_trades,
            'avg_profit': statistics.mean([t.profit_loss_pct for t in successful_trades]) if successful_trades else 0,
            'max_profit': max([t.profit_loss_pct for t in successful_trades]) if successful_trades else 0,
            'min_profit': min([t.profit_loss_pct for t in successful_trades]) if successful_trades else 0,
        }

    def _calculate_trade_efficiency(self, trades: List[TradeResult]) -> float:
        """计算交易效率"""
        # 简化实现，返回0.5
        return 0.5

    def _calculate_capital_efficiency(self, trades: List[TradeResult]) -> float:
        """计算资本效率"""
        # 简化实现，返回0.5
        return 0.5

    def _calculate_time_efficiency(self, trades: List[TradeResult]) -> float:
        """计算时间效率"""
        # 简化实现，返回0.5
        return 0.5

    def _create_insufficient_data_analysis(self, trades: List[TradeResult], period: str) -> WinRateAnalysis:
        """创建数据不足的分析结果"""
        return WinRateAnalysis(
            symbol=trades[0].symbol if trades else "",
            time_period=period,
            total_signals=len(trades),
            sample_size_adequacy=False,
            key_insights=["样本数据不足，需要更多交易数据进行分析"],
            data_quality_score=0.3
        )

    def _create_empty_performance_metrics(self, period: str) -> PerformanceMetrics:
        """创建空的绩效指标"""
        return PerformanceMetrics(period=period)

    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            'cache_size': len(self.cache),
            'cache_ttl': self.cache_ttl
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
        denominator = math_lib.sqrt((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2))

        return numerator / denominator if denominator != 0 else 0.0

    def _calculate_skewness(self, data: List[float]) -> float:
        """计算偏度"""
        if len(data) < 3:
            return 0.0

        n = len(data)
        mean = statistics.mean(data)
        std = statistics.stdev(data)

        if std == 0:
            return 0.0

        skewness = (sum((x - mean) ** 3 for x in data) / n) / (std ** 3)
        return skewness

    def _calculate_kurtosis(self, data: List[float]) -> float:
        """计算峰度"""
        if len(data) < 4:
            return 0.0

        n = len(data)
        mean = statistics.mean(data)
        std = statistics.stdev(data)

        if std == 0:
            return 0.0

        kurtosis = (sum((x - mean) ** 4 for x in data) / n) / (std ** 4) - 3
        return kurtosis

    def _calculate_binomial_p_value(self, k: int, n: int, p: float) -> float:
        """计算二项检验p值（简化实现）"""
        if n == 0:
            return 1.0

        observed_rate = k / n
        expected_rate = p

        # 简化的p值计算，基于偏差程度
        deviation = abs(observed_rate - expected_rate)
        p_value = 2 * (1 - self._normal_cdf(deviation / math_lib.sqrt(p * (1 - p) / n)))

        return min(1.0, max(0.0, p_value))

    def _normal_cdf(self, x: float) -> float:
        """标准正态分布累积函数（近似）"""
        # Abramowitz and Stegun 公式 26.2.17
        a1 =  0.254829592
        a2 = -0.284496736
        a3 =  1.421413741
        a4 = -1.453152027
        a5 =  1.061405429
        p  =  0.3275911

        sign = 1 if x >= 0 else -1
        x = abs(x) / math_lib.sqrt(2.0)

        t = 1.0 / (1.0 + p * x)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math_lib.exp(-x * x)

        return 0.5 * (1.0 + sign * y)