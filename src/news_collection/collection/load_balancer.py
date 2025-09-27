"""
Load balancer for multi-source distribution and intelligent traffic management
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import random
import statistics

from ..core.adapter import NewsSourceAdapter
from ..models.base import NewsSourceConfig
from .priority_engine import CollectionPriority, PriorityLevel


class LoadBalancingStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"  # 轮询
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"  # 加权轮询
    LEAST_CONNECTIONS = "least_connections"  # 最少连接
    PRIORITY_BASED = "priority_based"  # 基于优先级
    RESPONSE_TIME = "response_time"  # 基于响应时间
    ADAPTIVE = "adaptive"  # 自适应
    GEOGRAPHIC = "geographic"  # 地理位置


@dataclass
class LoadMetrics:
    """负载指标"""
    active_connections: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0  # 毫秒
    last_response_time: float = 0.0
    cpu_usage: float = 0.0  # 百分比
    memory_usage: float = 0.0  # 百分比
    success_rate: float = 100.0  # 百分比
    last_health_check: datetime = field(default_factory=datetime.now)
    consecutive_failures: int = 0
    backoff_until: Optional[datetime] = None


@dataclass
class SourceWeight:
    """源权重"""
    source_name: str
    weight: float
    priority: int
    reliability_score: float
    performance_score: float
    current_load: float
    max_capacity: int


class LoadBalancer:
    """负载均衡器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # 配置参数
        self.strategy = LoadBalancingStrategy(config.get('strategy', 'adaptive'))
        self.max_concurrent_per_source = config.get('max_concurrent_per_source', 10)
        self.health_check_interval = config.get('health_check_interval', 30)
        self.backoff_multiplier = config.get('backoff_multiplier', 2.0)
        self.max_backoff_time = config.get('max_backoff_time', 300)  # 5分钟
        self.failure_threshold = config.get('failure_threshold', 3)
        self.recovery_threshold = config.get('recovery_threshold', 5)

        # 负载指标
        self.load_metrics: Dict[str, LoadMetrics] = {}
        self.source_weights: Dict[str, SourceWeight] = {}
        self.active_connections: Dict[str, Set[str]] = {}
        self.request_queue: List[str] = []

        # 负载均衡状态
        self.current_round_robin_index = 0
        self.current_weighted_index = 0
        self.last_health_check = datetime.now()

        # 启动后台任务
        self.health_check_task: Optional[asyncio.Task] = None
        self.metrics_update_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """初始化负载均衡器"""
        self.logger.info("初始化负载均衡器")

        # 启动健康检查任务
        self.health_check_task = asyncio.create_task(self._health_check_loop())

        # 启动指标更新任务
        self.metrics_update_task = asyncio.create_task(self._metrics_update_loop())

    async def shutdown(self):
        """关闭负载均衡器"""
        self.logger.info("关闭负载均衡器")

        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass

        if self.metrics_update_task:
            self.metrics_update_task.cancel()
            try:
                await self.metrics_update_task
            except asyncio.CancelledError:
                pass

    def register_source(self, adapter: NewsSourceAdapter):
        """注册新闻源"""
        source_name = adapter.source_name

        # 初始化负载指标
        self.load_metrics[source_name] = LoadMetrics()

        # 初始化源权重
        self.source_weights[source_name] = SourceWeight(
            source_name=source_name,
            weight=self._calculate_initial_weight(adapter),
            priority=adapter.config.priority if adapter.config.priority else 5,
            reliability_score=self._calculate_reliability_score(adapter),
            performance_score=100.0,  # 初始给满分
            current_load=0.0,
            max_capacity=self.max_concurrent_per_source
        )

        # 初始化连接跟踪
        self.active_connections[source_name] = set()

        self.logger.info(f"注册新闻源到负载均衡器: {source_name}")

    def unregister_source(self, source_name: str):
        """注销新闻源"""
        if source_name in self.load_metrics:
            del self.load_metrics[source_name]

        if source_name in self.source_weights:
            del self.source_weights[source_name]

        if source_name in self.active_connections:
            del self.active_connections[source_name]

        self.logger.info(f"从负载均衡器注销新闻源: {source_name}")

    async def select_source(self,
                           adapters: Dict[str, NewsSourceAdapter],
                           priorities: Optional[Dict[str, CollectionPriority]] = None) -> Optional[str]:
        """选择最佳新闻源"""
        available_sources = self._get_available_sources(adapters)

        if not available_sources:
            self.logger.warning("没有可用的新闻源")
            return None

        # 根据策略选择源
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._select_round_robin(available_sources)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._select_weighted_round_robin(available_sources)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._select_least_connections(available_sources)
        elif self.strategy == LoadBalancingStrategy.PRIORITY_BASED:
            return self._select_priority_based(available_sources, priorities)
        elif self.strategy == LoadBalancingStrategy.RESPONSE_TIME:
            return self._select_response_time(available_sources)
        elif self.strategy == LoadBalancingStrategy.ADAPTIVE:
            return self._select_adaptive(available_sources, priorities)
        else:
            # 默认使用自适应策略
            return self._select_adaptive(available_sources, priorities)

    def _get_available_sources(self, adapters: Dict[str, NewsSourceAdapter]) -> List[str]:
        """获取可用源列表"""
        available = []

        for source_name, adapter in adapters.items():
            if self._is_source_available(source_name, adapter):
                available.append(source_name)

        return available

    def _is_source_available(self, source_name: str, adapter: NewsSourceAdapter) -> bool:
        """检查源是否可用"""
        # 检查适配器状态
        if not adapter.is_connected():
            return False

        # 检查负载指标
        if source_name not in self.load_metrics:
            return True

        metrics = self.load_metrics[source_name]

        # 检查退避期
        if metrics.backoff_until and datetime.now() < metrics.backoff_until:
            return False

        # 检查连续失败次数
        if metrics.consecutive_failures >= self.failure_threshold:
            return False

        # 检查连接数限制
        if len(self.active_connections.get(source_name, set())) >= self.max_concurrent_per_source:
            return False

        return True

    def _select_round_robin(self, available_sources: List[str]) -> str:
        """轮询选择"""
        if not available_sources:
            return None

        selected_source = available_sources[self.current_round_robin_index % len(available_sources)]
        self.current_round_robin_index += 1

        return selected_source

    def _select_weighted_round_robin(self, available_sources: List[str]) -> str:
        """加权轮询选择"""
        if not available_sources:
            return None

        # 获取可用源的权重
        weights = []
        for source_name in available_sources:
            weight = self.source_weights.get(source_name, SourceWeight(
                source_name=source_name, weight=1.0, priority=5, reliability_score=5.0,
                performance_score=100.0, current_load=0.0, max_capacity=10
            )).weight
            weights.append(weight)

        # 如果没有权重，使用普通轮询
        if sum(weights) == 0:
            return self._select_round_robin(available_sources)

        # 加权随机选择
        total_weight = sum(weights)
        random_weight = random.uniform(0, total_weight)

        current_weight = 0
        for i, weight in enumerate(weights):
            current_weight += weight
            if random_weight <= current_weight:
                return available_sources[i]

        return available_sources[-1]

    def _select_least_connections(self, available_sources: List[str]) -> str:
        """最少连接选择"""
        if not available_sources:
            return None

        # 计算每个源的活跃连接数
        connection_counts = []
        for source_name in available_sources:
            count = len(self.active_connections.get(source_name, set()))
            connection_counts.append((source_name, count))

        # 选择连接数最少的源
        return min(connection_counts, key=lambda x: x[1])[0]

    def _select_priority_based(self,
                              available_sources: List[str],
                              priorities: Optional[Dict[str, CollectionPriority]] = None) -> str:
        """基于优先级选择"""
        if not available_sources:
            return None

        if not priorities:
            return self._select_round_robin(available_sources)

        # 根据优先级排序
        priority_scores = []
        for source_name in available_sources:
            priority = priorities.get(source_name)
            if priority:
                score = priority.priority_score
            else:
                score = 50.0  # 默认分数
            priority_scores.append((source_name, score))

        # 选择最高优先级的源
        return max(priority_scores, key=lambda x: x[1])[0]

    def _select_response_time(self, available_sources: List[str]) -> str:
        """基于响应时间选择"""
        if not available_sources:
            return None

        # 获取响应时间
        response_times = []
        for source_name in available_sources:
            metrics = self.load_metrics.get(source_name, LoadMetrics())
            response_time = metrics.average_response_time
            if response_time == 0:
                response_time = 1000  # 默认1秒
            response_times.append((source_name, response_time))

        # 选择响应时间最短的源
        return min(response_times, key=lambda x: x[1])[0]

    def _select_adaptive(self,
                        available_sources: List[str],
                        priorities: Optional[Dict[str, CollectionPriority]] = None) -> str:
        """自适应选择"""
        if not available_sources:
            return None

        # 计算每个源的综合分数
        scores = []
        for source_name in available_sources:
            score = self._calculate_adaptive_score(source_name, priorities)
            scores.append((source_name, score))

        # 选择分数最高的源
        return max(scores, key=lambda x: x[1])[0]

    def _calculate_adaptive_score(self,
                                  source_name: str,
                                  priorities: Optional[Dict[str, CollectionPriority]] = None) -> float:
        """计算自适应分数"""
        score = 0.0

        # 获取源权重
        source_weight = self.source_weights.get(source_name, SourceWeight(
            source_name=source_name, weight=1.0, priority=5, reliability_score=5.0,
            performance_score=100.0, current_load=0.0, max_capacity=10
        ))

        # 负载指标
        metrics = self.load_metrics.get(source_name, LoadMetrics())

        # 1. 基础权重 (30%)
        score += source_weight.weight * 0.3

        # 2. 优先级分数 (25%)
        if priorities and source_name in priorities:
            priority_score = priorities[source_name].priority_score
            score += priority_score * 0.25

        # 3. 可靠性分数 (20%)
        score += source_weight.reliability_score * 0.2

        # 4. 性能分数 (15%)
        score += source_weight.performance_score * 0.15

        # 5. 负载因子 (负分)
        load_factor = len(self.active_connections.get(source_name, set())) / self.max_concurrent_per_source
        score -= load_factor * 20

        # 6. 响应时间因子 (负分)
        if metrics.average_response_time > 0:
            response_time_penalty = min(metrics.average_response_time / 100, 10)  # 最多扣10分
            score -= response_time_penalty

        # 7. 成功率因子
        if metrics.success_rate > 0:
            score += metrics.success_rate * 0.1

        return max(0, min(100, score))

    def _calculate_initial_weight(self, adapter: NewsSourceAdapter) -> float:
        """计算初始权重"""
        weight = 0.0

        # 基于优先级
        priority = adapter.config.priority if adapter.config.priority else 5
        weight += priority * 2

        # 基于速率限制
        rate_limit = adapter.config.rate_limit if adapter.config.rate_limit else 100
        weight += min(rate_limit / 10, 10)  # 最多10分

        # 基于超时设置
        timeout = adapter.config.timeout if adapter.config.timeout else 30
        if timeout <= 10:
            weight += 5  # 低超时给更高权重
        elif timeout <= 30:
            weight += 3
        else:
            weight += 1

        return max(1, weight)

    def _calculate_reliability_score(self, adapter: NewsSourceAdapter) -> float:
        """计算可靠性分数"""
        stats = adapter.get_stats()
        success_rate = stats.get('success_rate', 0.0)

        return success_rate * 10  # 转换为0-10分

    async def record_request_start(self, source_name: str, request_id: str):
        """记录请求开始"""
        if source_name not in self.active_connections:
            self.active_connections[source_name] = set()

        self.active_connections[source_name].add(request_id)

        # 更新负载指标
        if source_name in self.load_metrics:
            self.load_metrics[source_name].active_connections += 1
            self.load_metrics[source_name].total_requests += 1

        # 更新当前负载
        if source_name in self.source_weights:
            current_connections = len(self.active_connections[source_name])
            self.source_weights[source_name].current_load = current_connections / self.max_concurrent_per_source

    async def record_request_end(self,
                               source_name: str,
                               request_id: str,
                               success: bool,
                               response_time: float):
        """记录请求结束"""
        if source_name in self.active_connections:
            self.active_connections[source_name].discard(request_id)

        # 更新负载指标
        if source_name in self.load_metrics:
            metrics = self.load_metrics[source_name]
            metrics.active_connections = max(0, metrics.active_connections - 1)
            metrics.last_response_time = response_time

            # 更新平均响应时间
            if metrics.average_response_time == 0:
                metrics.average_response_time = response_time
            else:
                metrics.average_response_time = (metrics.average_response_time * 0.9) + (response_time * 0.1)

            # 更新成功率
            if success:
                metrics.consecutive_failures = 0
                if metrics.backoff_until:
                    metrics.backoff_until = None
            else:
                metrics.failed_requests += 1
                metrics.consecutive_failures += 1

            # 计算成功率
            total_requests = metrics.total_requests
            if total_requests > 0:
                metrics.success_rate = ((total_requests - metrics.failed_requests) / total_requests) * 100

            # 处理连续失败
            if metrics.consecutive_failures >= self.failure_threshold:
                backoff_time = min(
                    self.backoff_multiplier ** metrics.consecutive_failures * 10,
                    self.max_backoff_time
                )
                metrics.backoff_until = datetime.now() + timedelta(seconds=backoff_time)
                self.logger.warning(f"源 {source_name} 连续失败 {metrics.consecutive_failures} 次，退避 {backoff_time} 秒")

        # 更新当前负载
        if source_name in self.source_weights:
            current_connections = len(self.active_connections.get(source_name, set()))
            self.source_weights[source_name].current_load = current_connections / self.max_concurrent_per_source

            # 更新性能分数
            self._update_performance_score(source_name)

    def _update_performance_score(self, source_name: str):
        """更新性能分数"""
        if source_name not in self.source_weights or source_name not in self.load_metrics:
            return

        source_weight = self.source_weights[source_name]
        metrics = self.load_metrics[source_name]

        # 基于响应时间
        response_time_score = max(0, 100 - (metrics.average_response_time / 10))  # 10ms扣1分

        # 基于成功率
        success_rate_score = metrics.success_rate

        # 基于当前负载
        load_score = max(0, 100 - (source_weight.current_load * 100))

        # 综合性能分数
        performance_score = (response_time_score * 0.4) + (success_rate_score * 0.4) + (load_score * 0.2)

        source_weight.performance_score = performance_score

    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)

                # 检查所有源的连接状态
                await self._perform_health_checks()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("健康检查循环异常", exc_info=e)

    async def _perform_health_checks(self):
        """执行健康检查"""
        # 这里可以实现对适配器的健康检查
        # 实际项目中应该调用适配器的health_check方法
        pass

    async def _metrics_update_loop(self):
        """指标更新循环"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟更新一次

                # 更新权重
                self._update_weights()

                # 清理过期的退避
                self._cleanup_expired_backoffs()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("指标更新循环异常", exc_info=e)

    def _update_weights(self):
        """更新源权重"""
        for source_name, source_weight in self.source_weights.items():
            metrics = self.load_metrics.get(source_name, LoadMetrics())

            # 基于性能调整权重
            performance_factor = source_weight.performance_score / 100.0

            # 基于成功率调整权重
            success_factor = metrics.success_rate / 100.0

            # 基于负载调整权重
            load_factor = 1.0 - source_weight.current_load

            # 计算新权重
            base_weight = self._calculate_base_weight(source_weight)
            adjusted_weight = base_weight * performance_factor * success_factor * load_factor

            source_weight.weight = max(0.1, adjusted_weight)

    def _calculate_base_weight(self, source_weight: SourceWeight) -> float:
        """计算基础权重"""
        return (source_weight.priority * 2) + (source_weight.reliability_score * 1.5)

    def _cleanup_expired_backoffs(self):
        """清理过期的退避"""
        current_time = datetime.now()

        for source_name, metrics in self.load_metrics.items():
            if metrics.backoff_until and current_time >= metrics.backoff_until:
                metrics.backoff_until = None
                metrics.consecutive_failures = 0  # 重置失败计数
                self.logger.info(f"源 {source_name} 退避期结束，恢复正常服务")

    def get_load_balancer_stats(self) -> Dict[str, Any]:
        """获取负载均衡器统计信息"""
        total_sources = len(self.source_weights)
        active_sources = len([
            name for name, metrics in self.load_metrics.items()
            if metrics.backoff_until is None or datetime.now() >= metrics.backoff_until
        ])

        total_connections = sum(len(connections) for connections in self.active_connections.values())
        average_response_time = statistics.mean([
            metrics.average_response_time for metrics in self.load_metrics.values()
            if metrics.average_response_time > 0
        ]) if self.load_metrics else 0

        source_stats = {}
        for source_name, source_weight in self.source_weights.items():
            metrics = self.load_metrics.get(source_name, LoadMetrics())
            source_stats[source_name] = {
                'weight': source_weight.weight,
                'priority': source_weight.priority,
                'reliability_score': source_weight.reliability_score,
                'performance_score': source_weight.performance_score,
                'current_load': source_weight.current_load,
                'active_connections': len(self.active_connections.get(source_name, set())),
                'average_response_time': metrics.average_response_time,
                'success_rate': metrics.success_rate,
                'consecutive_failures': metrics.consecutive_failures,
                'is_backed_off': metrics.backoff_until is not None and datetime.now() < metrics.backoff_until
            }

        return {
            'strategy': self.strategy.value,
            'total_sources': total_sources,
            'active_sources': active_sources,
            'total_connections': total_connections,
            'average_response_time': average_response_time,
            'sources': source_stats
        }