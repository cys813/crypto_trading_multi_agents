"""
News Collection Agent Framework

A comprehensive framework for collecting cryptocurrency news from multiple sources
with unified adapter interfaces, connection management, health monitoring, and
automated failover mechanisms.
"""

from .news_manager import NewsCollectionManager
from .models import (
    NewsArticle,
    NewsSource,
    NewsSourceType,
    NewsCategory,
    ConnectionStatus,
    HealthMetrics,
    RateLimitInfo,
)
from .core import ConnectionManager, HealthMonitor, HealthAlert
from .adapters import (
    BaseNewsAdapter,
    CoinDeskAdapter,
    CoinTelegraphAdapter,
    DecryptAdapter,
)
from .utils import RateLimiter

__version__ = "1.0.0"
__author__ = "Crypto Trading Multi Agents Team"
__email__ = "team@crypto-trading-agents.com"

__all__ = [
    # Main manager
    "NewsCollectionManager",

    # Core components
    "ConnectionManager",
    "HealthMonitor",
    "HealthAlert",
    "RateLimiter",

    # Data models
    "NewsArticle",
    "NewsSource",
    "NewsSourceType",
    "NewsCategory",
    "ConnectionStatus",
    "HealthMetrics",
    "RateLimitInfo",

    # Adapters
    "BaseNewsAdapter",
    "CoinDeskAdapter",
    "CoinTelegraphAdapter",
    "DecryptAdapter",
]