"""
测试基础数据模型
"""

import pytest
from datetime import datetime
from news_collection.models.base import (
    NewsArticle,
    NewsSourceConfig,
    HealthStatus,
    NewsQuery,
    NewsCategory,
    NewsSourceStatus
)


class TestNewsArticle:
    """测试新闻文章模型"""

    def test_news_article_creation(self):
        """测试新闻文章创建"""
        article = NewsArticle(
            id="test_001",
            title="测试新闻标题",
            content="测试新闻内容"
        )

        assert article.id == "test_001"
        assert article.title == "测试新闻标题"
        assert article.content == "测试新闻内容"
        assert article.tags == []
        assert article.metadata == {}
        assert article.category == NewsCategory.GENERAL

    def test_news_article_with_optional_fields(self):
        """测试带可选字段的新闻文章"""
        article = NewsArticle(
            id="test_002",
            title="测试新闻标题",
            content="测试新闻内容",
            author="测试作者",
            published_at=datetime.now(),
            source="测试来源",
            category=NewsCategory.BREAKING,
            tags=["比特币", "加密货币"],
            metadata={"importance": "high"}
        )

        assert article.author == "测试作者"
        assert article.source == "测试来源"
        assert article.category == NewsCategory.BREAKING
        assert article.tags == ["比特币", "加密货币"]
        assert article.metadata == {"importance": "high"}


class TestNewsSourceConfig:
    """测试新闻源配置模型"""

    def test_news_source_config_creation(self):
        """测试新闻源配置创建"""
        config = NewsSourceConfig(
            name="test_source",
            adapter_type="test_adapter",
            base_url="https://example.com/api"
        )

        assert config.name == "test_source"
        assert config.adapter_type == "test_adapter"
        assert config.base_url == "https://example.com/api"
        assert config.enabled == True
        assert config.priority == 1
        assert config.headers == {}

    def test_news_source_config_with_optional_fields(self):
        """测试带可选字段的新闻源配置"""
        config = NewsSourceConfig(
            name="test_source",
            adapter_type="test_adapter",
            base_url="https://example.com/api",
            api_key="test_key",
            rate_limit=60,
            timeout=15,
            headers={"Authorization": "Bearer token"},
            enabled=False,
            priority=5
        )

        assert config.api_key == "test_key"
        assert config.rate_limit == 60
        assert config.timeout == 15
        assert config.headers == {"Authorization": "Bearer token"}
        assert config.enabled == False
        assert config.priority == 5


class TestHealthStatus:
    """测试健康状态模型"""

    def test_health_status_creation(self):
        """测试健康状态创建"""
        status = HealthStatus(
            is_healthy=True,
            response_time=150.5,
            status=NewsSourceStatus.ONLINE,
            last_check=datetime.now()
        )

        assert status.is_healthy == True
        assert status.response_time == 150.5
        assert status.status == NewsSourceStatus.ONLINE
        assert status.consecutive_failures == 0
        assert status.consecutive_successes == 0

    def test_health_status_with_errors(self):
        """测试带错误信息的健康状态"""
        status = HealthStatus(
            is_healthy=False,
            response_time=5000.0,
            status=NewsSourceStatus.OFFLINE,
            last_check=datetime.now(),
            error_message="连接超时",
            consecutive_failures=3,
            consecutive_successes=0
        )

        assert status.is_healthy == False
        assert status.error_message == "连接超时"
        assert status.consecutive_failures == 3


class TestNewsQuery:
    """测试新闻查询模型"""

    def test_news_query_creation(self):
        """测试新闻查询创建"""
        query = NewsQuery()

        assert query.keywords == []
        assert query.categories == []
        assert query.sources == []
        assert query.limit == 50
        assert query.offset == 0

    def test_news_query_with_parameters(self):
        """测试带参数的新闻查询"""
        query = NewsQuery(
            keywords=["比特币", "以太坊"],
            categories=[NewsCategory.MARKET_ANALYSIS, NewsCategory.TECHNOLOGY],
            sources=["coindesk", "cointelegraph"],
            limit=100,
            offset=20
        )

        assert query.keywords == ["比特币", "以太坊"]
        assert len(query.categories) == 2
        assert query.sources == ["coindesk", "cointelegraph"]
        assert query.limit == 100
        assert query.offset == 20

    def test_news_query_with_dates(self):
        """测试带日期的新闻查询"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        query = NewsQuery(
            start_date=start_date,
            end_date=end_date,
            keywords=["测试"]
        )

        assert query.start_date == start_date
        assert query.end_date == end_date


if __name__ == "__main__":
    pytest.main([__file__])