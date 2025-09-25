import pytest
from datetime import datetime, timezone
from news_collection.models import (
    NewsArticle,
    NewsSource,
    NewsSourceType,
    NewsCategory,
    ConnectionStatus,
    HealthMetrics,
    RateLimitInfo,
)


class TestNewsModels:
    """Test cases for news data models."""

    def test_news_article_creation(self):
        """Test NewsArticle creation and default values."""
        article = NewsArticle(
            id="test_123",
            title="Test Article",
            content="This is test content",
            url="https://example.com/article"
        )

        assert article.id == "test_123"
        assert article.title == "Test Article"
        assert article.content == "This is test content"
        assert article.url == "https://example.com/article"
        assert article.summary is None
        assert article.author is None
        assert article.category == NewsCategory.MARKET_NEWS
        assert article.tags == []
        assert article.metadata == {}
        assert article.published_at is not None

    def test_news_article_with_all_fields(self):
        """Test NewsArticle with all fields provided."""
        now = datetime.now(timezone.utc)
        article = NewsArticle(
            id="test_456",
            title="Full Article",
            content="Full content here",
            summary="Article summary",
            url="https://example.com/full",
            author="John Doe",
            published_at=now,
            source=NewsSourceType.COINDESK,
            category=NewsCategory.TECHNOLOGY,
            tags=["blockchain", "innovation"],
            sentiment_score=0.8,
            relevance_score=0.9,
            metadata={"views": 1000}
        )

        assert article.id == "test_456"
        assert article.title == "Full Article"
        assert article.content == "Full content here"
        assert article.summary == "Article summary"
        assert article.url == "https://example.com/full"
        assert article.author == "John Doe"
        assert article.published_at == now
        assert article.source == NewsSourceType.COINDESK
        assert article.category == NewsCategory.TECHNOLOGY
        assert article.tags == ["blockchain", "innovation"]
        assert article.sentiment_score == 0.8
        assert article.relevance_score == 0.9
        assert article.metadata == {"views": 1000}

    def test_news_source_creation(self):
        """Test NewsSource creation."""
        source = NewsSource(
            name="Test Source",
            source_type=NewsSourceType.COINDESK,
            base_url="https://api.test.com"
        )

        assert source.name == "Test Source"
        assert source.source_type == NewsSourceType.COINDESK
        assert source.base_url == "https://api.test.com"
        assert source.api_key is None
        assert source.rate_limit_per_minute == 60
        assert source.timeout_seconds == 30
        assert source.enabled is True
        assert source.priority == 1
        assert source.config == {}

    def test_news_source_with_config(self):
        """Test NewsSource with custom configuration."""
        source = NewsSource(
            name="Custom Source",
            source_type=NewsSourceType.COINTELEGRAPH,
            base_url="https://api.custom.com",
            api_key="test_key_123",
            rate_limit_per_minute=100,
            timeout_seconds=45,
            enabled=False,
            priority=3,
            config={"custom_param": "value"}
        )

        assert source.name == "Custom Source"
        assert source.source_type == NewsSourceType.COINTELEGRAPH
        assert source.api_key == "test_key_123"
        assert source.rate_limit_per_minute == 100
        assert source.timeout_seconds == 45
        assert source.enabled is False
        assert source.priority == 3
        assert source.config == {"custom_param": "value"}

    def test_connection_status_creation(self):
        """Test ConnectionStatus creation."""
        now = datetime.now()
        status = ConnectionStatus(
            source_name="Test Source",
            is_connected=True,
            response_time_ms=250.5,
            last_checked=now
        )

        assert status.source_name == "Test Source"
        assert status.is_connected is True
        assert status.response_time_ms == 250.5
        assert status.last_checked == now
        assert status.error_message is None
        assert status.consecutive_failures == 0
        assert status.last_success is None

    def test_connection_status_with_errors(self):
        """Test ConnectionStatus with error information."""
        now = datetime.now()
        status = ConnectionStatus(
            source_name="Failed Source",
            is_connected=False,
            response_time_ms=5000.0,
            last_checked=now,
            error_message="Connection timeout",
            consecutive_failures=3,
            last_success=now
        )

        assert status.source_name == "Failed Source"
        assert status.is_connected is False
        assert status.response_time_ms == 5000.0
        assert status.error_message == "Connection timeout"
        assert status.consecutive_failures == 3
        assert status.last_success == now

    def test_health_metrics_creation(self):
        """Test HealthMetrics creation."""
        now = datetime.now()
        metrics = HealthMetrics(
            source_name="Test Source",
            uptime_percentage=99.5,
            average_response_time_ms=150.0,
            success_rate=98.2,
            requests_per_minute=45.5,
            error_count_24h=2,
            last_updated=now
        )

        assert metrics.source_name == "Test Source"
        assert metrics.uptime_percentage == 99.5
        assert metrics.average_response_time_ms == 150.0
        assert metrics.success_rate == 98.2
        assert metrics.requests_per_minute == 45.5
        assert metrics.error_count_24h == 2
        assert metrics.last_updated == now

    def test_rate_limit_info_creation(self):
        """Test RateLimitInfo creation."""
        now = datetime.now()
        rate_info = RateLimitInfo(
            source_name="Test Source",
            requests_remaining=50,
            requests_limit=60,
            reset_time=now,
            retry_after=30
        )

        assert rate_info.source_name == "Test Source"
        assert rate_info.requests_remaining == 50
        assert rate_info.requests_limit == 60
        assert rate_info.reset_time == now
        assert rate_info.retry_after == 30

    def test_rate_limit_info_without_retry(self):
        """Test RateLimitInfo without retry_after."""
        now = datetime.now()
        rate_info = RateLimitInfo(
            source_name="Test Source",
            requests_remaining=10,
            requests_limit=60,
            reset_time=now
        )

        assert rate_info.source_name == "Test Source"
        assert rate_info.requests_remaining == 10
        assert rate_info.requests_limit == 60
        assert rate_info.reset_time == now
        assert rate_info.retry_after is None

    def test_news_source_type_values(self):
        """Test NewsSourceType enum values."""
        assert NewsSourceType.COINDESK.value == "coindesk"
        assert NewsSourceType.COINTELEGRAPH.value == "cointelegraph"
        assert NewsSourceType.DECRYPT.value == "decrypt"
        assert NewsSourceType.CRYPTOSLATE.value == "cryptoslate"
        assert NewsSourceType.THE_BLOCK.value == "the_block"

    def test_news_category_values(self):
        """Test NewsCategory enum values."""
        assert NewsCategory.MARKET_NEWS.value == "market_news"
        assert NewsCategory.TECHNOLOGY.value == "technology"
        assert NewsCategory.REGULATION.value == "regulation"
        assert NewsCategory.SECURITY.value == "security"
        assert NewsCategory.ADOPTION.value == "adoption"
        assert NewsCategory.DEFI.value == "defi"
        assert NewsCategory.NFT.value == "nft"
        assert NewsCategory.EXCHANGE.value == "exchange"
        assert NewsCategory.MINING.value == "mining"
        assert NewsCategory.TRADING.value == "trading"