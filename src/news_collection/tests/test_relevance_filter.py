"""
Unit tests for relevance filter
"""

import unittest
from datetime import datetime
from ..collection.relevance_filter import (
    RelevanceFilter,
    RelevanceLevel,
    RelevanceScore,
    CryptocurrencyInfo
)
from ..models.base import NewsArticle, NewsCategory


class TestRelevanceFilter(unittest.TestCase):
    """测试相关性过滤器"""

    def setUp(self):
        """设置测试环境"""
        self.config = {
            'min_relevance_score': 50.0,
            'high_relevance_threshold': 90.0,
            'medium_relevance_threshold': 70.0,
            'confidence_threshold': 0.7,
            'additional_keywords': {
                'defi_terms': ['yield farming', 'liquidity mining'],
                'nft_terms': ['digital art', 'nft marketplace']
            },
            'additional_cryptocurrencies': {
                'MATIC': {
                    'name': 'Polygon',
                    'aliases': ['Polygon', 'polygon', 'MATIC'],
                    'categories': ['layer2', 'scaling'],
                    'priority': 6
                }
            }
        }
        self.filter = RelevanceFilter(self.config)

    def test_high_relevance_bitcoin_article(self):
        """测试高相关性比特币文章"""
        article = NewsArticle(
            id="1",
            title="Bitcoin reaches all-time high as SEC approval expected",
            content="Bitcoin has reached a new all-time high of $50,000 as the SEC is expected to approve Bitcoin ETFs. This breakthrough in cryptocurrency adoption has led to increased trading volume and market confidence.",
            category=NewsCategory.BREAKING,
            source="coindesk",
            url="https://coindesk.com/bitcoin-ath",
            published_at=datetime.now()
        )

        score = self.filter.calculate_relevance(article)

        self.assertGreaterEqual(score.score, 90.0)
        self.assertEqual(score.level, RelevanceLevel.HIGH)
        self.assertGreaterEqual(score.confidence, 0.8)
        self.assertIn('BTC', score.matched_cryptos)
        self.assertGreater(len(score.matched_keywords), 0)

    def test_medium_relevance_ethereum_article(self):
        """测试中等相关性以太坊文章"""
        article = NewsArticle(
            id="2",
            title="Ethereum upgrade improves scalability",
            content="The latest Ethereum upgrade focuses on improving network scalability and reducing gas fees for users.",
            category=NewsCategory.TECHNOLOGY,
            source="decrypt",
            published_at=datetime.now()
        )

        score = self.filter.calculate_relevance(article)

        self.assertGreaterEqual(score.score, 70.0)
        self.assertLess(score.score, 90.0)
        self.assertEqual(score.level, RelevanceLevel.MEDIUM)
        self.assertIn('ETH', score.matched_cryptos)

    def test_low_relevance_crypto_article(self):
        """测试低相关性加密货币文章"""
        article = NewsArticle(
            id="3",
            title="Analysis of crypto market trends",
            content="This article provides a general analysis of market trends in the cryptocurrency space.",
            category=NewsCategory.MARKET_ANALYSIS,
            published_at=datetime.now()
        )

        score = self.filter.calculate_relevance(article)

        self.assertGreaterEqual(score.score, 50.0)
        self.assertLess(score.score, 70.0)
        self.assertEqual(score.level, RelevanceLevel.LOW)

    def test_irrelevant_article(self):
        """测试不相关文章"""
        article = NewsArticle(
            id="4",
            title="Traditional stock market analysis",
            content="This article discusses traditional stock market performance and investment strategies.",
            category=NewsCategory.GENERAL,
            published_at=datetime.now()
        )

        score = self.filter.calculate_relevance(article)

        self.assertLess(score.score, 50.0)
        self.assertEqual(score.level, RelevanceLevel.IRRELEVANT)

    def test_cryptocurrency_with_multiple_aliases(self):
        """测试多个别名的加密货币匹配"""
        article = NewsArticle(
            id="5",
            title="Polygon network sees increased adoption",
            content="Polygon (formerly Matic Network) has seen significant adoption in the DeFi space.",
            published_at=datetime.now()
        )

        score = self.filter.calculate_relevance(article)

        self.assertGreater(score.score, 50.0)
        self.assertIn('MATIC', score.matched_cryptos)

    def test_defi_keywords_detection(self):
        """测试DeFi关键词检测"""
        article = NewsArticle(
            id="6",
            title="New yield farming opportunities",
            content="Users can now participate in yield farming and liquidity mining protocols to earn high returns.",
            published_at=datetime.now()
        )

        score = self.filter.calculate_relevance(article)

        self.assertGreater(score.score, 60.0)
        self.assertIn('defi_terms', score.category_matches)

    def test_nft_keywords_detection(self):
        """测试NFT关键词检测"""
        article = NewsArticle(
            id="7",
            title="Digital art marketplaces thrive",
            content="NFT marketplaces and digital art platforms are experiencing unprecedented growth.",
            published_at=datetime.now()
        )

        score = self.filter.calculate_relevance(article)

        self.assertGreater(score.score, 60.0)
        self.assertIn('nft_terms', score.category_matches)

    def test_title_weighting(self):
        """测试标题权重"""
        # 标题包含加密货币关键词的文章
        article_with_crypto_title = NewsArticle(
            id="8",
            title="Bitcoin price surges to new high",
            content="General market analysis shows positive trends.",
            published_at=datetime.now()
        )

        # 内容包含加密货币关键词的文章
        article_with_crypto_content = NewsArticle(
            id="9",
            title="Market analysis report",
            content="Bitcoin prices have surged to new highs as market confidence grows.",
            published_at=datetime.now()
        )

        score_title = self.filter.calculate_relevance(article_with_crypto_title)
        score_content = self.filter.calculate_relevance(article_with_crypto_content)

        # 标题中的关键词应该获得更高分数
        self.assertGreater(score_title.score, score_content.score)

    def test_category_bonus(self):
        """测试类别加分"""
        # 监管类文章
        regulation_article = NewsArticle(
            id="10",
            title="New crypto regulations announced",
            content="Government announces new regulations for cryptocurrency exchanges.",
            category=NewsCategory.REGULATION,
            published_at=datetime.now()
        )

        # 常规类文章
        general_article = NewsArticle(
            id="11",
            title="New crypto regulations announced",
            content="Government announces new regulations for cryptocurrency exchanges.",
            category=NewsCategory.GENERAL,
            published_at=datetime.now()
        )

        score_regulation = self.filter.calculate_relevance(regulation_article)
        score_general = self.filter.calculate_relevance(general_article)

        # 监管类文章应该获得更高分数
        self.assertGreater(score_regulation.score, score_general.score)

    def test_is_relevant_method(self):
        """测试is_relevant方法"""
        # 相关文章
        relevant_article = NewsArticle(
            id="12",
            title="Bitcoin market analysis",
            content="Bitcoin prices show strong upward momentum.",
            published_at=datetime.now()
        )

        # 不相关文章
        irrelevant_article = NewsArticle(
            id="13",
            title="Weather forecast",
            content="Tomorrow will be sunny with temperatures reaching 25°C.",
            published_at=datetime.now()
        )

        self.assertTrue(self.filter.is_relevant(relevant_article))
        self.assertFalse(self.filter.is_relevant(irrelevant_article))

    def test_filter_articles(self):
        """测试文章过滤"""
        articles = [
            NewsArticle(
                id="14",
                title="Bitcoin news",
                content="Bitcoin reaches new high.",
                published_at=datetime.now()
            ),
            NewsArticle(
                id="15",
                title="Ethereum update",
                content="Ethereum network upgrade announced.",
                published_at=datetime.now()
            ),
            NewsArticle(
                id="16",
                title="General news",
                content="Unrelated news article.",
                published_at=datetime.now()
            )
        ]

        filtered_articles, scores = self.filter.filter_articles(articles)

        # 应该过滤掉不相关的文章
        self.assertEqual(len(filtered_articles), 2)
        self.assertEqual(len(scores), 2)
        self.assertEqual(filtered_articles[0].id, "14")
        self.assertEqual(filtered_articles[1].id, "15")

    def test_relevance_statistics(self):
        """测试相关性统计"""
        articles = [
            NewsArticle(
                id="17",
                title="Bitcoin breaking news",
                content="Bitcoin reaches all-time high.",
                category=NewsCategory.BREAKING,
                published_at=datetime.now()
            ),
            NewsArticle(
                id="18",
                title="Ethereum technology",
                content="Ethereum technology explained.",
                category=NewsCategory.TECHNOLOGY,
                published_at=datetime.now()
            ),
            NewsArticle(
                id="19",
                title="General article",
                content="General content.",
                category=NewsCategory.GENERAL,
                published_at=datetime.now()
            )
        ]

        stats = self.filter.get_relevance_statistics(articles)

        self.assertEqual(stats['total_articles'], 3)
        self.assertGreater(stats['average_score'], 0)
        self.assertIn('score_distribution', stats)
        self.assertIn('relevant_articles', stats)

    def test_update_crypto_database(self):
        """测试更新加密货币数据库"""
        new_cryptos = {
            'NEW': {
                'name': 'New Crypto',
                'aliases': ['New Crypto', 'NEW'],
                'categories': ['defi'],
                'priority': 5
            }
        }

        self.filter.update_crypto_database(new_cryptos)

        # 验证新加密货币已添加
        self.assertIn('NEW', self.filter.crypto_db)
        self.assertEqual(self.filter.crypto_db['NEW'].name, 'New Crypto')

        # 测试新加密货币能被识别
        article = NewsArticle(
            id="20",
            title="New Crypto launches",
            content="New Crypto has been launched with innovative features.",
            published_at=datetime.now()
        )

        score = self.filter.calculate_relevance(article)
        self.assertIn('NEW', score.matched_cryptos)

    def test_confidence_calculation(self):
        """测试置信度计算"""
        # 高置信度文章（多加密货币匹配）
        high_confidence_article = NewsArticle(
            id="21",
            title="Bitcoin and Ethereum surge",
            content="Both Bitcoin and Ethereum prices are surging as adoption increases.",
            published_at=datetime.now()
        )

        # 低置信度文章（少量匹配）
        low_confidence_article = NewsArticle(
            id="22",
            title="Crypto mentioned",
            content="The article briefly mentions crypto.",
            published_at=datetime.now()
        )

        high_score = self.filter.calculate_relevance(high_confidence_article)
        low_score = self.filter.calculate_relevance(low_confidence_article)

        self.assertGreater(high_score.confidence, low_score.confidence)

    def test_market_impact_scoring(self):
        """测试市场影响评分"""
        # 高市场影响文章
        high_impact_article = NewsArticle(
            id="23",
            title="SEC approves Bitcoin ETF",
            content="The SEC has officially approved Bitcoin ETFs, marking a major milestone.",
            category=NewsCategory.REGULATION,
            published_at=datetime.now()
        )

        # 低市场影响文章
        low_impact_article = NewsArticle(
            id="24",
            title="Bitcoin price analysis",
            content="Technical analysis of Bitcoin price movements.",
            category=NewsCategory.MARKET_ANALYSIS,
            published_at=datetime.now()
        )

        high_score = self.filter.calculate_relevance(high_impact_article)
        low_score = self.filter.calculate_relevance(low_impact_article)

        # 高市场影响文章应该获得更高分数
        self.assertGreater(high_score.score, low_score.score)


if __name__ == '__main__':
    unittest.main()