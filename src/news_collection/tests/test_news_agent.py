"""
测试新闻收集代理主类
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from news_collection.news_agent import NewsCollectionAgent
from news_collection.models.base import (
    NewsSourceConfig,
    NewsQuery,
    NewsArticle,
    NewsCategory
)


class TestNewsCollectionAgent:
    """测试新闻收集代理"""

    @pytest.fixture
    def agent(self):
        """测试代理实例"""
        return NewsCollectionAgent()

    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """测试代理初始化"""
        with patch.object(agent.config_manager, 'initialize', return_value=True):
            result = await agent.initialize()
            assert result == True
            assert agent._running == True
            assert agent._stats["start_time"] is not None

    @pytest.mark.asyncio
    async def test_agent_shutdown(self, agent):
        """测试代理关闭"""
        agent._running = True
        agent._stats["start_time"] = datetime.now()

        await agent.shutdown()
        assert agent._running == False

    @pytest.mark.asyncio
    async def test_collect_news_success(self, agent):
        """测试成功收集新闻"""
        # 模拟可用新闻源
        mock_config = NewsSourceConfig(
            name="test_source",
            adapter_type="mock",
            base_url="https://example.com/api"
        )

        with patch.object(agent, 'get_available_sources', return_value=[mock_config]):
            with patch.object(agent, '_collect_from_source') as mock_collect:
                # 模拟收集结果
                mock_result = Mock()
                mock_result.articles = [
                    NewsArticle(
                        id="test_001",
                        title="测试新闻",
                        content="测试内容",
                        published_at=datetime.now()
                    )
                ]
                mock_result.errors = []
                mock_result.sources_used = ["test_source"]
                mock_collect.return_value = mock_result

                query = NewsQuery(limit=10)
                result = await agent.collect_news(query)

                assert len(result.articles) == 1
                assert result.articles[0].title == "测试新闻"
                assert len(result.errors) == 0
                assert result.sources_used == ["test_source"]

    @pytest.mark.asyncio
    async def test_collect_news_no_sources(self, agent):
        """测试无可用新闻源时收集新闻"""
        with patch.object(agent, 'get_available_sources', return_value=[]):
            query = NewsQuery(limit=10)
            result = await agent.collect_news(query)

            assert len(result.articles) == 0
            assert len(result.errors) == 1
            assert "无可用新闻源" in result.errors[0]

    @pytest.mark.asyncio
    async def test_get_latest_news(self, agent):
        """测试获取最新新闻"""
        with patch.object(agent, 'collect_news') as mock_collect:
            mock_result = Mock()
            mock_result.articles = [
                NewsArticle(
                    id="latest_001",
                    title="最新新闻",
                    content="最新内容"
                )
            ]
            mock_collect.return_value = mock_result

            articles = await agent.get_latest_news(limit=5)

            assert len(articles) == 1
            assert articles[0].title == "最新新闻"

            # 验证collect_news调用参数
            mock_collect.assert_called_once()
            call_args = mock_collect.call_args[0][0]
            assert call_args.limit == 5

    @pytest.mark.asyncio
    async def test_search_news(self, agent):
        """测试搜索新闻"""
        with patch.object(agent, 'collect_news') as mock_collect:
            mock_result = Mock()
            mock_result.articles = [
                NewsArticle(
                    id="search_001",
                    title="比特币新闻",
                    content="比特币相关内容"
                )
            ]
            mock_collect.return_value = mock_result

            articles = await agent.search_news(["比特币", "加密货币"], limit=10)

            assert len(articles) == 1
            assert articles[0].title == "比特币新闻"

            # 验证collect_news调用参数
            mock_collect.assert_called_once()
            call_args = mock_collect.call_args[0][0]
            assert call_args.keywords == ["比特币", "加密货币"]
            assert call_args.limit == 10

    @pytest.mark.asyncio
    async def test_add_news_source(self, agent):
        """测试添加新闻源"""
        config = NewsSourceConfig(
            name="new_source",
            adapter_type="mock",
            base_url="https://example.com/api"
        )

        with patch.object(agent.config_manager, 'add_source', return_value=True):
            with patch.object(agent.connection_manager, 'add_source', return_value=True):
                with patch.object(agent.health_checker, 'add_source') as mock_add_health:
                    with patch.object(NewsSourceAdapterFactory, 'create_adapter') as mock_factory:
                        mock_adapter = Mock()
                        mock_adapter.initialize = AsyncMock(return_value=True)
                        mock_factory.return_value = mock_adapter

                        result = await agent.add_news_source(config)

                        assert result == True
                        mock_add_health.assert_called_once_with("new_source", mock_adapter)

    @pytest.mark.asyncio
    async def test_remove_news_source(self, agent):
        """测试移除新闻源"""
        with patch.object(agent.health_checker, 'remove_source'):
            with patch.object(agent.connection_manager, 'remove_source', return_value=True):
                with patch.object(agent.config_manager, 'remove_source', return_value=True):

                    result = await agent.remove_news_source("test_source")

                    assert result == True
                    agent.health_checker.remove_source.assert_called_once_with("test_source")

    @pytest.mark.asyncio
    async def test_get_available_sources(self, agent):
        """测试获取可用新闻源"""
        mock_config = NewsSourceConfig(
            name="available_source",
            adapter_type="mock",
            base_url="https://example.com/api",
            enabled=True
        )

        with patch.object(agent.connection_manager, 'get_available_sources', return_value=["available_source"]):
            with patch.object(agent.config_manager, 'get_all_sources', return_value={"available_source": mock_config}):

                sources = await agent.get_available_sources()

                assert len(sources) == 1
                assert sources[0].name == "available_source"
                assert sources[0].enabled == True

    @pytest.mark.asyncio
    async def test_get_statistics(self, agent):
        """测试获取统计信息"""
        agent._stats = {
            "start_time": datetime.now() - timedelta(hours=1),
            "total_requests": 100,
            "successful_requests": 80,
            "failed_requests": 20,
            "articles_collected": 500
        }
        agent._running = True

        with patch.object(agent.connection_manager, 'get_connection_stats', return_value={}):
            with patch.object(agent.error_handler, 'get_error_stats', return_value={}):
                with patch.object(agent.config_manager, 'get_config_stats', return_value={}):

                    stats = await agent.get_statistics()

                    assert "runtime_stats" in stats
                    assert "connection_stats" in stats
                    assert "error_stats" in stats
                    assert "config_stats" in stats

                    runtime_stats = stats["runtime_stats"]
                    assert runtime_stats["total_requests"] == 100
                    assert runtime_stats["successful_requests"] == 80
                    assert runtime_stats["failed_requests"] == 20
                    assert runtime_stats["articles_collected"] == 500
                    assert runtime_stats["is_running"] == True

    def test_deduplicate_articles(self, agent):
        """测试文章去重"""
        articles = [
            NewsArticle(
                id="001",
                title="比特币价格上涨",
                content="内容1"
            ),
            NewsArticle(
                id="002",
                title="BITCOIN 价格上涨",  # 标题相同（忽略大小写）
                content="内容2"
            ),
            NewsArticle(
                id="003",
                title="以太坊升级",
                content="内容3"
            ),
            NewsArticle(
                id="004",
                title="比特币价格上涨",  # 标题相同
                content="内容4"
            )
        ]

        unique_articles = agent._deduplicate_articles(articles)

        assert len(unique_articles) == 2
        titles = [article.title for article in unique_articles]
        assert "比特币价格上涨" in titles
        assert "以太坊升级" in titles

    @pytest.mark.asyncio
    async def test_retry_failed_source(self, agent):
        """测试重试失败的新闻源"""
        with patch.object(agent.error_handler, 'reset_circuit_breaker'):
            with patch.object(agent.connection_manager, 'retry_connection', return_value=True):

                result = await agent.retry_failed_source("failed_source")

                assert result == True
                agent.error_handler.reset_circuit_breaker.assert_called_once_with("failed_source")
                agent.connection_manager.retry_connection.assert_called_once_with("failed_source")

    @pytest.mark.asyncio
    async def test_get_error_history(self, agent):
        """测试获取错误历史"""
        mock_error = Mock()
        mock_error.context.source_name = "test_source"
        mock_error.context.operation = "fetch_news"
        mock_error.error_type.value = "connection_error"
        mock_error.severity.value = "high"
        mock_error.message = "连接失败"
        mock_error.context.timestamp = datetime.now()
        mock_error.retry_count = 2

        with patch.object(agent.error_handler, 'get_error_history', return_value=[mock_error]):

            error_history = await agent.get_error_history(limit=10)

            assert len(error_history) == 1
            error = error_history[0]
            assert error["source_name"] == "test_source"
            assert error["operation"] == "fetch_news"
            assert error["error_type"] == "connection_error"
            assert error["severity"] == "high"
            assert error["message"] == "连接失败"
            assert error["retry_count"] == 2


if __name__ == "__main__":
    pytest.main([__file__])