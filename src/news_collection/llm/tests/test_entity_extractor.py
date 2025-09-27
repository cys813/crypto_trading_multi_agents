"""
Tests for entity extractor module
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch

from ..entity_extractor import (
    EntityExtractor, EntityConfig, EntityExtractionResult, Entity,
    EntityRelationship, EntityType, EntityConfidence, EntityExtractionStats
)
from ..llm_connector import LLMConnector, LLMConfig, LLMMessage, LLMResponse
from ...models.base import NewsArticle


class TestEntityConfig:
    """测试实体提取配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = EntityConfig()
        assert config.enable_entity_linking is True
        assert config.enable_relationship_extraction is True
        assert config.enable_entity_disambiguation is True
        assert config.enable_sentiment_association is True
        assert len(config.prioritize_entity_types) == 4
        assert EntityType.CRYPTOCURRENCY in config.prioritize_entity_types
        assert EntityType.COMPANY in config.prioritize_entity_types
        assert config.max_entities_per_article == 50
        assert config.min_entity_confidence == 0.3
        assert config.include_entity_metadata is True
        assert config.include_entity_context is True
        assert config.language == "en"
        assert config.output_format == "structured"

    def test_custom_config(self):
        """测试自定义配置"""
        config = EntityConfig(
            enable_entity_linking=False,
            enable_relationship_extraction=False,
            prioritize_entity_types=[EntityType.CRYPTOCURRENCY],
            max_entities_per_article=30,
            min_entity_confidence=0.5,
            language="zh"
        )
        assert config.enable_entity_linking is False
        assert config.enable_relationship_extraction is False
        assert len(config.prioritize_entity_types) == 1
        assert EntityType.CRYPTOCURRENCY in config.prioritize_entity_types
        assert config.max_entities_per_article == 30
        assert config.min_entity_confidence == 0.5
        assert config.language == "zh"


class TestEntity:
    """测试实体类"""

    def test_entity_creation(self):
        """测试实体创建"""
        entity = Entity(
            id="bitcoin-1",
            text="Bitcoin",
            type=EntityType.CRYPTOCURRENCY,
            start_position=10,
            end_position=17,
            confidence=0.9,
            normalized_form="Bitcoin"
        )
        assert entity.id == "bitcoin-1"
        assert entity.text == "Bitcoin"
        assert entity.type == EntityType.CRYPTOCURRENCY
        assert entity.start_position == 10
        assert entity.end_position == 17
        assert entity.confidence == 0.9
        assert entity.normalized_form == "Bitcoin"
        assert entity.aliases == []
        assert entity.metadata == {}
        assert entity.sentiment == {}
        assert entity.relationships == []

    def test_entity_with_additional_data(self):
        """测试带额外数据的实体"""
        entity = Entity(
            id="coinbase-1",
            text="Coinbase",
            type=EntityType.COMPANY,
            start_position=25,
            end_position=32,
            confidence=0.85,
            normalized_form="Coinbase",
            aliases=["Coinbase Global"],
            description="Cryptocurrency exchange",
            metadata={"market_cap": "large", "country": "US"},
            context="Coinbase announced new features",
            sentiment={"positive": 0.7, "neutral": 0.3},
            relationships=[{"relation": "operates", "object": "exchange"}]
        )
        assert entity.aliases == ["Coinbase Global"]
        assert entity.description == "Cryptocurrency exchange"
        assert entity.metadata["market_cap"] == "large"
        assert entity.context == "Coinbase announced new features"
        assert entity.sentiment["positive"] == 0.7
        assert entity.relationships[0]["relation"] == "operates"


class TestEntityRelationship:
    """测试实体关系类"""

    def test_relationship_creation(self):
        """测试关系创建"""
        relationship = EntityRelationship(
            subject="Bitcoin",
            object="Coinbase",
            relation="traded_on",
            confidence=0.8,
            context="Bitcoin is traded on Coinbase",
            metadata={"relationship_type": "trading"}
        )
        assert relationship.subject == "Bitcoin"
        assert relationship.object == "Coinbase"
        assert relationship.relation == "traded_on"
        assert relationship.confidence == 0.8
        assert relationship.context == "Bitcoin is traded on Coinbase"
        assert relationship.metadata["relationship_type"] == "trading"


class TestEntityExtractionResult:
    """测试实体提取结果类"""

    def test_result_creation(self):
        """测试结果创建"""
        entities = [
            Entity(
                id="btc-1",
                text="Bitcoin",
                type=EntityType.CRYPTOCURRENCY,
                start_position=0,
                end_position=7,
                confidence=0.9
            )
        ]
        relationships = [
            EntityRelationship(
                subject="Bitcoin",
                object="Coinbase",
                relation="traded_on",
                confidence=0.8
            )
        ]

        result = EntityExtractionResult(
            entities=entities,
            relationships=relationships,
            entity_types_count={"cryptocurrency": 1},
            processing_time=1.5,
            metadata={"test": "data"}
        )

        assert len(result.entities) == 1
        assert len(result.relationships) == 1
        assert result.entity_types_count["cryptocurrency"] == 1
        assert result.processing_time == 1.5
        assert result.metadata["test"] == "data"


class TestEntityExtractor:
    """测试实体提取器"""

    @pytest.fixture
    def mock_llm_connector(self):
        """模拟LLM连接器"""
        connector = Mock(spec=LLMConnector)

        # 模拟生成响应
        async def mock_generate_response(messages, config=None):
            return LLMResponse(
                content='''{
                    "entities": [
                        {
                            "id": "entity_1",
                            "text": "Bitcoin",
                            "type": "cryptocurrency",
                            "start_position": 0,
                            "end_position": 7,
                            "confidence": 0.9,
                            "normalized_form": "Bitcoin",
                            "context": "Bitcoin shows strong performance",
                            "aliases": ["BTC"],
                            "description": "Leading cryptocurrency",
                            "metadata": {"symbol": "BTC"}
                        },
                        {
                            "id": "entity_2",
                            "text": "Coinbase",
                            "type": "company",
                            "start_position": 25,
                            "end_position": 32,
                            "confidence": 0.85,
                            "normalized_form": "Coinbase",
                            "context": "Coinbase exchange platform"
                        }
                    ],
                    "relationships": [
                        {
                            "subject": "Bitcoin",
                            "object": "Coinbase",
                            "relation": "traded_on",
                            "confidence": 0.8,
                            "context": "Bitcoin is traded on Coinbase"
                        }
                    ],
                    "entity_stats": {
                        "total_entities": 2,
                        "extraction_method": "llm_based"
                    },
                    "extraction_summary": {
                        "key_findings": ["Found Bitcoin and Coinbase entities"]
                    }
                }''',
                usage={"total_tokens": 200},
                model="test-model",
                provider="mock",
                response_time=1.2
            )

        connector.generate_response = AsyncMock(side_effect=mock_generate_response)
        return connector

    @pytest.fixture
    def sample_article(self):
        """示例文章"""
        return NewsArticle(
            id="test-article-1",
            title="Bitcoin Shows Strong Performance on Coinbase",
            content="Bitcoin shows strong performance as trading volume increases on Coinbase exchange. The leading cryptocurrency demonstrates resilience in current market conditions.",
            source="Crypto News",
            category="market_analysis",
            author="Jane Smith",
            tags=["bitcoin", "coinbase", "trading"]
        )

    def test_init(self, mock_llm_connector):
        """测试初始化"""
        config = EntityConfig()
        extractor = EntityExtractor(mock_llm_connector, config)

        assert extractor.llm_connector == mock_llm_connector
        assert extractor.config == config
        assert extractor.stats.total_articles == 0
        assert extractor.stats.successful_extractions == 0
        assert extractor.stats.failed_extractions == 0

        # 检查统计初始化
        for entity_type in EntityType:
            assert extractor.stats.entity_type_distribution[entity_type.value] == 0

        # 检查关键词集
        assert 'bitcoin' in extractor.crypto_keywords
        assert 'coinbase' in extractor.company_keywords
        assert 'blockchain' in extractor.technology_keywords

    def test_create_system_prompt(self):
        """测试系统提示创建"""
        config = EntityConfig()
        llm_connector = Mock(spec=LLMConnector)
        extractor = EntityExtractor(llm_connector, config)

        prompt = extractor._create_system_prompt()
        assert "entity extraction" in prompt.lower()
        assert "cryptocurrency" in prompt.lower()
        assert "financial news" in prompt.lower()
        assert "entity types" in prompt.lower()
        assert "extraction requirements" in prompt.lower()

    def test_create_user_prompt(self, sample_article):
        """测试用户提示创建"""
        config = EntityConfig()
        llm_connector = Mock(spec=LLMConnector)
        extractor = EntityExtractor(llm_connector, config)

        prompt = extractor._create_user_prompt(sample_article)
        assert sample_article.title in prompt
        assert sample_article.content in prompt
        assert sample_article.source in prompt
        assert sample_article.category.value in prompt
        assert "bitcoin, coinbase, trading" in prompt

    def test_parse_entity_response_json(self):
        """测试JSON响应解析"""
        config = EntityConfig()
        llm_connector = Mock(spec=LLMConnector)
        extractor = EntityExtractor(llm_connector, config)

        json_response = '''{
            "entities": [
                {
                    "id": "entity_1",
                    "text": "Ethereum",
                    "type": "cryptocurrency",
                    "confidence": 0.9
                }
            ],
            "relationships": []
        }'''

        result = extractor._parse_entity_response(json_response)
        assert len(result["entities"]) == 1
        assert result["entities"][0]["text"] == "Ethereum"
        assert result["entities"][0]["type"] == "cryptocurrency"

    def test_basic_entity_extraction(self):
        """测试基础实体提取"""
        config = EntityConfig()
        llm_connector = Mock(spec=LLMConnector)
        extractor = EntityExtractor(llm_connector, config)

        content = "Bitcoin and Ethereum are popular cryptocurrencies. Coinbase is a major exchange."
        result = extractor._basic_entity_extraction(content)

        assert "entities" in result
        assert len(result["entities"]) > 0

        # 检查是否找到预期实体
        entities = result["entities"]
        entity_texts = [entity["text"] for entity in entities]
        assert any("bitcoin" in text.lower() for text in entity_texts)
        assert any("coinbase" in text.lower() for text in entity_texts)

    def test_find_all_positions(self):
        """测试查找所有位置"""
        config = EntityConfig()
        llm_connector = Mock(spec=LLMConnector)
        extractor = EntityExtractor(llm_connector, config)

        text = "Bitcoin is popular. Bitcoin is valuable. Bitcoin is digital."
        positions = extractor._find_all_positions(text, "Bitcoin")

        assert len(positions) == 3
        assert positions[0] == 0
        assert positions[1] == 17
        assert positions[2] == 36

    def test_get_context(self):
        """测试获取上下文"""
        config = EntityConfig()
        llm_connector = Mock(spec=LLMConnector)
        extractor = EntityExtractor(llm_connector, config)

        text = "This is a long text with Bitcoin in the middle of the sentence."
        start = text.find("Bitcoin")
        end = start + len("Bitcoin")

        context = extractor._get_context(text, start, end, context_size=20)
        assert "Bitcoin" in context
        assert len(context) <= 50  # Bitcoin (7) + 20*2

    def test_create_entity(self):
        """测试创建实体对象"""
        config = EntityConfig()
        llm_connector = Mock(spec=LLMConnector)
        extractor = EntityExtractor(llm_connector, config)

        entity_data = {
            "id": "test-entity",
            "text": "Bitcoin",
            "type": "cryptocurrency",
            "start_position": 0,
            "end_position": 7,
            "confidence": 0.9,
            "normalized_form": "Bitcoin",
            "aliases": ["BTC"],
            "description": "Leading cryptocurrency",
            "metadata": {"symbol": "BTC"},
            "context": "Bitcoin context",
            "sentiment": {"positive": 0.8}
        }

        entity = extractor._create_entity(entity_data)
        assert entity.id == "test-entity"
        assert entity.text == "Bitcoin"
        assert entity.type == EntityType.CRYPTOCURRENCY
        assert entity.confidence == 0.9
        assert entity.aliases == ["BTC"]
        assert entity.sentiment["positive"] == 0.8

    @pytest.mark.asyncio
    async def test_extract_entities(self, mock_llm_connector, sample_article):
        """测试实体提取"""
        config = EntityConfig()
        extractor = EntityExtractor(mock_llm_connector, config)

        result = await extractor.extract_entities(sample_article)

        assert isinstance(result, EntityExtractionResult)
        assert len(result.entities) > 0
        assert len(result.relationships) > 0
        assert result.processing_time > 0
        assert "cryptocurrency" in result.entity_types_count
        assert "company" in result.entity_types_count

        # 检查实体详情
        bitcoin_entity = next((e for e in result.entities if e.text == "Bitcoin"), None)
        assert bitcoin_entity is not None
        assert bitcoin_entity.type == EntityType.CRYPTOCURRENCY
        assert bitcoin_entity.confidence > 0

    @pytest.mark.asyncio
    async def test_extract_entities_error_handling(self, mock_llm_connector, sample_article):
        """测试实体提取错误处理"""
        config = EntityConfig()
        extractor = EntityExtractor(mock_llm_connector, config)

        # 模拟LLM错误
        mock_llm_connector.generate_response.side_effect = Exception("API Error")

        result = await extractor.extract_entities(sample_article)

        assert isinstance(result, EntityExtractionResult)
        assert len(result.entities) == 0
        assert len(result.relationships) == 0
        assert "API Error" in result.metadata.get("error", "")

    @pytest.mark.asyncio
    async def test_extract_batch_entities(self, mock_llm_connector):
        """测试批量实体提取"""
        config = EntityConfig()
        extractor = EntityExtractor(mock_llm_connector, config)

        articles = [
            NewsArticle(
                id="article-1",
                title="Article 1",
                content="Bitcoin content",
                source="Test"
            ),
            NewsArticle(
                id="article-2",
                title="Article 2",
                content="Ethereum content",
                source="Test"
            )
        ]

        results = await extractor.extract_batch_entities(articles)

        assert len(results) == 2
        for result in results:
            assert isinstance(result, EntityExtractionResult)
            assert result.entities is not None

    def test_update_stats(self):
        """测试统计更新"""
        config = EntityConfig()
        llm_connector = Mock(spec=LLMConnector)
        extractor = EntityExtractor(llm_connector, config)

        # 创建测试结果
        result = EntityExtractionResult(
            entities=[
                Entity(
                    id="btc-1",
                    text="Bitcoin",
                    type=EntityType.CRYPTOCURRENCY,
                    start_position=0,
                    end_position=7,
                    confidence=0.9
                ),
                Entity(
                    id="coinbase-1",
                    text="Coinbase",
                    type=EntityType.COMPANY,
                    start_position=25,
                    end_position=32,
                    confidence=0.85
                )
            ],
            relationships=[
                EntityRelationship(
                    subject="Bitcoin",
                    object="Coinbase",
                    relation="traded_on",
                    confidence=0.8
                )
            ],
            entity_types_count={"cryptocurrency": 1, "company": 1},
            processing_time=1.0,
            metadata={}
        )

        extractor._update_stats(result)

        assert extractor.stats.entity_type_distribution["cryptocurrency"] == 1
        assert extractor.stats.entity_type_distribution["company"] == 1
        assert extractor.stats.average_entities_per_article == 2.0
        assert extractor.stats.total_relationships_extracted == 1
        assert extractor.stats.average_confidence_score > 0

    def test_get_stats(self):
        """测试获取统计信息"""
        config = EntityConfig()
        llm_connector = Mock(spec=LLMConnector)
        extractor = EntityExtractor(llm_connector, config)

        stats = extractor.get_stats()
        assert "total_articles" in stats
        assert "successful_extractions" in stats
        assert "failed_extractions" in stats
        assert "success_rate" in stats
        assert "average_processing_time" in stats
        assert "average_entities_per_article" in stats
        assert "average_confidence_score" in stats
        assert "total_relationships_extracted" in stats
        assert "entity_type_distribution" in stats
        assert "config" in stats

    def test_get_entity_summary(self):
        """测试获取实体摘要"""
        config = EntityConfig()
        llm_connector = Mock(spec=LLMConnector)
        extractor = EntityExtractor(llm_connector, config)

        # 创建测试结果
        results = [
            EntityExtractionResult(
                entities=[
                    Entity(
                        id="btc-1",
                        text="Bitcoin",
                        type=EntityType.CRYPTOCURRENCY,
                        start_position=0,
                        end_position=7,
                        confidence=0.9
                    )
                ],
                relationships=[],
                entity_types_count={"cryptocurrency": 1},
                processing_time=1.0,
                metadata={}
            ),
            EntityExtractionResult(
                entities=[
                    Entity(
                        id="eth-1",
                        text="Ethereum",
                        type=EntityType.CRYPTOCURRENCY,
                        start_position=0,
                        end_position=8,
                        confidence=0.85
                    )
                ],
                relationships=[],
                entity_types_count={"cryptocurrency": 1},
                processing_time=1.0,
                metadata={}
            )
        ]

        summary = extractor.get_entity_summary(results)
        assert summary["total_articles"] == 2
        assert summary["total_entities"] == 2
        assert summary["average_entities_per_article"] == 1.0
        assert "cryptocurrency" in summary["entity_type_distribution"]
        assert len(summary["top_entities"]) > 0

    def test_filter_entities_by_type(self):
        """测试按类型过滤实体"""
        entities = [
            Entity(
                id="btc-1",
                text="Bitcoin",
                type=EntityType.CRYPTOCURRENCY,
                start_position=0,
                end_position=7,
                confidence=0.9
            ),
            Entity(
                id="coinbase-1",
                text="Coinbase",
                type=EntityType.COMPANY,
                start_position=25,
                end_position=32,
                confidence=0.85
            )
        ]

        config = EntityConfig()
        llm_connector = Mock(spec=LLMConnector)
        extractor = EntityExtractor(llm_connector, config)

        crypto_entities = extractor.filter_entities_by_type(entities, [EntityType.CRYPTOCURRENCY])
        assert len(crypto_entities) == 1
        assert crypto_entities[0].type == EntityType.CRYPTOCURRENCY

    def test_filter_entities_by_confidence(self):
        """测试按置信度过滤实体"""
        entities = [
            Entity(
                id="high-confidence",
                text="High",
                type=EntityType.CRYPTOCURRENCY,
                start_position=0,
                end_position=4,
                confidence=0.9
            ),
            Entity(
                id="low-confidence",
                text="Low",
                type=EntityType.COMPANY,
                start_position=6,
                end_position=9,
                confidence=0.3
            )
        ]

        config = EntityConfig()
        llm_connector = Mock(spec=LLMConnector)
        extractor = EntityExtractor(llm_connector, config)

        high_conf_entities = extractor.filter_entities_by_confidence(entities, 0.8)
        assert len(high_conf_entities) == 1
        assert high_conf_entities[0].confidence >= 0.8

    def test_get_entity_context(self):
        """测试获取实体上下文"""
        entity = Entity(
            id="test",
            text="Bitcoin",
            type=EntityType.CRYPTOCURRENCY,
            start_position=20,
            end_position=27,
            confidence=0.9
        )

        content = "This is a test string with Bitcoin in the middle for context testing."
        config = EntityConfig()
        llm_connector = Mock(spec=LLMConnector)
        extractor = EntityExtractor(llm_connector, config)

        context = extractor.get_entity_context(entity, content, context_size=15)
        assert "Bitcoin" in context
        assert "test string" in context
        assert "middle" in context

    def test_validate_article(self):
        """测试文章验证"""
        config = EntityConfig()
        llm_connector = Mock(spec=LLMConnector)
        extractor = EntityExtractor(llm_connector, config)

        # 有效文章
        valid_article = NewsArticle(
            id="valid-article",
            title="Valid Article",
            content="This is a valid article content with sufficient length for entity extraction.",
            source="Test"
        )
        assert extractor.validate_article(valid_article) is True

        # 内容太短的文章
        short_content_article = NewsArticle(
            id="short-content",
            title="Short Content",
            content="Short",
            source="Test"
        )
        assert extractor.validate_article(short_content_article) is False

    def test_update_config(self):
        """测试配置更新"""
        config = EntityConfig()
        llm_connector = Mock(spec=LLMConnector)
        extractor = EntityExtractor(llm_connector, config)

        new_config = EntityConfig(
            enable_entity_linking=False,
            max_entities_per_article=20
        )

        extractor.update_config(new_config)
        assert extractor.config.enable_entity_linking is False
        assert extractor.config.max_entities_per_article == 20


if __name__ == "__main__":
    pytest.main([__file__])