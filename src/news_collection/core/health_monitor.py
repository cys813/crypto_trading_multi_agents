import asyncio
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..models import ConnectionStatus, HealthMetrics, NewsSource
from .connection_manager import ConnectionManager


@dataclass
class HealthAlert:
    """Represents a health alert."""
    source_name: str
    alert_type: str
    message: str
    severity: str  # "low", "medium", "high", "critical"
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class HealthMonitor:
    """Monitors health of news source connections."""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.logger = logging.getLogger(__name__)
        self._alerts: List[HealthAlert] = []
        self._alert_callbacks: List[Callable[[HealthAlert], None]] = []
        self._health_history: Dict[str, List[ConnectionStatus]] = {}
        self._max_history_size = 1000
        self._monitoring_task: Optional[asyncio.Task] = None
        self._monitoring_interval = 30  # seconds

        # Thresholds
        self._response_time_threshold = 5000  # ms
        self._failure_threshold = 3  # consecutive failures
        self._uptime_threshold = 95.0  # percentage

    async def start_monitoring(self) -> None:
        """Start health monitoring."""
        if self._monitoring_task and not self._monitoring_task.done():
            return

        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Started health monitoring")

    async def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self.logger.info("Stopped health monitoring")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while True:
            try:
                await asyncio.sleep(self._monitoring_interval)
                await self._check_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitoring error: {str(e)}")

    async def _check_health(self) -> None:
        """Check health of all connections."""
        try:
            # Get current connection statuses
            statuses = await self.connection_manager.test_all_connections()

            for source_name, status in statuses.items():
                await self._process_connection_status(source_name, status)

        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")

    async def _process_connection_status(self, source_name: str, status: ConnectionStatus) -> None:
        """Process connection status and generate alerts if needed."""
        # Store in history
        if source_name not in self._health_history:
            self._health_history[source_name] = []

        self._health_history[source_name].append(status)

        # Limit history size
        if len(self._health_history[source_name]) > self._max_history_size:
            self._health_history[source_name] = self._health_history[source_name][-self._max_history_size:]

        # Check for alerts
        await self._check_alerts(source_name, status)

    async def _check_alerts(self, source_name: str, status: ConnectionStatus) -> None:
        """Check for alert conditions and generate alerts."""
        # Check for connection failure
        if not status.is_connected:
            await self._create_alert(
                source_name=source_name,
                alert_type="connection_failed",
                message=f"Connection failed: {status.error_message}",
                severity="critical" if status.consecutive_failures >= 3 else "high",
            )

        # Check for slow response time
        if status.response_time_ms > self._response_time_threshold:
            await self._create_alert(
                source_name=source_name,
                alert_type="slow_response",
                message=f"Slow response time: {status.response_time_ms:.2f}ms",
                severity="medium",
            )

        # Check for consecutive failures
        if status.consecutive_failures >= self._failure_threshold:
            await self._create_alert(
                source_name=source_name,
                alert_type="consecutive_failures",
                message=f"{status.consecutive_failures} consecutive failures",
                severity="high",
            )

        # Check for recovery
        if status.is_connected and status.consecutive_failures == 0:
            await self._resolve_alerts(source_name)

    async def _create_alert(
        self,
        source_name: str,
        alert_type: str,
        message: str,
        severity: str,
    ) -> None:
        """Create a new alert."""
        # Check if similar alert already exists and is unresolved
        existing_alert = self._find_similar_alert(source_name, alert_type)
        if existing_alert and not existing_alert.resolved:
            return  # Don't duplicate alerts

        alert = HealthAlert(
            source_name=source_name,
            alert_type=alert_type,
            message=message,
            severity=severity,
            timestamp=datetime.now(),
        )

        self._alerts.append(alert)
        self.logger.warning(f"Health alert: {severity.upper()} - {source_name} - {message}")

        # Notify callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback error: {str(e)}")

    def _find_similar_alert(self, source_name: str, alert_type: str) -> Optional[HealthAlert]:
        """Find similar unresolved alert."""
        for alert in reversed(self._alerts):
            if (alert.source_name == source_name and
                alert.alert_type == alert_type and
                not alert.resolved):
                return alert
        return None

    async def _resolve_alerts(self, source_name: str) -> None:
        """Resolve all unresolved alerts for a source."""
        for alert in self._alerts:
            if alert.source_name == source_name and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                self.logger.info(f"Resolved alert: {source_name} - {alert.alert_type}")

    def add_alert_callback(self, callback: Callable[[HealthAlert], None]) -> None:
        """Add a callback for health alerts."""
        self._alert_callbacks.append(callback)

    def remove_alert_callback(self, callback: Callable[[HealthAlert], None]) -> None:
        """Remove a callback for health alerts."""
        if callback in self._alert_callbacks:
            self._alert_callbacks.remove(callback)

    def get_active_alerts(self) -> List[HealthAlert]:
        """Get all active (unresolved) alerts."""
        return [alert for alert in self._alerts if not alert.resolved]

    def get_all_alerts(self) -> List[HealthAlert]:
        """Get all alerts, including resolved ones."""
        return self._alerts.copy()

    def get_alerts_for_source(self, source_name: str) -> List[HealthAlert]:
        """Get alerts for a specific source."""
        return [alert for alert in self._alerts if alert.source_name == source_name]

    async def get_health_summary(self) -> Dict[str, Dict[str, any]]:
        """Get health summary for all sources."""
        summary = {}
        statuses = await self.connection_manager.get_all_connection_statuses()

        for source_name, status in statuses.items():
            history = self._health_history.get(source_name, [])
            active_alerts = len(self.get_alerts_for_source(source_name))

            # Calculate uptime from history
            if history:
                uptime_percentage = sum(1 for s in history if s.is_connected) / len(history) * 100
            else:
                uptime_percentage = 100.0 if status.is_connected else 0.0

            # Calculate average response time
            if history:
                avg_response = sum(s.response_time_ms for s in history) / len(history)
            else:
                avg_response = status.response_time_ms

            summary[source_name] = {
                "is_connected": status.is_connected,
                "uptime_percentage": uptime_percentage,
                "average_response_time_ms": avg_response,
                "active_alerts": active_alerts,
                "consecutive_failures": status.consecutive_failures,
                "last_checked": status.last_checked.isoformat(),
            }

        return summary

    async def get_health_metrics(self) -> Dict[str, HealthMetrics]:
        """Get detailed health metrics for all sources."""
        return await self.connection_manager.get_health_metrics()

    def clear_alerts(self) -> None:
        """Clear all alerts."""
        self._alerts.clear()
        self.logger.info("Cleared all alerts")

    def clear_alerts_for_source(self, source_name: str) -> None:
        """Clear alerts for a specific source."""
        self._alerts = [alert for alert in self._alerts if alert.source_name != source_name]
        self.logger.info(f"Cleared alerts for {source_name}")

    def set_thresholds(
        self,
        response_time_threshold: Optional[int] = None,
        failure_threshold: Optional[int] = None,
        uptime_threshold: Optional[float] = None,
    ) -> None:
        """Set health monitoring thresholds."""
        if response_time_threshold is not None:
            self._response_time_threshold = response_time_threshold
        if failure_threshold is not None:
            self._failure_threshold = failure_threshold
        if uptime_threshold is not None:
            self._uptime_threshold = uptime_threshold

        self.logger.info(f"Updated thresholds: response_time={self._response_time_threshold}ms, "
                        f"failures={self._failure_threshold}, uptime={self._uptime_threshold}%")