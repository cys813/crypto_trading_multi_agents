"""
做空分析师代理数据模型

该模块定义了做空分析师代理中使用的各种数据结构和模型。
"""

from .short_signal import (
    ShortSignal,
    ShortSignalType,
    ShortSignalStrength,
    SignalReliability,
    ShortSignalPortfolio
)

from .market_data import (
    MarketData,
    OHLCV,
    Ticker,
    OrderBook,
    OrderBookLevel,
    Trade,
    LiquidityData,
    FundingRate,
    OpenInterest,
    MarketDataType,
    TimeFrame,
    create_market_data_dataframe
)

from .short_analysis_result import (
    ShortAnalysisResult,
    TechnicalAnalysisResult,
    SentimentAnalysisResult,
    RiskAssessment,
    WinRateAnalysis,
    LLMAnalysis,
    ShortAnalysisDimension,
    AnalysisRecommendation,
    RiskLevel
)

__all__ = [
    # Signal models
    "ShortSignal",
    "ShortSignalType",
    "ShortSignalStrength",
    "SignalReliability",
    "ShortSignalPortfolio",

    # Market data models
    "MarketData",
    "OHLCV",
    "Ticker",
    "OrderBook",
    "OrderBookLevel",
    "Trade",
    "LiquidityData",
    "FundingRate",
    "OpenInterest",
    "MarketDataType",
    "TimeFrame",
    "create_market_data_dataframe",

    # Analysis result models
    "ShortAnalysisResult",
    "TechnicalAnalysisResult",
    "SentimentAnalysisResult",
    "RiskAssessment",
    "WinRateAnalysis",
    "LLMAnalysis",
    "ShortAnalysisDimension",
    "AnalysisRecommendation",
    "RiskLevel"
]