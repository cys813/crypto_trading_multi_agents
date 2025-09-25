"""
Metrics collection for the data collection agent.
"""

import asyncio
import time
from typing import Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog

logger = structlog.get_logger("data_collection.metrics")


@dataclass
class MetricsData:
    """Container for metrics data."""
    timestamp: datetime
    exchange: str
    symbol: str
    metric_name: str
    value: float
    labels: Dict[str, str]


class MetricsCollector:
    """Collects and exposes metrics for the data collection agent."""

    def __init__(self, port: int = 9090):
        self.port = port
        self.is_running = False
        self.metrics_buffer: list = []
        self.buffer_size = 1000

        # Prometheus metrics
        self.data_collection_counter = Counter(
            'data_collection_total',
            'Total data collections',
            ['exchange', 'symbol', 'data_type', 'status']
        )

        self.collection_duration = Histogram(
            'data_collection_duration_seconds',
            'Time spent collecting data',
            ['exchange', 'symbol', 'data_type']
        )

        self.active_positions = Gauge(
            'active_positions_total',
            'Number of active positions',
            ['exchange']
        )

        self.api_requests_total = Counter(
            'api_requests_total',
            'Total API requests',
            ['exchange', 'method', 'status']
        )

        self.system_errors = Counter(
            'system_errors_total',
            'Total system errors',
            ['component', 'error_type']
        )

        self.data_quality_score = Gauge(
            'data_quality_score',
            'Data quality score (0-100)',
            ['exchange', 'symbol', 'data_type']
        )

    async def start(self):
        """Start the metrics collector."""
        if self.is_running:
            logger.warning("Metrics collector is already running")
            return

        try:
            # Start Prometheus HTTP server
            start_http_server(self.port)
            self.is_running = True
            logger.info(f"Metrics collector started on port {self.port}")

            # Start metrics flush task
            asyncio.create_task(self._flush_metrics())

        except Exception as e:
            logger.error(f"Failed to start metrics collector: {e}")

    async def stop(self):
        """Stop the metrics collector."""
        self.is_running = False
        logger.info("Metrics collector stopped")

    def record_data_collection(self, exchange: str, symbol: str, data_type: str,
                             duration: float, success: bool):
        """Record a data collection event."""
        status = 'success' if success else 'failed'
        self.data_collection_counter.labels(
            exchange=exchange,
            symbol=symbol,
            data_type=data_type,
            status=status
        ).inc()

        self.collection_duration.labels(
            exchange=exchange,
            symbol=symbol,
            data_type=data_type
        ).observe(duration)

    def record_position_update(self, exchange: str, position_count: int):
        """Record position update."""
        self.active_positions.labels(exchange=exchange).set(position_count)

    def record_api_request(self, exchange: str, method: str, status: str):
        """Record API request."""
        self.api_requests_total.labels(
            exchange=exchange,
            method=method,
            status=status
        ).inc()

    def record_error(self, component: str, error_type: str):
        """Record system error."""
        self.system_errors.labels(
            component=component,
            error_type=error_type
        ).inc()

    def update_data_quality(self, exchange: str, symbol: str, data_type: str, score: float):
        """Update data quality score."""
        self.data_quality_score.labels(
            exchange=exchange,
            symbol=symbol,
            data_type=data_type
        ).set(score)

    def add_custom_metric(self, metric_data: MetricsData):
        """Add custom metric to buffer."""
        self.metrics_buffer.append(metric_data)

        if len(self.metrics_buffer) >= self.buffer_size:
            self._flush_buffer()

    async def _flush_metrics(self):
        """Periodically flush metrics."""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Flush every 30 seconds
                self._flush_buffer()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error flushing metrics: {e}")

    def _flush_buffer(self):
        """Flush metrics buffer."""
        if not self.metrics_buffer:
            return

        try:
            # Here you would typically send metrics to your monitoring system
            # For now, we'll just clear the buffer
            logger.debug(f"Flushed {len(self.metrics_buffer)} metrics")
            self.metrics_buffer.clear()

        except Exception as e:
            logger.error(f"Error flushing metrics buffer: {e}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics."""
        # This would typically collect data from Prometheus
        return {
            'collector_running': self.is_running,
            'buffer_size': len(self.metrics_buffer),
            'port': self.port
        }