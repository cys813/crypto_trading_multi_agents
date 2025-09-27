"""
报告生成工具函数

该模块提供了报告生成过程中使用的各种工具函数和格式化工具。
"""

import math
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum

from .report_models import ChartType


def format_number(value: Union[float, int], decimals: int = 2) -> str:
    """格式化数字"""
    if isinstance(value, int):
        return f"{value:,}"

    return f"{value:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """格式化百分比"""
    return f"{value:.{decimals}%}"


def format_duration(seconds: Union[int, float]) -> str:
    """格式化持续时间"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}小时"
    else:
        days = seconds / 86400
        return f"{days:.1f}天"


def format_timestamp(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化时间戳"""
    return timestamp.strftime(format_str)


def calculate_risk_level_color(risk_level: int) -> str:
    """计算风险等级对应的颜色"""
    color_map = {
        1: "#4CAF50",  # 绿色 - 低风险
        2: "#8BC34A",  # 浅绿色 - 较低风险
        3: "#FFC107",  # 黄色 - 中等风险
        4: "#FF9800",  # 橙色 - 较高风险
        5: "#F44336"   # 红色 - 高风险
    }
    return color_map.get(risk_level, "#757575")


def calculate_signal_strength_color(strength: int) -> str:
    """计算信号强度对应的颜色"""
    if strength >= 8:
        return "#4CAF50"  # 绿色 - 强信号
    elif strength >= 6:
        return "#8BC34A"  # 浅绿色 - 较强信号
    elif strength >= 4:
        return "#FFC107"  # 黄色 - 中等信号
    elif strength >= 2:
        return "#FF9800"  # 橙色 - 较弱信号
    else:
        return "#F44336"  # 红色 - 弱信号


def generate_chart_colors(chart_type: ChartType, count: int = 5) -> List[str]:
    """生成图表颜色方案"""
    color_schemes = {
        ChartType.LINE: [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ],
        ChartType.BAR: [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ],
        ChartType.SCATTER: [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ],
        ChartType.PIE: [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ],
        ChartType.HEATMAP: [
            '#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8',
            '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026'
        ],
        ChartType.CANDLESTICK: ['#ff7f0e', '#1f77b4'],  # 红涨绿跌
        ChartType.VOLUME: [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
    }

    colors = color_schemes.get(chart_type, ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
    return colors[:count]


def calculate_moving_average(data: List[float], window: int) -> List[float]:
    """计算移动平均线"""
    if window <= 0 or window > len(data):
        return data.copy()

    result = []
    for i in range(len(data)):
        if i < window - 1:
            result.append(data[i])
        else:
            avg = sum(data[i - window + 1:i + 1]) / window
            result.append(avg)

    return result


def calculate_volatility(data: List[float]) -> float:
    """计算波动率"""
    if len(data) < 2:
        return 0.0

    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    return math.sqrt(variance)


def calculate_trend(data: List[float], window: int = 10) -> float:
    """计算趋势斜率"""
    if len(data) < window:
        return 0.0

    # 使用线性回归计算趋势
    n = min(window, len(data))
    x_values = list(range(n))
    y_values = data[-n:]

    x_mean = sum(x_values) / n
    y_mean = sum(y_values) / n

    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
    denominator = sum((x - x_mean) ** 2 for x in x_values)

    if denominator == 0:
        return 0.0

    return numerator / denominator


def generate_summary_statistics(data: List[float]) -> Dict[str, float]:
    """生成摘要统计信息"""
    if not data:
        return {}

    sorted_data = sorted(data)
    n = len(data)

    stats = {
        'count': n,
        'mean': sum(data) / n,
        'min': min(data),
        'max': max(data),
        'median': sorted_data[n // 2] if n % 2 == 1 else (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2,
    }

    if n >= 2:
        # 计算标准差
        mean = stats['mean']
        variance = sum((x - mean) ** 2 for x in data) / n
        stats['std_dev'] = math.sqrt(variance)

        # 计算分位数
        q1_idx = int(n * 0.25)
        q3_idx = int(n * 0.75)
        stats['q1'] = sorted_data[q1_idx]
        stats['q3'] = sorted_data[q3_idx]

        # 计算偏度和峰度
        if stats['std_dev'] > 0:
            skewness = sum((x - mean) ** 3 for x in data) / (n * stats['std_dev'] ** 3)
            kurtosis = sum((x - mean) ** 4 for x in data) / (n * stats['std_dev'] ** 4) - 3
            stats['skewness'] = skewness
            stats['kurtosis'] = kurtosis

    return stats


def format_risk_level(risk_level: int) -> str:
    """格式化风险等级"""
    risk_levels = {
        1: "低风险",
        2: "较低风险",
        3: "中等风险",
        4: "较高风险",
        5: "高风险"
    }
    return risk_levels.get(risk_level, "未知风险")


def format_signal_strength(strength: int) -> str:
    """格式化信号强度"""
    if strength >= 8:
        return f"强信号 ({strength}/10)"
    elif strength >= 6:
        return f"较强信号 ({strength}/10)"
    elif strength >= 4:
        return f"中等信号 ({strength}/10)"
    elif strength >= 2:
        return f"较弱信号 ({strength}/10)"
    else:
        return f"弱信号 ({strength}/10)"


def calculate_performance_metrics(returns: List[float], benchmark_returns: Optional[List[float]] = None) -> Dict[str, float]:
    """计算性能指标"""
    if not returns:
        return {}

    n = len(returns)

    # 基本指标
    total_return = sum(returns)
    mean_return = total_return / n

    # 波动率
    volatility = calculate_volatility(returns)

    # 夏普比率（假设无风险利率为0）
    sharpe_ratio = mean_return / volatility if volatility > 0 else 0.0

    # 最大回撤
    cumulative_returns = [1.0]
    for r in returns:
        cumulative_returns.append(cumulative_returns[-1] * (1 + r))

    peak = cumulative_returns[0]
    max_drawdown = 0.0
    for value in cumulative_returns[1:]:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak
        max_drawdown = max(max_drawdown, drawdown)

    metrics = {
        'total_return': total_return,
        'mean_return': mean_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': sum(1 for r in returns if r > 0) / n
    }

    # 如果有基准收益率，计算相对指标
    if benchmark_returns and len(benchmark_returns) == n:
        # 超额收益
        excess_returns = [r - b for r, b in zip(returns, benchmark_returns)]
        metrics['excess_return'] = sum(excess_returns) / n
        metrics['tracking_error'] = calculate_volatility(excess_returns)
        metrics['information_ratio'] = metrics['excess_return'] / metrics['tracking_error'] if metrics['tracking_error'] > 0 else 0.0

    return metrics


def generate_time_range(start_date: datetime, end_date: datetime, interval_hours: int = 1) -> List[datetime]:
    """生成时间范围"""
    time_points = []
    current_time = start_date

    while current_time <= end_date:
        time_points.append(current_time)
        current_time += timedelta(hours=interval_hours)

    return time_points


def validate_chart_data(data: List[Any], chart_type: ChartType) -> List[str]:
    """验证图表数据"""
    errors = []

    if not data:
        errors.append("图表数据不能为空")
        return errors

    if chart_type == ChartType.LINE:
        # 线图数据应该是数字列表或(x, y)元组列表
        if isinstance(data[0], (int, float)):
            if len(data) < 2:
                errors.append("线图至少需要2个数据点")
        elif isinstance(data[0], (list, tuple)):
            if len(data[0]) != 2:
                errors.append("线图数据点应该是(x, y)格式")

    elif chart_type == ChartType.BAR:
        # 柱状图数据应该是数字列表或(标签, 值)元组列表
        if isinstance(data[0], (int, float)):
            if len(data) < 1:
                errors.append("柱状图至少需要1个数据点")
        elif isinstance(data[0], (list, tuple)):
            if len(data[0]) != 2:
                errors.append("柱状图数据点应该是(标签, 值)格式")

    elif chart_type == ChartType.PIE:
        # 饼图数据应该是(标签, 值)元组列表
        if not all(isinstance(item, (list, tuple)) and len(item) == 2 for item in data):
            errors.append("饼图数据点应该是(标签, 值)格式")

        # 验证值非负
        if any(isinstance(item[1], (int, float)) and item[1] < 0 for item in data):
            errors.append("饼图数据值不能为负数")

    return errors


def create_safe_filename(filename: str) -> str:
    """创建安全的文件名"""
    import re

    # 移除或替换不安全的字符
    unsafe_chars = r'[<>:"/\\|?*]'
    safe_filename = re.sub(unsafe_chars, '_', filename)

    # 移除开头和结尾的空格和点
    safe_filename = safe_filename.strip('. ')

    # 限制文件名长度
    if len(safe_filename) > 200:
        safe_filename = safe_filename[:200]

    return safe_filename


def format_bytes(bytes_value: int) -> str:
    """格式化字节数"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def escape_html(text: str) -> str:
    """转义HTML特殊字符"""
    html_escape_map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }

    for char, replacement in html_escape_map.items():
        text = text.replace(char, replacement)

    return text


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix