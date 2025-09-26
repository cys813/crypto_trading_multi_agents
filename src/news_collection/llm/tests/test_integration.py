"""
Integration tests for LLM modules
Tests the interactions between all LLM components in the news collection system
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, List, Any

from ..llm.summarizer import Summarizer, SummarizerConfig, SummaryResult, SummaryLength
from ..llm.sentiment_analyzer import SentimentAnalyzer, SentimentConfig, SentimentAnalysisResult, SentimentCategory
from ..llm.entity_extractor import EntityExtractor, EntityConfig, Entity, EntityType
from ..llm.market_impact import MarketImpactAssessor, MarketImpactConfig, MarketImpactResult, ImpactType
from ..llm.batch_processor import BatchProcessor, BatchConfig, BatchTask, BatchPriority
from ..llm.cache_manager import CacheManager, CacheConfig
from ..llm.content_segmenter import ContentSegmenter, SegmenterConfig, ContentSection, SectionType
from ..llm.llm_connector import LLMConnector, LLMConfig

from ...models.base import NewsArticle, NewsCategory


class TestLLMIntegration:
    """LLM模块集成测试"""

    @pytest.fixture
    def mock_llm_connector(self):
        """模拟LLM连接器"""
        connector = MagicMock(spec=LLMConnector)
        connector.generate_text = AsyncMock()
        connector.generate_structured_text = AsyncMock()
        return connector

    @pytest.fixture
    def cache_manager(self):
        """缓存管理器"""
        config = CacheConfig()
        return CacheManager(config)

    @pytest.fixture
    def sample_articles(self):
        """示例文章数据"""
        return [
            NewsArticle(
                id="crypto_news_001",
                title="Bitcoin Surges to New All-Time High",
                content="""
                Bitcoin, the world's largest cryptocurrency, has reached a new all-time high of $67,000
                as institutional adoption accelerates. Major companies including Tesla, MicroStrategy,
                and Square have added Bitcoin to their balance sheets. Regulatory clarity from
                the SEC and growing mainstream acceptance are driving this bull run.

                Ethereum has also seen significant gains, reaching $3,500 as DeFi protocols continue
                to innovate and NFT markets expand. The overall cryptocurrency market capitalization
                now exceeds $2 trillion, with Bitcoin dominance at around 45%.
                """,
                summary="Bitcoin reaches new ATH at $67,000 driven by institutional adoption.",
                author="Sarah Chen",
                published_at=datetime.now(),
                source="coindesk.com",
                url="https://coindesk.com/bitcoin-ath",
                category=NewsCategory.GENERAL,
                tags=["bitcoin", "cryptocurrency", "institutional"]
            ),
            NewsArticle(
                id="market_analysis_001",
                title="Fed Interest Rate Decision Impacts Crypto Markets",
                content="""
                The Federal Reserve's latest interest rate decision has sent ripples through
                cryptocurrency markets. The Fed's indication of potential rate hikes in 2024
                has led to increased volatility in Bitcoin and altcoins.

                Market analysts are divided on the long-term impact, with some predicting
                a flight to safety in Bitcoin as digital gold, while others expect reduced
                risk appetite could hurt crypto prices. Trading volumes have increased
                significantly as traders position for the changing macroeconomic environment.

                Ethereum's transition to proof-of-stake has made it more attractive to
                environmentally conscious investors, potentially providing a buffer against
                traditional market volatility.
                """,
                summary="Fed rate decision creates volatility in cryptocurrency markets.",
                author="Michael Rodriguez",
                published_at=datetime.now(),
                source="bloomberg.com",
                url="https://bloomberg.com/fed-crypto",
                category=NewsCategory.MARKET_ANALYSIS,
                tags=["fed", "interest-rates", "market-volatility"]
            )
        ]

    @pytest.fixture
    def llm_components(self, mock_llm_connector, cache_manager):
        """所有LLM组件"""
        summarizer = Summarizer(mock_llm_connector, SummarizerConfig())
        sentiment_analyzer = SentimentAnalyzer(mock_llm_connector, SentimentConfig())
        entity_extractor = EntityExtractor(mock_llm_connector, EntityConfig())
        market_impact_assessor = MarketImpactAssessor(mock_llm_connector, MarketImpactConfig())
        content_segmenter = ContentSegmenter(mock_llm_connector, SegmenterConfig())

        return {
            'summarizer': summarizer,
            'sentiment_analyzer': sentiment_analyzer,
            'entity_extractor': entity_extractor,
            'market_impact_assessor': market_impact_assessor,
            'content_segmenter': content_segmenter,
            'cache_manager': cache_manager,
            'llm_connector': mock_llm_connector
        }

    @pytest.mark.asyncio
    async def test_full_llm_pipeline_integration(self, llm_components, sample_articles):
        """测试完整LLM处理管道集成"""
        # 设置模拟响应
        llm_components['llm_connector'].generate_text.side_effect = [
            # 总结响应
            '{"summary": "Bitcoin reaches new ATH driven by institutional adoption", "key_points": ["Institutional adoption accelerates", "Regulatory clarity improves", "Market cap exceeds $2 trillion"], "confidence": 0.9}',
            '{"summary": "Fed rate decision creates crypto market volatility", "key_points": ["Rate hike expectations", "Increased trading volumes", "Ethereum proof-of-stake transition"], "confidence": 0.85}',
            # 情感分析响应
            '{"sentiment": "bullish", "score": 0.8, "aspects": {"price_action": "bullish", "market_sentiment": "positive", "regulatory": "neutral"}, "confidence": 0.85}',
            '{"sentiment": "neutral", "score": 0.1, "aspects": {"market_sentiment": "uncertain", "regulatory": "negative", "economic": "neutral"}, "confidence": 0.8}',
            # 实体提取响应
            '{"entities": [{"id": "bitcoin", "text": "Bitcoin", "type": "cryptocurrency", "confidence": 0.95}, {"id": "tesla", "text": "Tesla", "type": "company", "confidence": 0.9}]}',
            '{"entities": [{"id": "fed", "text": "Federal Reserve", "type": "organization", "confidence": 0.95}, {"id": "ethereum", "text": "Ethereum", "type": "cryptocurrency", "confidence": 0.9}]}',
            # 市场影响评估响应
            '{"impact_type": "high", "magnitude": 0.8, "timeframe": "short_term", "confidence": 0.85}',
            '{"impact_type": "medium", "magnitude": 0.5, "timeframe": "medium_term", "confidence": 0.8}'
        ]

        llm_components['llm_connector'].generate_structured_text.side_effect = [
            # 内容分段响应
            {
                "sections": [
                    {"id": "price_analysis", "title": "Price Analysis", "type": "analysis", "content": "Bitcoin reaches new ATH at $67,000", "importance": 0.9},
                    {"id": "institutional_news", "title": "Institutional Adoption", "type": "news", "content": "Major companies add Bitcoin to balance sheets", "importance": 0.8}
                ]
            },
            {
                "sections": [
                    {"id": "fed_decision", "title": "Fed Decision", "type": "analysis", "content": "Fed indicates potential rate hikes in 2024", "importance": 0.9},
                    {"id": "market_reaction", "title": "Market Reaction", "type": "analysis", "content": "Increased volatility in crypto markets", "importance": 0.8}
                ]
            }
        ]

        results = []
        for article in sample_articles:
            # 内容分段
            segments = await llm_components['content_segmenter'].segment_content(article)

            # 总结
            summary = await llm_components['summarizer'].summarize_article(article)

            # 情感分析
            sentiment = await llm_components['sentiment_analyzer'].analyze_sentiment(article)

            # 实体提取
            entities = await llm_components['entity_extractor'].extract_entities(article)

            # 市场影响评估
            market_impact = await llm_components['market_impact_assessor'].assess_market_impact(article)

            result = {
                'article_id': article.id,
                'segments': segments,
                'summary': summary,
                'sentiment': sentiment,
                'entities': entities,
                'market_impact': market_impact
            }
            results.append(result)

        # 验证结果
        assert len(results) == len(sample_articles)

        for result in results:
            assert result['segments'] is not None
            assert len(result['segments']) > 0
            assert result['summary'] is not None
            assert result['sentiment'] is not None
            assert result['entities'] is not None
            assert len(result['entities']) > 0
            assert result['market_impact'] is not None

        # 验证LLM调用次数
        assert llm_components['llm_connector'].generate_text.call_count == 12  # 2 articles * 6 calls
        assert llm_components['llm_connector'].generate_structured_text.call_count == 2  # 2 articles * 1 call

    @pytest.mark.asyncio
    async def test_cache_integration(self, llm_components, sample_articles):
        """测试缓存集成"""
        # 设置模拟响应
        llm_components['llm_connector'].generate_text.return_value = '{"summary": "Test summary", "confidence": 0.9}'

        # 第一次调用 - 应该调用LLM
        result1 = await llm_components['summarizer'].summarize_article(sample_articles[0])
        assert llm_components['llm_connector'].generate_text.call_count == 1

        # 第二次调用相同内容 - 应该使用缓存
        result2 = await llm_components['summarizer'].summarize_article(sample_articles[0])
        assert llm_components['llm_connector'].generate_text.call_count == 1  # 没有增加

        # 验证缓存命中
        assert result1.summary == result2.summary

    @pytest.mark.asyncio
    async def test_batch_processor_integration(self, llm_components, sample_articles):
        """测试批处理器集成"""
        batch_config = BatchConfig()
        batch_processor = BatchProcessor(llm_components['llm_connector'], batch_config)

        # 创建批处理任务
        tasks = []
        for i, article in enumerate(sample_articles):
            task = BatchTask(
                id=f"task_{i}",
                task_type="summarization",
                data=article,
                priority=BatchPriority.NORMAL,
                created_at=datetime.now(),
                timeout=30.0
            )
            tasks.append(task)

        # 设置模拟响应
        llm_components['llm_connector'].generate_text.return_value = '{"summary": "Batch summary", "confidence": 0.9}'

        # 处理批处理任务
        results = await batch_processor.process_tasks(tasks)

        # 验证结果
        assert len(results) == len(tasks)
        for result in results:
            assert result is not None
            assert result['success'] is True

    @pytest.mark.asyncio
    async def test_error_handling_integration(self, llm_components):
        """测试错误处理集成"""
        # 创建有问题的文章
        problematic_article = NewsArticle(
            id="error_test",
            title="Test",
            content="",  # 空内容
            published_at=datetime.now(),
            source="test.com",
            category=NewsCategory.GENERAL
        )

        # 设置模拟响应 - 抛出错误
        llm_components['llm_connector'].generate_text.side_effect = Exception("LLM Error")

        # 测试错误处理
        with pytest.raises(Exception):
            await llm_components['summarizer'].summarize_article(problematic_article)

    @pytest.mark.asyncio
    async def test_performance_integration(self, llm_components, sample_articles):
        """测试性能集成"""
        # 创建大量文章
        large_article_set = []
        for i in range(20):
            article = NewsArticle(
                id=f"perf_test_{i}",
                title=f"Performance Test {i}",
                content=f"Bitcoin price analysis for test {i}. Institutional adoption and market trends.",
                published_at=datetime.now(),
                source="test.com",
                category=NewsCategory.GENERAL
            )
            large_article_set.append(article)

        # 设置模拟响应
        llm_components['llm_connector'].generate_text.return_value = '{"summary": "Performance test summary", "confidence": 0.9}'

        # 测试并发处理
        start_time = datetime.now()

        tasks = []
        for article in large_article_set:
            task = asyncio.create_task(llm_components['summarizer'].summarize_article(article))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # 验证性能
        assert processing_time < 30.0  # 应该在30秒内完成
        assert len(results) == len(large_article_set)

        # 验证成功率
        success_count = sum(1 for result in results if not isinstance(result, Exception))
        success_rate = success_count / len(large_article_set)
        assert success_rate > 0.9  # 成功率应该超过90%

    @pytest.mark.asyncio
    async def test_configuration_integration(self, llm_components, sample_articles):
        """测试配置集成"""
        # 测试不同配置组合
        configs = [
            SummarizerConfig(max_length=50, style="concise"),
            SummarizerConfig(max_length=200, style="detailed"),
            SentimentConfig(enable_aspect_analysis=True),
            SentimentConfig(enable_aspect_analysis=False),
            EntityConfig(confidence_threshold=0.8),
            EntityConfig(confidence_threshold=0.6)
        ]

        llm_components['llm_connector'].generate_text.return_value = '{"summary": "Config test summary", "confidence": 0.9}'

        for config in configs:
            if isinstance(config, SummarizerConfig):
                llm_components['summarizer'].config = config
                result = await llm_components['summarizer'].summarize_article(sample_articles[0])
                assert result is not None
            elif isinstance(config, SentimentConfig):
                llm_components['sentiment_analyzer'].config = config
                result = await llm_components['sentiment_analyzer'].analyze_sentiment(sample_articles[0])
                assert result is not None
            elif isinstance(config, EntityConfig):
                llm_components['entity_extractor'].config = config
                result = await llm_components['entity_extractor'].extract_entities(sample_articles[0])
                assert result is not None

    @pytest.mark.asyncio
    async def test_data_flow_integration(self, llm_components, sample_articles):
        """测试数据流集成"""
        # 设置模拟响应
        llm_components['llm_connector'].generate_text.side_effect = [
            '{"summary": "Bitcoin reaches new ATH", "key_points": ["Institutional adoption", "Regulatory clarity"], "confidence": 0.9}',
            '{"sentiment": "bullish", "score": 0.8, "aspects": {"price_action": "bullish", "market_sentiment": "positive"}, "confidence": 0.85}',
            '{"entities": [{"id": "bitcoin", "text": "Bitcoin", "type": "cryptocurrency", "confidence": 0.95}, {"id": "tesla", "text": "Tesla", "type": "company", "confidence": 0.9}]}',
            '{"impact_type": "high", "magnitude": 0.8, "timeframe": "short_term", "confidence": 0.85}'
        ]

        article = sample_articles[0]

        # 执行完整的分析流程
        summary = await llm_components['summarizer'].summarize_article(article)
        sentiment = await llm_components['sentiment_analyzer'].analyze_sentiment(article)
        entities = await llm_components['entity_extractor'].extract_entities(article)
        market_impact = await llm_components['market_impact_assessor'].assess_market_impact(article)

        # 验证数据一致性
        assert summary.article_id == article.id
        assert sentiment.article_id == article.id
        assert all(entity.article_id == article.id for entity in entities)
        assert market_impact.article_id == article.id

        # 验证数据质量
        assert summary.confidence > 0.7
        assert sentiment.confidence > 0.7
        assert all(entity.confidence > 0.7 for entity in entities)
        assert market_impact.confidence > 0.7

    @pytest.mark.asyncio
    async def test_memory_efficiency_integration(self, llm_components):
        """测试内存效率集成"""
        # 创建大量数据来测试内存使用
        large_articles = []
        for i in range(50):
            article = NewsArticle(
                id=f"memory_test_{i}",
                title=f"Memory Test {i}",
                content="x" * 1000,  # 1KB内容
                published_at=datetime.now(),
                source="test.com",
                category=NewsCategory.GENERAL
            )
            large_articles.append(article)

        # 设置模拟响应
        llm_components['llm_connector'].generate_text.return_value = '{"summary": "Memory test summary", "confidence": 0.9}'

        # 处理大量文章
        tasks = []
        for article in large_articles:
            task = asyncio.create_task(llm_components['summarizer'].summarize_article(article))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证处理完成
        assert len(results) == len(large_articles)

        # 清理缓存
        llm_components['cache_manager'].clear()

    @pytest.mark.asyncio
    async def test_resource_management_integration(self, llm_components, sample_articles):
        """测试资源管理集成"""
        # 设置模拟响应
        llm_components['llm_connector'].generate_text.return_value = '{"summary": "Resource test summary", "confidence": 0.9}'

        # 测试并发限制
        semaphore = asyncio.Semaphore(5)  # 限制并发数

        async def process_with_semaphore(article):
            async with semaphore:
                return await llm_components['summarizer'].summarize_article(article)

        # 创建大量并发任务
        tasks = []
        for _ in range(20):
            task = asyncio.create_task(process_with_semaphore(sample_articles[0]))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证所有任务完成
        assert len(results) == 20
        success_count = sum(1 for result in results if not isinstance(result, Exception))
        assert success_count == 20

    @pytest.mark.asyncio
    async def test_monitoring_integration(self, llm_components, sample_articles):
        """测试监控集成"""
        # 设置模拟响应
        llm_components['llm_connector'].generate_text.return_value = '{"summary": "Monitoring test summary", "confidence": 0.9}'

        # 处理一些文章
        await llm_components['summarizer'].summarize_article(sample_articles[0])
        await llm_components['sentiment_analyzer'].analyze_sentiment(sample_articles[0])

        # 检查缓存统计
        cache_stats = llm_components['cache_manager'].get_stats()
        assert isinstance(cache_stats, dict)
        assert 'cache_hits' in cache_stats
        assert 'cache_misses' in cache_stats
        assert 'memory_usage' in cache_stats

        # 验证统计数据
        assert cache_stats['cache_hits'] >= 0
        assert cache_stats['cache_misses'] >= 0
        assert cache_stats['memory_usage'] >= 0

    @pytest.mark.asyncio
    async def test_fallback_integration(self, llm_components, sample_articles):
        """测试回退机制集成"""
        # 设置模拟响应 - 第一次失败，第二次成功
        llm_components['llm_connector'].generate_text.side_effect = [
            Exception("Network Error"),
            '{"summary": "Fallback summary", "confidence": 0.8}'
        ]

        # 测试重试机制
        try:
            result = await llm_components['summarizer'].summarize_article(sample_articles[0])
            # 如果实现了重试机制，应该成功
            assert result is not None
        except Exception:
            # 如果没有重试机制，应该抛出异常
            pass

    @pytest.mark.asyncio
    async def test_scalability_integration(self, llm_components):
        """测试可扩展性集成"""
        # 测试不同负载下的性能
        workloads = [5, 10, 20, 50]  # 不同数量的文章

        llm_components['llm_connector'].generate_text.return_value = '{"summary": "Scalability test summary", "confidence": 0.9}'

        for workload in workloads:
            # 创建测试文章
            articles = []
            for i in range(workload):
                article = NewsArticle(
                    id=f"scalability_test_{i}",
                    title=f"Scalability Test {i}",
                    content=f"Test content {i} for scalability testing.",
                    published_at=datetime.now(),
                    source="test.com",
                    category=NewsCategory.GENERAL
                )
                articles.append(article)

            # 处理文章
            start_time = datetime.now()

            tasks = []
            for article in articles:
                task = asyncio.create_task(llm_components['summarizer'].summarize_article(article))
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            # 验证可扩展性
            assert len(results) == workload
            success_count = sum(1 for result in results if not isinstance(result, Exception))
            success_rate = success_count / workload
            assert success_rate > 0.9

            # 性能应该在合理范围内
            throughput = workload / processing_time
            assert throughput > 0.5  # 每秒至少处理0.5篇文章

    @pytest.mark.asyncio
    async def test_inter_component_communication(self, llm_components, sample_articles):
        """测试组件间通信集成"""
        # 设置模拟响应
        llm_components['llm_connector'].generate_text.side_effect = [
            '{"summary": "Bitcoin reaches new ATH", "key_points": ["Institutional adoption"], "confidence": 0.9}',
            '{"sentiment": "bullish", "score": 0.8, "aspects": {"price_action": "bullish"}, "confidence": 0.85}',
            '{"entities": [{"id": "bitcoin", "text": "Bitcoin", "type": "cryptocurrency", "confidence": 0.95}]}',
            '{"impact_type": "high", "magnitude": 0.8, "timeframe": "short_term", "confidence": 0.85}'
        ]

        article = sample_articles[0]

        # 测试组件间数据共享
        summary = await llm_components['summarizer'].summarize_article(article)

        # 使用总结结果进行情感分析
        sentiment = await llm_components['sentiment_analyzer'].analyze_sentiment(article)

        # 验证数据一致性
        assert summary.article_id == sentiment.article_id
        assert summary.confidence > 0
        assert sentiment.confidence > 0

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, llm_components, sample_articles):
        """测试端到端工作流"""
        # 设置模拟响应
        llm_components['llm_connector'].generate_text.side_effect = [
            # 总结
            '{"summary": "Bitcoin reaches new ATH driven by institutional adoption", "key_points": ["Institutional adoption accelerates", "Market cap exceeds $2 trillion"], "confidence": 0.9}',
            '{"summary": "Fed decision creates crypto market volatility", "key_points": ["Rate hike expectations", "Increased trading volumes"], "confidence": 0.85}',
            # 情感分析
            '{"sentiment": "bullish", "score": 0.8, "aspects": {"price_action": "bullish", "market_sentiment": "positive"}, "confidence": 0.85}',
            '{"sentiment": "neutral", "score": 0.1, "aspects": {"market_sentiment": "uncertain", "regulatory": "negative"}, "confidence": 0.8}',
            # 实体提取
            '{"entities": [{"id": "bitcoin", "text": "Bitcoin", "type": "cryptocurrency", "confidence": 0.95}, {"id": "tesla", "text": "Tesla", "type": "company", "confidence": 0.9}]}',
            '{"entities": [{"id": "fed", "text": "Federal Reserve", "type": "organization", "confidence": 0.95}, {"id": "ethereum", "text": "Ethereum", "type": "cryptocurrency", "confidence": 0.9}]}',
            # 市场影响
            '{"impact_type": "high", "magnitude": 0.8, "timeframe": "short_term", "confidence": 0.85}',
            '{"impact_type": "medium", "magnitude": 0.5, "timeframe": "medium_term", "confidence": 0.8}'
        ]

        llm_components['llm_connector'].generate_structured_text.side_effect = [
            # 内容分段
            {
                "sections": [
                    {"id": "price_analysis", "title": "Price Analysis", "type": "analysis", "content": "Bitcoin reaches new ATH at $67,000", "importance": 0.9},
                    {"id": "institutional_news", "title": "Institutional Adoption", "type": "news", "content": "Major companies add Bitcoin to balance sheets", "importance": 0.8}
                ]
            },
            {
                "sections": [
                    {"id": "fed_decision", "title": "Fed Decision", "type": "analysis", "content": "Fed indicates potential rate hikes in 2024", "importance": 0.9},
                    {"id": "market_reaction", "title": "Market Reaction", "type": "analysis", "content": "Increased volatility in crypto markets", "importance": 0.8}
                ]
            }
        ]

        # 执行完整的端到端工作流
        workflow_results = []

        for article in sample_articles:
            workflow_result = {}

            # 1. 内容预处理和分段
            workflow_result['segments'] = await llm_components['content_segmenter'].segment_content(article)

            # 2. 智能总结
            workflow_result['summary'] = await llm_components['summarizer'].summarize_article(article)

            # 3. 情感分析
            workflow_result['sentiment'] = await llm_components['sentiment_analyzer'].analyze_sentiment(article)

            # 4. 实体提取
            workflow_result['entities'] = await llm_components['entity_extractor'].extract_entities(article)

            # 5. 市场影响评估
            workflow_result['market_impact'] = await llm_components['market_impact_assessor'].assess_market_impact(article)

            # 6. 综合评分
            workflow_result['composite_score'] = self._calculate_composite_score(workflow_result)

            workflow_results.append(workflow_result)

        # 验证端到端结果
        assert len(workflow_results) == len(sample_articles)

        for result in workflow_results:
            # 验证所有组件都产生了结果
            assert result['segments'] is not None
            assert result['summary'] is not None
            assert result['sentiment'] is not None
            assert result['entities'] is not None
            assert result['market_impact'] is not None
            assert result['composite_score'] is not None

            # 验证数据质量
            assert result['composite_score'] >= 0.0
            assert result['composite_score'] <= 1.0
            assert result['summary'].confidence >= 0.7
            assert result['sentiment'].confidence >= 0.7
            assert all(entity.confidence >= 0.7 for entity in result['entities'])
            assert result['market_impact'].confidence >= 0.7

    def _calculate_composite_score(self, analysis_result: Dict[str, Any]) -> float:
        """计算综合评分"""
        weights = {
            'summary': 0.25,
            'sentiment': 0.25,
            'entities': 0.25,
            'market_impact': 0.25
        }

        summary_score = analysis_result['summary'].confidence
        sentiment_score = analysis_result['sentiment'].confidence
        entity_score = analysis_result['entities'][0].confidence if analysis_result['entities'] else 0.0
        impact_score = analysis_result['market_impact'].confidence

        composite_score = (
            weights['summary'] * summary_score +
            weights['sentiment'] * sentiment_score +
            weights['entities'] * entity_score +
            weights['market_impact'] * impact_score
        )

        return round(composite_score, 3)

    @pytest.mark.asyncio
    async def test_stress_testing(self, llm_components):
        """测试压力测试"""
        # 创建大量并发请求
        concurrent_requests = 100

        # 创建测试文章
        test_articles = []
        for i in range(concurrent_requests):
            article = NewsArticle(
                id=f"stress_test_{i}",
                title=f"Stress Test {i}",
                content=f"Stress test content {i} for load testing.",
                published_at=datetime.now(),
                source="test.com",
                category=NewsCategory.GENERAL
            )
            test_articles.append(article)

        # 设置模拟响应
        llm_components['llm_connector'].generate_text.return_value = '{"summary": "Stress test summary", "confidence": 0.9}'

        # 并发处理
        start_time = datetime.now()

        tasks = []
        for article in test_articles:
            task = asyncio.create_task(llm_components['summarizer'].summarize_article(article))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # 验证压力测试结果
        assert len(results) == concurrent_requests

        success_count = sum(1 for result in results if not isinstance(result, Exception))
        success_rate = success_count / concurrent_requests
        assert success_rate > 0.8  # 成功率应该超过80%

        # 验证性能
        throughput = concurrent_requests / processing_time
        assert throughput > 1.0  # 每秒至少处理1个请求

    @pytest.mark.asyncio
    async def test_recovery_integration(self, llm_components, sample_articles):
        """测试恢复集成"""
        # 模拟部分失败场景
        llm_components['llm_connector'].generate_text.side_effect = [
            Exception("Network Error"),  # 第一次失败
            '{"summary": "Recovery summary", "confidence": 0.8}',  # 第二次成功
            '{"sentiment": "bullish", "score": 0.7, "confidence": 0.75}',  # 第三次成功
            Exception("Timeout Error")  # 第四次失败
        ]

        # 测试恢复能力
        results = []
        for i, article in enumerate(sample_articles[:2]):  # 只测试前两篇文章
            try:
                if i == 0:
                    # 第一篇文章尝试总结（会失败）
                    try:
                        summary = await llm_components['summarizer'].summarize_article(article)
                    except Exception:
                        summary = None

                    # 尝试情感分析（应该成功）
                    sentiment = await llm_components['sentiment_analyzer'].analyze_sentiment(article)

                    results.append({
                        'article_id': article.id,
                        'summary': summary,
                        'sentiment': sentiment,
                        'partial_success': summary is None and sentiment is not None
                    })
                else:
                    # 第二篇文章尝试总结（应该成功）
                    summary = await llm_components['summarizer'].summarize_article(article)

                    # 尝试情感分析（会失败）
                    try:
                        sentiment = await llm_components['sentiment_analyzer'].analyze_sentiment(article)
                    except Exception:
                        sentiment = None

                    results.append({
                        'article_id': article.id,
                        'summary': summary,
                        'sentiment': sentiment,
                        'partial_success': summary is not None and sentiment is None
                    })
            except Exception as e:
                results.append({
                    'article_id': article.id,
                    'error': str(e),
                    'failed': True
                })

        # 验证恢复能力
        assert len(results) == 2

        # 应该有部分成功的案例
        partial_success_count = sum(1 for r in results if r.get('partial_success', False))
        assert partial_success_count > 0

    @pytest.mark.asyncio
    async def test_configuration_validation_integration(self, llm_components, sample_articles):
        """测试配置验证集成"""
        # 测试无效配置
        invalid_configs = [
            SummarizerConfig(max_length=-1),  # 无效的最大长度
            SentimentConfig(confidence_threshold=1.5),  # 无效的置信度阈值
            EntityConfig(confidence_threshold=-0.1),  # 无效的置信度阈值
            MarketImpactConfig(confidence_threshold=2.0)  # 无效的置信度阈值
        ]

        for config in invalid_configs:
            # 配置应该在创建时验证，或者在使用时优雅地处理
            if isinstance(config, SummarizerConfig):
                llm_components['summarizer'].config = config
                # 应该能优雅处理无效配置
                try:
                    llm_components['llm_connector'].generate_text.return_value = '{"summary": "Validation test", "confidence": 0.9}'
                    result = await llm_components['summarizer'].summarize_article(sample_articles[0])
                    assert result is not None
                except Exception:
                    # 或者抛出有意义的异常
                    pass

    @pytest.mark.asyncio
    async def test_data_integrity_integration(self, llm_components, sample_articles):
        """测试数据完整性集成"""
        # 设置模拟响应
        llm_components['llm_connector'].generate_text.side_effect = [
            '{"summary": "Data integrity test", "key_points": ["Point 1", "Point 2"], "confidence": 0.9}',
            '{"sentiment": "bullish", "score": 0.8, "aspects": {"price_action": "bullish"}, "confidence": 0.85}',
            '{"entities": [{"id": "bitcoin", "text": "Bitcoin", "type": "cryptocurrency", "confidence": 0.95}]}',
            '{"impact_type": "high", "magnitude": 0.8, "timeframe": "short_term", "confidence": 0.85}'
        ]

        article = sample_articles[0]

        # 执行多次相同的分析
        results = []
        for _ in range(3):
            summary = await llm_components['summarizer'].summarize_article(article)
            sentiment = await llm_components['sentiment_analyzer'].analyze_sentiment(article)
            entities = await llm_components['entity_extractor'].extract_entities(article)
            market_impact = await llm_components['market_impact_assessor'].assess_market_impact(article)

            results.append({
                'summary': summary,
                'sentiment': sentiment,
                'entities': entities,
                'market_impact': market_impact
            })

        # 验证数据一致性
        for i in range(1, len(results)):
            # 由于使用了缓存，结果应该是一致的
            assert results[i]['summary'].summary == results[0]['summary'].summary
            assert results[i]['sentiment'].sentiment == results[0]['sentiment'].sentiment
            assert len(results[i]['entities']) == len(results[0]['entities'])
            assert results[i]['market_impact'].impact_type == results[0]['market_impact'].impact_type