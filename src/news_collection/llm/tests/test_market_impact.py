"""
Tests for market impact assessment module
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch

from ..market_impact import (
    MarketImpactAssessor, MarketImpactConfig, MarketImpactResult, ImpactScore,
    ImpactType, ImpactTimeframe, ImpactMagnitude, MarketImpactStats
)
from ..llm_connector import LLMConnector, LLMConfig, LLMMessage, LLMResponse
from ..sentiment_analyzer import SentimentAnalysisResult, SentimentCategory, SentimentScore
from ..entity_extractor import EntityExtractionResult, Entity, EntityType
from ...models.base import NewsArticle


class TestMarketImpactConfig:
    """测试市场影响配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = MarketImpactConfig()
        assert config.enable_multi_factor_analysis is True
        assert config.enable_correlation_analysis is True
        assert config.enable_risk_assessment is True
        assert config.enable_opportunity_identification is True
        assert len(config.impact_types_to_analyze) == 3
        assert ImpactType.PRICE_VOLATILITY in config.impact_types_to_analyze
        assert ImpactType.TRADING_VOLUME in config.impact_types_to_analyze
        assert len(config.timeframes_to_analyze) == 2
        assert ImpactTimeframe.IMMEDIATE in config.timeframes_to_analyze
        assert config.min_confidence_threshold == 0.4
        assert config.include_probability_assessment is True
        assert config.include_market_context is True
        assert config.language == "en"
        assert config.output_format == "structured"

    def test_custom_config(self):
        """测试自定义配置"""
        config = MarketImpactConfig(
            enable_multi_factor_analysis=False,
            impact_types_to_analyze=[ImpactType.PRICE_VOLATILITY],
            timeframes_to_analyze=[ImpactTimeframe.LONG_TERM],
            min_confidence_threshold=0.7,
            language="zh"
        )
        assert config.enable_multi_factor_analysis is False
        assert len(config.impact_types_to_analyze) == 1
        assert ImpactType.PRICE_VOLATILITY in config.impact_types_to_analyze
        assert len(config.timeframes_to_analyze) == 1
        assert ImpactTimeframe.LONG_TERM in config.timeframes_to_analyze
        assert config.min_confidence_threshold == 0.7
        assert config.language == "zh"


class TestImpactScore:
    """测试影响分数类"""

    def test_impact_score_creation(self):
        """测试影响分数创建"""
        score = ImpactScore(
            impact_type=ImpactType.PRICE_VOLATILITY,
            timeframe=ImpactTimeframe.IMMEDIATE,
            magnitude=ImpactMagnitude.HIGH,
            confidence=0.8,
            probability=0.7,
            direction="positive",
            reasoning="Strong positive impact expected",
            risk_level="medium"
        )
        assert score.impact_type == ImpactType.PRICE_VOLATILITY
        assert score.timeframe == ImpactTimeframe.IMMEDIATE
        assert score.magnitude == ImpactMagnitude.HIGH
        assert score.confidence == 0.8
        assert score.probability == 0.7
        assert score.direction == "positive"
        assert score.risk_level == "medium"
        assert score.key_factors == []
        assert score.affected_assets == []

    def test_impact_score_with_additional_data(self):
        """测试带额外数据的影响分数"""
        score = ImpactScore(
            impact_type=ImpactType.REGULATORY_IMPACT,
            timeframe=ImpactTimeframe.LONG_TERM,
            magnitude=ImpactMagnitude.VERY_HIGH,
            confidence=0.9,
            probability=0.8,
            direction="negative",
            reasoning="Major regulatory changes expected",
            key_factors=["compliance requirements", "legal implications"],
            affected_assets=["Bitcoin", "Ethereum", "Altcoins"],
            risk_level="high"
        )
        assert len(score.key_factors) == 2
        assert "compliance requirements" in score.key_factors
        assert len(score.affected_assets) == 3
        assert "Bitcoin" in score.affected_assets
        assert score.risk_level == "high"


class TestMarketImpactResult:
    """测试市场影响结果类"""

    def test_result_creation(self):
        """测试结果创建"""
        overall_impact = ImpactScore(
            impact_type=ImpactType.MARKET_SENTIMENT,
            timeframe=ImpactTimeframe.IMMEDIATE,
            magnitude=ImpactMagnitude.MODERATE,
            confidence=0.7,
            probability=0.6,
            direction="neutral",
            reasoning="Mixed market sentiment"
        )

        result = MarketImpactResult(
            overall_impact=overall_impact,
            impact_breakdown={
                ImpactType.PRICE_VOLATILITY: [],
                ImpactType.TRADING_VOLUME: []
            },
            market_sentiment={"overall": "neutral"},
            risk_assessment={"risk_level": "low"},
            opportunity_analysis={"opportunities": []},
            correlation_analysis={"correlations": []},
            processing_time=2.0,
            metadata={"test": "data"}
        )

        assert result.overall_impact == overall_impact
        assert len(result.impact_breakdown) == 2
        assert result.market_sentiment["overall"] == "neutral"
        assert result.risk_assessment["risk_level"] == "low"
        assert result.processing_time == 2.0
        assert result.metadata["test"] == "data"


class TestMarketImpactAssessor:
    """测试市场影响评估器"""

    @pytest.fixture
    def mock_llm_connector(self):
        """模拟LLM连接器"""
        connector = Mock(spec=LLMConnector)

        # 模拟生成响应
        async def mock_generate_response(messages, config=None):
            return LLMResponse(
                content='''{
                    "overall_impact": {
                        "impact_type": "price_volatility",
                        "timeframe": "immediate",
                        "magnitude": "high",
                        "confidence": 0.85,
                        "probability": 0.8,
                        "direction": "positive",
                        "reasoning": "Significant price movement expected due to market developments",
                        "key_factors": ["increased adoption", "positive sentiment"],
                        "affected_assets": ["Bitcoin", "Ethereum"]
                    },
                    "impact_breakdown": {
                        "price_volatility_immediate": {
                            "magnitude": "high",
                            "confidence": 0.85,
                            "probability": 0.8,
                            "direction": "positive",
                            "reasoning": "Immediate price volatility expected"
                        },
                        "trading_volume_short_term": {
                            "magnitude": "moderate",
                            "confidence": 0.7,
                            "probability": 0.6,
                            "direction": "positive",
                            "reasoning": "Trading volume increase expected"
                        }
                    },
                    "market_sentiment": {
                        "overall": "positive",
                        "confidence": 0.8,
                        "factors": ["bullish indicators", "institutional interest"]
                    },
                    "risk_assessment": {
                        "risk_level": "medium",
                        "factors": ["market volatility", "regulatory uncertainty"],
                        "mitigation": "diversification recommended"
                    },
                    "opportunity_analysis": {
                        "opportunities": ["long positions", "breakout trading"],
                        "confidence": 0.7,
                        "time_horizon": "short-term"
                    },
                    "correlation_analysis": {
                        "correlations": [
                            {"asset": "BTC", "correlation": 0.8, "direction": "positive"},
                            {"asset": "ETH", "correlation": 0.6, "direction": "positive"}
                        ]
                    },
                    "confidence_assessment": {
                        "overall_confidence": 0.8,
                        "reasoning": "Strong market signals and supporting factors"
                    }
                }''',
                usage={"total_tokens": 300},
                model="test-model",
                provider="mock",
                response_time=1.5
            )

        connector.generate_response = AsyncMock(side_effect=mock_generate_response)
        return connector

    @pytest.fixture
    def sample_article(self):
        """示例文章"""
        return NewsArticle(
            id="test-article-1",
            title="Major Exchange Announces Bitcoin Integration",
            content="A major cryptocurrency exchange announced comprehensive Bitcoin integration, including new trading pairs and institutional services. Market analysts predict significant impact on Bitcoin's adoption and price performance.",
            source="Crypto News",
            category="market_analysis",
            author="Mike Johnson",
            tags=["bitcoin", "exchange", "integration", "adoption"]
        )

    @pytest.fixture
    def sample_sentiment_result(self):
        """示例情感分析结果"""
        return SentimentAnalysisResult(
            overall_sentiment=SentimentScore(
                category=SentimentCategory.POSITIVE,
                score=0.7,
                confidence=0.8,
                explanation="Positive market sentiment detected",
                intensity=0.6
            ),
            aspect_sentiments={},
            market_impact_indicators={},
            temporal_indicators={},
            reliability_score=0.8,
            processing_time=1.0,
            metadata={}
        )

    @pytest.fixture
    def sample_entity_result(self):
        """示例实体提取结果"""
        return EntityExtractionResult(
            entities=[
                Entity(
                    id="bitcoin-1",
                    text="Bitcoin",
                    type=EntityType.CRYPTOCURRENCY,
                    start_position=0,
                    end_position=7,
                    confidence=0.9
                ),
                Entity(
                    id="exchange-1",
                    text="exchange",
                    type=EntityType.EXCHANGE,
                    start_position=25,
                    end_position=33,
                    confidence=0.8
                )
            ],
            relationships=[],
            entity_types_count={"cryptocurrency": 1, "exchange": 1},
            processing_time=1.2,
            metadata={}
        )

    def test_init(self, mock_llm_connector):
        """测试初始化"""
        config = MarketImpactConfig()
        assessor = MarketImpactAssessor(mock_llm_connector, config)

        assert assessor.llm_connector == mock_llm_connector
        assert assessor.config == config
        assert assessor.stats.total_analyses == 0
        assert assessor.stats.successful_analyses == 0
        assert assessor.stats.failed_analyses == 0

        # 检查统计初始化
        for impact_type in ImpactType:
            assert assessor.stats.impact_type_distribution[impact_type.value] == 0
        for magnitude in ImpactMagnitude:
            assert assessor.stats.magnitude_distribution[magnitude.value] == 0

        # 检查影响权重
        assert "sentiment_strength" in assessor.impact_weights
        assert "entity_relevance" in assessor.impact_weights
        assert assessor.impact_weights["sentiment_strength"] == 0.25

    def test_create_system_prompt(self):
        """测试系统提示创建"""
        config = MarketImpactConfig()
        llm_connector = Mock(spec=LLMConnector)
        assessor = MarketImpactAssessor(llm_connector, config)

        prompt = assessor._create_system_prompt()
        assert "market impact analyst" in prompt.lower()
        assert "cryptocurrency" in prompt.lower()
        assert "impact analysis framework" in prompt.lower()
        assert "price volatility" in prompt.lower()
        assert "trading volume" in prompt.lower()
        assert "risk assessment" in prompt.lower()

    def test_create_user_prompt(self, sample_article):
        """测试用户提示创建"""
        config = MarketImpactConfig()
        llm_connector = Mock(spec=LLMConnector)
        assessor = MarketImpactAssessor(llm_connector, config)

        prompt = assessor._create_user_prompt(sample_article)
        assert sample_article.title in prompt
        assert sample_article.content in prompt
        assert sample_article.source in prompt
        assert sample_article.category.value in prompt
        assert "bitcoin, exchange, integration, adoption" in prompt

    def test_create_user_prompt_with_sentiment_and_entities(self, sample_article, sample_sentiment_result, sample_entity_result):
        """测试带情感和实体数据的用户提示创建"""
        config = MarketImpactConfig()
        llm_connector = Mock(spec=LLMConnector)
        assessor = MarketImpactAssessor(llm_connector, config)

        prompt = assessor._create_user_prompt(sample_article, sample_sentiment_result, sample_entity_result)
        assert "Sentiment Analysis:" in prompt
        assert "positive" in prompt
        assert "Key Entities:" in prompt
        assert "cryptocurrency: Bitcoin" in prompt

    def test_parse_impact_response_json(self):
        """测试JSON响应解析"""
        config = MarketImpactConfig()
        llm_connector = Mock(spec=LLMConnector)
        assessor = MarketImpactAssessor(llm_connector, config)

        json_response = '''{
            "overall_impact": {
                "impact_type": "price_volatility",
                "timeframe": "immediate",
                "magnitude": "high",
                "confidence": 0.9,
                "probability": 0.8,
                "direction": "positive"
            },
            "impact_breakdown": {},
            "market_sentiment": {"overall": "positive"}
        }'''

        result = assessor._parse_impact_response(json_response)
        assert result["overall_impact"]["magnitude"] == "high"
        assert result["overall_impact"]["confidence"] == 0.9
        assert result["market_sentiment"]["overall"] == "positive"

    def test_basic_impact_analysis(self):
        """测试基础市场影响分析"""
        config = MarketImpactConfig()
        llm_connector = Mock(spec=LLMConnector)
        assessor = MarketImpactAssessor(llm_connector, config)

        content = "Breaking: Major announcement with unprecedented market impact expected"
        result = assessor._basic_impact_analysis(content)

        assert "overall_impact" in result
        assert result["overall_impact"]["magnitude"] == "extreme"
        assert result["overall_impact"]["direction"] == "positive"
        assert "market_sentiment" in result
        assert "risk_assessment" in result

    def test_create_impact_score(self):
        """测试创建影响分数对象"""
        config = MarketImpactConfig()
        llm_connector = Mock(spec=LLMConnector)
        assessor = MarketImpactAssessor(llm_connector, config)

        impact_data = {
            "magnitude": "high",
            "timeframe": "short_term",
            "confidence": 0.85,
            "probability": 0.8,
            "direction": "positive",
            "reasoning": "Strong positive impact expected",
            "key_factors": ["adoption", "sentiment"],
            "affected_assets": ["Bitcoin"]
        }

        score = assessor._create_impact_score(impact_data, ImpactType.PRICE_VOLATILITY, ImpactTimeframe.SHORT_TERM)
        assert score.impact_type == ImpactType.PRICE_VOLATILITY
        assert score.timeframe == ImpactTimeframe.SHORT_TERM
        assert score.magnitude == ImpactMagnitude.HIGH
        assert score.confidence == 0.85
        assert score.probability == 0.8
        assert score.direction == "positive"
        assert len(score.key_factors) == 2
        assert "adoption" in score.key_factors
        assert score.risk_level == "high"  # 高程度+高置信度=高风险

    @pytest.mark.asyncio
    async def test_assess_market_impact(self, mock_llm_connector, sample_article):
        """测试市场影响评估"""
        config = MarketImpactConfig()
        assessor = MarketImpactAssessor(mock_llm_connector, config)

        result = await assessor.assess_market_impact(sample_article)

        assert isinstance(result, MarketImpactResult)
        assert result.overall_impact.magnitude == ImpactMagnitude.HIGH
        assert result.overall_impact.confidence > 0
        assert len(result.impact_breakdown) > 0
        assert "market_sentiment" in result.market_sentiment
        assert "risk_assessment" in result.risk_assessment
        assert "opportunity_analysis" in result.opportunity_analysis
        assert result.processing_time > 0

    @pytest.mark.asyncio
    async def test_assess_market_impact_with_sentiment_and_entities(self, mock_llm_connector, sample_article, sample_sentiment_result, sample_entity_result):
        """测试带情感和实体数据的市场影响评估"""
        config = MarketImpactConfig()
        assessor = MarketImpactAssessor(mock_llm_connector, config)

        result = await assessor.assess_market_impact(sample_article, sample_sentiment_result, sample_entity_result)

        assert isinstance(result, MarketImpactResult)
        assert result.overall_impact.confidence > 0

    @pytest.mark.asyncio
    async def test_assess_market_impact_error_handling(self, mock_llm_connector, sample_article):
        """测试市场影响评估错误处理"""
        config = MarketImpactConfig()
        assessor = MarketImpactAssessor(mock_llm_connector, config)

        # 模拟LLM错误
        mock_llm_connector.generate_response.side_effect = Exception("API Error")

        result = await assessor.assess_market_impact(sample_article)

        assert isinstance(result, MarketImpactResult)
        assert result.overall_impact.magnitude == ImpactMagnitude.NONE
        assert result.overall_impact.confidence == 0.0
        assert "API Error" in result.overall_impact.reasoning
        assert "API Error" in result.metadata.get("error", "")

    @pytest.mark.asyncio
    async def test_assess_batch_market_impact(self, mock_llm_connector):
        """测试批量市场影响评估"""
        config = MarketImpactConfig()
        assessor = MarketImpactAssessor(mock_llm_connector, config)

        articles = [
            NewsArticle(
                id="article-1",
                title="Article 1",
                content="Bitcoin market analysis content",
                source="Test"
            ),
            NewsArticle(
                id="article-2",
                title="Article 2",
                content="Ethereum market analysis content",
                source="Test"
            )
        ]

        results = await assessor.assess_batch_market_impact(articles)

        assert len(results) == 2
        for result in results:
            assert isinstance(result, MarketImpactResult)
            assert result.overall_impact is not None

    def test_update_stats(self):
        """测试统计更新"""
        config = MarketImpactConfig()
        llm_connector = Mock(spec=LLMConnector)
        assessor = MarketImpactAssessor(llm_connector, config)

        # 创建测试结果
        result = MarketImpactResult(
            overall_impact=ImpactScore(
                impact_type=ImpactType.PRICE_VOLATILITY,
                timeframe=ImpactTimeframe.IMMEDIATE,
                magnitude=ImpactMagnitude.HIGH,
                confidence=0.8,
                probability=0.7,
                direction="positive",
                reasoning="Test impact"
            ),
            impact_breakdown={
                ImpactType.PRICE_VOLATILITY: [
                    ImpactScore(
                        impact_type=ImpactType.PRICE_VOLATILITY,
                        timeframe=ImpactTimeframe.IMMEDIATE,
                        magnitude=ImpactMagnitude.HIGH,
                        confidence=0.8,
                        probability=0.7,
                        direction="positive",
                        reasoning="Test breakdown"
                    )
                ]
            },
            market_sentiment={},
            risk_assessment={},
            opportunity_analysis={},
            correlation_analysis={},
            processing_time=1.5,
            metadata={}
        )

        assessor._update_stats(result)

        assert assessor.stats.impact_type_distribution["price_volatility"] == 1
        assert assessor.stats.magnitude_distribution["high"] == 1
        assert assessor.stats.average_processing_time == 1.5
        assert assessor.stats.average_confidence_score == 0.8

    def test_get_stats(self):
        """测试获取统计信息"""
        config = MarketImpactConfig()
        llm_connector = Mock(spec=LLMConnector)
        assessor = MarketImpactAssessor(llm_connector, config)

        stats = assessor.get_stats()
        assert "total_analyses" in stats
        assert "successful_analyses" in stats
        assert "failed_analyses" in stats
        assert "success_rate" in stats
        assert "average_processing_time" in stats
        assert "average_confidence_score" in stats
        assert "high_impact_articles" in stats
        assert "high_impact_rate" in stats
        assert "impact_type_distribution" in stats
        assert "magnitude_distribution" in stats
        assert "config" in stats

    def test_get_market_impact_summary(self):
        """测试获取市场影响摘要"""
        config = MarketImpactConfig()
        llm_connector = Mock(spec=LLMConnector)
        assessor = MarketImpactAssessor(llm_connector, config)

        # 创建测试结果
        results = [
            MarketImpactResult(
                overall_impact=ImpactScore(
                    impact_type=ImpactType.PRICE_VOLATILITY,
                    timeframe=ImpactTimeframe.IMMEDIATE,
                    magnitude=ImpactMagnitude.HIGH,
                    confidence=0.8,
                    probability=0.7,
                    direction="positive",
                    reasoning="High impact"
                ),
                impact_breakdown={},
                market_sentiment={},
                risk_assessment={},
                opportunity_analysis={},
                correlation_analysis={},
                processing_time=1.0,
                metadata={}
            ),
            MarketImpactResult(
                overall_impact=ImpactScore(
                    impact_type=ImpactType.MARKET_SENTIMENT,
                    timeframe=ImpactTimeframe.SHORT_TERM,
                    magnitude=ImpactMagnitude.MODERATE,
                    confidence=0.6,
                    probability=0.5,
                    direction="neutral",
                    reasoning="Moderate impact"
                ),
                impact_breakdown={},
                market_sentiment={},
                risk_assessment={},
                opportunity_analysis={},
                correlation_analysis={},
                processing_time=1.0,
                metadata={}
            )
        ]

        summary = assessor.get_market_impact_summary(results)
        assert summary["total_articles"] == 2
        assert summary["average_confidence"] == 0.7
        assert summary["average_probability"] == 0.6
        assert "magnitude_distribution" in summary
        assert "direction_distribution" in summary
        assert "impact_type_distribution" in summary
        assert summary["dominant_magnitude"] == "high"
        assert summary["high_impact_ratio"] == 0.5

    def test_filter_by_impact_level(self):
        """测试按影响程度过滤"""
        config = MarketImpactConfig()
        llm_connector = Mock(spec=LLMConnector)
        assessor = MarketImpactAssessor(llm_connector, config)

        results = [
            MarketImpactResult(
                overall_impact=ImpactScore(
                    impact_type=ImpactType.PRICE_VOLATILITY,
                    timeframe=ImpactTimeframe.IMMEDIATE,
                    magnitude=ImpactMagnitude.HIGH,
                    confidence=0.8,
                    probability=0.7,
                    direction="positive",
                    reasoning="High impact"
                ),
                impact_breakdown={},
                market_sentiment={},
                risk_assessment={},
                opportunity_analysis={},
                correlation_analysis={},
                processing_time=1.0,
                metadata={}
            ),
            MarketImpactResult(
                overall_impact=ImpactScore(
                    impact_type=ImpactType.MARKET_SENTIMENT,
                    timeframe=ImpactTimeframe.SHORT_TERM,
                    magnitude=ImpactMagnitude.LOW,
                    confidence=0.6,
                    probability=0.5,
                    direction="neutral",
                    reasoning="Low impact"
                ),
                impact_breakdown={},
                market_sentiment={},
                risk_assessment={},
                opportunity_analysis={},
                correlation_analysis={},
                processing_time=1.0,
                metadata={}
            )
        ]

        high_impact_results = assessor.filter_by_impact_level(results, ImpactMagnitude.MODERATE)
        assert len(high_impact_results) == 1
        assert high_impact_results[0].overall_impact.magnitude == ImpactMagnitude.HIGH

    def test_filter_by_confidence(self):
        """测试按置信度过滤"""
        config = MarketImpactConfig()
        llm_connector = Mock(spec=LLMConnector)
        assessor = MarketImpactAssessor(llm_connector, config)

        results = [
            MarketImpactResult(
                overall_impact=ImpactScore(
                    impact_type=ImpactType.PRICE_VOLATILITY,
                    timeframe=ImpactTimeframe.IMMEDIATE,
                    magnitude=ImpactMagnitude.HIGH,
                    confidence=0.8,
                    probability=0.7,
                    direction="positive",
                    reasoning="High confidence"
                ),
                impact_breakdown={},
                market_sentiment={},
                risk_assessment={},
                opportunity_analysis={},
                correlation_analysis={},
                processing_time=1.0,
                metadata={}
            ),
            MarketImpactResult(
                overall_impact=ImpactScore(
                    impact_type=ImpactType.MARKET_SENTIMENT,
                    timeframe=ImpactTimeframe.SHORT_TERM,
                    magnitude=ImpactMagnitude.MODERATE,
                    confidence=0.4,
                    probability=0.3,
                    direction="neutral",
                    reasoning="Low confidence"
                ),
                impact_breakdown={},
                market_sentiment={},
                risk_assessment={},
                opportunity_analysis={},
                correlation_analysis={},
                processing_time=1.0,
                metadata={}
            )
        ]

        high_conf_results = assessor.filter_by_confidence(results, 0.7)
        assert len(high_conf_results) == 1
        assert high_conf_results[0].overall_impact.confidence == 0.8

    def test_get_risk_alerts(self):
        """测试获取风险警报"""
        config = MarketImpactConfig()
        llm_connector = Mock(spec=LLMConnector)
        assessor = MarketImpactAssessor(llm_connector, config)

        results = [
            MarketImpactResult(
                overall_impact=ImpactScore(
                    impact_type=ImpactType.PRICE_VOLATILITY,
                    timeframe=ImpactTimeframe.IMMEDIATE,
                    magnitude=ImpactMagnitude.HIGH,
                    confidence=0.8,
                    probability=0.7,
                    direction="negative",
                    reasoning="High risk"
                ),
                impact_breakdown={},
                market_sentiment={},
                risk_assessment={"factors": ["market volatility"]},
                opportunity_analysis={},
                correlation_analysis={},
                processing_time=1.0,
                metadata={"article_id": "test-1"}
            ),
            MarketImpactResult(
                overall_impact=ImpactScore(
                    impact_type=ImpactType.MARKET_SENTIMENT,
                    timeframe=ImpactTimeframe.SHORT_TERM,
                    magnitude=ImpactMagnitude.LOW,
                    confidence=0.4,
                    probability=0.3,
                    direction="neutral",
                    reasoning="Low risk"
                ),
                impact_breakdown={},
                market_sentiment={},
                risk_assessment={},
                opportunity_analysis={},
                correlation_analysis={},
                processing_time=1.0,
                metadata={"article_id": "test-2"}
            )
        ]

        alerts = assessor.get_risk_alerts(results)
        assert len(alerts) == 1
        assert alerts[0]["article_id"] == "test-1"
        assert alerts[0]["impact_level"] == "high"
        assert alerts[0]["confidence"] == 0.8
        assert alerts[0]["direction"] == "negative"

    def test_generate_risk_recommendation(self):
        """测试生成风险建议"""
        config = MarketImpactConfig()
        llm_connector = Mock(spec=LLMConnector)
        assessor = MarketImpactAssessor(llm_connector, config)

        # 测试负面影响
        negative_result = MarketImpactResult(
            overall_impact=ImpactScore(
                impact_type=ImpactType.PRICE_VOLATILITY,
                timeframe=ImpactTimeframe.IMMEDIATE,
                magnitude=ImpactMagnitude.HIGH,
                confidence=0.8,
                probability=0.7,
                direction="negative",
                reasoning="Negative impact"
            ),
            impact_breakdown={},
            market_sentiment={},
            risk_assessment={},
            opportunity_analysis={},
            correlation_analysis={},
            processing_time=1.0,
            metadata={}
        )

        rec = assessor._generate_risk_recommendation(negative_result)
        assert "defensive" in rec.lower() or "reduced" in rec.lower()

        # 测试正面影响
        positive_result = MarketImpactResult(
            overall_impact=ImpactScore(
                impact_type=ImpactType.PRICE_VOLATILITY,
                timeframe=ImpactTimeframe.IMMEDIATE,
                magnitude=ImpactMagnitude.HIGH,
                confidence=0.8,
                probability=0.7,
                direction="positive",
                reasoning="Positive impact"
            ),
            impact_breakdown={},
            market_sentiment={},
            risk_assessment={},
            opportunity_analysis={},
            correlation_analysis={},
            processing_time=1.0,
            metadata={}
        )

        rec = assessor._generate_risk_recommendation(positive_result)
        assert "opportunities" in rec.lower() or "caution" in rec.lower()

    def test_validate_article(self):
        """测试文章验证"""
        config = MarketImpactConfig()
        llm_connector = Mock(spec=LLMConnector)
        assessor = MarketImpactAssessor(llm_connector, config)

        # 有效文章
        valid_article = NewsArticle(
            id="valid-article",
            title="Valid Market Impact Article",
            content="This is a valid article content with sufficient length for comprehensive market impact analysis including various factors and considerations.",
            source="Test"
        )
        assert assessor.validate_article(valid_article) is True

        # 内容太短的文章
        short_content_article = NewsArticle(
            id="short-content",
            title="Short Content",
            content="Short content",
            source="Test"
        )
        assert assessor.validate_article(short_content_article) is False

    def test_update_config(self):
        """测试配置更新"""
        config = MarketImpactConfig()
        llm_connector = Mock(spec=LLMConnector)
        assessor = MarketImpactAssessor(llm_connector, config)

        new_config = MarketImpactConfig(
            enable_multi_factor_analysis=False,
            min_confidence_threshold=0.8
        )

        assessor.update_config(new_config)
        assert assessor.config.enable_multi_factor_analysis is False
        assert assessor.config.min_confidence_threshold == 0.8


if __name__ == "__main__":
    pytest.main([__file__])