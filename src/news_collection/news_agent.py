"""
新闻收集代理主类
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

from .models.base import (
    NewsArticle,
    NewsSourceConfig,
    NewsQuery,
    NewsQueryResult,
    NewsCategory
)
from .core.adapter import NewsSourceAdapterFactory
from .core.connection_manager import ConnectionManager, ConnectionPoolConfig
from .core.health_checker import HealthChecker, HealthCheckConfig, HealthAlert
from .core.config_manager import ConfigManager, ConfigWatcherConfig
from .core.error_handler import ErrorHandler, ErrorType, ErrorSeverity, RetryPolicy


class NewsCollectionAgent:
    """新闻收集代理主类"""

    def __init__(self,
                 config_path: Optional[str] = None,
                 connection_pool_config: Optional[ConnectionPoolConfig] = None,
                 health_check_config: Optional[HealthCheckConfig] = None,
                 config_watcher_config: Optional[ConfigWatcherConfig] = None,
                 retry_policy: Optional[RetryPolicy] = None):
        """
        初始化新闻收集代理

        Args:
            config_path: 配置文件路径
            connection_pool_config: 连接池配置
            health_check_config: 健康检查配置
            config_watcher_config: 配置监听器配置
            retry_policy: 重试策略配置
        """
        self.logger = logging.getLogger(__name__)

        # 初始化组件
        self.config_manager = ConfigManager(config_path, config_watcher_config)
        self.connection_manager = ConnectionManager(connection_pool_config)
        self.health_checker = HealthChecker(health_check_config)
        self.error_handler = ErrorHandler(retry_policy)

        # 运行状态
        self._running = False
        self._stats = {
            "start_time": None,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "articles_collected": 0
        }

        # 设置回调
        self._setup_callbacks()

    async def initialize(self) -> bool:
        """初始化代理"""
        try:
            self.logger.info("初始化新闻收集代理")

            # 初始化配置管理器
            config_success = await self.config_manager.initialize()
            if not config_success:
                self.logger.error("配置管理器初始化失败")
                return False

            # 初始化连接管理器
            await self.connection_manager.initialize()

            # 初始化健康检查器
            await self.health_checker.start()

            # 添加配置中的新闻源
            await self._load_configured_sources()

            self._stats["start_time"] = datetime.now()
            self._running = True

            self.logger.info("新闻收集代理初始化成功")
            return True

        except Exception as e:
            self.logger.error(f"初始化新闻收集代理失败: {e}")
            return False

    async def shutdown(self):
        """关闭代理"""
        try:
            self.logger.info("关闭新闻收集代理")

            self._running = False

            # 停止健康检查器
            await self.health_checker.stop()

            # 关闭连接管理器
            await self.connection_manager.shutdown()

            # 关闭配置管理器
            await self.config_manager.shutdown()

            self.logger.info("新闻收集代理已关闭")

        except Exception as e:
            self.logger.error(f"关闭新闻收集代理时出错: {e}")

    async def collect_news(self, query: NewsQuery) -> NewsQueryResult:
        """
        收集新闻

        Args:
            query: 新闻查询参数

        Returns:
            查询结果
        """
        if not self._running:
            raise RuntimeError("代理未初始化或已关闭")

        self._stats["total_requests"] += 1
        start_time = datetime.now()

        try:
            # 获取可用新闻源
            available_sources = await self.get_available_sources()

            if not available_sources:
                self._stats["failed_requests"] += 1
                return NewsQueryResult(
                    articles=[],
                    total_count=0,
                    has_more=False,
                    query=query,
                    execution_time=0,
                    sources_used=[],
                    errors=["无可用新闻源"]
                )

            # 根据查询限制选择新闻源
            sources_to_use = available_sources
            if query.sources:
                sources_to_use = [s for s in available_sources if s.name in query.sources]

            # 并行收集新闻
            tasks = []
            for source_config in sources_to_use:
                task = self._collect_from_source(source_config, query)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 合并结果
            all_articles = []
            all_errors = []
            sources_used = []

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    all_errors.append(f"新闻源 {sources_to_use[i].name} 错误: {str(result)}")
                    continue

                if result:
                    all_articles.extend(result.articles)
                    all_errors.extend(result.errors)
                    sources_used.append(result.sources_used[0] if result.sources_used else "")

            # 去重和排序
            unique_articles = self._deduplicate_articles(all_articles)
            unique_articles.sort(key=lambda x: x.published_at or datetime.min, reverse=True)

            # 限制数量
            final_articles = unique_articles[:query.limit]

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            if final_articles:
                self._stats["successful_requests"] += 1
                self._stats["articles_collected"] += len(final_articles)
            else:
                self._stats["failed_requests"] += 1

            return NewsQueryResult(
                articles=final_articles,
                total_count=len(unique_articles),
                has_more=len(unique_articles) > query.limit,
                query=query,
                execution_time=execution_time,
                sources_used=list(set(sources_used)),
                errors=all_errors
            )

        except Exception as e:
            self._stats["failed_requests"] += 1
            self.logger.error(f"收集新闻失败: {e}")
            return NewsQueryResult(
                articles=[],
                total_count=0,
                has_more=False,
                query=query,
                execution_time=(datetime.now() - start_time).total_seconds() * 1000,
                sources_used=[],
                errors=[f"收集新闻失败: {str(e)}"]
            )

    async def get_latest_news(self, limit: int = 20, sources: Optional[List[str]] = None) -> List[NewsArticle]:
        """获取最新新闻"""
        query = NewsQuery(limit=limit, sources=sources)
        result = await self.collect_news(query)
        return result.articles

    async def search_news(self, keywords: List[str], limit: int = 50,
                         sources: Optional[List[str]] = None) -> List[NewsArticle]:
        """搜索新闻"""
        query = NewsQuery(keywords=keywords, limit=limit, sources=sources)
        result = await self.collect_news(query)
        return result.articles

    async def add_news_source(self, config: NewsSourceConfig) -> bool:
        """添加新闻源"""
        try:
            # 添加到配置管理器
            config_success = await self.config_manager.add_source(config)
            if not config_success:
                return False

            # 添加到连接管理器
            connection_success = await self.connection_manager.add_source(config)
            if not connection_success:
                return False

            # 添加到健康检查器
            adapter = NewsSourceAdapterFactory.create_adapter(config)
            await adapter.initialize()
            self.health_checker.add_source(config.name, adapter)

            self.logger.info(f"成功添加新闻源: {config.name}")
            return True

        except Exception as e:
            self.logger.error(f"添加新闻源失败: {config.name}, 错误: {e}")
            return False

    async def remove_news_source(self, source_name: str) -> bool:
        """移除新闻源"""
        try:
            # 从健康检查器移除
            self.health_checker.remove_source(source_name)

            # 从连接管理器移除
            await self.connection_manager.remove_source(source_name)

            # 从配置管理器移除
            await self.config_manager.remove_source(source_name)

            self.logger.info(f"成功移除新闻源: {source_name}")
            return True

        except Exception as e:
            self.logger.error(f"移除新闻源失败: {source_name}, 错误: {e}")
            return False

    async def get_available_sources(self) -> List[NewsSourceConfig]:
        """获取可用新闻源"""
        try:
            available_names = await self.connection_manager.get_available_sources()
            all_configs = self.config_manager.get_all_sources()

            return [config for config in all_configs.values()
                   if config.name in available_names and config.enabled]

        except Exception as e:
            self.logger.error(f"获取可用新闻源失败: {e}")
            return []

    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        try:
            health_status = await self.health_checker.get_health_status()
            monitoring_summary = self.health_checker.get_monitoring_summary()

            return {
                "health_status": health_status,
                "monitoring_summary": monitoring_summary,
                "available_sources": await self.get_available_sources()
            }

        except Exception as e:
            self.logger.error(f"获取健康状态失败: {e}")
            return {}

    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            connection_stats = await self.connection_manager.get_connection_stats()
            error_stats = self.error_handler.get_error_stats()
            config_stats = self.config_manager.get_config_stats()

            runtime = datetime.now() - self._stats["start_time"] if self._stats["start_time"] else timedelta(0)

            return {
                "runtime_stats": {
                    **self._stats,
                    "runtime_seconds": runtime.total_seconds(),
                    "is_running": self._running
                },
                "connection_stats": connection_stats,
                "error_stats": error_stats,
                "config_stats": config_stats
            }

        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            return {}

    def _setup_callbacks(self):
        """设置回调函数"""
        # 配置重载回调
        self.config_manager.add_reload_callback(self._on_config_reload)

        # 健康检查告警回调
        self.health_checker.add_alert_handler(self._on_health_alert)

    async def _on_config_reload(self):
        """配置重载回调"""
        self.logger.info("配置已重载，重新加载新闻源")
        await self._load_configured_sources()

    def _on_health_alert(self, alert):
        """健康检查告警回调"""
        self.logger.warning(f"健康告警: {alert.source_name} - {alert.message}")

    async def _load_configured_sources(self):
        """加载配置中的新闻源"""
        try:
            configs = self.config_manager.get_enabled_sources()

            for config in configs:
                try:
                    # 检查是否已存在
                    available_sources = await self.connection_manager.get_available_sources()
                    if config.name in available_sources:
                        continue

                    # 添加到连接管理器
                    success = await self.connection_manager.add_source(config)
                    if success:
                        # 添加到健康检查器
                        adapter = NewsSourceAdapterFactory.create_adapter(config)
                        await adapter.initialize()
                        self.health_checker.add_source(config.name, adapter)

                        self.logger.info(f"加载新闻源: {config.name}")

                except Exception as e:
                    self.logger.error(f"加载新闻源失败: {config.name}, 错误: {e}")

        except Exception as e:
            self.logger.error(f"加载配置中的新闻源失败: {e}")

    async def _collect_from_source(self, config: NewsSourceConfig, query: NewsQuery) -> Optional[NewsQueryResult]:
        """从单个新闻源收集新闻"""
        try:
            # 获取连接
            adapter = await self.connection_manager.get_connection(config.name)
            if not adapter:
                return None

            # 创建错误上下文
            from .core.error_handler import ErrorContext
            error_context = ErrorContext(
                source_name=config.name,
                operation="fetch_news",
                timestamp=datetime.now(),
                query=query,
                config=config
            )

            # 带重试的执行
            result = await self.error_handler.execute_with_retry(
                adapter.fetch_news,
                error_context,
                query
            )

            # 释放连接
            await self.connection_manager.release_connection(config.name)

            return result

        except Exception as e:
            self.logger.error(f"从新闻源 {config.name} 收集新闻失败: {e}")
            return None

    def _deduplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """去重文章"""
        seen_titles = set()
        unique_articles = []

        for article in articles:
            # 标准化标题用于比较
            normalized_title = article.title.lower().strip()
            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_articles.append(article)

        return unique_articles

    async def retry_failed_source(self, source_name: str) -> bool:
        """重试失败的新闻源"""
        try:
            # 重置断路器
            self.error_handler.reset_circuit_breaker(source_name)

            # 重试连接
            return await self.connection_manager.retry_connection(source_name)

        except Exception as e:
            self.logger.error(f"重试新闻源失败: {source_name}, 错误: {e}")
            return False

    async def get_error_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取错误历史"""
        try:
            error_history = self.error_handler.get_error_history(limit=limit)
            return [
                {
                    "source_name": error.context.source_name,
                    "operation": error.context.operation,
                    "error_type": error.error_type.value,
                    "severity": error.severity.value,
                    "message": error.message,
                    "timestamp": error.context.timestamp.isoformat(),
                    "retry_count": error.retry_count
                }
                for error in error_history
            ]

        except Exception as e:
            self.logger.error(f"获取错误历史失败: {e}")
            return []