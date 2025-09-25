"""
测试适配器基础功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from news_collection.models.base import (
    NewsSourceConfig,
    NewsQuery,
    NewsArticle,
    NewsCategory
)
from news_collection.core.adapter import NewsSourceAdapter, NewsSourceAdapterFactory


class MockNewsSourceAdapter(NewsSourceAdapter):
    """模拟新闻源适配器"""

    def __init__(self, config: NewsSourceConfig):
        super().__init__(config)
        self._is_connected = False

    @property
    def source_name(self) -> str:
        return "mock_source"

    @property
    def adapter_type(self) -> str:
        return "mock_adapter"

    async def connect(self) -> bool:
        self._is_connected = True
        return True

    async def disconnect(self) -> bool:
        self._is_connected = False
        return True

    async def fetch_news(self, query: NewsQuery):
        return MockNewsQueryResult()

    async def health_check(self):
        from news_collection.models.base import HealthStatus, NewsSourceStatus
        return HealthStatus(
            is_healthy=True,
            response_time=100.0,
            status=NewsSourceStatus.ONLINE,
            last_check=datetime.now()
        )

    async def get_latest_news(self, limit: int = 20):
        return [
            NewsArticle(
                id=f"article_{i}",
                title=f"测试文章 {i}",
                content=f"测试内容 {i}",
                published_at=datetime.now()
            )
            for i in range(limit)
        ]

    async def search_news(self, keywords: list, limit: int = 50):
        return [
            NewsArticle(
                id=f"search_{i}",
                title=f"搜索结果 {i}: {' '.join(keywords)}",
                content=f"搜索内容 {i}",
                published_at=datetime.now()
            )
            for i in range(limit)
        ]


class MockNewsQueryResult:
    """模拟查询结果"""
    def __init__(self):
        self.articles = []
        self.total_count = 0
        self.has_more = False
        self.query = NewsQuery()
        self.execution_time = 100.0
        self.sources_used = ["mock_source"]
        self.errors = []


class TestNewsSourceAdapter:
    """测试新闻源适配器基类"""

    @pytest.fixture
    def config(self):
        """测试配置"""
        return NewsSourceConfig(
            name="test_source",
            adapter_type="mock_adapter",
            base_url="https://example.com/api",
            api_key="test_key"
        )

    @pytest.fixture
    def adapter(self, config):
        """测试适配器"""
        return MockNewsSourceAdapter(config)

    @pytest.mark.asyncio
    async def test_adapter_initialization(self, adapter):
        """测试适配器初始化"""
        assert adapter.config.name == "test_source"
        assert adapter.config.adapter_type == "mock_adapter"
        assert adapter.source_name == "mock_source"
        assert adapter.adapter_type == "mock_adapter"

    @pytest.mark.asyncio
    async def test_adapter_connect_disconnect(self, adapter):
        """测试连接和断开"""
        # 测试连接
        result = await adapter.connect()
        assert result == True
        assert adapter._is_connected == True

        # 测试断开
        result = await adapter.disconnect()
        assert result == True
        assert adapter._is_connected == False

    @pytest.mark.asyncio
    async def test_adapter_initialize_and_close(self, adapter):
        """测试初始化和关闭"""
        # 测试初始化
        result = await adapter.initialize()
        assert result == True
        assert adapter.session is not None
        assert adapter._connection_info is not None
        assert adapter._connection_info.is_active == True

        # 测试关闭
        result = await adapter.close()
        assert result == True
        assert adapter._connection_info.is_active == False

    @pytest.mark.asyncio
    async def test_adapter_get_latest_news(self, adapter):
        """测试获取最新新闻"""
        await adapter.initialize()
        articles = await adapter.get_latest_news(limit=5)

        assert len(articles) == 5
        for i, article in enumerate(articles):
            assert article.id == f"article_{i}"
            assert article.title == f"测试文章 {i}"
            assert article.content == f"测试内容 {i}"

        await adapter.close()

    @pytest.mark.asyncio
    async def test_adapter_search_news(self, adapter):
        """测试搜索新闻"""
        await adapter.initialize()
        articles = await adapter.search_news(["比特币", "加密货币"], limit=3)

        assert len(articles) == 3
        for i, article in enumerate(articles):
            assert article.id == f"search_{i}"
            assert "比特币" in article.title
            assert "加密货币" in article.title

        await adapter.close()

    @pytest.mark.asyncio
    async def test_adapter_stats(self, adapter):
        """测试统计信息"""
        await adapter.initialize()

        stats = adapter.get_stats()
        assert stats["source_name"] == "mock_source"
        assert stats["request_count"] == 0
        assert stats["error_count"] == 0
        assert stats["is_connected"] == True

        await adapter.close()

    @pytest.mark.asyncio
    async def test_adapter_connection_info(self, adapter):
        """测试连接信息"""
        await adapter.initialize()

        connection_info = adapter.get_connection_info()
        assert connection_info is not None
        assert connection_info.source_name == "mock_source"
        assert connection_info.is_active == True
        assert connection_info.request_count == 0

        await adapter.close()


class TestNewsSourceAdapterFactory:
    """测试新闻源适配器工厂"""

    def test_factory_register_adapter(self):
        """测试注册适配器"""
        # 清理已注册的适配器
        NewsSourceAdapterFactory._adapters.clear()

        # 注册适配器
        NewsSourceAdapterFactory.register_adapter("mock", MockNewsSourceAdapter)

        assert "mock" in NewsSourceAdapterFactory._adapters
        assert NewsSourceAdapterFactory._adapters["mock"] == MockNewsSourceAdapter

    def test_factory_create_adapter(self):
        """测试创建适配器"""
        # 清理并注册适配器
        NewsSourceAdapterFactory._adapters.clear()
        NewsSourceAdapterFactory.register_adapter("mock", MockNewsSourceAdapter)

        config = NewsSourceConfig(
            name="test_source",
            adapter_type="mock",
            base_url="https://example.com/api"
        )

        adapter = NewsSourceAdapterFactory.create_adapter(config)
        assert isinstance(adapter, MockNewsSourceAdapter)
        assert adapter.config.name == "test_source"

    def test_factory_create_adapter_invalid_type(self):
        """测试创建无效类型的适配器"""
        config = NewsSourceConfig(
            name="test_source",
            adapter_type="invalid_type",
            base_url="https://example.com/api"
        )

        with pytest.raises(ValueError, match="不支持的适配器类型"):
            NewsSourceAdapterFactory.create_adapter(config)

    def test_factory_get_available_adapters(self):
        """测试获取可用适配器列表"""
        # 清理并注册适配器
        NewsSourceAdapterFactory._adapters.clear()
        NewsSourceAdapterFactory.register_adapter("mock", MockNewsSourceAdapter)

        adapters = NewsSourceAdapterFactory.get_available_adapters()
        assert "mock" in adapters


if __name__ == "__main__":
    pytest.main([__file__])