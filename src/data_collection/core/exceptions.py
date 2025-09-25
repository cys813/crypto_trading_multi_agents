"""
Comprehensive error handling system for the data collection agent.

This module provides:
- Custom exception classes for different error types
- Error codes and standardized error responses
- Error recovery and retry mechanisms
- Error statistics and monitoring
- Global exception handling
- Error alerting and notifications
"""

import traceback
import sys
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio
import threading
from functools import wraps
import json
from contextlib import contextmanager

from .logger import get_logger


class ErrorCode(Enum):
    """Standardized error codes for the application."""

    # Configuration errors (1000-1999)
    CONFIG_INVALID = "CONFIG_001"
    CONFIG_MISSING = "CONFIG_002"
    CONFIG_ENCRYPTION = "CONFIG_003"
    CONFIG_VALIDATION = "CONFIG_004"

    # Database errors (2000-2999)
    DATABASE_CONNECTION = "DB_001"
    DATABASE_QUERY = "DB_002"
    DATABASE_TIMEOUT = "DB_003"
    DATABASE_CONSTRAINT = "DB_004"
    DATABASE_MIGRATION = "DB_005"

    # Exchange errors (3000-3999)
    EXCHANGE_CONNECTION = "EX_001"
    EXCHANGE_API = "EX_002"
    EXCHANGE_RATE_LIMIT = "EX_003"
    EXCHANGE_AUTH = "EX_004"
    EXCHANGE_MARKET = "EX_005"
    EXCHANGE_ORDER = "EX_006"

    # Network errors (4000-4999)
    NETWORK_TIMEOUT = "NET_001"
    NETWORK_CONNECTION = "NET_002"
    NETWORK_DNS = "NET_003"
    NETWORK_SSL = "NET_004"

    # Data errors (5000-5999)
    DATA_VALIDATION = "DATA_001"
    DATA_QUALITY = "DATA_002"
    DATA_FORMAT = "DATA_003"
    DATA_MISSING = "DATA_004"
    DATA_CONSISTENCY = "DATA_005"

    # System errors (6000-6999)
    SYSTEM_MEMORY = "SYS_001"
    SYSTEM_DISK = "SYS_002"
    SYSTEM_CPU = "SYS_003"
    SYSTEM_PERFORMANCE = "SYS_004"

    # Business logic errors (7000-7999)
    BUSINESS_VALIDATION = "BIZ_001"
    BUSINESS_RULE = "BIZ_002"
    BUSINESS_STATE = "BIZ_003"

    # Security errors (8000-8999)
    SECURITY_AUTH = "SEC_001"
    SECURITY_PERMISSION = "SEC_002"
    SECURITY_ENCRYPTION = "SEC_003"

    # General errors (9000-9999)
    INTERNAL_ERROR = "GEN_001"
    UNKNOWN_ERROR = "GEN_002"


@dataclass
class ErrorContext:
    """Context information for errors."""
    component: str
    operation: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    exchange: Optional[str] = None
    symbol: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


class BaseException(Exception):
    """Base exception class for all application exceptions."""

    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
                 context: Optional[ErrorContext] = None, details: Dict[str, Any] = None,
                 recoverable: bool = True, retry_after: Optional[float] = None):
        self.message = message
        self.error_code = error_code
        self.context = context or ErrorContext(component="unknown", operation="unknown")
        self.details = details or {}
        self.recoverable = recoverable
        self.retry_after = retry_after
        self.timestamp = datetime.utcnow()

        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "context": {
                "component": self.context.component,
                "operation": self.context.operation,
                "user_id": self.context.user_id,
                "request_id": self.context.request_id,
                "exchange": self.context.exchange,
                "symbol": self.context.symbol,
                "additional_data": self.context.additional_data
            },
            "details": self.details,
            "recoverable": self.recoverable,
            "retry_after": self.retry_after
        }

    def __str__(self):
        return f"[{self.error_code.value}] {self.message}"


# Configuration exceptions
class ConfigurationError(BaseException):
    """Configuration-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.CONFIG_INVALID, **kwargs)


class ConfigurationMissingError(ConfigurationError):
    """Missing configuration errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.CONFIG_MISSING, **kwargs)


class ConfigurationEncryptionError(ConfigurationError):
    """Configuration encryption errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.CONFIG_ENCRYPTION, **kwargs)


class ConfigurationValidationError(ConfigurationError):
    """Configuration validation errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.CONFIG_VALIDATION, **kwargs)


# Database exceptions
class DatabaseError(BaseException):
    """Database-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.DATABASE_CONNECTION, **kwargs)


class DatabaseConnectionError(DatabaseError):
    """Database connection errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.DATABASE_CONNECTION, **kwargs)


class DatabaseQueryError(DatabaseError):
    """Database query errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.DATABASE_QUERY, **kwargs)


class DatabaseTimeoutError(DatabaseError):
    """Database timeout errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.DATABASE_TIMEOUT, **kwargs)


# Exchange exceptions
class ExchangeError(BaseException):
    """Exchange-related errors."""

    def __init__(self, message: str, exchange: str = None, **kwargs):
        context = kwargs.pop('context', None) or ErrorContext(component="exchange", operation="unknown")
        if exchange:
            context.exchange = exchange
        super().__init__(message, error_code=ErrorCode.EXCHANGE_API, context=context, **kwargs)


class ExchangeConnectionError(ExchangeError):
    """Exchange connection errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.EXCHANGE_CONNECTION, **kwargs)


class ExchangeRateLimitError(ExchangeError):
    """Exchange rate limit errors."""

    def __init__(self, message: str, retry_after: float = None, **kwargs):
        super().__init__(message, error_code=ErrorCode.EXCHANGE_RATE_LIMIT,
                        retry_after=retry_after, **kwargs)


class RateLimitExceededError(ExchangeRateLimitError):
    """Rate limit exceeded error."""

    def __init__(self, message: str, retry_after: float = None, **kwargs):
        super().__init__(message, retry_after=retry_after, **kwargs)


class ExchangeAuthenticationError(ExchangeError):
    """Exchange authentication errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.EXCHANGE_AUTH, **kwargs)


class ExchangeUnavailableError(ExchangeError):
    """Exchange unavailable error."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.EXCHANGE_CONNECTION, recoverable=False, **kwargs)


# Network exceptions
class NetworkError(BaseException):
    """Network-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.NETWORK_CONNECTION, **kwargs)


class NetworkTimeoutError(NetworkError):
    """Network timeout errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.NETWORK_TIMEOUT, **kwargs)


# Data exceptions
class DataError(BaseException):
    """Data-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.DATA_VALIDATION, **kwargs)


class DataValidationError(DataError):
    """Data validation errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.DATA_VALIDATION, **kwargs)


class DataQualityError(DataError):
    """Data quality errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.DATA_QUALITY, **kwargs)


class DataConsistencyError(DataError):
    """Data consistency errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.DATA_CONSISTENCY, **kwargs)


# System exceptions
class SystemError(BaseException):
    """System-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.SYSTEM_MEMORY, **kwargs)


class MemoryError(SystemError):
    """Memory-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.SYSTEM_MEMORY, **kwargs)


class DiskError(SystemError):
    """Disk-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.SYSTEM_DISK, **kwargs)


# Business exceptions
class BusinessError(BaseException):
    """Business logic errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.BUSINESS_VALIDATION, **kwargs)


class ValidationError(BusinessError):
    """Validation errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.BUSINESS_VALIDATION, **kwargs)


class SecurityError(BaseException):
    """Security-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.SECURITY_AUTH, **kwargs)


class ErrorHandler:
    """Centralized error handler with statistics and alerting."""

    def __init__(self):
        self.logger = get_logger("error_handler")
        self.error_stats = {}
        self.error_history = []
        self.alert_thresholds = {
            "error_rate": 0.1,  # 10% error rate threshold
            "error_count": 100,  # 100 errors in 5 minutes
            "critical_errors": 10  # 10 critical errors in 5 minutes
        }
        self.alert_callbacks = []
        self.recovery_strategies = {}
        self._lock = threading.Lock()

        # Setup default recovery strategies
        self._setup_default_recovery_strategies()

    def _setup_default_recovery_strategies(self):
        """Setup default recovery strategies for different error types."""
        self.recovery_strategies[ErrorCode.EXCHANGE_RATE_LIMIT] = self._retry_with_backoff
        self.recovery_strategies[ErrorCode.NETWORK_TIMEOUT] = self._retry_with_backoff
        self.recovery_strategies[ErrorCode.DATABASE_TIMEOUT] = self._retry_with_backoff

    def handle_exception(self, exc: Exception, context: Optional[ErrorContext] = None) -> Dict[str, Any]:
        """Handle exception with logging, statistics, and alerting."""
        error_info = self._create_error_info(exc, context)

        # Record error statistics
        self._record_error_stats(error_info)

        # Log the error
        self._log_error(error_info)

        # Check alert conditions
        self._check_alerts(error_info)

        # Try recovery if applicable
        recovery_result = self._try_recovery(error_info)

        return {
            "error_info": error_info,
            "recovery_attempted": recovery_result is not None,
            "recovery_successful": recovery_result if recovery_result is not None else False
        }

    def _create_error_info(self, exc: Exception, context: Optional[ErrorContext]) -> Dict[str, Any]:
        """Create structured error information."""
        if isinstance(exc, BaseException):
            return {
                "error_type": type(exc).__name__,
                "error_code": exc.error_code.value,
                "error_message": exc.message,
                "timestamp": exc.timestamp.isoformat(),
                "context": exc.context,
                "details": exc.details,
                "recoverable": exc.recoverable,
                "retry_after": exc.retry_after,
                "traceback": traceback.format_exc() if not isinstance(exc, BaseException) else None
            }
        else:
            return {
                "error_type": type(exc).__name__,
                "error_code": ErrorCode.INTERNAL_ERROR.value,
                "error_message": str(exc),
                "timestamp": datetime.utcnow().isoformat(),
                "context": context or ErrorContext(component="system", operation="unknown"),
                "details": {},
                "recoverable": True,
                "retry_after": None,
                "traceback": traceback.format_exc()
            }

    def _record_error_stats(self, error_info: Dict[str, Any]):
        """Record error statistics."""
        with self._lock:
            error_code = error_info["error_code"]
            timestamp = datetime.fromisoformat(error_info["timestamp"])

            # Initialize error stats if not exists
            if error_code not in self.error_stats:
                self.error_stats[error_code] = {
                    "count": 0,
                    "first_occurrence": timestamp,
                    "last_occurrence": timestamp,
                    "recovery_attempts": 0,
                    "successful_recoveries": 0
                }

            # Update stats
            stats = self.error_stats[error_code]
            stats["count"] += 1
            stats["last_occurrence"] = timestamp

            # Add to history (keep last 1000 errors)
            self.error_history.append(error_info)
            if len(self.error_history) > 1000:
                self.error_history = self.error_history[-1000:]

    def _log_error(self, error_info: Dict[str, Any]):
        """Log error with appropriate level."""
        error_code = error_info["error_code"]
        error_message = error_info["error_message"]
        context = error_info["context"]

        # Determine log level based on error code
        if error_code.startswith(("SYS_", "SEC_")):
            log_level = "critical"
        elif error_code.startswith(("DB_", "EX_", "NET_")):
            log_level = "error"
        elif error_code.startswith(("CONFIG_", "DATA_", "BIZ_")):
            log_level = "warning"
        else:
            log_level = "error"

        # Log with context
        log_method = getattr(self.logger, log_level)
        log_method(
            f"Error occurred: {error_message}",
            extra={
                "error_code": error_code,
                "component": context.component,
                "operation": context.operation,
                "exchange": context.exchange,
                "symbol": context.symbol,
                "error_details": error_info["details"]
            }
        )

    def _check_alerts(self, error_info: Dict[str, Any]):
        """Check if error meets alert conditions."""
        with self._lock:
            # Check error rate in last 5 minutes
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
            recent_errors = [e for e in self.error_history
                            if datetime.fromisoformat(e["timestamp"]) > cutoff_time]

            total_errors = len(recent_errors)
            critical_errors = len([e for e in recent_errors
                                 if e["error_code"].startswith(("SYS_", "SEC_"))])

            # Check thresholds
            if total_errors > self.alert_thresholds["error_count"]:
                self._send_alert("high_error_count", {
                    "threshold": self.alert_thresholds["error_count"],
                    "actual": total_errors,
                    "time_window": "5 minutes"
                })

            if critical_errors > self.alert_thresholds["critical_errors"]:
                self._send_alert("high_critical_error_count", {
                    "threshold": self.alert_thresholds["critical_errors"],
                    "actual": critical_errors,
                    "time_window": "5 minutes"
                })

    def _try_recovery(self, error_info: Dict[str, Any]) -> Optional[bool]:
        """Try to recover from error if possible."""
        error_code = ErrorCode(error_info["error_code"])

        if error_code in self.recovery_strategies:
            try:
                recovery_strategy = self.recovery_strategies[error_code]
                result = recovery_strategy(error_info)

                with self._lock:
                    self.error_stats[error_code.value]["recovery_attempts"] += 1
                    if result:
                        self.error_stats[error_code.value]["successful_recoveries"] += 1

                return result

            except Exception as e:
                self.logger.error(f"Recovery strategy failed: {e}")
                return False

        return None

    def _retry_with_backoff(self, error_info: Dict[str, Any]) -> bool:
        """Retry operation with exponential backoff."""
        # This is a placeholder - actual implementation would depend on the operation
        self.logger.info("Attempting retry with backoff...")
        return False

    def _send_alert(self, alert_type: str, alert_data: Dict[str, Any]):
        """Send alert to registered callbacks."""
        alert = {
            "type": alert_type,
            "data": alert_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.logger.warning(f"Alert triggered: {alert_type}", extra=alert_data)

        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback failed: {e}")

    def add_alert_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add alert callback function."""
        self.alert_callbacks.append(callback)

    def add_recovery_strategy(self, error_code: ErrorCode, strategy: Callable[[Dict[str, Any]], bool]):
        """Add custom recovery strategy."""
        self.recovery_strategies[error_code] = strategy

    def get_error_stats(self, time_range: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get error statistics."""
        with self._lock:
            stats = {
                "total_errors": sum(s["count"] for s in self.error_stats.values()),
                "unique_error_codes": len(self.error_stats),
                "error_stats_by_code": self.error_stats.copy(),
                "recent_errors": []
            }

            # Filter recent errors
            if time_range:
                cutoff_time = datetime.utcnow() - time_range
                stats["recent_errors"] = [
                    e for e in self.error_history
                    if datetime.fromisoformat(e["timestamp"]) > cutoff_time
                ]
            else:
                stats["recent_errors"] = self.error_history[-10:]  # Last 10 errors

            return stats

    def get_top_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top errors by frequency."""
        with self._lock:
            sorted_errors = sorted(
                self.error_stats.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )
            return [
                {
                    "error_code": code,
                    "count": stats["count"],
                    "first_occurrence": stats["first_occurrence"].isoformat(),
                    "last_occurrence": stats["last_occurrence"].isoformat(),
                    "recovery_rate": stats["successful_recoveries"] / max(stats["recovery_attempts"], 1)
                }
                for code, stats in sorted_errors[:limit]
            ]

    def clear_old_errors(self, days: int = 7):
        """Clear errors older than specified days."""
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            self.error_history = [
                e for e in self.error_history
                if datetime.fromisoformat(e["timestamp"]) > cutoff_time
            ]


# Global error handler instance
error_handler = ErrorHandler()


def handle_exceptions(context: Optional[ErrorContext] = None):
    """Decorator for automatic exception handling."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                error_handler.handle_exception(exc, context)
                raise

        return wrapper
    return decorator


def async_handle_exceptions(context: Optional[ErrorContext] = None):
    """Decorator for automatic async exception handling."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                error_handler.handle_exception(exc, context)
                raise

        return wrapper
    return decorator


@contextmanager
def error_context(component: str, operation: str, **kwargs):
    """Context manager for error context."""
    context = ErrorContext(component=component, operation=operation, **kwargs)
    try:
        yield context
    except Exception as exc:
        error_handler.handle_exception(exc, context)
        raise


def create_error_context(component: str, operation: str, **kwargs) -> ErrorContext:
    """Create error context."""
    return ErrorContext(component=component, operation=operation, **kwargs)


def retry_on_error(max_retries: int = 3, backoff_factor: float = 1.0,
                  retryable_errors: List[ErrorCode] = None):
    """Decorator to retry function on specific errors."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exception = exc

                    # Check if error is retryable
                    if isinstance(exc, BaseException):
                        error_code = exc.error_code
                    else:
                        error_code = ErrorCode.INTERNAL_ERROR

                    if retryable_errors and error_code not in retryable_errors:
                        break

                    if attempt < max_retries:
                        delay = backoff_factor * (2 ** attempt)
                        time.sleep(delay)
                        continue

            # If we get here, all retries failed
            raise last_exception

        return wrapper
    return decorator


def async_retry_on_error(max_retries: int = 3, backoff_factor: float = 1.0,
                        retryable_errors: List[ErrorCode] = None):
    """Decorator to retry async function on specific errors."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    last_exception = exc

                    # Check if error is retryable
                    if isinstance(exc, BaseException):
                        error_code = exc.error_code
                    else:
                        error_code = ErrorCode.INTERNAL_ERROR

                    if retryable_errors and error_code not in retryable_errors:
                        break

                    if attempt < max_retries:
                        delay = backoff_factor * (2 ** attempt)
                        await asyncio.sleep(delay)
                        continue

            # If we get here, all retries failed
            raise last_exception

        return wrapper
    return decorator


def get_error_dashboard_data() -> Dict[str, Any]:
    """Get error dashboard data."""
    stats = error_handler.get_error_stats()
    top_errors = error_handler.get_top_errors()

    return {
        "total_errors": stats["total_errors"],
        "unique_error_codes": stats["unique_error_codes"],
        "recent_errors": len(stats["recent_errors"]),
        "top_errors": top_errors,
        "error_rate_by_component": _calculate_error_rate_by_component(stats["recent_errors"])
    }


def _calculate_error_rate_by_component(errors: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate error rate by component."""
    component_stats = {}

    for error in errors:
        component = error["context"]["component"]
        component_stats[component] = component_stats.get(component, 0) + 1

    total_errors = sum(component_stats.values())
    if total_errors == 0:
        return {}

    return {
        component: count / total_errors
        for component, count in component_stats.items()
    }