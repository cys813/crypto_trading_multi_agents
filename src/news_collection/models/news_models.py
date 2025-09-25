from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class NewsSourceType(Enum):
    """News source types supported by the system."""
    COINDESK = "coindesk"
    COINTELEGRAPH = "cointelegraph"
    DECRYPT = "decrypt"
    CRYPTOSLATE = "cryptoslate"
    THE_BLOCK = "the_block"


class NewsCategory(Enum):
    """News categories for classification."""
    MARKET_NEWS = "market_news"
    TECHNOLOGY = "technology"
    REGULATION = "regulation"
    SECURITY = "security"
    ADOPTION = "adoption"
    DEFI = "defi"
    NFT = "nft"
    EXCHANGE = "exchange"
    MINING = "mining"
    TRADING = "trading"


@dataclass
class NewsArticle:
    """Represents a single news article."""
    id: str
    title: str
    content: str
    summary: Optional[str] = None
    url: str
    author: Optional[str] = None
    published_at: datetime = None
    source: NewsSourceType = None
    category: NewsCategory = NewsCategory.MARKET_NEWS
    tags: List[str] = None
    sentiment_score: Optional[float] = None
    relevance_score: Optional[float] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
        if self.published_at is None:
            self.published_at = datetime.now()


@dataclass
class NewsSource:
    """Represents a news source configuration."""
    name: str
    source_type: NewsSourceType
    base_url: str
    api_key: Optional[str] = None
    rate_limit_per_minute: int = 60
    timeout_seconds: int = 30
    enabled: bool = True
    priority: int = 1
    config: Dict[str, Any] = None

    def __post_init__(self):
        if self.config is None:
            self.config = {}


@dataclass
class ConnectionStatus:
    """Represents the connection status of a news source."""
    source_name: str
    is_connected: bool
    response_time_ms: float
    last_checked: datetime
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    last_success: Optional[datetime] = None


@dataclass
class HealthMetrics:
    """Health metrics for a news source."""
    source_name: str
    uptime_percentage: float
    average_response_time_ms: float
    success_rate: float
    requests_per_minute: float
    error_count_24h: int
    last_updated: datetime


@dataclass
class RateLimitInfo:
    """Rate limit information for a news source."""
    source_name: str
    requests_remaining: int
    requests_limit: int
    reset_time: datetime
    retry_after: Optional[int] = None