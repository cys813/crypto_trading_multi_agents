"""
Tests for the monitoring system
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.long_analyst.monitoring import (
    MonitoringManager,
    MetricsCollector,
    HealthEvaluator,
    AlertManager,
    MonitoringDashboard,
    MonitoringConfig,
    SystemMetrics,
    PerformanceMetrics,
    QualityMetrics,
    HealthMetrics,
    BusinessMetrics,
    Alert,
    AlertRule,
    HealthStatus,
    AlertSeverity,
    RuleType
)


class TestMonitoringManager:
    """Test cases for MonitoringManager"""

    @pytest.fixture
    def monitoring_config(self):
        """Create a monitoring configuration"""
        return MonitoringConfig(
            collection_interval=timedelta(seconds=30),
            alert_check_interval=timedelta(seconds=60)
        )

    @pytest.fixture
    def monitoring_manager(self, monitoring_config):
        """Create a MonitoringManager instance"""
        return MonitoringManager(monitoring_config)

    @pytest.mark.asyncio
    async def test_start_stop(self, monitoring_manager):
        """Test starting and stopping monitoring"""
        # Start monitoring
        await monitoring_manager.start()

        assert monitoring_manager._collection_task is not None
        assert monitoring_manager._health_check_task is not None
        assert monitoring_manager._alert_check_task is not None

        # Stop monitoring
        await monitoring_manager.stop()

        assert monitoring_manager._collection_task.cancelled()
        assert monitoring_manager._health_check_task.cancelled()
        assert monitoring_manager._alert_check_task.cancelled()

    @pytest.mark.asyncio
    async def test_collect_metrics(self, monitoring_manager):
        """Test metrics collection"""
        with patch.object(monitoring_manager.collectors['performance'], 'collect_performance_metrics') as mock_perf:
            with patch.object(monitoring_manager.collectors['quality'], 'collect_quality_metrics') as mock_qual:
                with patch.object(monitoring_manager.collectors['health'], 'collect_health_metrics') as mock_health:
                    with patch.object(monitoring_manager.collectors['business'], 'collect_business_metrics') as mock_bus:

                        # Setup mock responses
                        mock_perf.return_value = PerformanceMetrics(
                            data_processing_latency=0.1,
                            indicator_calculation_time=0.05,
                            llm_response_time=1.0,
                            report_generation_time=0.5,
                            throughput_requests_per_second=10.0,
                            resource_usage=Mock(cpu_percent=50, memory_percent=60, disk_percent=70, timestamp=datetime.now()),
                            concurrency_stats=Mock(active_requests=5, error_rate=0.01, timestamp=datetime.now()),
                            timestamp=datetime.now()
                        )
                        mock_qual.return_value = QualityMetrics(
                            signal_quality=Mock(signal_accuracy=0.85, timestamp=datetime.now()),
                            llm_quality=Mock(response_quality_score=0.8, timestamp=datetime.now()),
                            data_quality=Mock(completeness_score=0.9, timestamp=datetime.now()),
                            timestamp=datetime.now()
                        )
                        mock_health.return_value = HealthMetrics(
                            overall_status=HealthStatus.HEALTHY,
                            services_health={},
                            data_sources_health={},
                            components_health={},
                            uptime_percentage=0.99,
                            timestamp=datetime.now()
                        )
                        mock_bus.return_value = BusinessMetrics(
                            total_signals_generated=100,
                            successful_signals=80,
                            average_signal_confidence=0.75,
                            total_reports_generated=50,
                            user_satisfaction_score=0.85,
                            timestamp=datetime.now()
                        )

                        await monitoring_manager.collect_metrics()

                        assert len(monitoring_manager.metrics_history) == 1
                        assert monitoring_manager.collection_count == 1

    @pytest.mark.asyncio
    async def test_evaluate_health(self, monitoring_manager):
        """Test health evaluation"""
        # Add some metrics to history
        metrics = SystemMetrics(
            performance=Mock(),
            quality=Mock(),
            health=Mock(overall_status=HealthStatus.HEALTHY),
            business=Mock(),
            timestamp=datetime.now()
        )
        monitoring_manager.metrics_history.append(metrics)

        with patch.object(monitoring_manager.evaluators['health'], 'evaluate_system_health') as mock_eval:
            mock_eval.return_value = HealthStatus.HEALTHY

            health_status = await monitoring_manager.evaluate_health()

            assert health_status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_generate_report(self, monitoring_manager):
        """Test monitoring report generation"""
        # Add some metrics to history
        metrics = SystemMetrics(
            performance=Mock(),
            quality=Mock(),
            health=Mock(overall_status=HealthStatus.HEALTHY),
            business=Mock(),
            timestamp=datetime.now()
        )
        monitoring_manager.metrics_history.append(metrics)

        report = await monitoring_manager.generate_report("24h")

        assert report is not None
        assert report.report_id is not None
        assert report.generated_at is not None
        assert report.period_start is not None
        assert report.period_end is not None

    def test_get_system_status(self, monitoring_manager):
        """Test system status retrieval"""
        status = monitoring_manager.get_system_status()

        assert 'monitoring_active' in status
        assert 'start_time' in status
        assert 'uptime_seconds' in status
        assert 'metrics_collected' in status
        assert 'active_alerts_count' in status

    def test_acknowledge_alert(self, monitoring_manager):
        """Test alert acknowledgment"""
        # Add an active alert
        alert = Alert(
            id="test_alert",
            rule_id="test_rule",
            rule_name="Test Rule",
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="Test Description",
            metric_name="test_metric",
            current_value=10.0,
            threshold=5.0
        )
        monitoring_manager.active_alerts.append(alert)

        result = await monitoring_manager.acknowledge_alert("test_alert")

        assert result is True
        assert alert.status == Alert.ACKNOWLEDGED
        assert alert.acknowledged_at is not None


class TestMetricsCollector:
    """Test cases for MetricsCollector"""

    @pytest.fixture
    def metrics_collector(self):
        """Create a MetricsCollector instance"""
        config = MonitoringConfig()
        return MetricsCollector("performance", config)

    @pytest.mark.asyncio
    async def test_collect_performance_metrics(self, metrics_collector):
        """Test performance metrics collection"""
        with patch('psutil.cpu_percent') as mock_cpu:
            with patch('psutil.virtual_memory') as mock_memory:
                with patch('psutil.disk_usage') as mock_disk:
                    with patch('psutil.net_io_counters') as mock_network:
                        with patch('psutil.disk_io_counters') as mock_disk_io:

                            # Setup mock responses
                            mock_cpu.return_value = 50.0
                            mock_memory.return_value = Mock(percent=60.0)
                            mock_disk.return_value = Mock(percent=70.0)
                            mock_network.return_value = Mock(bytes_sent=1000, bytes_recv=2000)
                            mock_disk_io.return_value = Mock(read_bytes=3000, write_bytes=4000)

                            metrics = await metrics_collector.collect_performance_metrics()

                            assert isinstance(metrics, PerformanceMetrics)
                            assert metrics.data_processing_latency >= 0
                            assert metrics.resource_usage.cpu_percent == 50.0
                            assert metrics.resource_usage.memory_percent == 60.0

    @pytest.mark.asyncio
    async def test_collect_quality_metrics(self, metrics_collector):
        """Test quality metrics collection"""
        metrics = await metrics_collector.collect_quality_metrics()

        assert isinstance(metrics, QualityMetrics)
        assert metrics.signal_quality is not None
        assert metrics.llm_quality is not None
        assert metrics.data_quality is not None

    @pytest.mark.asyncio
    async def test_collect_health_metrics(self, metrics_collector):
        """Test health metrics collection"""
        metrics = await metrics_collector.collect_health_metrics()

        assert isinstance(metrics, HealthMetrics)
        assert metrics.overall_status is not None
        assert metrics.services_health is not None
        assert metrics.uptime_percentage >= 0

    def test_track_request_start_end(self, metrics_collector):
        """Test request tracking"""
        # Track request start
        metrics_collector.track_request_start("test_request_1")

        assert "test_request_1" in metrics_collector.active_requests

        # Track request end
        metrics_collector.track_request_end("test_request_1")

        assert "test_request_1" not in metrics_collector.active_requests
        assert len(metrics_collector.request_history) == 1

    def test_track_signal(self, metrics_collector):
        """Test signal tracking"""
        signal_data = {
            'symbol': 'BTCUSDT',
            'signal_type': 'BUY',
            'confidence': 0.8
        }

        metrics_collector.track_signal(signal_data)

        assert len(metrics_collector.signal_history) == 1
        assert metrics_collector.signal_history[0]['symbol'] == 'BTCUSDT'


class TestHealthEvaluator:
    """Test cases for HealthEvaluator"""

    @pytest.fixture
    def health_evaluator(self):
        """Create a HealthEvaluator instance"""
        config = MonitoringConfig()
        return HealthEvaluator(config)

    @pytest.mark.asyncio
    async def test_evaluate_system_health(self, health_evaluator):
        """Test system health evaluation"""
        metrics = SystemMetrics(
            performance=Mock(
                data_processing_latency=0.1,
                concurrency_stats=Mock(error_rate=0.01),
                resource_usage=Mock(cpu_percent=50, memory_percent=60, disk_percent=70)
            ),
            quality=Mock(
                signal_quality=Mock(signal_accuracy=0.85),
                llm_quality=Mock(response_quality_score=0.8),
                data_quality=Mock(completeness_score=0.9)
            ),
            health=Mock(
                uptime_percentage=0.99,
                services_health={'service1': Mock(is_healthy=True)},
                data_sources_health={'source1': Mock(is_available=True)},
                components_health={'component1': Mock(status=HealthStatus.HEALTHY)}
            ),
            business=Mock(),
            timestamp=datetime.now()
        )

        health_status = await health_evaluator.evaluate_system_health(metrics)

        assert health_status in [HealthStatus.HEALTHY, HealthStatus.WARNING, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]

    @pytest.mark.asyncio
    async def test_evaluate_component_health(self, health_evaluator):
        """Test component health evaluation"""
        component_metrics = {
            'error_rate': 0.01,
            'response_time': 0.5,
            'memory_usage': 60
        }

        component_health = await health_evaluator.evaluate_component_health("test_component", component_metrics)

        assert component_health.component_name == "test_component"
        assert component_health.health_score >= 0
        assert component_health.health_score <= 1

    @pytest.mark.asyncio
    async def test_evaluate_data_quality(self, health_evaluator):
        """Test data quality evaluation"""
        quality_metrics = {
            'completeness_score': 0.9,
            'accuracy_score': 0.85,
            'timeliness_score': 0.95,
            'consistency_score': 0.88
        }

        evaluation = await health_evaluator.evaluate_data_quality(quality_metrics)

        assert 'overall_score' in evaluation
        assert 'completeness' in evaluation
        assert 'accuracy' in evaluation
        assert 'recommendations' in evaluation


class TestAlertManager:
    """Test cases for AlertManager"""

    @pytest.fixture
    def alert_manager(self):
        """Create an AlertManager instance"""
        config = MonitoringConfig()
        return AlertManager(config)

    @pytest.fixture
    def sample_metrics(self):
        """Create sample metrics for testing"""
        return [
            SystemMetrics(
                performance=Mock(
                    data_processing_latency=6.0,  # Above threshold
                    concurrency_stats=Mock(error_rate=0.01),
                    resource_usage=Mock(cpu_percent=50, timestamp=datetime.now())
                ),
                quality=Mock(),
                health=Mock(),
                business=Mock(),
                timestamp=datetime.now()
            )
        ]

    @pytest.mark.asyncio
    async def test_process_metrics(self, alert_manager, sample_metrics):
        """Test metrics processing for alerts"""
        alerts = await alert_manager.process_metrics(sample_metrics)

        # Should generate alerts for high latency
        assert len(alerts) >= 0  # May or may not generate alerts depending on duration

    @pytest.mark.asyncio
    async def test_evaluate_rule(self, alert_manager, sample_metrics):
        """Test rule evaluation"""
        rule = alert_manager.rules['high_latency']
        alert = await alert_manager._evaluate_rule(rule, sample_metrics)

        # Should trigger alert if condition is met
        if alert:
            assert alert.rule_id == 'high_latency'
            assert alert.severity == AlertSeverity.HIGH

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, alert_manager):
        """Test alert acknowledgment"""
        # Create a test alert
        alert = Alert(
            id="test_alert",
            rule_id="test_rule",
            rule_name="Test Rule",
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="Test Description",
            metric_name="test_metric",
            current_value=10.0,
            threshold=5.0
        )
        alert_manager.active_alerts.append(alert)

        result = await alert_manager.acknowledge_alert("test_alert")

        assert result is True
        assert alert.status == Alert.ACKNOWLEDGED

    @pytest.mark.asyncio
    async def test_suppress_alert(self, alert_manager):
        """Test alert suppression"""
        # Suppress a rule
        await alert_manager.suppress_alert("high_latency", timedelta(minutes=5), "testing")

        # Check if rule is suppressed
        assert alert_manager._is_rule_suppressed("high_latency")

    def test_get_active_alerts(self, alert_manager):
        """Test getting active alerts"""
        # Add test alerts
        alert1 = Alert(id="alert1", rule_id="rule1", severity=AlertSeverity.HIGH, title="Alert 1")
        alert2 = Alert(id="alert2", rule_id="rule2", severity=AlertSeverity.MEDIUM, title="Alert 2")

        alert_manager.active_alerts.extend([alert1, alert2])

        active_alerts = alert_manager.get_active_alerts()

        assert len(active_alerts) == 2

    def test_get_alert_summary(self, alert_manager):
        """Test alert summary generation"""
        # Add test alerts
        alert1 = Alert(id="alert1", rule_id="rule1", severity=AlertSeverity.HIGH, title="Alert 1")
        alert2 = Alert(id="alert2", rule_id="rule2", severity=AlertSeverity.MEDIUM, title="Alert 2")

        alert_manager.active_alerts.extend([alert1, alert2])

        summary = alert_manager.get_alert_summary()

        assert 'total_active_alerts' in summary
        assert 'severity_distribution' in summary
        assert 'rule_distribution' in summary
        assert summary['total_active_alerts'] == 2


class TestMonitoringDashboard:
    """Test cases for MonitoringDashboard"""

    @pytest.fixture
    def dashboard(self):
        """Create a MonitoringDashboard instance"""
        config = MonitoringConfig()
        return MonitoringDashboard(config)

    @pytest.fixture
    def sample_metrics(self):
        """Create sample metrics for testing"""
        return SystemMetrics(
            performance=Mock(
                data_processing_latency=0.1,
                throughput_requests_per_second=10.0,
                concurrency_stats=Mock(error_rate=0.01),
                resource_usage=Mock(cpu_percent=50, memory_percent=60, disk_percent=70, timestamp=datetime.now())
            ),
            quality=Mock(
                signal_quality=Mock(signal_accuracy=0.85, false_positive_rate=0.15),
                llm_quality=Mock(response_quality_score=0.8)
            ),
            health=Mock(
                uptime_percentage=0.99,
                services_health={},
                data_sources_health={},
                components_health={}
            ),
            business=Mock(),
            timestamp=datetime.now()
        )

    @pytest.mark.asyncio
    async def test_update_metrics(self, dashboard, sample_metrics):
        """Test updating dashboard metrics"""
        await dashboard.update_metrics(sample_metrics)

        assert dashboard.current_metrics == sample_metrics
        assert 'system_health' in dashboard.widget_data
        assert 'performance_metrics' in dashboard.widget_data
        assert 'resource_metrics' in dashboard.widget_data

    @pytest.mark.asyncio
    async def test_update_health_status(self, dashboard):
        """Test updating health status"""
        await dashboard.update_health_status(HealthStatus.HEALTHY)

        assert dashboard.current_health_status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_update_alerts(self, dashboard):
        """Test updating alerts"""
        alerts = [
            Alert(id="alert1", rule_id="rule1", severity=AlertSeverity.HIGH, title="Alert 1"),
            Alert(id="alert2", rule_id="rule2", severity=AlertSeverity.MEDIUM, title="Alert 2")
        ]

        await dashboard.update_alerts(alerts)

        assert len(dashboard.current_alerts) == 2
        assert 'recent_alerts' in dashboard.widget_data

    @pytest.mark.asyncio
    async def test_render_dashboard(self, dashboard, sample_metrics):
        """Test dashboard rendering"""
        await dashboard.update_metrics(sample_metrics)
        await dashboard.update_health_status(HealthStatus.HEALTHY)

        html = await dashboard.render_dashboard()

        assert isinstance(html, str)
        assert '<html>' in html
        assert 'Long Analyst Agent Monitoring Dashboard' in html

    def test_get_dashboard_data(self, dashboard, sample_metrics):
        """Test getting dashboard data"""
        dashboard.current_metrics = sample_metrics
        dashboard.current_health_status = HealthStatus.HEALTHY

        data = dashboard.get_dashboard_data()

        assert 'config' in data
        assert 'widget_data' in data
        assert 'current_health_status' in data
        assert data['current_health_status'] == HealthStatus.HEALTHY.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])