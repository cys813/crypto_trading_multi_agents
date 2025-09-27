"""
Data models for the reporting system
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class ReportFormat(str, Enum):
    """Report output formats"""
    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"


class ReportType(str, Enum):
    """Report types"""
    STANDARD = "standard"
    QUICK_DECISION = "quick_decision"
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    COMPREHENSIVE = "comprehensive"


class ConfidenceLevel(str, Enum):
    """Confidence levels for recommendations"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class MarketDataPoint:
    """Single market data point"""
    timestamp: datetime
    price: float
    volume: float
    high: float
    low: float
    open: float
    close: float


@dataclass
class TechnicalIndicator:
    """Technical indicator data"""
    name: str
    value: float
    signal: str
    confidence: float
    timestamp: datetime


@dataclass
class SignalStrength:
    """Signal strength assessment"""
    overall_score: float
    technical_score: float
    fundamental_score: float
    sentiment_score: float
    confidence: ConfidenceLevel


@dataclass
class EntryRecommendation:
    """Entry recommendation details"""
    price: float
    timing: str
    confidence: ConfidenceLevel
    reasoning: List[str]
    risk_level: str


@dataclass
class RiskManagement:
    """Risk management parameters"""
    stop_loss: float
    take_profit_levels: List[float]
    position_size: float
    risk_per_trade: float
    risk_reward_ratio: float


@dataclass
class StrategyRecommendation:
    """Complete strategy recommendation"""
    action: str  # "BUY", "HOLD", "SELL"
    symbol: str
    entry_recommendation: EntryRecommendation
    risk_management: RiskManagement
    reasoning: List[str]
    expected_win_rate: float
    time_horizon: str
    confidence: ConfidenceLevel


@dataclass
class RiskRewardAnalysis:
    """Risk-reward analysis results"""
    expected_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_probability: float
    risk_reward_ratio: float
    breakeven_points: List[float]
    sensitivity_analysis: Dict[str, float]


@dataclass
class TechnicalAnalysis:
    """Technical analysis summary"""
    trend: str
    key_indicators: List[TechnicalIndicator]
    support_levels: List[float]
    resistance_levels: List[float]
    momentum: str
    volatility: float


@dataclass
class FundamentalAnalysis:
    """Fundamental analysis summary"""
    market_cap: float
    volume_24h: float
    price_change_24h: float
    market_dominance: float
    key_metrics: Dict[str, float]


@dataclass
class SentimentAnalysis:
    """Sentiment analysis summary"""
    overall_sentiment: str
    news_sentiment: float
    social_sentiment: float
    market_sentiment: float
    confidence: float


@dataclass
class ReportSummary:
    """Report executive summary"""
    signal_strength: SignalStrength
    key_findings: List[str]
    main_recommendations: List[str]
    primary_risks: List[str]
    overall_assessment: str
    confidence_score: float


class ReportConfig(BaseModel):
    """Report generation configuration"""
    report_type: ReportType = ReportType.STANDARD
    output_format: ReportFormat = ReportFormat.HTML
    include_charts: bool = True
    include_technical_analysis: bool = True
    include_fundamental_analysis: bool = True
    include_sentiment_analysis: bool = True
    template_name: str = "standard"
    language: str = "zh-CN"
    timezone: str = "UTC"

    class Config:
        use_enum_values = True


class TemplateConfig(BaseModel):
    """Template configuration"""
    name: str
    description: str
    template_path: str
    variables: List[str] = Field(default_factory=list)
    output_formats: List[ReportFormat] = Field(default_factory=list)
    version: str = "1.0"

    class Config:
        use_enum_values = True


class AnalysisReport(BaseModel):
    """Complete analysis report"""
    report_id: str
    symbol: str
    report_type: ReportType
    generated_at: datetime
    market_data: List[MarketDataPoint] = Field(default_factory=list)
    technical_analysis: Optional[TechnicalAnalysis] = None
    fundamental_analysis: Optional[FundamentalAnalysis] = None
    sentiment_analysis: Optional[SentimentAnalysis] = None
    strategy_recommendation: Optional[StrategyRecommendation] = None
    risk_reward_analysis: Optional[RiskRewardAnalysis] = None
    summary: Optional[ReportSummary] = None
    charts: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


@dataclass
class AnalysisRequest:
    """Analysis request parameters"""
    symbol: str
    report_type: ReportType = ReportType.STANDARD
    timeframe: str = "1h"
    lookback_period: int = 100
    include_technical: bool = True
    include_fundamental: bool = True
    include_sentiment: bool = True
    custom_parameters: Dict[str, Any] = field(default_factory=dict)