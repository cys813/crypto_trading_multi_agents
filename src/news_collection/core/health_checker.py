"""
新闻源健康检查器 - 实时监控新闻源健康状态
"""

import asyncio
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, field
from enum import Enum

from ..models.base import HealthStatus, NewsSourceStatus, NewsSourceConfig
from .adapter import NewsSourceAdapter


class HealthCheckLevel(Enum):
    """健康检查级别"""
    BASIC = "basic"  # 基本连接检查
    DETAILED = "detailed"  # 详细功能检查
    COMPREHENSIVE = "comprehensive"  # 全面性能检查


@dataclass
class HealthCheckConfig:
    """健康检查配置"""
    check_interval: int = 30  # seconds
    timeout: int = 10  # seconds
    max_failures: int = 3  # 最大失败次数
    recovery_threshold: int = 2  # 恢复阈值（连续成功次数）
    check_level: HealthCheckLevel = HealthCheckLevel.BASIC
    enable_alerts: bool = True
    alert_cooldown: int = 300  # 5分钟冷却时间


@dataclass
class HealthAlert:
    """健康告警"""
    source_name: str
    alert_type: str
    message: str
    severity: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class HealthChecker:
    """新闻源健康检查器"""

    def __init__(self, config: Optional[HealthCheckConfig] = None):
        self.config = config or HealthCheckConfig()
        self._health_status: Dict[str, HealthStatus] = {}
        self._check_tasks: Dict[str, asyncio.Task] = {}
        self._alert_handlers: List[Callable[[HealthAlert], None]] = []
        self._alert_history: List[HealthAlert] = []
        self._last_alert_time: Dict[str, datetime] = {}
        self._logger = logging.getLogger(__name__)
        self._running = False

    async def start(self):
        """启动健康检查器"""
        self._running = True
        self._logger.info("启动健康检查器")

    async def stop(self):
        """停止健康检查器"""
        self._running = False
        self._logger.info("停止健康检查器")

        # 取消所有检查任务
        for task in self._check_tasks.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._check_tasks.clear()

    def add_source(self, source_name: str, adapter: NewsSourceAdapter):
        """添加新闻源进行健康检查"""
        if source_name in self._check_tasks:
            self._logger.warning(f"新闻源 {source_name} 已在监控中")
            return

        # 启动健康检查任务
        task = asyncio.create_task(self._health_check_loop(source_name, adapter))
        self._check_tasks[source_name] = task

        # 初始化健康状态
        self._health_status[source_name] = HealthStatus(
            is_healthy=True,
            response_time=0,
            status=NewsSourceStatus.ONLINE,
            last_check=datetime.now()
        )

        self._logger.info(f"开始监控新闻源: {source_name}")

    def remove_source(self, source_name: str):
        """移除新闻源监控"""
        if source_name in self._check_tasks:
            task = self._check_tasks.pop(source_name)
            task.cancel()
            try:
                task.result()
            except asyncio.CancelledError:
                pass

            self._health_status.pop(source_name, None)
            self._last_alert_time.pop(source_name, None)

            self._logger.info(f"停止监控新闻源: {source_name}")

    def add_alert_handler(self, handler: Callable[[HealthAlert], None]):
        """添加告警处理器"""
        self._alert_handlers.append(handler)

    def remove_alert_handler(self, handler: Callable[[HealthAlert], None]):
        """移除告警处理器"""
        if handler in self._alert_handlers:
            self._alert_handlers.remove(handler)

    def get_health_status(self, source_name: Optional[str] = None) -> Dict[str, HealthStatus]:
        """获取健康状态"""
        if source_name:
            return self._health_status.get(source_name)
        else:
            return self._health_status.copy()

    def get_alert_history(self, source_name: Optional[str] = None,
                         limit: int = 100) -> List[HealthAlert]:
        """获取告警历史"""
        if source_name:
            alerts = [alert for alert in self._alert_history if alert.source_name == source_name]
        else:
            alerts = self._alert_history.copy()

        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def perform_manual_check(self, source_name: str, adapter: NewsSourceAdapter) -> HealthStatus:
        """执行手动健康检查"""
        self._logger.info(f"执行手动健康检查: {source_name}")
        return await self._perform_health_check(source_name, adapter)

    async def _health_check_loop(self, source_name: str, adapter: NewsSourceAdapter):
        """健康检查循环"""
        while self._running:
            try:
                # 执行健康检查
                health_status = await self._perform_health_check(source_name, adapter)
                self._health_status[source_name] = health_status

                # 处理状态变化
                await self._handle_status_change(source_name, health_status)

                # 等待下次检查
                await asyncio.sleep(self.config.check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"健康检查异常: {source_name}, 错误: {e}")
                # 记录失败状态
                self._health_status[source_name] = HealthStatus(
                    is_healthy=False,
                    response_time=0,
                    status=NewsSourceStatus.OFFLINE,
                    last_check=datetime.now(),
                    error_message=str(e)
                )
                await asyncio.sleep(self.config.check_interval)

    async def _perform_health_check(self, source_name: str, adapter: NewsSourceAdapter) -> HealthStatus:
        """执行健康检查"""
        start_time = datetime.now()

        try:
            if self.config.check_level == HealthCheckLevel.BASIC:
                health_status = await self._basic_health_check(adapter)
            elif self.config.check_level == HealthCheckLevel.DETAILED:
                health_status = await self._detailed_health_check(adapter)
            else:  # COMPREHENSIVE
                health_status = await self._comprehensive_health_check(adapter)

            response_time = (datetime.now() - start_time).total_seconds() * 1000
            health_status.response_time = response_time
            health_status.last_check = start_time

            return health_status

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            return HealthStatus(
                is_healthy=False,
                response_time=response_time,
                status=NewsSourceStatus.OFFLINE,
                last_check=start_time,
                error_message=str(e)
            )

    async def _basic_health_check(self, adapter: NewsSourceAdapter) -> HealthStatus:
        """基本健康检查 - 只检查连接"""
        try:
            # 使用适配器的健康检查方法
            return await adapter.health_check()

        except Exception as e:
            return HealthStatus(
                is_healthy=False,
                response_time=0,
                status=NewsSourceStatus.OFFLINE,
                last_check=datetime.now(),
                error_message=str(e)
            )

    async def _detailed_health_check(self, adapter: NewsSourceAdapter) -> HealthStatus:
        """详细健康检查 - 检查基本功能"""
        try:
            # 基本连接检查
            basic_status = await self._basic_health_check(adapter)
            if not basic_status.is_healthy:
                return basic_status

            # 检查获取最新新闻功能
            try:
                await adapter.get_latest_news(limit=1)
            except Exception as e:
                return HealthStatus(
                    is_healthy=False,
                    response_time=basic_status.response_time,
                    status=NewsSourceStatus.DEGRADED,
                    last_check=datetime.now(),
                    error_message=f"功能检查失败: {str(e)}"
                )

            return HealthStatus(
                is_healthy=True,
                response_time=basic_status.response_time,
                status=NewsSourceStatus.ONLINE,
                last_check=datetime.now()
            )

        except Exception as e:
            return HealthStatus(
                is_healthy=False,
                response_time=0,
                status=NewsSourceStatus.OFFLINE,
                last_check=datetime.now(),
                error_message=str(e)
            )

    async def _comprehensive_health_check(self, adapter: NewsSourceAdapter) -> HealthStatus:
        """全面健康检查 - 检查性能和功能"""
        try:
            # 详细健康检查
            detailed_status = await self._detailed_health_check(adapter)
            if not detailed_status.is_healthy:
                return detailed_status

            # 性能测试
            start_time = datetime.now()
            try:
                # 测试获取多条新闻
                articles = await adapter.get_latest_news(limit=5)
                if len(articles) == 0:
                    return HealthStatus(
                        is_healthy=False,
                        response_time=detailed_status.response_time,
                        status=NewsSourceStatus.DEGRADED,
                        last_check=datetime.now(),
                        error_message="未获取到任何新闻"
                    )

                # 测试搜索功能
                search_results = await adapter.search_news(['bitcoin'], limit=3)
                if len(search_results) == 0:
                    return HealthStatus(
                        is_healthy=False,
                        response_time=detailed_status.response_time,
                        status=NewsSourceStatus.DEGRADED,
                        last_check=datetime.now(),
                        error_message="搜索功能异常"
                    )

            except Exception as e:
                return HealthStatus(
                    is_healthy=False,
                    response_time=detailed_status.response_time,
                    status=NewsSourceStatus.DEGRADED,
                    last_check=datetime.now(),
                    error_message=f"性能测试失败: {str(e)}"
                )

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            # 根据响应时间判断状态
            if response_time > 5000:  # 5秒
                status = NewsSourceStatus.DEGRADED
            else:
                status = NewsSourceStatus.ONLINE

            return HealthStatus(
                is_healthy=True,
                response_time=response_time,
                status=status,
                last_check=datetime.now()
            )

        except Exception as e:
            return HealthStatus(
                is_healthy=False,
                response_time=0,
                status=NewsSourceStatus.OFFLINE,
                last_check=datetime.now(),
                error_message=str(e)
            )

    async def _handle_status_change(self, source_name: str, current_status: HealthStatus):
        """处理状态变化"""
        previous_status = self._health_status.get(source_name)

        if previous_status is None:
            return

        # 检查状态变化
        if previous_status.is_healthy != current_status.is_healthy:
            if not current_status.is_healthy:
                # 从健康变为不健康
                await self._create_alert(source_name, "DOWN",
                                       f"新闻源 {source_name} 不可用: {current_status.error_message}", "HIGH")
            else:
                # 从不健康变为健康
                await self._create_alert(source_name, "UP",
                                       f"新闻源 {source_name} 已恢复", "NORMAL")
                # 标记相关告警为已解决
                await self._resolve_alerts(source_name)

        # 检查状态级别变化
        elif previous_status.status != current_status.status:
            if current_status.status == NewsSourceStatus.DEGRADED:
                await self._create_alert(source_name, "DEGRADED",
                                       f"新闻源 {source_name} 性能下降", "MEDIUM")

    async def _create_alert(self, source_name: str, alert_type: str,
                           message: str, severity: str):
        """创建告警"""
        # 检查告警冷却
        last_alert_time = self._last_alert_time.get(source_name)
        if last_alert_time:
            cooldown_passed = (datetime.now() - last_alert_time).total_seconds() > self.config.alert_cooldown
            if not cooldown_passed:
                return

        alert = HealthAlert(
            source_name=source_name,
            alert_type=alert_type,
            message=message,
            severity=severity,
            timestamp=datetime.now()
        )

        self._alert_history.append(alert)
        self._last_alert_time[source_name] = datetime.now()

        self._logger.warning(f"告警: {message}")

        # 通知告警处理器
        if self.config.enable_alerts:
            for handler in self._alert_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    self._logger.error(f"告警处理器异常: {e}")

    async def _resolve_alerts(self, source_name: str):
        """解决告警"""
        for alert in self._alert_history:
            if alert.source_name == source_name and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                self._logger.info(f"告警已解决: {alert.message}")

    def get_monitoring_summary(self) -> Dict:
        """获取监控摘要"""
        total_sources = len(self._health_status)
        healthy_sources = sum(1 for status in self._health_status.values() if status.is_healthy)
        offline_sources = total_sources - healthy_sources

        active_alerts = len([alert for alert in self._alert_history if not alert.resolved])

        return {
            "total_sources": total_sources,
            "healthy_sources": healthy_sources,
            "offline_sources": offline_sources,
            "health_percentage": (healthy_sources / max(total_sources, 1)) * 100,
            "active_alerts": active_alerts,
            "total_alerts": len(self._alert_history),
            "check_level": self.config.check_level.value,
            "last_update": max((status.last_check for status in self._health_status.values()), default=datetime.now())
        }