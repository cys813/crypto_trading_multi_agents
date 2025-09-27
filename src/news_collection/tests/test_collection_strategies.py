"""
Unit tests for collection strategies
"""

import unittest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from ..collection.strategies import (
    IncrementalCollectionStrategy,
    FullCollectionStrategy,
    PriorityBasedCollectionStrategy,
    CollectionStrategyFactory,
    CollectionResult,
    CollectionStrategy
)
from ..models.base import (
    NewsArticle,
    NewsQuery,
    NewsQueryResult,
    NewsSourceConfig,
    NewsCategory
)
from ..core.adapter import NewsSourceAdapter


class TestCollectionStrategies(unittest.TestCase):
    """测试收集策略"""

    def setUp(self):
        """设置测试环境"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # 创建模拟适配器
        self.mock_adapter = Mock(spec=NewsSourceAdapter)
        self.mock_adapter.source_name = "test_source"
        self.mock_adapter.is_connected.return_value = True
        self.mock_adapter.config = NewsSourceConfig(
            name="test_source",
            adapter_type="test",
            base_url="http://test.com",
            priority=5
        )

        # 创建测试文章
        self.test_articles = [
            NewsArticle(
                id="1",
                title="Bitcoin price reaches new all-time high",
                content="Bitcoin has reached a new all-time high of $50,000...",
                category=NewsCategory.MARKET_ANALYSIS,
                published_at=datetime.now() - timedelta(hours=1)
            ),
            NewsArticle(
                id="2",
                title="Ethereum upgrade announced",
                content="Ethereum developers have announced a major upgrade...",
                category=NewsCategory.TECHNOLOGY,
                published_at=datetime.now() - timedelta(hours=2)
            )
        ]

    def tearDown(self):
        """清理测试环境"""
        self.loop.close()

    def test_incremental_collection_strategy_initialization(self):
        """测试增量收集策略初始化"""
        config = {
            'window_days': 15,
            'max_articles_per_source': 100
        }
        strategy = IncrementalCollectionStrategy(config)

        self.assertEqual(strategy.window_days, 15)
        self.assertEqual(strategy.max_articles_per_source, 100)

    def test_full_collection_strategy_initialization(self):
        """测试全量收集策略初始化"""
        config = {'max_articles_per_source': 500}
        strategy = FullCollectionStrategy(config)

        self.assertEqual(strategy.max_articles_per_source, 500)

    def test_priority_based_collection_strategy_initialization(self):
        """测试基于优先级的收集策略初始化"""
        config = {
            'priority_threshold': 5,
            'max_articles_per_source': 200
        }
        strategy = PriorityBasedCollectionStrategy(config)

        self.assertEqual(strategy.priority_threshold, 5)
        self.assertEqual(strategy.max_articles_per_source, 200)

    def test_collection_strategy_factory(self):
        """测试收集策略工厂"""
        # 测试创建增量策略
        incremental_config = {'window_days': 10}
        incremental_strategy = CollectionStrategyFactory.create_strategy(
            "incremental", incremental_config
        )
        self.assertIsInstance(incremental_strategy, IncrementalCollectionStrategy)

        # 测试创建全量策略
        full_config = {'max_articles_per_source': 300}
        full_strategy = CollectionStrategyFactory.create_strategy(
            "full", full_config
        )
        self.assertIsInstance(full_strategy, FullCollectionStrategy)

        # 测试创建优先级策略
        priority_config = {'priority_threshold': 7}
        priority_strategy = CollectionStrategyFactory.create_strategy(
            "priority_based", priority_config
        )
        self.assertIsInstance(priority_strategy, PriorityBasedCollectionStrategy)

        # 测试不支持策略类型
        with self.assertRaises(ValueError):
            CollectionStrategyFactory.create_strategy("unsupported", {})

    def test_collection_strategy_factory_available_strategies(self):
        """测试获取可用策略列表"""
        strategies = CollectionStrategyFactory.get_available_strategies()
        expected_strategies = ["incremental", "full", "priority_based"]

        for strategy in expected_strategies:
            self.assertIn(strategy, strategies)

    def test_collection_strategy_factory_register_strategy(self):
        """测试注册新策略"""
        class CustomStrategy(CollectionStrategy):
            async def collect(self, adapters, query=None):
                return CollectionResult([], [], 0, 0, [], self.strategy_name)

        # 注册自定义策略
        CollectionStrategyFactory.register_strategy("custom", CustomStrategy)

        # 测试创建自定义策略
        custom_strategy = CollectionStrategyFactory.create_strategy("custom", {})
        self.assertIsInstance(custom_strategy, CustomStrategy)

        # 验证策略在可用列表中
        strategies = CollectionStrategyFactory.get_available_strategies()
        self.assertIn("custom", strategies)


class TestIncrementalCollectionStrategyAsync(unittest.TestCase):
    """异步测试增量收集策略"""

    def setUp(self):
        """设置测试环境"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # 创建模拟适配器
        self.mock_adapter = Mock(spec=NewsSourceAdapter)
        self.mock_adapter.source_name = "test_source"
        self.mock_adapter.is_connected.return_value = True
        self.mock_adapter.config = NewsSourceConfig(
            name="test_source",
            adapter_type="test",
            base_url="http://test.com",
            priority=5
        )

        # 创建测试文章
        self.test_articles = [
            NewsArticle(
                id="1",
                title="Bitcoin price surge",
                content="Bitcoin prices are surging...",
                published_at=datetime.now() - timedelta(hours=1)
            ),
            NewsArticle(
                id="2",
                title="Ethereum news",
                content="Ethereum development update...",
                published_at=datetime.now() - timedelta(hours=2)
            )
        ]

        # 模拟fetch_news方法
        self.mock_adapter.fetch_news = AsyncMock(return_value=NewsQueryResult(
            articles=self.test_articles,
            total_count=len(self.test_articles),
            has_more=False,
            query=NewsQuery(),
            execution_time=100,
            sources_used=["test_source"],
            errors=[]
        ))

    def tearDown(self):
        """清理测试环境"""
        self.loop.close()

    def test_incremental_collection_with_connected_adapter(self):
        """测试已连接适配器的增量收集"""
        config = {'window_days': 15, 'max_articles_per_source': 100}
        strategy = IncrementalCollectionStrategy(config)
        adapters = {"test_source": self.mock_adapter}

        async def run_test():
            result = await strategy.collect(adapters)

            self.assertEqual(len(result.articles), 2)
            self.assertEqual(result.total_count, 2)
            self.assertEqual(result.sources_used, ["test_source"])
            self.assertEqual(len(result.errors), 0)

            # 验证fetch_news被调用
            self.mock_adapter.fetch_news.assert_called_once()

        self.loop.run_until_complete(run_test())

    def test_incremental_collection_with_disconnected_adapter(self):
        """测试断开连接适配器的增量收集"""
        self.mock_adapter.is_connected.return_value = False

        config = {'window_days': 15, 'max_articles_per_source': 100}
        strategy = IncrementalCollectionStrategy(config)
        adapters = {"test_source": self.mock_adapter}

        async def run_test():
            result = await strategy.collect(adapters)

            self.assertEqual(len(result.articles), 0)
            self.assertEqual(result.total_count, 0)
            self.assertEqual(len(result.sources_used), 0)
            self.assertEqual(len(result.errors), 1)
            self.assertIn("未连接", result.errors[0])

        self.loop.run_until_complete(run_test())

    def test_incremental_collection_with_fetch_error(self):
        """测试获取错误时的增量收集"""
        self.mock_adapter.fetch_news.side_effect = Exception("Network error")

        config = {'window_days': 15, 'max_articles_per_source': 100}
        strategy = IncrementalCollectionStrategy(config)
        adapters = {"test_source": self.mock_adapter}

        async def run_test():
            result = await strategy.collect(adapters)

            self.assertEqual(len(result.articles), 0)
            self.assertEqual(result.total_count, 0)
            self.assertEqual(len(result.sources_used), 0)
            self.assertEqual(len(result.errors), 1)
            self.assertIn("收集失败", result.errors[0])

        self.loop.run_until_complete(run_test())


class TestFullCollectionStrategyAsync(unittest.TestCase):
    """异步测试全量收集策略"""

    def setUp(self):
        """设置测试环境"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # 创建模拟适配器
        self.mock_adapter = Mock(spec=NewsSourceAdapter)
        self.mock_adapter.source_name = "test_source"
        self.mock_adapter.is_connected.return_value = True
        self.mock_adapter.config = NewsSourceConfig(
            name="test_source",
            adapter_type="test",
            base_url="http://test.com",
            priority=5
        )

        # 创建测试文章
        self.test_articles = [
            NewsArticle(
                id="1",
                title="Article 1",
                content="Content 1"
            ),
            NewsArticle(
                id="2",
                title="Article 2",
                content="Content 2"
            )
        ]

        # 模拟get_latest_news方法
        self.mock_adapter.get_latest_news = AsyncMock(return_value=self.test_articles)

    def tearDown(self):
        """清理测试环境"""
        self.loop.close()

    def test_full_collection_successful(self):
        """测试成功的全量收集"""
        config = {'max_articles_per_source': 500}
        strategy = FullCollectionStrategy(config)
        adapters = {"test_source": self.mock_adapter}

        async def run_test():
            result = await strategy.collect(adapters)

            self.assertEqual(len(result.articles), 2)
            self.assertEqual(result.total_count, 2)
            self.assertEqual(result.sources_used, ["test_source"])
            self.assertEqual(len(result.errors), 0)

            # 验证get_latest_news被调用
            self.mock_adapter.get_latest_news.assert_called_once_with(500)

        self.loop.run_until_complete(run_test())

    def test_full_collection_with_error(self):
        """测试错误情况的全量收集"""
        self.mock_adapter.get_latest_news.side_effect = Exception("API error")

        config = {'max_articles_per_source': 500}
        strategy = FullCollectionStrategy(config)
        adapters = {"test_source": self.mock_adapter}

        async def run_test():
            result = await strategy.collect(adapters)

            self.assertEqual(len(result.articles), 0)
            self.assertEqual(result.total_count, 0)
            self.assertEqual(len(result.sources_used), 0)
            self.assertEqual(len(result.errors), 1)
            self.assertIn("异常", result.errors[0])

        self.loop.run_until_complete(run_test())


class TestPriorityBasedCollectionStrategyAsync(unittest.TestCase):
    """异步测试基于优先级的收集策略"""

    def setUp(self):
        """设置测试环境"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # 创建高优先级适配器
        self.high_priority_adapter = Mock(spec=NewsSourceAdapter)
        self.high_priority_adapter.source_name = "high_priority_source"
        self.high_priority_adapter.is_connected.return_value = True
        self.high_priority_adapter.config = NewsSourceConfig(
            name="high_priority_source",
            adapter_type="test",
            base_url="http://test.com",
            priority=8
        )

        # 创建低优先级适配器
        self.low_priority_adapter = Mock(spec=NewsSourceAdapter)
        self.low_priority_adapter.source_name = "low_priority_source"
        self.low_priority_adapter.is_connected.return_value = True
        self.low_priority_adapter.config = NewsSourceConfig(
            name="low_priority_source",
            adapter_type="test",
            base_url="http://test.com",
            priority=3
        )

        # 创建测试文章
        self.test_articles = [NewsArticle(id="1", title="Test", content="Test")]

        # 模拟get_latest_news方法
        self.high_priority_adapter.get_latest_news = AsyncMock(return_value=self.test_articles)
        self.low_priority_adapter.get_latest_news = AsyncMock(return_value=self.test_articles)

    def tearDown(self):
        """清理测试环境"""
        self.loop.close()

    def test_priority_based_collection_filters_by_priority(self):
        """测试基于优先级的过滤"""
        config = {'priority_threshold': 5, 'max_articles_per_source': 200}
        strategy = PriorityBasedCollectionStrategy(config)
        adapters = {
            "high_priority_source": self.high_priority_adapter,
            "low_priority_source": self.low_priority_adapter
        }

        async def run_test():
            result = await strategy.collect(adapters)

            # 只应该收集高优先级源
            self.assertEqual(len(result.sources_used), 1)
            self.assertEqual(result.sources_used[0], "high_priority_source")
            self.assertEqual(len(result.articles), 1)

            # 验证只有高优先级适配器被调用
            self.high_priority_adapter.get_latest_news.assert_called_once()
            self.low_priority_adapter.get_latest_news.assert_not_called()

        self.loop.run_until_complete(run_test())

    def test_priority_based_collection_no_high_priority_sources(self):
        """测试没有高优先级源的情况"""
        config = {'priority_threshold': 10, 'max_articles_per_source': 200}
        strategy = PriorityBasedCollectionStrategy(config)
        adapters = {
            "high_priority_source": self.high_priority_adapter,
            "low_priority_source": self.low_priority_adapter
        }

        async def run_test():
            result = await strategy.collect(adapters)

            # 不应该收集任何源
            self.assertEqual(len(result.sources_used), 0)
            self.assertEqual(len(result.articles), 0)
            self.assertEqual(len(result.errors), 1)
            self.assertIn("没有高优先级的可用源", result.errors[0])

        self.loop.run_until_complete(run_test())


if __name__ == '__main__':
    unittest.main()