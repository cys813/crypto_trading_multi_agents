"""
Analysis Orchestrator for Long Analyst Agent.

This module orchestrates the execution of analysis tasks across different
timeframes and symbols, managing priorities and resource allocation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import time
import heapq
from datetime import datetime, timedelta

from ..models.market_data import Timeframe, MarketData
from ..models.analysis_result import AnalysisResult, AnalysisDimension
from ..events.event_manager import EventManager
from ..utils.performance_monitor import PerformanceMonitor


class Priority(Enum):
    """Task priorities."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AnalysisTask:
    """Analysis task definition."""
    id: str
    symbol: str
    timeframe: Timeframe
    priority: Priority
    created_at: float
    scheduled_at: float
    max_execution_time: float
    retry_count: int = 0
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None

    def __lt__(self, other):
        """Define task ordering for priority queue."""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value  # Higher priority first
        return self.scheduled_at < other.scheduled_at  # Earlier tasks first


@dataclass
class OrchestratorConfig:
    """Configuration for analysis orchestrator."""

    # Task management
    max_concurrent_tasks: int = 10
    max_pending_tasks: int = 1000
    task_timeout_seconds: int = 300

    # Scheduling
    enable_priority_scheduling: bool = True
    enable_load_balancing: bool = True
    schedule_interval_seconds: float = 1.0

    # Retry settings
    max_retry_attempts: int = 3
    retry_delay_seconds: float = 5.0
    backoff_factor: float = 2.0

    # Resource management
    cpu_threshold: float = 0.8
    memory_threshold: float = 0.8
    enable_resource_monitoring: bool = True

    # Analysis settings
    default_timeframes: List[Timeframe] = None
    analysis_interval_seconds: Dict[Timeframe, int] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.default_timeframes is None:
            self.default_timeframes = [Timeframe.M1, Timeframe.M5, Timeframe.M15, Timeframe.H1, Timeframe.H4]

        if self.analysis_interval_seconds is None:
            self.analysis_interval_seconds = {
                Timeframe.M1: 60,
                Timeframe.M5: 300,
                Timeframe.M15: 900,
                Timeframe.H1: 3600,
                Timeframe.H4: 14400,
                Timeframe.D1: 86400
            }


class AnalysisOrchestrator:
    """
    Orchestrator for analysis task execution.

    This class manages the scheduling, execution, and monitoring of
    analysis tasks across different symbols and timeframes.
    """

    def __init__(self, analysis_timeframes: List[Timeframe] = None, config: OrchestratorConfig = None):
        """Initialize the analysis orchestrator."""
        self.analysis_timeframes = analysis_timeframes or [Timeframe.H1, Timeframe.H4]
        self.config = config or OrchestratorConfig()
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()
        self.event_manager = EventManager()

        # Task management
        self.task_queue = []
        self.running_tasks = {}
        self.completed_tasks = {}
        self.task_counter = 0

        # Symbol management
        self.symbol_analysis_schedule = {}
        self.symbol_last_analysis = {}

        # Resource monitoring
        self.system_resources = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'active_tasks': 0
        }

        # Background tasks
        self.background_tasks = []
        self.is_running = False

        # Metrics
        self.metrics = {
            'total_tasks_created': 0,
            'total_tasks_completed': 0,
            'total_tasks_failed': 0,
            'total_retry_attempts': 0,
            'average_execution_time': 0.0,
            'tasks_per_second': 0.0
        }

        self.logger.info("Analysis orchestrator initialized")

    async def start(self):
        """Start the analysis orchestrator."""
        self.logger.info("Starting analysis orchestrator")

        if self.is_running:
            self.logger.warning("Analysis orchestrator is already running")
            return

        # Initialize symbol schedules
        await self._initialize_symbol_schedules()

        # Start background tasks
        self.background_tasks = [
            asyncio.create_task(self._task_scheduling_loop()),
            asyncio.create_task(self._task_execution_loop()),
            asyncio.create_task(self._resource_monitoring_loop()),
            asyncio.create_task(self._metric_collection_loop())
        ]

        self.is_running = True
        self.logger.info("Analysis orchestrator started")

    async def stop(self):
        """Stop the analysis orchestrator."""
        self.logger.info("Stopping analysis orchestrator")

        if not self.is_running:
            self.logger.warning("Analysis orchestrator is not running")
            return

        self.is_running = False

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)

        # Cancel running tasks
        for task_id, task in list(self.running_tasks.items()):
            task.status = TaskStatus.CANCELLED
            self.logger.info(f"Cancelled task {task_id}")

        self.background_tasks.clear()
        self.logger.info("Analysis orchestrator stopped")

    async def schedule_analysis(self, symbol: str, timeframe: Timeframe,
                               priority: Priority = Priority.NORMAL) -> str:
        """
        Schedule an analysis task.

        Args:
            symbol: Trading symbol to analyze
            timeframe: Timeframe for analysis
            priority: Task priority

        Returns:
            Task ID
        """
        self.task_counter += 1
        task_id = f"task_{self.task_counter}_{int(time.time())}"

        # Calculate next scheduled time
        next_analysis_time = self._calculate_next_analysis_time(symbol, timeframe)

        task = AnalysisTask(
            id=task_id,
            symbol=symbol,
            timeframe=timeframe,
            priority=priority,
            created_at=time.time(),
            scheduled_at=next_analysis_time,
            max_execution_time=self.config.task_timeout_seconds,
            max_retries=self.config.max_retry_attempts
        )

        # Add to priority queue
        heapq.heappush(self.task_queue, task)

        # Update metrics
        self.metrics['total_tasks_created'] += 1

        # Emit scheduling event
        await self.event_manager.emit("task_scheduled", {
            "task_id": task_id,
            "symbol": symbol,
            "timeframe": timeframe.value,
            "priority": priority.value,
            "scheduled_at": next_analysis_time
        })

        self.logger.info(f"Scheduled analysis task {task_id} for {symbol} ({timeframe.value})")
        return task_id

    async def get_triggered_symbols(self) -> List[Tuple[str, Timeframe]]:
        """
        Get symbols that need immediate analysis.

        Returns:
            List of (symbol, timeframe) tuples that need analysis
        """
        triggered = []
        current_time = time.time()

        # Check for overdue tasks
        while self.task_queue and self.task_queue[0].scheduled_at <= current_time:
            task = heapq.heappop(self.task_queue)

            if task.status == TaskStatus.PENDING:
                triggered.append((task.symbol, task.timeframe))

                # Schedule next analysis
                next_time = self._calculate_next_analysis_time(task.symbol, task.timeframe)
                task.scheduled_at = next_time
                heapq.heappush(self.task_queue, task)

        return triggered

    async def execute_task(self, task: AnalysisTask) -> AnalysisResult:
        """
        Execute an analysis task.

        Args:
            task: Task to execute

        Returns:
            Analysis result
        """
        start_time = time.time()

        try:
            # Update task status
            task.status = TaskStatus.RUNNING
            self.running_tasks[task.id] = task

            # Emit task start event
            await self.event_manager.emit("task_started", {
                "task_id": task.id,
                "symbol": task.symbol,
                "timeframe": task.timeframe.value
            })

            # Execute analysis (this would be integrated with actual analysis engines)
            result = await self._execute_analysis(task)

            # Update task status
            task.status = TaskStatus.COMPLETED
            task.result = result

            # Update metrics
            self.metrics['total_tasks_completed'] += 1
            execution_time = (time.time() - start_time)
            self.metrics['average_execution_time'] = (
                (self.metrics['average_execution_time'] * (self.metrics['total_tasks_completed'] - 1) + execution_time) /
                self.metrics['total_tasks_completed']
            )

            # Store completed task
            self.completed_tasks[task.id] = task

            # Remove from running tasks
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]

            # Emit task completion event
            await self.event_manager.emit("task_completed", {
                "task_id": task.id,
                "symbol": task.symbol,
                "timeframe": task.timeframe.value,
                "execution_time": execution_time,
                "success": True
            })

            return result

        except Exception as e:
            # Handle task failure
            task.status = TaskStatus.FAILED
            task.error = str(e)

            # Update metrics
            self.metrics['total_tasks_failed'] += 1

            # Remove from running tasks
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]

            # Emit task failure event
            await self.event_manager.emit("task_failed", {
                "task_id": task.id,
                "symbol": task.symbol,
                "timeframe": task.timeframe.value,
                "error": str(e)
            })

            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                task.scheduled_at = time.time() + (task.retry_delay * (self.config.backoff_factor ** task.retry_count))

                # Add back to queue
                heapq.heappush(self.task_queue, task)

                self.metrics['total_retry_attempts'] += 1
                self.logger.info(f"Retrying task {task.id} (attempt {task.retry_count})")

            raise

    async def _execute_analysis(self, task: AnalysisTask) -> AnalysisResult:
        """Execute the actual analysis for a task."""
        # This is a placeholder - in a real implementation, this would
        # call the actual analysis engines (technical, fundamental, sentiment)

        # Simulate analysis time
        await asyncio.sleep(0.1)

        # Create mock analysis result
        result = AnalysisResult(
            symbol=task.symbol,
            timeframe=task.timeframe,
            timestamp=time.time(),
            dimensions={
                AnalysisDimension.TECHNICAL: {
                    'score': 0.7,
                    'confidence': 0.8,
                    'indicators': ['RSI', 'MACD', 'Bollinger Bands']
                },
                AnalysisDimension.FUNDAMENTAL: {
                    'score': 0.6,
                    'confidence': 0.7,
                    'factors': ['market_cap', 'volume', 'adoption']
                },
                AnalysisDimension.SENTIMENT: {
                    'score': 0.8,
                    'confidence': 0.6,
                    'sources': ['news', 'social_media']
                }
            },
            overall_score=0.7,
            confidence=0.7,
            metadata={
                'task_id': task.id,
                'execution_time': time.time() - task.created_at,
                'data_points': 1000
            }
        )

        return result

    async def _task_scheduling_loop(self):
        """Background task for scheduling analysis tasks."""
        self.logger.info("Starting task scheduling loop")

        while self.is_running:
            try:
                # Schedule regular analysis for configured timeframes
                for symbol in self.symbol_analysis_schedule:
                    for timeframe in self.analysis_timeframes:
                        await self._schedule_regular_analysis(symbol, timeframe)

                # Sleep for scheduling interval
                await asyncio.sleep(self.config.schedule_interval_seconds)

            except Exception as e:
                self.logger.error(f"Error in task scheduling loop: {e}")
                await asyncio.sleep(5)

        self.logger.info("Task scheduling loop stopped")

    async def _task_execution_loop(self):
        """Background task for executing analysis tasks."""
        self.logger.info("Starting task execution loop")

        while self.is_running:
            try:
                # Check resource availability
                if self._can_execute_task():
                    # Get next task to execute
                    current_time = time.time()
                    executable_tasks = []

                    # Find tasks that are ready to execute
                    temp_queue = []
                    while self.task_queue:
                        task = heapq.heappop(self.task_queue)
                        if task.scheduled_at <= current_time and task.status == TaskStatus.PENDING:
                            executable_tasks.append(task)
                        else:
                            temp_queue.append(task)

                    # Put back non-executable tasks
                    for task in temp_queue:
                        heapq.heappush(self.task_queue, task)

                    # Execute highest priority task
                    if executable_tasks:
                        task = executable_tasks[0]  # Already sorted by priority
                        try:
                            await self.execute_task(task)
                        except Exception as e:
                            self.logger.error(f"Error executing task {task.id}: {e}")

                else:
                    # Wait for resources to become available
                    await asyncio.sleep(1.0)

            except Exception as e:
                self.logger.error(f"Error in task execution loop: {e}")
                await asyncio.sleep(5)

        self.logger.info("Task execution loop stopped")

    async def _resource_monitoring_loop(self):
        """Background task for resource monitoring."""
        self.logger.info("Starting resource monitoring loop")

        while self.is_running:
            try:
                if self.config.enable_resource_monitoring:
                    # Update system resources
                    self.system_resources['active_tasks'] = len(self.running_tasks)

                    # Check resource thresholds
                    if self.system_resources['active_tasks'] >= self.config.max_concurrent_tasks:
                        self.logger.warning("Maximum concurrent tasks reached")

                await asyncio.sleep(5)

            except Exception as e:
                self.logger.error(f"Error in resource monitoring loop: {e}")
                await asyncio.sleep(10)

        self.logger.info("Resource monitoring loop stopped")

    async def _metric_collection_loop(self):
        """Background task for collecting metrics."""
        self.logger.info("Starting metric collection loop")

        while self.is_running:
            try:
                # Calculate tasks per second
                current_time = time.time()
                if hasattr(self, '_last_metric_time'):
                    time_diff = current_time - self._last_metric_time
                    if time_diff > 0:
                        tasks_completed = self.metrics['total_tasks_completed']
                        if hasattr(self, '_last_completed_count'):
                            recent_tasks = tasks_completed - self._last_completed_count
                            self.metrics['tasks_per_second'] = recent_tasks / time_diff

                        self._last_completed_count = tasks_completed

                self._last_metric_time = current_time

                # Record metrics
                self.performance_monitor.record_metric("active_tasks", len(self.running_tasks))
                self.performance_monitor.record_metric("pending_tasks", len(self.task_queue))
                self.performance_monitor.record_metric("total_tasks_created", self.metrics['total_tasks_created'])
                self.performance_monitor.record_metric("total_tasks_completed", self.metrics['total_tasks_completed'])
                self.performance_monitor.record_metric("total_tasks_failed", self.metrics['total_tasks_failed'])

                await asyncio.sleep(30)  # Collect metrics every 30 seconds

            except Exception as e:
                self.logger.error(f"Error in metric collection loop: {e}")
                await asyncio.sleep(30)

        self.logger.info("Metric collection loop stopped")

    def _can_execute_task(self) -> bool:
        """Check if a task can be executed based on resource availability."""
        if not self.config.enable_resource_monitoring:
            return True

        return len(self.running_tasks) < self.config.max_concurrent_tasks

    def _calculate_next_analysis_time(self, symbol: str, timeframe: Timeframe) -> float:
        """Calculate the next analysis time for a symbol and timeframe."""
        current_time = time.time()

        # Get the last analysis time for this symbol/timeframe
        last_analysis = self.symbol_last_analysis.get(f"{symbol}_{timeframe.value}", 0)

        # Get the analysis interval for this timeframe
        interval = self.config.analysis_interval_seconds.get(timeframe, 3600)

        # Calculate next analysis time
        next_time = max(last_analysis + interval, current_time)

        return next_time

    async def _schedule_regular_analysis(self, symbol: str, timeframe: Timeframe):
        """Schedule regular analysis for a symbol and timeframe."""
        last_analysis = self.symbol_last_analysis.get(f"{symbol}_{timeframe.value}", 0)
        current_time = time.time()
        interval = self.config.analysis_interval_seconds.get(timeframe, 3600)

        if current_time - last_analysis >= interval:
            # Schedule new analysis
            await self.schedule_analysis(symbol, timeframe)
            self.symbol_last_analysis[f"{symbol}_{timeframe.value}"] = current_time

    async def _initialize_symbol_schedules(self):
        """Initialize symbol analysis schedules."""
        # This would typically be populated with the list of symbols to analyze
        self.symbol_analysis_schedule = {
            'BTC/USDT': True,
            'ETH/USDT': True,
            'BNB/USDT': True,
            'SOL/USDT': True,
            'ADA/USDT': True
        }

    async def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics."""
        return {
            **self.metrics,
            "task_queue_size": len(self.task_queue),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "system_resources": self.system_resources,
            "is_running": self.is_running
        }

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        # Check running tasks
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            return {
                "task_id": task_id,
                "status": task.status.value,
                "symbol": task.symbol,
                "timeframe": task.timeframe.value,
                "priority": task.priority.value,
                "created_at": task.created_at,
                "retry_count": task.retry_count
            }

        # Check completed tasks
        if task_id in self.completed_tasks:
            task = self.completed_tasks[task_id]
            return {
                "task_id": task_id,
                "status": task.status.value,
                "symbol": task.symbol,
                "timeframe": task.timeframe.value,
                "priority": task.priority.value,
                "created_at": task.created_at,
                "completed_at": task.created_at + task.max_execution_time,
                "retry_count": task.retry_count,
                "has_result": task.result is not None
            }

        # Check pending tasks
        for task in self.task_queue:
            if task.id == task_id:
                return {
                    "task_id": task_id,
                    "status": task.status.value,
                    "symbol": task.symbol,
                    "timeframe": task.timeframe.value,
                    "priority": task.priority.value,
                    "created_at": task.created_at,
                    "scheduled_at": task.scheduled_at,
                    "retry_count": task.retry_count
                }

        return None

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health_status = {
            "status": "healthy",
            "components": {},
            "metrics": await self.get_metrics()
        }

        # Check task queue
        if len(self.task_queue) > self.config.max_pending_tasks * 0.9:
            health_status["status"] = "degraded"
            health_status["components"]["task_queue"] = {
                "status": "degraded",
                "reason": "queue nearly full"
            }

        # Check running tasks
        if len(self.running_tasks) >= self.config.max_concurrent_tasks:
            health_status["status"] = "degraded"
            health_status["components"]["task_execution"] = {
                "status": "degraded",
                "reason": "maximum concurrent tasks reached"
            }

        # Check background tasks
        active_background_tasks = [task for task in self.background_tasks if not task.done()]
        if len(active_background_tasks) < len(self.background_tasks):
            health_status["components"]["background_tasks"] = {
                "status": "degraded",
                "active": len(active_background_tasks),
                "total": len(self.background_tasks)
            }

        return health_status

    async def shutdown(self):
        """Shutdown the orchestrator."""
        await self.stop()