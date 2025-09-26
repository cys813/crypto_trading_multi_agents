"""
Tests for LLM connector module
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from ..llm_connector import (
    LLMConnector, LLMConfig, LLMProvider, LLMMessage, LLMResponse,
    OpenAIProvider, AnthropicProvider, MockProvider, CacheManager
)
from ...models.base import NewsArticle


class TestLLMConfig:
    """测试LLM配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = LLMConfig()
        assert config.provider == LLMProvider.MOCK
        assert config.model == "gpt-3.5-turbo"
        assert config.max_tokens == 2000
        assert config.temperature == 0.3
        assert config.timeout == 30.0
        assert config.retry_attempts == 3
        assert config.enable_cache == True

    def test_custom_config(self):
        """测试自定义配置"""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4",
            max_tokens=1000,
            temperature=0.5
        )
        assert config.provider == LLMProvider.OPENAI
        assert config.model == "gpt-4"
        assert config.max_tokens == 1000
        assert config.temperature == 0.5


class TestLLMMessage:
    """测试LLM消息类"""

    def test_message_creation(self):
        """测试消息创建"""
        message = LLMMessage(role="user", content="Hello, world!")
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.metadata == {}

    def test_message_with_metadata(self):
        """测试带元数据的消息"""
        metadata = {"source": "test", "timestamp": "2023-01-01"}
        message = LLMMessage(role="system", content="System message", metadata=metadata)
        assert message.metadata == metadata


class TestMockProvider:
    """测试Mock提供商"""

    @pytest.mark.asyncio
    async def test_generate_response(self):
        """测试生成响应"""
        config = LLMConfig(provider=LLMProvider.MOCK)
        provider = MockProvider(config)

        messages = [
            LLMMessage(role="user", content="Test message")
        ]

        response = await provider.generate_response(messages, config)

        assert isinstance(response, LLMResponse)
        assert response.provider == LLMProvider.MOCK
        assert response.content is not None
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        config = LLMConfig(provider=LLMProvider.MOCK)
        provider = MockProvider(config)

        is_healthy = await provider.health_check()
        assert is_healthy is True


class TestCacheManager:
    """测试缓存管理器"""

    def test_cache_key_generation(self):
        """测试缓存键生成"""
        config = LLMConfig()
        cache = CacheManager(config)

        messages = [
            LLMMessage(role="user", content="Test message")
        ]

        key1 = cache._generate_cache_key(messages, config)
        key2 = cache._generate_cache_key(messages, config)

        # 相同输入应该生成相同键
        assert key1 == key2

        # 不同输入应该生成不同键
        different_messages = [LLMMessage(role="user", content="Different message")]
        key3 = cache._generate_cache_key(different_messages, config)
        assert key1 != key3

    def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        config = LLMConfig()
        cache = CacheManager(config)

        messages = [LLMMessage(role="user", content="Test message")]
        response = LLMResponse(
            content="Test response",
            usage={"total_tokens": 10},
            model="test-model",
            provider=LLMProvider.MOCK,
            response_time=0.1
        )

        # 缓存响应
        cache.set(messages, config, response)

        # 获取缓存的响应
        cached_response = cache.get(messages, config)

        assert cached_response is not None
        assert cached_response.content == response.content
        assert cached_response.cached is True

    def test_cache_stats(self):
        """测试缓存统计"""
        config = LLMConfig()
        cache = CacheManager(config)

        messages = [LLMMessage(role="user", content="Test message")]
        response = LLMResponse(
            content="Test response",
            usage={"total_tokens": 10},
            model="test-model",
            provider=LLMProvider.MOCK,
            response_time=0.1
        )

        # 初始统计
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

        # 缓存命中
        cache.set(messages, config, response)
        cached_response = cache.get(messages, config)
        assert cached_response is not None

        # 检查统计更新
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 1.0

        # 缓存未命中
        different_messages = [LLMMessage(role="user", content="Different message")]
        cache.get(different_messages, config)

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


class TestLLMConnector:
    """测试LLM连接器"""

    @pytest.mark.asyncio
    async def test_generate_response(self):
        """测试生成响应"""
        config = LLMConfig(provider=LLMProvider.MOCK)
        connector = LLMConnector(config)

        messages = [LLMMessage(role="user", content="Hello, world!")]

        response = await connector.generate_response(messages)

        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert response.provider == LLMProvider.MOCK

    @pytest.mark.asyncio
    async def test_caching(self):
        """测试缓存功能"""
        config = LLMConfig(enable_cache=True)
        connector = LLMConnector(config)

        messages = [LLMMessage(role="user", content="Test message")]

        # 第一次请求
        response1 = await connector.generate_response(messages)
        assert response1.cached is False

        # 第二次请求应该从缓存获取
        response2 = await connector.generate_response(messages)
        assert response2.cached is True

        # 响应内容应该相同
        assert response1.content == response2.content

    @pytest.mark.asyncio
    async def test_stats(self):
        """测试统计信息"""
        config = LLMConfig()
        connector = LLMConnector(config)

        messages = [LLMMessage(role="user", content="Test message")]

        # 生成一些请求
        await connector.generate_response(messages)
        await connector.generate_response(messages)

        stats = connector.get_stats()
        assert stats["total_requests"] == 2
        assert stats["successful_requests"] == 2
        assert stats["failed_requests"] == 0
        assert stats["total_tokens_used"] > 0

    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        config = LLMConfig()
        connector = LLMConnector(config)

        health = await connector.health_check()
        assert health["provider"] == "mock"
        assert health["healthy"] is True
        assert "cache_stats" in health
        assert "request_stats" in health


class TestLLMConnectorIntegration:
    """LLM连接器集成测试"""

    @pytest.mark.asyncio
    async def test_with_news_article(self):
        """测试与新闻文章的集成"""
        config = LLMConfig()
        connector = LLMConnector(config)

        article = NewsArticle(
            id="test-article-1",
            title="Bitcoin reaches new all-time high",
            content="Bitcoin has reached a new all-time high of $50,000 as institutional adoption continues to grow.",
            source="Test News",
            category="breaking"
        )

        # 创建摘要请求
        messages = [
            LLMMessage(
                role="user",
                content=f"Please summarize this news article:\n\nTitle: {article.title}\n\nContent: {article.content}"
            )
        ]

        response = await connector.generate_response(messages)

        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        # 配置一个会失败的提供商
        config = LLMConfig(retry_attempts=1)
        connector = LLMConnector(config)

        # 模拟提供商总是失败
        with patch.object(connector.provider, 'generate_response', side_effect=Exception("API Error")):
            messages = [LLMMessage(role="user", content="Test message")]

            with pytest.raises(Exception):
                await connector.generate_response(messages)

            # 检查统计信息
            stats = connector.get_stats()
            assert stats["failed_requests"] == 1


if __name__ == "__main__":
    pytest.main([__file__])