"""
Performance optimization utilities for data collection.

This module provides performance monitoring, caching strategies,
and optimization techniques for high-frequency data collection.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics

from ..config.settings import get_settings


@dataclass
class PerformanceMetrics:
    """Performance metrics for data collection operations."""
    operation: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    data_points: int = 0
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None


@dataclass
class CacheStats:
    """Cache performance statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size: int = 0
    hit_rate: float = 0.0

    def update_hit_rate(self):
        """Calculate hit rate."""
        total_requests = self.hits + self.misses
        self.hit_rate = self.hits / total_requests if total_requests > 0 else 0.0


class PerformanceMonitor:
    """Monitor and analyze performance of data collection operations."""

    def __init__(self, max_samples: int = 1000):
        self.logger = logging.getLogger(__name__)
        self.max_samples = max_samples

        # Performance metrics storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_samples))
        self.cache_stats = CacheStats()

        # Performance thresholds
        self.thresholds = {
            'warning_duration': 5.0,  # seconds
            'critical_duration': 10.0,  # seconds
            'warning_memory': 100 * 1024 * 1024,  # 100MB
            'critical_memory': 500 * 1024 * 1024,  # 500MB
            'warning_cpu': 80.0,  # percentage
            'critical_cpu': 95.0  # percentage
        }

        # Real-time performance tracking
        self.active_operations = {}
        self.performance_alerts = deque(maxlen=100)

    def start_operation(self, operation: str, data_points: int = 0) -> str:
        """Start tracking an operation."""
        operation_id = f"{operation}_{time.time()}_{id(asyncio.current_task())}"
        self.active_operations[operation_id] = PerformanceMetrics(
            operation=operation,
            start_time=time.time(),
            data_points=data_points
        )
        return operation_id

    def end_operation(self, operation_id: str, success: bool = True, error_message: Optional[str] = None):
        """End tracking an operation."""
        if operation_id not in self.active_operations:
            return

        metrics = self.active_operations[operation_id]
        metrics.end_time = time.time()
        metrics.duration = metrics.end_time - metrics.start_time
        metrics.success = success
        metrics.error_message = error_message

        # Store metrics
        self.metrics[metrics.operation].append(metrics)

        # Remove from active operations
        del self.active_operations[operation_id]

        # Check performance thresholds
        self._check_performance_thresholds(metrics)

        return metrics

    def _check_performance_thresholds(self, metrics: PerformanceMetrics):
        """Check if metrics exceed performance thresholds."""
        if metrics.duration > self.thresholds['critical_duration']:
            self._add_performance_alert(
                'critical', f'Critical duration for {metrics.operation}: {metrics.duration:.2f}s',
                metrics
            )
        elif metrics.duration > self.thresholds['warning_duration']:
            self._add_performance_alert(
                'warning', f'Warning duration for {metrics.operation}: {metrics.duration:.2f}s',
                metrics
            )

    def _add_performance_alert(self, severity: str, message: str, metrics: PerformanceMetrics):
        """Add a performance alert."""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'severity': severity,
            'message': message,
            'operation': metrics.operation,
            'duration': metrics.duration,
            'success': metrics.success
        }

        self.performance_alerts.append(alert)

        if severity == 'critical':
            self.logger.critical(f"Performance Alert: {message}")
        else:
            self.logger.warning(f"Performance Alert: {message}")

    def get_operation_stats(self, operation: str) -> Dict[str, Any]:
        """Get statistics for a specific operation."""
        if operation not in self.metrics or not self.metrics[operation]:
            return {}

        metrics_list = list(self.metrics[operation])
        durations = [m.duration for m in metrics_list if m.duration]
        success_rate = sum(1 for m in metrics_list if m.success) / len(metrics_list)

        return {
            'total_operations': len(metrics_list),
            'success_rate': success_rate,
            'avg_duration': statistics.mean(durations) if durations else 0,
            'min_duration': min(durations) if durations else 0,
            'max_duration': max(durations) if durations else 0,
            'p95_duration': statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else 0,
            'total_data_points': sum(m.data_points for m in metrics_list),
            'avg_data_points_per_operation': sum(m.data_points for m in metrics_list) / len(metrics_list)
        }

    def get_system_performance(self) -> Dict[str, Any]:
        """Get overall system performance."""
        all_metrics = []
        for metrics_queue in self.metrics.values():
            all_metrics.extend(list(metrics_queue))

        if not all_metrics:
            return {}

        total_operations = len(all_metrics)
        successful_operations = sum(1 for m in all_metrics if m.success)
        success_rate = successful_operations / total_operations if total_operations > 0 else 0

        durations = [m.duration for m in all_metrics if m.duration]

        return {
            'total_operations': total_operations,
            'success_rate': success_rate,
            'avg_duration': statistics.mean(durations) if durations else 0,
            'active_operations': len(self.active_operations),
            'cache_hit_rate': self.cache_stats.hit_rate,
            'recent_alerts': list(self.performance_alerts)[-10:],
            'performance_by_operation': {
                op: self.get_operation_stats(op) for op in self.metrics.keys()
            }
        }

    def get_performance_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent performance alerts."""
        return list(self.performance_alerts)[-limit:]

    def record_cache_hit(self):
        """Record a cache hit."""
        self.cache_stats.hits += 1
        self.cache_stats.update_hit_rate()

    def record_cache_miss(self):
        """Record a cache miss."""
        self.cache_stats.misses += 1
        self.cache_stats.update_hit_rate()

    def record_cache_eviction(self):
        """Record a cache eviction."""
        self.cache_stats.evictions += 1

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'hits': self.cache_stats.hits,
            'misses': self.cache_stats.misses,
            'evictions': self.cache_stats.evictions,
            'hit_rate': self.cache_stats.hit_rate,
            'total_requests': self.cache_stats.hits + self.cache_stats.misses
        }


class CircuitBreaker:
    """Circuit breaker for preventing cascade failures."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
        self.logger = logging.getLogger(__name__)

    async def call(self, operation: Callable, *args, **kwargs):
        """Execute operation with circuit breaker protection."""
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half-open'
                self.logger.info("Circuit breaker attempting reset")
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = await operation(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self.last_failure_time is None:
            return True

        return (datetime.now() - self.last_failure_time).total_seconds() >= self.recovery_timeout

    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = 'closed'

    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state."""
        return {
            'state': self.state,
            'failure_count': self.failure_count,
            'failure_threshold': self.failure_threshold,
            'recovery_timeout': self.recovery_timeout,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class RateLimiter:
    """Rate limiter for controlling request frequency."""

    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.logger = logging.getLogger(__name__)

    async def acquire(self) -> bool:
        """Acquire permission to make a request."""
        now = time.time()

        # Remove old requests
        while self.requests and self.requests[0] <= now - self.time_window:
            self.requests.popleft()

        # Check if we can make a new request
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True

        return False

    async def wait_for_permission(self, timeout: Optional[float] = None) -> bool:
        """Wait for permission to make a request."""
        start_time = time.time()

        while True:
            if await self.acquire():
                return True

            if timeout and (time.time() - start_time) > timeout:
                return False

            await asyncio.sleep(0.1)

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        now = time.time()
        recent_requests = sum(1 for req_time in self.requests if req_time > now - self.time_window)

        return {
            'max_requests': self.max_requests,
            'time_window': self.time_window,
            'current_requests': recent_requests,
            'remaining_requests': max(0, self.max_requests - recent_requests),
            'utilization': recent_requests / self.max_requests
        }


class ConnectionPool:
    """Connection pool for efficient resource management."""

    def __init__(self, factory: Callable, min_size: int = 1, max_size: int = 10):
        self.factory = factory
        self.min_size = min_size
        self.max_size = max_size
        self.pool = deque()
        self.active_connections = set()
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """Initialize connection pool."""
        async with self.lock:
            for _ in range(self.min_size):
                connection = await self.factory()
                self.pool.append(connection)

    async def get_connection(self):
        """Get a connection from the pool."""
        async with self.lock:
            if self.pool:
                connection = self.pool.popleft()
                self.active_connections.add(connection)
                return connection

            # Create new connection if under max size
            if len(self.active_connections) < self.max_size:
                connection = await self.factory()
                self.active_connections.add(connection)
                return connection

            # Wait for a connection to be returned
            raise Exception("No available connections in pool")

    async def return_connection(self, connection):
        """Return a connection to the pool."""
        async with self.lock:
            if connection in self.active_connections:
                self.active_connections.remove(connection)
                self.pool.append(connection)

    async def close_all(self):
        """Close all connections."""
        async with self.lock:
            all_connections = list(self.pool) + list(self.active_connections)
            self.pool.clear()
            self.active_connections.clear()

            for connection in all_connections:
                try:
                    if hasattr(connection, 'close'):
                        await connection.close()
                    elif hasattr(connection, 'cleanup'):
                        await connection.cleanup()
                except Exception as e:
                    self.logger.error(f"Error closing connection: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return {
            'pool_size': len(self.pool),
            'active_connections': len(self.active_connections),
            'total_connections': len(self.pool) + len(self.active_connections),
            'min_size': self.min_size,
            'max_size': self.max_size,
            'utilization': len(self.active_connections) / self.max_size if self.max_size > 0 else 0
        }


class BatchProcessor:
    """Batch processor for efficient bulk operations."""

    def __init__(self, batch_size: int = 100, max_wait_time: float = 5.0):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.batch = []
        self.last_flush_time = time.time()
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger(__name__)

    async def add_item(self, item: Any, processor: Callable):
        """Add item to batch."""
        async with self.lock:
            self.batch.append(item)

            # Check if batch is ready to process
            if (len(self.batch) >= self.batch_size or
                    time.time() - self.last_flush_time >= self.max_wait_time):
                await self._flush_batch(processor)

    async def _flush_batch(self, processor: Callable):
        """Flush and process current batch."""
        if not self.batch:
            return

        current_batch = self.batch.copy()
        self.batch.clear()
        self.last_flush_time = time.time()

        try:
            await processor(current_batch)
        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            raise

    async def force_flush(self, processor: Callable):
        """Force flush remaining items."""
        async with self.lock:
            await self._flush_batch(processor)

    def get_stats(self) -> Dict[str, Any]:
        """Get batch processor statistics."""
        return {
            'current_batch_size': len(self.batch),
            'batch_size': self.batch_size,
            'max_wait_time': self.max_wait_time,
            'time_since_last_flush': time.time() - self.last_flush_time
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(operation_name: str):
    """Decorator to monitor performance of async functions."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            operation_id = performance_monitor.start_operation(operation_name)
            try:
                result = await func(*args, **kwargs)
                performance_monitor.end_operation(operation_id, success=True)
                return result
            except Exception as e:
                performance_monitor.end_operation(operation_id, success=False, error_message=str(e))
                raise
        return wrapper
    return decorator


async def optimize_memory_usage():
    """Optimize memory usage by cleaning up unused resources."""
    # This would typically involve:
    # - Cleaning up old cached data
    # - Closing unused connections
    # - Garbage collection
    # - Memory pool optimization
    pass


async def get_system_resources() -> Dict[str, Any]:
    """Get current system resource usage."""
    try:
        import psutil
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_available': psutil.virtual_memory().available,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else None
        }
    except ImportError:
        return {
            'cpu_percent': 0,
            'memory_percent': 0,
            'memory_available': 0,
            'disk_usage': 0,
            'network_io': None,
            'error': 'psutil not available'
        }