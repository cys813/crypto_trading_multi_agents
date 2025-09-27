"""
Tests for sentiment analyzer module
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch

from ..sentiment_analyzer import (
    SentimentAnalyzer, SentimentConfig, SentimentAnalysisResult,
    SentimentScore, SentimentCategory, SentimentAspect, SentimentStats
)
from ..llm_connector import LLMConnector, LLMConfig, LLMMessage, LLMResponse
from ...models.base import NewsArticle


class TestSentimentConfig:
    """测试情感分析配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = SentimentConfig()
        assert config.enable_aspect_analysis is True
        assert config.enable_intensity_scoring is True
        assert config.enable_emotion_detection is True
        assert config.enable_confidence_scoring is True
        assert config.enable_context_analysis is True
        assert config.language == "en"
        assert config.output_format == "structured"
        assert config.include_explanation is True
        assert config.include_key_phrases is True
        assert config.max_key_phrases == 10

    def test_custom_config(self):
        """测试自定义配置"""
        config = SentimentConfig(
            enable_aspect_analysis=False,
            enable_intensity_scoring=False,
            language="zh",
            output_format="simple",
            max_key_phrases=5
        )
        assert config.enable_aspect_analysis is False
        assert config.enable_intensity_scoring is False
        assert config.language == "zh"
        assert config.output_format == "simple"
        assert config.max_key_phrases == 5


class TestSentimentScore:
    """测试情感分数类"""

    def test_sentiment_score_creation(self):
        """测试情感分数创建"""
        score = SentimentScore(
            category=SentimentCategory.POSITIVE,
            score=0.8,
            confidence=0.9,
            explanation="Strong positive sentiment detected",
            intensity=0.7
        )
        assert score.category == SentimentCategory.POSITIVE
        assert score.score == 0.8
        assert score.confidence == 0.9
        assert score.intensity == 0.7
        assert score.key_phrases == []
        assert score.emotions == {}
        assert score.aspects == {}

    def test_sentiment_score_with_additional_data(self):
        """测试带额外数据的情感分数"""
        score = SentimentScore(
            category=SentimentCategory.NEGATIVE,
            score=-0.6,
            confidence=0.8,
            explanation="Negative sentiment with concerns",
            intensity=0.5,
            key_phrases=["decline", "risk", "concern"],
            emotions={"fear": 0.7, "uncertainty": 0.5},
            aspects={"market": "bearish", "regulatory": "restrictive"}
        )
        assert score.key_phrases == ["decline", "risk", "concern"]
        assert score.emotions == {"fear": 0.7, "uncertainty": 0.5}
        assert score.aspects == {"market": "bearish", "regulatory": "restrictive"}


class TestSentimentAnalyzer:
    """测试情感分析器"""

    @pytest.fixture
    def mock_llm_connector(self):
        """模拟LLM连接器"""
        connector = Mock(spec=LLMConnector)

        # 模拟生成响应
        async def mock_generate_response(messages, config=None):
            return LLMResponse(
                content='''{
                    "overall_sentiment": {
                        "category": "positive",
                        "score": 0.7,
                        "confidence": 0.85,
                        "explanation": "The article shows positive market sentiment",
                        "intensity": 0.6
                    },
                    "aspect_sentiments": {
                        "market_sentiment": {
                            "category": "positive",
                            "score": 0.8,
                            "confidence": 0.9,
                            "explanation": "Strong market optimism",
                            "intensity": 0.7
                        }
                    },
                    "market_impact_indicators": {
                        "volatility": 0.4,
                        "reaction": 0.6,
                        "time_horizon": "short-term"
                    },
                    "key_phrases": ["bullish", "growth", "adoption"],
                    "emotions": {"optimism": 0.8, "excitement": 0.6},
                    "reliability_score": 0.8,
                    "analysis_confidence": 0.85
                }''',
                usage={"total_tokens": 150},
                model="test-model",
                provider="mock",
                response_time=0.8
            )

        connector.generate_response = AsyncMock(side_effect=mock_generate_response)
        return connector

    @pytest.fixture
    def sample_article(self):
        """示例文章"""
        return NewsArticle(
            id="test-article-1",
            title="Bitcoin Shows Strong Growth Potential",
            content="Bitcoin demonstrates significant growth potential as institutional adoption continues to increase. Market analysts are optimistic about the future trajectory, citing strong fundamentals and increasing mainstream acceptance.",
            source="Crypto News",
            category="market_analysis",
            author="John Doe",
            tags=["bitcoin", "growth", "adoption"]
        )

    def test_init(self, mock_llm_connector):
        """测试初始化"""
        config = SentimentConfig()
        analyzer = SentimentAnalyzer(mock_llm_connector, config)

        assert analyzer.llm_connector == mock_llm_connector
        assert analyzer.config == config
        assert analyzer.stats.total_analyses == 0
        assert analyzer.stats.successful_analyses == 0
        assert analyzer.stats.failed_analyses == 0

        # 检查统计初始化
        for category in SentimentCategory:
            assert analyzer.stats.sentiment_distribution[category.value] == 0
        for aspect in SentimentAspect:
            assert analyzer.stats.aspect_analysis_count[aspect.value] == 0

    def test_create_system_prompt(self):
        """测试系统提示创建"""
        config = SentimentConfig()
        llm_connector = Mock(spec=LLMConnector)
        analyzer = SentimentAnalyzer(llm_connector, config)

        prompt = analyzer._create_system_prompt()
        assert "sentiment analyst" in prompt.lower()
        assert "cryptocurrency" in prompt.lower()
        assert "financial news" in prompt.lower()
        assert "market sentiment" in prompt.lower()

    def test_create_user_prompt(self, sample_article):
        """测试用户提示创建"""
        config = SentimentConfig()
        llm_connector = Mock(spec=LLMConnector)
        analyzer = SentimentAnalyzer(llm_connector, config)

        prompt = analyzer._create_user_prompt(sample_article)
        assert sample_article.title in prompt
        assert sample_article.content in prompt
        assert sample_article.source in prompt
        assert sample_article.category.value in prompt
        assert "bitcoin, growth, adoption" in prompt

    def test_parse_sentiment_response_json(self):
        """测试JSON响应解析"""
        config = SentimentConfig()
        llm_connector = Mock(spec=LLMConnector)
        analyzer = SentimentAnalyzer(llm_connector, config)

        json_response = '''{
            "overall_sentiment": {
                "category": "positive",
                "score": 0.8,
                "confidence": 0.9,
                "explanation": "Positive market sentiment"
            },
            "aspect_sentiments": {},
            "market_impact_indicators": {},
            "key_phrases": ["growth", "optimism"],
            "emotions": {},
            "reliability_score": 0.8
        }'''

        result = analyzer._parse_sentiment_response(json_response)
        assert result["overall_sentiment"]["category"] == "positive"
        assert result["overall_sentiment"]["score"] == 0.8
        assert result["key_phrases"] == ["growth", "optimism"]

    def test_parse_sentiment_response_text(self):
        """测试文本响应解析"""
        config = SentimentConfig()
        llm_connector = Mock(spec=LLMConnector)
        analyzer = SentimentAnalyzer(llm_connector, config)

        text_response = """
        Overall sentiment: The market shows positive sentiment with bullish expectations.
        Market sentiment: Strong optimistic outlook for cryptocurrency prices.
        Regulatory sentiment: Neutral with no significant changes.
        """
        result = analyzer._parse_sentiment_response(text_response)
        assert "overall_sentiment" in result
        assert "aspect_sentiments" in result

    def test_create_sentiment_score(self):
        """测试情感分数创建"""
        config = SentimentConfig()
        llm_connector = Mock(spec=LLMConnector)
        analyzer = SentimentAnalyzer(llm_connector, config)

        sentiment_data = {
            "category": "positive",
            "score": 0.7,
            "confidence": 0.85,
            "explanation": "Positive market indicators",
            "intensity": 0.6,
            "key_phrases": ["growth", "optimism"],
            "emotions": {"excitement": 0.7}
        }

        score = analyzer._create_sentiment_score(sentiment_data)
        assert score.category == SentimentCategory.POSITIVE
        assert score.score == 0.7
        assert score.confidence == 0.85
        assert score.intensity == 0.6
        assert score.key_phrases == ["growth", "optimism"]
        assert score.emotions == {"excitement": 0.7}

    @pytest.mark.asyncio
    async def test_analyze_sentiment(self, mock_llm_connector, sample_article):
        """测试情感分析"""
        config = SentimentConfig()
        analyzer = SentimentAnalyzer(mock_llm_connector, config)

        result = await analyzer.analyze_sentiment(sample_article)

        assert isinstance(result, SentimentAnalysisResult)
        assert result.overall_sentiment.category == SentimentCategory.POSITIVE
        assert result.overall_sentiment.score == 0.7
        assert result.overall_sentiment.confidence == 0.85
        assert len(result.aspect_sentiments) > 0
        assert "market_impact_indicators" in result.market_impact_indicators
        assert result.processing_time > 0
        assert result.reliability_score > 0

    @pytest.mark.asyncio
    async def test_analyze_sentiment_error_handling(self, mock_llm_connector, sample_article):
        """测试情感分析错误处理"""
        config = SentimentConfig()
        analyzer = SentimentAnalyzer(mock_llm_connector, config)

        # 模拟LLM错误
        mock_llm_connector.generate_response.side_effect = Exception("API Error")

        result = await analyzer.analyze_sentiment(sample_article)

        assert isinstance(result, SentimentAnalysisResult)
        assert result.overall_sentiment.category == SentimentCategory.NEUTRAL
        assert result.overall_sentiment.score == 0.0
        assert result.overall_sentiment.confidence == 0.0
        assert "API Error" in result.overall_sentiment.explanation
        assert result.reliability_score == 0.0

    @pytest.mark.asyncio
    async def test_analyze_batch_sentiment(self, mock_llm_connector):
        """测试批量情感分析"""
        config = SentimentConfig()
        analyzer = SentimentAnalyzer(mock_llm_connector, config)

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

        results = await analyzer.analyze_batch_sentiment(articles)

        assert len(results) == 2
        for result in results:
            assert isinstance(result, SentimentAnalysisResult)
            assert result.overall_sentiment is not None

    def test_analyze_temporal_indicators(self):
        """测试时间指标分析"""
        config = SentimentConfig()
        llm_connector = Mock(spec=LLMConnector)
        analyzer = SentimentAnalyzer(llm_connector, config)

        # 测试紧急内容
        urgent_article = NewsArticle(
            id="urgent-article",
            title="URGENT: Market Alert",
            content="Breaking: Critical market emergency requiring immediate attention",
            source="News"
        )

        sentiment_data = {"market_impact_indicators": {"time_horizon": "immediate"}}
        temporal = analyzer._analyze_temporal_indicators(urgent_article, sentiment_data)

        assert temporal["time_horizon"] == "immediate"
        assert temporal["urgency"] > 0.5

        # 测试长期内容
        long_term_article = NewsArticle(
            id="long-term-article",
            title="Long-term Market Analysis",
            content="This represents a fundamental long-term shift in market dynamics",
            source="Analysis"
        )

        temporal = analyzer._analyze_temporal_indicators(long_term_article, {})
        assert temporal["duration"] == "long-term"

    def test_update_stats(self):
        """测试统计更新"""
        config = SentimentConfig()
        llm_connector = Mock(spec=LLMConnector)
        analyzer = SentimentAnalyzer(llm_connector, config)

        # 创建测试结果
        result = SentimentAnalysisResult(
            overall_sentiment=SentimentScore(
                category=SentimentCategory.POSITIVE,
                score=0.7,
                confidence=0.8,
                explanation="Test",
                intensity=0.6
            ),
            aspect_sentiments={
                SentimentAspect.MARKET_SENTIMENT: SentimentScore(
                    category=SentimentCategory.POSITIVE,
                    score=0.8,
                    confidence=0.9,
                    explanation="Market test",
                    intensity=0.7
                )
            },
            market_impact_indicators={},
            temporal_indicators={},
            reliability_score=0.8,
            processing_time=1.0,
            metadata={}
        )

        analyzer._update_stats(result)

        assert analyzer.stats.sentiment_distribution["positive"] == 1
        assert analyzer.stats.aspect_analysis_count["market_sentiment"] == 1
        assert analyzer.stats.average_processing_time == 1.0
        assert analyzer.stats.average_confidence == 0.8

    def test_get_stats(self):
        """测试获取统计信息"""
        config = SentimentConfig()
        llm_connector = Mock(spec=LLMConnector)
        analyzer = SentimentAnalyzer(llm_connector, config)

        stats = analyzer.get_stats()
        assert "total_analyses" in stats
        assert "successful_analyses" in stats
        assert "failed_analyses" in stats
        assert "success_rate" in stats
        assert "average_processing_time" in stats
        assert "average_confidence" in stats
        assert "sentiment_distribution" in stats
        assert "aspect_analysis_count" in stats
        assert "config" in stats

    def test_get_market_sentiment_summary(self):
        """测试市场情感摘要"""
        config = SentimentConfig()
        llm_connector = Mock(spec=LLMConnector)
        analyzer = SentimentAnalyzer(llm_connector, config)

        # 创建测试结果
        results = [
            SentimentAnalysisResult(
                overall_sentiment=SentimentScore(
                    category=SentimentCategory.POSITIVE,
                    score=0.7,
                    confidence=0.8,
                    explanation="Test",
                    intensity=0.6
                ),
                aspect_sentiments={},
                market_impact_indicators={"volatility": 0.4, "reaction": 0.6},
                temporal_indicators={},
                reliability_score=0.8,
                processing_time=1.0,
                metadata={}
            ),
            SentimentAnalysisResult(
                overall_sentiment=SentimentScore(
                    category=SentimentCategory.NEGATIVE,
                    score=-0.5,
                    confidence=0.7,
                    explanation="Test",
                    intensity=0.5
                ),
                aspect_sentiments={},
                market_impact_indicators={"volatility": 0.6, "reaction": -0.3},
                temporal_indicators={},
                reliability_score=0.7,
                processing_time=1.0,
                metadata={}
            )
        ]

        summary = analyzer.get_market_sentiment_summary(results)
        assert summary["total_articles"] == 2
        assert "sentiment_distribution" in summary
        assert "average_sentiment_score" in summary
        assert "average_confidence" in summary
        assert "market_impact_indicators" in summary
        assert summary["average_sentiment_score"] == 0.1  # (0.7 + (-0.5)) / 2

    def test_validate_article(self):
        """测试文章验证"""
        config = SentimentConfig()
        llm_connector = Mock(spec=LLMConnector)
        analyzer = SentimentAnalyzer(llm_connector, config)

        # 有效文章
        valid_article = NewsArticle(
            id="valid-article",
            title="Valid Article Title",
            content="This is a valid article content with sufficient length for sentiment analysis.",
            source="Test"
        )
        assert analyzer.validate_article(valid_article) is True

        # 内容太短的文章
        short_content_article = NewsArticle(
            id="short-content",
            title="Short Content",
            content="Short",
            source="Test"
        )
        assert analyzer.validate_article(short_content_article) is False

        # 标题太短的文章
        short_title_article = NewsArticle(
            id="short-title",
            title="Short",
            content="This article has sufficient content but the title is too short.",
            source="Test"
        )
        assert analyzer.validate_article(short_title_article) is False

    def test_update_config(self):
        """测试配置更新"""
        config = SentimentConfig()
        llm_connector = Mock(spec=LLMConnector)
        analyzer = SentimentAnalyzer(llm_connector, config)

        new_config = SentimentConfig(
            enable_aspect_analysis=False,
            language="zh"
        )

        analyzer.update_config(new_config)
        assert analyzer.config.enable_aspect_analysis is False
        assert analyzer.config.language == "zh"


class TestSentimentAnalysisResult:
    """测试情感分析结果类"""

    def test_result_creation(self):
        """测试结果创建"""
        overall_sentiment = SentimentScore(
            category=SentimentCategory.POSITIVE,
            score=0.7,
            confidence=0.8,
            explanation="Test sentiment",
            intensity=0.6
        )

        result = SentimentAnalysisResult(
            overall_sentiment=overall_sentiment,
            aspect_sentiments={},
            market_impact_indicators={"volatility": 0.4},
            temporal_indicators={"duration": "short-term"},
            reliability_score=0.8,
            processing_time=1.0,
            metadata={"test": "data"}
        )

        assert result.overall_sentiment == overall_sentiment
        assert result.market_impact_indicators["volatility"] == 0.4
        assert result.temporal_indicators["duration"] == "short-term"
        assert result.reliability_score == 0.8
        assert result.processing_time == 1.0
        assert result.metadata["test"] == "data"


if __name__ == "__main__":
    pytest.main([__file__])