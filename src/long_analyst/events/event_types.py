"""
Event types and definitions for the Long Analyst Agent.

Defines the structure and types of events used throughout the system
for communication and coordination between components.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
import uuid
import json


class EventType(Enum):
    """Event types used in the system."""
    # Analysis events
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"
    ANALYSIS_TIMEOUT = "analysis_timeout"

    # Market data events
    MARKET_DATA_RECEIVED = "market_data_received"
    MARKET_DATA_UPDATED = "market_data_updated"
    MARKET_DATA_ERROR = "market_data_error"

    # Signal events
    SIGNAL_GENERATED = "signal_generated"
    SIGNAL_TRIGGERED = "signal_triggered"
    SIGNAL_EXPIRED = "signal_expired"
    SIGNAL_CANCELLED = "signal_cancelled"

    # Technical analysis events
    TECHNICAL_ANALYSIS_STARTED = "technical_analysis_started"
    TECHNICAL_ANALYSIS_COMPLETED = "technical_analysis_completed"
    INDICATOR_CALCULATED = "indicator_calculated"
    PATTERN_DETECTED = "pattern_detected"

    # LLM analysis events
    LLM_ANALYSIS_STARTED = "llm_analysis_started"
    LLM_ANALYSIS_COMPLETED = "llm_analysis_completed"
    LLM_CONTEXT_UPDATED = "llm_context_updated"
    LLM_ERROR = "llm_error"

    # Performance events
    PERFORMANCE_METRICS_UPDATED = "performance_metrics_updated"
    HEALTH_CHECK_COMPLETED = "health_check_completed"
    ERROR_OCCURRED = "error_occurred"
    WARNING_ISSUED = "warning_issued"

    # System events
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    SYSTEM_ERROR = "system_error"

    # Data storage events
    DATA_STORED = "data_stored"
    DATA_RETRIEVED = "data_retrieved"
    DATA_DELETED = "data_deleted"
    DATA_BACKUP_COMPLETED = "data_backup_completed"

    # External integration events
    EXTERNAL_API_CALL = "external_api_call"
    EXTERNAL_API_RESPONSE = "external_api_response"
    EXTERNAL_API_ERROR = "external_api_error"


class EventPriority(Enum):
    """Event priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class EventStatus(Enum):
    """Event processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class Event:
    """
    Base event class for the event-driven system.

    All events in the system inherit from this base class,
    providing a consistent structure for event handling.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.SYSTEM_ERROR
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    priority: EventPriority = EventPriority.NORMAL
    status: EventStatus = EventStatus.PENDING

    # Event payload
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Event routing
    source: str = "system"
    target: Optional[str] = None
    correlation_id: Optional[str] = None

    # Retry and error handling
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None

    # Performance tracking
    processing_start_time: Optional[float] = None
    processing_end_time: Optional[float] = None
    processing_duration: Optional[float] = None

    def __post_init__(self):
        """Validate event data."""
        if not self.source:
            raise ValueError("Event source cannot be empty")

    @property
    def age_seconds(self) -> float:
        """Get event age in seconds."""
        return datetime.now().timestamp() - self.timestamp

    @property
    def is_expired(self) -> bool:
        """Check if event has expired."""
        return self.age_seconds > 3600  # 1 hour expiry

    @property
    def should_retry(self) -> bool:
        """Check if event should be retried."""
        return (self.status == EventStatus.FAILED and
                self.retry_count < self.max_retries and
                not self.is_expired)

    def start_processing(self):
        """Mark event as processing started."""
        self.status = EventStatus.PROCESSING
        self.processing_start_time = datetime.now().timestamp()

    def complete_processing(self):
        """Mark event as processing completed."""
        self.status = EventStatus.COMPLETED
        self.processing_end_time = datetime.now().timestamp()
        if self.processing_start_time:
            self.processing_duration = self.processing_end_time - self.processing_start_time

    def fail_processing(self, error_message: str, stack_trace: Optional[str] = None):
        """Mark event as processing failed."""
        self.status = EventStatus.FAILED
        self.error_message = error_message
        self.stack_trace = stack_trace
        self.processing_end_time = datetime.now().timestamp()
        if self.processing_start_time:
            self.processing_duration = self.processing_end_time - self.processing_start_time

    def retry_processing(self):
        """Mark event for retry."""
        self.status = EventStatus.RETRYING
        self.retry_count += 1
        self.error_message = None
        self.stack_trace = None
        self.processing_start_time = None
        self.processing_end_time = None
        self.processing_duration = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "priority": self.priority.value,
            "status": self.status.value,
            "data": self.data,
            "metadata": self.metadata,
            "source": self.source,
            "target": self.target,
            "correlation_id": self.correlation_id,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "processing_start_time": self.processing_start_time,
            "processing_end_time": self.processing_end_time,
            "processing_duration": self.processing_duration
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        return cls(
            id=data["id"],
            event_type=EventType(data["event_type"]),
            timestamp=data["timestamp"],
            priority=EventPriority(data["priority"]),
            status=EventStatus(data["status"]),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            source=data.get("source", "system"),
            target=data.get("target"),
            correlation_id=data.get("correlation_id"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            error_message=data.get("error_message"),
            stack_trace=data.get("stack_trace"),
            processing_start_time=data.get("processing_start_time"),
            processing_end_time=data.get("processing_end_time"),
            processing_duration=data.get("processing_duration")
        )

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        """Create event from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def copy(self) -> "Event":
        """Create a copy of the event."""
        return Event.from_dict(self.to_dict())

    def __str__(self) -> str:
        """String representation of the event."""
        return f"Event({self.event_type.value}, source={self.source}, status={self.status.value})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"Event(id={self.id[:8]}..., type={self.event_type.value}, "
                f"source={self.source}, priority={self.priority.value}, "
                f"status={self.status.value}, age={self.age_seconds:.1f}s)")


# Factory functions for creating common events
def create_analysis_started_event(symbol: str, timeframe: str, correlation_id: Optional[str] = None) -> Event:
    """Create an analysis started event."""
    return Event(
        event_type=EventType.ANALYSIS_STARTED,
        priority=EventPriority.NORMAL,
        data={
            "symbol": symbol,
            "timeframe": timeframe,
            "action": "start"
        },
        source="analysis_engine",
        correlation_id=correlation_id
    )


def create_analysis_completed_event(symbol: str, signals_count: int, processing_time: float,
                                  correlation_id: Optional[str] = None) -> Event:
    """Create an analysis completed event."""
    return Event(
        event_type=EventType.ANALYSIS_COMPLETED,
        priority=EventPriority.NORMAL,
        data={
            "symbol": symbol,
            "signals_count": signals_count,
            "processing_time_ms": processing_time,
            "action": "complete"
        },
        source="analysis_engine",
        correlation_id=correlation_id
    )


def create_signal_generated_event(signal_id: str, symbol: str, signal_type: str, strength: float,
                                 correlation_id: Optional[str] = None) -> Event:
    """Create a signal generated event."""
    return Event(
        event_type=EventType.SIGNAL_GENERATED,
        priority=EventPriority.HIGH,
        data={
            "signal_id": signal_id,
            "symbol": symbol,
            "signal_type": signal_type,
            "strength": strength,
            "action": "generate"
        },
        source="signal_generator",
        correlation_id=correlation_id
    )


def create_error_event(error_message: str, source: str, stack_trace: Optional[str] = None,
                      correlation_id: Optional[str] = None) -> Event:
    """Create an error event."""
    return Event(
        event_type=EventType.ERROR_OCCURRED,
        priority=EventPriority.CRITICAL,
        data={
            "error": error_message,
            "action": "error"
        },
        source=source,
        correlation_id=correlation_id,
        error_message=error_message,
        stack_trace=stack_trace
    )


def create_market_data_event(symbol: str, data_type: str, price: float, volume: float,
                           correlation_id: Optional[str] = None) -> Event:
    """Create a market data event."""
    return Event(
        event_type=EventType.MARKET_DATA_RECEIVED,
        priority=EventPriority.NORMAL,
        data={
            "symbol": symbol,
            "data_type": data_type,
            "price": price,
            "volume": volume,
            "action": "receive"
        },
        source="market_data_manager",
        correlation_id=correlation_id
    )


def create_performance_event(metric_name: str, value: float, timestamp: Optional[float] = None) -> Event:
    """Create a performance metrics event."""
    return Event(
        event_type=EventType.PERFORMANCE_METRICS_UPDATED,
        priority=EventPriority.LOW,
        data={
            "metric_name": metric_name,
            "value": value,
            "timestamp": timestamp or datetime.now().timestamp(),
            "action": "update"
        },
        source="performance_monitor"
    )


def create_health_check_event(component: str, status: str, metrics: Dict[str, Any]) -> Event:
    """Create a health check event."""
    return Event(
        event_type=EventType.HEALTH_CHECK_COMPLETED,
        priority=EventPriority.NORMAL,
        data={
            "component": component,
            "status": status,
            "metrics": metrics,
            "action": "health_check"
        },
        source="health_monitor"
    )