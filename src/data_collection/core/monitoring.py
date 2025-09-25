"""
Prometheus monitoring integration for the data collection agent.

This module provides:
- Comprehensive metrics collection
- Prometheus endpoint exposure
- System health monitoring
- Business metrics tracking
- Performance monitoring
- Alert threshold management
"""

import time
import threading
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, deque
import json
import logging
from pathlib import Path

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, CollectorRegistry, generate_latest,
        start_http_server, multiprocess, Info
    )
    from prometheus_client.exposition import make_asgi_app
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("Prometheus client not available. Metrics will be disabled.")

import psutil
import async_timeout

from .config import get_config
from .logger import get_logger
from .exceptions import error_handler


@dataclass
class MetricDefinition:
    """Definition for custom metrics."""
    name: str
    type: str  # counter, gauge, histogram
    description: str
    labels: List[str]
    buckets: Optional[List[float]] = None


class SystemMetricsCollector:
    """Collects system-level metrics."""

    def __init__(self, collection_interval: int = 15):
        self.collection_interval = collection_interval
        self.logger = get_logger("system_metrics")
        self._running = False
        self._thread = None
        self._stop_event = threading.Event()
        self._metrics_history = defaultdict(lambda: deque(maxlen=1000))

    def start(self):
        """Start system metrics collection."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._collect_loop, daemon=True)
        self._thread.start()
        self.logger.info("System metrics collection started")

    def stop(self):
        """Stop system metrics collection."""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()
        self._thread.join(timeout=5)
        self.logger.info("System metrics collection stopped")

    def _collect_loop(self):
        """Main collection loop."""
        while self._running and not self._stop_event.wait(self.collection_interval):
            try:
                metrics = self._collect_system_metrics()
                self._store_metrics(metrics)
            except Exception as e:
                self.logger.error(f"Error collecting system metrics: {e}")

    def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg()

            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()

            # Network metrics
            network = psutil.net_io_counters()

            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()

            return {
                # CPU
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "load_avg_1m": load_avg[0],
                "load_avg_5m": load_avg[1],
                "load_avg_15m": load_avg[2],

                # Memory
                "memory_total": memory.total,
                "memory_available": memory.available,
                "memory_used": memory.used,
                "memory_percent": memory.percent,
                "swap_total": swap.total,
                "swap_used": swap.used,
                "swap_percent": swap.percent,

                # Disk
                "disk_total": disk.total,
                "disk_used": disk.used,
                "disk_free": disk.free,
                "disk_percent": disk.percent,

                # Disk I/O
                "disk_read_bytes": disk_io.read_bytes,
                "disk_write_bytes": disk_io.write_bytes,
                "disk_read_count": disk_io.read_count,
                "disk_write_count": disk_io.write_count,

                # Network
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "network_packets_sent": network.packets_sent,
                "network_packets_recv": network.packets_recv,

                # Process
                "process_memory_rss": process_memory.rss,
                "process_memory_vms": process_memory.vms,
                "process_cpu_percent": process_cpu,
                "process_threads": process.num_threads(),
                "process_handles": process.num_handles() if hasattr(process, 'num_handles') else 0
            }

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return {}

    def _store_metrics(self, metrics: Dict[str, float]):
        """Store metrics in history."""
        timestamp = time.time()
        for key, value in metrics.items():
            self._metrics_history[key].append((timestamp, value))

    def get_metrics_history(self, metric_name: str, duration: int = 3600) -> List[tuple]:
        """Get metrics history for the specified duration."""
        cutoff_time = time.time() - duration
        return [(ts, val) for ts, val in self._metrics_history[metric_name] if ts > cutoff_time]

    def get_current_metrics(self) -> Dict[str, float]:
        """Get current metrics values."""
        return self._collect_system_metrics()


class BusinessMetricsCollector:
    """Collects business-level metrics."""

    def __init__(self):
        self.logger = get_logger("business_metrics")
        self.collection_stats = defaultdict(int)
        self.quality_stats = defaultdict(list)
        self.exchange_stats = defaultdict(lambda: defaultdict(int))

    def record_data_collection(self, exchange: str, data_type: str, symbol: str,
                             success: bool, duration: float, data_points: int = 0):
        """Record data collection metrics."""
        key = f"{exchange}_{data_type}"
        self.collection_stats[f"{key}_total"] += 1
        self.collection_stats[f"{key}_duration"] += duration

        if success:
            self.collection_stats[f"{key}_success"] += 1
            if data_points > 0:
                self.quality_stats[f"{key}_throughput"].append(data_points / duration)
        else:
            self.collection_stats[f"{key}_failed"] += 1

        # Exchange-specific stats
        self.exchange_stats[exchange][f"{data_type}_total"] += 1
        if success:
            self.exchange_stats[exchange][f"{data_type}_success"] += 1
        else:
            self.exchange_stats[exchange][f"{data_type}_failed"] += 1

    def record_data_quality(self, exchange: str, data_type: str, symbol: str,
                          quality_score: float, accuracy: float, completeness: float, timeliness: float):
        """Record data quality metrics."""
        key = f"{exchange}_{data_type}_{symbol}"
        self.quality_stats[f"{key}_quality_score"].append(quality_score)
        self.quality_stats[f"{key}_accuracy"].append(accuracy)
        self.quality_stats[f"{key}_completeness"].append(completeness)
        self.quality_stats[f"{key}_timeliness"].append(timeliness)

    def record_api_request(self, endpoint: str, method: str, status_code: int, duration: float):
        """Record API request metrics."""
        key = f"{method}_{endpoint}"
        self.collection_stats[f"{key}_total"] += 1
        self.collection_stats[f"{key}_duration"] += duration

        if 200 <= status_code < 300:
            self.collection_stats[f"{key}_success"] += 1
        elif 400 <= status_code < 500:
            self.collection_stats[f"{key}_client_error"] += 1
        else:
            self.collection_stats[f"{key}_server_error"] += 1

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get data collection statistics."""
        stats = {}

        # Calculate success rates and average durations
        for key, total in self.collection_stats.items():
            if key.endswith('_total'):
                base_key = key[:-6]  # Remove '_total' suffix
                success = self.collection_stats.get(f"{base_key}_success", 0)
                failed = self.collection_stats.get(f"{base_key}_failed", 0)
                duration = self.collection_stats.get(f"{base_key}_duration", 0)

                stats[base_key] = {
                    "total": total,
                    "success": success,
                    "failed": failed,
                    "success_rate": success / total if total > 0 else 0,
                    "avg_duration": duration / total if total > 0 else 0
                }

        return stats

    def get_quality_stats(self) -> Dict[str, Any]:
        """Get data quality statistics."""
        stats = {}

        for key, values in self.quality_stats.items():
            if values:
                stats[key] = {
                    "count": len(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values)
                }

        return stats

    def get_exchange_stats(self) -> Dict[str, Any]:
        """Get exchange-specific statistics."""
        stats = {}

        for exchange, exchange_data in self.exchange_stats.items():
            stats[exchange] = {}
            for key, value in exchange_data.items():
                if key.endswith('_total'):
                    base_key = key[:-6]
                    success = exchange_data.get(f"{base_key}_success", 0)
                    failed = exchange_data.get(f"{base_key}_failed", 0)

                    stats[exchange][base_key] = {
                        "total": value,
                        "success": success,
                        "failed": failed,
                        "success_rate": success / value if value > 0 else 0
                    }

        return stats


class PrometheusMetrics:
    """Prometheus metrics collection and exposure."""

    def __init__(self):
        if not PROMETHEUS_AVAILABLE:
            self.logger = get_logger("prometheus")
            self.logger.warning("Prometheus client not available")
            return

        self.logger = get_logger("prometheus")
        self.registry = CollectorRegistry()
        self.config = get_config()

        # System metrics
        self.system_metrics = self._create_system_metrics()

        # Application metrics
        self.app_metrics = self._create_app_metrics()

        # Business metrics
        self.business_metrics = self._create_business_metrics()

        # Custom metrics registry
        self.custom_metrics = {}

        # Start metrics collection
        self.system_collector = SystemMetricsCollector()
        self.business_collector = BusinessMetricsCollector()

        self.logger.info("Prometheus metrics initialized")

    def _create_system_metrics(self) -> Dict[str, Any]:
        """Create system metrics."""
        return {
            'cpu_usage': Gauge(
                'system_cpu_usage_percent',
                'CPU usage percentage',
                registry=self.registry
            ),
            'memory_usage': Gauge(
                'system_memory_usage_bytes',
                'Memory usage in bytes',
                registry=self.registry
            ),
            'disk_usage': Gauge(
                'system_disk_usage_bytes',
                'Disk usage in bytes',
                registry=self.registry
            ),
            'load_average': Gauge(
                'system_load_average',
                'System load average',
                ['period'],
                registry=self.registry
            )
        }

    def _create_app_metrics(self) -> Dict[str, Any]:
        """Create application metrics."""
        return {
            'request_count': Counter(
                'app_requests_total',
                'Total number of requests',
                ['method', 'endpoint', 'status'],
                registry=self.registry
            ),
            'request_duration': Histogram(
                'app_request_duration_seconds',
                'Request duration in seconds',
                ['method', 'endpoint'],
                registry=self.registry
            ),
            'active_connections': Gauge(
                'app_active_connections',
                'Number of active connections',
                registry=self.registry
            ),
            'error_count': Counter(
                'app_errors_total',
                'Total number of errors',
                ['error_type', 'component'],
                registry=self.registry
            )
        }

    def _create_business_metrics(self) -> Dict[str, Any]:
        """Create business metrics."""
        return {
            'data_collection_count': Counter(
                'business_data_collection_total',
                'Total data collection operations',
                ['exchange', 'data_type', 'status'],
                registry=self.registry
            ),
            'data_collection_duration': Histogram(
                'business_data_collection_duration_seconds',
                'Data collection duration in seconds',
                ['exchange', 'data_type'],
                registry=self.registry
            ),
            'data_quality_score': Gauge(
                'business_data_quality_score',
                'Data quality score',
                ['exchange', 'data_type', 'symbol'],
                registry=self.registry
            ),
            'api_rate_limit_usage': Gauge(
                'business_api_rate_limit_usage',
                'API rate limit usage percentage',
                ['exchange'],
                registry=self.registry
            )
        }

    def start_collection(self):
        """Start metrics collection."""
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            # Start system metrics collection
            self.system_collector.start()

            # Start Prometheus server if enabled
            if self.config.monitoring.prometheus_enabled:
                self.start_prometheus_server()

            self.logger.info("Metrics collection started")

        except Exception as e:
            self.logger.error(f"Failed to start metrics collection: {e}")

    def stop_collection(self):
        """Stop metrics collection."""
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            self.system_collector.stop()
            self.logger.info("Metrics collection stopped")

        except Exception as e:
            self.logger.error(f"Failed to stop metrics collection: {e}")

    def start_prometheus_server(self):
        """Start Prometheus metrics server."""
        try:
            port = self.config.monitoring.prometheus_port
            start_http_server(port, registry=self.registry)
            self.logger.info(f"Prometheus server started on port {port}")

        except Exception as e:
            self.logger.error(f"Failed to start Prometheus server: {e}")

    def update_system_metrics(self):
        """Update system metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            metrics = self.system_collector.get_current_metrics()

            # Update Prometheus metrics
            if 'cpu_percent' in metrics:
                self.system_metrics['cpu_usage'].set(metrics['cpu_percent'])

            if 'memory_used' in metrics:
                self.system_metrics['memory_usage'].set(metrics['memory_used'])

            if 'disk_used' in metrics:
                self.system_metrics['disk_usage'].set(metrics['disk_used'])

            if 'load_avg_1m' in metrics:
                self.system_metrics['load_average'].labels(period='1m').set(metrics['load_avg_1m'])

            if 'load_avg_5m' in metrics:
                self.system_metrics['load_average'].labels(period='5m').set(metrics['load_avg_5m'])

            if 'load_avg_15m' in metrics:
                self.system_metrics['load_average'].labels(period='15m').set(metrics['load_avg_15m'])

        except Exception as e:
            self.logger.error(f"Failed to update system metrics: {e}")

    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record request metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            self.app_metrics['request_count'].labels(method=method, endpoint=endpoint, status=status).inc()
            self.app_metrics['request_duration'].labels(method=method, endpoint=endpoint).observe(duration)

            # Also record in business metrics collector
            self.business_collector.record_api_request(endpoint, method, status, duration)

        except Exception as e:
            self.logger.error(f"Failed to record request metrics: {e}")

    def record_data_collection(self, exchange: str, data_type: str, symbol: str,
                             success: bool, duration: float, data_points: int = 0):
        """Record data collection metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            status = 'success' if success else 'failed'
            self.business_metrics['data_collection_count'].labels(
                exchange=exchange, data_type=data_type, status=status
            ).inc()
            self.business_metrics['data_collection_duration'].labels(
                exchange=exchange, data_type=data_type
            ).observe(duration)

            # Also record in business metrics collector
            self.business_collector.record_data_collection(
                exchange, data_type, symbol, success, duration, data_points
            )

        except Exception as e:
            self.logger.error(f"Failed to record data collection metrics: {e}")

    def record_data_quality(self, exchange: str, data_type: str, symbol: str,
                          quality_score: float, accuracy: float, completeness: float, timeliness: float):
        """Record data quality metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            self.business_metrics['data_quality_score'].labels(
                exchange=exchange, data_type=data_type, symbol=symbol
            ).set(quality_score)

            # Also record in business metrics collector
            self.business_collector.record_data_quality(
                exchange, data_type, symbol, quality_score, accuracy, completeness, timeliness
            )

        except Exception as e:
            self.logger.error(f"Failed to record data quality metrics: {e}")

    def record_error(self, error_type: str, component: str):
        """Record error metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            self.app_metrics['error_count'].labels(error_type=error_type, component=component).inc()

        except Exception as e:
            self.logger.error(f"Failed to record error metrics: {e}")

    def add_custom_metric(self, definition: MetricDefinition):
        """Add custom metric definition."""
        if not PROMETHEUS_AVAILABLE:
            return

        try:
            if definition.type == 'counter':
                metric = Counter(
                    definition.name,
                    definition.description,
                    definition.labels,
                    registry=self.registry
                )
            elif definition.type == 'gauge':
                metric = Gauge(
                    definition.name,
                    definition.description,
                    definition.labels,
                    registry=self.registry
                )
            elif definition.type == 'histogram':
                metric = Histogram(
                    definition.name,
                    definition.description,
                    definition.labels,
                    buckets=definition.buckets,
                    registry=self.registry
                )
            else:
                raise ValueError(f"Unknown metric type: {definition.type}")

            self.custom_metrics[definition.name] = metric
            self.logger.info(f"Added custom metric: {definition.name}")

        except Exception as e:
            self.logger.error(f"Failed to add custom metric {definition.name}: {e}")

    def get_custom_metric(self, name: str):
        """Get custom metric by name."""
        return self.custom_metrics.get(name)

    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format."""
        if not PROMETHEUS_AVAILABLE:
            return "# Prometheus client not available"

        try:
            return generate_latest(self.registry).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Failed to generate metrics: {e}")
            return "# Error generating metrics"

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        try:
            return {
                "system_metrics": self.system_collector.get_current_metrics(),
                "business_stats": self.business_collector.get_collection_stats(),
                "quality_stats": self.business_collector.get_quality_stats(),
                "exchange_stats": self.business_collector.get_exchange_stats(),
                "error_stats": error_handler.get_error_stats(timedelta(minutes=30)),
                "top_errors": error_handler.get_top_errors(10),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to get dashboard data: {e}")
            return {"error": str(e)}

    def create_asgi_app(self):
        """Create ASGI app for metrics endpoint."""
        if not PROMETHEUS_AVAILABLE:
            async def metrics_app(scope, receive, send):
                await send({
                    'type': 'http.response.start',
                    'status': 503,
                    'headers': [[b'content-type', b'text/plain']],
                })
                await send({
                    'type': 'http.response.body',
                    'body': b'Prometheus client not available',
                })
            return metrics_app

        return make_asgi_app(registry=self.registry)


# Global metrics instance
metrics = PrometheusMetrics()


def get_metrics() -> PrometheusMetrics:
    """Get global metrics instance."""
    return metrics


def record_request(method: str, endpoint: str, status: int, duration: float):
    """Record request metrics globally."""
    metrics.record_request(method, endpoint, status, duration)


def record_data_collection(exchange: str, data_type: str, symbol: str,
                         success: bool, duration: float, data_points: int = 0):
    """Record data collection metrics globally."""
    metrics.record_data_collection(exchange, data_type, symbol, success, duration, data_points)


def record_data_quality(exchange: str, data_type: str, symbol: str,
                       quality_score: float, accuracy: float, completeness: float, timeliness: float):
    """Record data quality metrics globally."""
    metrics.record_data_quality(exchange, data_type, symbol, quality_score, accuracy, completeness, timeliness)


def record_error(error_type: str, component: str):
    """Record error metrics globally."""
    metrics.record_error(error_type, component)


def get_dashboard_data() -> Dict[str, Any]:
    """Get dashboard data globally."""
    return metrics.get_dashboard_data()


def start_metrics_collection():
    """Start metrics collection globally."""
    metrics.start_collection()


def stop_metrics_collection():
    """Stop metrics collection globally."""
    metrics.stop_collection()