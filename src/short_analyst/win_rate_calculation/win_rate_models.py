"""
做空胜率计算与风险评估模型定义

该模块定义了做空胜率计算和风险评估中使用的数据结构和枚举。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
import uuid
import statistics
import math as math_lib

from ..models.short_signal import ShortSignal, ShortSignalType, ShortSignalStrength


class WinRateMetric(Enum):
    """胜率计算指标类型"""
    OVERALL_SUCCESS_RATE = "overall_success_rate"           # 整体成功率
    SIGNAL_TYPE_SUCCESS = "signal_type_success"             # 信号类型成功率
    TIME_PERIOD_SUCCESS = "time_period_success"             # 时间段成功率
    MARKET_CONDITION_SUCCESS = "market_condition_success"   # 市场条件成功率
    STRENGTH_CORRELATION = "strength_correlation"           # 强度相关性
    VOLATILITY_ADJUSTED = "volatility_adjusted"             # 波动率调整胜率


class RiskCategory(Enum):
    """风险类别"""
    MARKET_RISK = "market_risk"              # 市场风险
    LIQUIDITY_RISK = "liquidity_risk"        # 流动性风险
    VOLATILITY_RISK = "volatility_risk"      # 波动率风险
    LEVERAGE_RISK = "leverage_risk"          # 杠杆风险
    SHORT_SQUEEZE_RISK = "short_squeeze_risk" # 轧空风险
    REGULATORY_RISK = "regulatory_risk"      # 监管风险
    BLACK_SWAN_RISK = "black_swan_risk"     # 黑天鹅风险


class PerformanceMetric(Enum):
    """绩效指标"""
    TOTAL_TRADES = "total_trades"                 # 总交易次数
    SUCCESSFUL_TRADES = "successful_trades"       # 成功交易次数
    FAILED_TRADES = "failed_trades"               # 失败交易次数
    SUCCESS_RATE = "success_rate"                 # 成功率
    AVERAGE_PROFIT = "average_profit"             # 平均盈利
    AVERAGE_LOSS = "average_loss"                 # 平均亏损
    PROFIT_FACTOR = "profit_factor"               # 盈亏比
    MAX_DRAWDOWN = "max_drawdown"                 # 最大回撤
    SHARPE_RATIO = "sharpe_ratio"                 # 夏普比率
    SORTINO_RATIO = "sortino_ratio"               # 索提诺比率
    CALMAR_RATIO = "calmar_ratio"                 # 卡尔马比率
    AVERAGE_HOLDING_TIME = "average_holding_time" # 平均持仓时间


@dataclass
class TradeResult:
    """交易结果"""
    trade_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    signal_id: str = ""
    symbol: str = ""

    # 交易详情
    entry_price: float = 0.0
    exit_price: float = 0.0
    entry_time: datetime = field(default_factory=datetime.now)
    exit_time: datetime = field(default_factory=datetime.now)

    # 盈亏计算
    profit_loss: float = 0.0      # 盈亏金额
    profit_loss_pct: float = 0.0  # 盈亏百分比
    fees: float = 0.0             # 手续费

    # 交易属性
    signal_type: Optional[ShortSignalType] = None
    signal_strength: Optional[ShortSignalStrength] = None
    holding_period: float = 0.0  # 持仓时间（小时）

    # 市场条件
    market_conditions: Dict[str, Any] = field(default_factory=dict)
    volatility_at_entry: float = 0.0
    volume_at_entry: float = 0.0

    # 结果状态
    is_successful: bool = False
    exit_reason: str = ""  # profit_target, stop_loss, timeout, manual

    # 风险指标
    max_drawdown: float = 0.0
    risk_reward_ratio: float = 0.0

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        if self.entry_price > 0 and self.exit_price > 0:
            # 计算盈亏百分比（做空：入场价 - 出场价）/ 入场价
            self.profit_loss_pct = (self.entry_price - self.exit_price) / self.entry_price
            self.is_successful = self.profit_loss_pct > 0

        # 计算持仓时间
        if self.exit_time > self.entry_time:
            self.holding_period = (self.exit_time - self.entry_time).total_seconds() / 3600

        # 计算风险回报比
        if self.profit_loss_pct > 0 and self.max_drawdown > 0:
            self.risk_reward_ratio = abs(self.profit_loss_pct / self.max_drawdown)


@dataclass
class WinRateAnalysis:
    """胜率分析结果"""
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    analysis_time: datetime = field(default_factory=datetime.now)
    symbol: str = ""
    time_period: str = ""  # 7d, 30d, 90d, 1y

    # 基础统计
    total_signals: int = 0
    successful_signals: int = 0
    failed_signals: int = 0

    # 胜率指标
    overall_success_rate: float = 0.0  # 整体成功率
    weighted_success_rate: float = 0.0  # 加权成功率（按信号强度）
    confidence_interval: Tuple[float, float] = (0.0, 0.0)  # 95%置信区间

    # 信号类型分析
    success_by_signal_type: Dict[str, float] = field(default_factory=dict)
    volume_by_signal_type: Dict[str, int] = field(default_factory=dict)

    # 强度相关性
    success_by_strength: Dict[str, float] = field(default_factory=dict)
    strength_correlation: float = 0.0  # 强度与成功率的相关性

    # 时间分析
    success_by_time_period: Dict[str, float] = field(default_factory=dict)
    performance_trend: str = "stable"  # improving, declining, stable

    # 市场条件分析
    success_by_market_condition: Dict[str, float] = field(default_factory=dict)
    best_market_conditions: List[str] = field(default_factory=list)
    worst_market_conditions: List[str] = field(default_factory=list)

    # 盈亏统计
    average_profit: float = 0.0
    average_loss: float = 0.0
    profit_factor: float = 0.0  # 盈亏比
    max_consecutive_losses: int = 0
    max_consecutive_wins: int = 0

    # 风险调整指标
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    recovery_factor: float = 0.0

    # 统计显著性
    p_value: float = 0.0
    is_statistically_significant: bool = False

    # 建议和洞察
    key_insights: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)

    # 元数据
    data_quality_score: float = 1.0
    sample_size_adequacy: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskAssessment:
    """风险评估结果"""
    assessment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    assessment_time: datetime = field(default_factory=datetime.now)
    symbol: str = ""

    # 整体风险评分
    overall_risk_score: float = 0.0  # 0-1之间
    risk_level: str = "medium"  # low, medium, high, extreme

    # 各类风险评分
    market_risk_score: float = 0.0
    liquidity_risk_score: float = 0.0
    volatility_risk_score: float = 0.0
    leverage_risk_score: float = 0.0
    short_squeeze_risk_score: float = 0.0
    regulatory_risk_score: float = 0.0
    systemic_risk_score: float = 0.0

    # 风险指标
    var_95: float = 0.0  # 95%置信度VaR
    var_99: float = 0.0  # 99%置信度VaR
    expected_shortfall: float = 0.0  # 期望损失
    beta: float = 0.0  # 贝塔系数
    correlation_with_market: float = 0.0

    # 特殊风险
    short_squeeze_probability: float = 0.0
    liquidation_risk: float = 0.0
    counterparty_risk: float = 0.0

    # 风险控制建议
    position_size_limit: float = 0.0  # 建议仓位限制
    stop_loss_distance: float = 0.0   # 建议止损距离
    hedge_ratio: float = 0.0        # 建议对冲比率
    leverage_limit: float = 0.0     # 建议杠杆限制

    # 风险预警
    risk_warnings: List[str] = field(default_factory=list)
    alert_triggers: List[str] = field(default_factory=list)

    # 压力测试结果
    stress_test_results: Dict[str, float] = field(default_factory=dict)
    scenario_analysis: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # 元数据
    confidence_score: float = 0.0
    data_freshness: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """绩效指标集合"""
    metrics_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    calculation_time: datetime = field(default_factory=datetime.now)
    symbol: str = ""
    period: str = ""  # 7d, 30d, 90d, 1y

    # 基础交易统计
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    breakeven_trades: int = 0

    # 胜率指标
    win_rate: float = 0.0
    win_rate_weighted: float = 0.0  # 按盈亏加权
    win_rate_volume: float = 0.0    # 按成交量加权

    # 盈亏统计
    total_profit: float = 0.0
    total_loss: float = 0.0
    net_profit: float = 0.0
    average_profit: float = 0.0
    average_loss: float = 0.0
    profit_factor: float = 0.0

    # 风险调整收益
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    information_ratio: float = 0.0

    # 回撤统计
    max_drawdown: float = 0.0
    max_drawdown_duration: float = 0.0  # 天数
    average_drawdown: float = 0.0
    recovery_time: float = 0.0  # 平均恢复时间（天）

    # 连续统计
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    average_consecutive_wins: float = 0.0
    average_consecutive_losses: float = 0.0

    # 时间统计
    average_holding_time: float = 0.0  # 小时
    median_holding_time: float = 0.0
    best_trade_duration: float = 0.0
    worst_trade_duration: float = 0.0

    # 按信号类型分类
    performance_by_signal_type: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # 按强度分类
    performance_by_strength: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # 统计指标
    profit_std_dev: float = 0.0
    loss_std_dev: float = 0.0
    profit_skewness: float = 0.0
    loss_skewness: float = 0.0
    kurtosis: float = 0.0

    # 效率指标
    trade_efficiency: float = 0.0  # 实际盈利/理论最大盈利
    capital_efficiency: float = 0.0  # 盈利/使用资本
    time_efficiency: float = 0.0    # 盈利/持仓时间

    # 元数据
    benchmark_performance: float = 0.0
    alpha: float = 0.0
    beta: float = 0.0
    r_squared: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationRecommendation:
    """优化建议"""
    recommendation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    recommendation_time: datetime = field(default_factory=datetime.now)
    symbol: str = ""

    # 优化目标
    optimization_target: str = ""  # win_rate, profit_factor, sharpe_ratio
    current_value: float = 0.0
    expected_improvement: float = 0.0
    confidence_level: float = 0.0

    # 优化策略
    strategy: str = ""
    implementation_steps: List[str] = field(default_factory=list)

    # 参数调整
    parameter_changes: Dict[str, Any] = field(default_factory=dict)

    # 预期影响
    expected_win_rate_change: float = 0.0
    expected_risk_change: float = 0.0
    expected_return_change: float = 0.0

    # 成本分析
    implementation_cost: float = 0.0
    expected_roi: float = 0.0
    payback_period: float = 0.0

    # 风险评估
    risk_factors: List[str] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)

    # 验证方法
    backtest_results: Dict[str, float] = field(default_factory=dict)
    validation_metrics: List[str] = field(default_factory=list)

    # 状态
    priority: str = "medium"  # low, medium, high, urgent
    status: str = "proposed"   # proposed, approved, implemented, validated

    # 元数据
    estimated_implementation_time: float = 0.0  # 小时
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# 类型别名
TradeHistory = List[TradeResult]
WinRateHistory = List[WinRateAnalysis]
RiskHistory = List[RiskAssessment]