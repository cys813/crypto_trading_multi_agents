"""
Example usage of the monitoring system
"""

import asyncio
import json
from datetime import datetime, timedelta
from src.long_analyst.monitoring import (
    MonitoringManager,
    MonitoringConfig,
    AlertRule,
    AlertSeverity,
    RuleType
)


async def monitoring_example():
    """Example of using the monitoring system"""
    print("=== Monitoring System Example ===")

    # Create monitoring configuration
    config = MonitoringConfig(
        collection_interval=timedelta(seconds=10),  # Faster for demo
        alert_check_interval=timedelta(seconds=20),
        dashboard_refresh_interval=timedelta(seconds=5),
        max_latency_ms=2.0,  # 2 seconds
        max_error_rate=0.05,  # 5%
        alert_channels=["log"],  # Only log alerts for demo
        storage_backend="memory"
    )

    # Create monitoring manager
    manager = MonitoringManager(config)

    try:
        # Start monitoring
        print("Starting monitoring system...")
        await manager.start()

        # Let it run for a short time to collect some metrics
        print("Collecting metrics for 30 seconds...")
        await asyncio.sleep(30)

        # Get system status
        print("\nSystem Status:")
        status = manager.get_system_status()
        print(json.dumps(status, indent=2))

        # Get metrics history
        print(f"\nMetrics History: {len(manager.metrics_history)} entries")
        if manager.metrics_history:
            latest = manager.metrics_history[-1]
            print(f"Latest metrics timestamp: {latest.timestamp}")
            print(f"Processing latency: {latest.performance.data_processing_latency * 1000:.1f}ms")
            print(f"Throughput: {latest.performance.throughput_requests_per_second:.1f} req/s")
            print(f"Error rate: {latest.performance.concurrency_stats.error_rate:.2%}")
            print(f"CPU usage: {latest.performance.resource_usage.cpu_percent:.1f}%")
            print(f"Memory usage: {latest.performance.resource_usage.memory_percent:.1f}%")
            print(f"System health: {latest.health.overall_status}")

        # Generate monitoring report
        print("\nGenerating monitoring report...")
        report = await manager.generate_report("1h")
        print(f"Report generated: {report.report_id}")
        print(f"Period: {report.period_start} to {report.period_end}")
        print(f"Summary: {report.summary}")

        # Get active alerts
        print(f"\nActive alerts: {len(manager.get_active_alerts())}")
        active_alerts = manager.get_active_alerts()
        for alert in active_alerts:
            print(f"  - {alert.title} ({alert.severity})")

        # Get alert summary
        print("\nAlert Summary:")
        summary = manager.get_alert_summary()
        print(json.dumps(summary, indent=2))

        # Track some requests for demonstration
        print("\nTracking some requests...")
        manager.collectors['performance'].track_request_start("request_1")
        await asyncio.sleep(0.1)
        manager.collectors['performance'].track_request_end("request_1", 0.1)

        manager.collectors['performance'].track_request_start("request_2")
        await asyncio.sleep(0.05)
        manager.collectors['performance'].track_request_end("request_2", 0.05, error=True)

        manager.collectors['performance'].track_request_start("request_3")
        await asyncio.sleep(0.2)
        manager.collectors['performance'].track_request_end("request_3", 0.2)

        # Track some signals
        manager.collectors['business'].track_signal({
            'symbol': 'BTCUSDT',
            'signal_type': 'BUY',
            'confidence': 0.8,
            'success': True
        })

        manager.collectors['business'].track_signal({
            'symbol': 'ETHUSDT',
            'signal_type': 'SELL',
            'confidence': 0.6,
            'success': False
        })

        # Track some reports
        manager.collectors['business'].track_report({
            'symbol': 'BTCUSDT',
            'report_type': 'STANDARD',
            'generation_time': 1.5
        })

        # Let it collect more metrics
        print("Collecting more metrics...")
        await asyncio.sleep(10)

        # Get updated status
        print("\nUpdated System Status:")
        updated_status = manager.get_system_status()
        print(f"Metrics collected: {updated_status['metrics_collected']}")
        print(f"Active alerts: {updated_status['active_alerts_count']}")

        # Generate dashboard
        print("\nGenerating dashboard...")
        dashboard_html = await manager.dashboard.render_dashboard()
        with open("monitoring_dashboard.html", "w", encoding="utf-8") as f:
            f.write(dashboard_html)
        print("Dashboard saved to monitoring_dashboard.html")

        # Stop monitoring
        print("\nStopping monitoring system...")
        await manager.stop()

        print("Monitoring example completed successfully!")

    except Exception as e:
        print(f"Error in monitoring example: {e}")
        raise


async def alert_management_example():
    """Example of alert management"""
    print("\n=== Alert Management Example ===")

    config = MonitoringConfig()
    manager = MonitoringManager(config)

    try:
        await manager.start()

        # Add a custom alert rule
        custom_rule = AlertRule(
            id="custom_latency_alert",
            name="Custom High Latency Alert",
            description="Processing latency exceeds custom threshold",
            rule_type=RuleType.THRESHOLD,
            metric_name="data_processing_latency",
            condition="value > threshold",
            threshold=1.0,  # 1 second
            duration=timedelta(minutes=1),
            severity=AlertSeverity.HIGH,
            enabled=True,
            tags=["custom", "latency"]
        )

        manager.alert_manager.add_rule(custom_rule)
        print("Added custom alert rule")

        # List all rules
        print(f"\nTotal alert rules: {len(manager.alert_manager.rules)}")
        for rule_id, rule in manager.alert_manager.rules.items():
            print(f"  - {rule_id}: {rule.name} ({'enabled' if rule.enabled else 'disabled'})")

        # Simulate some metrics that would trigger alerts
        print("\nSimulating high latency metrics...")
        await asyncio.sleep(2)  # Let it collect some baseline metrics

        # Wait for alert checking
        await asyncio.sleep(25)  # Wait for alert check interval

        # Check for alerts
        active_alerts = manager.get_active_alerts()
        print(f"Active alerts after simulation: {len(active_alerts)}")

        for alert in active_alerts:
            print(f"  Alert: {alert.title}")
            print(f"    Severity: {alert.severity}")
            print(f"    Current Value: {alert.current_value}")
            print(f"    Threshold: {alert.threshold}")
            print(f"    Triggered At: {alert.triggered_at}")

            # Acknowledge the alert
            await manager.acknowledge_alert(alert.id)
            print(f"    Acknowledged: {alert.acknowledged_at is not None}")

        # Suppress a rule
        print("\nSuppressing high latency rule for 5 minutes...")
        await manager.alert_manager.suppress_alert("high_latency", timedelta(minutes=5), "demo suppression")

        # Check suppressed rules
        print(f"Suppressed rules: {len(manager.alert_manager.alert_suppressions)}")

        # Resolve alerts
        print("\nResolving alerts...")
        for alert in manager.get_active_alerts():
            await manager.resolve_alert(alert.id)
            print(f"  Resolved alert {alert.id}: {alert.resolved_at is not None}")

        await manager.stop()

    except Exception as e:
        print(f"Error in alert management example: {e}")
        raise


async def health_evaluation_example():
    """Example of health evaluation"""
    print("\n=== Health Evaluation Example ===")

    from src.long_analyst.monitoring import HealthEvaluator, MonitoringConfig

    config = MonitoringConfig()
    evaluator = HealthEvaluator(config)

    # Create sample metrics
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
            components_health={'component1': Mock(status="HEALTHY")}
        ),
        business=Mock(),
        timestamp=datetime.now()
    )

    # Evaluate system health
    print("Evaluating system health...")
    health_status = await evaluator.evaluate_system_health(metrics)
    print(f"Overall health status: {health_status}")

    # Evaluate component health
    print("\nEvaluating component health...")
    component_metrics = {
        'error_rate': 0.01,
        'response_time': 0.5,
        'memory_usage': 60
    }
    component_health = await evaluator.evaluate_component_health("test_component", component_metrics)
    print(f"Component health: {component_health.status}")
    print(f"Health score: {component_health.health_score:.2f}")
    print(f"Issues: {component_health.issues}")

    # Evaluate data quality
    print("\nEvaluating data quality...")
    quality_metrics = {
        'completeness_score': 0.9,
        'accuracy_score': 0.85,
        'timeliness_score': 0.95,
        'consistency_score': 0.88
    }
    quality_evaluation = await evaluator.evaluate_data_quality(quality_metrics)
    print(f"Overall quality score: {quality_evaluation['overall_score']:.2f}")
    print("Recommendations:")
    for rec in quality_evaluation['recommendations']:
        print(f"  - {rec}")

    # Get health trends
    print("\nGetting health trends...")
    trends = evaluator.get_health_trends(timedelta(hours=1))
    print(f"Trends: {trends}")


async def dashboard_example():
    """Example of dashboard functionality"""
    print("\n=== Dashboard Example ===")

    from src.long_analyst.monitoring import MonitoringDashboard, MonitoringConfig

    config = MonitoringConfig()
    dashboard = MonitoringDashboard(config)

    # Create sample metrics
    metrics = SystemMetrics(
        performance=Mock(
            data_processing_latency=0.1,
            throughput_requests_per_second=10.0,
            concurrency_stats=Mock(error_rate=0.01),
            resource_usage=Mock(cpu_percent=50, memory_percent=60, disk_percent=70)
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

    # Update dashboard with metrics
    print("Updating dashboard with metrics...")
    await dashboard.update_metrics(metrics)
    await dashboard.update_health_status("HEALTHY")

    # Add some alerts
    from src.long_analyst.monitoring.models import Alert, AlertSeverity
    alerts = [
        Alert(
            id="alert1",
            rule_id="rule1",
            rule_name="Test Rule 1",
            severity=AlertSeverity.HIGH,
            title="High Latency Detected",
            description="Processing latency exceeds threshold",
            metric_name="data_processing_latency",
            current_value=2.5,
            threshold=2.0
        ),
        Alert(
            id="alert2",
            rule_id="rule2",
            rule_name="Test Rule 2",
            severity=AlertSeverity.MEDIUM,
            title="Memory Usage High",
            description="Memory usage exceeds threshold",
            metric_name="memory_percent",
            current_value=85.0,
            threshold=80.0
        )
    ]
    await dashboard.update_alerts(alerts)

    # Get dashboard data
    print("\nDashboard data:")
    dashboard_data = dashboard.get_dashboard_data()
    print(f"  Widget count: {len(dashboard_data['widget_data'])}")
    print(f"  Health status: {dashboard_data['current_health_status']}")

    # Generate dashboard HTML
    print("\nGenerating dashboard HTML...")
    html_content = await dashboard.render_dashboard()
    with open("example_dashboard.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Dashboard saved to example_dashboard.html")

    # Export dashboard configuration
    print("\nExporting dashboard configuration...")
    config_json = dashboard.export_dashboard_config()
    with open("dashboard_config.json", "w") as f:
        f.write(config_json)
    print("Dashboard configuration saved to dashboard_config.json")


async def main():
    """Run all monitoring examples"""
    await monitoring_example()
    await alert_management_example()
    await health_evaluation_example()
    await dashboard_example()

    print("\n=== All Monitoring Examples Completed ===")


if __name__ == "__main__":
    # Mock classes for examples
    from unittest.mock import Mock
    from src.long_analyst.monitoring.models import SystemMetrics, HealthStatus

    asyncio.run(main())