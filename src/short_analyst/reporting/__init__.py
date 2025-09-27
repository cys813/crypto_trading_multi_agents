"""
做空分析报告生成模块

该模块提供了完整的报告生成功能，支持多种输出格式和报告类型。
"""

from .report_generator import (
    ReportGenerator,
    ReportMetadata,
    ReportContent,
    ShortAnalysisReport
)

__all__ = [
    'ReportGenerator',
    'ReportType',
    'ReportFormat',
    'ReportMetadata',
    'ReportContent',
    'ShortAnalysisReport',
    'ChartConfig'
]

# 模块版本
__version__ = '1.0.0'

# 模块描述
__description__ = '做空分析报告生成系统'

# 主要组件
from .report_generator import (
    ReportGenerator,
    ReportMetadata,
    ReportContent,
    ShortAnalysisReport
)

# 数据模型
from .report_models import (
    ReportType,
    ReportFormat,
    ChartConfig
)

# 工具函数
from .report_utils import (
    format_number,
    format_percentage,
    format_duration,
    format_timestamp,
    calculate_risk_level_color,
    calculate_signal_strength_color,
    generate_chart_colors
)

# 异常类
from .report_exceptions import (
    ReportGenerationError,
    ReportValidationError,
    ReportExportError,
    ChartGenerationError
)

# 默认配置
DEFAULT_REPORT_CONFIG = {
    'include_charts': True,
    'include_technical_analysis': True,
    'include_risk_assessment': True,
    'include_recommendations': True,
    'max_signals_per_report': 50,
    'chart_width': 800,
    'chart_height': 400,
    'chart_dpi': 100,
    'language': 'zh-CN'
}