"""
Main monitoring manager for the long analyst agent
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid

from .models import (
    MonitoringConfig,
    SystemMetrics,
    PerformanceMetrics,
    QualityMetrics,
    HealthMetrics,
    BusinessMetrics,
    MonitoringReport,
    Alert,
    HealthStatus
)
from .metrics_collector import MetricsCollector
from .health_evaluator import HealthEvaluator
from .alert_manager import AlertManager
from .monitoring_dashboard import MonitoringDashboard

logger = logging.getLogger(__name__)


class MonitoringManager:
    """Main monitoring manager"""

    def __init__(self, config: MonitoringConfig = None):
        """
        Initialize monitoring manager

        Args:
            config: Monitoring configuration
        """
        self.config = config or MonitoringConfig()
        self.collectors = self._init_collectors()
        self.evaluators = self._init_evaluators()
        self.alert_manager = AlertManager(self.config)
        self.dashboard = MonitoringDashboard(self.config)

        # Background tasks
        self._collection_task = None
        self._health_check_task = None
        self._alert_check_task = None

        # Storage for metrics
        self.metrics_history = []
        self.active_alerts = []

        # Performance tracking
        self.start_time = datetime.now()
        self.collection_count = 0

    def _init_collectors(self) -> Dict[str, Any]:
        """Initialize metrics collectors"""
        return {
            'performance': MetricsCollector('performance', self.config),
            'quality': MetricsCollector('quality', self.config),
            'health': MetricsCollector('health', self.config),
            'business': MetricsCollector('business', self.config)
        }

    def _init_evaluators(self) -> Dict[str, Any]:
        """Initialize health evaluators"""
        return {
            'health': HealthEvaluator(self.config)
        }

    async def start(self):
        """Start monitoring system"""
        logger.info("Starting monitoring system")

        # Start background tasks
        self._collection_task = asyncio.create_task(self._collection_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._alert_check_task = asyncio.create_task(self._alert_check_loop())

        logger.info("Monitoring system started successfully")

    async def stop(self):
        """Stop monitoring system"""
        logger.info("Stopping monitoring system")

        # Cancel background tasks
        if self._collection_task:
            self._collection_task.cancel()
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._alert_check_task:
            self._alert_check_task.cancel()

        logger.info("Monitoring system stopped")

    async def _collection_loop(self):
        """Main metrics collection loop"""
        while True:
            try:
                await self.collect_metrics()
                await asyncio.sleep(self.config.collection_interval.total_seconds())
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(self.config.collection_interval.total_seconds())

    async def _health_check_loop(self):
        """Main health check loop"""
        while True:
            try:
                await self.evaluate_health()
                await asyncio.sleep(self.config.alert_check_interval.total_seconds())
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health evaluation: {e}")
                await asyncio.sleep(self.config.alert_check_interval.total_seconds())

    async def _alert_check_loop(self):
        """Main alert check loop"""
        while True:
            try:
                await self._check_alerts()
                await asyncio.sleep(self.config.alert_check_interval.total_seconds())
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert checking: {e}")
                await asyncio.sleep(self.config.alert_check_interval.total_seconds())

    async def collect_metrics(self) -> None:
        """
        Collect all system metrics

        Returns:
            None
        """
        start_time = datetime.now()

        try:
            # Collect metrics from all collectors
            performance_metrics = await self.collectors['performance'].collect_performance_metrics()
            quality_metrics = await self.collectors['quality'].collect_quality_metrics()
            health_metrics = await self.collectors['health'].collect_health_metrics()
            business_metrics = await self.collectors['business'].collect_business_metrics()

            # Create system metrics
            system_metrics = SystemMetrics(
                performance=performance_metrics,
                quality=quality_metrics,
                health=health_metrics,
                business=business_metrics,
                timestamp=datetime.now()
            )

            # Store metrics
            self._store_metrics(system_metrics)

            # Update dashboard
            await self.dashboard.update_metrics(system_metrics)

            # Update performance tracking
            self.collection_count += 1
            collection_time = (datetime.now() - start_time).total_seconds()
            if collection_time > self.config.collection_interval.total_seconds():
                logger.warning(f"Metrics collection took {collection_time:.2f}s, longer than interval")

            logger.debug(f"Collected metrics in {collection_time:.2f}s")

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            raise

    async def evaluate_health(self) -> HealthStatus:
        """
        Evaluate system health

        Returns:
            System health status
        """
        try:
            if not self.metrics_history:
                logger.warning("No metrics history available for health evaluation")
                return HealthStatus.HEALTHY

            # Get latest metrics
            latest_metrics = self.metrics_history[-1]

            # Evaluate health
            health_status = await self.evaluators['health'].evaluate_system_health(latest_metrics)

            # Update dashboard
            await self.dashboard.update_health_status(health_status)

            logger.debug(f"System health status: {health_status}")

            return health_status

        except Exception as e:
            logger.error(f"Error evaluating health: {e}")
            return HealthStatus.UNHEALTHY

    async def _check_alerts(self):
        """Check for alert conditions"""
        try:
            if not self.metrics_history:
                return

            # Get recent metrics for alert evaluation
            recent_metrics = self._get_recent_metrics(
                self.config.alert_check_interval * 2  # Look back twice the check interval
            )

            if recent_metrics:
                # Process alerts
                alerts = await self.alert_manager.process_metrics(recent_metrics)

                # Update active alerts
                await self._update_active_alerts(alerts)

                # Update dashboard
                await self.dashboard.update_alerts(alerts)

                if alerts:
                    logger.info(f"Generated {len(alerts)} new alerts")

        except Exception as e:
            logger.error(f"Error checking alerts: {e}")

    async def generate_report(self, period: str = "24h") -> MonitoringReport:
        """
        Generate monitoring report

        Args:
            period: Time period for report (1h, 24h, 7d, 30d)

        Returns:
            Monitoring report
        """
        try:
            # Calculate time range
            end_time = datetime.now()
            if period == "1h":
                start_time = end_time - timedelta(hours=1)
            elif period == "24h":
                start_time = end_time - timedelta(days=1)
            elif period == "7d":
                start_time = end_time - timedelta(days=7)
            elif period == "30d":
                start_time = end_time - timedelta(days=30)
            else:
                raise ValueError(f"Invalid period: {period}")

            # Get metrics for the period
            period_metrics = self._get_metrics_in_range(start_time, end_time)

            # Generate report
            report = MonitoringReport(
                report_id=str(uuid.uuid4()),
                generated_at=datetime.now(),
                period_start=start_time,
                period_end=end_time,
                summary=self._generate_summary(period_metrics),
                performance_summary=self._generate_performance_summary(period_metrics),
                quality_summary=self._generate_quality_summary(period_metrics),
                health_summary=self._generate_health_summary(period_metrics),
                alerts_summary=self._generate_alerts_summary(period_metrics),
                recommendations=self._generate_recommendations(period_metrics)
            )

            logger.info(f"Generated monitoring report for period {period}")

            return report

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise

    def _store_metrics(self, metrics: SystemMetrics):
        """Store metrics in history"""
        self.metrics_history.append(metrics)

        # Apply retention policy
        cutoff_time = datetime.now() - self.config.retention_period
        self.metrics_history = [m for m in self.metrics_history if m.timestamp > cutoff_time]

    def _get_recent_metrics(self, duration: timedelta) -> List[SystemMetrics]:
        """Get metrics from recent duration"""
        cutoff_time = datetime.now() - duration
        return [m for m in self.metrics_history if m.timestamp > cutoff_time]

    def _get_metrics_in_range(self, start_time: datetime, end_time: datetime) -> List[SystemMetrics]:
        """Get metrics in time range"""
        return [m for m in self.metrics_history if start_time <= m.timestamp <= end_time]

    async def _update_active_alerts(self, new_alerts: List[Alert]):
        """Update active alerts list"""
        # Add new alerts
        for alert in new_alerts:
            if alert.status == Alert.ACTIVE:
                self.active_alerts.append(alert)

        # Remove resolved alerts
        self.active_alerts = [a for a in self.active_alerts if a.status == Alert.ACTIVE]

    def _generate_summary(self, metrics: List[SystemMetrics]) -> Dict[str, Any]:
        """Generate report summary"""
        if not metrics:
            return {"status": "No data available"}

        total_metrics = len(metrics)
        healthy_count = sum(1 for m in metrics if m.health.overall_status == HealthStatus.HEALTHY)

        return {
            "total_metrics_points": total_metrics,
            "healthy_percentage": (healthy_count / total_metrics) * 100 if total_metrics > 0 else 0,
            "monitoring_uptime": (datetime.now() - self.start_time).total_seconds(),
            "collection_count": self.collection_count
        }

    def _generate_performance_summary(self, metrics: List[SystemMetrics]) -> Dict[str, Any]:
        """Generate performance summary"""
        if not metrics:
            return {"status": "No data available"}

        # Calculate averages
        avg_latency = sum(m.performance.data_processing_latency for m in metrics) / len(metrics)
        avg_throughput = sum(m.performance.throughput_requests_per_second for m in metrics) / len(metrics)
        avg_error_rate = sum(m.performance.concurrency_stats.error_rate for m in metrics) / len(metrics)

        return {
            "average_latency_ms": avg_latency * 1000,
            "average_throughput_rps": avg_throughput,
            "average_error_rate": avg_error_rate,
            "latency_threshold_ms": self.config.max_latency_ms * 1000,
            "latency_compliance": avg_latency < self.config.max_latency_ms
        }

    def _generate_quality_summary(self, metrics: List[SystemMetrics]) -> Dict[str, Any]:
        """Generate quality summary"""
        if not metrics:
            return {"status": "No data available"}

        # Calculate averages
        avg_signal_accuracy = sum(m.quality.signal_quality.signal_accuracy for m in metrics) / len(metrics)
        avg_data_completeness = sum(m.quality.data_quality.completeness_score for m in metrics) / len(metrics)
        avg_llm_quality = sum(m.quality.llm_quality.response_quality_score for m in metrics) / len(metrics)

        return {
            "average_signal_accuracy": avg_signal_accuracy,
            "average_data_completeness": avg_data_completeness,
            "average_llm_quality": avg_llm_quality,
            "quality_score": (avg_signal_accuracy + avg_data_completeness + avg_llm_quality) / 3
        }

    def _generate_health_summary(self, metrics: List[SystemMetrics]) -> Dict[str, Any]:
        """Generate health summary"""
        if not metrics:
            return {"status": "No data available"}

        # Count health statuses
        status_counts = {}
        for metric in metrics:
            status = metric.health.overall_status
            status_counts[status] = status_counts.get(status, 0) + 1

        # Calculate uptime
        uptime_percentage = (status_counts.get(HealthStatus.HEALTHY, 0) / len(metrics)) * 100

        return {
            "uptime_percentage": uptime_percentage,
            "status_distribution": status_counts,
            "availability_target": self.config.min_availability * 100,
            "availability_compliance": uptime_percentage >= (self.config.min_availability * 100)
        }

    def _generate_alerts_summary(self, metrics: List[SystemMetrics]) -> Dict[str, Any]:
        """Generate alerts summary"""
        period_alerts = [a for a in self.active_alerts if a.triggered_at >= metrics[0].timestamp if metrics]

        # Count by severity
        severity_counts = {}
        for alert in period_alerts:
            severity = alert.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "total_alerts": len(period_alerts),
            "active_alerts": len([a for a in period_alerts if a.status == Alert.ACTIVE]),
            "severity_distribution": severity_counts,
            "critical_alerts": severity_counts.get(AlertSeverity.CRITICAL, 0)
        }

    def _generate_recommendations(self, metrics: List[SystemMetrics]) -> List[str]:
        """Generate recommendations based on metrics"""
        recommendations = []

        if not metrics:
            return ["No data available for recommendations"]

        # Performance recommendations
        avg_latency = sum(m.performance.data_processing_latency for m in metrics) / len(metrics)
        if avg_latency > self.config.max_latency_ms:
            recommendations.append("Consider optimizing data processing pipelines to reduce latency")

        # Error rate recommendations
        avg_error_rate = sum(m.performance.concurrency_stats.error_rate for m in metrics) / len(metrics)
        if avg_error_rate > self.config.max_error_rate:
            recommendations.append("Investigate and address high error rates in system components")

        # Quality recommendations
        avg_signal_accuracy = sum(m.quality.signal_quality.signal_accuracy for m in metrics) / len(metrics)
        if avg_signal_accuracy < 0.8:
            recommendations.append("Review and improve signal generation algorithms for better accuracy")

        # Resource recommendations
        avg_cpu = sum(m.performance.resource_usage.cpu_percent for m in metrics) / len(metrics)
        if avg_cpu > 80:
            recommendations.append("Consider scaling system resources to handle high CPU usage")

        # Health recommendations
        uptime_percentage = (sum(1 for m in metrics if m.health.overall_status == HealthStatus.HEALTHY) / len(metrics)) * 100
        if uptime_percentage < self.config.min_availability * 100:
            recommendations.append("Improve system reliability and implement better fault tolerance")

        return recommendations if recommendations else ["System performance is within acceptable parameters"]

    def get_metrics_history(self, duration: timedelta = None) -> List[SystemMetrics]:
        """
        Get metrics history

        Args:
            duration: Time duration to retrieve (None for all history)

        Returns:
            List of system metrics
        """
        if duration is None:
            return self.metrics_history.copy()

        cutoff_time = datetime.now() - duration
        return self._get_metrics_in_range(cutoff_time, datetime.now())

    def get_active_alerts(self) -> List[Alert]:
        """
        Get active alerts

        Returns:
            List of active alerts
        """
        return self.active_alerts.copy()

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status

        Returns:
            System status summary
        """
        latest_metrics = self.metrics_history[-1] if self.metrics_history else None

        status = {
            "monitoring_active": self._collection_task is not None,
            "start_time": self.start_time.isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "metrics_collected": self.collection_count,
            "active_alerts_count": len(self.active_alerts),
            "config": self.config.dict()
        }

        if latest_metrics:
            status["latest_metrics"] = {
                "timestamp": latest_metrics.timestamp.isoformat(),
                "performance_latency_ms": latest_metrics.performance.data_processing_latency * 1000,
                "error_rate": latest_metrics.performance.concurrency_stats.error_rate,
                "health_status": latest_metrics.health.overall_status.value,
                "signal_accuracy": latest_metrics.quality.signal_quality.signal_accuracy
            }

        return status

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system") -> bool:
        """
        Acknowledge an alert

        Args:
            alert_id: Alert ID to acknowledge
            acknowledged_by: Who acknowledged the alert

        Returns:
            True if successful, False otherwise
        """
        for alert in self.active_alerts:
            if alert.id == alert_id and alert.status == Alert.ACTIVE:
                alert.status = Alert.ACKNOWLEDGED
                alert.acknowledged_at = datetime.now()
                logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
                return True

        return False

    async def resolve_alert(self, alert_id: str, resolved_by: str = "system") -> bool:
        """
        Resolve an alert

        Args:
            alert_id: Alert ID to resolve
            resolved_by: Who resolved the alert

        Returns:
            True if successful, False otherwise
        """
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.status = Alert.RESOLVED
                alert.resolved_at = datetime.now()
                logger.info(f"Alert {alert_id} resolved by {resolved_by}")
                return True

        return False