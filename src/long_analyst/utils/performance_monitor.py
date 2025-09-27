"""
Performance monitoring for the Long Analyst Agent.

Provides comprehensive performance tracking, metrics collection,
and real-time monitoring capabilities.
"""

import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import json


@dataclass
class MetricData:
    """Single metric data point."""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricAggregation:
    """Aggregated metric data."""
    name: str
    count: int
    sum: float
    min: float
    max: float
    avg: float
    last_updated: float
    tags: Dict[str, str] = field(default_factory=dict)


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system.

    Tracks system metrics, performance indicators, and provides
    real-time monitoring capabilities.
    """

    def __init__(self, max_metrics_history: int = 10000, aggregation_window: int = 60):
        """Initialize the performance monitor."""
        self.logger = logging.getLogger(__name__)
        self.max_metrics_history = max_metrics_history
        self.aggregation_window = aggregation_window

        # Metrics storage
        self.metrics_history: deque = deque(maxlen=max_metrics_history)
        self.aggregated_metrics: Dict[str, MetricAggregation] = {}
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}

        # Performance tracking
        self.start_time = time.time()
        self.last_metrics_update = time.time()
        self.metrics_update_interval = 30  # seconds

        # Thread safety
        self._lock = threading.RLock()

        # Alert thresholds
        self.alert_thresholds: Dict[str, Dict[str, float]] = {
            "processing_time": {"warning": 1000, "critical": 2000},  # milliseconds
            "error_rate": {"warning": 0.1, "critical": 0.2},  # percentage
            "memory_usage": {"warning": 80, "critical": 90},  # percentage
            "cpu_usage": {"warning": 80, "critical": 90},  # percentage
        }

        self.logger.info("Performance monitor initialized")

    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None,
                     metadata: Optional[Dict[str, Any]] = None):
        """
        Record a metric value.

        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags for categorization
            metadata: Additional metadata
        """
        try:
            with self._lock:
                timestamp = time.time()
                metric = MetricData(
                    name=name,
                    value=value,
                    timestamp=timestamp,
                    tags=tags or {},
                    metadata=metadata or {}
                )

                # Add to history
                self.metrics_history.append(metric)

                # Update aggregation
                self._update_aggregation(metric)

                # Update counters and gauges
                if name.endswith("_count"):
                    self.counters[name] = int(value)
                else:
                    self.gauges[name] = value

        except Exception as e:
            self.logger.error(f"Error recording metric {name}: {e}")

    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """
        Increment a counter metric.

        Args:
            name: Counter name
            value: Increment value
            tags: Optional tags
        """
        with self._lock:
            counter_key = f"{name}_count"
            self.counters[counter_key] += value
            self.record_metric(counter_key, float(self.counters[counter_key]), tags)

    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Set a gauge metric.

        Args:
            name: Gauge name
            value: Gauge value
            tags: Optional tags
        """
        with self._lock:
            self.gauges[name] = value
            self.record_metric(name, value, tags)

    def time_function(self, metric_name: str):
        """
        Decorator to time function execution.

        Args:
            metric_name: Name for the timing metric
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                    self.record_metric(f"{metric_name}_time", execution_time)
                    return result
                except Exception as e:
                    execution_time = (time.time() - start_time) * 1000
                    self.record_metric(f"{metric_name}_time", execution_time)
                    self.increment_counter(f"{metric_name}_errors")
                    raise
            return wrapper
        return decorator

    def _update_aggregation(self, metric: MetricData):
        """Update aggregated metrics."""
        key = f"{metric.name}_{json.dumps(metric.tags, sort_keys=True)}"

        if key not in self.aggregated_metrics:
            self.aggregated_metrics[key] = MetricAggregation(
                name=metric.name,
                count=0,
                sum=0.0,
                min=float('inf'),
                max=float('-inf'),
                avg=0.0,
                last_updated=metric.timestamp,
                tags=metric.tags
            )

        agg = self.aggregated_metrics[key]
        agg.count += 1
        agg.sum += metric.value
        agg.min = min(agg.min, metric.value)
        agg.max = max(agg.max, metric.value)
        agg.avg = agg.sum / agg.count
        agg.last_updated = metric.timestamp

    def get_metric_value(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[float]:
        """
        Get current metric value.

        Args:
            name: Metric name
            tags: Optional tags

        Returns:
            Current metric value or None if not found
        """
        with self._lock:
            # Check gauges first
            if name in self.gauges:
                return self.gauges[name]

            # Check aggregated metrics
            key = f"{name}_{json.dumps(tags or {}, sort_keys=True)}"
            if key in self.aggregated_metrics:
                return self.aggregated_metrics[key].avg

            # Check recent metrics
            recent_metrics = [m for m in self.metrics_history if m.name == name]
            if recent_metrics:
                return recent_metrics[-1].value

            return None

    def get_metric_history(self, name: str, since: Optional[float] = None,
                          limit: int = 100) -> List[MetricData]:
        """
        Get metric history.

        Args:
            name: Metric name
            since: Optional timestamp to start from
            limit: Maximum number of data points

        Returns:
            List of metric data points
        """
        with self._lock:
            history = [m for m in self.metrics_history if m.name == name]

            if since:
                history = [m for m in history if m.timestamp >= since]

            history.sort(key=lambda x: x.timestamp, reverse=True)
            return history[:limit]

    def get_aggregated_metrics(self, since: Optional[float] = None) -> Dict[str, MetricAggregation]:
        """
        Get all aggregated metrics.

        Args:
            since: Optional timestamp to filter by

        Returns:
            Dictionary of aggregated metrics
        """
        with self._lock:
            if since:
                return {
                    key: agg for key, agg in self.aggregated_metrics.items()
                    if agg.last_updated >= since
                }
            return self.aggregated_metrics.copy()

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        with self._lock:
            uptime = time.time() - self.start_time
            metrics_count = len(self.metrics_history)
            aggregated_count = len(self.aggregated_metrics)

            return {
                "uptime_seconds": uptime,
                "metrics_recorded": metrics_count,
                "aggregated_metrics": aggregated_count,
                "active_counters": len(self.counters),
                "active_gauges": len(self.gauges),
                "last_update": self.last_metrics_update,
                "timestamp": time.time()
            }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary with key metrics."""
        with self._lock:
            summary = {
                "system_metrics": self.get_current_metrics(),
                "key_performance_indicators": {},
                "alerts": self._check_alerts(),
                "top_metrics": {}
            }

            # Calculate key performance indicators
            if "event_processing_time" in self.gauges:
                summary["key_performance_indicators"]["avg_processing_time"] = self.gauges["event_processing_time"]

            if "events_handled" in self.counters:
                events_handled = self.counters["events_handled"]
                uptime = time.time() - self.start_time
                events_per_second = events_handled / uptime if uptime > 0 else 0
                summary["key_performance_indicators"]["events_per_second"] = events_per_second

            if "llm_analysis_time" in self.gauges:
                summary["key_performance_indicators"]["avg_llm_analysis_time"] = self.gauges["llm_analysis_time"]

            # Get top metrics by frequency
            metric_counts = defaultdict(int)
            for metric in self.metrics_history:
                metric_counts[metric.name] += 1

            top_metrics = sorted(metric_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            summary["top_metrics"] = dict(top_metrics)

            return summary

    def _check_alerts(self) -> List[Dict[str, Any]]:
        """Check for alert conditions."""
        alerts = []
        current_time = time.time()

        with self._lock:
            for metric_name, thresholds in self.alert_thresholds.items():
                value = self.get_metric_value(metric_name)

                if value is None:
                    continue

                if value >= thresholds["critical"]:
                    alerts.append({
                        "level": "critical",
                        "metric": metric_name,
                        "value": value,
                        "threshold": thresholds["critical"],
                        "timestamp": current_time,
                        "message": f"Critical: {metric_name} is {value:.2f} (threshold: {thresholds['critical']})"
                    })
                elif value >= thresholds["warning"]:
                    alerts.append({
                        "level": "warning",
                        "metric": metric_name,
                        "value": value,
                        "threshold": thresholds["warning"],
                        "timestamp": current_time,
                        "message": f"Warning: {metric_name} is {value:.2f} (threshold: {thresholds['warning']})"
                    })

        return alerts

    def get_error_rate(self) -> float:
        """Calculate overall error rate."""
        with self._lock:
            total_events = self.counters.get("events_handled", 0)
            error_events = self.counters.get("error_events", 0)

            if total_events == 0:
                return 0.0

            return error_events / total_events

    def export_metrics(self, format: str = "json") -> str:
        """
        Export metrics data.

        Args:
            format: Export format ("json" or "csv")

        Returns:
            Exported metrics data
        """
        if format.lower() == "json":
            return self._export_json()
        elif format.lower() == "csv":
            return self._export_csv()
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_json(self) -> str:
        """Export metrics as JSON."""
        data = {
            "export_timestamp": time.time(),
            "system_metrics": self.get_current_metrics(),
            "aggregated_metrics": {
                key: {
                    "name": agg.name,
                    "count": agg.count,
                    "sum": agg.sum,
                    "min": agg.min,
                    "max": agg.max,
                    "avg": agg.avg,
                    "last_updated": agg.last_updated,
                    "tags": agg.tags
                }
                for key, agg in self.aggregated_metrics.items()
            },
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "alerts": self._check_alerts()
        }

        return json.dumps(data, indent=2)

    def _export_csv(self) -> str:
        """Export metrics as CSV."""
        if not self.metrics_history:
            return "timestamp,name,value,tags,metadata"

        lines = ["timestamp,name,value,tags,metadata"]
        for metric in self.metrics_history:
            line = f"{metric.timestamp},{metric.name},{metric.value},\"{json.dumps(metric.tags)}\",\"{json.dumps(metric.metadata)}\""
            lines.append(line)

        return "\n".join(lines)

    def reset_metrics(self):
        """Reset all metrics and counters."""
        with self._lock:
            self.metrics_history.clear()
            self.aggregated_metrics.clear()
            self.counters.clear()
            self.gauges.clear()
            self.start_time = time.time()
            self.last_metrics_update = time.time()

        self.logger.info("Performance metrics reset")

    def cleanup_old_metrics(self, max_age: float = 3600):
        """
        Clean up old metrics data.

        Args:
            max_age: Maximum age of metrics to keep (in seconds)
        """
        with self._lock:
            cutoff_time = time.time() - max_age

            # Remove old metrics from history
            self.metrics_history = deque(
                [m for m in self.metrics_history if m.timestamp >= cutoff_time],
                maxlen=self.max_metrics_history
            )

            # Remove old aggregated metrics
            self.aggregated_metrics = {
                key: agg for key, agg in self.aggregated_metrics.items()
                if agg.last_updated >= cutoff_time
            }

        self.logger.debug(f"Cleaned up metrics older than {max_age} seconds")

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on performance monitor."""
        current_metrics = self.get_current_metrics()
        alerts = self._check_alerts()

        health_status = {
            "status": "healthy",
            "metrics": current_metrics,
            "alerts_count": len(alerts),
            "oldest_metric_age": 0,
            "storage_usage": {
                "history_usage": len(self.metrics_history) / self.max_metrics_history,
                "aggregations_count": len(self.aggregated_metrics)
            }
        }

        # Check storage usage
        if len(self.metrics_history) / self.max_metrics_history > 0.9:
            health_status["status"] = "warning"

        # Check for critical alerts
        if any(alert["level"] == "critical" for alert in alerts):
            health_status["status"] = "degraded"

        # Check oldest metric age
        if self.metrics_history:
            oldest_metric = min(self.metrics_history, key=lambda x: x.timestamp)
            health_status["oldest_metric_age"] = time.time() - oldest_metric.timestamp

            if health_status["oldest_metric_age"] > 3600:  # 1 hour
                health_status["status"] = "warning"

        return health_status

    def __str__(self) -> str:
        """String representation."""
        metrics_count = len(self.metrics_history)
        uptime = time.time() - self.start_time
        return f"PerformanceMonitor(metrics={metrics_count}, uptime={uptime:.1f}s)"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"PerformanceMonitor(metrics={len(self.metrics_history)}, "
                f"aggregations={len(self.aggregated_metrics)}, "
                f"counters={len(self.counters)}, gauges={len(self.gauges)})")