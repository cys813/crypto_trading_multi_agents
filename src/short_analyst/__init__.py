"""
做空分析师代理 (Short Analyst Agent)

专门用于识别高估资产、市场过热信号、潜在风险因素的做空分析代理。
通过技术指标分析、情绪分析和LLM深度分析生成高质量的做空分析报告和胜率评估。
"""

__version__ = "1.0.0"
__author__ = "Crypto Trading Multi-Agents Team"
__email__ = "dev@crypto-trading-agents.com"

# TODO: Import modules when they are implemented
# from .core import (
#     ShortAnalystArchitecture,
#     ShortAnalystConfig,
#     AnalysisMode,
#     get_short_analyst,
#     initialize_short_analyst
# )

# from .models import (
#     ShortSignal,
#     ShortSignalType,
#     ShortSignalStrength,
#     MarketData,
#     ShortAnalysisResult,
#     AnalysisRecommendation,
#     RiskLevel
# )

__all__ = []

# 版本信息
VERSION_INFO = {
    "version": __version__,
    "author": __author__,
    "email": __email__,
    "description": "做空分析师代理 - 专门用于识别做空机会和风险评估",
    "license": "MIT",
    "github": "https://github.com/cys813/crypto_trading_multi_agents",
    "docs": "https://crypto-trading-agents.readthedocs.io"
}


def get_version_info():
    """获取版本信息"""
    return VERSION_INFO


def print_version():
    """打印版本信息"""
    info = get_version_info()
    print(f"做空分析师代理 v{info['version']}")
    print(f"作者: {info['author']}")
    print(f"邮箱: {info['email']}")
    print(f"描述: {info['description']}")
    print(f"GitHub: {info['github']}")
    print(f"文档: {info['docs']}")


# 创建默认实例
default_short_analyst = None


# TODO: Implement when core module is ready
# def get_default_short_analyst() -> ShortAnalystArchitecture:
#     """获取默认做空分析师实例"""
#     global default_short_analyst
#     if default_short_analyst is None:
#         default_short_analyst = ShortAnalystArchitecture()
#     return default_short_analyst