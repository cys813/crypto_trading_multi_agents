"""
报告生成模块的数据模型定义

该模块定义了报告生成过程中使用的各种数据结构和枚举类型。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid


class ReportType(Enum):
    """报告类型枚举"""
    SIGNAL_ANALYSIS = "signal_analysis"           # 信号分析报告
    WIN_RATE_ANALYSIS = "win_rate_analysis"       # 胜率分析报告
    PERFORMANCE_REPORT = "performance_report"     # 表现报告
    COMPREHENSIVE_REPORT = "comprehensive_report" # 综合分析报告
    RISK_ASSESSMENT = "risk_assessment"           # 风险评估报告
    DAILY_SUMMARY = "daily_summary"               # 日常总结报告
    WEEKLY_SUMMARY = "weekly_summary"             # 周总结报告


class ReportFormat(Enum):
    """报告输出格式枚举"""
    JSON = "json"                     # JSON格式
    MARKDOWN = "markdown"             # Markdown格式
    HTML = "html"                     # HTML格式
    PDF = "pdf"                       # PDF格式
    CSV = "csv"                       # CSV格式
    EXCEL = "excel"                   # Excel格式


class ChartType(Enum):
    """图表类型枚举"""
    LINE = "line"                     # 线图
    BAR = "bar"                       # 柱状图
    SCATTER = "scatter"               # 散点图
    PIE = "pie"                       # 饼图
    HEATMAP = "heatmap"               # 热力图
    CANDLESTICK = "candlestick"       # K线图
    VOLUME = "volume"                 # 成交量图


class ReportLanguage(Enum):
    """报告语言枚举"""
    ZH_CN = "zh-CN"                   # 简体中文
    EN_US = "en-US"                   # 英文
    ZH_TW = "zh-TW"                   # 繁体中文


@dataclass
class ChartConfig:
    """图表配置"""
    chart_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    chart_type: ChartType = ChartType.LINE
    title: str = ""
    data_source: List[Any] = field(default_factory=list)
    width: int = 800
    height: int = 400
    dpi: int = 100
    theme: str = "default"  # default, dark, light
    colors: List[str] = field(default_factory=list)

    # 坐标轴配置
    x_axis_label: str = ""
    y_axis_label: str = ""
    x_axis_format: str = ""
    y_axis_format: str = ""

    # 图例配置
    show_legend: bool = True
    legend_position: str = "top"  # top, bottom, left, right

    # 网格线配置
    show_grid: bool = True
    grid_color: str = "#e0e0e0"

    # 附加配置
    annotations: List[Dict[str, Any]] = field(default_factory=list)
    tooltips: bool = True

    def __post_init__(self):
        """初始化后处理"""
        if not self.colors:
            self.colors = generate_default_colors(self.chart_type)

        # 验证图表尺寸
        if self.width < 100 or self.width > 2000:
            raise ValueError("图表宽度必须在100-2000像素之间")

        if self.height < 100 or self.height > 1500:
            raise ValueError("图表高度必须在100-1500像素之间")


@dataclass
class ReportSection:
    """报告章节"""
    section_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: str = ""
    section_type: str = "text"  # text, table, chart, list
    order: int = 0

    # 数据和配置
    data: Any = None
    config: Optional[Dict[str, Any]] = None

    # 元数据
    word_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """初始化后处理"""
        self.word_count = len(self.content.split()) if self.content else 0


@dataclass
class TableConfig:
    """表格配置"""
    table_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    headers: List[str] = field(default_factory=list)
    rows: List[List[Any]] = field(default_factory=list)
    column_formats: Optional[Dict[str, str]] = None  # 列格式化配置
    style: str = "default"  # default, compact, striped

    # 样式配置
    header_bg_color: str = "#f5f5f5"
    header_text_color: str = "#333333"
    row_colors: List[str] = field(default_factory=lambda: ["#ffffff", "#fafafa"])

    # 分页配置
    page_size: int = 50
    show_pagination: bool = True

    def __post_init__(self):
        """初始化后处理"""
        if self.column_formats is None:
            self.column_formats = {}

        # 验证表格数据
        if self.rows and self.headers:
            for row in self.rows:
                if len(row) != len(self.headers):
                    raise ValueError("表格行必须与表头列数一致")


@dataclass
class ReportTemplate:
    """报告模板"""
    template_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    template_type: ReportType = ReportType.COMPREHENSIVE_REPORT

    # 模板内容
    sections: List[ReportSection] = field(default_factory=list)
    charts: List[ChartConfig] = field(default_factory=list)
    tables: List[TableConfig] = field(default_factory=list)

    # 样式配置
    font_family: str = "Arial, sans-serif"
    font_size: int = 12
    line_height: float = 1.5
    color_scheme: str = "default"  # default, dark, light

    # 页面配置
    page_size: str = "A4"
    page_orientation: str = "portrait"  # portrait, landscape
    margins: Dict[str, int] = field(default_factory=lambda: {
        "top": 20, "right": 20, "bottom": 20, "left": 20
    })

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"

    def validate_template(self) -> List[str]:
        """验证模板的有效性"""
        errors = []

        if not self.name:
            errors.append("模板名称不能为空")

        if not self.sections:
            errors.append("模板必须包含至少一个章节")

        # 验证章节顺序
        section_orders = [section.order for section in self.sections]
        if len(set(section_orders)) != len(section_orders):
            errors.append("章节顺序不能重复")

        return errors


@dataclass
class ReportExportConfig:
    """报告导出配置"""
    export_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    format: ReportFormat = ReportFormat.MARKDOWN

    # 文件配置
    filename: str = ""
    directory: str = ""
    include_timestamp: bool = True

    # 内容配置
    include_charts: bool = True
    include_tables: bool = True
    include_appendices: bool = False
    include_metadata: bool = False

    # 样式配置
    apply_custom_styles: bool = True
    use_template_styles: bool = True

    # 导出选项
    compress_output: bool = False
    encrypt_output: bool = False
    password: Optional[str] = None

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """初始化后处理"""
        if not self.filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.filename = f"short_analysis_report_{timestamp}"


@dataclass
class ReportFilter:
    """报告过滤器"""
    filter_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # 时间过滤器
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # 信号过滤器
    signal_types: List[str] = field(default_factory=list)
    min_signal_strength: Optional[int] = None
    max_signal_strength: Optional[int] = None

    # 胜率过滤器
    min_win_rate: Optional[float] = None
    max_win_rate: Optional[float] = None
    min_sample_size: Optional[int] = None

    # 风险过滤器
    max_risk_level: Optional[int] = None
    risk_levels: List[int] = field(default_factory=list)

    # 交易对过滤器
    symbols: List[str] = field(default_factory=list)
    exclude_symbols: List[str] = field(default_factory=list)

    # 其他过滤器
    min_confidence: Optional[float] = None
    max_confidence: Optional[float] = None

    def apply_filter(self, data: List[Any]) -> List[Any]:
        """应用过滤器到数据"""
        filtered_data = []

        for item in data:
            if self._passes_filter(item):
                filtered_data.append(item)

        return filtered_data

    def _passes_filter(self, item: Any) -> bool:
        """检查单个项目是否通过过滤器"""
        # 这里需要根据具体的数据结构实现过滤逻辑
        # 这是一个示例实现
        return True


# 辅助函数
def generate_default_colors(chart_type: ChartType) -> List[str]:
    """生成默认颜色方案"""
    color_schemes = {
        ChartType.LINE: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
        ChartType.BAR: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
        ChartType.SCATTER: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
        ChartType.PIE: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
        ChartType.HEATMAP: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8'],
        ChartType.CANDLESTICK: ['#ff7f0e', '#1f77b4'],  # 红涨绿跌
        ChartType.VOLUME: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    }

    return color_schemes.get(chart_type, ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])


def create_default_template(report_type: ReportType) -> ReportTemplate:
    """创建默认报告模板"""
    template = ReportTemplate(
        name=f"{report_type.value}_default",
        description=f"默认{report_type.value}报告模板",
        template_type=report_type
    )

    # 根据报告类型添加默认章节
    if report_type == ReportType.SIGNAL_ANALYSIS:
        template.sections = [
            ReportSection(title="执行摘要", section_type="text", order=1),
            ReportSection(title="信号分析", section_type="text", order=2),
            ReportSection(title="技术指标", section_type="table", order=3),
            ReportSection(title="风险评估", section_type="text", order=4),
            ReportSection(title="交易建议", section_type="text", order=5)
        ]
    elif report_type == ReportType.WIN_RATE_ANALYSIS:
        template.sections = [
            ReportSection(title="胜率概览", section_type="text", order=1),
            ReportSection(title="胜率分析", section_type="table", order=2),
            ReportSection(title="性能指标", section_type="table", order=3),
            ReportSection(title="优化建议", section_type="text", order=4)
        ]

    return template