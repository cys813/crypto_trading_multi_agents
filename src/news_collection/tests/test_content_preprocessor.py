"""
Tests for content preprocessor
"""

import unittest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch

from ..processing.content_preprocessor import ContentPreprocessor, PreprocessingStats
from ..processing.models import ProcessingConfig
from ..models.base import NewsArticle, NewsCategory


class TestContentPreprocessor(unittest.TestCase):
    """测试内容预处理器"""

    def setUp(self):
        """测试设置"""
        self.config = ProcessingConfig()
        self.preprocessor = ContentPreprocessor(self.config)

        # 测试文章
        self.test_article = NewsArticle(
            id="test_001",
            title="Test Article <b>Title</b>",
            content="""
            <p>This is a test article with HTML tags.</p>
            <script>alert('ads');</script>
            Visit https://example.com for more info.
            Multiple    spaces    here.
            AAAABBBBCCCC repeated characters.
            """,
            summary="Test summary",
            author="Test Author",
            published_at=datetime.now(),
            source="test.com",
            url="https://test.com/article",
            category=NewsCategory.GENERAL,
            tags=["test", "article"]
        )

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.preprocessor)
        self.assertIsInstance(self.preprocessor.config, ProcessingConfig)
        self.assertIsNotNone(self.preprocessor.html_tag_pattern)
        self.assertIsNotNone(self.preprocessor.url_pattern)
        self.assertIsNotNone(self.preprocessor.whitespace_pattern)

    def test_remove_html_tags(self):
        """测试HTML标签移除"""
        content = "<p>Hello <b>world</b></p>"
        cleaned_content, count = self.preprocessor._remove_html_tags(content)

        self.assertEqual(cleaned_content, "Hello world")
        self.assertEqual(count, 2)  # <p> and <b>

    def test_remove_urls(self):
        """测试URL移除"""
        content = "Visit https://example.com and http://test.org"
        cleaned_content, count = self.preprocessor._remove_urls(content)

        self.assertEqual(cleaned_content, "Visit [URL] and [URL]")
        self.assertEqual(count, 2)

    def test_normalize_whitespace(self):
        """测试空白字符标准化"""
        content = "Multiple    spaces   and\t\ttabs"
        cleaned_content, count = self.preprocessor._normalize_whitespace(content)

        self.assertEqual(cleaned_content, "Multiple spaces and tabs")
        self.assertGreater(count, 0)

    def test_clean_special_chars(self):
        """测试特殊字符清理"""
        content = "Hello @world# $%^&*() test"
        cleaned_content = self.preprocessor._clean_special_chars(content)

        self.assertNotIn("@", cleaned_content)
        self.assertNotIn("#", cleaned_content)
        self.assertNotIn("$", cleaned_content)
        self.assertIn("Hello world test", cleaned_content)

    def test_remove_repeated_chars(self):
        """测试重复字符移除"""
        content = "AAAAA BBBBB CCCCC"
        cleaned_content = self.preprocessor._remove_repeated_chars(content)

        self.assertEqual(cleaned_content, "AAA BBB CCC")

    def test_remove_boilerplate(self):
        """测试样板文本移除"""
        content = "Main content. 点击这里阅读更多. 免责声明：内容仅供参考。"
        cleaned_content, count = self.preprocessor._remove_boilerplate(content)

        self.assertNotIn("点击这里阅读更多", cleaned_content)
        self.assertNotIn("免责声明", cleaned_content)
        self.assertGreater(count, 0)

    def test_preprocess_title(self):
        """测试标题预处理"""
        title = "<h1>Test Title</h1>"
        processed_title = self.preprocessor._preprocess_title(title)

        self.assertEqual(processed_title, "Test Title")

    def test_preprocess_summary(self):
        """测试摘要预处理"""
        summary = "<p>Test summary</p>"
        processed_summary = self.preprocessor._preprocess_summary(summary)

        self.assertEqual(processed_summary, "Test summary")

    def test_generate_content_hash(self):
        """测试内容哈希生成"""
        content = "Test content"
        hash1 = self.preprocessor.generate_content_hash(content)
        hash2 = self.preprocessor.generate_content_hash(content)

        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA256

    def test_validate_content(self):
        """测试内容验证"""
        # 有效内容
        valid_content = "This is a valid news article with sufficient content length and word count."
        self.assertTrue(self.preprocessor.validate_content(valid_content))

        # 无效内容（过短）
        short_content = "Too short"
        self.assertFalse(self.preprocessor.validate_content(short_content))

        # 无效内容（重复率过高）
        repetitive_content = "abc" * 100
        self.assertFalse(self.preprocessor.validate_content(repetitive_content))

    def test_preprocess_short_content(self):
        """测试短内容处理"""
        short_article = NewsArticle(
            id="test_short",
            title="Short Article",
            content="Too short",
            published_at=datetime.now(),
            source="test.com"
        )

        processed_article, stats = asyncio.run(self.preprocessor.preprocess(short_article))

        # 应该返回原始文章
        self.assertEqual(processed_article.content, "Too short")
        self.assertEqual(stats.original_length, 9)
        self.assertEqual(stats.processed_length, 9)

    @patch('src.news_collection.processing.content_preprocessor.ContentPreprocessor._remove_html_tags')
    @patch('src.news_collection.processing.content_preprocessor.ContentPreprocessor._remove_urls')
    @patch('src.news_collection.processing.content_preprocessor.ContentPreprocessor._normalize_whitespace')
    def test_preprocess_full_pipeline(self, mock_normalize, mock_urls, mock_html):
        """测试完整预处理流程"""
        # 设置mock返回值
        mock_html.return_value = ("cleaned content", 2)
        mock_urls.return_value = ("cleaned content", 1)
        mock_normalize.return_value = ("cleaned content", 1)

        processed_article, stats = asyncio.run(self.preprocessor.preprocess(self.test_article))

        # 验证mock被调用
        mock_html.assert_called_once()
        mock_urls.assert_called_once()
        mock_normalize.assert_called_once()

        # 验证结果
        self.assertIsNotNone(processed_article)
        self.assertIsInstance(stats, PreprocessingStats)

    def test_batch_preprocess(self):
        """测试批量预处理"""
        articles = [
            self.test_article,
            NewsArticle(
                id="test_002",
                title="Second Article",
                content="Second article content.",
                published_at=datetime.now(),
                source="test.com"
            )
        ]

        results = asyncio.run(self.preprocessor.batch_preprocess(articles))

        self.assertEqual(len(results), 2)
        for processed_article, stats in results:
            self.assertIsInstance(processed_article, NewsArticle)
            self.assertIsInstance(stats, PreprocessingStats)

    def test_preprocessing_error_handling(self):
        """测试预处理错误处理"""
        # 创建一个会导致错误的配置
        invalid_config = ProcessingConfig(min_content_length=-100)
        invalid_preprocessor = ContentPreprocessor(invalid_config)

        # 应该能处理错误而不崩溃
        result = asyncio.run(invalid_preprocessor.preprocess(self.test_article))
        processed_article, stats = result

        self.assertIsInstance(processed_article, NewsArticle)
        self.assertIsInstance(stats, PreprocessingStats)

    def test_metadata_update(self):
        """测试元数据更新"""
        processed_article, stats = asyncio.run(self.preprocessor.preprocess(self.test_article))

        self.assertTrue(processed_article.metadata['preprocessed'])
        self.assertIn('preprocessing_time', processed_article.metadata)
        self.assertIn('original_length', processed_article.metadata)
        self.assertIn('processed_length', processed_article.metadata)


if __name__ == '__main__':
    unittest.main()