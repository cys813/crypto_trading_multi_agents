"""
Analysis result models for the Long Analyst Agent.

Defines structures for storing and managing analysis results from
different dimensions (technical, fundamental, sentiment, LLM).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
import uuid


class AnalysisDimension(Enum):
    """Dimensions of analysis."""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    LLM = "llm"
    COMBINED = "combined"


class AnalysisStatus(Enum):
    """Status of analysis."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class ConfidenceLevel(Enum):
    """Confidence levels for analysis results."""
    VERY_LOW = 0.1
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9


@dataclass
class AnalysisMetric:
    """Individual analysis metric."""
    name: str
    value: float
    weight: float = 1.0
    confidence: float = 0.5
    description: str = ""
    interpretation: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TechnicalIndicators:
    """Technical analysis indicators."""
    # Trend indicators
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None

    # Momentum indicators
    rsi: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    stochastic_k: Optional[float] = None
    stochastic_d: Optional[float] = None

    # Volatility indicators
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None
    atr: Optional[float] = None
    standard_deviation: Optional[float] = None

    # Volume indicators
    volume_sma: Optional[float] = None
    on_balance_volume: Optional[float] = None
    money_flow_index: Optional[float] = None

    # Support/Resistance
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)

    # Pattern recognition
    patterns: List[str] = field(default_factory=list)
    candlestick_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trend": {
                "sma_20": self.sma_20,
                "sma_50": self.sma_50,
                "sma_200": self.sma_200,
                "ema_12": self.ema_12,
                "ema_26": self.ema_26
            },
            "momentum": {
                "rsi": self.rsi,
                "macd_line": self.macd_line,
                "macd_signal": self.macd_signal,
                "macd_histogram": self.macd_histogram,
                "stochastic_k": self.stochastic_k,
                "stochastic_d": self.stochastic_d
            },
            "volatility": {
                "bollinger_upper": self.bollinger_upper,
                "bollinger_middle": self.bollinger_middle,
                "bollinger_lower": self.bollinger_lower,
                "atr": self.atr,
                "standard_deviation": self.standard_deviation
            },
            "volume": {
                "volume_sma": self.volume_sma,
                "on_balance_volume": self.on_balance_volume,
                "money_flow_index": self.money_flow_index
            },
            "support_resistance": {
                "support_levels": self.support_levels,
                "resistance_levels": self.resistance_levels
            },
            "patterns": {
                "patterns": self.patterns,
                "candlestick_patterns": self.candlestick_patterns
            }
        }


@dataclass
class FundamentalMetrics:
    """Fundamental analysis metrics."""
    # Market metrics
    market_cap: Optional[float] = None
    circulating_supply: Optional[float] = None
    total_supply: Optional[float] = None
    max_supply: Optional[float] = None

    # On-chain metrics
    active_addresses: Optional[int] = None
    transaction_count: Optional[int] = None
    transaction_volume: Optional[float] = None
    hash_rate: Optional[float] = None
    staking_rewards: Optional[float] = None

    # Financial metrics
    revenue: Optional[float] = None
    expenses: Optional[float] = None
    profit_margin: Optional[float] = None
    price_to_earnings: Optional[float] = None

    # Development metrics
    github_commits: Optional[int] = None
    developer_activity: Optional[float] = None
    code_quality_score: Optional[float] = None

    # Network metrics
    network_value_to_transactions: Optional[float] = None
    market_cap_to_realized_value: Optional[float] = None
    stock_to_flow: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "market": {
                "market_cap": self.market_cap,
                "circulating_supply": self.circulating_supply,
                "total_supply": self.total_supply,
                "max_supply": self.max_supply
            },
            "on_chain": {
                "active_addresses": self.active_addresses,
                "transaction_count": self.transaction_count,
                "transaction_volume": self.transaction_volume,
                "hash_rate": self.hash_rate,
                "staking_rewards": self.staking_rewards
            },
            "financial": {
                "revenue": self.revenue,
                "expenses": self.expenses,
                "profit_margin": self.profit_margin,
                "price_to_earnings": self.price_to_earnings
            },
            "development": {
                "github_commits": self.github_commits,
                "developer_activity": self.developer_activity,
                "code_quality_score": self.code_quality_score
            },
            "network": {
                "network_value_to_transactions": self.network_value_to_transactions,
                "market_cap_to_realized_value": self.market_cap_to_realized_value,
                "stock_to_flow": self.stock_to_flow
            }
        }


@dataclass
class SentimentMetrics:
    """Sentiment analysis metrics."""
    # Social media sentiment
    twitter_sentiment: Optional[float] = None
    reddit_sentiment: Optional[float] = None
    telegram_sentiment: Optional[float] = None
    discord_sentiment: Optional[float] = None

    # News sentiment
    news_sentiment: Optional[float] = None
    news_volume: Optional[int] = None
    news_impact_score: Optional[float] = None

    # Market sentiment
    fear_greed_index: Optional[float] = None
    social_volume: Optional[int] = None
    mention_count: Optional[int] = None
    engagement_rate: Optional[float] = None

    # Whale activity
    whale_transactions: Optional[int] = None
    whale_accumulation: Optional[float] = None
    exchange_net_flow: Optional[float] = None

    # Overall sentiment
    overall_sentiment: Optional[float] = None
    sentiment_trend: Optional[str] = None  # "increasing", "decreasing", "stable"
    sentiment_volatility: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "social_media": {
                "twitter_sentiment": self.twitter_sentiment,
                "reddit_sentiment": self.reddit_sentiment,
                "telegram_sentiment": self.telegram_sentiment,
                "discord_sentiment": self.discord_sentiment
            },
            "news": {
                "news_sentiment": self.news_sentiment,
                "news_volume": self.news_volume,
                "news_impact_score": self.news_impact_score
            },
            "market": {
                "fear_greed_index": self.fear_greed_index,
                "social_volume": self.social_volume,
                "mention_count": self.mention_count,
                "engagement_rate": self.engagement_rate
            },
            "whale_activity": {
                "whale_transactions": self.whale_transactions,
                "whale_accumulation": self.whale_accumulation,
                "exchange_net_flow": self.exchange_net_flow
            },
            "overall": {
                "overall_sentiment": self.overall_sentiment,
                "sentiment_trend": self.sentiment_trend,
                "sentiment_volatility": self.sentiment_volatility
            }
        }


@dataclass
class LLMAnalysis:
    """LLM-powered analysis results."""
    # Market understanding
    market_context: str = ""
    trend_assessment: str = ""
    risk_factors: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)

    # Signal generation
    signal_reasoning: str = ""
    confidence_assessment: str = ""
    alternative_scenarios: List[str] = field(default_factory=list)

    # Technical interpretation
    technical_patterns: List[str] = field(default_factory=list)
    key_levels: List[float] = field(default_factory=list)
    expected_price_action: str = ""

    # Fundamental insights
    competitive_position: str = ""
    growth_potential: str = ""
    regulatory_outlook: str = ""

    # Sentiment interpretation
    sentiment_narrative: str = ""
    market_psychology: str = ""
    contrarian_signals: List[str] = field(default_factory=list)

    # Overall assessment
    investment_thesis: str = ""
    time_horizon: str = ""
    risk_management: str = ""

    # Scores
    technical_score: Optional[float] = None
    fundamental_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    overall_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "market_understanding": {
                "market_context": self.market_context,
                "trend_assessment": self.trend_assessment,
                "risk_factors": self.risk_factors,
                "opportunities": self.opportunities
            },
            "signal_generation": {
                "signal_reasoning": self.signal_reasoning,
                "confidence_assessment": self.confidence_assessment,
                "alternative_scenarios": self.alternative_scenarios
            },
            "technical_interpretation": {
                "technical_patterns": self.technical_patterns,
                "key_levels": self.key_levels,
                "expected_price_action": self.expected_price_action
            },
            "fundamental_insights": {
                "competitive_position": self.competitive_position,
                "growth_potential": self.growth_potential,
                "regulatory_outlook": self.regulatory_outlook
            },
            "sentiment_interpretation": {
                "sentiment_narrative": self.sentiment_narrative,
                "market_psychology": self.market_psychology,
                "contrarian_signals": self.contrarian_signals
            },
            "overall_assessment": {
                "investment_thesis": self.investment_thesis,
                "time_horizon": self.time_horizon,
                "risk_management": self.risk_management
            },
            "scores": {
                "technical_score": self.technical_score,
                "fundamental_score": self.fundamental_score,
                "sentiment_score": self.sentiment_score,
                "overall_score": self.overall_score
            }
        }


@dataclass
class AnalysisResult:
    """
    Comprehensive analysis result from the Long Analyst Agent.

    This combines results from all analysis dimensions and provides
    a unified view for signal generation.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str = ""
    dimension: AnalysisDimension = AnalysisDimension.TECHNICAL
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    status: AnalysisStatus = AnalysisStatus.COMPLETED
    confidence: float = 0.5
    score: float = 0.5

    # Analysis data
    technical_indicators: Optional[TechnicalIndicators] = None
    fundamental_metrics: Optional[FundamentalMetrics] = None
    sentiment_metrics: Optional[SentimentMetrics] = None
    llm_analysis: Optional[LLMAnalysis] = None

    # Metrics and indicators
    metrics: List[AnalysisMetric] = field(default_factory=list)
    signals: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Context information
    timeframe: str = "1h"
    data_source: str = "binance"
    analysis_duration: float = 0.0  # Analysis duration in seconds

    # Quality and reliability
    data_quality_score: float = 1.0
    reliability_score: float = 0.5
    completeness_score: float = 1.0

    # Error handling
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate analysis result."""
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")

        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")

        if not (0.0 <= self.score <= 1.0):
            raise ValueError("Score must be between 0.0 and 1.0")

    @property
    def is_successful(self) -> bool:
        """Check if analysis was successful."""
        return self.status == AnalysisStatus.COMPLETED

    @property
    def age_seconds(self) -> float:
        """Get analysis age in seconds."""
        return datetime.now().timestamp() - self.timestamp

    @property
    def has_technical_data(self) -> bool:
        """Check if technical data is available."""
        return self.technical_indicators is not None

    @property
    def has_fundamental_data(self) -> bool:
        """Check if fundamental data is available."""
        return self.fundamental_metrics is not None

    @property
    def has_sentiment_data(self) -> bool:
        """Check if sentiment data is available."""
        return self.sentiment_metrics is not None

    @property
    def has_llm_analysis(self) -> bool:
        """Check if LLM analysis is available."""
        return self.llm_analysis is not None

    def get_top_signals(self, limit: int = 5) -> List[str]:
        """Get top signals based on confidence."""
        # Sort signals by confidence if available
        if self.metrics:
            sorted_metrics = sorted(self.metrics, key=lambda x: x.confidence, reverse=True)
            return [metric.name for metric in sorted_metrics[:limit]]
        return self.signals[:limit]

    def get_key_metrics(self, limit: int = 10) -> List[AnalysisMetric]:
        """Get key metrics sorted by importance."""
        return sorted(self.metrics, key=lambda x: x.weight * x.confidence, reverse=True)[:limit]

    def add_metric(self, name: str, value: float, weight: float = 1.0,
                   confidence: float = 0.5, description: str = ""):
        """Add a new metric to the analysis result."""
        metric = AnalysisMetric(
            name=name,
            value=value,
            weight=weight,
            confidence=confidence,
            description=description
        )
        self.metrics.append(metric)

    def add_warning(self, warning: str):
        """Add a warning to the analysis result."""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": self.id,
            "symbol": self.symbol,
            "dimension": self.dimension.value,
            "timestamp": self.timestamp,
            "status": self.status.value,
            "confidence": self.confidence,
            "score": self.score,
            "timeframe": self.timeframe,
            "data_source": self.data_source,
            "analysis_duration": self.analysis_duration,
            "data_quality_score": self.data_quality_score,
            "reliability_score": self.reliability_score,
            "completeness_score": self.completeness_score,
            "error_message": self.error_message,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "signals": self.signals,
            "recommendations": self.recommendations
        }

        if self.technical_indicators:
            result["technical_indicators"] = self.technical_indicators.to_dict()

        if self.fundamental_metrics:
            result["fundamental_metrics"] = self.fundamental_metrics.to_dict()

        if self.sentiment_metrics:
            result["sentiment_metrics"] = self.sentiment_metrics.to_dict()

        if self.llm_analysis:
            result["llm_analysis"] = self.llm_analysis.to_dict()

        if self.metrics:
            result["metrics"] = [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "weight": metric.weight,
                    "confidence": metric.confidence,
                    "description": metric.description,
                    "interpretation": metric.interpretation,
                    "metadata": metric.metadata
                }
                for metric in self.metrics
            ]

        return result

    def merge_with(self, other: "AnalysisResult") -> "AnalysisResult":
        """
        Merge with another analysis result.

        Args:
            other: Another analysis result to merge with

        Returns:
            Merged analysis result
        """
        if self.symbol != other.symbol:
            raise ValueError("Cannot merge analysis results for different symbols")

        # Create merged result
        merged = AnalysisResult(
            symbol=self.symbol,
            dimension=AnalysisDimension.COMBINED,
            timestamp=max(self.timestamp, other.timestamp),
            status=AnalysisStatus.COMPLETED if self.is_successful and other.is_successful else AnalysisStatus.FAILED,
            confidence=(self.confidence + other.confidence) / 2,
            score=(self.score + other.score) / 2
        )

        # Merge technical indicators
        if self.technical_indicators or other.technical_indicators:
            merged.technical_indicators = self.technical_indicators or other.technical_indicators

        # Merge fundamental metrics
        if self.fundamental_metrics or other.fundamental_metrics:
            merged.fundamental_metrics = self.fundamental_metrics or other.fundamental_metrics

        # Merge sentiment metrics
        if self.sentiment_metrics or other.sentiment_metrics:
            merged.sentiment_metrics = self.sentiment_metrics or other.sentiment_metrics

        # Merge LLM analysis
        if self.llm_analysis or other.llm_analysis:
            merged.llm_analysis = self.llm_analysis or other.llm_analysis

        # Merge metrics
        merged.metrics = self.metrics + other.metrics

        # Merge signals and recommendations
        merged.signals = list(set(self.signals + other.signals))
        merged.recommendations = list(set(self.recommendations + other.recommendations))

        # Merge warnings
        merged.warnings = list(set(self.warnings + other.warnings))

        return merged

    def __str__(self) -> str:
        """String representation."""
        return f"AnalysisResult({self.symbol}, {self.dimension.value}, score={self.score:.2f})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"AnalysisResult(id={self.id[:8]}..., symbol={self.symbol}, "
                f"dimension={self.dimension.value}, score={self.score:.2f}, "
                f"confidence={self.confidence:.2f})")