"""
Tests for batch processor module
"""

import pytest
import asyncio
import time
import threading
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from ..batch_processor import (
    BatchProcessor, BatchConfig, BatchTask, BatchResult, BatchStats,
    BatchPriority, BatchStrategy, RateLimiter
)
from ..llm_connector import LLMConnector, LLMConfig, LLMMessage, LLMResponse
from ..summarizer import NewsSummarizer, SummaryConfig, SummaryResult
from ..sentiment_analyzer import SentimentAnalyzer, SentimentConfig, SentimentAnalysisResult
from ..entity_extractor import EntityExtractor, EntityConfig, EntityExtractionResult
from ..market_impact import MarketImpactAssessor, MarketImpactConfig, MarketImpactResult
from ...models.base import NewsArticle


class TestBatchConfig:
    """测试批处理配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = BatchConfig()
        assert config.max_batch_size == 10
        assert config.max_concurrent_requests == 5
        assert config.processing_timeout == 60.0
        assert config.retry_attempts == 3
        assert config.retry_delay == 1.0
        assert config.batch_strategy == BatchStrategy.ADAPTIVE
        assert config.enable_rate_limiting is True
        assert config.requests_per_minute == 60
        assert config.enable_memory_management is True
        assert config.max_memory_usage == 1024 * 1024 * 1024
        assert config.enable_progress_tracking is True
        assert config.enable_error_handling is True
        assert config.enable_result_caching is True
        assert config.priority_weighting is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = BatchConfig(
            max_batch_size=20,
            max_concurrent_requests=10,
            processing_timeout=120.0,
            batch_strategy=BatchStrategy.PARALLEL,
            enable_rate_limiting=False,
            requests_per_minute=120
        )
        assert config.max_batch_size == 20
        assert config.max_concurrent_requests == 10
        assert config.processing_timeout == 120.0
        assert config.batch_strategy == BatchStrategy.PARALLEL
        assert config.enable_rate_limiting is False
        assert config.requests_per_minute == 120


class TestBatchTask:
    """测试批处理任务类"""

    def test_task_creation(self):
        """测试任务创建"""
        task = BatchTask(
            id="test-task-1",
            task_type="summarize",
            data={"content": "test"},
            priority=BatchPriority.HIGH,
            created_at=datetime.now(),
            timeout=30.0
        )
        assert task.id == "test-task-1"
        assert task.task_type == "summarize"
        assert task.data == {"content": "test"}
        assert task.priority == BatchPriority.HIGH
        assert task.timeout == 30.0
        assert task.retry_count == 0
        assert task.callback is None
        assert task.metadata == {}

    def test_task_with_metadata(self):
        """测试带元数据的任务"""
        metadata = {"source": "test", "priority": "urgent"}
        callback = Mock()

        task = BatchTask(
            id="test-task-2",
            task_type="sentiment",
            data="test content",
            priority=BatchPriority.CRITICAL,
            created_at=datetime.now(),
            timeout=60.0,
            callback=callback,
            metadata=metadata
        )
        assert task.callback == callback
        assert task.metadata == metadata


class TestBatchResult:
    """测试批处理结果类"""

    def test_result_creation(self):
        """测试结果创建"""
        result = BatchResult(
            task_id="test-task-1",
            task_type="summarize",
            result={"summary": "test summary"},
            success=True,
            processing_time=1.5
        )
        assert result.task_id == "test-task-1"
        assert result.task_type == "summarize"
        assert result.result == {"summary": "test summary"}
        assert result.success is True
        assert result.processing_time == 1.5
        assert result.error_message is None
        assert result.metadata == {}

    def test_result_creation_with_error(self):
        """测试错误结果创建"""
        result = BatchResult(
            task_id="test-task-2",
            task_type="sentiment",
            result=None,
            success=False,
            processing_time=2.0,
            error_message="Processing failed",
            metadata={"retry_count": 3}
        )
        assert result.success is False
        assert result.error_message == "Processing failed"
        assert result.metadata["retry_count"] == 3


class TestRateLimiter:
    """测试速率限制器"""

    def test_rate_limiter_init(self):
        """测试速率限制器初始化"""
        limiter = RateLimiter(60)
        assert limiter.requests_per_minute == 60
        assert len(limiter.requests) == 0

    def test_can_proceed_under_limit(self):
        """测试在限制内是否可以继续"""
        limiter = RateLimiter(60)
        assert limiter.can_proceed() is True
        assert len(limiter.requests) == 1

    def test_can_proceed_over_limit(self):
        """测试超过限制时是否可以继续"""
        limiter = RateLimiter(1)

        # 第一次请求应该通过
        assert limiter.can_proceed() is True

        # 第二次请求应该被限制
        assert limiter.can_proceed() is False

    def test_wait_time_calculation(self):
        """测试等待时间计算"""
        limiter = RateLimiter(1)
        limiter.requests.append(datetime.now() - timedelta(seconds=30))

        wait_time = limiter.wait_time()
        assert 28.0 <= wait_time <= 32.0  # 大约30秒

    def test_old_requests_cleanup(self):
        """测试旧请求清理"""
        limiter = RateLimiter(1)
        old_time = datetime.now() - timedelta(minutes=2)
        limiter.requests.append(old_time)

        # 调用can_proceed应该清理旧请求
        limiter.can_proceed()
        assert old_time not in limiter.requests


class TestBatchProcessor:
    """测试批处理器"""

    @pytest.fixture
    def mock_llm_connector(self):
        """模拟LLM连接器"""
        connector = Mock(spec=LLMConnector)

        async def mock_generate_response(messages, config=None):
            return LLMResponse(
                content="Mock response",
                usage={"total_tokens": 10},
                model="test-model",
                provider="mock",
                response_time=0.1
            )

        connector.generate_response = AsyncMock(side_effect=mock_generate_response)
        return connector

    @pytest.fixture
    def sample_article(self):
        """示例文章"""
        return NewsArticle(
            id="test-article-1",
            title="Test Article",
            content="This is a test article content for batch processing.",
            source="Test Source"
        )

    @pytest.fixture
    def batch_processor(self, mock_llm_connector):
        """批处理器实例"""
        config = BatchConfig(
            max_concurrent_requests=2,
            max_batch_size=5,
            enable_rate_limiting=False,
            retry_attempts=2,
            processing_timeout=10.0
        )
        return BatchProcessor(mock_llm_connector, config)

    def test_init(self, batch_processor):
        """测试初始化"""
        assert batch_processor.llm_connector is not None
        assert batch_processor.config.max_concurrent_requests == 2
        assert batch_processor.config.max_batch_size == 5
        assert batch_processor.is_running is False
        assert batch_processor.stats.total_tasks_processed == 0
        assert batch_processor.stats.successful_tasks == 0
        assert batch_processor.stats.failed_tasks == 0

    @pytest.mark.asyncio
    async def test_start_and_stop(self, batch_processor):
        """测试启动和停止"""
        # 启动处理器
        await batch_processor.start()
        assert batch_processor.is_running is True

        # 短暂等待确保处理循环启动
        await asyncio.sleep(0.1)

        # 停止处理器
        await batch_processor.stop()
        assert batch_processor.is_running is False

    @pytest.mark.asyncio
    async def test_submit_task(self, batch_processor, sample_article):
        """测试提交任务"""
        await batch_processor.start()

        task_id = await batch_processor.submit_task(
            "summarize",
            sample_article,
            BatchPriority.NORMAL
        )

        assert isinstance(task_id, str)
        assert "summarize" in task_id
        assert batch_processor.stats.current_queue_size > 0

        await batch_processor.stop()

    @pytest.mark.asyncio
    async def test_submit_task_with_metadata(self, batch_processor, sample_article):
        """测试提交带元数据的任务"""
        await batch_processor.start()

        callback = Mock()
        metadata = {"source": "test", "category": "analysis"}

        task_id = await batch_processor.submit_task(
            "sentiment",
            sample_article,
            BatchPriority.HIGH,
            callback=callback,
            metadata=metadata
        )

        assert isinstance(task_id, str)
        assert "sentiment" in task_id

        await batch_processor.stop()

    def test_calculate_queue_priority(self, batch_processor):
        """测试队列优先级计算"""
        task = BatchTask(
            id="test-task",
            task_type="summarize",
            data="test",
            priority=BatchPriority.HIGH,
            created_at=datetime.now(),
            timeout=30.0
        )

        priority = batch_processor._calculate_queue_priority(task)
        assert isinstance(priority, int)
        assert priority > 0

    @pytest.mark.asyncio
    async def test_process_summarization_task(self, batch_processor, sample_article):
        """测试处理摘要任务"""
        task = BatchTask(
            id="test-summarize",
            task_type="summarize",
            data=sample_article,
            priority=BatchPriority.NORMAL,
            created_at=datetime.now(),
            timeout=30.0
        )

        # 模拟summarizer
        batch_processor.summarizer.summarize_article = AsyncMock(
            return_value=SummaryResult(
                summary="Test summary",
                key_points=["Point 1"],
                confidence=0.8,
                processing_time=0.5,
                word_count={"original": 50, "summary": 10}
            )
        )

        result = await batch_processor._process_summarization(task)

        assert isinstance(result, SummaryResult)
        assert result.summary == "Test summary"
        assert len(result.key_points) == 1

    @pytest.mark.asyncio
    async def test_process_sentiment_analysis_task(self, batch_processor, sample_article):
        """测试处理情感分析任务"""
        from ..sentiment_analyzer import SentimentScore, SentimentCategory

        task = BatchTask(
            id="test-sentiment",
            task_type="sentiment",
            data=sample_article,
            priority=BatchPriority.NORMAL,
            created_at=datetime.now(),
            timeout=30.0
        )

        # 模拟sentiment_analyzer
        sentiment_score = SentimentScore(
            category=SentimentCategory.POSITIVE,
            score=0.7,
            confidence=0.8,
            explanation="Positive sentiment",
            intensity=0.6
        )

        batch_processor.sentiment_analyzer.analyze_sentiment = AsyncMock(
            return_value=SentimentAnalysisResult(
                overall_sentiment=sentiment_score,
                aspect_sentiments={},
                market_impact_indicators={},
                temporal_indicators={},
                reliability_score=0.8,
                processing_time=0.5,
                metadata={}
            )
        )

        result = await batch_processor._process_sentiment_analysis(task)

        assert isinstance(result, SentimentAnalysisResult)
        assert result.overall_sentiment.category == SentimentCategory.POSITIVE

    @pytest.mark.asyncio
    async def test_process_entity_extraction_task(self, batch_processor, sample_article):
        """测试处理实体提取任务"""
        from ..entity_extractor import Entity, EntityType

        task = BatchTask(
            id="test-entity",
            task_type="extract_entities",
            data=sample_article,
            priority=BatchPriority.NORMAL,
            created_at=datetime.now(),
            timeout=30.0
        )

        # 模拟entity_extractor
        entity = Entity(
            id="test-entity-1",
            text="Bitcoin",
            type=EntityType.CRYPTOCURRENCY,
            start_position=0,
            end_position=7,
            confidence=0.9
        )

        batch_processor.entity_extractor.extract_entities = AsyncMock(
            return_value=EntityExtractionResult(
                entities=[entity],
                relationships=[],
                entity_types_count={"cryptocurrency": 1},
                processing_time=0.5,
                metadata={}
            )
        )

        result = await batch_processor._process_entity_extraction(task)

        assert isinstance(result, EntityExtractionResult)
        assert len(result.entities) == 1
        assert result.entities[0].text == "Bitcoin"

    @pytest.mark.asyncio
    async def test_process_market_impact_task(self, batch_processor, sample_article):
        """测试处理市场影响评估任务"""
        from ..market_impact import ImpactScore, ImpactType, ImpactTimeframe, ImpactMagnitude

        task = BatchTask(
            id="test-market-impact",
            task_type="market_impact",
            data=sample_article,
            priority=BatchPriority.NORMAL,
            created_at=datetime.now(),
            timeout=30.0
        )

        # 模拟market_impact_assessor
        impact_score = ImpactScore(
            impact_type=ImpactType.PRICE_VOLATILITY,
            timeframe=ImpactTimeframe.IMMEDIATE,
            magnitude=ImpactMagnitude.MODERATE,
            confidence=0.7,
            probability=0.6,
            direction="positive",
            reasoning="Moderate positive impact"
        )

        batch_processor.market_impact_assessor.assess_market_impact = AsyncMock(
            return_value=MarketImpactResult(
                overall_impact=impact_score,
                impact_breakdown={},
                market_sentiment={},
                risk_assessment={},
                opportunity_analysis={},
                correlation_analysis={},
                processing_time=0.5,
                metadata={}
            )
        )

        result = await batch_processor._process_market_impact(task)

        assert isinstance(result, MarketImpactResult)
        assert result.overall_impact.magnitude == ImpactMagnitude.MODERATE

    @pytest.mark.asyncio
    async def test_process_comprehensive_analysis_task(self, batch_processor, sample_article):
        """测试处理综合分析任务"""
        task = BatchTask(
            id="test-comprehensive",
            task_type="comprehensive",
            data=sample_article,
            priority=BatchPriority.NORMAL,
            created_at=datetime.now(),
            timeout=60.0
        )

        # 模拟所有组件
        batch_processor.summarizer.summarize_article = AsyncMock(
            return_value=SummaryResult(
                summary="Test summary",
                key_points=["Point 1"],
                confidence=0.8,
                processing_time=0.5,
                word_count={"original": 50, "summary": 10}
            )
        )

        from ..sentiment_analyzer import SentimentScore, SentimentCategory
        sentiment_score = SentimentScore(
            category=SentimentCategory.POSITIVE,
            score=0.7,
            confidence=0.8,
            explanation="Positive sentiment",
            intensity=0.6
        )

        batch_processor.sentiment_analyzer.analyze_sentiment = AsyncMock(
            return_value=SentimentAnalysisResult(
                overall_sentiment=sentiment_score,
                aspect_sentiments={},
                market_impact_indicators={},
                temporal_indicators={},
                reliability_score=0.8,
                processing_time=0.5,
                metadata={}
            )
        )

        # 模拟其他组件返回基本结果
        batch_processor.content_segmenter.segment_content = AsyncMock()
        batch_processor.entity_extractor.extract_entities = AsyncMock()
        batch_processor.market_impact_assessor.assess_market_impact = AsyncMock()

        result = await batch_processor._process_comprehensive_analysis(task)

        assert isinstance(result, dict)
        assert "article_id" in result
        assert "summary" in result
        assert "sentiment" in result

    @pytest.mark.asyncio
    async def test_task_processing_with_retry(self, batch_processor, sample_article):
        """测试任务重试机制"""
        task = BatchTask(
            id="test-retry",
            task_type="summarize",
            data=sample_article,
            priority=BatchPriority.NORMAL,
            created_at=datetime.now(),
            timeout=30.0
        )

        # 第一次调用失败，第二次成功
        call_count = 0
        async def mock_summarize(article):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First attempt failed")
            return SummaryResult(
                summary="Retry success",
                key_points=["Success"],
                confidence=0.8,
                processing_time=0.5,
                word_count={"original": 50, "summary": 10}
            )

        batch_processor.summarizer.summarize_article = AsyncMock(side_effect=mock_summarize)

        # 减少重试延迟以便快速测试
        batch_processor.config.retry_delay = 0.1

        result = await batch_processor._process_task(task)

        assert isinstance(result, BatchResult)
        assert result.success is True
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_task_processing_max_retries_exceeded(self, batch_processor, sample_article):
        """测试超过最大重试次数"""
        task = BatchTask(
            id="test-max-retry",
            task_type="summarize",
            data=sample_article,
            priority=BatchPriority.NORMAL,
            created_at=datetime.now(),
            timeout=30.0
        )

        # 总是失败
        batch_processor.summarizer.summarize_article = AsyncMock(
            side_effect=Exception("Always fails")
        )

        # 减少重试次数和延迟以便快速测试
        batch_processor.config.retry_attempts = 1
        batch_processor.config.retry_delay = 0.1

        result = await batch_processor._process_task(task)

        assert isinstance(result, BatchResult)
        assert result.success is False
        assert "Always fails" in result.error_message

    @pytest.mark.asyncio
    async def test_get_result(self, batch_processor):
        """测试获取任务结果"""
        await batch_processor.start()

        # 添加一个完成的任务
        test_result = BatchResult(
            task_id="test-get",
            task_type="summarize",
            result={"test": "data"},
            success=True,
            processing_time=1.0
        )

        batch_processor.completed_tasks["test-get"] = test_result

        # 获取结果
        result = await batch_processor.get_result("test-get")
        assert result is not None
        assert result.task_id == "test-get"
        assert result.result == {"test": "data"}

        # 测试获取不存在的任务
        result = await batch_processor.get_result("non-existent", timeout=0.1)
        assert result is None

        await batch_processor.stop()

    @pytest.mark.asyncio
    async def test_wait_for_completion(self, batch_processor):
        """测试等待多个任务完成"""
        await batch_processor.start()

        # 添加完成的任务
        results = {
            "task-1": BatchResult("task-1", "type1", {"data": 1}, True, 1.0),
            "task-2": BatchResult("task-2", "type2", {"data": 2}, True, 1.0)
        }

        for task_id, result in results.items():
            batch_processor.completed_tasks[task_id] = result

        # 等待所有任务完成
        completed = await batch_processor.wait_for_completion(["task-1", "task-2"])
        assert len(completed) == 2
        assert "task-1" in completed
        assert "task-2" in completed

        await batch_processor.stop()

    def test_get_stats(self, batch_processor):
        """测试获取统计信息"""
        stats = batch_processor.get_stats()
        assert isinstance(stats, dict)
        assert "total_tasks_processed" in stats
        assert "successful_tasks" in stats
        assert "failed_tasks" in stats
        assert "is_running" in stats
        assert "queue_size" in stats

    @pytest.mark.asyncio
    async def test_health_check(self, batch_processor):
        """测试健康检查"""
        await batch_processor.start()

        health = await batch_processor.health_check()
        assert health["status"] == "healthy"
        assert "queue_size" in health
        assert "stats" in health
        assert "components" in health

        await batch_processor.stop()

        health = await batch_processor.health_check()
        assert health["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_cancel_task(self, batch_processor, sample_article):
        """测试取消任务"""
        await batch_processor.start()

        # 提交任务
        task_id = await batch_processor.submit_task(
            "summarize",
            sample_article,
            BatchPriority.NORMAL
        )

        # 取消任务
        cancelled = await batch_processor.cancel_task(task_id)
        assert cancelled is True

        # 队列大小应该减少
        assert batch_processor.stats.current_queue_size == 0

        await batch_processor.stop()

    def test_update_config(self, batch_processor):
        """测试更新配置"""
        new_config = BatchConfig(
            max_concurrent_requests=10,
            max_batch_size=20,
            enable_rate_limiting=True,
            requests_per_minute=120
        )

        batch_processor.update_config(new_config)
        assert batch_processor.config.max_concurrent_requests == 10
        assert batch_processor.config.max_batch_size == 20
        assert batch_processor.config.enable_rate_limiting is True
        assert batch_processor.config.requests_per_minute == 120

    @pytest.mark.asyncio
    async def test_clear_completed_tasks(self, batch_processor):
        """测试清理已完成任务"""
        # 添加一些完成的任务
        batch_processor.completed_tasks = {
            "task-1": BatchResult("task-1", "type", {"data": 1}, True, 1.0),
            "task-2": BatchResult("task-2", "type", {"data": 2}, True, 1.0)
        }

        assert len(batch_processor.completed_tasks) == 2

        await batch_processor.clear_completed_tasks()
        assert len(batch_processor.completed_tasks) == 0

    @pytest.mark.asyncio
    async def test_process_immediate(self, batch_processor, sample_article):
        """测试立即处理任务"""
        # 模拟summarizer
        batch_processor.summarizer.summarize_article = AsyncMock(
            return_value=SummaryResult(
                summary="Immediate summary",
                key_points=["Immediate"],
                confidence=0.9,
                processing_time=0.3,
                word_count={"original": 50, "summary": 10}
            )
        )

        result = await batch_processor.process_immediate("summarize", sample_article)

        assert isinstance(result, SummaryResult)
        assert result.summary == "Immediate summary"

    def test_callback_handling(self, batch_processor):
        """测试回调处理"""
        callback = Mock()
        result = BatchResult(
            task_id="test-callback",
            task_type="summarize",
            result={"test": "data"},
            success=True,
            processing_time=1.0
        )

        # 测试同步回调
        batch_processor._call_callback(callback, result)
        callback.assert_called_once_with(result)

        # 测试异步回调
        async_callback = AsyncMock()
        batch_processor._call_callback(async_callback, result)
        # 需要等待异步回调执行
        # 注意：在真实环境中，这会在事件循环中执行


if __name__ == "__main__":
    pytest.main([__file__])