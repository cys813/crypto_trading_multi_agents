"""
Tests for news summarizer module
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from ..summarizer import (
    NewsSummarizer, SummaryConfig, SummaryResult, SummaryStats,
    SummaryLength, SummaryFocus
)
from ..llm_connector import LLMConnector, LLMConfig, LLMMessage, LLMResponse
from ...models.base import NewsArticle


class TestSummaryConfig:
    """测试摘要配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = SummaryConfig()
        assert config.length == SummaryLength.MEDIUM
        assert config.focus == SummaryFocus.GENERAL
        assert config.include_key_points == True
        assert config.include_entities == True
        assert config.max_bullet_points == 5

    def test_custom_config(self):
        """测试自定义配置"""
        config = SummaryConfig(
            length=SummaryLength.SHORT,
            focus=SummaryFocus.MARKET_IMPACT,
            include_key_points=False,
            max_bullet_points=3
        )
        assert config.length == SummaryLength.SHORT
        assert config.focus == SummaryFocus.MARKET_IMPACT
        assert config.include_key_points == False
        assert config.max_bullet_points == 3


class TestNewsSummarizer:
    """测试新闻摘要器"""

    @pytest.fixture
    def mock_llm_connector(self):
        """模拟LLM连接器"""
        connector = Mock(spec=LLMConnector)

        # 模拟生成响应
        async def mock_generate_response(messages, config=None):
            return LLMResponse(
                content='{"summary": "This is a test summary", "key_points": ["Point 1", "Point 2"], "confidence": 0.8}',
                usage={"total_tokens": 100},
                model="test-model",
                provider="mock",
                response_time=0.5
            )

        connector.generate_response = AsyncMock(side_effect=mock_generate_response)
        return connector

    @pytest.fixture
    def sample_article(self):
        """示例文章"""
        return NewsArticle(
            id="test-article-1",
            title="Bitcoin Surges to New Heights",
            content="Bitcoin has experienced a significant surge, reaching new price levels as institutional investors continue to show strong interest in the cryptocurrency market. The latest price action has been driven by increased adoption and positive regulatory developments.",
            source="Crypto News",
            category="market_analysis"
        )

    def test_init(self, mock_llm_connector):
        """测试初始化"""
        config = SummaryConfig()
        summarizer = NewsSummarizer(mock_llm_connector, config)

        assert summarizer.llm_connector == mock_llm_connector
        assert summarizer.config == config
        assert summarizer.stats.total_articles == 0

    @pytest.mark.asyncio
    async def test_summarize_article(self, mock_llm_connector, sample_article):
        """测试文章摘要"""
        config = SummaryConfig()
        summarizer = NewsSummarizer(mock_llm_connector, config)

        result = await summarizer.summarize_article(sample_article)

        assert isinstance(result, SummaryResult)
        assert result.summary == "This is a test summary"
        assert len(result.key_points) == 2
        assert result.confidence == 0.8
        assert result.word_count["original"] > 0

    @pytest.mark.asyncio
    async def test_summarize_batch(self, mock_llm_connector):
        """测试批量摘要"""
        config = SummaryConfig()
        summarizer = NewsSummarizer(mock_llm_connector, config)

        articles = [
            NewsArticle(
                id="article-1",
                title="Article 1",
                content="Content for article 1",
                source="Test"
            ),
            NewsArticle(
                id="article-2",
                title="Article 2",
                content="Content for article 2",
                source="Test"
            )
        ]

        results = await summarizer.summarize_batch(articles)

        assert len(results) == 2
        for result in results:
            assert isinstance(result, SummaryResult)
            assert result.summary is not None

    @pytest.mark.asyncio
    async def test_article_validation(self, mock_llm_connector):
        """测试文章验证"""
        config = SummaryConfig()
        summarizer = NewsSummarizer(mock_llm_connector, config)

        # 有效文章
        valid_article = NewsArticle(
            id="valid-article",
            title="Valid Title",
            content="This is a valid article content with sufficient length for summarization.",
            source="Test"
        )
        assert summarizer.validate_article(valid_article) is True

        # 无效文章（内容太短）
        invalid_article = NewsArticle(
            id="invalid-article",
            title="Invalid",
            content="Short",
            source="Test"
        )
        assert summarizer.validate_article(invalid_article) is False

    @pytest.mark.asyncio
    async def test_quality_metrics(self, mock_llm_connector, sample_article):
        """测试质量指标"""
        config = SummaryConfig()
        summarizer = NewsSummarizer(mock_llm_connector, config)

        result = await summarizer.summarize_article(sample_article)
        metrics = summarizer.get_quality_metrics(result)

        assert "overall_quality_score" in metrics
        assert "confidence_score" in metrics
        assert "word_count_ratio" in metrics
        assert "key_points_count" in metrics
        assert 0.0 <= metrics["overall_quality_score"] <= 1.0

    def test_get_stats(self, mock_llm_connector):
        """测试统计信息"""
        config = SummaryConfig()
        summarizer = NewsSummarizer(mock_llm_connector, config)

        stats = summarizer.get_stats()
        assert stats["total_articles"] == 0
        assert stats["successful_summaries"] == 0
        assert stats["failed_summaries"] == 0
        assert "config" in stats

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_llm_connector, sample_article):
        """测试错误处理"""
        config = SummaryConfig()
        summarizer = NewsSummarizer(mock_llm_connector, config)

        # 模拟LLM连接器失败
        mock_llm_connector.generate_response.side_effect = Exception("API Error")

        result = await summarizer.summarize_article(sample_article)

        assert isinstance(result, SummaryResult)
        assert "Failed to generate summary" in result.summary
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_different_summary_types(self, mock_llm_connector, sample_article):
        """测试不同类型的摘要"""
        # 测试不同长度
        short_config = SummaryConfig(length=SummaryLength.SHORT)
        summarizer = NewsSummarizer(mock_llm_connector, short_config)
        result = await summarizer.summarize_article(sample_article)
        assert summarizer.config.length == SummaryLength.SHORT

        # 测试不同焦点
        market_config = SummaryConfig(focus=SummaryFocus.MARKET_IMPACT)
        market_summarizer = NewsSummarizer(mock_llm_connector, market_config)
        market_result = await market_summarizer.summarize_article(sample_article)
        assert market_summarizer.config.focus == SummaryFocus.MARKET_IMPACT


class TestSummaryResult:
    """测试摘要结果类"""

    def test_summary_result_creation(self):
        """测试摘要结果创建"""
        result = SummaryResult(
            summary="Test summary",
            key_points=["Point 1", "Point 2"],
            entities=[],
            sentiment={},
            confidence=0.8,
            processing_time=1.0,
            word_count={"original": 100, "summary": 20},
            metadata={}
        )

        assert result.summary == "Test summary"
        assert len(result.key_points) == 2
        assert result.confidence == 0.8
        assert result.word_count["original"] == 100


if __name__ == "__main__":
    pytest.main([__file__])