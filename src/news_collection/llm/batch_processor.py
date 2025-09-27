"""
Batch processing optimization module for efficient LLM operations
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, List, Tuple, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import queue
import threading
from datetime import datetime, timedelta

from ..models.base import NewsArticle
from .llm_connector import LLMConnector, LLMMessage, LLMConfig, LLMResponse
from .summarizer import NewsSummarizer, SummaryConfig, SummaryResult
from .sentiment_analyzer import SentimentAnalyzer, SentimentConfig, SentimentAnalysisResult
from .content_segmenter import ContentSegmenter, SectionConfig, SegmentationResult
from .entity_extractor import EntityExtractor, EntityConfig, EntityExtractionResult
from .market_impact import MarketImpactAssessor, MarketImpactConfig, MarketImpactResult


class BatchPriority(Enum):
    """批处理优先级枚举"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class BatchStrategy(Enum):
    """批处理策略枚举"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    SEMAPHORE = "semaphore"
    QUEUE_BASED = "queue_based"
    ADAPTIVE = "adaptive"


@dataclass
class BatchConfig:
    """批处理配置"""
    max_batch_size: int = 10
    max_concurrent_requests: int = 5
    processing_timeout: float = 60.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    batch_strategy: BatchStrategy = BatchStrategy.ADAPTIVE
    enable_rate_limiting: bool = True
    requests_per_minute: int = 60
    enable_memory_management: bool = True
    max_memory_usage: int = 1024 * 1024 * 1024  # 1GB
    enable_progress_tracking: bool = True
    enable_error_handling: bool = True
    enable_result_caching: bool = True
    priority_weighting: bool = True


@dataclass
class BatchTask:
    """批处理任务"""
    id: str
    task_type: str
    data: Any
    priority: BatchPriority
    created_at: datetime
    timeout: float
    retry_count: int = 0
    callback: Optional[Callable] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BatchResult:
    """批处理结果"""
    task_id: str
    task_type: str
    result: Any
    success: bool
    processing_time: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BatchStats:
    """批处理统计"""
    total_batches_processed: int = 0
    total_tasks_processed: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    average_batch_time: float = 0.0
    average_task_time: float = 0.0
    current_queue_size: int = 0
    max_queue_size: int = 0
    memory_usage: float = 0.0
    throughput: float = 0.0  # tasks per second
    error_rate: float = 0.0
    priority_distribution: Dict[str, int] = field(default_factory=dict)


class RateLimiter:
    """速率限制器"""

    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.lock = threading.Lock()

    def can_proceed(self) -> bool:
        """检查是否可以继续请求"""
        with self.lock:
            now = datetime.now()
            # 清理超过1分钟的请求记录
            self.requests = [req_time for req_time in self.requests if now - req_time < timedelta(minutes=1)]

            if len(self.requests) < self.requests_per_minute:
                self.requests.append(now)
                return True
            return False

    def wait_time(self) -> float:
        """获取等待时间"""
        with self.lock:
            if not self.requests:
                return 0.0

            now = datetime.now()
            oldest_request = min(self.requests)
            wait_time = 60.0 - (now - oldest_request).total_seconds()
            return max(0.0, wait_time)


class BatchProcessor:
    """批处理器"""

    def __init__(self, llm_connector: LLMConnector, config: BatchConfig):
        self.llm_connector = llm_connector
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.stats = BatchStats()

        # 初始化组件
        self.summarizer = NewsSummarizer(llm_connector, SummaryConfig())
        self.sentiment_analyzer = SentimentAnalyzer(llm_connector, SentimentConfig())
        self.content_segmenter = ContentSegmenter(llm_connector, SectionConfig())
        self.entity_extractor = EntityExtractor(llm_connector, EntityConfig())
        self.market_impact_assessor = MarketImpactAssessor(llm_connector, MarketImpactConfig())

        # 任务队列
        self.task_queue = queue.PriorityQueue()
        self.result_queue = queue.Queue()

        # 速率限制
        self.rate_limiter = RateLimiter(self.config.requests_per_minute) if self.config.enable_rate_limiting else None

        # 并发控制
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_requests)

        # 状态控制
        self.is_running = False
        self.processing_tasks = {}
        self.completed_tasks = {}

        # 线程安全
        self.lock = threading.Lock()

        # 初始化优先级分布
        for priority in BatchPriority:
            self.stats.priority_distribution[priority.value] = 0

    async def start(self):
        """启动批处理器"""
        if self.is_running:
            return

        self.is_running = True
        self.logger.info("Batch processor started")

        # 启动处理循环
        asyncio.create_task(self._processing_loop())

    async def stop(self):
        """停止批处理器"""
        self.is_running = False
        self.logger.info("Batch processor stopping...")

        # 等待当前任务完成
        await self._wait_for_completion()

        # 关闭执行器
        self.executor.shutdown(wait=True)
        self.logger.info("Batch processor stopped")

    async def submit_task(self, task_type: str, data: Any, priority: BatchPriority = BatchPriority.NORMAL,
                         callback: Optional[Callable] = None, timeout: Optional[float] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """提交任务"""
        task_id = f"{task_type}_{int(time.time() * 1000)}_{len(self.processing_tasks)}"

        task = BatchTask(
            id=task_id,
            task_type=task_type,
            data=data,
            priority=priority,
            created_at=datetime.now(),
            timeout=timeout or self.config.processing_timeout,
            callback=callback,
            metadata=metadata or {}
        )

        # 根据优先级计算队列优先级
        queue_priority = self._calculate_queue_priority(task)

        with self.lock:
            self.task_queue.put((queue_priority, task))
            self.stats.current_queue_size = self.task_queue.qsize()
            self.stats.max_queue_size = max(self.stats.max_queue_size, self.stats.current_queue_size)
            self.stats.priority_distribution[priority.value] += 1

        self.logger.debug(f"Task {task_id} submitted with priority {priority.value}")
        return task_id

    def _calculate_queue_priority(self, task: BatchTask) -> int:
        """计算队列优先级"""
        if self.config.priority_weighting:
            priority_map = {
                BatchPriority.CRITICAL: 1,
                BatchPriority.HIGH: 2,
                BatchPriority.NORMAL: 3,
                BatchPriority.LOW: 4
            }
            base_priority = priority_map[task.priority]

            # 根据等待时间调整优先级（越久等待优先级越高）
            wait_time = (datetime.now() - task.created_at).total_seconds()
            time_bonus = int(wait_time / 10)  # 每10秒提升一级

            return max(1, base_priority - time_bonus)
        else:
            return 0

    async def _processing_loop(self):
        """处理循环"""
        while self.is_running:
            try:
                if not self.task_queue.empty():
                    # 获取下一个任务
                    queue_priority, task = self.task_queue.get_nowait()

                    # 更新队列大小统计
                    with self.lock:
                        self.stats.current_queue_size = self.task_queue.qsize()

                    # 处理任务
                    asyncio.create_task(self._process_task(task))

                else:
                    # 队列为空，短暂休眠
                    await asyncio.sleep(0.1)

            except queue.Empty:
                await asyncio.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Error in processing loop: {str(e)}")
                await asyncio.sleep(1)

    async def _process_task(self, task: BatchTask):
        """处理单个任务"""
        start_time = time.time()
        task_id = task.id

        try:
            self.logger.debug(f"Processing task {task_id}")

            # 检查速率限制
            if self.rate_limiter and not self.rate_limiter.can_proceed():
                wait_time = self.rate_limiter.wait_time()
                await asyncio.sleep(wait_time)

            # 获取信号量
            async with self.semaphore:
                # 根据任务类型处理
                if task.task_type == "summarize":
                    result = await self._process_summarization(task)
                elif task.task_type == "sentiment":
                    result = await self._process_sentiment_analysis(task)
                elif task.task_type == "segment":
                    result = await self._process_content_segmentation(task)
                elif task.task_type == "extract_entities":
                    result = await self._process_entity_extraction(task)
                elif task.task_type == "market_impact":
                    result = await self._process_market_impact(task)
                elif task.task_type == "comprehensive":
                    result = await self._process_comprehensive_analysis(task)
                else:
                    raise ValueError(f"Unknown task type: {task.task_type}")

                # 创建批处理结果
                batch_result = BatchResult(
                    task_id=task_id,
                    task_type=task.task_type,
                    result=result,
                    success=True,
                    processing_time=time.time() - start_time,
                    metadata=task.metadata
                )

                # 更新统计
                self._update_task_stats(batch_result, True)

                # 调用回调函数
                if task.callback:
                    await self._call_callback(task.callback, batch_result)

                # 存储结果
                with self.lock:
                    self.completed_tasks[task_id] = batch_result

                self.logger.debug(f"Task {task_id} completed successfully in {batch_result.processing_time:.2f}s")

        except Exception as e:
            processing_time = time.time() - start_time
            error_message = str(e)

            self.logger.error(f"Task {task_id} failed: {error_message}")

            # 重试逻辑
            if task.retry_count < self.config.retry_attempts:
                task.retry_count += 1
                # 指数退避
                retry_delay = self.config.retry_delay * (2 ** task.retry_count)
                await asyncio.sleep(retry_delay)

                # 重新提交任务
                queue_priority = self._calculate_queue_priority(task)
                with self.lock:
                    self.task_queue.put((queue_priority, task))
                    self.stats.current_queue_size = self.task_queue.qsize()

                self.logger.info(f"Retrying task {task_id} (attempt {task.retry_count})")
            else:
                # 创建失败结果
                batch_result = BatchResult(
                    task_id=task_id,
                    task_type=task.task_type,
                    result=None,
                    success=False,
                    processing_time=processing_time,
                    error_message=error_message,
                    metadata=task.metadata
                )

                # 更新统计
                self._update_task_stats(batch_result, False)

                # 调用回调函数
                if task.callback:
                    await self._call_callback(task.callback, batch_result)

                # 存储结果
                with self.lock:
                    self.completed_tasks[task_id] = batch_result

                self.logger.error(f"Task {task_id} failed after {task.retry_count} retries")

    async def _process_summarization(self, task: BatchTask) -> SummaryResult:
        """处理摘要任务"""
        if isinstance(task.data, list):
            return await self.summarizer.summarize_batch(task.data)
        else:
            return await self.summarizer.summarize_article(task.data)

    async def _process_sentiment_analysis(self, task: BatchTask) -> SentimentAnalysisResult:
        """处理情感分析任务"""
        if isinstance(task.data, list):
            return await self.sentiment_analyzer.analyze_batch_sentiment(task.data)
        else:
            return await self.sentiment_analyzer.analyze_sentiment(task.data)

    async def _process_content_segmentation(self, task: BatchTask) -> SegmentationResult:
        """处理内容分段任务"""
        if isinstance(task.data, list):
            return await self.content_segmenter.segment_batch_content(task.data)
        else:
            return await self.content_segmenter.segment_content(task.data)

    async def _process_entity_extraction(self, task: BatchTask) -> EntityExtractionResult:
        """处理实体提取任务"""
        if isinstance(task.data, list):
            return await self.entity_extractor.extract_batch_entities(task.data)
        else:
            return await self.entity_extractor.extract_entities(task.data)

    async def _process_market_impact(self, task: BatchTask) -> MarketImpactResult:
        """处理市场影响评估任务"""
        data = task.data
        if isinstance(data, dict):
            articles = data.get("articles", [])
            sentiment_results = data.get("sentiment_results", [])
            entity_results = data.get("entity_results", [])

            if len(articles) == 1:
                return await self.market_impact_assessor.assess_market_impact(
                    articles[0],
                    sentiment_results[0] if sentiment_results else None,
                    entity_results[0] if entity_results else None
                )
            else:
                return await self.market_impact_assessor.assess_batch_market_impact(
                    articles, sentiment_results, entity_results
                )
        else:
            return await self.market_impact_assessor.assess_market_impact(data)

    async def _process_comprehensive_analysis(self, task: BatchTask) -> Dict[str, Any]:
        """处理综合分析任务"""
        data = task.data
        if isinstance(data, list):
            articles = data
        else:
            articles = [data]

        results = []
        for article in articles:
            try:
                # 并行执行所有分析
                summary_task = asyncio.create_task(self.summarizer.summarize_article(article))
                sentiment_task = asyncio.create_task(self.sentiment_analyzer.analyze_sentiment(article))
                segmentation_task = asyncio.create_task(self.content_segmenter.segment_content(article))
                entity_task = asyncio.create_task(self.entity_extractor.extract_entities(article))

                # 等待所有任务完成
                summary_result, sentiment_result, segmentation_result, entity_result = await asyncio.gather(
                    summary_task, sentiment_task, segmentation_task, entity_task,
                    return_exceptions=True
                )

                # 处理异常
                if isinstance(summary_result, Exception):
                    summary_result = None
                if isinstance(sentiment_result, Exception):
                    sentiment_result = None
                if isinstance(segmentation_result, Exception):
                    segmentation_result = None
                if isinstance(entity_result, Exception):
                    entity_result = None

                # 市场影响分析（依赖前面的结果）
                market_impact_result = await self.market_impact_assessor.assess_market_impact(
                    article, sentiment_result, entity_result
                )

                article_result = {
                    "article_id": article.id,
                    "summary": summary_result.__dict__ if summary_result else None,
                    "sentiment": sentiment_result.__dict__ if sentiment_result else None,
                    "segmentation": segmentation_result.__dict__ if segmentation_result else None,
                    "entities": entity_result.__dict__ if entity_result else None,
                    "market_impact": market_impact_result.__dict__ if market_impact_result else None,
                    "processing_time": time.time()
                }
                results.append(article_result)

            except Exception as e:
                self.logger.error(f"Comprehensive analysis failed for article {article.id}: {str(e)}")
                results.append({
                    "article_id": article.id,
                    "error": str(e),
                    "processing_time": time.time()
                })

        return {"results": results, "total_articles": len(articles)} if len(articles) > 1 else results[0]

    async def _call_callback(self, callback: Callable, result: BatchResult):
        """调用回调函数"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(result)
            else:
                callback(result)
        except Exception as e:
            self.logger.error(f"Callback function failed: {str(e)}")

    def _update_task_stats(self, result: BatchResult, success: bool):
        """更新任务统计"""
        with self.lock:
            self.stats.total_tasks_processed += 1
            if success:
                self.stats.successful_tasks += 1
            else:
                self.stats.failed_tasks += 1

            # 更新平均时间
            total_time = self.stats.average_task_time * (self.stats.total_tasks_processed - 1)
            total_time += result.processing_time
            self.stats.average_task_time = total_time / self.stats.total_tasks_processed

            # 更新错误率
            self.stats.error_rate = self.stats.failed_tasks / self.stats.total_tasks_processed

            # 更新吞吐量
            if self.stats.total_tasks_processed > 0:
                total_runtime = time.time() - getattr(self, '_start_time', time.time())
                self.stats.throughput = self.stats.total_tasks_processed / max(1, total_runtime)

    async def _wait_for_completion(self):
        """等待所有任务完成"""
        while not self.task_queue.empty() or self.processing_tasks:
            await asyncio.sleep(0.1)

    async def get_result(self, task_id: str, timeout: Optional[float] = None) -> Optional[BatchResult]:
        """获取任务结果"""
        start_time = time.time()

        while True:
            with self.lock:
                if task_id in self.completed_tasks:
                    return self.completed_tasks[task_id]

            # 检查超时
            if timeout and (time.time() - start_time) > timeout:
                return None

            await asyncio.sleep(0.1)

    async def wait_for_completion(self, task_ids: List[str], timeout: Optional[float] = None) -> Dict[str, BatchResult]:
        """等待多个任务完成"""
        results = {}
        start_time = time.time()

        while len(results) < len(task_ids):
            # 检查超时
            if timeout and (time.time() - start_time) > timeout:
                break

            with self.lock:
                for task_id in task_ids:
                    if task_id not in results and task_id in self.completed_tasks:
                        results[task_id] = self.completed_tasks[task_id]

            await asyncio.sleep(0.1)

        return results

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            stats = self.stats.__dict__.copy()
            stats["is_running"] = self.is_running
            stats["queue_size"] = self.task_queue.qsize()
            stats["memory_usage"] = self._get_memory_usage()
            return stats

    def _get_memory_usage(self) -> float:
        """获取内存使用量"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0

    async def clear_completed_tasks(self):
        """清理已完成的任务"""
        with self.lock:
            self.completed_tasks.clear()
        self.logger.info("Completed tasks cleared")

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        # 由于任务已经开始处理，取消操作比较复杂
        # 这里简化实现，仅从队列中移除未处理的任务
        with self.lock:
            # 创建新队列，排除要取消的任务
            new_queue = queue.PriorityQueue()
            removed = False

            while not self.task_queue.empty():
                try:
                    priority, task = self.task_queue.get_nowait()
                    if task.id != task_id:
                        new_queue.put((priority, task))
                    else:
                        removed = True
                except queue.Empty:
                    break

            self.task_queue = new_queue
            self.stats.current_queue_size = self.task_queue.qsize()

        return removed

    def update_config(self, config: BatchConfig):
        """更新配置"""
        self.config = config
        self.logger.info("Batch processor configuration updated")

        # 更新速率限制器
        if self.config.enable_rate_limiting:
            self.rate_limiter = RateLimiter(self.config.requests_per_minute)
        else:
            self.rate_limiter = None

        # 更新信号量
        if hasattr(self, 'semaphore'):
            self.semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy" if self.is_running else "stopped",
            "queue_size": self.task_queue.qsize(),
            "active_tasks": len(self.processing_tasks),
            "completed_tasks": len(self.completed_tasks),
            "stats": self.get_stats(),
            "components": {
                "summarizer": "healthy",
                "sentiment_analyzer": "healthy",
                "content_segmenter": "healthy",
                "entity_extractor": "healthy",
                "market_impact_assessor": "healthy"
            }
        }

    async def process_immediate(self, task_type: str, data: Any, timeout: Optional[float] = None) -> Any:
        """立即处理任务（绕过队列）"""
        task = BatchTask(
            id=f"immediate_{int(time.time() * 1000)}",
            task_type=task_type,
            data=data,
            priority=BatchPriority.CRITICAL,
            created_at=datetime.now(),
            timeout=timeout or self.config.processing_timeout
        )

        return await self._process_task(task)