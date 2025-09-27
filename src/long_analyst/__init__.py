"""
Long Analyst Agent - Multi-dimensional analysis for cryptocurrency long signals.

This package provides comprehensive analysis capabilities including:
- Technical indicators optimized for long positions
- Fundamental analysis integration
- Sentiment analysis from multiple sources
- LLM-powered signal evaluation
- Real-time event processing
- Performance optimization and scalability
"""

__version__ = "1.0.0"
__author__ = "Crypto Trading Multi Agents Team"

from .core.long_analyst import LongAnalystAgent
from .core.architecture import MultiDimensionalAnalysisEngine
from .models.signal import Signal, SignalStrength, SignalType

__all__ = [
    "LongAnalystAgent",
    "MultiDimensionalAnalysisEngine",
    "Signal",
    "SignalStrength",
    "SignalType"
]