"""
新闻收集代理 - 多源新闻收集和管理系统
"""

from .models.base import (
    NewsArticle,
    NewsSourceConfig,
    HealthStatus,
    NewsQuery,
    NewsQueryResult,
    NewsCategory,
    NewsSourceStatus,
    ConnectionInfo
)

from .core.adapter import NewsSourceAdapter, NewsSourceAdapterFactory
from .core.connection_manager import ConnectionManager, ConnectionPoolConfig
from .core.health_checker import HealthChecker, HealthCheckConfig, HealthAlert
from .core.config_manager import ConfigManager, ConfigWatcherConfig
from .core.error_handler import ErrorHandler, ErrorType, ErrorSeverity, RetryPolicy

from .adapters.coindesk_adapter import CoinDeskAdapter
from .adapters.cointelegraph_adapter import CoinTelegraphAdapter
from .adapters.decrypt_adapter import DecryptAdapter

__version__ = "1.0.0"
__author__ = "Crypto Trading Multi-Agents Team"

__all__ = [
    # Models
    "NewsArticle",
    "NewsSourceConfig",
    "HealthStatus",
    "NewsQuery",
    "NewsQueryResult",
    "NewsCategory",
    "NewsSourceStatus",
    "ConnectionInfo",

    # Core Components
    "NewsSourceAdapter",
    "NewsSourceAdapterFactory",
    "ConnectionManager",
    "ConnectionPoolConfig",
    "HealthChecker",
    "HealthCheckConfig",
    "HealthAlert",
    "ConfigManager",
    "ConfigWatcherConfig",
    "ErrorHandler",
    "ErrorType",
    "ErrorSeverity",
    "RetryPolicy",

    # Adapters
    "CoinDeskAdapter",
    "CoinTelegraphAdapter",
    "DecryptAdapter",
]