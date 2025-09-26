"""
Unit tests for incremental tracker
"""

import unittest
import asyncio
import tempfile
import os
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from ..collection.incremental_tracker import (
    IncrementalTracker,
    ArticleFingerprint,
    SourceTrackingInfo
)
from ..models.base import NewsArticle


class TestIncrementalTracker(unittest.TestCase):
    """测试增量跟踪器"""

    def setUp(self):
        """设置测试环境"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'window_days': 15,
            'max_articles_in_memory': 1000,
            'persistence_interval': 60,
            'storage_path': self.temp_dir
        }
        self.tracker = IncrementalTracker(self.config)

        # 创建测试文章
        self.test_articles = [
            NewsArticle(
                id="1",
                title="Bitcoin price reaches $50,000",
                content="Bitcoin has reached a new all-time high...",
                source="coindesk",
                url="https://coindesk.com/bitcoin-50000",
                published_at=datetime.now() - timedelta(hours=1)
            ),
            NewsArticle(
                id="2",
                title="Ethereum upgrade announced",
                content="Ethereum developers have announced a major upgrade...",
                source="decrypt",
                url="https://decrypt.com/ethereum-upgrade",
                published_at=datetime.now() - timedelta(hours=2)
            ),
            NewsArticle(
                id="3",
                title="Duplicate Bitcoin article",
                content="Bitcoin has reached a new all-time high...",  # 相同内容
                source="coindesk",
                url="https://coindesk.com/bitcoin-50000",  # 相同URL
                published_at=datetime.now() - timedelta(hours=1)
            )
        ]

    def tearDown(self):
        """清理测试环境"""
        self.loop.close()
        # 清理临时目录
        shutil.rmtree(self.temp_dir)

    def test_tracker_initialization(self):
        """测试跟踪器初始化"""
        self.assertEqual(self.tracker.window_days, 15)
        self.assertEqual(self.tracker.max_articles_in_memory, 1000)
        self.assertEqual(self.tracker.storage_path, self.temp_dir)

    def test_generate_fingerprint(self):
        """测试生成文章指纹"""
        article = self.test_articles[0]
        fingerprint = self.tracker.get_fingerprint(article)

        # URL文章应该使用URL生成指纹
        self.assertEqual(fingerprint, self.tracker._generate_hash(article.url))

    def test_generate_fingerprint_without_url(self):
        """测试无URL文章的指纹生成"""
        article = NewsArticle(
            id="4",
            title="Test article",
            content="Test content",
            source="test_source",
            url=None,
            published_at=datetime.now()
        )

        fingerprint = self.tracker.get_fingerprint(article)

        # 无URL文章应该使用标题+来源+发布时间生成指纹
        expected_text = f"{article.title}_{article.source}_{article.published_at}"
        expected_fingerprint = self.tracker._generate_hash(expected_text)
        self.assertEqual(fingerprint, expected_fingerprint)

    def test_duplicate_detection(self):
        """测试重复检测"""
        # 跟踪第一篇文章
        article1 = self.test_articles[0]
        fingerprint1 = self.tracker.track_article(article1)

        # 检查第二篇不重复的文章
        article2 = self.test_articles[1]
        is_duplicate2 = self.tracker.is_duplicate(article2)
        self.assertFalse(is_duplicate2)

        # 检查第三篇重复的文章（相同URL）
        article3 = self.test_articles[2]
        is_duplicate3 = self.tracker.is_duplicate(article3)
        self.assertTrue(is_duplicate3)

    def test_duplicate_detection_without_url(self):
        """测试无URL文章的重复检测"""
        article_without_url = NewsArticle(
            id="5",
            title="Test title",
            content="Test content",
            source="test_source",
            url=None,
            published_at=datetime.now()
        )

        # 第一次跟踪
        self.tracker.track_article(article_without_url)

        # 相同文章应该被检测为重复
        duplicate_article = NewsArticle(
            id="6",
            title="Test title",
            content="Test content",
            source="test_source",
            url=None,
            published_at=datetime.now()
        )

        is_duplicate = self.tracker.is_duplicate(duplicate_article)
        self.assertTrue(is_duplicate)

    def test_track_article(self):
        """测试跟踪文章"""
        article = self.test_articles[0]
        fingerprint = self.tracker.track_article(article)

        # 验证指纹被存储
        self.assertIn(fingerprint, self.tracker.article_fingerprints)

        # 验证URL索引
        self.assertEqual(self.tracker.url_index[article.url], fingerprint)

        # 验证标题源索引
        title_hash = self.tracker._generate_hash(article.title)
        title_source_key = f"{title_hash}_{article.source}"
        self.assertIn(title_source_key, self.tracker.title_source_index)
        self.assertIn(fingerprint, self.tracker.title_source_index[title_source_key])

    def test_update_source_tracking(self):
        """测试更新源跟踪信息"""
        source_name = "coindesk"
        collection_time = datetime.now()
        articles_count = 5
        last_article_id = "article123"

        # 更新跟踪信息（成功）
        self.tracker.update_source_tracking(
            source_name, collection_time, articles_count, last_article_id, success=True
        )

        tracking_info = self.tracker.get_source_tracking_info(source_name)
        self.assertIsNotNone(tracking_info)
        self.assertEqual(tracking_info.source_name, source_name)
        self.assertEqual(tracking_info.last_collection_time, collection_time)
        self.assertEqual(tracking_info.total_articles_collected, articles_count)
        self.assertEqual(tracking_info.last_article_id, last_article_id)
        self.assertEqual(tracking_info.consecutive_failures, 0)

        # 更新跟踪信息（失败）
        self.tracker.update_source_tracking(
            source_name, collection_time, articles_count, success=False
        )

        tracking_info = self.tracker.get_source_tracking_info(source_name)
        self.assertEqual(tracking_info.consecutive_failures, 1)

    def test_get_last_collection_time(self):
        """测试获取最后收集时间"""
        source_name = "test_source"
        collection_time = datetime.now()

        # 没有跟踪信息时应该返回None
        last_time = self.tracker.get_last_collection_time(source_name)
        self.assertIsNone(last_time)

        # 更新跟踪信息后应该返回正确时间
        self.tracker.update_source_tracking(source_name, collection_time, 1, success=True)
        last_time = self.tracker.get_last_collection_time(source_name)
        self.assertEqual(last_time, collection_time)

    def test_get_collection_window(self):
        """测试获取收集时间窗口"""
        end_time = datetime.now()
        expected_start_time = end_time - timedelta(days=15)

        start_time, returned_end_time = self.tracker.get_collection_window()

        self.assertEqual(returned_end_time.date(), end_time.date())
        self.assertEqual(start_time.date(), expected_start_time.date())

    def test_get_articles_in_window(self):
        """测试获取时间窗口内的文章"""
        # 创建不同时间的测试文章
        old_article = NewsArticle(
            id="7",
            title="Old article",
            content="Old content",
            published_at=datetime.now() - timedelta(days=20)
        )

        recent_article = NewsArticle(
            id="8",
            title="Recent article",
            content="Recent content",
            published_at=datetime.now() - timedelta(days=5)
        )

        # 跟踪文章
        self.tracker.track_article(old_article)
        self.tracker.track_article(recent_article)

        # 获取最近15天的文章
        start_time = datetime.now() - timedelta(days=15)
        end_time = datetime.now()
        articles = self.tracker.get_articles_in_window(start_time, end_time)

        # 应该只返回最近的文章
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].published_at, recent_article.published_at)

    def test_remove_expired_articles(self):
        """测试移除过期文章"""
        # 创建过期文章
        old_fingerprint = "old_fingerprint"
        old_article_fingerprint = ArticleFingerprint(
            title_hash="old_title",
            content_hash="old_content",
            source="old_source",
            url="old_url",
            published_at=datetime.now() - timedelta(days=20),
            created_at=datetime.now() - timedelta(days=20)
        )

        self.tracker.article_fingerprints[old_fingerprint] = old_article_fingerprint
        self.tracker.url_index["old_url"] = old_fingerprint

        # 创建近期文章
        recent_fingerprint = "recent_fingerprint"
        recent_article_fingerprint = ArticleFingerprint(
            title_hash="recent_title",
            content_hash="recent_content",
            source="recent_source",
            url="recent_url",
            published_at=datetime.now() - timedelta(days=5),
            created_at=datetime.now() - timedelta(days=5)
        )

        self.tracker.article_fingerprints[recent_fingerprint] = recent_article_fingerprint
        self.tracker.url_index["recent_url"] = recent_fingerprint

        # 移除10天前的文章
        cutoff_time = datetime.now() - timedelta(days=10)
        removed_count = self.tracker.remove_expired_articles(cutoff_time)

        self.assertEqual(removed_count, 1)
        self.assertIn(recent_fingerprint, self.tracker.article_fingerprints)
        self.assertNotIn(old_fingerprint, self.tracker.article_fingerprints)
        self.assertNotIn("old_url", self.tracker.url_index)
        self.assertIn("recent_url", self.tracker.url_index)

    def test_get_statistics(self):
        """测试获取统计信息"""
        # 添加一些测试数据
        self.tracker.track_article(self.test_articles[0])
        self.tracker.update_source_tracking("coindesk", datetime.now(), 5, success=True)

        stats = self.tracker.get_statistics()

        self.assertGreater(stats['total_articles_tracked'], 0)
        self.assertGreater(stats['total_sources_tracked'], 0)
        self.assertGreater(stats['estimated_memory_usage_bytes'], 0)
        self.assertIn('sources', stats)
        self.assertIn('coindesk', stats['sources'])

    def test_persistence_save_load(self):
        """测试持久化保存和加载"""
        # 添加测试数据
        self.tracker.track_article(self.test_articles[0])
        self.tracker.update_source_tracking("coindesk", datetime.now(), 5, "article123", success=True)

        # 保存数据
        self.loop.run_until_complete(self.tracker._save_data())

        # 验证文件已创建
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'fingerprints.pkl')))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'tracking.json')))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, 'indexes.json')))

        # 创建新的跟踪器实例
        new_tracker = IncrementalTracker(self.config)

        # 加载数据
        self.loop.run_until_complete(new_tracker._load_data())

        # 验证数据已恢复
        self.assertEqual(len(new_tracker.article_fingerprints), 1)
        self.assertEqual(len(new_tracker.source_tracking), 1)
        self.assertIn("coindesk", new_tracker.source_tracking)

    def test_export_data(self):
        """测试数据导出"""
        # 添加测试数据
        self.tracker.track_article(self.test_articles[0])

        export_path = os.path.join(self.temp_dir, 'export.json')
        success = self.tracker.export_data(export_path)

        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))

        # 验证导出的数据
        import json
        with open(export_path, 'r') as f:
            exported_data = json.load(f)

        self.assertIn('fingerprints', exported_data)
        self.assertIn('source_tracking', exported_data)
        self.assertIn('export_time', exported_data)
        self.assertIn('statistics', exported_data)

    def test_memory_cleanup(self):
        """测试内存清理"""
        # 添加大量文章
        for i in range(1500):  # 超过max_articles_in_memory
            article = NewsArticle(
                id=f"article_{i}",
                title=f"Title {i}",
                content=f"Content {i}",
                url=f"https://example.com/{i}",
                published_at=datetime.now()
            )
            self.tracker.track_article(article)

        # 模拟内存清理（实际中会在persistence循环中触发）
        cutoff_time = datetime.now() - timedelta(days=self.tracker.window_days)
        removed_count = self.tracker.remove_expired_articles(cutoff_time)

        self.assertGreater(removed_count, 0)

    def test_source_tracking_stats(self):
        """测试源跟踪统计"""
        source_name = "test_source"
        collection_time = datetime.now()

        # 多次更新跟踪信息
        self.tracker.update_source_tracking(source_name, collection_time, 5, success=True)
        self.tracker.update_source_tracking(source_name, collection_time, 3, success=True)
        self.tracker.update_source_tracking(source_name, collection_time, 7, success=True)

        tracking_info = self.tracker.get_source_tracking_info(source_name)

        self.assertEqual(tracking_info.total_articles_collected, 15)  # 5+3+7
        self.assertEqual(tracking_info.consecutive_failures, 0)
        self.assertIn(collection_time.strftime('%Y-%m-%d'), tracking_info.collection_stats)
        self.assertEqual(tracking_info.collection_stats[collection_time.strftime('%Y-%m-%d')], 15)


if __name__ == '__main__':
    unittest.main()