"""
Metrics collection and monitoring utilities.

This module provides functionality for collecting and reporting metrics
for the data collection agent, including performance metrics and system health.
"""

import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import asyncio


@dataclass
class RequestMetrics:
    """Metrics for individual requests."""
    exchange: str
    method: str
    success: bool
    latency: float
    timestamp: datetime


@dataclass
class DataQualityMetrics:
    """Metrics for data quality."""
    exchange: str
    symbol: str
    data_type: str
    accuracy: float
    completeness: float
    timeliness: float
    timestamp: datetime


class MetricsCollector:
    """Collects and manages system metrics."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Request metrics
        self.request_metrics: List[RequestMetrics] = []
        self.request_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.latency_history = defaultdict(list)

        # Data quality metrics
        self.quality_metrics: List[DataQualityMetrics] = []
        self.quality_scores = defaultdict(list)

        # System metrics
        self.start_time = datetime.now()
        self.health_checks = defaultdict(dict)
        self.connection_pools = defaultdict(dict)

        # Performance thresholds
        self.latency_threshold = 100  # ms
        self.error_threshold = 0.05  # 5%
        self.quality_threshold = 0.99  # 99%

        # Cleanup task
        self._cleanup_task = None

    def record_request(self, exchange: str, method: str, success: bool, latency: float):
        """Record a request metric."""
        timestamp = datetime.now()
        metric = RequestMetrics(exchange, method, success, latency, timestamp)

        self.request_metrics.append(metric)
        self.request_counts[(exchange, method)] += 1

        if success:
            self.latency_history[(exchange, method)].append(latency)
        else:
            self.error_counts[(exchange, method)] += 1

        # Log slow requests
        if latency > self.latency_threshold:
            self.logger.warning(f"Slow request: {exchange}.{method} took {latency:.2f}ms")

        # Log errors
        if not success:
            self.logger.error(f"Failed request: {exchange}.{method}")

    def record_data_quality(self, exchange: str, symbol: str, data_type: str,
                          accuracy: float, completeness: float, timeliness: float):
        """Record data quality metrics."""
        timestamp = datetime.now()
        metric = DataQualityMetrics(exchange, symbol, data_type, accuracy, completeness, timeliness, timestamp)

        self.quality_metrics.append(metric)

        # Calculate overall quality score
        quality_score = (accuracy + completeness + timeliness) / 3
        self.quality_scores[(exchange, data_type)].append(quality_score)

        # Log low quality
        if quality_score < self.quality_threshold:
            self.logger.warning(f"Low data quality: {exchange}.{symbol}.{data_type} - {quality_score:.3f}")

    def record_health_check(self, exchange: str, status: str, latency: float, error: Optional[str] = None):
        """Record health check results."""
        self.health_checks[exchange] = {
            'timestamp': datetime.now(),
            'status': status,
            'latency': latency,
            'error': error
        }

    def record_connection_pool_status(self, exchange: str, available: int, total: int):
        """Record connection pool status."""
        self.connection_pools[exchange] = {
            'timestamp': datetime.now(),
            'available': available,
            'total': total,
            'utilization': (total - available) / total if total > 0 else 0
        }

    def get_request_metrics(self, exchange: Optional[str] = None, method: Optional[str] = None,
                          time_range: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get request metrics summary."""
        now = datetime.now()
        filtered_metrics = []

        for metric in self.request_metrics:
            # Filter by exchange
            if exchange and metric.exchange != exchange:
                continue

            # Filter by method
            if method and metric.method != method:
                continue

            # Filter by time range
            if time_range and (now - metric.timestamp) > time_range:
                continue

            filtered_metrics.append(metric)

        if not filtered_metrics:
            return {
                'total_requests': 0,
                'success_rate': 0,
                'avg_latency': 0,
                'error_rate': 0
            }

        # Calculate metrics
        total_requests = len(filtered_metrics)
        successful_requests = sum(1 for m in filtered_metrics if m.success)
        success_rate = successful_requests / total_requests if total_requests > 0 else 0

        latencies = [m.latency for m in filtered_metrics if m.success]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        error_rate = 1 - success_rate

        return {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'success_rate': success_rate,
            'avg_latency': avg_latency,
            'error_rate': error_rate,
            'min_latency': min(latencies) if latencies else 0,
            'max_latency': max(latencies) if latencies else 0
        }

    def get_data_quality_metrics(self, exchange: Optional[str] = None,
                               data_type: Optional[str] = None) -> Dict[str, Any]:
        """Get data quality metrics summary."""
        filtered_metrics = []

        for metric in self.quality_metrics:
            # Filter by exchange
            if exchange and metric.exchange != exchange:
                continue

            # Filter by data type
            if data_type and metric.data_type != data_type:
                continue

            filtered_metrics.append(metric)

        if not filtered_metrics:
            return {
                'total_checks': 0,
                'avg_accuracy': 0,
                'avg_completeness': 0,
                'avg_timeliness': 0,
                'avg_quality_score': 0
            }

        # Calculate quality metrics
        total_checks = len(filtered_metrics)
        avg_accuracy = sum(m.accuracy for m in filtered_metrics) / total_checks
        avg_completeness = sum(m.completeness for m in filtered_metrics) / total_checks
        avg_timeliness = sum(m.timeliness for m in filtered_metrics) / total_checks
        avg_quality_score = (avg_accuracy + avg_completeness + avg_timeliness) / 3

        return {
            'total_checks': total_checks,
            'avg_accuracy': avg_accuracy,
            'avg_completeness': avg_completeness,
            'avg_timeliness': avg_timeliness,
            'avg_quality_score': avg_quality_score,
            'min_quality_score': min(
                (m.accuracy + m.completeness + m.timeliness) / 3 for m in filtered_metrics
            ),
            'max_quality_score': max(
                (m.accuracy + m.completeness + m.timeliness) / 3 for m in filtered_metrics
            )
        }

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get overall system metrics."""
        uptime = datetime.now() - self.start_time

        # Calculate overall health
        healthy_exchanges = sum(1 for check in self.health_checks.values()
                               if check.get('status') == 'healthy')
        total_exchanges = len(self.health_checks)

        overall_health = healthy_exchanges / total_exchanges if total_exchanges > 0 else 0

        # Get connection pool utilization
        pool_utilization = {}
        for exchange, pool_data in self.connection_pools.items():
            pool_utilization[exchange] = pool_data.get('utilization', 0)

        avg_pool_utilization = sum(pool_utilization.values()) / len(pool_utilization) if pool_utilization else 0

        return {
            'uptime_seconds': uptime.total_seconds(),
            'start_time': self.start_time.isoformat(),
            'overall_health': overall_health,
            'healthy_exchanges': healthy_exchanges,
            'total_exchanges': total_exchanges,
            'avg_pool_utilization': avg_pool_utilization,
            'pool_utilization': pool_utilization,
            'latest_health_checks': {
                exchange: {
                    'status': check.get('status'),
                    'latency': check.get('latency'),
                    'timestamp': check.get('timestamp').isoformat() if check.get('timestamp') else None
                }
                for exchange, check in self.health_checks.items()
            }
        }

    def get_top_errors(self, limit: int = 10) -> List[Dict]:
        """Get top error occurrences."""
        error_counts = defaultdict(int)

        for metric in self.request_metrics:
            if not metric.success:
                key = f"{metric.exchange}.{metric.method}"
                error_counts[key] += 1

        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"method": method, "count": count} for method, count in sorted_errors[:limit]]

    def get_slowest_endpoints(self, limit: int = 10) -> List[Dict]:
        """Get slowest endpoints by average latency."""
        latency_stats = defaultdict(list)

        for metric in self.request_metrics:
            if metric.success:
                key = f"{metric.exchange}.{metric.method}"
                latency_stats[key].append(metric.latency)

        avg_latencies = []
        for endpoint, latencies in latency_stats.items():
            avg_latencies.append({
                'endpoint': endpoint,
                'avg_latency': sum(latencies) / len(latencies),
                'count': len(latencies)
            })

        return sorted(avg_latencies, key=lambda x: x['avg_latency'], reverse=True)[:limit]

    async def start_cleanup_task(self):
        """Start background cleanup task."""
        async def cleanup():
            while True:
                try:
                    # Clean up old metrics (keep last 24 hours)
                    cutoff_time = datetime.now() - timedelta(hours=24)

                    # Clean request metrics
                    self.request_metrics = [
                        m for m in self.request_metrics
                        if m.timestamp > cutoff_time
                    ]

                    # Clean quality metrics
                    self.quality_metrics = [
                        m for m in self.quality_metrics
                        if m.timestamp > cutoff_time
                    ]

                    # Clean latency history (keep last 1000 entries per endpoint)
                    for key in self.latency_history:
                        self.latency_history[key] = self.latency_history[key][-1000:]

                    # Clean quality scores (keep last 1000 entries per endpoint)
                    for key in self.quality_scores:
                        self.quality_scores[key] = self.quality_scores[key][-1000:]

                    await asyncio.sleep(3600)  # Cleanup every hour

                except Exception as e:
                    self.logger.error(f"Metrics cleanup error: {e}")
                    await asyncio.sleep(300)  # Wait before retrying

        self._cleanup_task = asyncio.create_task(cleanup())

    async def stop_cleanup_task(self):
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    def export_metrics(self, format_type: str = 'json') -> str:
        """Export metrics in specified format."""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'request_metrics': self.get_request_metrics(),
            'data_quality_metrics': self.get_data_quality_metrics(),
            'system_metrics': self.get_system_metrics(),
            'top_errors': self.get_top_errors(),
            'slowest_endpoints': self.get_slowest_endpoints()
        }

        if format_type == 'json':
            import json
            return json.dumps(metrics, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format_type}")