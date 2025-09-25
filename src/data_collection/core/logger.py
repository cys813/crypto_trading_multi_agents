"""
Structured logging system for the data collection agent.

This module provides a comprehensive logging system with:
- JSON and text format support
- Multiple output channels (console, file, remote)
- Log rotation and management
- Context-aware logging with request IDs
- Performance monitoring
- Structured log fields for better analysis
"""

import logging
import logging.handlers
import json
import sys
import threading
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
from pathlib import Path
import uuid
import traceback
from contextlib import contextmanager
import asyncio
from queue import Queue
import time

from .config import get_config


class StructuredFormatter(logging.Formatter):
    """Structured JSON log formatter with enhanced fields."""

    def __init__(self, include_extra: bool = True, service_name: str = "data_collection_agent"):
        super().__init__()
        self.include_extra = include_extra
        self.service_name = service_name
        self.fields_to_skip = {'args', 'message', 'exc_info', 'exc_text', 'stack_info', 'msg'}

    def format(self, record):
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread_id": record.thread,
            "process_id": record.process
        }

        # Add exception information
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add stack information
        if record.stack_info:
            log_entry["stack_info"] = self.formatStack(record.stack_info)

        # Add performance metrics
        if hasattr(record, 'duration'):
            log_entry["duration_ms"] = record.duration

        # Add request context
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id

        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id

        if hasattr(record, 'session_id'):
            log_entry["session_id"] = record.session_id

        # Add exchange context
        if hasattr(record, 'exchange'):
            log_entry["exchange"] = record.exchange

        if hasattr(record, 'symbol'):
            log_entry["symbol"] = record.symbol

        # Add extra fields
        if self.include_extra:
            for key, value in record.__dict__.items():
                if key not in self.fields_to_skip and not key.startswith('_'):
                    # Skip already handled fields
                    if key in log_entry:
                        continue
                    try:
                        # Ensure value is JSON serializable
                        json.dumps(value)
                        log_entry[key] = value
                    except (TypeError, ValueError):
                        log_entry[key] = str(value)

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for better readability."""

    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'

    def __init__(self):
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    def format(self, record):
        """Format log record with colors."""
        log_color = self.COLORS.get(record.levelname, self.RESET)
        formatted = super().format(record)
        return f"{log_color}{formatted}{self.RESET}"


class AsyncLogHandler(logging.Handler):
    """Asynchronous log handler for better performance."""

    def __init__(self, target_handler: logging.Handler, max_queue_size: int = 10000):
        super().__init__()
        self.target_handler = target_handler
        self.queue = Queue(maxsize=max_queue_size)
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        self._shutdown = False

    def emit(self, record):
        """Emit log record asynchronously."""
        try:
            self.queue.put_nowait(record)
        except Exception as e:
            # Fallback to synchronous logging if queue is full
            print(f"Log queue full, falling back to sync: {e}")
            self.target_handler.emit(record)

    def _process_queue(self):
        """Process log queue in worker thread."""
        while not self._shutdown:
            try:
                record = self.queue.get(timeout=1)
                self.target_handler.emit(record)
                self.queue.task_done()
            except Exception:
                continue

    def close(self):
        """Close the handler."""
        self._shutdown = True
        self.worker_thread.join(timeout=5)
        super().close()


class RequestIdFilter(logging.Filter):
    """Filter to add request ID to log records."""

    def __init__(self, request_id: str = None):
        super().__init__()
        self.request_id = request_id or str(uuid.uuid4())

    def filter(self, record):
        """Add request ID to log record."""
        record.request_id = self.request_id
        return True


class ContextFilter(logging.Filter):
    """Filter to add context information to log records."""

    def __init__(self, context: Dict[str, Any] = None):
        super().__init__()
        self.context = context or {}

    def filter(self, record):
        """Add context to log record."""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


class PerformanceFilter(logging.Filter):
    """Filter to add performance metrics to log records."""

    def __init__(self):
        super().__init__()
        self.start_time = time.time()

    def filter(self, record):
        """Add performance metrics to log record."""
        record.duration = (time.time() - self.start_time) * 1000  # milliseconds
        return True


class LoggerManager:
    """Advanced logging manager with multiple output support."""

    def __init__(self):
        self.loggers = {}
        self.handlers = {}
        self.config = None
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration from settings."""
        try:
            self.config = get_config()
            if not self.config:
                raise ValueError("Configuration not loaded")

            log_config = self.config.logging
            log_level = getattr(logging, log_config.level.upper())

            # Create root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(log_level)

            # Clear existing handlers
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)

            # Setup output handlers
            self.handlers = {}

            # Console output
            if 'console' in log_config.output:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(log_level)

                if log_config.format == 'json':
                    console_handler.setFormatter(StructuredFormatter(
                        include_extra=True,
                        service_name=self.config.app_name
                    ))
                else:
                    console_handler.setFormatter(ColoredFormatter())

                # Wrap in async handler for better performance
                async_console_handler = AsyncLogHandler(console_handler)
                root_logger.addHandler(async_console_handler)
                self.handlers['console'] = async_console_handler

            # File output
            if 'file' in log_config.output:
                file_handler = self._create_file_handler(log_config)
                root_logger.addHandler(file_handler)
                self.handlers['file'] = file_handler

            # Remote logging (could be extended to support ELK, Splunk, etc.)
            if 'remote' in log_config.output:
                remote_handler = self._create_remote_handler(log_config)
                if remote_handler:
                    root_logger.addHandler(remote_handler)
                    self.handlers['remote'] = remote_handler

            # Prevent duplicate logging from third-party libraries
            logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
            logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
            logging.getLogger("ccxt").setLevel(logging.WARNING)

            logging.info(f"Logging system initialized with level: {log_config.level}")

        except Exception as e:
            # Fallback to basic logging if setup fails
            print(f"Failed to setup logging system: {e}")
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

    def _create_file_handler(self, log_config) -> logging.Handler:
        """Create rotating file handler."""
        file_path = Path(log_config.file_path)
        max_size = self._parse_size(log_config.max_file_size)
        backup_count = log_config.backup_count

        # Create log directory
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_config.level.upper()))

        # Use structured formatter for files
        file_handler.setFormatter(StructuredFormatter(
            include_extra=True,
            service_name=self.config.app_name
        ))

        return file_handler

    def _create_remote_handler(self, log_config) -> Optional[logging.Handler]:
        """Create remote logging handler (placeholder for future implementation)."""
        # This could be extended to support:
        # - ELK stack (Elasticsearch, Logstash, Kibana)
        # - Splunk HTTP Event Collector
        # - Cloud logging services (AWS CloudWatch, GCP Cloud Logging)
        # - Custom logging endpoints
        return None

    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes."""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)

    def get_logger(self, name: str, context: Dict[str, Any] = None) -> logging.Logger:
        """Get logger instance with optional context."""
        if name not in self.loggers:
            logger = logging.getLogger(name)

            # Add context filter if provided
            if context:
                context_filter = ContextFilter(context)
                logger.addFilter(context_filter)

            self.loggers[name] = logger

        return self.loggers[name]

    def add_request_context(self, logger: logging.Logger, request_id: str = None) -> logging.Logger:
        """Add request context to logger."""
        request_filter = RequestIdFilter(request_id)
        logger.addFilter(request_filter)
        return logger

    def add_performance_context(self, logger: logging.Logger) -> logging.Logger:
        """Add performance tracking to logger."""
        performance_filter = PerformanceFilter()
        logger.addFilter(performance_filter)
        return logger

    def create_child_logger(self, parent_name: str, child_name: str,
                           context: Dict[str, Any] = None) -> logging.Logger:
        """Create child logger with inherited context."""
        full_name = f"{parent_name}.{child_name}"
        parent_logger = self.get_logger(parent_name)
        child_logger = self.get_logger(full_name, context)

        # Inherit filters from parent
        for filter_obj in parent_logger.filters:
            child_logger.addFilter(filter_obj)

        return child_logger

    def set_log_level(self, logger_name: str, level: str):
        """Set log level for specific logger."""
        if logger_name in self.loggers:
            log_level = getattr(logging, level.upper())
            self.loggers[logger_name].setLevel(log_level)

    def reload_logging(self):
        """Reload logging configuration."""
        logging.info("Reloading logging configuration...")
        self.setup_logging()

    def get_logger_stats(self) -> Dict[str, Any]:
        """Get logging statistics."""
        stats = {
            "total_loggers": len(self.loggers),
            "handlers": list(self.handlers.keys()),
            "loggers": {}
        }

        for name, logger in self.loggers.items():
            stats["loggers"][name] = {
                "level": logging.getLevelName(logger.level),
                "filters_count": len(logger.filters),
                "handlers_count": len(logger.handlers)
            }

        return stats

    def cleanup(self):
        """Cleanup logging resources."""
        for handler in self.handlers.values():
            handler.close()
        self.handlers.clear()


# Global logger manager instance
logger_manager = LoggerManager()


def get_logger(name: str, context: Dict[str, Any] = None) -> logging.Logger:
    """Get logger instance with optional context."""
    return logger_manager.get_logger(name, context)


def get_exchange_logger(exchange_name: str, symbol: str = None) -> logging.Logger:
    """Get logger for specific exchange and symbol."""
    context = {"exchange": exchange_name}
    if symbol:
        context["symbol"] = symbol

    logger_name = f"exchange.{exchange_name}"
    if symbol:
        logger_name += f".{symbol.replace('/', '_')}"

    return get_logger(logger_name, context)


@contextmanager
def log_execution_time(logger: logging.Logger, operation: str):
    """Context manager to log execution time."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = (time.time() - start_time) * 1000
        logger.info(f"Operation completed: {operation}", extra={"duration": duration})


def log_function_call(func):
    """Decorator to log function calls."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling function: {func.__name__}", extra={
            "function": func.__name__,
            "args_count": len(args),
            "kwargs_count": len(kwargs)
        })

        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000
            logger.debug(f"Function completed: {func.__name__}", extra={
                "function": func.__name__,
                "duration": duration,
                "success": True
            })
            return result
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"Function failed: {func.__name__}", extra={
                "function": func.__name__,
                "duration": duration,
                "success": False,
                "error": str(e)
            })
            raise

    return wrapper


class RequestContext:
    """Context manager for request-scoped logging."""

    def __init__(self, request_id: str = None, user_id: str = None, **kwargs):
        self.request_id = request_id or str(uuid.uuid4())
        self.user_id = user_id
        self.extra_context = kwargs
        self.logger = None

    def __enter__(self):
        """Enter request context."""
        context = {"request_id": self.request_id}
        if self.user_id:
            context["user_id"] = self.user_id
        context.update(self.extra_context)

        self.logger = get_logger("request", context)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit request context."""
        if self.logger:
            if exc_type:
                self.logger.error("Request failed", extra={
                    "exception_type": exc_type.__name__,
                    "exception_message": str(exc_val)
                })
            else:
                self.logger.debug("Request completed successfully")


def get_request_context(request_id: str = None, **kwargs) -> RequestContext:
    """Get request context manager."""
    return RequestContext(request_id, **kwargs)


def reload_logging():
    """Reload logging configuration."""
    logger_manager.reload_logging()