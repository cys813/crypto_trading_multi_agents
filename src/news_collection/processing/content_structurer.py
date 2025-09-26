"""
Content structurer for organizing and structuring news content
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict
import json

from ..models.base import NewsArticle, NewsCategory
from .models import ProcessingConfig


@dataclass
class StructuredContent:
    """结构化内容"""
    title: str
    summary: str
    main_content: str
    sections: List[Dict[str, str]]
    key_points: List[str]
    entities: Dict[str, List[str]]
    metadata: Dict[str, Any]
    tags: List[str]
    category: NewsCategory
    sentiment: Optional[Dict[str, float]] = None
    urgency_level: str = "normal"
    reading_time_minutes: int = 0


@dataclass
class StructuringStats:
    """结构化统计信息"""
    sections_extracted: int
    key_points_extracted: int
    entities_extracted: int
    sentiment_analyzed: bool
    processing_time: float


class ContentStructurer:
    """内容结构化器 - 将内容转换为结构化格式"""

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # 章节提取模式
        self.section_patterns = [
            re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE),  # Markdown标题
            re.compile(r'^(.+)\n[=-]{3,}$', re.MULTILINE),  # 下划线标题
            re.compile(r'^[A-Z][A-Z\s]{10,}$', re.MULTILINE),  # 全大写标题
        ]

        # 关键点提取模式
        self.key_point_patterns = [
            re.compile(r'^[•\-\*]\s+(.+)$', re.MULTILINE),  # 项目符号
            re.compile(r'^\d+\.\s+(.+)$', re.MULTILINE),  # 数字列表
            re.compile(r'^[A-Z]\.\s+(.+)$', re.MULTILINE),  # 字母列表
        ]

        # 实体识别模式
        self.entity_patterns = {
            'cryptocurrencies': [
                re.compile(r'\b(Bitcoin|BTC|Ethereum|ETH|Binance Coin|BNB|Cardano|ADA|Solana|SOL|XRP|Polkadot|DOT|Dogecoin|DOGE|Avalanche|AVAX|Polygon|MATIC|Chainlink|LINK|Litecoin|LTC|Bitcoin Cash|BCH|Stellar|XLM|Filecoin|FIL|TRON|TRX|Ethereum Classic|ETC|Monero|XMR|Cosmos|ATOM|Algorand|ALGO|VeChain|VET|Uniswap|UNI|Aave|AAVE|Compound|COMP|Maker|MKR|Synthetix|SNX|Yearn\.finance|YFI|Curve Finance Token|CRV|SushiSwap|SUSHI|1INCH|The Graph|GRT|Theta Network|THETA|FTX Token|FTT|LEO Token|LEO|OKB|Huobi Token|HT|KuCoin Token|KCS|Crypto\.com Coin|CRO|GateToken|GT|FTX Token|FTT)\b', re.IGNORECASE),
            ],
            'companies': [
                re.compile(r'\b(Binance|Coinbase|Kraken|Bitfinex|Bitstamp|Gemini|Huobi|OKX|KuCoin|Gate\.io|FTX|Crypto\.com|Bittrex|Poloniex|Liquid|Bybit|Deribit|BitMEX|eToro|Robinhood|PayPal|Square|MicroStrategy|Tesla|Amazon|Google|Microsoft|Apple|Facebook|Meta|Twitter|Tesla|Mastercard|Visa|PayPal|Stripe|Goldman Sachs|JPMorgan Chase|Bank of America|Morgan Stanley|BlackRock|Fidelity|Vanguard|Charles Schwab|T Rowe Price| Invesco|State Street|BNY Mellon|Northern Trust|T. Rowe Price|American Express|Discover|Capital One|Bank of New York Mellon|PNC Financial|U.S. Bancorp|Truist Financial|Citigroup|Wells Fargo)\b', re.IGNORECASE),
            ],
            'countries': [
                re.compile(r'\b(United States|USA|China|Japan|Germany|United Kingdom|UK|India|France|Italy|Brazil|Canada|Russia|South Korea|Spain|Australia|Mexico|Indonesia|Netherlands|Saudi Arabia|Switzerland|Turkey|Taiwan|Poland|Belgium|Argentina|Ireland|Israel|Austria|Nigeria|United Arab Emirates|UAE|Norway|Hong Kong|Singapore|Malaysia|Thailand|Philippines|Vietnam|South Africa|Egypt|Kenya|Nigeria|Chile|Colombia|Peru|Venezuela|Argentina|Uruguay|Paraguay|Bolivia|Ecuador|Guyana|Suriname|French Guiana)\b', re.IGNORECASE),
            ],
            'regulatory_terms': [
                re.compile(r'\b(SEC|CFTC|FCA|FSA|FINMA|BaFin|MAS|ASIC|CySEC|FINRA|ESMA|MiFID|GDPR|CCPA|AML|KYC|FATF|Basel III|Dodd-Frank|Sarbanes-Oxley|SOX|Federal Reserve|Fed|ECB|BoE|BoJ|PBOC|RBA|RBNZ|SNB|Norges Bank|Danmarks Nationalbank|Bank of Canada|Bank of Mexico|Central Bank of Brazil|Central Bank of Russia|Reserve Bank of India|Reserve Bank of Australia|Bank of Japan|People\'s Bank of China|European Central Bank|Federal Reserve System|Bank of England|Bank of Canada|Reserve Bank of New Zealand|South African Reserve Bank|Central Bank of Argentina|Central Bank of Chile|Central Bank of Colombia|Central Bank of Peru|Central Bank of Uruguay|Central Bank of Paraguay|Central Bank of Bolivia|Central Bank of Ecuador|Central Bank of Venezuela)\b', re.IGNORECASE),
            ]
        }

        # 情感分析关键词
        self.sentiment_keywords = {
            'positive': [
                '上涨', '增长', '提升', '突破', '创新高', '利好', '积极', '乐观',
                'bullish', 'surge', 'rise', 'growth', 'increase', 'positive', 'optimistic',
                'rally', 'boom', 'bull run', 'breakthrough', 'milestone', 'achievement'
            ],
            'negative': [
                '下跌', '下降', '暴跌', '崩盘', '利空', '消极', '悲观', '风险',
                'bearish', 'drop', 'fall', 'decline', 'decrease', 'negative', 'pessimistic',
                'crash', 'slump', 'recession', 'risk', 'concern', 'warning', 'loss'
            ],
            'neutral': [
                '稳定', '持平', '不变', '观望', '盘整', '横盘',
                'stable', 'steady', 'unchanged', 'neutral', 'sideways', 'consolidation'
            ]
        }

    async def structure_content(self, article: NewsArticle) -> Tuple[StructuredContent, StructuringStats]:
        """结构化内容"""
        start_time = datetime.now()

        try:
            # 提取章节
            sections = await self._extract_sections(article.content)

            # 提取关键点
            key_points = await self._extract_key_points(article.content)

            # 识别实体
            entities = await self._extract_entities(article.content)

            # 分析情感
            sentiment = await self._analyze_sentiment(article.content)

            # 计算阅读时间
            reading_time = self._calculate_reading_time(article.content)

            # 确定紧急程度
            urgency_level = self._determine_urgency(article, key_points)

            # 生成摘要（如果不存在）
            summary = article.summary or await self._generate_summary(article.content)

            # 创建结构化内容
            structured_content = StructuredContent(
                title=article.title,
                summary=summary,
                main_content=article.content,
                sections=sections,
                key_points=key_points,
                entities=entities,
                metadata=article.metadata or {},
                tags=article.tags or [],
                category=article.category,
                sentiment=sentiment,
                urgency_level=urgency_level,
                reading_time_minutes=reading_time
            )

            # 更新统计
            stats = StructuringStats(
                sections_extracted=len(sections),
                key_points_extracted=len(key_points),
                entities_extracted=sum(len(entities_list) for entities_list in entities.values()),
                sentiment_analyzed=sentiment is not None,
                processing_time=(datetime.now() - start_time).total_seconds()
            )

            self.logger.info(f"内容结构化完成: {len(sections)} 章节, {len(key_points)} 关键点, {stats.entities_extracted} 实体")

            return structured_content, stats

        except Exception as e:
            self.logger.error(f"内容结构化失败: {str(e)}", exc_info=True)
            # 返回基本结构化内容
            structured_content = StructuredContent(
                title=article.title,
                summary=article.summary or "",
                main_content=article.content,
                sections=[],
                key_points=[],
                entities={},
                metadata=article.metadata or {},
                tags=article.tags or [],
                category=article.category,
                reading_time=self._calculate_reading_time(article.content)
            )

            stats = StructuringStats(
                sections_extracted=0,
                key_points_extracted=0,
                entities_extracted=0,
                sentiment_analyzed=False,
                processing_time=(datetime.now() - start_time).total_seconds()
            )

            return structured_content, stats

    async def batch_structure_content(self, articles: List[NewsArticle]) -> List[Tuple[StructuredContent, StructuringStats]]:
        """批量结构化内容"""
        self.logger.info(f"开始批量结构化 {len(articles)} 篇文章")

        results = []
        for article in articles:
            try:
                structured_content, stats = await self.structure_content(article)
                results.append((structured_content, stats))
            except Exception as e:
                self.logger.error(f"批量结构化失败: {str(e)}", exc_info=True)
                # 返回基本结构化内容
                structured_content = StructuredContent(
                    title=article.title,
                    summary=article.summary or "",
                    main_content=article.content,
                    sections=[],
                    key_points=[],
                    entities={},
                    metadata=article.metadata or {},
                    tags=article.tags or [],
                    category=article.category,
                    reading_time=self._calculate_reading_time(article.content)
                )

                stats = StructuringStats(
                    sections_extracted=0,
                    key_points_extracted=0,
                    entities_extracted=0,
                    sentiment_analyzed=False,
                    processing_time=0.0
                )
                results.append((structured_content, stats))

        self.logger.info(f"批量结构化完成，处理了 {len(results)} 篇文章")
        return results

    async def _extract_sections(self, content: str) -> List[Dict[str, str]]:
        """提取章节"""
        sections = []
        lines = content.split('\n')
        current_section = ""
        current_content = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检查是否是标题
            is_header = False
            for pattern in self.section_patterns:
                match = pattern.match(line)
                if match:
                    is_header = True
                    # 保存前一个章节
                    if current_section and current_content:
                        sections.append({
                            'title': current_section,
                            'content': '\n'.join(current_content).strip()
                        })

                    # 开始新章节
                    if pattern.pattern.startswith(r'^#'):
                        level = len(match.group(1))
                        current_section = match.group(2)
                    elif pattern.pattern.startswith(r'^(.+)'):
                        current_section = match.group(1)
                    else:
                        current_section = line

                    current_content = []
                    break

            if not is_header:
                current_content.append(line)

        # 添加最后一个章节
        if current_section and current_content:
            sections.append({
                'title': current_section,
                'content': '\n'.join(current_content).strip()
            })

        # 如果没有找到章节，将整个内容作为一个章节
        if not sections:
            sections.append({
                'title': 'Main Content',
                'content': content.strip()
            })

        return sections

    async def _extract_key_points(self, content: str) -> List[str]:
        """提取关键点"""
        key_points = []
        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检查是否是列表项
            for pattern in self.key_point_patterns:
                match = pattern.match(line)
                if match:
                    key_point = match.group(1).strip()
                    if len(key_point) > 10:  # 过滤过短的点
                        key_points.append(key_point)
                    break

        # 如果没有找到列表项，尝试从段落中提取关键句
        if not key_points:
            key_points = self._extract_key_sentences(content)

        # 去重并限制数量
        unique_points = list(dict.fromkeys(key_points))  # 保持顺序的去重
        return unique_points[:10]  # 最多返回10个关键点

    def _extract_key_sentences(self, content: str) -> List[str]:
        """从段落中提取关键句"""
        sentences = re.split(r'[.!?。！？]', content)
        key_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if (len(sentence) > 20 and
                any(keyword in sentence.lower() for keyword in
                    ['重要', '关键', '主要', '核心', 'essential', 'key', 'main', 'important', 'critical'])):
                key_sentences.append(sentence)

        return key_sentences[:5]

    async def _extract_entities(self, content: str) -> Dict[str, List[str]]:
        """提取命名实体"""
        entities = {}

        for entity_type, patterns in self.entity_patterns.items():
            found_entities = set()
            for pattern in patterns:
                matches = pattern.findall(content)
                if matches:
                    found_entities.update(matches)

            if found_entities:
                entities[entity_type] = list(found_entities)

        return entities

    async def _analyze_sentiment(self, content: str) -> Optional[Dict[str, float]]:
        """分析情感"""
        try:
            content_lower = content.lower()

            # 计算情感分数
            positive_count = sum(1 for keyword in self.sentiment_keywords['positive'] if keyword in content_lower)
            negative_count = sum(1 for keyword in self.sentiment_keywords['negative'] if keyword in content_lower)
            neutral_count = sum(1 for keyword in self.sentiment_keywords['neutral'] if keyword in content_lower)

            total_count = positive_count + negative_count + neutral_count
            if total_count == 0:
                return None

            # 计算情感比例
            positive_score = positive_count / total_count
            negative_score = negative_count / total_count
            neutral_score = neutral_count / total_count

            # 确定主要情感
            if positive_score > negative_score and positive_score > neutral_score:
                dominant = 'positive'
            elif negative_score > positive_score and negative_score > neutral_score:
                dominant = 'negative'
            else:
                dominant = 'neutral'

            return {
                'positive': positive_score,
                'negative': negative_score,
                'neutral': neutral_score,
                'dominant': dominant,
                'confidence': max(positive_score, negative_score, neutral_score)
            }

        except Exception as e:
            self.logger.error(f"情感分析失败: {str(e)}", exc_info=True)
            return None

    def _calculate_reading_time(self, content: str) -> int:
        """计算阅读时间（分钟）"""
        if not content:
            return 0

        # 平均阅读速度：每分钟200-300字
        words = len(content.split())
        reading_time = max(1, int(words / 250))

        return reading_time

    def _determine_urgency(self, article: NewsArticle, key_points: List[str]) -> str:
        """确定紧急程度"""
        urgency_indicators = [
            '紧急', '突发', '即时', '立即', '快讯', 'breaking', 'urgent', 'immediate',
            'alert', 'critical', 'important', 'serious', 'severe'
        ]

        # 检查标题中的紧急词
        title_lower = article.title.lower()
        if any(indicator in title_lower for indicator in urgency_indicators):
            return "high"

        # 检查关键点中的紧急词
        key_points_text = ' '.join(key_points).lower()
        if any(indicator in key_points_text for indicator in urgency_indicators):
            return "high"

        # 检查分类
        if article.category == NewsCategory.BREAKING:
            return "high"

        # 默认为正常
        return "normal"

    async def _generate_summary(self, content: str) -> str:
        """生成摘要"""
        try:
            # 简单的摘要生成：取前两句话
            sentences = re.split(r'[.!?。！？]', content)
            sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

            if len(sentences) >= 2:
                summary = sentences[0] + '. ' + sentences[1] + '.'
            elif sentences:
                summary = sentences[0] + '.'
            else:
                summary = content[:200] + '...' if len(content) > 200 else content

            return summary

        except Exception as e:
            self.logger.error(f"摘要生成失败: {str(e)}", exc_info=True)
            return content[:200] + '...' if len(content) > 200 else content

    def structure_to_article(self, structured_content: StructuredContent, original_article: NewsArticle) -> NewsArticle:
        """将结构化内容转换为文章"""
        # 更新元数据
        updated_metadata = {
            **(original_article.metadata or {}),
            'structured': True,
            'structuring_time': datetime.now().isoformat(),
            'sections_count': len(structured_content.sections),
            'key_points_count': len(structured_content.key_points),
            'entities_count': sum(len(entities_list) for entities_list in structured_content.entities.values()),
            'sentiment': structured_content.sentiment,
            'urgency_level': structured_content.urgency_level,
            'reading_time_minutes': structured_content.reading_time_minutes
        }

        # 创建更新后的文章
        updated_article = NewsArticle(
            id=original_article.id,
            title=structured_content.title,
            content=structured_content.main_content,
            summary=structured_content.summary,
            author=original_article.author,
            published_at=original_article.published_at,
            source=original_article.source,
            url=original_article.url,
            category=structured_content.category,
            tags=structured_content.tags,
            metadata=updated_metadata
        )

        return updated_article

    def get_entity_patterns(self) -> Dict[str, List[str]]:
        """获取实体识别模式"""
        return {entity_type: [pattern.pattern for pattern in patterns]
                for entity_type, patterns in self.entity_patterns.items()}

    def add_entity_pattern(self, entity_type: str, pattern: str):
        """添加实体识别模式"""
        try:
            compiled_pattern = re.compile(pattern, re.IGNORECASE)
            if entity_type not in self.entity_patterns:
                self.entity_patterns[entity_type] = []
            self.entity_patterns[entity_type].append(compiled_pattern)
            self.logger.info(f"已添加 {entity_type} 实体模式: {pattern}")
        except Exception as e:
            self.logger.error(f"添加实体模式失败: {str(e)}", exc_info=True)