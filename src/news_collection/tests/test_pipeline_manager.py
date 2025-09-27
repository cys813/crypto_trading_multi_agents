"""
Tests for pipeline manager
"""

import unittest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch

from ..processing.pipeline_manager import PipelineManager, PipelineResult
from ..processing.models import ProcessingConfig
from ..models.base import NewsArticle, NewsCategory


class TestPipelineManager(unittest.TestCase):
    """测试管道管理器"""

    def setUp(self):
        """测试设置"""
        self.config = ProcessingConfig()
        self.pipeline = PipelineManager(self.config)

        # 测试文章
        self.test_articles = [
            NewsArticle(
                id="test_001",
                title="Bitcoin Price Analysis",
                content="Bitcoin price analysis showing bullish trends.",
                published_at=datetime.now(),
                source="coindesk.com",
                category=NewsCategory.GENERAL
            ),
            NewsArticle(
                id="test_002",
                title="Ethereum Upgrade News",
                content="Ethereum network upgrade scheduled for next month.",
                published_at=datetime.now(),
                source="cointelegraph.com",
                category=NewsCategory.TECHNOLOGY
            ),
            NewsArticle(
                id="test_003",
                title="Market Regulation Update",
                content="New cryptocurrency regulations proposed by financial authorities.",
                published_at=datetime.now(),
                source="reuters.com",
                category=NewsCategory.REGULATION
            )
        ]

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.pipeline)
        self.assertIsInstance(self.pipeline.config, ProcessingConfig)
        self.assertFalse(self.pipeline.is_running)
        self.assertEqual(len(self.pipeline.processed_articles), 0)
        self.assertIsNotNone(self.pipeline.preprocessor)
        self.assertIsNotNone(self.pipeline.deduplication_engine)
        self.assertIsNotNone(self.pipeline.noise_filter)
        self.assertIsNotNone(self.pipeline.content_structurer)
        self.assertIsNotNone(self.pipeline.quality_scorer)

    def test_process_empty_articles(self):
        """测试处理空文章列表"""
        result = asyncio.run(self.pipeline.process_articles([]))

        self.assertIsInstance(result, PipelineResult)
        self.assertEqual(len(result.articles), 0)
        self.assertEqual(len(result.processing_results), 0)
        self.assertEqual(result.execution_time, 0.0)
        self.assertEqual(len(result.errors), 0)

    def test_process_single_article(self):
        """测试处理单篇文章"""
        result = asyncio.run(self.pipeline.process_articles([self.test_articles[0]]))

        self.assertIsInstance(result, PipelineResult)
        self.assertEqual(len(result.articles), 1)
        self.assertEqual(len(result.processing_results), 1)
        self.assertGreater(result.execution_time, 0)

        # 检查处理结果
        processing_result = result.processing_results[0]
        self.assertIn(processing_result.status.value, ['completed', 'failed', 'skipped'])
        self.assertIsInstance(processing_result.processing_time, float)
        self.assertGreater(processing_result.processing_time, 0)

    def test_process_multiple_articles(self):
        """测试处理多篇文章"""
        result = asyncio.run(self.pipeline.process_articles(self.test_articles))

        self.assertIsInstance(result, PipelineResult)
        self.assertEqual(len(result.articles), len(self.test_articles))
        self.assertEqual(len(result.processing_results), len(self.test_articles))

        # 检查统计信息
        self.assertGreater(result.stats.total_articles, 0)
        self.assertGreater(result.stats.total_processing_time, 0)

    def test_parallel_processing(self):
        """测试并行处理"""
        # 启用并行处理
        self.config.enable_parallel_processing = True
        self.config.max_batch_size = 10

        result = asyncio.run(self.pipeline.process_articles(self.test_articles))

        self.assertIsInstance(result, PipelineResult)
        self.assertEqual(len(result.articles), len(self.test_articles))

    def test_sequential_processing(self):
        """测试串行处理"""
        # 禁用并行处理
        self.config.enable_parallel_processing = False

        result = asyncio.run(self.pipeline.process_articles(self.test_articles))

        self.assertIsInstance(result, PipelineResult)
        self.assertEqual(len(result.articles), len(self.test_articles))

    def test_pipeline_stages_execution(self):
        """测试管道阶段执行"""
        # 启用所有阶段
        self.config.enable_preprocessing = True
        self.config.enable_deduplication = True
        self.config.enable_noise_filtering = True
        self.config.enable_structuring = True
        self.config.enable_quality_scoring = True

        result = asyncio.run(self.pipeline.process_articles([self.test_articles[0]]))

        processing_result = result.processing_results[0]

        # 检查阶段是否被执行
        if processing_result.status.value == 'completed':
            self.assertGreater(len(processing_result.stages_completed), 0)

    def test_error_handling(self):
        """测试错误处理"""
        # 创建会导致错误的文章
        invalid_article = NewsArticle(
            id="invalid",
            title="",  # 空标题可能导致错误
            content="",  # 空内容
            published_at=None,
            source="",
            category=NewsCategory.GENERAL
        )

        result = asyncio.run(self.pipeline.process_articles([invalid_article]))

        # 应该能够处理错误而不崩溃
        self.assertIsInstance(result, PipelineResult)
        self.assertEqual(len(result.processing_results), 1)

        processing_result = result.processing_results[0]
        if processing_result.status.value == 'failed':
            self.assertGreater(len(processing_result.errors), 0)

    def test_pipeline_stats(self):
        """测试管道统计"""
        result = asyncio.run(self.pipeline.process_articles(self.test_articles))

        stats = result.stats
        self.assertGreater(stats.total_articles, 0)
        self.assertGreater(stats.total_processing_time, 0)
        self.assertGreaterEqual(stats.successful_articles, 0)
        self.assertGreaterEqual(stats.failed_articles, 0)
        self.assertGreaterEqual(stats.skipped_articles, 0)

    def test_get_pipeline_status(self):
        """测试获取管道状态"""
        status = self.pipeline.get_pipeline_status()

        self.assertIsInstance(status, dict)
        self.assertIn('is_running', status)
        self.assertIn('total_processed', status)
        self.assertIn('stats', status)
        self.assertIn('config', status)

    def test_get_component_stats(self):
        """测试获取组件统计"""
        component_stats = self.pipeline.get_component_stats()

        self.assertIsInstance(component_stats, dict)
        self.assertIn('preprocessor', component_stats)
        self.assertIn('deduplication_engine', component_stats)
        self.assertIn('noise_filter', component_stats)
        self.assertIn('content_structurer', component_stats)
        self.assertIn('quality_scorer', component_stats)

    def test_clear_processed_articles(self):
        """测试清空已处理文章"""
        # 先处理一些文章
        asyncio.run(self.pipeline.process_articles([self.test_articles[0]]))
        self.assertGreater(len(self.pipeline.processed_articles), 0)

        # 清空
        self.pipeline.clear_processed_articles()
        self.assertEqual(len(self.pipeline.processed_articles), 0)

    def test_update_config(self):
        """测试更新配置"""
        new_config = ProcessingConfig(quality_threshold=0.8)
        self.pipeline.update_config(new_config)

        self.assertEqual(self.pipeline.config.quality_threshold, 0.8)

    def test_get_performance_metrics(self):
        """测试获取性能指标"""
        # 先处理一些文章
        asyncio.run(self.pipeline.process_articles(self.test_articles))

        metrics = self.pipeline.get_performance_metrics()

        self.assertIsInstance(metrics, dict)
        self.assertIn('throughput', metrics)
        self.assertIn('success_rate', metrics)
        self.assertIn('average_processing_time', metrics)
        self.assertIn('stage_efficiency', metrics)
        self.assertIn('quality_distribution', metrics)

    def test_health_check(self):
        """测试健康检查"""
        health = asyncio.run(self.pipeline.health_check())

        self.assertIsInstance(health, dict)
        self.assertIn('status', health)
        self.assertIn('components', health)
        self.assertIn('performance', health)
        self.assertIn('last_updated', health)

    def test_shutdown(self):
        """测试关闭管道"""
        # 模拟管道运行
        self.pipeline.is_running = True

        # 关闭
        self.pipeline.shutdown()

        self.assertFalse(self.pipeline.is_running)
        # 验证线程池被关闭（这里只是测试方法调用不报错）

    def test_duplicate_detection_integration(self):
        """测试重复检测集成"""
        # 处理一篇文章
        result1 = asyncio.run(self.pipeline.process_articles([self.test_articles[0]]))

        # 处理相同内容的另一篇文章
        duplicate_article = NewsArticle(
            id="duplicate_001",
            title=self.test_articles[0].title,
            content=self.test_articles[0].content,
            published_at=self.test_articles[0].published_at,
            source=self.test_articles[0].source,
            category=self.test_articles[0].category
        )

        result2 = asyncio.run(self.pipeline.process_articles([duplicate_article]))

        # 检查是否检测为重复
        processing_result = result2.processing_results[0]
        # 如果被检测为重复，状态应该是skipped
        if processing_result.is_duplicate:
            self.assertEqual(processing_result.status.value, 'skipped')

    def test_quality_threshold_filtering(self):
        """测试质量阈值过滤"""
        # 设置高质量阈值
        self.config.quality_threshold = 0.9

        # 处理文章
        result = asyncio.run(self.pipeline.process_articles([self.test_articles[0]]))

        processing_result = result.processing_results[0]

        # 检查质量分数是否被计算
        self.assertIsNotNone(processing_result.quality_score)

    @patch('src.news_collection.processing.pipeline_manager.PipelineManager._process_single_article')
    def test_batch_processing_error_handling(self, mock_process):
        """测试批处理错误处理"""
        # 模拟一些处理失败
        mock_process.side_effect = [
            (self.test_articles[0], MagicMock(status_value='completed')),
            Exception("Processing failed"),
            (self.test_articles[2], MagicMock(status_value='completed'))
        ]

        result = asyncio.run(self.pipeline.process_articles(self.test_articles))

        # 应该有错误信息
        self.assertGreater(len(result.errors), 0)
        self.assertEqual(len(result.processing_results), 3)

    def test_pipeline_timeout_handling(self):
        """测试管道超时处理"""
        # 设置短超时
        self.config.processing_timeout = 0.1

        # 创建需要长时间处理的文章（大内容）
        large_content_article = NewsArticle(
            id="large_content",
            title="Large Content Article",
            content="x" * 10000,  # 大内容
            published_at=datetime.now(),
            source="test.com",
            category=NewsCategory.GENERAL
        )

        # 应该能够处理超时而不崩溃
        result = asyncio.run(self.pipeline.process_articles([large_content_article]))

        self.assertIsInstance(result, PipelineResult)
        self.assertEqual(len(result.processing_results), 1)


if __name__ == '__main__':
    unittest.main()