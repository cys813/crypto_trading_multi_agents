"""
Collection optimizer for performance tuning and adaptive optimization
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import statistics
import json
from pathlib import Path

from ..core.adapter import NewsSourceAdapter
from ..models.base import NewsArticle, NewsQuery, NewsQueryResult
from .strategies import CollectionStrategy, CollectionResult
from .load_balancer import LoadBalancer


class OptimizationTarget(Enum):
    """优化目标"""
    SPEED = "speed"  # 速度优化
    ACCURACY = "accuracy"  # 准确性优化
    EFFICIENCY = "efficiency"  # 效率优化
    RELIABILITY = "reliability"  # 可靠性优化
    BALANCED = "balanced"  # 平衡优化


@dataclass
class PerformanceMetrics:
    """性能指标"""
    collection_speed: float = 0.0  # 文章/分钟
    accuracy_rate: float = 100.0  # 百分比
    resource_efficiency: float = 100.0  # 百分比
    reliability_score: float = 100.0  # 百分比
    latency: float = 0.0  # 毫秒
    throughput: float = 0.0  # 文章/小时
    error_rate: float = 0.0  # 百分比
    memory_usage: float = 0.0  # MB
    cpu_usage: float = 0.0  # 百分比


@dataclass
class OptimizationParameters:
    """优化参数"""
    batch_size: int = 50
    concurrency_limit: int = 5
    timeout_multiplier: float = 1.0
    retry_attempts: int = 3
    cache_enabled: bool = True
    prefetch_enabled: bool = True
    compression_enabled: bool = True
    adaptive_batching: bool = True
    smart_retry: bool = True


@dataclass
class OptimizationResult:
    """优化结果"""
    target: OptimizationTarget
    parameters: OptimizationParameters
    performance_improvement: Dict[str, float]
    recommendations: List[str]
    confidence: float  # 0-1
    estimated_impact: str


class CollectionOptimizer:
    """收集优化器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # 配置参数
        self.optimization_target = OptimizationTarget(config.get('target', 'balanced'))
        self.optimization_interval = config.get('optimization_interval', 300)  # 5分钟
        self.performance_history_size = config.get('performance_history_size', 100)
        self.optimization_threshold = config.get('optimization_threshold', 0.1)  # 10%改善阈值

        # 性能历史
        self.performance_history: List[PerformanceMetrics] = []
        self.optimization_history: List[OptimizationResult] = []

        # 当前参数
        self.current_parameters = OptimizationParameters(
            batch_size=config.get('batch_size', 50),
            concurrency_limit=config.get('concurrency_limit', 5),
            timeout_multiplier=config.get('timeout_multiplier', 1.0),
            retry_attempts=config.get('retry_attempts', 3),
            cache_enabled=config.get('cache_enabled', True),
            prefetch_enabled=config.get('prefetch_enabled', True),
            compression_enabled=config.get('compression_enabled', True),
            adaptive_batching=config.get('adaptive_batching', True),
            smart_retry=config.get('smart_retry', True)
        )

        # 缓存和预取
        self.article_cache: Dict[str, NewsArticle] = {}
        self.prefetch_queue: List[str] = []
        self.cache_size_limit = config.get('cache_size_limit', 1000)

        # 优化任务
        self.optimization_task: Optional[asyncio.Task] = None
        self.is_optimizing = False

    async def initialize(self):
        """初始化优化器"""
        self.logger.info("初始化收集优化器")

        # 启动优化循环
        self.optimization_task = asyncio.create_task(self._optimization_loop())

    async def shutdown(self):
        """关闭优化器"""
        self.logger.info("关闭收集优化器")

        if self.optimization_task:
            self.optimization_task.cancel()
            try:
                await self.optimization_task
            except asyncio.CancelledError:
                pass

    async def optimize_collection(self,
                                 strategy: CollectionStrategy,
                                 adapters: Dict[str, NewsSourceAdapter],
                                 query: Optional[NewsQuery] = None) -> CollectionResult:
        """优化的收集执行"""
        start_time = time.time()

        # 应用优化参数
        optimized_result = await self._execute_optimized_collection(strategy, adapters, query)

        # 记录性能指标
        execution_time = (time.time() - start_time) * 1000  # 毫秒
        await self._record_performance_metrics(optimized_result, execution_time)

        # 缓存结果
        if self.current_parameters.cache_enabled:
            await self._cache_articles(optimized_result.articles)

        return optimized_result

    async def _execute_optimized_collection(self,
                                           strategy: CollectionStrategy,
                                           adapters: Dict[str, NewsSourceAdapter],
                                           query: Optional[NewsQuery] = None) -> CollectionResult:
        """执行优化的收集"""
        # 根据优化目标调整参数
        if self.optimization_target == OptimizationTarget.SPEED:
            return await self._optimize_for_speed(strategy, adapters, query)
        elif self.optimization_target == OptimizationTarget.ACCURACY:
            return await self._optimize_for_accuracy(strategy, adapters, query)
        elif self.optimization_target == OptimizationTarget.EFFICIENCY:
            return await self._optimize_for_efficiency(strategy, adapters, query)
        elif self.optimization_target == OptimizationTarget.RELIABILITY:
            return await self._optimize_for_reliability(strategy, adapters, query)
        else:  # BALANCED
            return await self._optimize_balanced(strategy, adapters, query)

    async def _optimize_for_speed(self,
                                 strategy: CollectionStrategy,
                                 adapters: Dict[str, NewsSourceAdapter],
                                 query: Optional[NewsQuery] = None) -> CollectionResult:
        """速度优化"""
        # 增加并发度
        if hasattr(strategy, 'config'):
            strategy.config['max_articles_per_source'] = int(
                strategy.config.get('max_articles_per_source', 100) * 1.5
            )

        # 减少超时时间
        for adapter in adapters.values():
            original_timeout = adapter.config.timeout
            adapter.config.timeout = int(original_timeout * 0.8)

        try:
            result = await strategy.collect(adapters, query)
            return result
        finally:
            # 恢复原始超时
            for adapter in adapters.values():
                adapter.config.timeout = int(adapter.config.timeout / 0.8)

    async def _optimize_for_accuracy(self,
                                   strategy: CollectionStrategy,
                                   adapters: Dict[str, NewsSourceAdapter],
                                   query: Optional[NewsQuery] = None) -> CollectionResult:
        """准确性优化"""
        # 减少并发度以提高准确性
        if hasattr(strategy, 'config'):
            strategy.config['max_articles_per_source'] = int(
                strategy.config.get('max_articles_per_source', 100) * 0.8
            )

        # 增加重试次数
        original_retry = self.current_parameters.retry_attempts
        self.current_parameters.retry_attempts = min(original_retry + 2, 5)

        try:
            result = await strategy.collect(adapters, query)
            return result
        finally:
            self.current_parameters.retry_attempts = original_retry

    async def _optimize_for_efficiency(self,
                                     strategy: CollectionStrategy,
                                     adapters: Dict[str, NewsSourceAdapter],
                                     query: Optional[NewsQuery] = None) -> CollectionResult:
        """效率优化"""
        # 调整批处理大小
        if hasattr(strategy, 'config'):
            original_batch = strategy.config.get('max_articles_per_source', 100)
            optimal_batch = self._calculate_optimal_batch_size(adapters)
            strategy.config['max_articles_per_source'] = optimal_batch

        # 启用压缩
        compression_enabled = self.current_parameters.compression_enabled
        self.current_parameters.compression_enabled = True

        try:
            result = await strategy.collect(adapters, query)
            return result
        finally:
            self.current_parameters.compression_enabled = compression_enabled

    async def _optimize_for_reliability(self,
                                     strategy: CollectionStrategy,
                                     adapters: Dict[str, NewsSourceAdapter],
                                     query: Optional[NewsQuery] = None) -> CollectionResult:
        """可靠性优化"""
        # 增加超时时间
        for adapter in adapters.values():
            adapter.config.timeout = int(adapter.config.timeout * 1.5)

        # 增加重试次数和智能重试
        original_retry = self.current_parameters.retry_attempts
        original_smart_retry = self.current_parameters.smart_retry
        self.current_parameters.retry_attempts = min(original_retry + 2, 5)
        self.current_parameters.smart_retry = True

        try:
            result = await strategy.collect(adapters, query)
            return result
        finally:
            # 恢复原始设置
            for adapter in adapters.values():
                adapter.config.timeout = int(adapter.config.timeout / 1.5)
            self.current_parameters.retry_attempts = original_retry
            self.current_parameters.smart_retry = original_smart_retry

    async def _optimize_balanced(self,
                                strategy: CollectionStrategy,
                                adapters: Dict[str, NewsSourceAdapter],
                                query: Optional[NewsQuery] = None) -> CollectionResult:
        """平衡优化"""
        # 使用自适应批处理
        if self.current_parameters.adaptive_batching:
            optimal_batch = self._calculate_optimal_batch_size(adapters)
            if hasattr(strategy, 'config'):
                strategy.config['max_articles_per_source'] = optimal_batch

        # 智能重试
        if self.current_parameters.smart_retry:
            self._enable_smart_retry(adapters)

        try:
            result = await strategy.collect(adapters, query)
            return result
        finally:
            if self.current_parameters.smart_retry:
                self._disable_smart_retry(adapters)

    def _calculate_optimal_batch_size(self, adapters: Dict[str, NewsSourceAdapter]) -> int:
        """计算最优批处理大小"""
        if not adapters:
            return 50

        # 基于适配器性能计算
        total_capacity = sum(adapter.config.rate_limit for adapter in adapters.values())
        adapter_count = len(adapters)

        # 基础批大小
        base_batch = max(10, total_capacity // adapter_count)

        # 基于历史性能调整
        if self.performance_history:
            recent_performance = self.performance_history[-10:]
            avg_speed = statistics.mean(p.collection_speed for p in recent_performance)

            if avg_speed > 100:  # 高速系统
                return int(base_batch * 1.5)
            elif avg_speed < 50:  # 低速系统
                return int(base_batch * 0.7)

        return base_batch

    def _enable_smart_retry(self, adapters: Dict[str, NewsSourceAdapter]):
        """启用智能重试"""
        for adapter in adapters.values():
            # 这里可以添加智能重试逻辑
            # 例如：基于错误类型决定是否重试
            pass

    def _disable_smart_retry(self, adapters: Dict[str, NewsSourceAdapter]):
        """禁用智能重试"""
        for adapter in adapters.values():
            # 恢复正常重试逻辑
            pass

    async def _record_performance_metrics(self, result: CollectionResult, execution_time: float):
        """记录性能指标"""
        metrics = PerformanceMetrics()

        # 计算收集速度
        metrics.collection_speed = (result.total_count / max(execution_time / 60000, 1))  # 文章/分钟
        metrics.throughput = result.total_count * 60  # 文章/小时

        # 计算错误率
        metrics.error_rate = (len(result.errors) / max(result.total_count, 1)) * 100

        # 记录延迟
        metrics.latency = execution_time

        # 估算资源使用（简化计算）
        metrics.memory_usage = len(result.articles) * 0.5  # 假设每篇文章0.5MB
        metrics.cpu_usage = min(100, execution_time / 10)  # 简化的CPU使用率

        # 添加到历史记录
        self.performance_history.append(metrics)

        # 限制历史记录大小
        if len(self.performance_history) > self.performance_history_size:
            self.performance_history = self.performance_history[-self.performance_history_size:]

    async def _cache_articles(self, articles: List[NewsArticle]):
        """缓存文章"""
        for article in articles:
            if article.id and article.id not in self.article_cache:
                self.article_cache[article.id] = article

        # 清理缓存
        if len(self.article_cache) > self.cache_size_limit:
            # 简单的LRU策略：删除最旧的50%
            keys_to_remove = list(self.article_cache.keys())[:len(self.article_cache) // 2]
            for key in keys_to_remove:
                del self.article_cache[key]

    async def _optimization_loop(self):
        """优化循环"""
        while True:
            try:
                await asyncio.sleep(self.optimization_interval)

                # 检查是否需要优化
                if await self._should_optimize():
                    await self._perform_optimization()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("优化循环异常", exc_info=e)

    async def _should_optimize(self) -> bool:
        """检查是否需要优化"""
        if len(self.performance_history) < 10:
            return False

        if self.is_optimizing:
            return False

        # 检查性能是否有明显下降
        recent_performance = self.performance_history[-5:]
        older_performance = self.performance_history[-10:-5]

        if len(recent_performance) < 5 or len(older_performance) < 5:
            return False

        # 比较平均性能
        recent_speed = statistics.mean(p.collection_speed for p in recent_performance)
        older_speed = statistics.mean(p.collection_speed for p in older_performance)

        performance_degradation = (older_speed - recent_speed) / older_speed

        return performance_degradation > self.optimization_threshold

    async def _perform_optimization(self):
        """执行优化"""
        self.is_optimizing = True
        self.logger.info("开始性能优化")

        try:
            # 分析当前性能
            current_performance = self._analyze_current_performance()

            # 生成优化建议
            optimization_result = await self._generate_optimization_recommendations(current_performance)

            # 应用优化
            await self._apply_optimization(optimization_result)

            # 记录优化结果
            self.optimization_history.append(optimization_result)

            self.logger.info(f"优化完成: {optimization_result.estimated_impact}")

        except Exception as e:
            self.logger.error("优化过程异常", exc_info=e)
        finally:
            self.is_optimizing = False

    def _analyze_current_performance(self) -> PerformanceMetrics:
        """分析当前性能"""
        if not self.performance_history:
            return PerformanceMetrics()

        recent_metrics = self.performance_history[-10:]

        return PerformanceMetrics(
            collection_speed=statistics.mean(m.collection_speed for m in recent_metrics),
            accuracy_rate=statistics.mean(m.accuracy_rate for m in recent_metrics),
            resource_efficiency=statistics.mean(m.resource_efficiency for m in recent_metrics),
            reliability_score=statistics.mean(m.reliability_score for m in recent_metrics),
            latency=statistics.mean(m.latency for m in recent_metrics),
            throughput=statistics.mean(m.throughput for m in recent_metrics),
            error_rate=statistics.mean(m.error_rate for m in recent_metrics),
            memory_usage=statistics.mean(m.memory_usage for m in recent_metrics),
            cpu_usage=statistics.mean(m.cpu_usage for m in recent_metrics)
        )

    async def _generate_optimization_recommendations(self,
                                                    current_performance: PerformanceMetrics) -> OptimizationResult:
        """生成优化建议"""
        recommendations = []
        performance_improvement = {}
        new_parameters = OptimizationParameters(**self.current_parameters.__dict__)

        # 基于优化目标生成建议
        if self.optimization_target == OptimizationTarget.SPEED:
            recommendations, performance_improvement, new_parameters = await self._optimize_for_speed_recommendations(
                current_performance, new_parameters
            )
        elif self.optimization_target == OptimizationTarget.ACCURACY:
            recommendations, performance_improvement, new_parameters = await self._optimize_for_accuracy_recommendations(
                current_performance, new_parameters
            )
        elif self.optimization_target == OptimizationTarget.EFFICIENCY:
            recommendations, performance_improvement, new_parameters = await self._optimize_for_efficiency_recommendations(
                current_performance, new_parameters
            )
        elif self.optimization_target == OptimizationTarget.RELIABILITY:
            recommendations, performance_improvement, new_parameters = await self._optimize_for_reliability_recommendations(
                current_performance, new_parameters
            )
        else:  # BALANCED
            recommendations, performance_improvement, new_parameters = await self._optimize_balanced_recommendations(
                current_performance, new_parameters
            )

        # 计算影响估算
        estimated_impact = self._estimate_impact(performance_improvement)

        return OptimizationResult(
            target=self.optimization_target,
            parameters=new_parameters,
            performance_improvement=performance_improvement,
            recommendations=recommendations,
            confidence=self._calculate_confidence(performance_improvement),
            estimated_impact=estimated_impact
        )

    async def _optimize_for_speed_recommendations(self,
                                                  current_performance: PerformanceMetrics,
                                                  parameters: OptimizationParameters) -> Tuple[List[str], Dict[str, float], OptimizationParameters]:
        """速度优化建议"""
        recommendations = []
        improvements = {}

        # 检查并发度
        if current_performance.collection_speed < 50:
            parameters.concurrency_limit = min(parameters.concurrency_limit + 2, 10)
            recommendations.append("增加并发度以提高收集速度")
            improvements['speed'] = 25.0

        # 检查批处理大小
        if parameters.batch_size < 100:
            parameters.batch_size = int(parameters.batch_size * 1.5)
            recommendations.append("增加批处理大小以提高吞吐量")
            improvements['throughput'] = 30.0

        # 检查缓存
        if not parameters.cache_enabled:
            parameters.cache_enabled = True
            recommendations.append("启用缓存以减少重复处理")
            improvements['efficiency'] = 20.0

        return recommendations, improvements, parameters

    async def _optimize_for_accuracy_recommendations(self,
                                                    current_performance: PerformanceMetrics,
                                                    parameters: OptimizationParameters) -> Tuple[List[str], Dict[str, float], OptimizationParameters]:
        """准确性优化建议"""
        recommendations = []
        improvements = {}

        # 检查错误率
        if current_performance.error_rate > 5:
            parameters.retry_attempts = min(parameters.retry_attempts + 1, 5)
            recommendations.append("增加重试次数以提高数据准确性")
            improvements['accuracy'] = 15.0

        # 检查并发度（高并发可能影响准确性）
        if parameters.concurrency_limit > 5:
            parameters.concurrency_limit = max(3, parameters.concurrency_limit - 1)
            recommendations.append("降低并发度以提高数据质量")
            improvements['accuracy'] = 10.0

        # 检查超时
        if parameters.timeout_multiplier < 1.5:
            parameters.timeout_multiplier *= 1.2
            recommendations.append("增加超时时间以确保完整数据收集")
            improvements['reliability'] = 12.0

        return recommendations, improvements, parameters

    async def _optimize_for_efficiency_recommendations(self,
                                                      current_performance: PerformanceMetrics,
                                                      parameters: OptimizationParameters) -> Tuple[List[str], Dict[str, float], OptimizationParameters]:
        """效率优化建议"""
        recommendations = []
        improvements = {}

        # 检查内存使用
        if current_performance.memory_usage > 500:  # 500MB
            if not parameters.compression_enabled:
                parameters.compression_enabled = True
                recommendations.append("启用压缩以减少内存使用")
                improvements['memory'] = 30.0

        # 检查批处理大小
        if parameters.batch_size > 200:
            parameters.batch_size = int(parameters.batch_size * 0.8)
            recommendations.append("减少批处理大小以优化资源使用")
            improvements['efficiency'] = 15.0

        # 检查自适应批处理
        if not parameters.adaptive_batching:
            parameters.adaptive_batching = True
            recommendations.append("启用自适应批处理以优化效率")
            improvements['efficiency'] = 20.0

        return recommendations, improvements, parameters

    async def _optimize_for_reliability_recommendations(self,
                                                        current_performance: PerformanceMetrics,
                                                        parameters: OptimizationParameters) -> Tuple[List[str], Dict[str, float], OptimizationParameters]:
        """可靠性优化建议"""
        recommendations = []
        improvements = {}

        # 检查错误率
        if current_performance.error_rate > 3:
            parameters.retry_attempts = min(parameters.retry_attempts + 2, 5)
            parameters.smart_retry = True
            recommendations.append("启用智能重试以提高可靠性")
            improvements['reliability'] = 25.0

        # 检查超时
        if parameters.timeout_multiplier < 2.0:
            parameters.timeout_multiplier *= 1.5
            recommendations.append("增加超时时间以提高连接可靠性")
            improvements['reliability'] = 15.0

        # 检查并发度
        if parameters.concurrency_limit > 8:
            parameters.concurrency_limit = 5
            recommendations.append("降低并发度以提高系统稳定性")
            improvements['stability'] = 20.0

        return recommendations, improvements, parameters

    async def _optimize_balanced_recommendations(self,
                                                 current_performance: PerformanceMetrics,
                                                 parameters: OptimizationParameters) -> Tuple[List[str], Dict[str, float], OptimizationParameters]:
        """平衡优化建议"""
        recommendations = []
        improvements = {}

        # 综合分析，根据最需要改进的方面提供建议
        if current_performance.collection_speed < 30:
            parameters.concurrency_limit = min(parameters.concurrency_limit + 1, 7)
            recommendations.append("适度增加并发度以提高整体性能")
            improvements['balanced'] = 15.0

        if current_performance.error_rate > 2:
            parameters.retry_attempts = min(parameters.retry_attempts + 1, 4)
            recommendations.append("适度增加重试次数以确保数据质量")
            improvements['quality'] = 12.0

        if current_performance.memory_usage > 300:
            if not parameters.compression_enabled:
                parameters.compression_enabled = True
                recommendations.append("启用压缩以平衡性能和资源使用")
                improvements['resource'] = 18.0

        return recommendations, improvements, parameters

    def _estimate_impact(self, improvements: Dict[str, float]) -> str:
        """估算优化影响"""
        if not improvements:
            return "轻微改善"

        avg_improvement = statistics.mean(improvements.values())

        if avg_improvement >= 30:
            return "显著改善"
        elif avg_improvement >= 20:
            return "明显改善"
        elif avg_improvement >= 10:
            return "适度改善"
        else:
            return "轻微改善"

    def _calculate_confidence(self, improvements: Dict[str, float]) -> float:
        """计算优化置信度"""
        if not improvements:
            return 0.5

        # 基于改善幅度和历史成功率计算置信度
        avg_improvement = statistics.mean(improvements.values())

        if avg_improvement >= 25:
            return 0.9
        elif avg_improvement >= 15:
            return 0.8
        elif avg_improvement >= 10:
            return 0.7
        else:
            return 0.6

    async def _apply_optimization(self, optimization_result: OptimizationResult):
        """应用优化"""
        self.current_parameters = optimization_result.parameters

        self.logger.info(f"应用优化参数: {optimization_result.recommendations}")

    def get_optimizer_stats(self) -> Dict[str, Any]:
        """获取优化器统计信息"""
        if not self.performance_history:
            return {"status": "insufficient_data"}

        current_performance = self._analyze_current_performance()

        return {
            "optimization_target": self.optimization_target.value,
            "current_parameters": {
                "batch_size": self.current_parameters.batch_size,
                "concurrency_limit": self.current_parameters.concurrency_limit,
                "timeout_multiplier": self.current_parameters.timeout_multiplier,
                "retry_attempts": self.current_parameters.retry_attempts,
                "cache_enabled": self.current_parameters.cache_enabled,
                "prefetch_enabled": self.current_parameters.prefetch_enabled,
                "compression_enabled": self.current_parameters.compression_enabled,
                "adaptive_batching": self.current_parameters.adaptive_batching,
                "smart_retry": self.current_parameters.smart_retry
            },
            "current_performance": {
                "collection_speed": current_performance.collection_speed,
                "accuracy_rate": current_performance.accuracy_rate,
                "resource_efficiency": current_performance.resource_efficiency,
                "reliability_score": current_performance.reliability_score,
                "latency": current_performance.latency,
                "throughput": current_performance.throughput,
                "error_rate": current_performance.error_rate
            },
            "optimization_history": len(self.optimization_history),
            "performance_history": len(self.performance_history),
            "cache_size": len(self.article_cache),
            "is_optimizing": self.is_optimizing
        }