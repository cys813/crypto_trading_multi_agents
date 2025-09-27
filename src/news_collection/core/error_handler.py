"""
错误处理器 - 连接和数据获取异常处理
"""

import traceback
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum

from ..models.base import NewsSourceConfig, NewsQuery, NewsQueryResult
from .adapter import NewsSourceAdapter


class ErrorType(Enum):
    """错误类型枚举"""
    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    DATA_FORMAT_ERROR = "data_format_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """错误上下文"""
    source_name: str
    operation: str
    timestamp: datetime
    query: Optional[NewsQuery] = None
    config: Optional[NewsSourceConfig] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorInfo:
    """错误信息"""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    context: ErrorContext
    exception: Optional[Exception] = None
    traceback_str: Optional[str] = None
    retry_count: int = 0
    should_retry: bool = True


@dataclass
class RetryPolicy:
    """重试策略"""
    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    backoff_factor: float = 2.0
    retryable_errors: List[ErrorType] = field(default_factory=lambda: [
        ErrorType.CONNECTION_ERROR,
        ErrorType.TIMEOUT_ERROR,
        ErrorType.NETWORK_ERROR,
        ErrorType.RATE_LIMIT_ERROR
    ])


@dataclass
class CircuitBreakerConfig:
    """断路器配置"""
    failure_threshold: int = 5  # 失败阈值
    recovery_timeout: int = 60  # 恢复超时（秒）
    expected_exception: List[type] = field(default_factory=lambda: [
        ConnectionError,
        TimeoutError,
        asyncio.TimeoutError
    ])


class CircuitBreaker:
    """断路器模式实现"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.logger = logging.getLogger(__name__)

    def call(self, func, *args, **kwargs):
        """调用函数并应用断路器逻辑"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                self.logger.info("断路器状态: HALF_OPEN")
            else:
                raise Exception("断路器已开启，拒绝调用")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except tuple(self.config.expected_exception) as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """判断是否应该尝试重置"""
        if self.last_failure_time is None:
            return True

        recovery_time = datetime.now() - self.last_failure_time
        return recovery_time.total_seconds() >= self.config.recovery_timeout

    def _on_success(self):
        """成功处理"""
        self.failure_count = 0
        if self.state != "CLOSED":
            self.state = "CLOSED"
            self.logger.info("断路器状态: CLOSED")

    def _on_failure(self):
        """失败处理"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.config.failure_threshold:
            self.state = "OPEN"
            self.logger.warning(f"断路器已开启，失败次数: {self.failure_count}")

    def get_state(self) -> Dict[str, Any]:
        """获取断路器状态"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "config": self.config.__dict__
        }


class ErrorHandler:
    """错误处理器"""

    def __init__(self, retry_policy: Optional[RetryPolicy] = None,
                 circuit_breaker_config: Optional[CircuitBreakerConfig] = None):
        self.retry_policy = retry_policy or RetryPolicy()
        self.circuit_breaker_config = circuit_breaker_config or CircuitBreakerConfig()
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._error_handlers: Dict[ErrorType, Callable] = {}
        self._error_history: List[ErrorInfo] = []
        self._error_stats: Dict[str, Dict] = {}
        self._logger = logging.getLogger(__name__)

    def register_error_handler(self, error_type: ErrorType, handler: Callable):
        """注册错误处理器"""
        self._error_handlers[error_type] = handler

    def unregister_error_handler(self, error_type: ErrorType):
        """注销错误处理器"""
        self._error_handlers.pop(error_type, None)

    async def handle_error(self, error: Exception, context: ErrorContext,
                          adapter: Optional[NewsSourceAdapter] = None) -> ErrorInfo:
        """处理错误"""
        # 识别错误类型
        error_info = self._classify_error(error, context)

        # 记录错误
        self._record_error(error_info)

        # 获取断路器
        circuit_breaker = self._get_circuit_breaker(context.source_name)

        # 处理错误
        await self._process_error(error_info, circuit_breaker)

        # 调用注册的错误处理器
        if error_info.error_type in self._error_handlers:
            try:
                handler = self._error_handlers[error_info.error_type]
                if asyncio.iscoroutinefunction(handler):
                    await handler(error_info)
                else:
                    handler(error_info)
            except Exception as e:
                self._logger.error(f"错误处理器异常: {e}")

        return error_info

    async def execute_with_retry(self, func: Callable, context: ErrorContext,
                               *args, **kwargs) -> Any:
        """带重试的函数执行"""
        last_error: Optional[ErrorInfo] = None

        for attempt in range(self.retry_policy.max_attempts):
            try:
                # 获取断路器
                circuit_breaker = self._get_circuit_breaker(context.source_name)

                # 使用断路器执行函数
                def wrapped_func():
                    return func(*args, **kwargs)

                result = circuit_breaker.call(wrapped_func)
                if asyncio.iscoroutine(result):
                    result = await result

                return result

            except Exception as e:
                error_info = await self.handle_error(e, context)
                last_error = error_info

                # 检查是否应该重试
                if not self._should_retry(error_info, attempt):
                    break

                # 计算延迟时间
                delay = self._calculate_retry_delay(attempt)
                self._logger.info(f"重试 {attempt + 1}/{self.retry_policy.max_attempts}, 延迟 {delay}s")
                await asyncio.sleep(delay)

        # 所有重试都失败
        if last_error:
            raise self._create_retries_exhausted_error(last_error)
        else:
            raise Exception("未知错误")

    def get_error_stats(self, source_name: Optional[str] = None) -> Dict[str, Any]:
        """获取错误统计"""
        if source_name:
            return self._error_stats.get(source_name, {})
        else:
            return self._error_stats.copy()

    def get_error_history(self, source_name: Optional[str] = None,
                         limit: int = 100, error_type: Optional[ErrorType] = None) -> List[ErrorInfo]:
        """获取错误历史"""
        history = self._error_history

        # 筛选
        if source_name:
            history = [e for e in history if e.context.source_name == source_name]

        if error_type:
            history = [e for e in history if e.error_type == error_type]

        # 排序和限制
        history.sort(key=lambda x: x.context.timestamp, reverse=True)
        return history[:limit]

    def get_circuit_breaker_status(self, source_name: str) -> Dict[str, Any]:
        """获取断路器状态"""
        circuit_breaker = self._circuit_breakers.get(source_name)
        if circuit_breaker:
            return circuit_breaker.get_state()
        return {"state": "NOT_INITIALIZED"}

    def reset_circuit_breaker(self, source_name: str):
        """重置断路器"""
        if source_name in self._circuit_breakers:
            self._circuit_breakers[source_name] = CircuitBreaker(self.circuit_breaker_config)
            self._logger.info(f"重置断路器: {source_name}")

    def clear_error_history(self, source_name: Optional[str] = None):
        """清空错误历史"""
        if source_name:
            self._error_history = [e for e in self._error_history if e.context.source_name != source_name]
            self._error_stats.pop(source_name, None)
        else:
            self._error_history.clear()
            self._error_stats.clear()

    def _classify_error(self, error: Exception, context: ErrorContext) -> ErrorInfo:
        """分类错误"""
        error_type = ErrorType.UNKNOWN_ERROR
        severity = ErrorSeverity.MEDIUM

        # 根据异常类型分类
        if isinstance(error, ConnectionError):
            error_type = ErrorType.CONNECTION_ERROR
            severity = ErrorSeverity.HIGH
        elif isinstance(error, TimeoutError) or isinstance(error, asyncio.TimeoutError):
            error_type = ErrorType.TIMEOUT_ERROR
            severity = ErrorSeverity.MEDIUM
        elif "401" in str(error) or "Unauthorized" in str(error):
            error_type = ErrorType.AUTHENTICATION_ERROR
            severity = ErrorSeverity.HIGH
        elif "429" in str(error) or "Too Many Requests" in str(error):
            error_type = ErrorType.RATE_LIMIT_ERROR
            severity = ErrorSeverity.MEDIUM
        elif "JSON" in str(error) or "parse" in str(error).lower():
            error_type = ErrorType.DATA_FORMAT_ERROR
            severity = ErrorSeverity.LOW
        elif "Network" in str(error) or "DNS" in str(error):
            error_type = ErrorType.NETWORK_ERROR
            severity = ErrorSeverity.HIGH

        # 根据上下文调整严重程度
        if context.operation == "health_check":
            severity = ErrorSeverity.LOW
        elif context.operation == "fetch_news":
            severity = ErrorSeverity.MEDIUM

        return ErrorInfo(
            error_type=error_type,
            severity=severity,
            message=str(error),
            context=context,
            exception=error,
            traceback_str=traceback.format_exc(),
            should_retry=error_type in self.retry_policy.retryable_errors
        )

    def _record_error(self, error_info: ErrorInfo):
        """记录错误"""
        # 添加到历史
        self._error_history.append(error_info)

        # 更新统计
        source_name = error_info.context.source_name
        if source_name not in self._error_stats:
            self._error_stats[source_name] = {
                "total_errors": 0,
                "error_types": {},
                "last_error": None,
                "consecutive_errors": 0
            }

        stats = self._error_stats[source_name]
        stats["total_errors"] += 1
        stats["last_error"] = error_info.context.timestamp

        # 按类型统计
        error_type = error_info.error_type.value
        if error_type not in stats["error_types"]:
            stats["error_types"][error_type] = 0
        stats["error_types"][error_type] += 1

        # 连续错误
        if error_info.error_type in [ErrorType.CONNECTION_ERROR, ErrorType.TIMEOUT_ERROR]:
            stats["consecutive_errors"] += 1
        else:
            stats["consecutive_errors"] = 0

        # 限制历史记录大小
        if len(self._error_history) > 1000:
            self._error_history = self._error_history[-500:]

    async def _process_error(self, error_info: ErrorInfo, circuit_breaker: CircuitBreaker):
        """处理错误"""
        source_name = error_info.context.source_name

        # 记录日志
        self._logger.error(
            f"错误 [{error_info.error_type.value}] {source_name}: {error_info.message}",
            extra={
                "source": source_name,
                "operation": error_info.context.operation,
                "severity": error_info.severity.value,
                "retry_count": error_info.retry_count
            }
        )

        # 根据严重程度处理
        if error_info.severity == ErrorSeverity.CRITICAL:
            self._logger.critical(f"严重错误: {source_name} - {error_info.message}")

        # 如果是认证错误，禁用新闻源
        if error_info.error_type == ErrorType.AUTHENTICATION_ERROR:
            self._logger.error(f"认证失败，禁用新闻源: {source_name}")
            # 这里可以调用配置管理器禁用新闻源

    def _get_circuit_breaker(self, source_name: str) -> CircuitBreaker:
        """获取或创建断路器"""
        if source_name not in self._circuit_breakers:
            self._circuit_breakers[source_name] = CircuitBreaker(self.circuit_breaker_config)
        return self._circuit_breakers[source_name]

    def _should_retry(self, error_info: ErrorInfo, attempt: int) -> bool:
        """判断是否应该重试"""
        if attempt >= self.retry_policy.max_attempts - 1:
            return False

        if not error_info.should_retry:
            return False

        # 认证错误不重试
        if error_info.error_type == ErrorType.AUTHENTICATION_ERROR:
            return False

        # 数据格式错误不重试
        if error_info.error_type == ErrorType.DATA_FORMAT_ERROR:
            return False

        return True

    def _calculate_retry_delay(self, attempt: int) -> float:
        """计算重试延迟"""
        delay = self.retry_policy.base_delay * (self.retry_policy.backoff_factor ** attempt)
        return min(delay, self.retry_policy.max_delay)

    def _create_retries_exhausted_error(self, last_error: ErrorInfo) -> Exception:
        """创建重试耗尽异常"""
        message = f"重试耗尽 [{last_error.error_type.value}] {last_error.context.source_name}: {last_error.message}"
        return Exception(message)

    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        total_errors = len(self._error_history)
        error_types = {}

        for error in self._error_history:
            error_type = error.error_type.value
            if error_type not in error_types:
                error_types[error_type] = 0
            error_types[error_type] += 1

        return {
            "total_errors": total_errors,
            "error_types": error_types,
            "sources_with_errors": len(self._error_stats),
            "active_circuit_breakers": len([cb for cb in self._circuit_breakers.values() if cb.state == "OPEN"]),
            "retry_policy": self.retry_policy.__dict__
        }