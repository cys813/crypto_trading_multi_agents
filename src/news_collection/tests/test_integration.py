"""
Integration tests for the entire processing pipeline
"""

import unittest
import asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock

from ..processing.pipeline_manager import PipelineManager
from ..processing.models import ProcessingConfig
from ..models.base import NewsArticle, NewsCategory


class TestProcessingPipelineIntegration(unittest.TestCase):
    """测试处理管道集成"""

    def setUp(self):
        """测试设置"""
        self.config = ProcessingConfig()
        self.pipeline = PipelineManager(self.config)

        # 创建测试文章数据
        self.test_articles = [
            # 高质量文章
            NewsArticle(
                id="high_quality_001",
                title="Bitcoin Reaches All-Time High Amid Institutional Adoption",
                content="""
                Bitcoin, the world's largest cryptocurrency, has reached a new all-time high of $65,000
                as institutional investors continue to adopt digital assets. Major companies including
                Tesla and MicroStrategy have added Bitcoin to their balance sheets, while traditional
                financial institutions are launching cryptocurrency investment products.

                The surge comes as regulatory clarity improves and mainstream acceptance grows.
                Analysts predict further growth as more institutions enter the market.
                """,
                summary="Bitcoin reaches new all-time high driven by institutional adoption.",
                author="John Smith",
                published_at=datetime.now(),
                source="coindesk.com",
                url="https://coindesk.com/bitcoin-ath",
                category=NewsCategory.GENERAL,
                tags=["bitcoin", "institutional", "adoption"]
            ),
            # 包含噪声的文章
            NewsArticle(
                id="noisy_001",
                title="Crypto News Update <script>alert('ads')</script>",
                content="""
                <p>Cryptocurrency markets show mixed signals today.</p>
                <div class="ad">Click here for special offers!!!</div>
                Bitcoin trading volume increased while Ethereum remained stable.
                免责声明：投资有风险，入市需谨慎。本文仅供参考，不构成投资建议。
                Visit https://scam-site.com for more info!!! AAAABBBBCCCC repeated characters.
                """,
                published_at=datetime.now(),
                source="unknown-source.com",
                category=NewsCategory.GENERAL
            ),
            # 重复文章
            NewsArticle(
                id="duplicate_001",
                title="Bitcoin Reaches All-Time High Amid Institutional Adoption",
                content="""
                Bitcoin, the world's largest cryptocurrency, has reached a new all-time high of $65,000
                as institutional investors continue to adopt digital assets. Major companies including
                Tesla and MicroStrategy have added Bitcoin to their balance sheets, while traditional
                financial institutions are launching cryptocurrency investment products.
                """,
                published_at=datetime.now(),
                source="bloomberg.com",
                category=NewsCategory.GENERAL
            ),
            # 低质量文章
            NewsArticle(
                id="low_quality_001",
                title="Short",
                content="Too short content",
                published_at=datetime.now(),
                source="low-quality-source.com",
                category=NewsCategory.GENERAL
            )
        ]

    def test_full_pipeline_integration(self):
        """测试完整管道集成"""
        # 启用所有处理阶段
        self.config.enable_preprocessing = True
        self.config.enable_deduplication = True
        self.config.enable_noise_filtering = True
        self.config.enable_structuring = True
        self.config.enable_quality_scoring = True

        # 启用并行处理
        self.config.enable_parallel_processing = True
        self.config.max_batch_size = 10

        result = asyncio.run(self.pipeline.process_articles(self.test_articles))

        # 验证基本结果
        self.assertIsInstance(result, PipelineManager)
        self.assertEqual(len(result.articles), len(self.test_articles))
        self.assertEqual(len(result.processing_results), len(self.test_articles))

        # 验证统计信息
        stats = result.stats
        self.assertGreater(stats.total_articles, 0)
        self.assertGreater(stats.total_processing_time, 0)
        self.assertGreaterEqual(stats.successful_articles, 0)

        # 验证处理结果
        for processing_result in result.processing_results:
            self.assertIn(processing_result.status.value, ['completed', 'failed', 'skipped'])
            self.assertIsInstance(processing_result.processing_time, float)
            self.assertGreater(processing_result.processing_time, 0)

            # 检查元数据
            self.assertIsInstance(processing_result.metadata, dict)

            # 检查错误列表
            self.assertIsInstance(processing_result.errors, list)

    def test_preprocessing_integration(self):
        """测试预处理集成"""
        # 只启用预处理
        self.config.enable_preprocessing = True
        self.config.enable_deduplication = False
        self.config.enable_noise_filtering = False
        self.config.enable_structuring = False
        self.config.enable_quality_scoring = False

        result = asyncio.run(self.pipeline.process_articles([self.test_articles[1]]))  # 噪声文章

        processing_result = result.processing_results[0]

        # 验证预处理被执行
        self.assertIn('preprocessing', [stage.value for stage in processing_result.stages_completed])

        # 验证预处理统计
        self.assertIn('preprocessing_stats', processing_result.metadata)
        preprocessing_stats = processing_result.metadata['preprocessing_stats']
        self.assertIn('original_length', preprocessing_stats)
        self.assertIn('processed_length', preprocessing_stats)

    def test_deduplication_integration(self):
        """测试去重集成"""
        # 只启用去重
        self.config.enable_preprocessing = False
        self.config.enable_deduplication = True
        self.config.enable_noise_filtering = False
        self.config.enable_structuring = False
        self.config.enable_quality_scoring = False

        # 处理包含重复的文章
        result = asyncio.run(self.pipeline.process_articles([
            self.test_articles[0],  # 原始文章
            self.test_articles[2]   # 重复文章
        ]))

        # 检查是否检测到重复
        duplicate_result = None
        for processing_result in result.processing_results:
            if processing_result.is_duplicate:
                duplicate_result = processing_result
                break

        self.assertIsNotNone(duplicate_result, "应该检测到重复文章")
        self.assertTrue(duplicate_result.is_duplicate)
        self.assertEqual(duplicate_result.status.value, 'skipped')

    def test_noise_filtering_integration(self):
        """测试噪声过滤集成"""
        # 只启用噪声过滤
        self.config.enable_preprocessing = False
        self.config.enable_deduplication = False
        self.config.enable_noise_filtering = True
        self.config.enable_structuring = False
        self.config.enable_quality_scoring = False

        result = asyncio.run(self.pipeline.process_articles([self.test_articles[1]]))  # 噪声文章

        processing_result = result.processing_results[0]

        # 验证噪声过滤被执行
        self.assertIn('noise_filtering', [stage.value for stage in processing_result.stages_completed])

        # 验证噪声过滤统计
        self.assertIn('noise_filtering_stats', processing_result.metadata)
        noise_stats = processing_result.metadata['noise_filtering_stats']
        self.assertIn('original_length', noise_stats)
        self.assertIn('filtered_length', noise_stats)
        self.assertIn('removed_ads', noise_stats)

    def test_quality_scoring_integration(self):
        """测试质量评分集成"""
        # 只启用质量评分
        self.config.enable_preprocessing = False
        self.config.enable_deduplication = False
        self.config.enable_noise_filtering = False
        self.config.enable_structuring = False
        self.config.enable_quality_scoring = True

        result = asyncio.run(self.pipeline.process_articles([self.test_articles[0]]))  # 高质量文章

        processing_result = result.processing_results[0]

        # 验证质量评分被执行
        self.assertIn('quality_scoring', [stage.value for stage in processing_result.stages_completed])

        # 验证质量分数
        self.assertIsNotNone(processing_result.quality_score)
        self.assertIsInstance(processing_result.quality_score, float)
        self.assertGreaterEqual(processing_result.quality_score, 0.0)
        self.assertLessEqual(processing_result.quality_score, 1.0)

        # 验证质量评分元数据
        self.assertIn('quality_score', processing_result.metadata)
        quality_metadata = processing_result.metadata['quality_score']
        self.assertIn('overall_score', quality_metadata)
        self.assertIn('grade', quality_metadata)
        self.assertIn('confidence', quality_metadata)
        self.assertIn('recommendation', quality_metadata)

    def test_content_structuring_integration(self):
        """测试内容结构化集成"""
        # 只启用内容结构化
        self.config.enable_preprocessing = False
        self.config.enable_deduplication = False
        self.config.enable_noise_filtering = False
        self.config.enable_structuring = True
        self.config.enable_quality_scoring = False

        result = asyncio.run(self.pipeline.process_articles([self.test_articles[0]]))

        processing_result = result.processing_results[0]

        # 验证结构化被执行
        self.assertIn('structuring', [stage.value for stage in processing_result.stages_completed])

        # 验证结构化统计
        self.assertIn('structuring_stats', processing_result.metadata)
        structuring_stats = processing_result.metadata['structuring_stats']
        self.assertIn('sections_extracted', structuring_stats)
        self.assertIn('key_points_extracted', structuring_stats)
        self.assertIn('entities_extracted', structuring_stats)

    def test_performance_benchmark(self):
        """测试性能基准"""
        # 创建大量测试文章
        large_article_set = []
        for i in range(100):
            article = NewsArticle(
                id=f"benchmark_{i:03d}",
                title=f"Test Article {i}",
                content=f"This is test article {i} with sufficient content for processing. "
                       f"Bitcoin price analysis and market trends discussion. "
                       f"Institutional adoption and regulatory developments.",
                published_at=datetime.now(),
                source="test.com",
                category=NewsCategory.GENERAL
            )
            large_article_set.append(article)

        # 运行性能测试
        start_time = datetime.now()
        result = asyncio.run(self.pipeline.process_articles(large_article_set))
        end_time = datetime.now()

        # 验证性能
        processing_time = (end_time - start_time).total_seconds()
        self.assertLess(processing_time, 60.0)  # 应该在60秒内完成

        # 验证吞吐量
        throughput = len(large_article_set) / processing_time
        self.assertGreater(throughput, 1.0)  # 每秒至少处理1篇文章

        # 验证成功率
        success_rate = result.stats.successful_articles / len(large_article_set)
        self.assertGreater(success_rate, 0.8)  # 成功率应该超过80%

    def test_error_recovery(self):
        """测试错误恢复"""
        # 创建一些会导致错误的文章
        problematic_articles = [
            NewsArticle(
                id="error_001",
                title="",  # 空标题
                content="",  # 空内容
                published_at=None,
                source="",
                category=NewsCategory.GENERAL
            ),
            self.test_articles[0],  # 正常文章
            NewsArticle(
                id="error_002",
                title="Valid Title",
                content="x" * 50000,  # 超大内容
                published_at=datetime.now(),
                source="test.com",
                category=NewsCategory.GENERAL
            )
        ]

        # 应该能处理错误而不崩溃
        result = asyncio.run(self.pipeline.process_articles(problematic_articles))

        self.assertEqual(len(result.articles), len(problematic_articles))
        self.assertEqual(len(result.processing_results), len(problematic_articles))

        # 检查是否有错误被记录
        has_errors = any(len(r.errors) > 0 for r in result.processing_results)
        self.assertTrue(has_errors)

        # 检查是否有成功处理的文章
        has_success = any(r.status.value == 'completed' for r in result.processing_results)
        self.assertTrue(has_success)

    def test_memory_efficiency(self):
        """测试内存效率"""
        # 创建大量文章来测试内存使用
        memory_test_articles = []
        for i in range(50):
            article = NewsArticle(
                id=f"memory_test_{i:03d}",
                title=f"Memory Test Article {i}",
                content="x" * 2000,  # 中等内容大小
                published_at=datetime.now(),
                source="test.com",
                category=NewsCategory.GENERAL
            )
            memory_test_articles.append(article)

        # 处理文章
        result = asyncio.run(self.pipeline.process_articles(memory_test_articles))

        # 验证处理完成
        self.assertEqual(len(result.articles), len(memory_test_articles))

        # 清理缓存
        self.pipeline.clear_processed_articles()

        # 验证缓存被清空
        self.assertEqual(len(self.pipeline.processed_articles), 0)

    def test_config_flexibility(self):
        """测试配置灵活性"""
        # 测试不同配置组合
        configs = [
            ProcessingConfig(enable_preprocessing=True, enable_deduplication=False),
            ProcessingConfig(enable_preprocessing=False, enable_deduplication=True),
            ProcessingConfig(enable_noise_filtering=True, enable_quality_scoring=False),
            ProcessingConfig(enable_structuring=True, enable_preprocessing=False),
            ProcessingConfig(enable_quality_scoring=True, enable_noise_filtering=False)
        ]

        for config in configs:
            self.pipeline.update_config(config)
            result = asyncio.run(self.pipeline.process_articles([self.test_articles[0]]))

            # 验证处理完成
            self.assertEqual(len(result.articles), 1)
            self.assertEqual(len(result.processing_results), 1)

    def test_health_monitoring(self):
        """测试健康监控"""
        # 处理一些文章
        asyncio.run(self.pipeline.process_articles(self.test_articles))

        # 检查健康状态
        health = asyncio.run(self.pipeline.health_check())

        self.assertEqual(health['status'], 'healthy')
        self.assertIn('components', health)
        self.assertIn('performance', health)

        # 检查组件状态
        for component_status in health['components'].values():
            self.assertEqual(component_status, 'healthy')

        # 检查性能指标
        performance = health['performance']
        self.assertIn('throughput', performance)
        self.assertIn('success_rate', performance)
        self.assertIn('average_processing_time', performance)


if __name__ == '__main__':
    unittest.main()