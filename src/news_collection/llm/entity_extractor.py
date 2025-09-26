"""
Entity extraction module for identifying and categorizing entities in news articles
"""

import logging
import time
import json
import re
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from ..models.base import NewsArticle
from .llm_connector import LLMConnector, LLMMessage, LLMConfig, LLMResponse


class EntityType(Enum):
    """实体类型枚举"""
    CRYPTOCURRENCY = "cryptocurrency"
    COMPANY = "company"
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    TECHNOLOGY = "technology"
    PROTOCOL = "protocol"
    EXCHANGE = "exchange"
    WALLET = "wallet"
    REGULATOR = "regulator"
    EVENT = "event"
    PRODUCT = "product"
    SERVICE = "service"
    CONCEPT = "concept"
    METRIC = "metric"
    DATE = "date"
    AMOUNT = "amount"
    PERCENTAGE = "percentage"
    OTHER = "other"


class EntityConfidence(Enum):
    """实体置信度枚举"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class EntityConfig:
    """实体提取配置"""
    enable_entity_linking: bool = True
    enable_relationship_extraction: bool = True
    enable_entity_disambiguation: bool = True
    enable_sentiment_association: bool = True
    prioritize_entity_types: List[EntityType] = field(default_factory=lambda: [
        EntityType.CRYPTOCURRENCY,
        EntityType.COMPANY,
        EntityType.PERSON,
        EntityType.ORGANIZATION
    ])
    max_entities_per_article: int = 50
    min_entity_confidence: float = 0.3
    include_entity_metadata: bool = True
    include_entity_context: bool = True
    language: str = "en"
    output_format: str = "structured"


@dataclass
class Entity:
    """实体对象"""
    id: str
    text: str
    type: EntityType
    start_position: int
    end_position: int
    confidence: float
    normalized_form: Optional[str] = None
    aliases: List[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = None
    context: str = ""
    sentiment: Dict[str, Any] = None
    relationships: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []
        if self.metadata is None:
            self.metadata = {}
        if self.sentiment is None:
            self.sentiment = {}
        if self.relationships is None:
            self.relationships = []


@dataclass
class EntityRelationship:
    """实体关系"""
    subject: str
    object: str
    relation: str
    confidence: float
    context: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class EntityExtractionResult:
    """实体提取结果"""
    entities: List[Entity]
    relationships: List[EntityRelationship]
    entity_types_count: Dict[str, int]
    processing_time: float
    metadata: Dict[str, Any]


@dataclass
class EntityExtractionStats:
    """实体提取统计"""
    total_articles: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    average_processing_time: float = 0.0
    average_entities_per_article: float = 0.0
    entity_type_distribution: Dict[str, int] = field(default_factory=dict)
    total_relationships_extracted: int = 0
    average_confidence_score: float = 0.0


class EntityExtractor:
    """实体提取器"""

    def __init__(self, llm_connector: LLMConnector, config: EntityConfig):
        self.llm_connector = llm_connector
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.stats = EntityExtractionStats()

        # 初始化实体类型分布
        for entity_type in EntityType:
            self.stats.entity_type_distribution[entity_type.value] = 0

        # 预编译正则表达式
        self.word_pattern = re.compile(r'\b\w+\b')
        self.currency_pattern = re.compile(r'\$?\d+(?:,\d{3})*(?:\.\d+)?\s*(?:BTC|ETH|USD|EUR|GBP)?')
        self.percentage_pattern = re.compile(r'\d+(?:\.\d+)?%')

        # 加载实体词汇表（简化版）
        self.crypto_keywords = {
            'bitcoin', 'btc', 'ethereum', 'eth', 'ripple', 'xrp', 'cardano', 'ada',
            'polkadot', 'dot', 'chainlink', 'link', 'litecoin', 'ltc', 'bitcoin cash',
            'bch', 'stellar', 'xlm', 'dogecoin', 'doge', 'polygon', 'matic', 'solana', 'sol'
        }

        self.company_keywords = {
            'coinbase', 'binance', 'kraken', 'gemini', 'circle', 'tether', 'blockchain.com',
            'microstrategy', 'tesla', 'square', 'paypal', 'visa', 'mastercard', 'jpmorgan',
            'goldman sachs', 'morgan stanley', 'fidelity', 'blackrock'
        }

        self.technology_keywords = {
            'blockchain', 'smart contract', 'defi', 'nft', 'web3', 'dao', 'consensus',
            'proof of work', 'proof of stake', 'mining', 'staking', 'yield farming',
            'liquidity pool', 'decentralized', 'centralized', 'cryptography'
        }

    def _create_system_prompt(self) -> str:
        """创建系统提示"""
        system_prompt = """You are an expert entity extraction specialist for cryptocurrency and financial news.

Your task is to identify, categorize, and extract entities from news articles with high precision.

Entity Types to Extract:

1. Cryptocurrency:
   - Bitcoin (BTC), Ethereum (ETH), and other cryptocurrencies
   - Token names, symbols, and variants
   - Stablecoins and their issuers

2. Companies:
   - Crypto exchanges (Binance, Coinbase, Kraken, etc.)
   - Mining companies and hardware manufacturers
   - Financial institutions and banks
   - Technology companies involved in crypto
   - Investment firms and funds

3. People:
   - CEOs, founders, and executives
   - Developers and technical experts
   - Regulators and government officials
   - Investors and influencers
   - Analysts and researchers

4. Organizations:
   - Regulatory bodies (SEC, CFTC, etc.)
   - Industry associations
   - Development foundations
   - Standards organizations
   - Government agencies

5. Locations:
   - Countries, cities, and regions
   - Specific addresses or facilities
   - Geographic regions relevant to crypto

6. Technologies:
   - Blockchain protocols and networks
   - Consensus mechanisms
   - Development frameworks
   - Security technologies
   - Scaling solutions

7. Protocols:
   - DeFi protocols
   - Layer 2 solutions
   - Cross-chain protocols
   - Oracle services
   - Privacy protocols

8. Exchanges:
   - Trading platforms
   - OTC desks
   - Derivatives exchanges
   - NFT marketplaces

9. Regulators:
   - Government regulatory bodies
   - Financial authorities
   - International organizations

10. Events:
    - Conferences and summits
    - Forks and upgrades
    - Launches and releases
    - Regulatory decisions

11. Metrics:
    - Price points and market caps
    - Volume and trading data
    - Adoption metrics
    - Technical indicators

Extraction Requirements:

1. Identify all relevant entities with their exact text positions
2. Categorize entities correctly using the provided types
3. Provide confidence scores for each extraction
4. Extract relationships between entities when possible
5. Normalize entity names to standard forms
6. Include contextual information for each entity
7. Associate sentiment with entities when detectable

Quality Guidelines:
- Prioritize precision over recall (better to miss some than to include wrong ones)
- Ensure entity boundaries are accurate
- Use the most specific entity type available
- Consider context when disambiguating entities
- Extract entities that are relevant to the cryptocurrency domain

Output format: structured JSON

Respond with JSON containing:
- entities: array of entity objects with all required fields
- relationships: array of relationship objects between entities
- entity_stats: object with counts by type and confidence scores
- extraction_summary: object with key findings and insights

Ensure your extraction is:
- Accurate and precise
- Comprehensive within the domain
- Contextually relevant
- Well-structured and formatted"""

        return system_prompt

    def _create_user_prompt(self, article: NewsArticle) -> str:
        """创建用户提示"""
        prompt = f"""Please extract entities from the following news article:

Title: {article.title}
Source: {article.source or 'Unknown'}
Published: {article.published_at or 'Unknown date'}
Category: {article.category.value if article.category else 'General'}
Author: {article.author or 'Unknown'}

Content:
{article.content}

"""

        if article.tags:
            prompt += f"Tags: {', '.join(article.tags)}\n"

        # 添加配置说明
        if self.config.prioritize_entity_types:
            priority_types = [entity_type.value for entity_type in self.config.prioritize_entity_types]
            prompt += f"\nPrioritize these entity types: {', '.join(priority_types)}\n"

        prompt += f"\nMaximum entities to extract: {self.config.max_entities_per_article}\n"
        prompt += f"Minimum confidence threshold: {self.config.min_entity_confidence}\n"

        config_features = []
        if self.config.enable_entity_linking:
            config_features.append("entity linking")
        if self.config.enable_relationship_extraction:
            config_features.append("relationship extraction")
        if self.config.enable_entity_disambiguation:
            config_features.append("entity disambiguation")
        if self.config.enable_sentiment_association:
            config_features.append("sentiment association")

        if config_features:
            prompt += f"\nInclude: {', '.join(config_features)}\n"

        prompt += "\nPlease provide comprehensive entity extraction following the requirements specified."

        return prompt

    def _parse_entity_response(self, response: str) -> Dict[str, Any]:
        """解析实体提取响应"""
        try:
            # 尝试解析JSON
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError:
            # 如果不是有效的JSON，执行基础实体提取
            self.logger.warning("Failed to parse JSON entity response, using basic extraction")
            return self._basic_entity_extraction(response)

    def _basic_entity_extraction(self, content: str) -> Dict[str, Any]:
        """基础实体提取逻辑"""
        entities = []
        entity_id = 0

        # 基于关键词匹配提取实体
        # 加密货币
        for crypto in self.crypto_keywords:
            if crypto.lower() in content.lower():
                positions = self._find_all_positions(content, crypto)
                for pos in positions:
                    entity_id += 1
                    entities.append({
                        "id": f"entity_{entity_id}",
                        "text": crypto,
                        "type": "cryptocurrency",
                        "start_position": pos,
                        "end_position": pos + len(crypto),
                        "confidence": 0.8,
                        "normalized_form": crypto.upper(),
                        "context": self._get_context(content, pos, pos + len(crypto))
                    })

        # 公司
        for company in self.company_keywords:
            if company.lower() in content.lower():
                positions = self._find_all_positions(content, company)
                for pos in positions:
                    entity_id += 1
                    entities.append({
                        "id": f"entity_{entity_id}",
                        "text": company,
                        "type": "company",
                        "start_position": pos,
                        "end_position": pos + len(company),
                        "confidence": 0.7,
                        "normalized_form": company.title(),
                        "context": self._get_context(content, pos, pos + len(company))
                    })

        # 技术
        for tech in self.technology_keywords:
            if tech.lower() in content.lower():
                positions = self._find_all_positions(content, tech)
                for pos in positions:
                    entity_id += 1
                    entities.append({
                        "id": f"entity_{entity_id}",
                        "text": tech,
                        "type": "technology",
                        "start_position": pos,
                        "end_position": pos + len(tech),
                        "confidence": 0.6,
                        "normalized_form": tech.lower(),
                        "context": self._get_context(content, pos, pos + len(tech))
                    })

        return {
            "entities": entities[:self.config.max_entities_per_article],
            "relationships": [],
            "entity_stats": {
                "total_entities": len(entities),
                "extraction_method": "keyword_based"
            }
        }

    def _find_all_positions(self, text: str, search_term: str) -> List[int]:
        """查找所有匹配位置"""
        positions = []
        text_lower = text.lower()
        search_lower = search_term.lower()
        start = 0

        while True:
            pos = text_lower.find(search_lower, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1

        return positions

    def _get_context(self, text: str, start: int, end: int, context_size: int = 100) -> str:
        """获取实体上下文"""
        context_start = max(0, start - context_size)
        context_end = min(len(text), end + context_size)
        return text[context_start:context_end].strip()

    def _create_entity(self, entity_data: Dict[str, Any]) -> Entity:
        """创建实体对象"""
        entity_type_map = {
            "cryptocurrency": EntityType.CRYPTOCURRENCY,
            "company": EntityType.COMPANY,
            "person": EntityType.PERSON,
            "organization": EntityType.ORGANIZATION,
            "location": EntityType.LOCATION,
            "technology": EntityType.TECHNOLOGY,
            "protocol": EntityType.PROTOCOL,
            "exchange": EntityType.EXCHANGE,
            "wallet": EntityType.WALLET,
            "regulator": EntityType.REGULATOR,
            "event": EntityType.EVENT,
            "product": EntityType.PRODUCT,
            "service": EntityType.SERVICE,
            "concept": EntityType.CONCEPT,
            "metric": EntityType.METRIC,
            "date": EntityType.DATE,
            "amount": EntityType.AMOUNT,
            "percentage": EntityType.PERCENTAGE,
            "other": EntityType.OTHER
        }

        return Entity(
            id=entity_data.get("id", ""),
            text=entity_data.get("text", ""),
            type=entity_type_map.get(entity_data.get("type", "other"), EntityType.OTHER),
            start_position=entity_data.get("start_position", 0),
            end_position=entity_data.get("end_position", 0),
            confidence=entity_data.get("confidence", 0.0),
            normalized_form=entity_data.get("normalized_form"),
            aliases=entity_data.get("aliases", []),
            description=entity_data.get("description"),
            metadata=entity_data.get("metadata", {}),
            context=entity_data.get("context", ""),
            sentiment=entity_data.get("sentiment", {}),
            relationships=entity_data.get("relationships", [])
        )

    async def extract_entities(self, article: NewsArticle) -> EntityExtractionResult:
        """提取实体"""
        start_time = time.time()
        self.stats.total_articles += 1

        try:
            # 创建消息
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(article)

            messages = [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=user_prompt)
            ]

            # 调用LLM
            response = await self.llm_connector.generate_response(messages)

            # 解析响应
            extraction_data = self._parse_entity_response(response.content)

            # 创建实体对象
            entities = []
            for entity_data in extraction_data.get("entities", []):
                # 过滤低置信度实体
                if entity_data.get("confidence", 0.0) >= self.config.min_entity_confidence:
                    entity = self._create_entity(entity_data)
                    entities.append(entity)

            # 限制实体数量
            entities = entities[:self.config.max_entities_per_article]

            # 创建关系对象
            relationships = []
            for rel_data in extraction_data.get("relationships", []):
                relationship = EntityRelationship(
                    subject=rel_data.get("subject", ""),
                    object=rel_data.get("object", ""),
                    relation=rel_data.get("relation", ""),
                    confidence=rel_data.get("confidence", 0.0),
                    context=rel_data.get("context", ""),
                    metadata=rel_data.get("metadata", {})
                )
                relationships.append(relationship)

            # 统计实体类型
            entity_types_count = {}
            for entity in entities:
                entity_type = entity.type.value
                entity_types_count[entity_type] = entity_types_count.get(entity_type, 0) + 1

            # 创建结果
            result = EntityExtractionResult(
                entities=entities,
                relationships=relationships,
                entity_types_count=entity_types_count,
                processing_time=time.time() - start_time,
                metadata={
                    "llm_provider": response.provider.value,
                    "llm_model": response.model,
                    "response_time": response.response_time,
                    "tokens_used": response.usage.get("total_tokens", 0),
                    "cached": response.cached,
                    "extraction_stats": extraction_data.get("entity_stats", {})
                }
            )

            # 更新统计
            self.stats.successful_extractions += 1
            self._update_stats(result)

            self.logger.info(f"Successfully extracted {len(entities)} entities from article {article.id}")
            return result

        except Exception as e:
            self.stats.failed_extractions += 1
            self.logger.error(f"Failed to extract entities from article {article.id}: {str(e)}")

            # 返回默认结果
            return EntityExtractionResult(
                entities=[],
                relationships=[],
                entity_types_count={},
                processing_time=time.time() - start_time,
                metadata={"error": str(e)}
            )

    async def extract_batch_entities(self, articles: List[NewsArticle]) -> List[EntityExtractionResult]:
        """批量实体提取"""
        self.logger.info(f"Starting batch entity extraction from {len(articles)} articles")

        tasks = []
        for article in articles:
            task = self.extract_entities(article)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        extraction_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Batch entity extraction failed for article {articles[i].id}: {str(result)}")
                extraction_results.append(EntityExtractionResult(
                    entities=[],
                    relationships=[],
                    entity_types_count={},
                    processing_time=0.0,
                    metadata={"error": str(result), "batch_failed": True}
                ))
            else:
                extraction_results.append(result)

        self.logger.info(f"Batch entity extraction completed: {len(extraction_results)} articles processed")
        return extraction_results

    def _update_stats(self, result: EntityExtractionResult):
        """更新统计信息"""
        # 更新平均处理时间
        total_time = self.stats.average_processing_time * (self.stats.successful_extractions - 1)
        total_time += result.processing_time
        self.stats.average_processing_time = total_time / self.stats.successful_extractions

        # 更新平均实体数量
        total_entities = self.stats.average_entities_per_article * (self.stats.successful_extractions - 1)
        total_entities += len(result.entities)
        self.stats.average_entities_per_article = total_entities / self.stats.successful_extractions

        # 更新实体类型分布
        for entity in result.entities:
            self.stats.entity_type_distribution[entity.type.value] += 1

        # 更新关系数量
        self.stats.total_relationships_extracted += len(result.relationships)

        # 更新平均置信度
        if result.entities:
            total_confidence = self.stats.average_confidence_score * (self.stats.successful_extractions - 1)
            avg_confidence = sum(entity.confidence for entity in result.entities) / len(result.entities)
            total_confidence += avg_confidence
            self.stats.average_confidence_score = total_confidence / self.stats.successful_extractions

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        success_rate = self.stats.successful_extractions / max(1, self.stats.total_articles)
        return {
            "total_articles": self.stats.total_articles,
            "successful_extractions": self.stats.successful_extractions,
            "failed_extractions": self.stats.failed_extractions,
            "success_rate": success_rate,
            "average_processing_time": self.stats.average_processing_time,
            "average_entities_per_article": self.stats.average_entities_per_article,
            "average_confidence_score": self.stats.average_confidence_score,
            "total_relationships_extracted": self.stats.total_relationships_extracted,
            "entity_type_distribution": self.stats.entity_type_distribution,
            "config": {
                "enable_entity_linking": self.config.enable_entity_linking,
                "enable_relationship_extraction": self.config.enable_relationship_extraction,
                "enable_entity_disambiguation": self.config.enable_entity_disambiguation,
                "enable_sentiment_association": self.config.enable_sentiment_association,
                "max_entities_per_article": self.config.max_entities_per_article,
                "min_entity_confidence": self.config.min_entity_confidence
            }
        }

    def update_config(self, config: EntityConfig):
        """更新配置"""
        self.config = config
        self.logger.info("Entity extractor configuration updated")

    def get_entity_summary(self, results: List[EntityExtractionResult]) -> Dict[str, Any]:
        """获取实体摘要"""
        if not results:
            return {"error": "No results to analyze"}

        # 统计所有实体
        all_entities = []
        all_relationships = []
        entity_type_counts = {}

        for result in results:
            all_entities.extend(result.entities)
            all_relationships.extend(result.relationships)

            for entity_type, count in result.entity_types_count.items():
                entity_type_counts[entity_type] = entity_type_counts.get(entity_type, 0) + count

        # 找出最常见的实体
        entity_frequency = {}
        for entity in all_entities:
            normalized = entity.normalized_form or entity.text
            entity_frequency[normalized] = entity_frequency.get(normalized, 0) + 1

        top_entities = sorted(entity_frequency.items(), key=lambda x: x[1], reverse=True)[:20]

        # 计算平均置信度
        avg_confidence = sum(entity.confidence for entity in all_entities) / len(all_entities) if all_entities else 0

        return {
            "total_articles": len(results),
            "total_entities": len(all_entities),
            "total_relationships": len(all_relationships),
            "average_entities_per_article": len(all_entities) / len(results),
            "entity_type_distribution": entity_type_counts,
            "average_confidence_score": avg_confidence,
            "top_entities": top_entities,
            "relationship_types": {}  # TODO: 实现关系类型统计
        }

    def filter_entities_by_type(self, entities: List[Entity], entity_types: List[EntityType]) -> List[Entity]:
        """按类型过滤实体"""
        type_set = set(entity_types)
        return [entity for entity in entities if entity.type in type_set]

    def filter_entities_by_confidence(self, entities: List[Entity], min_confidence: float) -> List[Entity]:
        """按置信度过滤实体"""
        return [entity for entity in entities if entity.confidence >= min_confidence]

    def get_entity_context(self, entity: Entity, original_content: str, context_size: int = 100) -> str:
        """获取实体上下文"""
        start = max(0, entity.start_position - context_size)
        end = min(len(original_content), entity.end_position + context_size)
        return original_content[start:end]

    def validate_article(self, article: NewsArticle) -> bool:
        """验证文章是否适合实体提取"""
        if not article.content or len(article.content.strip()) < 50:
            self.logger.warning(f"Article {article.id} has insufficient content for entity extraction")
            return False

        return True