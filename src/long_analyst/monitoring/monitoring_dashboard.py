"""
Monitoring dashboard for real-time system monitoring
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from .models import (
    SystemMetrics,
    Alert,
    HealthStatus,
    DashboardConfig,
    DashboardWidget,
    MonitoringConfig
)

logger = logging.getLogger(__name__)


class MonitoringDashboard:
    """Monitoring dashboard for real-time system monitoring"""

    def __init__(self, config: MonitoringConfig):
        """
        Initialize monitoring dashboard

        Args:
            config: Monitoring configuration
        """
        self.config = config

        # Current metrics and alerts
        self.current_metrics = None
        self.current_health_status = HealthStatus.HEALTHY
        self.current_alerts = []

        # Dashboard configuration
        self.dashboard_config = self._create_default_dashboard_config()

        # Widget data
        self.widget_data = {}

    def _create_default_dashboard_config(self) -> DashboardConfig:
        """Create default dashboard configuration"""
        widgets = [
            DashboardWidget(
                widget_id="system_health",
                widget_type="gauge",
                title="System Health",
                data_source="health_status",
                config={"min": 0, "max": 100, "thresholds": [70, 90]},
                position={"row": 0, "col": 0}
            ),
            DashboardWidget(
                widget_id="active_alerts",
                widget_type="counter",
                title="Active Alerts",
                data_source="alerts",
                config={"severity_colors": True},
                position={"row": 0, "col": 1}
            ),
            DashboardWidget(
                widget_id="performance_latency",
                widget_type="line_chart",
                title="Processing Latency",
                data_source="performance_metrics",
                config={"metric": "data_processing_latency", "time_range": "1h"},
                position={"row": 1, "col": 0}
            ),
            DashboardWidget(
                widget_id="resource_usage",
                widget_type="bar_chart",
                title="Resource Usage",
                data_source="resource_metrics",
                config={"resources": ["cpu", "memory", "disk"]},
                position={"row": 1, "col": 1}
            ),
            DashboardWidget(
                widget_id="signal_quality",
                widget_type="line_chart",
                title="Signal Quality",
                data_source="quality_metrics",
                config={"metrics": ["signal_accuracy", "false_positive_rate"], "time_range": "1h"},
                position={"row": 2, "col": 0}
            ),
            DashboardWidget(
                widget_id="throughput",
                widget_type="line_chart",
                title="System Throughput",
                data_source="performance_metrics",
                config={"metric": "throughput_requests_per_second", "time_range": "1h"},
                position={"row": 2, "col": 1}
            ),
            DashboardWidget(
                widget_id="recent_alerts",
                widget_type="table",
                title="Recent Alerts",
                data_source="recent_alerts",
                config={"limit": 10, "columns": ["severity", "title", "triggered_at"]},
                position={"row": 3, "col": 0, "colspan": 2}
            )
        ]

        layout = {
            "rows": 4,
            "columns": 2,
            "widget_width": 400,
            "widget_height": 300,
            "spacing": 10
        }

        return DashboardConfig(
            dashboard_id="main",
            title="Long Analyst Agent Monitoring Dashboard",
            refresh_interval=self.config.dashboard_refresh_interval,
            widgets=widgets,
            layout=layout
        )

    async def update_metrics(self, metrics: SystemMetrics):
        """Update dashboard with new metrics"""
        self.current_metrics = metrics

        # Update widget data
        await self._update_widget_data(metrics)

        logger.debug("Dashboard metrics updated")

    async def update_health_status(self, health_status: HealthStatus):
        """Update dashboard health status"""
        self.current_health_status = health_status
        await self._update_widget_data_health(health_status)

    async def update_alerts(self, alerts: List[Alert]):
        """Update dashboard alerts"""
        self.current_alerts = alerts
        await self._update_widget_data_alerts(alerts)

    async def _update_widget_data(self, metrics: SystemMetrics):
        """Update widget data with metrics"""
        # System health widget
        health_score = self._calculate_health_score(metrics)
        self.widget_data['system_health'] = {
            "value": health_score,
            "status": self.current_health_status.value,
            "timestamp": metrics.timestamp.isoformat()
        }

        # Performance metrics widget
        self.widget_data['performance_metrics'] = {
            "latency_ms": metrics.performance.data_processing_latency * 1000,
            "throughput_rps": metrics.performance.throughput_requests_per_second,
            "error_rate": metrics.performance.concurrency_stats.error_rate,
            "timestamp": metrics.timestamp.isoformat()
        }

        # Resource usage widget
        self.widget_data['resource_metrics'] = {
            "cpu_percent": metrics.performance.resource_usage.cpu_percent,
            "memory_percent": metrics.performance.resource_usage.memory_percent,
            "disk_percent": metrics.performance.resource_usage.disk_percent,
            "timestamp": metrics.timestamp.isoformat()
        }

        # Quality metrics widget
        self.widget_data['quality_metrics'] = {
            "signal_accuracy": metrics.quality.signal_quality.signal_accuracy,
            "false_positive_rate": metrics.quality.signal_quality.false_positive_rate,
            "llm_quality": metrics.quality.llm_quality.response_quality_score,
            "timestamp": metrics.timestamp.isoformat()
        }

        # Active alerts widget
        active_alerts_count = len(self.current_alerts)
        self.widget_data['active_alerts'] = {
            "count": active_alerts_count,
            "by_severity": self._count_alerts_by_severity(self.current_alerts),
            "timestamp": datetime.now().isoformat()
        }

    async def _update_widget_data_health(self, health_status: HealthStatus):
        """Update health-specific widget data"""
        if 'system_health' not in self.widget_data:
            self.widget_data['system_health'] = {}

        self.widget_data['system_health']['status'] = health_status.value
        self.widget_data['system_health']['updated_at'] = datetime.now().isoformat()

    async def _update_widget_data_alerts(self, alerts: List[Alert]):
        """Update alert-specific widget data"""
        # Recent alerts widget
        recent_alerts = sorted(alerts, key=lambda x: x.triggered_at, reverse=True)[:10]
        self.widget_data['recent_alerts'] = [
            {
                "id": alert.id,
                "severity": alert.severity.value,
                "title": alert.title,
                "description": alert.description,
                "triggered_at": alert.triggered_at.isoformat(),
                "status": alert.status.value
            }
            for alert in recent_alerts
        ]

    def _calculate_health_score(self, metrics: SystemMetrics) -> float:
        """Calculate overall health score"""
        try:
            # Simple health score calculation
            performance_score = 1.0 - min(metrics.performance.concurrency_stats.error_rate * 10, 1.0)
            quality_score = metrics.quality.signal_quality.signal_accuracy
            availability_score = metrics.health.uptime_percentage

            return (performance_score + quality_score + availability_score) / 3 * 100

        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 50.0

    def _count_alerts_by_severity(self, alerts: List[Alert]) -> Dict[str, int]:
        """Count alerts by severity"""
        severity_counts = {}
        for alert in alerts:
            severity = alert.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        return severity_counts

    async def render_dashboard(self) -> str:
        """
        Render dashboard as HTML

        Returns:
            HTML string of dashboard
        """
        try:
            html_template = self._get_dashboard_html_template()

            # Prepare template context
            context = {
                "dashboard_title": self.dashboard_config.title,
                "refresh_interval": self.dashboard_config.refresh_interval.total_seconds() * 1000,
                "widget_data": self.widget_data,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "health_status": self.current_health_status.value
            }

            # Simple template rendering (in production, use a proper template engine)
            html_content = html_template.format(**context)

            return html_content

        except Exception as e:
            logger.error(f"Error rendering dashboard: {e}")
            return f"<html><body><h1>Error rendering dashboard: {e}</h1></body></html>"

    def _get_dashboard_html_template(self) -> str:
        """Get dashboard HTML template"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{dashboard_title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .dashboard-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .health-status {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .health-status.healthy {{ background-color: #28a745; }}
        .health-status.warning {{ background-color: #ffc107; }}
        .health-status.degraded {{ background-color: #fd7e14; }}
        .health-status.unhealthy {{ background-color: #dc3545; }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }}
        .widget {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .widget h3 {{
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background-color: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s ease;
        }}
        .alert-item {{
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }}
        .alert-item.critical {{ border-left-color: #dc3545; background-color: #f8d7da; }}
        .alert-item.high {{ border-left-color: #fd7e14; background-color: #fff3cd; }}
        .alert-item.medium {{ border-left-color: #ffc107; background-color: #fff3cd; }}
        .alert-item.low {{ border-left-color: #17a2b8; background-color: #d1ecf1; }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
    <script>
        function refreshDashboard() {{
            setTimeout(function() {{
                location.reload();
            }}, {refresh_interval});
        }}
    </script>
</head>
<body onload="refreshDashboard()">
    <div class="dashboard-header">
        <h1>{dashboard_title}</h1>
        <span class="health-status {health_status}">{health_status.upper()}</span>
        <div style="margin-top: 10px;">Last Updated: {last_updated}</div>
    </div>

    <div class="dashboard-grid">
        <!-- System Health Widget -->
        <div class="widget">
            <h3>System Health</h3>
            <div class="metric-value" id="health-score">
                {widget_data[system_health][value]:.1f}%
            </div>
            <div class="metric-label">Overall Health Score</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {widget_data[system_health][value]}%"></div>
            </div>
        </div>

        <!-- Active Alerts Widget -->
        <div class="widget">
            <h3>Active Alerts</h3>
            <div class="metric-value" id="alert-count">
                {widget_data[active_alerts][count]}
            </div>
            <div class="metric-label">Total Active Alerts</div>
            <div style="margin-top: 10px;">
                <span style="color: #dc3545;">Critical: {widget_data[active_alerts][by_severity].get(critical, 0)}</span> |
                <span style="color: #fd7e14;">High: {widget_data[active_alerts][by_severity].get(high, 0)}</span> |
                <span style="color: #ffc107;">Medium: {widget_data[active_alerts][by_severity].get(medium, 0)}</span> |
                <span style="color: #17a2b8;">Low: {widget_data[active_alerts][by_severity].get(low, 0)}</span>
            </div>
        </div>

        <!-- Performance Metrics Widget -->
        <div class="widget">
            <h3>Performance Metrics</h3>
            <div><strong>Latency:</strong> {widget_data[performance_metrics][latency_ms]:.1f}ms</div>
            <div><strong>Throughput:</strong> {widget_data[performance_metrics][throughput_rps]:.1f} req/s</div>
            <div><strong>Error Rate:</strong> {widget_data[performance_metrics][error_rate]:.1%}</div>
        </div>

        <!-- Resource Usage Widget -->
        <div class="widget">
            <h3>Resource Usage</h3>
            <div><strong>CPU:</strong> {widget_data[resource_metrics][cpu_percent]:.1f}%</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {widget_data[resource_metrics][cpu_percent]}%"></div>
            </div>
            <div><strong>Memory:</strong> {widget_data[resource_metrics][memory_percent]:.1f}%</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {widget_data[resource_metrics][memory_percent]}%"></div>
            </div>
            <div><strong>Disk:</strong> {widget_data[resource_metrics][disk_percent]:.1f}%</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {widget_data[resource_metrics][disk_percent]}%"></div>
            </div>
        </div>

        <!-- Quality Metrics Widget -->
        <div class="widget">
            <h3>Quality Metrics</h3>
            <div><strong>Signal Accuracy:</strong> {widget_data[quality_metrics][signal_accuracy]:.1%}</div>
            <div><strong>False Positive Rate:</strong> {widget_data[quality_metrics][false_positive_rate]:.1%}</div>
            <div><strong>LLM Quality:</strong> {widget_data[quality_metrics][llm_quality]:.1%}</div>
        </div>

        <!-- Recent Alerts Widget -->
        <div class="widget" style="grid-column: span 2;">
            <h3>Recent Alerts</h3>
            <div id="recent-alerts">
                {recent_alerts_html}
            </div>
        </div>
    </div>

    <div class="footer">
        <p>Long Analyst Agent Monitoring Dashboard | Auto-refresh every {refresh_interval/1000:.0f} seconds</p>
    </div>
</body>
</html>
        """.replace("{recent_alerts_html}", self._generate_recent_alerts_html())

    def _generate_recent_alerts_html(self) -> str:
        """Generate HTML for recent alerts"""
        if 'recent_alerts' not in self.widget_data:
            return "<p>No recent alerts</p>"

        alerts_html = []
        for alert in self.widget_data['recent_alerts'][:5]:  # Show last 5 alerts
            alerts_html.append(f"""
            <div class="alert-item {alert['severity']}">
                <strong>{alert['title']}</strong>
                <br><small>{alert['description']}</small>
                <br><small>{alert['triggered_at']}</small>
            </div>
            """)

        return "".join(alerts_html) if alerts_html else "<p>No recent alerts</p>"

    async def generate_widget(self, widget_type: str, data: Dict) -> str:
        """
        Generate a specific widget

        Args:
            widget_type: Type of widget to generate
            data: Widget data

        Returns:
            HTML string for the widget
        """
        if widget_type == "gauge":
            return self._generate_gauge_widget(data)
        elif widget_type == "counter":
            return self._generate_counter_widget(data)
        elif widget_type == "line_chart":
            return self._generate_line_chart_widget(data)
        elif widget_type == "bar_chart":
            return self._generate_bar_chart_widget(data)
        elif widget_type == "table":
            return self._generate_table_widget(data)
        else:
            return f"<div>Unknown widget type: {widget_type}</div>"

    def _generate_gauge_widget(self, data: Dict) -> str:
        """Generate gauge widget HTML"""
        value = data.get('value', 0)
        status = data.get('status', 'unknown')

        return f"""
        <div class="gauge-widget">
            <div class="gauge-value">{value:.1f}%</div>
            <div class="gauge-status {status}">{status}</div>
        </div>
        """

    def _generate_counter_widget(self, data: Dict) -> str:
        """Generate counter widget HTML"""
        count = data.get('count', 0)
        return f'<div class="counter-widget"><div class="counter-value">{count}</div></div>'

    def _generate_line_chart_widget(self, data: Dict) -> str:
        """Generate line chart widget HTML"""
        # Placeholder for line chart
        return '<div class="chart-widget">Line Chart (Placeholder)</div>'

    def _generate_bar_chart_widget(self, data: Dict) -> str:
        """Generate bar chart widget HTML"""
        # Placeholder for bar chart
        return '<div class="chart-widget">Bar Chart (Placeholder)</div>'

    def _generate_table_widget(self, data: Dict) -> str:
        """Generate table widget HTML"""
        # Placeholder for table
        return '<div class="table-widget">Table (Placeholder)</div>'

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get complete dashboard data

        Returns:
            Dashboard data dictionary
        """
        return {
            "config": self.dashboard_config.dict(),
            "widget_data": self.widget_data,
            "current_metrics": self.current_metrics.dict() if self.current_metrics else None,
            "current_health_status": self.current_health_status.value,
            "current_alerts": [alert.dict() for alert in self.current_alerts],
            "last_updated": datetime.now().isoformat()
        }

    def export_dashboard_config(self) -> str:
        """
        Export dashboard configuration

        Returns:
            JSON string of dashboard configuration
        """
        return json.dumps(self.dashboard_config.dict(), indent=2)

    def import_dashboard_config(self, config_json: str):
        """
        Import dashboard configuration

        Args:
            config_json: JSON configuration string
        """
        try:
            config_data = json.loads(config_json)
            self.dashboard_config = DashboardConfig(**config_data)
            logger.info("Dashboard configuration imported successfully")
        except Exception as e:
            logger.error(f"Error importing dashboard configuration: {e}")
            raise

    def add_widget(self, widget: DashboardWidget):
        """Add a new widget to the dashboard"""
        self.dashboard_config.widgets.append(widget)
        logger.info(f"Added widget: {widget.widget_id}")

    def remove_widget(self, widget_id: str):
        """Remove a widget from the dashboard"""
        self.dashboard_config.widgets = [
            w for w in self.dashboard_config.widgets if w.widget_id != widget_id
        ]
        logger.info(f"Removed widget: {widget_id}")

    def get_widget_data(self, widget_id: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific widget"""
        return self.widget_data.get(widget_id)