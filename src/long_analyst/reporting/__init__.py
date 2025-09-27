"""
Report Generation Module for Long Analyst Agent

This module provides comprehensive report generation capabilities including:
- Standardized analysis report generation
- Strategy recommendations with risk/reward analysis
- Multi-format output (HTML, PDF, JSON)
- Real-time report generation and delivery
- Historical report tracking and comparison
"""

from .report_generator import ReportGenerator
from .template_engine import TemplateEngine
from .report_analyzer import ReportAnalyzer
from .report_visualizer import ReportVisualizer
from .strategy_advisor import StrategyAdvisor
from .risk_reward_analyzer import RiskRewardAnalyzer
from .models import (
    AnalysisReport,
    ReportConfig,
    TemplateConfig,
    ReportSummary,
    StrategyRecommendation,
    RiskRewardAnalysis
)

__all__ = [
    'ReportGenerator',
    'TemplateEngine',
    'ReportAnalyzer',
    'ReportVisualizer',
    'StrategyAdvisor',
    'RiskRewardAnalyzer',
    'AnalysisReport',
    'ReportConfig',
    'TemplateConfig',
    'ReportSummary',
    'StrategyRecommendation',
    'RiskRewardAnalysis'
]