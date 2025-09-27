"""
做空分析结果模型定义

该模块定义了做空分析师代理的分析结果数据结构。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

from .short_signal import ShortSignal, ShortSignalType
from .market_data import MarketData


class ShortAnalysisDimension(Enum):
    """做空分析维度"""
    TECHNICAL = "technical"        # 技术分析
    SENTIMENT = "sentiment"        # 情绪分析
    FUNDAMENTAL = "fundamental"    # 基本面分析
    LIQUIDITY = "liquidity"        # 流动性分析
    RISK = "risk"                  # 风险分析
    MARKET_STRUCTURE = "market_structure"  # 市场结构分析


class AnalysisRecommendation(Enum):
    """分析建议"""
    STRONG_SHORT = "strong_short"      # 强烈做空
    MODERATE_SHORT = "moderate_short"    # 适度做空
    WEAK_SHORT = "weak_short"           # 弱做空
    HOLD = "hold"                       # 持有观望
    STRONG_LONG = "strong_long"        # 强烈做多 (用于反向信号)
    AVOID_SHORT = "avoid_short"         # 避免做空


class RiskLevel(Enum):
    """风险等级"""
    VERY_LOW = 1    # 极低风险
    LOW = 2         # 低风险
    MEDIUM = 3      # 中等风险
    HIGH = 4        # 高风险
    VERY_HIGH = 5   # 极高风险


@dataclass
class TechnicalAnalysisResult:
    """技术分析结果"""
    # 趋势分析
    trend_strength: float = field(default=0.0)  # 趋势强度 (-1到1)
    trend_direction: str = field(default="neutral")  # 趋势方向
    trend_reversal_signals: List[str] = field(default_factory=list)

    # 超买超卖分析
    rsi_value: float = field(default=50.0)
    rsi_signal: str = field(default="neutral")
    overbought_signals: List[str] = field(default_factory=list)

    # 形态分析
    chart_patterns: List[Dict[str, Any]] = field(default_factory=list)
    reversal_patterns: List[Dict[str, Any]] = field(default_factory=list)

    # 支撑阻力
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    key_price_levels: List[float] = field(default_factory=list)

    # 成交量分析
    volume_analysis: Dict[str, Any] = field(default_factory=dict)
    volume_signals: List[str] = field(default_factory=list)

    # 动量指标
    momentum_indicators: Dict[str, float] = field(default_factory=dict)
    momentum_signals: List[str] = field(default_factory=list)

    # 波动率分析
    volatility_analysis: Dict[str, Any] = field(default_factory=dict)
    volatility_signals: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "trend_strength": self.trend_strength,
            "trend_direction": self.trend_direction,
            "trend_reversal_signals": self.trend_reversal_signals,
            "rsi_value": self.rsi_value,
            "rsi_signal": self.rsi_signal,
            "overbought_signals": self.overbought_signals,
            "chart_patterns": self.chart_patterns,
            "reversal_patterns": self.reversal_patterns,
            "support_levels": self.support_levels,
            "resistance_levels": self.resistance_levels,
            "key_price_levels": self.key_price_levels,
            "volume_analysis": self.volume_analysis,
            "volume_signals": self.volume_signals,
            "momentum_indicators": self.momentum_indicators,
            "momentum_signals": self.momentum_signals,
            "volatility_analysis": self.volatility_analysis,
            "volatility_signals": self.volatility_signals
        }


@dataclass
class SentimentAnalysisResult:
    """情绪分析结果"""
    # 整体情绪
    overall_sentiment: float = field(default=0.0)  # 整体情绪 (-1到1)
    sentiment_trend: float = field(default=0.0)    # 情绪趋势 (-1到1)
    sentiment_intensity: float = field(default=0.0)  # 情绪强度 (0-1)

    # 恐惧贪婪指标
    fear_greed_index: float = field(default=50.0)
    fear_greed_signal: str = field(default="neutral")

    # 社交媒体情绪
    social_sentiment_score: float = field(default=0.0)
    social_sentiment_trend: float = field(default=0.0)
    social_volume: int = field(default=0)
    social_engagement: float = field(default=0.0)

    # 新闻情绪
    news_sentiment_score: float = field(default=0.0)
    news_sentiment_trend: float = field(default=0.0)
    news_volume: int = field(default=0)
    news_impact_score: float = field(default=0.0)

    # 情绪信号
    bearish_signals: List[str] = field(default_factory=list)
    bullish_signals: List[str] = field(default_factory=list)
    extreme_sentiment_signals: List[str] = field(default_factory=list)

    # 情绪异常
    sentiment_anomalies: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "overall_sentiment": self.overall_sentiment,
            "sentiment_trend": self.sentiment_trend,
            "sentiment_intensity": self.sentiment_intensity,
            "fear_greed_index": self.fear_greed_index,
            "fear_greed_signal": self.fear_greed_signal,
            "social_sentiment_score": self.social_sentiment_score,
            "social_sentiment_trend": self.social_sentiment_trend,
            "social_volume": self.social_volume,
            "social_engagement": self.social_engagement,
            "news_sentiment_score": self.news_sentiment_score,
            "news_sentiment_trend": self.news_sentiment_trend,
            "news_volume": self.news_volume,
            "news_impact_score": self.news_impact_score,
            "bearish_signals": self.bearish_signals,
            "bullish_signals": self.bullish_signals,
            "extreme_sentiment_signals": self.extreme_sentiment_signals,
            "sentiment_anomalies": self.sentiment_anomalies
        }


@dataclass
class RiskAssessment:
    """风险评估"""
    # 整体风险
    overall_risk_level: RiskLevel = field(default=RiskLevel.MEDIUM)
    risk_score: float = field(default=0.5)  # 风险评分 (0-1)

    # 做空特有风险
    unlimited_upside_risk: float = field(default=0.0)  # 无限上涨风险 (0-1)
    short_squeeze_risk: float = field(default=0.0)      # 轧空风险 (0-1)
    liquidity_risk: float = field(default=0.0)          # 流动性风险 (0-1)
    borrowing_cost_risk: float = field(default=0.0)      # 借贷成本风险 (0-1)

    # 市场风险
    market_volatility_risk: float = field(default=0.0)   # 市场波动风险 (0-1)
    correlation_risk: float = field(default=0.0)         # 相关性风险 (0-1)
    tail_risk: float = field(default=0.0)                # 尾部风险 (0-1)

    # 操作风险
    execution_risk: float = field(default=0.0)           # 执行风险 (0-1)
    timing_risk: float = field(default=0.0)              # 时机风险 (0-1)
    position_size_risk: float = field(default=0.0)      # 仓位风险 (0-1)

    # 风险因素
    risk_factors: List[Dict[str, Any]] = field(default_factory=list)
    risk_mitigations: List[str] = field(default_factory=list)

    # 建议参数
    suggested_position_size: float = field(default=0.0)  # 建议仓位大小比例
    suggested_stop_loss: float = field(default=0.0)     # 建议止损比例
    suggested_hedging_ratio: float = field(default=0.0)  # 建议对冲比例

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "overall_risk_level": self.overall_risk_level.value,
            "risk_score": self.risk_score,
            "unlimited_upside_risk": self.unlimited_upside_risk,
            "short_squeeze_risk": self.short_squeeze_risk,
            "liquidity_risk": self.liquidity_risk,
            "borrowing_cost_risk": self.borrowing_cost_risk,
            "market_volatility_risk": self.market_volatility_risk,
            "correlation_risk": self.correlation_risk,
            "tail_risk": self.tail_risk,
            "execution_risk": self.execution_risk,
            "timing_risk": self.timing_risk,
            "position_size_risk": self.position_size_risk,
            "risk_factors": self.risk_factors,
            "risk_mitigations": self.risk_mitigations,
            "suggested_position_size": self.suggested_position_size,
            "suggested_stop_loss": self.suggested_stop_loss,
            "suggested_hedging_ratio": self.suggested_hedging_ratio
        }


@dataclass
class WinRateAnalysis:
    """胜率分析"""
    # 基础胜率
    historical_win_rate: float = field(default=0.0)      # 历史胜率 (0-1)
    current_market_win_rate: float = field(default=0.0)   # 当前市场胜率 (0-1)
    adjusted_win_rate: float = field(default=0.0)         # 调整后胜率 (0-1)

    # 统计数据
    sample_size: int = field(default=0)                   # 样本数量
    confidence_interval: tuple = field(default=(0.0, 1.0))  # 置信区间
    statistical_significance: float = field(default=0.0)   # 统计显著性 (0-1)

    # 胜率因素
    win_rate_factors: Dict[str, float] = field(default_factory=dict)
    win_rate_trend: float = field(default=0.0)            # 胜率趋势 (-1到1)

    # 不同市场条件的胜率
    bull_market_win_rate: float = field(default=0.0)       # 牛市胜率
    bear_market_win_rate: float = field(default=0.0)       # 熊市胜率
    sideways_market_win_rate: float = field(default=0.0)   # 震荡市胜率
    high_volatility_win_rate: float = field(default=0.0)   # 高波动胜率

    # 预期收益
    expected_profit: float = field(default=0.0)           # 预期收益
    expected_loss: float = field(default=0.0)             # 预期亏损
    profit_loss_ratio: float = field(default=1.0)         # 盈亏比
    expected_return: float = field(default=0.0)           # 预期回报率

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "historical_win_rate": self.historical_win_rate,
            "current_market_win_rate": self.current_market_win_rate,
            "adjusted_win_rate": self.adjusted_win_rate,
            "sample_size": self.sample_size,
            "confidence_interval": self.confidence_interval,
            "statistical_significance": self.statistical_significance,
            "win_rate_factors": self.win_rate_factors,
            "win_rate_trend": self.win_rate_trend,
            "bull_market_win_rate": self.bull_market_win_rate,
            "bear_market_win_rate": self.bear_market_win_rate,
            "sideways_market_win_rate": self.sideways_market_win_rate,
            "high_volatility_win_rate": self.high_volatility_win_rate,
            "expected_profit": self.expected_profit,
            "expected_loss": self.expected_loss,
            "profit_loss_ratio": self.profit_loss_ratio,
            "expected_return": self.expected_return
        }


@dataclass
class LLMAnalysis:
    """LLM分析结果"""
    # 基础信息
    llm_model: str = field(default="")
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    prompt_tokens: int = field(default=0)
    completion_tokens: int = field(default=0)
    total_tokens: int = field(default=0)

    # 分析内容
    market_summary: str = field(default="")              # 市场总结
    short_thesis: str = field(default="")                # 做空论点
    risk_assessment: str = field(default="")             # 风险评估
    timing_assessment: str = field(default="")           # 时机评估
    entry_strategy: str = field(default="")              # 入场策略
    exit_strategy: str = field(default="")               # 出场策略

    # 关键发现
    key_findings: List[str] = field(default_factory=list)
    market_conditions: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)

    # 评分
    confidence_score: float = field(default=0.0)        # 置信度评分 (0-1)
    analysis_quality_score: float = field(default=0.0)   # 分析质量评分 (0-1)
    reasoning_clarity_score: float = field(default=0.0)  # 推理清晰度评分 (0-1)

    # 建议
    recommendation: AnalysisRecommendation = field(default=AnalysisRecommendation.HOLD)
    time_horizon: str = field(default="short_term")      # 时间周期
    position_sizing: str = field(default="small")        # 仓位大小建议

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "llm_model": self.llm_model,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "market_summary": self.market_summary,
            "short_thesis": self.short_thesis,
            "risk_assessment": self.risk_assessment,
            "timing_assessment": self.timing_assessment,
            "entry_strategy": self.entry_strategy,
            "exit_strategy": self.exit_strategy,
            "key_findings": self.key_findings,
            "market_conditions": self.market_conditions,
            "risk_factors": self.risk_factors,
            "opportunities": self.opportunities,
            "confidence_score": self.confidence_score,
            "analysis_quality_score": self.analysis_quality_score,
            "reasoning_clarity_score": self.reasoning_clarity_score,
            "recommendation": self.recommendation.value,
            "time_horizon": self.time_horizon,
            "position_sizing": self.position_sizing
        }


@dataclass
class ShortAnalysisResult:
    """做空分析结果"""
    # 基础信息
    symbol: str
    timestamp: datetime
    analysis_id: str = field(default="")

    # 分析结果
    signals: List[ShortSignal] = field(default_factory=list)
    technical_analysis: TechnicalAnalysisResult = field(default_factory=TechnicalAnalysisResult)
    sentiment_analysis: SentimentAnalysisResult = field(default_factory=SentimentAnalysisResult)
    risk_assessment: Optional[RiskAssessment] = field(default=None)
    win_rate_analysis: Optional[WinRateAnalysis] = field(default=None)
    llm_analysis: Optional[LLMAnalysis] = field(default=None)

    # 综合评分
    overall_score: float = field(default=0.0)           # 综合评分 (0-10)
    signal_strength_score: float = field(default=0.0)    # 信号强度评分 (0-10)
    risk_adjusted_score: float = field(default=0.0)      # 风险调整后评分 (0-10)

    # 建议信息
    recommendation: AnalysisRecommendation = field(default=AnalysisRecommendation.HOLD)
    confidence_level: float = field(default=0.0)        # 置信度 (0-1)
    urgency_level: str = field(default="low")           # 紧急程度

    # 执行建议
    suggested_entry_price: Optional[float] = field(default=None)
    suggested_stop_loss: Optional[float] = field(default=None)
    suggested_take_profit: Optional[float] = field(default=None)
    suggested_position_size: float = field(default=0.0)   # 建议仓位大小比例

    # 市场条件
    market_regime: str = field(default="unknown")       # 市场状态
    volatility_regime: str = field(default="normal")     # 波动率状态
    liquidity_regime: str = field(default="normal")      # 流动性状态

    # 时间信息
    expected_holding_period: str = field(default="1-7 days")  # 预期持有期
    optimal_entry_timing: str = field(default="now")         # 最佳入场时机
    analysis_valid_until: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))

    # 性能指标
    processing_time_ms: float = field(default=0.0)      # 处理时间(毫秒)
    data_quality_score: float = field(default=1.0)      # 数据质量评分 (0-1)

    # 错误信息
    error_message: Optional[str] = field(default=None)
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self):
        """初始化后处理"""
        if not self.analysis_id:
            import uuid
            self.analysis_id = str(uuid.uuid4())

        # 计算综合评分
        self._calculate_scores()

    def _calculate_scores(self):
        """计算各项评分"""
        if self.signals:
            # 信号强度评分
            signal_scores = [signal.overall_score * 10 for signal in self.signals]
            self.signal_strength_score = sum(signal_scores) / len(signal_scores)
        else:
            self.signal_strength_score = 0.0

        # 风险调整评分
        if self.risk_assessment:
            risk_penalty = self.risk_assessment.risk_score * 2  # 风险惩罚
            self.risk_adjusted_score = max(0, self.signal_strength_score - risk_penalty)
        else:
            self.risk_adjusted_score = self.signal_strength_score

        # 综合评分
        self.overall_score = self.risk_adjusted_score

    @property
    def is_recommended(self) -> bool:
        """是否推荐做空"""
        return self.recommendation in [
            AnalysisRecommendation.STRONG_SHORT,
            AnalysisRecommendation.MODERATE_SHORT
        ]

    @property
    def is_high_confidence(self) -> bool:
        """是否高置信度"""
        return self.confidence_level >= 0.7

    @property
    def time_sensitivity(self) -> str:
        """时间敏感性"""
        if self.urgency_level == "high":
            return "immediate"
        elif self.urgency_level == "medium":
            return "soon"
        else:
            return "normal"

    @property
    def risk_category(self) -> str:
        """风险类别"""
        if self.risk_assessment:
            if self.risk_assessment.overall_risk_level in [RiskLevel.VERY_LOW, RiskLevel.LOW]:
                return "low_risk"
            elif self.risk_assessment.overall_risk_level == RiskLevel.MEDIUM:
                return "medium_risk"
            else:
                return "high_risk"
        return "unknown"

    def get_key_signals(self) -> List[ShortSignal]:
        """获取关键信号"""
        return [signal for signal in self.signals if signal.strength.value >= 7]

    def get_low_risk_signals(self) -> List[ShortSignal]:
        """获取低风险信号"""
        return [signal for signal in self.signals if signal.risk_level <= 2]

    def validate_result(self) -> List[str]:
        """验证分析结果"""
        errors = []

        if not self.symbol:
            errors.append("交易对符号不能为空")

        if self.overall_score < 1.0 and self.recommendation != AnalysisRecommendation.HOLD:
            errors.append("评分过低但仍推荐做空")

        if self.confidence_level < 0.3:
            errors.append("置信度过低")

        if self.data_quality_score < 0.5:
            errors.append("数据质量过低")

        if self.error_message:
            errors.append(f"分析错误: {self.error_message}")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "analysis_id": self.analysis_id,
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "signals": [signal.to_dict() for signal in self.signals],
            "technical_analysis": self.technical_analysis.to_dict(),
            "sentiment_analysis": self.sentiment_analysis.to_dict(),
            "risk_assessment": self.risk_assessment.to_dict() if self.risk_assessment else None,
            "win_rate_analysis": self.win_rate_analysis.to_dict() if self.win_rate_analysis else None,
            "llm_analysis": self.llm_analysis.to_dict() if self.llm_analysis else None,
            "overall_score": self.overall_score,
            "signal_strength_score": self.signal_strength_score,
            "risk_adjusted_score": self.risk_adjusted_score,
            "recommendation": self.recommendation.value,
            "confidence_level": self.confidence_level,
            "urgency_level": self.urgency_level,
            "suggested_entry_price": self.suggested_entry_price,
            "suggested_stop_loss": self.suggested_stop_loss,
            "suggested_take_profit": self.suggested_take_profit,
            "suggested_position_size": self.suggested_position_size,
            "market_regime": self.market_regime,
            "volatility_regime": self.volatility_regime,
            "liquidity_regime": self.liquidity_regime,
            "expected_holding_period": self.expected_holding_period,
            "optimal_entry_timing": self.optimal_entry_timing,
            "analysis_valid_until": self.analysis_valid_until.isoformat(),
            "processing_time_ms": self.processing_time_ms,
            "data_quality_score": self.data_quality_score,
            "error_message": self.error_message,
            "warnings": self.warnings,
            "is_recommended": self.is_recommended,
            "is_high_confidence": self.is_high_confidence,
            "time_sensitivity": self.time_sensitivity,
            "risk_category": self.risk_category
        }

    def get_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        return {
            "symbol": self.symbol,
            "recommendation": self.recommendation.value,
            "overall_score": self.overall_score,
            "confidence_level": self.confidence_level,
            "signal_count": len(self.signals),
            "key_signals": len(self.get_key_signals()),
            "risk_level": self.risk_assessment.overall_risk_level.value if self.risk_assessment else None,
            "expected_holding_period": self.expected_holding_period,
            "urgency": self.urgency_level
        }