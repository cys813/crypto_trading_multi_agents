"""
LLM分析模型定义

该模块定义了LLM分析与推理引擎中使用的各种数据结构和枚举。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
import uuid

from ..models.short_signal import ShortSignal, ShortSignalType, ShortSignalStrength


# 简化的信号类型定义（避免循环导入）
class FusionSignal:
    """融合信号类型"""
    def __init__(self, signal_id: str, signal_type: str, confidence: float, metadata: dict = None):
        self.signal_id = signal_id
        self.signal_type = signal_type
        self.confidence = confidence
        self.metadata = metadata or {}


class AnalysisType(Enum):
    """分析类型"""
    MARKET_SENTIMENT = "market_sentiment"           # 市场情绪分析
    TECHNICAL_EXPLANATION = "technical_explanation" # 技术指标解释
    RISK_ASSESSMENT = "risk_assessment"             # 风险评估
    TRADING_DECISION = "trading_decision"           # 交易决策
    MARKET_FORECAST = "market_forecast"             # 市场预测
    NEWS_IMPACT = "news_impact"                     # 新闻影响分析


class SentimentPolarity(Enum):
    """情绪极性"""
    EXTREMELY_BEARISH = -2     # 极度看跌
    BEARISH = -1               # 看跌
    NEUTRAL = 0                # 中性
    BULLISH = 1                # 看涨
    EXTREMELY_BULLISH = 2      # 极度看涨


class ConfidenceLevel(Enum):
    """置信度等级"""
    VERY_LOW = 1              # 极低 (0-20%)
    LOW = 2                   # 低 (20-40%)
    MEDIUM = 3                # 中等 (40-60%)
    HIGH = 4                  # 高 (60-80%)
    VERY_HIGH = 5             # 极高 (80-100%)


class RiskTolerance(Enum):
    """风险承受能力"""
    CONSERVATIVE = 1          # 保守型
    MODERATE = 2              # 稳健型
    AGGRESSIVE = 3            # 激进型


class TimeHorizon(Enum):
    """时间范围"""
    INTRADAY = "intraday"     # 日内
    SHORT_TERM = "short_term" # 短期 (1-7天)
    MEDIUM_TERM = "medium_term" # 中期 (1-4周)
    LONG_TERM = "long_term"   # 长期 (1-3个月)


@dataclass
class MarketSentiment:
    """市场情绪分析结果"""
    sentiment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    analysis_time: datetime = field(default_factory=datetime.now)
    symbol: str = ""

    # 整体情绪
    overall_sentiment: SentimentPolarity = SentimentPolarity.NEUTRAL
    sentiment_score: float = 0.0  # -2到2之间的分数
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    # 情绪组成部分
    fear_greed_index: Optional[float] = None
    social_sentiment: Optional[SentimentPolarity] = None
    news_sentiment: Optional[SentimentPolarity] = None
    technical_sentiment: Optional[SentimentPolarity] = None

    # 情绪变化趋势
    sentiment_trend: str = "stable"  # rising, falling, stable
    momentum: float = 0.0  # 情绪动量

    # 分析详情
    key_factors: List[str] = field(default_factory=list)
    contrarian_signals: List[str] = field(default_factory=list)
    extreme_conditions: List[str] = field(default_factory=list)

    # 元数据
    data_sources: List[str] = field(default_factory=list)
    analysis_depth: str = "standard"  # basic, standard, deep
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TechnicalExplanation:
    """技术指标解释"""
    explanation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    analysis_time: datetime = field(default_factory=datetime.now)
    symbol: str = ""

    # 指标分析
    indicator_name: str = ""
    indicator_value: float = 0.0
    interpretation: str = ""
    significance: str = ""  # high, medium, low

    # 技术背景
    market_context: str = ""
    trend_analysis: str = ""
    pattern_recognition: Optional[str] = None

    # 交易含义
    bearish_implications: List[str] = field(default_factory=list)
    bullish_implications: List[str] = field(default_factory=list)
    neutral_factors: List[str] = field(default_factory=list)

    # 预测和置信度
    short_term_outlook: str = ""
    medium_term_outlook: str = ""
    outlook_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    # 关键水平
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    key_price_levels: List[float] = field(default_factory=list)

    # 元数据
    chart_patterns: List[str] = field(default_factory=list)
    volume_analysis: str = ""
    timeframe: str = ""
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

    # 风险维度
    market_risk: float = 0.0      # 市场风险
    liquidity_risk: float = 0.0   # 流动性风险
    volatility_risk: float = 0.0  # 波动率风险
    leverage_risk: float = 0.0    # 杠杆风险
    counterparty_risk: float = 0.0 # 对手方风险
    systemic_risk: float = 0.0    # 系统性风险

    # 特殊风险
    short_squeeze_risk: float = 0.0    # 轧空风险
    regulatory_risk: float = 0.0       # 监管风险
    black_swan_risk: float = 0.0      # 黑天鹅风险

    # 风险指标
    max_drawdown: float = 0.0          # 最大回撤预期
    var_95: float = 0.0               # 95%置信度VaR
    expected_shortfall: float = 0.0    # 期望损失
    beta: float = 0.0                  # 贝塔系数

    # 风险控制建议
    position_size_limit: float = 0.0   # 建议仓位限制
    stop_loss_distance: float = 0.0    # 止损距离
    hedge_ratio: float = 0.0          # 对冲比率
    diversification_needs: List[str] = field(default_factory=list)

    # 监控指标
    key_risk_indicators: List[str] = field(default_factory=list)
    early_warning_signals: List[str] = field(default_factory=list)

    # 元数据
    assessment_horizon: str = "short_term"
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TradingDecision:
    """交易决策建议"""
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    decision_time: datetime = field(default_factory=datetime.now)
    symbol: str = ""

    # 核心决策
    action: str = ""  # hold, short, cover, reduce
    conviction_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    urgency: str = "normal"  # low, normal, high

    # 交易参数
    recommended_entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: List[float] = field(default_factory=list)
    position_size: float = 0.0  # 建议仓位比例
    leverage_ratio: float = 1.0

    # 时间框架
    entry_timeframe: str = ""  # 1m, 5m, 15m, 1h, 4h, 1d
    expected_duration: str = ""  # minutes, hours, days, weeks
    exit_strategy: str = ""

    # 决策依据
    primary_reasons: List[str] = field(default_factory=list)
    supporting_factors: List[str] = field(default_factory=list)
    conflicting_factors: List[str] = field(default_factory=list)

    # 风险调整
    risk_reward_ratio: float = 0.0
    win_probability: float = 0.0
    expected_return: float = 0.0  # 百分比
    max_loss_acceptable: float = 0.0  # 百分比

    # 备选方案
    alternative_actions: List[Dict[str, Any]] = field(default_factory=list)
    contingency_plans: List[str] = field(default_factory=list)

    # 元数据
    decision_model: str = "hybrid"  # technical, fundamental, sentiment, hybrid
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMAnalysisInput:
    """LLM分析输入数据"""
    input_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    symbol: str = ""

    # 市场数据
    current_price: float = 0.0
    price_change_24h: float = 0.0
    volume_24h: float = 0.0
    market_cap: Optional[float] = None

    # 技术信号
    fusion_signals: List[FusionSignal] = field(default_factory=list)
    raw_indicators: Dict[str, Any] = field(default_factory=dict)

    # 市场情绪
    news_headlines: List[str] = field(default_factory=list)
    social_media_sentiment: Optional[SentimentPolarity] = None
    fear_greed_index: Optional[float] = None

    # 宏观因素
    market_conditions: str = ""
    trend_context: str = ""
    volatility_context: str = ""

    # 分析参数
    analysis_types: List[AnalysisType] = field(default_factory=list)
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    time_horizon: TimeHorizon = TimeHorizon.SHORT_TERM

    # 上下文信息
    recent_events: List[str] = field(default_factory=list)
    analyst_notes: Optional[str] = None
    custom_prompts: List[str] = field(default_factory=list)

    # 元数据
    data_quality_score: float = 1.0
    completeness_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMAnalysisOutput:
    """LLM分析输出结果"""
    output_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    analysis_time: datetime = field(default_factory=datetime.now)
    input_id: str = ""
    symbol: str = ""

    # 分析结果
    market_sentiment: Optional[MarketSentiment] = None
    technical_explanations: List[TechnicalExplanation] = field(default_factory=list)
    risk_assessment: Optional[RiskAssessment] = None
    trading_decision: Optional[TradingDecision] = None

    # 综合评分
    overall_score: float = 0.0  # 0-1之间
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    # 关键洞察
    key_insights: List[str] = field(default_factory=list)
    contrarian_signals: List[str] = field(default_factory=list)
    warning_signals: List[str] = field(default_factory=list)

    # 预测和展望
    short_term_forecast: str = ""
    medium_term_forecast: str = ""
    confidence_intervals: Dict[str, Tuple[float, float]] = field(default_factory=dict)

    # 建议行动
    immediate_actions: List[str] = field(default_factory=list)
    monitoring_points: List[str] = field(default_factory=list)
    research_needs: List[str] = field(default_factory=list)

    # 分析质量
    reasoning_quality: float = 0.0  # 0-1之间
    data_completeness: float = 0.0
    logical_consistency: float = 0.0

    # 性能指标
    processing_time: float = 0.0  # 秒
    token_count: int = 0
    cost_estimate: float = 0.0

    # 元数据
    model_used: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    analysis_version: str = "1.0"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMAnalysisContext:
    """LLM分析上下文管理"""
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    symbol: str = ""

    # 分析历史
    analysis_history: List[LLMAnalysisOutput] = field(default_factory=list)
    decision_history: List[TradingDecision] = field(default_factory=list)
    performance_tracking: Dict[str, Any] = field(default_factory=dict)

    # 学习和适应
    learning_data: Dict[str, Any] = field(default_factory=dict)
    adaptation_parameters: Dict[str, Any] = field(default_factory=dict)
    accuracy_metrics: Dict[str, float] = field(default_factory=dict)

    # 上下文状态
    current_market_regime: str = ""
    recent_accuracy: float = 0.0
    confidence_trend: str = "stable"  # improving, declining, stable

    # 元数据
    last_updated: datetime = field(default_factory=datetime.now)
    context_size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# 类型别名
AnalysisInput = LLMAnalysisInput
AnalysisOutput = LLMAnalysisOutput
AnalysisContext = LLMAnalysisContext

# 补充枚举定义
class AnalysisQuality(Enum):
    """分析质量"""
    POOR = 1                         # 差 (0-40%)
    FAIR = 2                         # 一般 (40-60%)
    GOOD = 3                         # 良好 (60-80%)
    EXCELLENT = 4                    # 优秀 (80-100%)


class LLMProvider(Enum):
    """LLM提供商"""
    OPENAI = "openai"                 # OpenAI
    ANTHROPIC = "anthropic"           # Anthropic
    AZURE = "azure"                   # Azure OpenAI
    LOCAL = "local"                   # 本地模型
    MOCK = "mock"                     # 模拟模式