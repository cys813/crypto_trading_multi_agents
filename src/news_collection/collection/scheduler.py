"""
Collection scheduler implementation with intelligent timing and load management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass
from enum import Enum
import json
import os

from ..core.adapter import NewsSourceAdapter
from .strategies import CollectionStrategy, CollectionResult, CollectionStrategyFactory
from ..models.base import NewsSourceConfig


class ScheduleType(Enum):
    """调度类型枚举"""
    INTERVAL = "interval"  # 间隔调度
    CRON = "cron"  # Cron表达式调度
    IMMEDIATE = "immediate"  # 立即执行
    ON_DEMAND = "on_demand"  # 按需执行


@dataclass
class ScheduleConfig:
    """调度配置"""
    schedule_type: ScheduleType
    interval_minutes: Optional[int] = None  # 间隔调度
    cron_expression: Optional[str] = None  # Cron调度
    enabled: bool = True
    max_concurrent_jobs: int = 5
    retry_attempts: int = 3
    retry_delay_minutes: int = 5


@dataclass
class CollectionJob:
    """收集任务"""
    job_id: str
    strategy_type: str
    strategy_config: Dict[str, Any]
    schedule_config: ScheduleConfig
    created_at: datetime
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[CollectionResult] = None


class CollectionScheduler:
    """收集调度器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.jobs: Dict[str, CollectionJob] = {}
        self.running_jobs: Set[str] = set()
        self.adapters: Dict[str, NewsSourceAdapter] = {}
        self.is_running = False
        self.scheduler_task: Optional[asyncio.Task] = None

        # 状态存储路径
        self.state_file = config.get('state_file', 'scheduler_state.json')

    async def initialize(self):
        """初始化调度器"""
        self.logger.info("初始化收集调度器")

        # 加载状态
        await self._load_state()

        # 启动调度器
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())

    async def shutdown(self):
        """关闭调度器"""
        self.logger.info("关闭收集调度器")

        self.is_running = False

        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass

        # 保存状态
        await self._save_state()

    def register_adapter(self, adapter: NewsSourceAdapter):
        """注册适配器"""
        self.adapters[adapter.source_name] = adapter
        self.logger.info(f"注册适配器: {adapter.source_name}")

    def unregister_adapter(self, source_name: str):
        """注销适配器"""
        if source_name in self.adapters:
            del self.adapters[source_name]
            self.logger.info(f"注销适配器: {source_name}")

    def add_job(self,
               job_id: str,
               strategy_type: str,
               strategy_config: Dict[str, Any],
               schedule_config: ScheduleConfig) -> str:
        """添加收集任务"""
        if job_id in self.jobs:
            raise ValueError(f"任务ID已存在: {job_id}")

        job = CollectionJob(
            job_id=job_id,
            strategy_type=strategy_type,
            strategy_config=strategy_config,
            schedule_config=schedule_config,
            created_at=datetime.now()
        )

        # 计算下次运行时间
        job.next_run = self._calculate_next_run(job)

        self.jobs[job_id] = job
        self.logger.info(f"添加收集任务: {job_id} (策略: {strategy_type})")

        return job_id

    def remove_job(self, job_id: str) -> bool:
        """移除收集任务"""
        if job_id in self.jobs:
            job = self.jobs[job_id]

            # 如果任务正在运行，等待完成
            if job_id in self.running_jobs:
                self.logger.warning(f"任务 {job_id} 正在运行，将在完成后移除")
                job.status = "removing"
                return False

            del self.jobs[job_id]
            self.logger.info(f"移除收集任务: {job_id}")
            return True

        return False

    def get_job(self, job_id: str) -> Optional[CollectionJob]:
        """获取任务信息"""
        return self.jobs.get(job_id)

    def get_all_jobs(self) -> Dict[str, CollectionJob]:
        """获取所有任务"""
        return self.jobs.copy()

    def get_running_jobs(self) -> List[str]:
        """获取正在运行的任务"""
        return list(self.running_jobs)

    async def execute_job_now(self, job_id: str) -> Optional[CollectionResult]:
        """立即执行任务"""
        if job_id not in self.jobs:
            raise ValueError(f"任务不存在: {job_id}")

        job = self.jobs[job_id]

        if job_id in self.running_jobs:
            raise ValueError(f"任务正在运行: {job_id}")

        return await self._execute_job(job)

    async def _scheduler_loop(self):
        """调度器主循环"""
        self.logger.info("调度器循环启动")

        while self.is_running:
            try:
                # 检查待执行的任务
                await self._check_and_execute_jobs()

                # 清理已完成和失败的任务
                self._cleanup_jobs()

                # 保存状态
                await self._save_state()

                # 等待下一个检查周期
                await asyncio.sleep(30)  # 30秒检查一次

            except Exception as e:
                self.logger.error("调度器循环异常", exc_info=e)
                await asyncio.sleep(60)  # 出错后等待更长时间

    async def _check_and_execute_jobs(self):
        """检查并执行待运行的任务"""
        now = datetime.now()

        # 获取需要运行的任务
        ready_jobs = []
        for job_id, job in self.jobs.items():
            if (job.status == "pending" and
                job.schedule_config.enabled and
                job.next_run and
                job.next_run <= now and
                job_id not in self.running_jobs and
                len(self.running_jobs) < job.schedule_config.max_concurrent_jobs):
                ready_jobs.append((job_id, job))

        # 执行就绪任务
        for job_id, job in ready_jobs:
            if len(self.running_jobs) < job.schedule_config.max_concurrent_jobs:
                self.running_jobs.add(job_id)
                asyncio.create_task(self._execute_job_async(job))

    async def _execute_job_async(self, job: CollectionJob):
        """异步执行任务"""
        try:
            result = await self._execute_job(job)
            job.result = result
        except Exception as e:
            self.logger.error(f"任务 {job.job_id} 执行失败", exc_info=e)
            job.status = "failed"
        finally:
            self.running_jobs.discard(job.job_id)

    async def _execute_job(self, job: CollectionJob) -> CollectionResult:
        """执行单个任务"""
        self.logger.info(f"开始执行任务: {job.job_id}")

        job.status = "running"
        job.last_run = datetime.now()
        job.run_count += 1

        try:
            # 创建收集策略
            strategy = CollectionStrategyFactory.create_strategy(
                job.strategy_type,
                job.strategy_config
            )

            # 执行收集
            result = await strategy.collect(self.adapters)

            # 更新任务状态
            job.status = "completed"
            job.result = result

            # 计算下次运行时间
            job.next_run = self._calculate_next_run(job)

            self.logger.info(f"任务 {job.job_id} 执行完成，收集到 {result.total_count} 篇文章")

            return result

        except Exception as e:
            # 重试逻辑
            if job.run_count <= job.schedule_config.retry_attempts:
                self.logger.warning(f"任务 {job.job_id} 执行失败，准备重试 (第{job.run_count}次)")

                # 计算重试时间
                retry_delay = timedelta(minutes=job.schedule_config.retry_delay_minutes)
                job.next_run = datetime.now() + retry_delay
                job.status = "pending"

                raise Exception(f"任务执行失败，将重试: {str(e)}")
            else:
                job.status = "failed"
                self.logger.error(f"任务 {job.job_id} 执行失败，已达到最大重试次数")
                raise

    def _calculate_next_run(self, job: CollectionJob) -> Optional[datetime]:
        """计算下次运行时间"""
        now = datetime.now()
        schedule_config = job.schedule_config

        if not schedule_config.enabled:
            return None

        if schedule_config.schedule_type == ScheduleType.IMMEDIATE:
            return now

        elif schedule_config.schedule_type == ScheduleType.INTERVAL:
            if schedule_config.interval_minutes:
                return now + timedelta(minutes=schedule_config.interval_minutes)

        elif schedule_config.schedule_type == ScheduleType.CRON:
            # 简化的Cron表达式处理（这里可以集成更完整的Cron库）
            if schedule_config.cron_expression:
                # 这里简化处理，实际项目中可以使用croniter等库
                return now + timedelta(minutes=30)  # 默认30分钟

        elif schedule_config.schedule_type == ScheduleType.ON_DEMAND:
            return None  # 按需执行，没有固定时间

        return now + timedelta(hours=1)  # 默认1小时

    def _cleanup_jobs(self):
        """清理已完成和失败的任务"""
        # 这里可以实现任务历史记录清理逻辑
        pass

    async def _save_state(self):
        """保存调度器状态"""
        try:
            state = {
                'jobs': {},
                'timestamp': datetime.now().isoformat()
            }

            # 序列化任务状态
            for job_id, job in self.jobs.items():
                state['jobs'][job_id] = {
                    'job_id': job.job_id,
                    'strategy_type': job.strategy_type,
                    'strategy_config': job.strategy_config,
                    'schedule_config': {
                        'schedule_type': job.schedule_config.schedule_type.value,
                        'interval_minutes': job.schedule_config.interval_minutes,
                        'cron_expression': job.schedule_config.cron_expression,
                        'enabled': job.schedule_config.enabled,
                        'max_concurrent_jobs': job.schedule_config.max_concurrent_jobs,
                        'retry_attempts': job.schedule_config.retry_attempts,
                        'retry_delay_minutes': job.schedule_config.retry_delay_minutes
                    },
                    'created_at': job.created_at.isoformat(),
                    'last_run': job.last_run.isoformat() if job.last_run else None,
                    'next_run': job.next_run.isoformat() if job.next_run else None,
                    'run_count': job.run_count,
                    'status': job.status
                }

            # 保存到文件
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error("保存调度器状态失败", exc_info=e)

    async def _load_state(self):
        """加载调度器状态"""
        if not os.path.exists(self.state_file):
            return

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            # 恢复任务状态
            for job_data in state.get('jobs', {}).values():
                schedule_config_data = job_data['schedule_config']
                schedule_config = ScheduleConfig(
                    schedule_type=ScheduleType(schedule_config_data['schedule_type']),
                    interval_minutes=schedule_config_data['interval_minutes'],
                    cron_expression=schedule_config_data['cron_expression'],
                    enabled=schedule_config_data['enabled'],
                    max_concurrent_jobs=schedule_config_data['max_concurrent_jobs'],
                    retry_attempts=schedule_config_data['retry_attempts'],
                    retry_delay_minutes=schedule_config_data['retry_delay_minutes']
                )

                job = CollectionJob(
                    job_id=job_data['job_id'],
                    strategy_type=job_data['strategy_type'],
                    strategy_config=job_data['strategy_config'],
                    schedule_config=schedule_config,
                    created_at=datetime.fromisoformat(job_data['created_at']),
                    last_run=datetime.fromisoformat(job_data['last_run']) if job_data['last_run'] else None,
                    next_run=datetime.fromisoformat(job_data['next_run']) if job_data['next_run'] else None,
                    run_count=job_data['run_count'],
                    status=job_data['status']
                )

                self.jobs[job.job_id] = job

            self.logger.info(f"加载了 {len(self.jobs)} 个任务状态")

        except Exception as e:
            self.logger.error("加载调度器状态失败", exc_info=e)

    def get_scheduler_stats(self) -> Dict[str, Any]:
        """获取调度器统计信息"""
        total_jobs = len(self.jobs)
        running_jobs = len(self.running_jobs)
        pending_jobs = sum(1 for job in self.jobs.values() if job.status == "pending")
        completed_jobs = sum(1 for job in self.jobs.values() if job.status == "completed")
        failed_jobs = sum(1 for job in self.jobs.values() if job.status == "failed")

        return {
            'total_jobs': total_jobs,
            'running_jobs': running_jobs,
            'pending_jobs': pending_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'registered_adapters': len(self.adapters),
            'is_running': self.is_running
        }