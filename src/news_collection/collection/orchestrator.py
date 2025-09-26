"""
Multi-source news collection orchestrator - integrates all collection components
"""

import asyncio
import logging
import yaml
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path

from ..core.adapter import NewsSourceAdapter, NewsSourceAdapterFactory
from ..core.config_manager import ConfigManager
from .strategies import CollectionStrategyFactory
from .scheduler import CollectionScheduler, ScheduleConfig, ScheduleType
from .incremental_tracker import IncrementalTracker
from .relevance_filter import RelevanceFilter
from .priority_engine import PriorityEngine
from .load_balancer import LoadBalancer, LoadBalancingStrategy
from .optimizer import CollectionOptimizer, OptimizationTarget
from ..processing.pipeline_manager import PipelineManager, ProcessingConfig
from ..models.base import (
    NewsArticle,
    NewsQuery,
    NewsQueryResult,
    NewsSourceConfig,
    CollectionResult
)


class CollectionOrchestrator:
    """多源新闻收集协调器"""

    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(self.__class__.__name__)

        # 加载配置
        self.config = self._load_config(config_path)

        # 初始化组件
        self.adapters: Dict[str, NewsSourceAdapter] = {}
        self.scheduler: Optional[CollectionScheduler] = None
        self.tracker: Optional[IncrementalTracker] = None
        self.filter: Optional[RelevanceFilter] = None
        self.priority_engine: Optional[PriorityEngine] = None
        self.load_balancer: Optional[LoadBalancer] = None
        self.optimizer: Optional[CollectionOptimizer] = None
        self.config_manager: Optional[ConfigManager] = None
        self.processing_pipeline: Optional[PipelineManager] = None

        # 状态标志
        self.is_initialized = False
        self.is_running = False

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置文件"""
        if config_path is None:
            # 默认配置路径
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config', 'collection', 'collection_config.yaml')

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self.logger.info(f"加载配置文件: {config_path}")
            return config
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            # 返回默认配置
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'collection': {
                'default_strategy': 'incremental',
                'time_window_days': 15,
                'max_articles_per_source': 100
            },
            'scheduler': {
                'check_interval': 30,
                'max_concurrent_jobs': 5,
                'state_file': 'scheduler_state.json'
            },
            'incremental_tracker': {
                'window_days': 15,
                'max_articles_in_memory': 10000,
                'persistence_interval': 300
            },
            'relevance_filter': {
                'min_relevance_score': 50.0,
                'high_relevance_threshold': 90.0,
                'medium_relevance_threshold': 70.0,
                'confidence_threshold': 0.7
            },
            'priority_engine': {
                'critical_threshold': 90,
                'high_threshold': 75,
                'medium_threshold': 60,
                'low_threshold': 40
            },
            'load_balancer': {
                'strategy': 'adaptive',
                'max_concurrent_per_source': 10,
                'health_check_interval': 30
            },
            'optimizer': {
                'target': 'balanced',
                'optimization_interval': 300,
                'performance_history_size': 100
            },
            'processing': {
                'enabled': True,
                'config_path': 'processing_config.yaml'
            }
        }

    async def initialize(self):
        """初始化收集协调器"""
        if self.is_initialized:
            self.logger.warning("收集协调器已经初始化")
            return

        self.logger.info("初始化多源新闻收集协调器")

        try:
            # 初始化配置管理器
            self.config_manager = ConfigManager(self.config.get('config_manager', {}))

            # 初始化增量跟踪器
            tracker_config = self.config.get('incremental_tracker', {})
            self.tracker = IncrementalTracker(tracker_config)
            await self.tracker.initialize()

            # 初始化相关性过滤器
            filter_config = self.config.get('relevance_filter', {})
            # 加载额外的关键词配置
            keywords_config = self._load_keywords_config()
            filter_config.update(keywords_config)
            self.filter = RelevanceFilter(filter_config)

            # 初始化优先级引擎
            priority_config = self.config.get('priority_engine', {})
            # 加载优先级规则配置
            priority_rules = self._load_priority_rules()
            priority_config.update(priority_rules)
            self.priority_engine = PriorityEngine(priority_config)

            # 初始化负载均衡器
            balancer_config = self.config.get('load_balancer', {})
            self.load_balancer = LoadBalancer(balancer_config)
            await self.load_balancer.initialize()

            # 初始化收集优化器
            optimizer_config = self.config.get('optimizer', {})
            self.optimizer = CollectionOptimizer(optimizer_config)
            await self.optimizer.initialize()

            # 初始化处理管道
            processing_config = self.config.get('processing', {})
            if processing_config.get('enabled', True):
                await self._initialize_processing_pipeline(processing_config)

            # 初始化调度器
            scheduler_config = self.config.get('scheduler', {})
            self.scheduler = CollectionScheduler(scheduler_config)
            await self.scheduler.initialize()

            self.is_initialized = True
            self.logger.info("收集协调器初始化完成")

        except Exception as e:
            self.logger.error("初始化收集协调器失败", exc_info=e)
            raise

    def _load_keywords_config(self) -> Dict[str, Any]:
        """加载关键词配置"""
        keywords_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'config', 'collection', 'relevance_keywords.yaml'
        )

        try:
            with open(keywords_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"加载关键词配置失败: {e}")
            return {}

    def _load_priority_rules(self) -> Dict[str, Any]:
        """加载优先级规则配置"""
        rules_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'config', 'collection', 'priority_rules.yaml'
        )

        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.warning(f"加载优先级规则失败: {e}")
            return {}

    async def _initialize_processing_pipeline(self, processing_config: Dict[str, Any]):
        """初始化处理管道"""
        try:
            # 加载处理配置
            config_path = processing_config.get('config_path', 'processing_config.yaml')
            full_config_path = os.path.join(
                os.path.dirname(__file__), '..', '..', '..', 'config', config_path
            )

            if os.path.exists(full_config_path):
                with open(full_config_path, 'r', encoding='utf-8') as f:
                    pipeline_config_dict = yaml.safe_load(f)
                pipeline_config = ProcessingConfig(**pipeline_config_dict)
            else:
                # 使用默认配置
                pipeline_config = ProcessingConfig()

            self.processing_pipeline = PipelineManager(pipeline_config)
            self.logger.info(f"处理管道初始化完成，配置文件: {full_config_path}")

        except Exception as e:
            self.logger.error("初始化处理管道失败", exc_info=e)
            # 禁用处理管道
            self.processing_pipeline = None

    def register_adapter(self, adapter: NewsSourceAdapter):
        """注册新闻源适配器"""
        if not self.is_initialized:
            raise RuntimeError("协调器未初始化")

        adapter_id = adapter.source_name
        self.adapters[adapter_id] = adapter

        # 注册到各个组件
        self.scheduler.register_adapter(adapter)
        self.load_balancer.register_source(adapter)

        self.logger.info(f"注册适配器: {adapter_id}")

    def register_adapters_from_config(self, source_configs: List[NewsSourceConfig]):
        """从配置注册多个适配器"""
        for config in source_configs:
            if config.enabled:
                try:
                    adapter = NewsSourceAdapterFactory.create_adapter(config)
                    self.register_adapter(adapter)
                except Exception as e:
                    self.logger.error(f"注册适配器失败 {config.name}: {e}")

    async def start_collection(self):
        """启动收集过程"""
        if not self.is_initialized:
            raise RuntimeError("协调器未初始化")

        if self.is_running:
            self.logger.warning("收集过程已在运行")
            return

        self.logger.info("启动多源新闻收集过程")

        try:
            # 初始化所有适配器
            init_tasks = []
            for adapter_id, adapter in self.adapters.items():
                task = self._initialize_adapter(adapter)
                init_tasks.append(task)

            await asyncio.gather(*init_tasks, return_exceptions=True)

            # 启动调度器
            self.is_running = True

            # 添加默认收集任务
            await self._setup_default_collection_jobs()

            self.logger.info("收集过程启动完成")

        except Exception as e:
            self.logger.error("启动收集过程失败", exc_info=e)
            raise

    async def _initialize_adapter(self, adapter: NewsSourceAdapter):
        """初始化单个适配器"""
        try:
            success = await adapter.initialize()
            if success:
                self.logger.info(f"适配器初始化成功: {adapter.source_name}")
            else:
                self.logger.error(f"适配器初始化失败: {adapter.source_name}")
        except Exception as e:
            self.logger.error(f"适配器初始化异常: {adapter.source_name}", exc_info=e)

    async def _setup_default_collection_jobs(self):
        """设置默认收集任务"""
        collection_config = self.config.get('collection', {})

        # 增量收集任务
        incremental_config = {
            'window_days': collection_config.get('time_window_days', 15),
            'max_articles_per_source': collection_config.get('max_articles_per_source', 100)
        }

        schedule_config = ScheduleConfig(
            schedule_type=ScheduleType.INTERVAL,
            interval_minutes=30,  # 每30分钟执行一次
            enabled=True,
            max_concurrent_jobs=3,
            retry_attempts=3,
            retry_delay_minutes=5
        )

        self.scheduler.add_job(
            job_id="incremental_collection",
            strategy_type="incremental",
            strategy_config=incremental_config,
            schedule_config=schedule_config
        )

        # 全量收集任务（每天执行一次）
        full_schedule_config = ScheduleConfig(
            schedule_type=ScheduleType.INTERVAL,
            interval_minutes=1440,  # 24小时
            enabled=True,
            max_concurrent_jobs=1,
            retry_attempts=3,
            retry_delay_minutes=30
        )

        self.scheduler.add_job(
            job_id="full_collection",
            strategy_type="full",
            strategy_config={'max_articles_per_source': 500},
            schedule_config=full_schedule_config
        )

        self.logger.info("设置默认收集任务完成")

    async def stop_collection(self):
        """停止收集过程"""
        if not self.is_running:
            return

        self.logger.info("停止多源新闻收集过程")

        try:
            self.is_running = False

            # 关闭所有适配器
            close_tasks = []
            for adapter in self.adapters.values():
                task = adapter.close()
                close_tasks.append(task)

            await asyncio.gather(*close_tasks, return_exceptions=True)

            # 关闭各个组件
            if self.scheduler:
                await self.scheduler.shutdown()

            if self.load_balancer:
                await self.load_balancer.shutdown()

            if self.optimizer:
                await self.optimizer.shutdown()

            if self.tracker:
                await self.tracker.shutdown()

            self.logger.info("收集过程已停止")

        except Exception as e:
            self.logger.error("停止收集过程失败", exc_info=e)

    async def collect_news(self,
                          strategy_type: str = None,
                          query: Optional[NewsQuery] = None,
                          sources: Optional[List[str]] = None) -> CollectionResult:
        """执行新闻收集"""
        if not self.is_initialized:
            raise RuntimeError("协调器未初始化")

        # 使用默认策略
        if strategy_type is None:
            strategy_type = self.config.get('collection', {}).get('default_strategy', 'incremental')

        # 筛选适配器
        target_adapters = self._filter_adapters(sources)

        if not target_adapters:
            return CollectionResult(
                articles=[],
                sources_used=[],
                total_count=0,
                execution_time=0,
                errors=["没有可用的新闻源"]
            )

        try:
            # 计算优先级
            priorities = await self.priority_engine.calculate_collection_priority(target_adapters)

            # 选择最佳源
            best_source = await self.load_balancer.select_source(target_adapters, priorities)

            if best_source:
                # 只从最佳源收集
                selected_adapters = {best_source: target_adapters[best_source]}
            else:
                # 如果无法选择，使用所有可用源
                selected_adapters = target_adapters

            # 创建收集策略
            strategy_config = self.config.get('collection', {}).copy()
            strategy = CollectionStrategyFactory.create_strategy(strategy_type, strategy_config)

            # 执行优化的收集
            result = await self.optimizer.optimize_collection(strategy, selected_adapters, query)

            # 过滤相关性
            if result.articles:
                filtered_articles, relevance_scores = self.filter.filter_articles(result.articles)
                result.articles = filtered_articles
                result.total_count = len(filtered_articles)

            # 处理管道
            if result.articles and self.processing_pipeline:
                try:
                    self.logger.info(f"开始处理管道，输入 {len(result.articles)} 篇文章")
                    pipeline_result = await self.processing_pipeline.process_articles(result.articles)

                    # 更新结果为处理后的文章
                    result.articles = pipeline_result.articles
                    result.total_count = len(pipeline_result.articles)

                    # 添加处理统计信息
                    result.metadata = result.metadata or {}
                    result.metadata['processing_stats'] = {
                        'pipeline_execution_time': pipeline_result.execution_time,
                        'successful_articles': pipeline_result.stats.successful_articles,
                        'failed_articles': pipeline_result.stats.failed_articles,
                        'skipped_articles': pipeline_result.stats.skipped_articles,
                        'quality_distribution': pipeline_result.stats.quality_distribution
                    }

                    # 记录处理错误
                    if pipeline_result.errors:
                        result.errors.extend(pipeline_result.errors)

                    self.logger.info(f"处理管道完成: 成功 {pipeline_result.stats.successful_articles}, "
                                   f"失败 {pipeline_result.stats.failed_articles}, "
                                   f"跳过 {pipeline_result.stats.skipped_articles}")

                except Exception as e:
                    error_msg = f"处理管道执行失败: {str(e)}"
                    result.errors.append(error_msg)
                    self.logger.error(error_msg, exc_info=True)

            # 跟踪收集结果
            await self._track_collection_result(result)

            return result

        except Exception as e:
            self.logger.error("收集新闻失败", exc_info=e)
            return CollectionResult(
                articles=[],
                sources_used=[],
                total_count=0,
                execution_time=0,
                errors=[f"收集失败: {str(e)}"]
            )

    def _filter_adapters(self, sources: Optional[List[str]] = None) -> Dict[str, NewsSourceAdapter]:
        """筛选适配器"""
        if sources is None:
            return self.adapters.copy()

        filtered = {}
        for source_name in sources:
            if source_name in self.adapters:
                filtered[source_name] = self.adapters[source_name]
            else:
                self.logger.warning(f"未找到适配器: {source_name}")

        return filtered

    async def _track_collection_result(self, result: CollectionResult):
        """跟踪收集结果"""
        try:
            collection_time = datetime.now()

            for source_name in result.sources_used:
                # 跟踪文章
                for article in result.articles:
                    self.tracker.track_article(article)

                # 更新源跟踪信息
                self.tracker.update_source_tracking(
                    source_name=source_name,
                    collection_time=collection_time,
                    articles_count=len([a for a in result.articles if a.source == source_name]),
                    success=len(result.errors) == 0
                )

        except Exception as e:
            self.logger.error("跟踪收集结果失败", exc_info=e)

    async def get_collection_status(self) -> Dict[str, Any]:
        """获取收集状态"""
        if not self.is_initialized:
            return {"status": "not_initialized"}

        status = {
            "is_running": self.is_running,
            "registered_adapters": len(self.adapters),
            "adapter_status": {},
            "scheduler_stats": self.scheduler.get_scheduler_stats() if self.scheduler else {},
            "tracker_stats": self.tracker.get_statistics() if self.tracker else {},
            "load_balancer_stats": self.load_balancer.get_load_balancer_stats() if self.load_balancer else {},
            "optimizer_stats": self.optimizer.get_optimizer_stats() if self.optimizer else {},
            "processing_pipeline_stats": await self.get_processing_pipeline_status() if self.processing_pipeline else None
        }

        # 获取适配器状态
        for adapter_id, adapter in self.adapters.items():
            status["adapter_status"][adapter_id] = {
                "is_connected": adapter.is_connected(),
                "stats": adapter.get_stats()
            }

        return status

    async def get_processing_pipeline_status(self) -> Dict[str, Any]:
        """获取处理管道状态"""
        if not self.processing_pipeline:
            return {"status": "not_initialized"}

        try:
            # 获取管道状态
            pipeline_status = self.processing_pipeline.get_pipeline_status()

            # 获取健康状态
            health_status = await self.processing_pipeline.health_check()

            # 获取性能指标
            performance_metrics = self.processing_pipeline.get_performance_metrics()

            # 获取组件统计
            component_stats = self.processing_pipeline.get_component_stats()

            return {
                "status": "healthy",
                "pipeline_status": pipeline_status,
                "health_status": health_status,
                "performance_metrics": performance_metrics,
                "component_stats": component_stats
            }

        except Exception as e:
            self.logger.error("获取处理管道状态失败", exc_info=e)
            return {"status": "error", "error": str(e)}

    async def execute_scheduled_collection(self, job_id: str) -> Optional[CollectionResult]:
        """执行定时收集任务"""
        if not self.scheduler:
            return None

        return await self.scheduler.execute_job_now(job_id)

    def add_collection_job(self,
                           job_id: str,
                           strategy_type: str,
                           strategy_config: Dict[str, Any],
                           schedule_type: str = "interval",
                           **schedule_kwargs) -> str:
        """添加收集任务"""
        if not self.scheduler:
            raise RuntimeError("调度器未初始化")

        schedule_config = ScheduleConfig(
            schedule_type=ScheduleType(schedule_type),
            **schedule_kwargs
        )

        return self.scheduler.add_job(
            job_id=job_id,
            strategy_type=strategy_type,
            strategy_config=strategy_config,
            schedule_config=schedule_config
        )

    def remove_collection_job(self, job_id: str) -> bool:
        """移除收集任务"""
        if not self.scheduler:
            return False

        return self.scheduler.remove_job(job_id)

    def get_collection_jobs(self) -> Dict[str, Any]:
        """获取收集任务列表"""
        if not self.scheduler:
            return {}

        return self.scheduler.get_all_jobs()

    async def get_relevant_articles(self,
                                   limit: int = 100,
                                   min_relevance_score: Optional[float] = None) -> List[NewsArticle]:
        """获取相关文章"""
        if not self.tracker:
            return []

        # 获取时间窗口
        start_time, end_time = self.tracker.get_collection_window()

        # 获取窗口内的所有文章
        all_fingerprints = self.tracker.get_articles_in_window(start_time, end_time)

        # 转换为文章对象（这里需要实现从指纹重建文章的逻辑）
        # 简化实现，返回空列表
        return []

    async def cleanup_expired_data(self, days: int = 15):
        """清理过期数据"""
        if not self.tracker:
            return

        cutoff_time = datetime.now() - timedelta(days=days)
        removed_count = self.tracker.remove_expired_articles(cutoff_time)

        self.logger.info(f"清理了 {removed_count} 篇过期文章")

    async def export_collection_data(self, export_path: str) -> bool:
        """导出收集数据"""
        try:
            # 导出跟踪器数据
            tracker_success = self.tracker.export_data(export_path + "_tracker.json")

            # 导出过滤器配置
            filter_success = self.filter.export_configuration(export_path + "_filter.json")

            # 导出统计信息
            stats = await self.get_collection_status()
            import json
            with open(export_path + "_stats.json", 'w') as f:
                json.dump(stats, f, indent=2, default=str)

            return tracker_success and filter_success

        except Exception as e:
            self.logger.error("导出收集数据失败", exc_info=e)
            return False

    def configure_processing_pipeline(self, config: ProcessingConfig) -> bool:
        """配置处理管道"""
        if not self.processing_pipeline:
            self.logger.warning("处理管道未初始化")
            return False

        try:
            self.processing_pipeline.update_config(config)
            self.logger.info("处理管道配置更新完成")
            return True

        except Exception as e:
            self.logger.error("配置处理管道失败", exc_info=e)
            return False

    def enable_processing_stage(self, stage: str, enabled: bool) -> bool:
        """启用或禁用处理阶段"""
        if not self.processing_pipeline:
            self.logger.warning("处理管道未初始化")
            return False

        try:
            config = self.processing_pipeline.config
            config_dict = config.__dict__

            stage_mapping = {
                'preprocessing': 'enable_preprocessing',
                'deduplication': 'enable_deduplication',
                'noise_filtering': 'enable_noise_filtering',
                'structuring': 'enable_structuring',
                'quality_scoring': 'enable_quality_scoring'
            }

            if stage in stage_mapping:
                config_dict[stage_mapping[stage]] = enabled
                new_config = ProcessingConfig(**config_dict)
                self.processing_pipeline.update_config(new_config)
                self.logger.info(f"处理阶段 {stage} 已{'启用' if enabled else '禁用'}")
                return True
            else:
                self.logger.error(f"未知的处理阶段: {stage}")
                return False

        except Exception as e:
            self.logger.error(f"配置处理阶段失败: {stage}", exc_info=e)
            return False

    def clear_processing_cache(self) -> bool:
        """清空处理缓存"""
        if not self.processing_pipeline:
            self.logger.warning("处理管道未初始化")
            return False

        try:
            self.processing_pipeline.clear_processed_articles()
            self.logger.info("处理缓存已清空")
            return True

        except Exception as e:
            self.logger.error("清空处理缓存失败", exc_info=e)
            return False