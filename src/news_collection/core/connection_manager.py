"""
新闻源连接管理器 - 管理多个新闻源的连接和生命周期
"""

import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

from ..models.base import NewsSourceConfig, ConnectionInfo, HealthStatus, NewsSourceStatus
from .adapter import NewsSourceAdapter, NewsSourceAdapterFactory


@dataclass
class ConnectionPoolConfig:
    """连接池配置"""
    max_connections_per_source: int = 5
    connection_timeout: int = 30  # seconds
    idle_timeout: int = 300  # seconds (5 minutes)
    health_check_interval: int = 30  # seconds
    retry_attempts: int = 3
    retry_delay: float = 1.0  # seconds


class ConnectionManager:
    """新闻源连接管理器"""

    def __init__(self, pool_config: Optional[ConnectionPoolConfig] = None):
        self.pool_config = pool_config or ConnectionPoolConfig()
        self._connections: Dict[str, List[NewsSourceAdapter]] = {}
        self._active_connections: Dict[str, NewsSourceAdapter] = {}
        self._connection_stats: Dict[str, Dict] = {}
        self._health_status: Dict[str, HealthStatus] = {}
        self._lock = asyncio.Lock()
        self._health_check_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._logger = logging.getLogger(__name__)

    async def initialize(self):
        """初始化连接管理器"""
        self._logger.info("初始化连接管理器")
        await self._start_health_check()
        await self._start_cleanup_task()

    async def shutdown(self):
        """关闭连接管理器"""
        self._logger.info("关闭连接管理器")

        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # 关闭所有连接
        await self.close_all_connections()

    async def add_source(self, config: NewsSourceConfig) -> bool:
        """添加新闻源"""
        async with self._lock:
            if config.name in self._connections:
                self._logger.warning(f"新闻源 {config.name} 已存在")
                return False

            try:
                adapter = NewsSourceAdapterFactory.create_adapter(config)
                success = await adapter.initialize()

                if success:
                    self._connections[config.name] = [adapter]
                    self._connection_stats[config.name] = {
                        'total_requests': 0,
                        'successful_requests': 0,
                        'failed_requests': 0,
                        'last_used': None,
                        'connection_time': datetime.now()
                    }
                    self._logger.info(f"成功添加新闻源: {config.name}")
                    return True
                else:
                    self._logger.error(f"初始化新闻源失败: {config.name}")
                    return False

            except Exception as e:
                self._logger.error(f"添加新闻源异常: {config.name}, 错误: {e}")
                return False

    async def remove_source(self, source_name: str) -> bool:
        """移除新闻源"""
        async with self._lock:
            if source_name not in self._connections:
                self._logger.warning(f"新闻源 {source_name} 不存在")
                return False

            try:
                # 关闭所有连接
                adapters = self._connections.pop(source_name, [])
                for adapter in adapters:
                    await adapter.close()

                # 清理相关数据
                self._active_connections.pop(source_name, None)
                self._connection_stats.pop(source_name, None)
                self._health_status.pop(source_name, None)

                self._logger.info(f"成功移除新闻源: {source_name}")
                return True

            except Exception as e:
                self._logger.error(f"移除新闻源异常: {source_name}, 错误: {e}")
                return False

    async def get_connection(self, source_name: str) -> Optional[NewsSourceAdapter]:
        """获取新闻源连接"""
        async with self._lock:
            if source_name not in self._connections:
                return None

            adapters = self._connections[source_name]

            # 查找可用连接
            for adapter in adapters:
                if adapter.is_connected():
                    self._active_connections[source_name] = adapter
                    self._update_stats(source_name)
                    return adapter

            # 如果没有可用连接，尝试创建新连接
            if len(adapters) < self.pool_config.max_connections_per_source:
                try:
                    config = adapters[0].config if adapters else None
                    if config:
                        new_adapter = NewsSourceAdapterFactory.create_adapter(config)
                        success = await new_adapter.initialize()

                        if success:
                            adapters.append(new_adapter)
                            self._active_connections[source_name] = new_adapter
                            self._update_stats(source_name)
                            return new_adapter
                except Exception as e:
                    self._logger.error(f"创建新连接失败: {source_name}, 错误: {e}")

            return None

    async def release_connection(self, source_name: str):
        """释放连接"""
        async with self._lock:
            self._active_connections.pop(source_name, None)

    async def get_available_sources(self) -> List[str]:
        """获取可用新闻源列表"""
        async with self._lock:
            available_sources = []
            for source_name, adapters in self._connections.items():
                for adapter in adapters:
                    if adapter.is_connected():
                        available_sources.append(source_name)
                        break
            return available_sources

    async def get_connection_stats(self, source_name: Optional[str] = None) -> Dict:
        """获取连接统计信息"""
        async with self._lock:
            if source_name:
                return self._connection_stats.get(source_name, {})
            else:
                return self._connection_stats.copy()

    async def get_health_status(self, source_name: Optional[str] = None) -> Dict[str, HealthStatus]:
        """获取健康状态"""
        async with self._lock:
            if source_name:
                return self._health_status.get(source_name)
            else:
                return self._health_status.copy()

    async def close_all_connections(self):
        """关闭所有连接"""
        async with self._lock:
            for source_name, adapters in self._connections.items():
                for adapter in adapters:
                    try:
                        await adapter.close()
                    except Exception as e:
                        self._logger.error(f"关闭连接失败: {source_name}, 错误: {e}")

            self._connections.clear()
            self._active_connections.clear()

    def _update_stats(self, source_name: str):
        """更新统计信息"""
        if source_name in self._connection_stats:
            self._connection_stats[source_name]['last_used'] = datetime.now()
            self._connection_stats[source_name]['total_requests'] += 1

    async def _start_health_check(self):
        """启动健康检查任务"""
        self._health_check_task = asyncio.create_task(self._health_check_loop())

    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await asyncio.sleep(self.pool_config.health_check_interval)
                await self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"健康检查异常: {e}")

    async def _perform_health_checks(self):
        """执行健康检查"""
        async with self._lock:
            for source_name, adapters in self._connections.items():
                if adapters:
                    adapter = adapters[0]  # 使用第一个连接进行健康检查
                    try:
                        health_status = await adapter.health_check()
                        self._health_status[source_name] = health_status

                        if not health_status.is_healthy:
                            self._logger.warning(f"新闻源 {source_name} 健康检查失败: {health_status.error_message}")

                    except Exception as e:
                        self._logger.error(f"健康检查异常: {source_name}, 错误: {e}")
                        self._health_status[source_name] = HealthStatus(
                            is_healthy=False,
                            response_time=0,
                            status=NewsSourceStatus.OFFLINE,
                            last_check=datetime.now(),
                            error_message=str(e)
                        )

    async def _start_cleanup_task(self):
        """启动清理任务"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        """清理循环"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟清理一次
                await self._cleanup_idle_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"清理任务异常: {e}")

    async def _cleanup_idle_connections(self):
        """清理空闲连接"""
        async with self._lock:
            current_time = datetime.now()
            sources_to_cleanup = []

            for source_name, adapters in self._connections.items():
                active_adapters = []
                for adapter in adapters:
                    connection_info = adapter.get_connection_info()
                    if connection_info and connection_info.is_active:
                        # 检查是否空闲超时
                        idle_time = (current_time - connection_info.last_used).total_seconds()
                        if idle_time > self.pool_config.idle_timeout:
                            await adapter.close()
                        else:
                            active_adapters.append(adapter)
                    else:
                        active_adapters.append(adapter)

                self._connections[source_name] = active_adapters

    async def retry_connection(self, source_name: str) -> bool:
        """重试连接"""
        async with self._lock:
            if source_name not in self._connections:
                return False

            for attempt in range(self.pool_config.retry_attempts):
                try:
                    adapters = self._connections[source_name]
                    if adapters:
                        adapter = adapters[0]
                        await adapter.close()
                        success = await adapter.initialize()

                        if success:
                            self._logger.info(f"重试连接成功: {source_name}")
                            return True

                        await asyncio.sleep(self.pool_config.retry_delay)

                except Exception as e:
                    self._logger.error(f"重试连接异常: {source_name}, 尝试 {attempt + 1}, 错误: {e}")
                    await asyncio.sleep(self.pool_config.retry_delay)

            self._logger.error(f"重试连接失败: {source_name}")
            return False