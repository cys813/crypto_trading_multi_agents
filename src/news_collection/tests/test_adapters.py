import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from news_collection.adapters.base_adapter import BaseNewsAdapter
from news_collection.adapters.coindesk_adapter import CoinDeskAdapter
from news_collection.adapters.cointelegraph_adapter import CoinTelegraphAdapter
from news_collection.adapters.decrypt_adapter import DecryptAdapter
from news_collection.models import (
    NewsSource,
    NewsSourceType,
    NewsCategory,
    NewsArticle,
    ConnectionStatus,
    RateLimitInfo,
)


class TestBaseAdapter:
    """Test cases for BaseNewsAdapter."""

    def test_base_adapter_creation(self):
        """Test BaseNewsAdapter creation."""
        source_config = NewsSource(
            name="Test Source",
            source_type=NewsSourceType.COINDESK,
            base_url="https://api.test.com"
        )

        # Create a concrete implementation for testing
        class TestAdapter(BaseNewsAdapter):
            @property
            def source_name(self):
                return "Test Adapter"

            @property
            def supported_categories(self):
                return [NewsCategory.MARKET_NEWS]

            async def fetch_news(self, **kwargs):
                return []

            async def test_connection(self):
                return ConnectionStatus(
                    source_name=self.source_name,
                    is_connected=True,
                    response_time_ms=100,
                    last_checked=datetime.now()
                )

            async def get_rate_limit_info(self):
                return RateLimitInfo(
                    source_name=self.source_name,
                    requests_remaining=60,
                    requests_limit=60,
                    reset_time=datetime.now()
                )

            def _parse_article(self, raw_data):
                return NewsArticle(
                    id="test",
                    title="Test",
                    content="Content",
                    url="https://test.com"
                )

        adapter = TestAdapter(source_config)

        assert adapter.source_config == source_config
        assert adapter.source_name == "Test Adapter"
        assert adapter.supported_categories == [NewsCategory.MARKET_NEWS]
        assert adapter.is_healthy() is True
        assert adapter.get_failure_count() == 0

    def test_base_adapter_health_tracking(self):
        """Test health tracking in BaseAdapter."""
        source_config = NewsSource(
            name="Test Source",
            source_type=NewsSourceType.COINDESK,
            base_url="https://api.test.com"
        )

        class TestAdapter(BaseNewsAdapter):
            @property
            def source_name(self):
                return "Test Adapter"

            @property
            def supported_categories(self):
                return [NewsCategory.MARKET_NEWS]

            async def fetch_news(self, **kwargs):
                return []

            async def test_connection(self):
                return ConnectionStatus(
                    source_name=self.source_name,
                    is_connected=True,
                    response_time_ms=100,
                    last_checked=datetime.now()
                )

            async def get_rate_limit_info(self):
                return RateLimitInfo(
                    source_name=self.source_name,
                    requests_remaining=60,
                    requests_limit=60,
                    reset_time=datetime.now()
                )

            def _parse_article(self, raw_data):
                return NewsArticle(
                    id="test",
                    title="Test",
                    content="Content",
                    url="https://test.com"
                )

        adapter = TestAdapter(source_config)

        # Initially healthy
        assert adapter.is_healthy() is True
        assert adapter.get_failure_count() == 0

        # Simulate failures
        adapter._consecutive_failures = 2
        assert adapter.is_healthy() is True
        assert adapter.get_failure_count() == 2

        # Simulate unhealthy state
        adapter._consecutive_failures = 3
        assert adapter.is_healthy() is False
        assert adapter.get_failure_count() == 3

        # Simulate recovery
        adapter._consecutive_failures = 0
        adapter._is_healthy = True
        assert adapter.is_healthy() is True
        assert adapter.get_failure_count() == 0


class TestCoinDeskAdapter:
    """Test cases for CoinDeskAdapter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.source_config = NewsSource(
            name="CoinDesk",
            source_type=NewsSourceType.COINDESK,
            base_url="https://api.coindesk.com/v1"
        )
        self.adapter = CoinDeskAdapter(self.source_config)

    def test_coindesk_adapter_properties(self):
        """Test CoinDesk adapter properties."""
        assert self.adapter.source_name == "CoinDesk"
        assert len(self.adapter.supported_categories) == 10
        assert NewsCategory.MARKET_NEWS in self.adapter.supported_categories
        assert NewsCategory.TECHNOLOGY in self.adapter.supported_categories

    def test_parse_article(self):
        """Test article parsing."""
        raw_data = {
            "id": "12345",
            "title": "Bitcoin Price Surges",
            "body": "Bitcoin price has surged to new heights...",
            "url": "https://www.coindesk.com/bitcoin-price-surges",
            "author": {"name": "John Doe"},
            "published_at": "2023-12-01T10:00:00Z",
            "summary": "Bitcoin reaches new all-time high",
            "tags": [{"name": "bitcoin"}, {"name": "price"}],
            "image_url": "https://example.com/image.jpg"
        }

        article = self.adapter._parse_article(raw_data)

        assert article.id.startswith("coindesk_")
        assert article.title == "Bitcoin Price Surges"
        assert "Bitcoin price has surged" in article.content
        assert article.url == "https://www.coindesk.com/bitcoin-price-surges"
        assert article.author == "John Doe"
        assert article.source == NewsSourceType.COINDESK
        assert "bitcoin" in article.tags
        assert "price" in article.tags
        assert article.metadata["source_specific"]["image_url"] == "https://example.com/image.jpg"

    def test_determine_category(self):
        """Test category determination."""
        # Market news
        market_data = {"title": "Bitcoin market analysis", "body": "Price trading volume analysis"}
        category = self.adapter._determine_category(market_data)
        assert category == NewsCategory.MARKET_NEWS

        # Technology
        tech_data = {"title": "Blockchain technology update", "body": "New protocol development"}
        category = self.adapter._determine_category(tech_data)
        assert category == NewsCategory.TECHNOLOGY

        # Regulation
        reg_data = {"title": "SEC regulation news", "body": "New legal compliance requirements"}
        category = self.adapter._determine_category(reg_data)
        assert category == NewsCategory.REGULATION

    def test_parse_date(self):
        """Test date parsing."""
        # ISO format with Z
        date_str = "2023-12-01T10:00:00Z"
        parsed_date = self.adapter._parse_date(date_str)
        assert parsed_date is not None
        assert parsed_date.tzinfo is not None

        # ISO format without Z
        date_str = "2023-12-01T10:00:00"
        parsed_date = self.adapter._parse_date(date_str)
        assert parsed_date is not None

        # Invalid date
        assert self.adapter._parse_date("invalid") is None

    def test_should_include_article(self):
        """Test article filtering."""
        article = NewsArticle(
            id="test",
            title="Bitcoin news",
            content="Bitcoin content",
            url="https://test.com",
            category=NewsCategory.MARKET_NEWS,
            published_at=datetime.now(timezone.utc),
            tags=["bitcoin"]
        )

        # Should include by default
        assert self.adapter._should_include_article(article, None, None, None) is True

        # Category filter - should exclude if not matching
        assert self.adapter._should_include_article(
            article, NewsCategory.TECHNOLOGY, None, None
        ) is False

        # Category filter - should include if matching
        assert self.adapter._should_include_article(
            article, NewsCategory.MARKET_NEWS, None, None
        ) is True

        # Keywords filter - should include if matching
        assert self.adapter._should_include_article(
            article, None, ["bitcoin"], None
        ) is True

        # Keywords filter - should exclude if not matching
        assert self.adapter._should_include_article(
            article, None, ["ethereum"], None
        ) is False

        # Time filter - should exclude if too old
        old_time = datetime.now(timezone.utc) - timedelta(hours=25)
        since_time = datetime.now(timezone.utc) - timedelta(hours=24)
        article.published_at = old_time
        assert self.adapter._should_include_article(
            article, None, None, since_time
        ) is False


class TestCoinTelegraphAdapter:
    """Test cases for CoinTelegraphAdapter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.source_config = NewsSource(
            name="CoinTelegraph",
            source_type=NewsSourceType.COINTELEGRAPH,
            base_url="https://cointelegraph.com/api/v1"
        )
        self.adapter = CoinTelegraphAdapter(self.source_config)

    def test_cointelegraph_adapter_properties(self):
        """Test CoinTelegraph adapter properties."""
        assert self.adapter.source_name == "CoinTelegraph"
        assert len(self.adapter.supported_categories) == 10
        assert NewsCategory.MARKET_NEWS in self.adapter.supported_categories

    def test_parse_article(self):
        """Test article parsing."""
        raw_data = {
            "id": "67890",
            "title": "Ethereum Upgrade Complete",
            "body": "Ethereum upgrade has been successfully completed...",
            "url": "https://cointelegraph.com/ethereum-upgrade",
            "author": {"name": "Jane Smith"},
            "published_at": "2023-12-01T11:00:00Z",
            "lead": "Ethereum completes major network upgrade",
            "tags": [{"name": "ethereum"}, {"name": "upgrade"}],
            "categories": [{"name": "technology"}],
            "views": 1000,
            "comments": 50
        }

        article = self.adapter._parse_article(raw_data)

        assert article.id.startswith("cointelegraph_")
        assert article.title == "Ethereum Upgrade Complete"
        assert "Ethereum upgrade has been successfully completed" in article.content
        assert article.summary == "Ethereum completes major network upgrade"
        assert article.author == "Jane Smith"
        assert article.source == NewsSourceType.COINTELEGRAPH
        assert "ethereum" in article.tags
        assert "upgrade" in article.tags
        assert "technology" in article.tags
        assert article.metadata["source_specific"]["views"] == 1000
        assert article.metadata["source_specific"]["comments"] == 50


class TestDecryptAdapter:
    """Test cases for DecryptAdapter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.source_config = NewsSource(
            name="Decrypt",
            source_type=NewsSourceType.DECRYPT,
            base_url="https://api.decrypt.co/v1"
        )
        self.adapter = DecryptAdapter(self.source_config)

    def test_decrypt_adapter_properties(self):
        """Test Decrypt adapter properties."""
        assert self.adapter.source_name == "Decrypt"
        assert len(self.adapter.supported_categories) == 10
        assert NewsCategory.MARKET_NEWS in self.adapter.supported_categories

    def test_parse_article(self):
        """Test article parsing."""
        raw_data = {
            "id": "abc123",
            "title": "DeFi Protocol Launch",
            "content": "New DeFi protocol launched with innovative features...",
            "url": "https://decrypt.co/defi-protocol",
            "author": "Alex Johnson",
            "published_at": "2023-12-01T12:00:00Z",
            "excerpt": "Revolutionary DeFi protocol enters market",
            "tags": ["defi", "protocol"],
            "categories": [{"name": "defi"}],
            "featured_image": "https://decrypt.co/image.jpg",
            "reading_time": 5,
            "word_count": 1200
        }

        article = self.adapter._parse_article(raw_data)

        assert article.id.startswith("decrypt_")
        assert article.title == "DeFi Protocol Launch"
        assert "New DeFi protocol launched" in article.content
        assert article.summary == "Revolutionary DeFi protocol enters market"
        assert article.author == "Alex Johnson"
        assert article.source == NewsSourceType.DECRYPT
        assert "defi" in article.tags
        assert "protocol" in article.tags
        assert "defi" in article.tags
        assert article.metadata["source_specific"]["featured_image"] == "https://decrypt.co/image.jpg"
        assert article.metadata["source_specific"]["reading_time"] == 5
        assert article.metadata["source_specific"]["word_count"] == 1200

    def test_parse_date_multiple_formats(self):
        """Test date parsing with multiple formats."""
        # ISO with microseconds
        date1 = self.adapter._parse_date("2023-12-01T10:00:00.123Z")
        assert date1 is not None

        # ISO without microseconds
        date2 = self.adapter._parse_date("2023-12-01T10:00:00Z")
        assert date2 is not None

        # Standard datetime
        date3 = self.adapter._parse_date("2023-12-01 10:00:00")
        assert date3 is not None

        # Date only
        date4 = self.adapter._parse_date("2023-12-01")
        assert date4 is not None

        # Invalid
        assert self.adapter._parse_date("invalid") is None


# Import for test
from datetime import timedelta