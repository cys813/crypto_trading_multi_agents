"""
Data models for the monitoring system
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class HealthStatus(str, Enum):
    """System health status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class MetricType(str, Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class RuleType(str, Enum):
    """Alert rule types"""
    THRESHOLD = "threshold"
    TREND = "trend"
    ANOMALY = "anomaly"
    AVAILABILITY = "availability"


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class ResourceUsage:
    """System resource usage"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io_bytes: int
    disk_io_bytes: int
    timestamp: datetime


@dataclass
class ConcurrencyStats:
    """Concurrency statistics"""
    active_requests: int
    max_concurrent: int
    total_requests: int
    average_response_time: float
    error_rate: float
    timestamp: datetime


@dataclass
class PerformanceMetrics:
    """Performance metrics"""
    data_processing_latency: float
    indicator_calculation_time: float
    llm_response_time: float
    report_generation_time: float
    throughput_requests_per_second: float
    resource_usage: ResourceUsage
    concurrency_stats: ConcurrencyStats
    timestamp: datetime


@dataclass
class SignalQualityMetrics:
    """Signal quality metrics"""
    signal_accuracy: float
    false_positive_rate: float
    signal_coverage: float
    signal_consistency: float
    timestamp: datetime


@dataclass
class LLMQualityMetrics:
    """LLM quality metrics"""
    response_quality_score: float
    response_time_avg: float
    error_rate: float
    cost_per_request: float
    cache_hit_rate: float
    timestamp: datetime


@dataclass
class DataQualityMetrics:
    """Data quality metrics"""
    completeness_score: float
    accuracy_score: float
    timeliness_score: float
    consistency_score: float
    timestamp: datetime


@dataclass
class QualityMetrics:
    """Quality metrics"""
    signal_quality: SignalQualityMetrics
    llm_quality: LLMQualityMetrics
    data_quality: DataQualityMetrics
    timestamp: datetime


@dataclass
class ServiceHealth:
    """Service health status"""
    service_name: str
    is_healthy: bool
    response_time: float
    error_message: Optional[str] = None
    last_check: datetime = field(default_factory=datetime.now)


@dataclass
class DataSourceHealth:
    """Data source health status"""
    source_name: str
    is_available: bool
    latency: float
    error_rate: float
    last_update: datetime


@dataclass
class ComponentHealth:
    """Component health status"""
    component_name: str
    status: HealthStatus
    health_score: float
    issues: List[str] = field(default_factory=list)
    last_check: datetime = field(default_factory=datetime.now)


@dataclass
class HealthMetrics:
    """Health metrics"""
    overall_status: HealthStatus
    services_health: Dict[str, ServiceHealth]
    data_sources_health: Dict[str, DataSourceHealth]
    components_health: Dict[str, ComponentHealth]
    uptime_percentage: float
    timestamp: datetime


@dataclass
class BusinessMetrics:
    """Business metrics"""
    total_signals_generated: int
    successful_signals: int
    average_signal_confidence: float
    total_reports_generated: int
    user_satisfaction_score: float
    timestamp: datetime


class SystemMetrics(BaseModel):
    """Complete system metrics"""
    performance: PerformanceMetrics
    quality: QualityMetrics
    health: HealthMetrics
    business: BusinessMetrics
    timestamp: datetime = Field(default_factory=datetime.now)


class AlertRule(BaseModel):
    """Alert rule definition"""
    id: str
    name: str
    description: str
    rule_type: RuleType
    metric_name: str
    condition: str  # e.g., "value > threshold"
    threshold: float
    duration: timedelta = Field(default=timedelta(minutes=5))
    severity: AlertSeverity = AlertSeverity.MEDIUM
    enabled: bool = True
    tags: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class Alert(BaseModel):
    """Alert instance"""
    id: str
    rule_id: str
    rule_name: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.ACTIVE
    title: str
    description: str
    metric_name: str
    current_value: float
    threshold: float
    triggered_at: datetime = Field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class MonitoringConfig(BaseModel):
    """Monitoring configuration"""
    collection_interval: timedelta = Field(default=timedelta(seconds=30))
    retention_period: timedelta = Field(default=timedelta(days=30))
    alert_check_interval: timedelta = Field(default=timedelta(seconds=60))
    dashboard_refresh_interval: timedelta = Field(default=timedelta(seconds=10))

    # Performance thresholds
    max_latency_ms: float = Field(default=5000.0)
    max_error_rate: float = Field(default=0.05)  # 5%
    min_availability: float = Field(default=0.99)  # 99%

    # Alert channels
    alert_channels: List[str] = Field(default_factory=lambda: ["log"])
    webhook_url: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    email_recipients: List[str] = Field(default_factory=list)

    # Storage backend
    storage_backend: str = Field(default="memory")  # memory, redis, influxdb
    storage_config: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


@dataclass
class MonitoringReport:
    """Monitoring report"""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    summary: Dict[str, Any]
    performance_summary: Dict[str, Any]
    quality_summary: Dict[str, Any]
    health_summary: Dict[str, Any]
    alerts_summary: Dict[str, Any]
    recommendations: List[str]


@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""
    widget_id: str
    widget_type: str  # gauge, chart, table, etc.
    title: str
    data_source: str
    config: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, int] = field(default_factory=dict)  # row, col


@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    dashboard_id: str
    title: str
    refresh_interval: timedelta
    widgets: List[DashboardWidget]
    layout: Dict[str, Any] = field(default_factory=dict)


class FaultRecoveryStrategy(BaseModel):
    """Fault recovery strategy"""
    strategy_id: str
    name: str
    description: str
    fault_type: str
    recovery_steps: List[str]
    max_retries: int = 3
    retry_delay: timedelta = Field(default=timedelta(seconds=5))
    enabled: bool = True


@dataclass
class RecoveryEvent:
    """Recovery event"""
    event_id: str
    fault_type: str
    strategy_id: str
    component_name: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    successful: bool = False
    error_message: Optional[str] = None
    retry_count: int = 0