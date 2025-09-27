"""
Signal detection algorithms for Long Analyst Agent.

This module contains specialized detectors for different types of
trading signals optimized for long opportunities.
"""

from .trend_detector import TrendDetector
from .breakout_detector import BreakoutDetector
from .pullback_detector import PullbackDetector
from .pattern_detector import PatternDetector

__all__ = [
    'TrendDetector',
    'BreakoutDetector',
    'PullbackDetector',
    'PatternDetector'
]