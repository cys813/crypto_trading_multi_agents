"""
News Collection Agent - 基础数据模型定义
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class NewsSourceStatus(Enum):
    """新闻源状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"


class NewsCategory(Enum):
    """新闻分类枚举"""
    BREAKING = "breaking"
    MARKET_ANALYSIS = "market_analysis"
    REGULATION = "regulation"
    TECHNOLOGY = "technology"
    SECURITY = "security"
    ADOPTION = "adoption"
    GENERAL = "general"


@dataclass
class NewsArticle:
    """新闻文章数据模型"""
    id: str
    title: str
    content: str
    summary: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    source: Optional[str] = None
    url: Optional[str] = None
    category: NewsCategory = NewsCategory.GENERAL
    tags: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class NewsSourceConfig:
    """新闻源配置模型"""
    name: str
    adapter_type: str
    base_url: str
    api_key: Optional[str] = None
    rate_limit: int = 100  # requests per minute
    timeout: int = 30  # seconds
    headers: Dict[str, str] = None
    enabled: bool = True
    priority: int = 1  # 1-10, higher is more important

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


@dataclass
class HealthStatus:
    """健康状态模型"""
    is_healthy: bool
    response_time: float  # milliseconds
    status: NewsSourceStatus
    last_check: datetime
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0


@dataclass
class ConnectionInfo:
    """连接信息模型"""
    connection_id: str
    source_name: str
    created_at: datetime
    last_used: datetime
    is_active: bool
    request_count: int = 0
    error_count: int = 0


@dataclass
class NewsQuery:
    """新闻查询模型"""
    keywords: Optional[List[str]] = None
    categories: Optional[List[NewsCategory]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sources: Optional[List[str]] = None
    limit: int = 50
    offset: int = 0

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.categories is None:
            self.categories = []
        if self.sources is None:
            self.sources = []


@dataclass
class NewsQueryResult:
    """新闻查询结果模型"""
    articles: List[NewsArticle]
    total_count: int
    has_more: bool
    query: NewsQuery
    execution_time: float  # milliseconds
    sources_used: List[str]
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []