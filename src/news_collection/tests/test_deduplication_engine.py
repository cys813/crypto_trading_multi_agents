"""
Tests for deduplication engine
"""

import unittest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from ..processing.deduplication_engine import DeduplicationEngine, FingerprintCache
from ..processing.models import ProcessingConfig
from ..models.base import NewsArticle, NewsCategory


class TestDeduplicationEngine(unittest.TestCase):
    """测试去重引擎"""

    def setUp(self):
        """测试设置"""
        self.config = ProcessingConfig()
        self.engine = DeduplicationEngine(self.config)

        # 测试文章
        self.article1 = NewsArticle(
            id="article_001",
            title="Bitcoin Price Surge",
            content="Bitcoin price surged to new heights as institutional adoption increases.",
            published_at=datetime.now(),
            source="coindesk.com",
            category=NewsCategory.GENERAL
        )

        self.article2 = NewsArticle(
            id="article_002",
            title="Bitcoin Rises to New High",
            content="Bitcoin price reached new levels with growing institutional interest.",
            published_at=datetime.now(),
            source="cointelegraph.com",
            category=NewsCategory.GENERAL
        )

        self.article3 = NewsArticle(
            id="article_003",
            title="Ethereum Update",
            content="Ethereum developers released new protocol improvements.",
            published_at=datetime.now(),
            source="decrypt.co",
            category=NewsCategory.TECHNOLOGY
        )

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.engine)
        self.assertIsInstance(self.engine.config, ProcessingConfig)
        self.assertIsInstance(self.engine.cache, FingerprintCache)
        self.assertEqual(self.engine.stats['total_processed'], 0)

    def test_generate_content_hash(self):
        """测试内容哈希生成"""
        content = "Test content"
        hash1 = self.engine._generate_content_hash(content)
        hash2 = self.engine._generate_content_hash(content)

        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA256

    def test_generate_source_fingerprint(self):
        """测试源指纹生成"""
        fingerprint = self.engine._generate_source_fingerprint(self.article1)
        self.assertIsInstance(fingerprint, str)
        self.assertEqual(len(fingerprint), 32)  # MD5

    def test_calculate_content_similarity(self):
        """测试内容相似度计算"""
        # 相似内容
        content1 = "Bitcoin price increased significantly."
        content2 = "Bitcoin price rose significantly."
        similarity = self.engine._calculate_content_similarity(content1, content2)
        self.assertGreater(similarity, 0.5)

        # 不同内容
        content3 = "Ethereum developers announced upgrades."
        similarity2 = self.engine._calculate_content_similarity(content1, content3)
        self.assertLess(similarity2, 0.3)

    def test_calculate_title_similarity(self):
        """测试标题相似度计算"""
        # 相似标题
        title1 = "Bitcoin Price Surge"
        title2 = "Bitcoin Price Increases"
        similarity = self.engine._calculate_title_similarity(title1, title2)
        self.assertGreater(similarity, 0.5)

        # 不同标题
        title3 = "Ethereum Network Upgrade"
        similarity2 = self.engine._calculate_title_similarity(title1, title3)
        self.assertLess(similarity2, 0.3)

    def test_levenshtein_distance(self):
        """测试编辑距离计算"""
        distance = self.engine._levenshtein_distance("kitten", "sitting")
        self.assertEqual(distance, 3)

        distance2 = self.engine._levenshtein_distance("", "test")
        self.assertEqual(distance2, 4)

    @patch('src.news_collection.processing.deduplication_engine.SKLEARN_AVAILABLE', False)
    def test_semantic_hash_fallback(self):
        """测试语义哈希回退机制"""
        content = "Test content"
        hash_result = asyncio.run(self.engine._generate_semantic_hash(content))

        # 当sklearn不可用时，应该回退到内容哈希
        content_hash = self.engine._generate_content_hash(content)
        self.assertEqual(hash_result, content_hash)

    def test_deduplicate_exact_duplicate(self):
        """测试完全重复检测"""
        # 创建完全相同的文章
        duplicate_article = NewsArticle(
            id="article_001_duplicate",
            title=self.article1.title,
            content=self.article1.content,
            published_at=self.article1.published_at,
            source=self.article1.source,
            category=self.article1.category
        )

        result = asyncio.run(self.engine.deduplicate(duplicate_article, [self.article1]))

        self.assertTrue(result.is_duplicate)
        self.assertGreater(result.similarity_score, 0.9)
        self.assertIsNotNone(result.duplicate_group_id)

    def test_deduplicate_different_content(self):
        """测试不同内容检测"""
        result = asyncio.run(self.engine.deduplicate(self.article3, [self.article1, self.article2]))

        self.assertFalse(result.is_duplicate)
        self.assertLess(result.similarity_score, 0.5)

    def test_deduplicate_time_window(self):
        """测试时间窗口检测"""
        # 创建旧文章
        old_article = NewsArticle(
            id="old_article",
            title="Old Bitcoin News",
            content="Bitcoin price movements.",
            published_at=datetime.now() - timedelta(days=2),
            source="oldsource.com",
            category=NewsCategory.GENERAL
        )

        # 创建相似但时间窗口外的文章
        new_article = NewsArticle(
            id="new_article",
            title="Bitcoin Price Changes",
            content="Bitcoin price changes reported.",
            published_at=datetime.now(),
            source="newsource.com",
            category=NewsCategory.GENERAL
        )

        result = asyncio.run(self.engine.deduplicate(new_article, [old_article]))

        # 应该不被认为是重复的，因为时间窗口外
        self.assertFalse(result.is_duplicate)

    def test_cache_operations(self):
        """测试缓存操作"""
        # 生成指纹
        fingerprint = asyncio.run(self.engine._generate_fingerprint(self.article1))

        # 测试缓存重复检测
        cache_result = asyncio.run(self.engine._check_cache_duplicate(fingerprint))
        self.assertIsNone(cache_result)  # 初始为空

        # 添加到缓存
        group_id = "test_group"
        await self.engine._update_cache(fingerprint, group_id)

        # 再次检查缓存
        cache_result = asyncio.run(self.engine._check_cache_duplicate(fingerprint))
        self.assertIsNotNone(cache_result)
        self.assertTrue(cache_result.is_duplicate)

    def test_batch_deduplicate(self):
        """测试批量去重"""
        articles = [self.article1, self.article2, self.article3]
        results = asyncio.run(self.engine.batch_deduplicate(articles))

        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result.is_duplicate, bool)
            self.assertIsInstance(result.similarity_score, float)
            self.assertGreaterEqual(result.similarity_score, 0.0)
            self.assertLessEqual(result.similarity_score, 1.0)

    def test_stats_tracking(self):
        """测试统计跟踪"""
        initial_stats = self.engine.get_stats()
        initial_processed = initial_stats['total_processed']

        # 处理一些文章
        asyncio.run(self.engine.deduplicate(self.article1))
        asyncio.run(self.engine.deduplicate(self.article2))

        final_stats = self.engine.get_stats()
        self.assertEqual(final_stats['total_processed'], initial_processed + 2)
        self.assertGreater(final_stats['avg_processing_time'], 0)

    def test_clear_cache(self):
        """测试缓存清理"""
        # 添加一些指纹到缓存
        fingerprint = asyncio.run(self.engine._generate_fingerprint(self.article1))
        await self.engine._update_cache(fingerprint, "test_group")

        self.assertGreater(len(self.engine.cache.fingerprints), 0)

        # 清空缓存
        self.engine.clear_cache()
        self.assertEqual(len(self.engine.cache.fingerprints), 0)
        self.assertEqual(len(self.engine.cache.article_groups), 0)

    def test_cleanup_cache(self):
        """测试缓存清理"""
        # 创建过期指纹
        expired_fingerprint = MagicMock()
        expired_fingerprint.fingerprint_id = "expired"
        expired_fingerprint.expires_at = datetime.now() - timedelta(hours=1)

        self.engine.cache.fingerprints["expired"] = expired_fingerprint

        # 清理缓存
        asyncio.run(self.engine._cleanup_cache())

        self.assertNotIn("expired", self.engine.cache.fingerprints)

    def test_error_handling(self):
        """测试错误处理"""
        # 创建无效文章
        invalid_article = NewsArticle(
            id="invalid",
            title="",  # 空标题
            content="",  # 空内容
            published_at=None,  # 无时间
            source="",  # 空源
            category=NewsCategory.GENERAL
        )

        # 应该能处理错误而不崩溃
        result = asyncio.run(self.engine.deduplicate(invalid_article))
        self.assertIsInstance(result.is_duplicate, bool)
        self.assertIsInstance(result.similarity_score, float)


if __name__ == '__main__':
    unittest.main()