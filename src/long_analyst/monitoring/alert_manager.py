"""
Alert manager for handling system alerts and notifications
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import json

from .models import (
    Alert,
    AlertRule,
    AlertSeverity,
    AlertStatus,
    RuleType,
    SystemMetrics,
    MonitoringConfig
)

logger = logging.getLogger(__name__)


class AlertManager:
    """Alert manager for handling system alerts and notifications"""

    def __init__(self, config: MonitoringConfig):
        """
        Initialize alert manager

        Args:
            config: Monitoring configuration
        """
        self.config = config

        # Load alert rules
        self.rules = self._load_alert_rules()

        # Alert history
        self.alert_history = []
        self.active_alerts = []

        # Alert suppression
        self.alert_suppressions = {}  # rule_id -> suppression_end_time

        # Notifiers
        self.notifiers = self._init_notifiers()

    def _load_alert_rules(self) -> Dict[str, AlertRule]:
        """Load alert rules"""
        default_rules = {
            "high_latency": AlertRule(
                id="high_latency",
                name="High Processing Latency",
                description="Processing latency exceeds threshold",
                rule_type=RuleType.THRESHOLD,
                metric_name="data_processing_latency",
                condition="value > threshold",
                threshold=self.config.max_latency_ms,
                duration=timedelta(minutes=5),
                severity=AlertSeverity.HIGH,
                enabled=True,
                tags=["performance", "latency"]
            ),
            "high_error_rate": AlertRule(
                id="high_error_rate",
                name="High Error Rate",
                description="System error rate exceeds threshold",
                rule_type=RuleType.THRESHOLD,
                metric_name="error_rate",
                condition="value > threshold",
                threshold=self.config.max_error_rate,
                duration=timedelta(minutes=5),
                severity=AlertSeverity.CRITICAL,
                enabled=True,
                tags=["performance", "errors"]
            ),
            "low_availability": AlertRule(
                id="low_availability",
                name="Low System Availability",
                description="System availability below target",
                rule_type=RuleType.THRESHOLD,
                metric_name="uptime_percentage",
                condition="value < threshold",
                threshold=self.config.min_availability,
                duration=timedelta(minutes=10),
                severity=AlertSeverity.CRITICAL,
                enabled=True,
                tags=["availability"]
            ),
            "high_cpu_usage": AlertRule(
                id="high_cpu_usage",
                name="High CPU Usage",
                description="CPU usage exceeds threshold",
                rule_type=RuleType.THRESHOLD,
                metric_name="cpu_percent",
                condition="value > threshold",
                threshold=80.0,
                duration=timedelta(minutes=5),
                severity=AlertSeverity.MEDIUM,
                enabled=True,
                tags=["resources", "cpu"]
            ),
            "high_memory_usage": AlertRule(
                id="high_memory_usage",
                name="High Memory Usage",
                description="Memory usage exceeds threshold",
                rule_type=RuleType.THRESHOLD,
                metric_name="memory_percent",
                condition="value > threshold",
                threshold=85.0,
                duration=timedelta(minutes=5),
                severity=AlertSeverity.MEDIUM,
                enabled=True,
                tags=["resources", "memory"]
            ),
            "low_signal_accuracy": AlertRule(
                id="low_signal_accuracy",
                name="Low Signal Accuracy",
                description="Signal accuracy below threshold",
                rule_type=RuleType.THRESHOLD,
                metric_name="signal_accuracy",
                condition="value < threshold",
                threshold=0.7,
                duration=timedelta(minutes=15),
                severity=AlertSeverity.MEDIUM,
                enabled=True,
                tags=["quality", "signals"]
            ),
            "service_down": AlertRule(
                id="service_down",
                name="Service Unavailable",
                description="Service is not responding",
                rule_type=RuleType.AVAILABILITY,
                metric_name="service_health",
                condition="value == False",
                threshold=1.0,
                duration=timedelta(minutes=2),
                severity=AlertSeverity.CRITICAL,
                enabled=True,
                tags=["availability", "services"]
            )
        }

        return default_rules

    def _init_notifiers(self) -> Dict[str, Any]:
        """Initialize notification notifiers"""
        return {
            'log': LogNotifier(),
            'webhook': WebhookNotifier(self.config.webhook_url) if self.config.webhook_url else None,
            'slack': SlackNotifier(self.config.slack_webhook_url) if self.config.slack_webhook_url else None,
            'email': EmailNotifier(self.config.email_recipients) if self.config.email_recipients else None
        }

    async def process_metrics(self, metrics: List[SystemMetrics]) -> List[Alert]:
        """
        Process metrics and generate alerts

        Args:
            metrics: List of system metrics

        Returns:
            List of new alerts
        """
        new_alerts = []

        try:
            for rule_id, rule in self.rules.items():
                if not rule.enabled:
                    continue

                # Check if rule is suppressed
                if self._is_rule_suppressed(rule_id):
                    continue

                # Evaluate rule
                alert = await self._evaluate_rule(rule, metrics)
                if alert:
                    new_alerts.append(alert)
                    await self._handle_new_alert(alert)

            logger.debug(f"Processed metrics, generated {len(new_alerts)} alerts")

        except Exception as e:
            logger.error(f"Error processing metrics for alerts: {e}")

        return new_alerts

    async def _evaluate_rule(self, rule: AlertRule, metrics: List[SystemMetrics]) -> Optional[Alert]:
        """Evaluate a single alert rule"""
        try:
            # Get relevant metrics for the rule
            relevant_metrics = self._get_relevant_metrics(rule, metrics)

            if not relevant_metrics:
                return None

            # Check condition duration
            if not self._check_duration_condition(rule, relevant_metrics):
                return None

            # Evaluate the rule condition
            triggered = await self._evaluate_rule_condition(rule, relevant_metrics)

            if triggered:
                # Check if similar alert is already active
                if self._has_similar_active_alert(rule):
                    return None

                # Create alert
                latest_metric = relevant_metrics[-1]
                current_value = self._extract_metric_value(rule.metric_name, latest_metric)

                alert = Alert(
                    id=str(uuid.uuid4()),
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    title=f"{rule.name} - Threshold Exceeded",
                    description=rule.description,
                    metric_name=rule.metric_name,
                    current_value=current_value,
                    threshold=rule.threshold,
                    triggered_at=datetime.now(),
                    tags=rule.tags
                )

                return alert

        except Exception as e:
            logger.error(f"Error evaluating rule {rule.id}: {e}")

        return None

    def _get_relevant_metrics(self, rule: AlertRule, metrics: List[SystemMetrics]) -> List[SystemMetrics]:
        """Get metrics relevant to the rule"""
        duration_needed = rule.duration
        cutoff_time = datetime.now() - duration_needed

        return [m for m in metrics if m.timestamp > cutoff_time]

    def _check_duration_condition(self, rule: AlertRule, metrics: List[SystemMetrics]) -> bool:
        """Check if condition has been met for the required duration"""
        if len(metrics) < 2:
            return False

        # Check if condition is met across all metrics in the duration
        for metric in metrics:
            value = self._extract_metric_value(rule.metric_name, metric)
            if not self._evaluate_threshold_condition(rule, value):
                return False

        return True

    async def _evaluate_rule_condition(self, rule: AlertRule, metrics: List[SystemMetrics]) -> bool:
        """Evaluate the rule condition"""
        if rule.rule_type == RuleType.THRESHOLD:
            latest_metric = metrics[-1]
            value = self._extract_metric_value(rule.metric_name, latest_metric)
            return self._evaluate_threshold_condition(rule, value)

        elif rule.rule_type == RuleType.AVAILABILITY:
            # For availability rules, check if any metric shows the condition
            for metric in metrics:
                value = self._extract_metric_value(rule.metric_name, metric)
                if value == rule.threshold:  # For availability, threshold is the expected value
                    return True

        return False

    def _evaluate_threshold_condition(self, rule: AlertRule, value: float) -> bool:
        """Evaluate threshold condition"""
        if ">" in rule.condition:
            return value > rule.threshold
        elif "<" in rule.condition:
            return value < rule.threshold
        elif ">=" in rule.condition:
            return value >= rule.threshold
        elif "<=" in rule.condition:
            return value <= rule.threshold
        elif "==" in rule.condition:
            return value == rule.threshold
        elif "!=" in rule.condition:
            return value != rule.threshold

        return False

    def _extract_metric_value(self, metric_name: str, metric: SystemMetrics) -> float:
        """Extract metric value from system metrics"""
        if metric_name == "data_processing_latency":
            return metric.performance.data_processing_latency
        elif metric_name == "error_rate":
            return metric.performance.concurrency_stats.error_rate
        elif metric_name == "uptime_percentage":
            return metric.health.uptime_percentage
        elif metric_name == "cpu_percent":
            return metric.performance.resource_usage.cpu_percent
        elif metric_name == "memory_percent":
            return metric.performance.resource_usage.memory_percent
        elif metric_name == "signal_accuracy":
            return metric.quality.signal_quality.signal_accuracy
        elif metric_name == "service_health":
            # For service health, return 1.0 if all services are healthy, 0.0 otherwise
            healthy_services = sum(1 for s in metric.health.services_health.values() if s.is_healthy)
            total_services = len(metric.health.services_health)
            return 1.0 if healthy_services == total_services and total_services > 0 else 0.0
        else:
            logger.warning(f"Unknown metric name: {metric_name}")
            return 0.0

    def _has_similar_active_alert(self, rule: AlertRule) -> bool:
        """Check if there's already an active alert for this rule"""
        for alert in self.active_alerts:
            if alert.rule_id == rule.id and alert.status == AlertStatus.ACTIVE:
                return True
        return False

    def _is_rule_suppressed(self, rule_id: str) -> bool:
        """Check if a rule is currently suppressed"""
        if rule_id not in self.alert_suppressions:
            return False

        suppression_end = self.alert_suppressions[rule_id]
        if datetime.now() > suppression_end:
            del self.alert_suppressions[rule_id]
            return False

        return True

    async def _handle_new_alert(self, alert: Alert):
        """Handle a new alert"""
        # Add to active alerts
        self.active_alerts.append(alert)

        # Add to history
        self.alert_history.append(alert)

        # Send notifications
        await self._send_alert_notifications(alert)

        # Log the alert
        logger.warning(f"New alert: {alert.title} - {alert.description}")

    async def _send_alert_notifications(self, alert: Alert):
        """Send alert notifications through configured channels"""
        for channel in self.config.alert_channels:
            notifier = self.notifiers.get(channel)
            if notifier:
                try:
                    await notifier.send_notification(alert)
                except Exception as e:
                    logger.error(f"Error sending alert notification via {channel}: {e}")

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
            if alert.id == alert_id and alert.status == AlertStatus.ACTIVE:
                alert.status = AlertStatus.ACKNOWLEDGED
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
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.now()
                logger.info(f"Alert {alert_id} resolved by {resolved_by}")
                return True

        return False

    async def suppress_alert(self, rule_id: str, duration: timedelta, reason: str = "manual"):
        """
        Suppress alerts for a rule

        Args:
            rule_id: Rule ID to suppress
            duration: Suppression duration
            reason: Reason for suppression
        """
        suppression_end = datetime.now() + duration
        self.alert_suppressions[rule_id] = suppression_end

        logger.info(f"Suppressed alerts for rule {rule_id} until {suppression_end}: {reason}")

        # Resolve any active alerts for this rule
        for alert in self.active_alerts:
            if alert.rule_id == rule_id and alert.status == AlertStatus.ACTIVE:
                await self.resolve_alert(alert.id, f"suppression: {reason}")

    def add_rule(self, rule: AlertRule):
        """Add a new alert rule"""
        self.rules[rule.id] = rule
        logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_id: str):
        """Remove an alert rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")

    def enable_rule(self, rule_id: str):
        """Enable an alert rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            logger.info(f"Enabled alert rule: {rule_id}")

    def disable_rule(self, rule_id: str):
        """Disable an alert rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            logger.info(f"Disabled alert rule: {rule_id}")

    def get_active_alerts(self) -> List[Alert]:
        """Get list of active alerts"""
        return [alert for alert in self.active_alerts if alert.status == AlertStatus.ACTIVE]

    def get_alert_history(self, duration: timedelta = None) -> List[Alert]:
        """Get alert history"""
        if duration is None:
            return self.alert_history.copy()

        cutoff_time = datetime.now() - duration
        return [alert for alert in self.alert_history if alert.triggered_at > cutoff_time]

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary"""
        active_alerts = self.get_active_alerts()

        # Count by severity
        severity_counts = {}
        for alert in active_alerts:
            severity = alert.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Count by rule
        rule_counts = {}
        for alert in active_alerts:
            rule = alert.rule_id
            rule_counts[rule] = rule_counts.get(rule, 0) + 1

        return {
            'total_active_alerts': len(active_alerts),
            'severity_distribution': severity_counts,
            'rule_distribution': rule_counts,
            'suppressed_rules': len(self.alert_suppressions),
            'total_rules': len(self.rules),
            'enabled_rules': sum(1 for rule in self.rules.values() if rule.enabled)
        }

    def clear_resolved_alerts(self, older_than: timedelta = timedelta(days=7)):
        """Clear resolved alerts older than specified duration"""
        cutoff_time = datetime.now() - older_than

        # Remove from active alerts
        self.active_alerts = [
            alert for alert in self.active_alerts
            if not (alert.status == AlertStatus.RESOLVED and alert.resolved_at < cutoff_time)
        ]

        logger.info(f"Cleared resolved alerts older than {older_than}")


class LogNotifier:
    """Log notifier for alerts"""

    async def send_notification(self, alert: Alert):
        """Send alert notification to log"""
        logger.error(f"ALERT [{alert.severity.upper()}] {alert.title}: {alert.description}")


class WebhookNotifier:
    """Webhook notifier for alerts"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send_notification(self, alert: Alert):
        """Send alert notification via webhook"""
        # In a real implementation, this would make HTTP requests
        logger.info(f"Webhook notification sent for alert {alert.id}: {self.webhook_url}")


class SlackNotifier:
    """Slack notifier for alerts"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send_notification(self, alert: Alert):
        """Send alert notification via Slack"""
        # In a real implementation, this would send to Slack webhook
        message = {
            "text": f"🚨 *{alert.title}*",
            "attachments": [
                {
                    "color": "danger" if alert.severity == AlertSeverity.CRITICAL else "warning",
                    "fields": [
                        {"title": "Description", "value": alert.description, "short": False},
                        {"title": "Current Value", "value": str(alert.current_value), "short": True},
                        {"title": "Threshold", "value": str(alert.threshold), "short": True},
                        {"title": "Time", "value": alert.triggered_at.strftime("%Y-%m-%d %H:%M:%S"), "short": True}
                    ]
                }
            ]
        }

        logger.info(f"Slack notification sent for alert {alert.id}: {self.webhook_url}")


class EmailNotifier:
    """Email notifier for alerts"""

    def __init__(self, recipients: List[str]):
        self.recipients = recipients

    async def send_notification(self, alert: Alert):
        """Send alert notification via email"""
        # In a real implementation, this would send emails
        subject = f"Alert: {alert.title}"
        body = f"""
Alert Details:
- Title: {alert.title}
- Description: {alert.description}
- Severity: {alert.severity}
- Current Value: {alert.current_value}
- Threshold: {alert.threshold}
- Triggered At: {alert.triggered_at}

Please investigate and take appropriate action.
"""

        logger.info(f"Email notification sent for alert {alert.id} to {self.recipients}")