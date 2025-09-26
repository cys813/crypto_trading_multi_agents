"""
Cryptocurrency relevance filtering and scoring system
"""

import re
import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

from ..models.base import NewsArticle, NewsCategory


class RelevanceLevel(Enum):
    """相关性级别"""
    HIGH = "high"  # 高度相关 (90-100分)
    MEDIUM = "medium"  # 中等相关 (70-89分)
    LOW = "low"  # 低相关 (50-69分)
    IRRELEVANT = "irrelevant"  # 不相关 (<50分)


@dataclass
class CryptocurrencyInfo:
    """加密货币信息"""
    symbol: str
    name: str
    aliases: List[str]
    categories: List[str]
    priority: int = 1  # 1-10, 越高越重要


@dataclass
class RelevanceScore:
    """相关性分数"""
    score: float
    level: RelevanceLevel
    matched_keywords: List[str]
    matched_cryptos: List[str]
    category_matches: List[str]
    confidence: float  # 置信度 0-1
    reasoning: List[str]


class RelevanceFilter:
    """加密货币相关性过滤器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # 配置参数
        self.min_relevance_score = config.get('min_relevance_score', 50.0)
        self.high_relevance_threshold = config.get('high_relevance_threshold', 90.0)
        self.medium_relevance_threshold = config.get('medium_relevance_threshold', 70.0)
        self.confidence_threshold = config.get('confidence_threshold', 0.7)

        # 加载加密货币数据库
        self.crypto_db = self._load_crypto_database()

        # 加载关键词
        self.keywords = self._load_keywords()

        # 编译正则表达式
        self._compile_patterns()

    def _load_crypto_database(self) -> Dict[str, CryptocurrencyInfo]:
        """加载加密货币数据库"""
        # 主要加密货币列表
        crypto_data = {
            "BTC": CryptocurrencyInfo(
                symbol="BTC",
                name="Bitcoin",
                aliases=["Bitcoin", "bitcoin", "BTC", "XBT", "Bitcoins"],
                categories=["major", "store_of_value", "payment"],
                priority=10
            ),
            "ETH": CryptocurrencyInfo(
                symbol="ETH",
                name="Ethereum",
                aliases=["Ethereum", "ethereum", "ETH", "Ether"],
                categories=["major", "smart_contract", "defi"],
                priority=9
            ),
            "BNB": CryptocurrencyInfo(
                symbol="BNB",
                name="Binance Coin",
                aliases=["Binance Coin", "BNB", "Binance Coin"],
                categories=["exchange", "defi"],
                priority=8
            ),
            "ADA": CryptocurrencyInfo(
                symbol="ADA",
                name="Cardano",
                aliases=["Cardano", "cardano", "ADA"],
                categories=["smart_contract", "layer1"],
                priority=7
            ),
            "SOL": CryptocurrencyInfo(
                symbol="SOL",
                name="Solana",
                aliases=["Solana", "solana", "SOL"],
                categories=["smart_contract", "layer1"],
                priority=7
            ),
            "DOT": CryptocurrencyInfo(
                symbol="DOT",
                name="Polkadot",
                aliases=["Polkadot", "polkadot", "DOT"],
                categories=["interoperability", "layer1"],
                priority=6
            ),
            "DOGE": CryptocurrencyInfo(
                symbol="DOGE",
                name="Dogecoin",
                aliases=["Dogecoin", "dogecoin", "DOGE", "Dogi"],
                categories=["meme", "payment"],
                priority=6
            ),
            "XRP": CryptocurrencyInfo(
                symbol="XRP",
                name="Ripple",
                aliases=["Ripple", "ripple", "XRP"],
                categories=["payment", "institutional"],
                priority=7
            ),
            "AVAX": CryptocurrencyInfo(
                symbol="AVAX",
                name="Avalanche",
                aliases=["Avalanche", "avalanche", "AVAX"],
                categories=["smart_contract", "layer1"],
                priority=6
            ),
            "MATIC": CryptocurrencyInfo(
                symbol="MATIC",
                name="Polygon",
                aliases=["Polygon", "polygon", "MATIC"],
                categories=["layer2", "scaling"],
                priority=6
            ),
            "LINK": CryptocurrencyInfo(
                symbol="LINK",
                name="Chainlink",
                aliases=["Chainlink", "chainlink", "LINK"],
                categories=["oracle", "defi"],
                priority=7
            ),
            "UNI": CryptocurrencyInfo(
                symbol="UNI",
                name="Uniswap",
                aliases=["Uniswap", "uniswap", "UNI"],
                categories=["defi", "dex"],
                priority=7
            ),
            "LTC": CryptocurrencyInfo(
                symbol="LTC",
                name="Litecoin",
                aliases=["Litecoin", "litecoin", "LTC"],
                categories=["payment", "store_of_value"],
                priority=5
            ),
            "BCH": CryptocurrencyInfo(
                symbol="BCH",
                name="Bitcoin Cash",
                aliases=["Bitcoin Cash", "bitcoin cash", "BCH"],
                categories=["payment", "store_of_value"],
                priority=5
            ),
            "ATOM": CryptocurrencyInfo(
                symbol="ATOM",
                name="Cosmos",
                aliases=["Cosmos", "cosmos", "ATOM"],
                categories=["interoperability", "layer1"],
                priority=6
            )
        }

        # 从配置文件加载更多加密货币
        config_crypto = config.get('additional_cryptocurrencies', {})
        for symbol, data in config_crypto.items():
            crypto_data[symbol] = CryptocurrencyInfo(
                symbol=symbol,
                name=data.get('name', symbol),
                aliases=data.get('aliases', []),
                categories=data.get('categories', []),
                priority=data.get('priority', 1)
            )

        return crypto_data

    def _load_keywords(self) -> Dict[str, List[str]]:
        """加载相关性关键词"""
        keywords = {
            "high_relevance": [
                "cryptocurrency", "crypto", "blockchain", "decentralized", "defi",
                "nft", "nfts", "token", "tokens", "coin", "coins", "mining",
                "miner", "wallet", "exchange", "trading", "bitcoin", "ethereum",
                "altcoin", "altcoins", "staking", "yield farming", "liquidity",
                "smart contract", "dapp", "dapps", "web3", "metaverse"
            ],
            "market_terms": [
                "price", "prices", "market", "markets", "trading", "trade",
                "bull", "bear", "bullish", "bearish", "volatility", "pump",
                "dump", "rally", "crash", "correction", "resistance", "support",
                " ATH", "all-time high", "ATL", "all-time low", "market cap",
                "volume", "liquidity", "futures", "options", "leverage"
            ],
            "technology_terms": [
                "consensus", "proof of work", "proof of stake", "pos", "pow",
                "hash rate", "block", "blocks", "chain", "fork", "hard fork",
                "soft fork", "upgrade", "protocol", "network", "node", "nodes",
                "validator", "validation", "encryption", "cryptography", "hash"
            ],
            "regulation_terms": [
                "regulation", "regulatory", "SEC", "CFTC", "compliance", "legal",
                "law", "laws", "legislation", "government", "ban", "approve",
                "approval", "license", "tax", "taxation", "policy", "policies"
            ],
            "security_terms": [
                "hack", "hacked", "hacking", "security", "exploit", "vulnerability",
                "breach", "theft", "stolen", "scam", "fraud", "phishing", "malware"
            ]
        }

        # 从配置文件加载额外关键词
        config_keywords = config.get('additional_keywords', {})
        for category, words in config_keywords.items():
            if category in keywords:
                keywords[category].extend(words)
            else:
                keywords[category] = words

        return keywords

    def _compile_patterns(self):
        """编译正则表达式模式"""
        # 编译加密货币名称模式
        self.crypto_patterns = {}
        for symbol, crypto_info in self.crypto_db.items():
            pattern = r'\b(?:' + '|'.join(re.escape(alias) for alias in crypto_info.aliases) + r')\b'
            self.crypto_patterns[symbol] = re.compile(pattern, re.IGNORECASE)

        # 编译关键词模式
        self.keyword_patterns = {}
        for category, words in self.keywords.items():
            pattern = r'\b(?:' + '|'.join(re.escape(word) for word in words) + r')\b'
            self.keyword_patterns[category] = re.compile(pattern, re.IGNORECASE)

    def calculate_relevance(self, article: NewsArticle) -> RelevanceScore:
        """计算文章相关性分数"""
        text = f"{article.title} {article.content or ''}".lower()

        # 匹配结果
        matched_keywords = []
        matched_cryptos = []
        category_matches = []
        reasoning = []
        total_score = 0.0

        # 1. 加密货币匹配 (最高权重)
        crypto_score, matched_crypto_symbols = self._score_crypto_matches(text)
        if matched_crypto_symbols:
            matched_cryptos.extend(matched_crypto_symbols)
            reasoning.append(f"匹配到加密货币: {', '.join(matched_crypto_symbols)}")
        total_score += crypto_score * 0.4  # 40%权重

        # 2. 关键词匹配
        keyword_score, matched_keyword_cats = self._score_keyword_matches(text)
        if matched_keyword_cats:
            category_matches.extend(matched_keyword_cats)
            reasoning.append(f"匹配到关键词类别: {', '.join(matched_keyword_cats)}")
        total_score += keyword_score * 0.3  # 30%权重

        # 3. 标题相关性 (标题中的关键词更重要)
        title_score = self._score_title_relevance(article.title, text)
        if title_score > 0:
            reasoning.append(f"标题相关性得分: {title_score:.1f}")
        total_score += title_score * 0.2  # 20%权重

        # 4. 类别匹配
        category_score = self._score_category_match(article.category)
        if category_score > 0:
            reasoning.append(f"新闻类别匹配得分: {category_score:.1f}")
            category_matches.append(article.category.value)
        total_score += category_score * 0.1  # 10%权重

        # 限制分数范围
        total_score = max(0, min(100, total_score))

        # 确定相关性级别
        if total_score >= self.high_relevance_threshold:
            level = RelevanceLevel.HIGH
        elif total_score >= self.medium_relevance_threshold:
            level = RelevanceLevel.MEDIUM
        elif total_score >= self.min_relevance_score:
            level = RelevanceLevel.LOW
        else:
            level = RelevanceLevel.IRRELEVANT

        # 计算置信度
        confidence = self._calculate_confidence(
            matched_cryptos, matched_keyword_cats, total_score
        )

        # 去重关键词
        matched_keywords = list(set(matched_keywords))

        return RelevanceScore(
            score=total_score,
            level=level,
            matched_keywords=matched_keywords,
            matched_cryptos=matched_cryptos,
            category_matches=list(set(category_matches)),
            confidence=confidence,
            reasoning=reasoning
        )

    def _score_crypto_matches(self, text: str) -> Tuple[float, List[str]]:
        """评分加密货币匹配"""
        score = 0.0
        matched_symbols = []

        for symbol, pattern in self.crypto_patterns.items():
            matches = pattern.findall(text)
            if matches:
                matched_symbols.append(symbol)
                crypto_info = self.crypto_db[symbol]

                # 基于优先级和出现次数计算分数
                base_score = crypto_info.priority * 2
                frequency_bonus = min(len(matches), 5) * 2  # 最多额外10分

                # 主要加密货币额外加分
                if "major" in crypto_info.categories:
                    base_score += 5

                score += base_score + frequency_bonus

        # 限制分数
        return min(score, 40.0), matched_symbols  # 最多40分

    def _score_keyword_matches(self, text: str) -> Tuple[float, List[str]]:
        """评分关键词匹配"""
        score = 0.0
        matched_categories = []

        for category, pattern in self.keyword_patterns.items():
            matches = pattern.findall(text)
            if matches:
                matched_categories.append(category)

                # 不同类别有不同权重
                if category == "high_relevance":
                    category_score = min(len(matches) * 3, 15)  # 最多15分
                elif category == "market_terms":
                    category_score = min(len(matches) * 2, 10)  # 最多10分
                elif category == "technology_terms":
                    category_score = min(len(matches) * 1.5, 8)  # 最多8分
                elif category == "regulation_terms":
                    category_score = min(len(matches) * 2, 10)  # 最多10分
                elif category == "security_terms":
                    category_score = min(len(matches) * 2.5, 12)  # 最多12分
                else:
                    category_score = min(len(matches) * 1, 5)  # 最多5分

                score += category_score

        # 限制分数
        return min(score, 30.0), matched_categories  # 最多30分

    def _score_title_relevance(self, title: str, full_text: str) -> float:
        """评分标题相关性"""
        if not title:
            return 0.0

        title_lower = title.lower()
        score = 0.0

        # 检查标题中是否有加密货币
        for symbol, pattern in self.crypto_patterns.items():
            if pattern.search(title_lower):
                crypto_info = self.crypto_db[symbol]
                score += crypto_info.priority * 1.5  # 标题中的加密货币更重要

        # 检查标题中是否有高相关性关键词
        high_relevance_pattern = self.keyword_patterns.get("high_relevance", re.compile(r''))
        if high_relevance_pattern.search(title_lower):
            score += 5

        # 检查标题是否直接讨论市场或价格
        market_keywords = ["price", "market", "trading", "buy", "sell", "investment"]
        for keyword in market_keywords:
            if keyword in title_lower:
                score += 2

        return min(score, 20.0)  # 最多20分

    def _score_category_match(self, category: NewsCategory) -> float:
        """评分类别匹配"""
        category_scores = {
            NewsCategory.BREAKING: 8,
            NewsCategory.MARKET_ANALYSIS: 10,
            NewsCategory.REGULATION: 9,
            NewsCategory.TECHNOLOGY: 7,
            NewsCategory.SECURITY: 8,
            NewsCategory.ADOPTION: 6,
            NewsCategory.GENERAL: 3
        }

        return category_scores.get(category, 0)

    def _calculate_confidence(self,
                            matched_cryptos: List[str],
                            matched_categories: List[str],
                            score: float) -> float:
        """计算置信度"""
        confidence = 0.0

        # 基于匹配的加密货币数量
        if len(matched_cryptos) >= 2:
            confidence += 0.4
        elif len(matched_cryptos) == 1:
            confidence += 0.2

        # 基于匹配的关键词类别数量
        if len(matched_categories) >= 3:
            confidence += 0.3
        elif len(matched_categories) >= 2:
            confidence += 0.2
        elif len(matched_categories) == 1:
            confidence += 0.1

        # 基于分数
        if score >= 80:
            confidence += 0.3
        elif score >= 60:
            confidence += 0.2
        elif score >= 40:
            confidence += 0.1

        return min(confidence, 1.0)

    def is_relevant(self, article: NewsArticle, min_score: Optional[float] = None) -> bool:
        """判断文章是否相关"""
        if min_score is None:
            min_score = self.min_relevance_score

        relevance_score = self.calculate_relevance(article)
        return relevance_score.score >= min_score

    def filter_articles(self,
                       articles: List[NewsArticle],
                       min_score: Optional[float] = None,
                       min_confidence: Optional[float] = None) -> Tuple[List[NewsArticle], List[RelevanceScore]]:
        """过滤文章"""
        if min_score is None:
            min_score = self.min_relevance_score
        if min_confidence is None:
            min_confidence = self.confidence_threshold

        relevant_articles = []
        relevance_scores = []

        for article in articles:
            score = self.calculate_relevance(article)

            if score.score >= min_score and score.confidence >= min_confidence:
                relevant_articles.append(article)
                relevance_scores.append(score)

        return relevant_articles, relevance_scores

    def get_relevance_statistics(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """获取相关性统计信息"""
        scores = [self.calculate_relevance(article) for article in articles]

        if not scores:
            return {"total_articles": 0}

        # 分数分布
        score_distribution = {
            "high": len([s for s in scores if s.level == RelevanceLevel.HIGH]),
            "medium": len([s for s in scores if s.level == RelevanceLevel.MEDIUM]),
            "low": len([s for s in scores if s.level == RelevanceLevel.LOW]),
            "irrelevant": len([s for s in scores if s.level == RelevanceLevel.IRRELEVANT])
        }

        # 最常匹配的加密货币
        crypto_frequency = {}
        for score in scores:
            for crypto in score.matched_cryptos:
                crypto_frequency[crypto] = crypto_frequency.get(crypto, 0) + 1

        top_cryptos = sorted(crypto_frequency.items(), key=lambda x: x[1], reverse=True)[:10]

        # 平均分数
        avg_score = sum(s.score for s in scores) / len(scores)
        avg_confidence = sum(s.confidence for s in scores) / len(scores)

        return {
            "total_articles": len(articles),
            "average_score": avg_score,
            "average_confidence": avg_confidence,
            "score_distribution": score_distribution,
            "top_cryptocurrencies": top_cryptos,
            "relevant_articles": len([s for s in scores if s.score >= self.min_relevance_score])
        }

    def update_crypto_database(self, new_cryptos: Dict[str, Dict[str, Any]]):
        """更新加密货币数据库"""
        for symbol, data in new_cryptos.items():
            self.crypto_db[symbol] = CryptocurrencyInfo(
                symbol=symbol,
                name=data.get('name', symbol),
                aliases=data.get('aliases', []),
                categories=data.get('categories', []),
                priority=data.get('priority', 1)
            )

            # 重新编译模式
            pattern = r'\b(?:' + '|'.join(re.escape(alias) for alias in self.crypto_db[symbol].aliases) + r')\b'
            self.crypto_patterns[symbol] = re.compile(pattern, re.IGNORECASE)

        self.logger.info(f"更新了 {len(new_cryptos)} 个加密货币到数据库")

    def export_configuration(self, export_path: str) -> bool:
        """导出配置"""
        try:
            config_data = {
                "cryptocurrencies": {
                    symbol: {
                        "name": crypto.name,
                        "aliases": crypto.aliases,
                        "categories": crypto.categories,
                        "priority": crypto.priority
                    }
                    for symbol, crypto in self.crypto_db.items()
                },
                "keywords": self.keywords,
                "thresholds": {
                    "min_relevance_score": self.min_relevance_score,
                    "high_relevance_threshold": self.high_relevance_threshold,
                    "medium_relevance_threshold": self.medium_relevance_threshold,
                    "confidence_threshold": self.confidence_threshold
                }
            }

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"相关性过滤器配置导出到: {export_path}")
            return True

        except Exception as e:
            self.logger.error("导出配置失败", exc_info=e)
            return False