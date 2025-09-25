"""
Enhanced Exchange Manager with multi-exchange connection management, load balancing,
rate limiting, and failover capabilities.

This module provides a comprehensive solution for managing multiple cryptocurrency
exchange connections with advanced features for high-performance trading systems.
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import aiohttp
import ccxt
from ccxt.base.errors import NetworkError, ExchangeError, RateLimitError
from collections import defaultdict, deque
import redis.asyncio as redis
from contextlib import asynccontextmanager

from ..core.config import get_config
from ..core.logger import get_logger
from ..core.exceptions import ExchangeConnectionError, RateLimitExceededError, ExchangeUnavailableError
from ..utils.metrics import MetricsCollector


class ExchangeStatus(Enum):
    """Exchange connection status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    INITIALIZING = "initializing"


class ConnectionStrategy(Enum):
    """Load balancing connection strategies."""
    ROUND_ROBIN = "round_robin"
    LEAST_LATENCY = "least_latency"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    FAILOVER = "failover"
    LEAST_CONNECTIONS = "least_connections"


class Priority(Enum):
    """Request priority levels."""
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class RateLimitInfo:
    """Rate limit information for an exchange method."""
    limit: int
    window: int  # Time window in seconds
    remaining: int
    reset_time: float
    requests: deque = field(default_factory=deque)
    backoff_multiplier: float = 1.0
    last_backoff: float = 0.0


@dataclass
class ExchangeConnection:
    """Enhanced exchange connection with comprehensive monitoring."""
    exchange_id: str
    exchange: ccxt.Exchange
    status: ExchangeStatus
    session: aiohttp.ClientSession
    last_ping: float = field(default_factory=time.time)
    latency: float = 0.0
    error_count: int = 0
    success_count: int = 0
    consecutive_errors: int = 0
    weight: int = 100
    rate_limits: Dict[str, RateLimitInfo] = field(default_factory=dict)
    active_connections: int = 0
    total_requests: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[float] = None
    health_score: float = 1.0
    created_at: float = field(default_factory=time.time)
    region: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)

    def update_success(self, latency: float):
        """Update connection after successful request."""
        self.success_count += 1
        self.total_requests += 1
        self.last_ping = time.time()

        # Update latency with exponential moving average
        if self.latency == 0:
            self.latency = latency
        else:
            self.latency = self.latency * 0.8 + latency * 0.2

        # Update health score
        self.consecutive_errors = 0
        self.health_score = min(1.0, self.health_score + 0.01)

    def update_error(self, error: str):
        """Update connection after failed request."""
        self.error_count += 1
        self.total_requests += 1
        self.consecutive_errors += 1
        self.last_error = error
        self.last_error_time = time.time()

        # Update health score
        self.health_score = max(0.0, self.health_score - 0.1)

    def get_success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.success_count / self.total_requests

    def is_healthy(self) -> bool:
        """Check if connection is healthy."""
        if self.status == ExchangeStatus.OFFLINE:
            return False
        if self.consecutive_errors > 5:
            return False
        if self.health_score < 0.3:
            return False
        return True


class RateLimiter:
    """Advanced rate limiter with Redis support and distributed limiting."""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.logger = get_logger("rate_limiter")
        self.local_limits: Dict[str, RateLimitInfo] = {}
        self.use_redis = redis_client is not None

    async def acquire_permit(self, exchange_id: str, method: str,
                           priority: Priority = Priority.NORMAL) -> bool:
        """Acquire permit for making a request."""
        key = f"{exchange_id}:{method}"

        if self.use_redis:
            return await self._acquire_redis_permit(key, priority)
        else:
            return await self._acquire_local_permit(key, priority)

    async def _acquire_redis_permit(self, key: str, priority: Priority) -> bool:
        """Acquire permit using Redis for distributed rate limiting."""
        try:
            current_time = time.time()

            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()

            # Get current window requests
            pipe.zrangebyscore(f"rate_limit:{key}", current_time - 60, current_time)
            pipe.zcard(f"rate_limit:{key}")
            pipe.ttl(f"rate_limit:{key}")

            results = await pipe.execute()
            requests_in_window = results[1]
            ttl = results[2]

            # Set default limit based on priority
            limit = 100 if priority == Priority.NORMAL else (50 if priority == Priority.HIGH else 200)

            if requests_in_window < limit:
                # Add current request
                pipe.zadd(f"rate_limit:{key}", {str(current_time): current_time})
                pipe.expire(f"rate_limit:{key}", 60 if ttl == -1 else ttl)
                await pipe.execute()
                return True
            else:
                # Check if we can prioritize based on priority
                if priority == Priority.HIGH:
                    # Remove oldest low priority request
                    oldest_requests = await self.redis_client.zrange(f"rate_limit:{key}", 0, 0)
                    if oldest_requests:
                        await self.redis_client.zrem(f"rate_limit:{key}", oldest_requests[0])
                        # Add current request
                        await self.redis_client.zadd(f"rate_limit:{key}", {str(current_time): current_time})
                        return True

                return False

        except Exception as e:
            self.logger.error(f"Redis rate limiting error: {e}")
            return await self._acquire_local_permit(key, priority)

    async def _acquire_local_permit(self, key: str, priority: Priority) -> bool:
        """Acquire permit using local rate limiting."""
        if key not in self.local_limits:
            self.local_limits[key] = RateLimitInfo(
                limit=100 if priority == Priority.NORMAL else (50 if priority == Priority.HIGH else 200),
                window=60,
                remaining=100,
                reset_time=time.time() + 60,
                requests=deque()
            )

        limit_info = self.local_limits[key]
        current_time = time.time()

        # Clean expired requests
        while limit_info.requests and limit_info.requests[0] <= current_time - limit_info.window:
            limit_info.requests.popleft()

        # Check if we can make the request
        if len(limit_info.requests) < limit_info.limit:
            limit_info.requests.append(current_time)
            limit_info.remaining = limit_info.limit - len(limit_info.requests)
            return True
        elif priority == Priority.HIGH:
            # High priority requests can bypass limit
            limit_info.requests.append(current_time)
            limit_info.remaining = limit_info.limit - len(limit_info.requests)
            return True

        return False

    async def get_remaining_requests(self, exchange_id: str, method: str) -> int:
        """Get remaining requests for an exchange method."""
        key = f"{exchange_id}:{method}"

        if self.use_redis:
            try:
                current_time = time.time()
                count = await self.redis_client.zcount(f"rate_limit:{key}", current_time - 60, current_time)
                return max(0, 100 - count)
            except Exception as e:
                self.logger.error(f"Error getting Redis remaining requests: {e}")

        if key in self.local_limits:
            return self.local_limits[key].remaining
        return 100

    async def handle_rate_limit_error(self, exchange_id: str, method: str):
        """Handle rate limit errors with backoff."""
        key = f"{exchange_id}:{method}"

        if key in self.local_limits:
            limit_info = self.local_limits[key]
            limit_info.backoff_multiplier = min(limit_info.backoff_multiplier * 1.5, 8.0)
            limit_info.last_backoff = time.time()


class ConnectionPool:
    """Intelligent connection pool with load balancing."""

    def __init__(self, max_size: int = 10, idle_timeout: int = 300):
        self.max_size = max_size
        self.idle_timeout = idle_timeout
        self.connections: Dict[str, List[ExchangeConnection]] = defaultdict(list)
        self.active_connections: Dict[str, int] = defaultdict(int)
        self.logger = get_logger("connection_pool")
        self._cleanup_task: Optional[asyncio.Task] = None

    async def get_connection(self, exchange_id: str,
                          connection_manager: 'ExchangeManager') -> Optional[ExchangeConnection]:
        """Get a connection from the pool."""
        # Try to get from pool first
        if self.connections[exchange_id]:
            connection = self.connections[exchange_id].pop()
            self.active_connections[exchange_id] += 1
            return connection

        # Create new connection if under limit
        if self.active_connections[exchange_id] < self.max_size:
            try:
                connection = await connection_manager._create_connection(exchange_id)
                self.active_connections[exchange_id] += 1
                return connection
            except Exception as e:
                self.logger.error(f"Failed to create connection for {exchange_id}: {e}")

        return None

    async def return_connection(self, connection: ExchangeConnection):
        """Return a connection to the pool."""
        exchange_id = connection.exchange_id
        self.active_connections[exchange_id] -= 1

        # Only return healthy connections to pool
        if connection.is_healthy():
            self.connections[exchange_id].append(connection)
        else:
            # Close unhealthy connections
            await connection_manager._close_connection(connection)

    async def start_cleanup(self, connection_manager: 'ExchangeManager'):
        """Start background cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop(connection_manager))

    async def _cleanup_loop(self, connection_manager: 'ExchangeManager'):
        """Cleanup idle connections."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                for exchange_id, connections in self.connections.items():
                    current_time = time.time()
                    connections_to_remove = []

                    for connection in connections:
                        if current_time - connection.last_ping > self.idle_timeout:
                            connections_to_remove.append(connection)

                    for connection in connections_to_remove:
                        await connection_manager._close_connection(connection)
                        self.connections[exchange_id].remove(connection)

            except Exception as e:
                self.logger.error(f"Connection pool cleanup error: {e}")

    async def stop(self):
        """Stop the connection pool."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


class ExchangeManager:
    """Enhanced exchange manager with advanced features."""

    def __init__(self, strategy: ConnectionStrategy = ConnectionStrategy.WEIGHTED_ROUND_ROBIN):
        self.config = get_config()
        self.logger = get_logger("exchange_manager")
        self.metrics = MetricsCollector()
        self.strategy = strategy

        # Core components
        self.connections: Dict[str, ExchangeConnection] = {}
        self.connection_pool = ConnectionPool()
        self.rate_limiter: Optional[RateLimiter] = None

        # State management
        self._running = False
        self._health_check_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

        # Performance tracking
        self.request_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.error_counts: Dict[str, int] = defaultdict(int)

        # Initialize Redis client if configured
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis client for distributed rate limiting."""
        try:
            redis_config = self.config.redis
            self.redis_client = redis.Redis(
                host=redis_config.host,
                port=redis_config.port,
                password=redis_config.password,
                db=redis_config.database if hasattr(redis_config, 'database') else 0,
                decode_responses=True
            )
            self.rate_limiter = RateLimiter(self.redis_client)
        except Exception as e:
            self.logger.warning(f"Failed to initialize Redis: {e}")
            self.rate_limiter = RateLimiter()

    async def initialize(self):
        """Initialize the exchange manager."""
        async with self._lock:
            if self._running:
                return

            try:
                self.logger.info("Initializing Exchange Manager...")

                # Load exchange configurations
                exchange_configs = self.config.exchanges

                # Initialize connections
                for exchange_name, exchange_config in exchange_configs.items():
                    if exchange_config.enabled:
                        await self._add_exchange(exchange_name, exchange_config)

                # Start background tasks
                self._running = True
                self._health_check_task = asyncio.create_task(self._health_check_loop())
                self._metrics_task = asyncio.create_task(self._metrics_loop())

                # Start connection pool cleanup
                await self.connection_pool.start_cleanup(self)

                self.logger.info(f"Exchange Manager initialized with {len(self.connections)} exchanges")

            except Exception as e:
                self.logger.error(f"Failed to initialize Exchange Manager: {e}")
                raise

    async def _add_exchange(self, exchange_name: str, exchange_config: Any):
        """Add an exchange to the manager."""
        try:
            # Create CCXT instance
            exchange_class = getattr(ccxt, exchange_name)
            exchange = exchange_class({
                'apiKey': exchange_config.api_key,
                'secret': exchange_config.api_secret,
                'password': exchange_config.passphrase,
                'sandbox': exchange_config.sandbox,
                'enableRateLimit': exchange_config.enable_rate_limit,
                'timeout': exchange_config.timeout,
                'verbose': False,
                'options': exchange_config.options
            })

            # Create HTTP session
            session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=exchange_config.timeout / 1000),
                connector=aiohttp.TCPConnector(
                    limit=100,
                    limit_per_host=30,
                    ttl_dns_cache=300,
                    use_dns_cache=True,
                    keepalive_timeout=60
                )
            )

            # Create connection
            connection = ExchangeConnection(
                exchange_id=exchange_name,
                exchange=exchange,
                status=ExchangeStatus.INITIALIZING,
                session=session,
                weight=exchange_config.rate_limit,
                region=exchange_config.options.get('region'),
                capabilities=self._get_exchange_capabilities(exchange)
            )

            self.connections[exchange_name] = connection
            self.logger.info(f"Added exchange: {exchange_name}")

        except Exception as e:
            self.logger.error(f"Failed to add exchange {exchange_name}: {e}")
            raise

    def _get_exchange_capabilities(self, exchange: ccxt.Exchange) -> List[str]:
        """Get exchange capabilities."""
        capabilities = []

        if hasattr(exchange, 'fetch_markets'):
            capabilities.append('markets')
        if hasattr(exchange, 'fetch_ticker'):
            capabilities.append('ticker')
        if hasattr(exchange, 'fetch_ohlcv'):
            capabilities.append('ohlcv')
        if hasattr(exchange, 'fetch_order_book'):
            capabilities.append('orderbook')
        if hasattr(exchange, 'fetch_trades'):
            capabilities.append('trades')
        if hasattr(exchange, 'fetch_balance'):
            capabilities.append('balance')
        if hasattr(exchange, 'fetch_positions'):
            capabilities.append('positions')
        if hasattr(exchange, 'fetch_orders'):
            capabilities.append('orders')

        return capabilities

    async def _create_connection(self, exchange_id: str) -> ExchangeConnection:
        """Create a new connection for an exchange."""
        if exchange_id not in self.connections:
            raise ValueError(f"Exchange {exchange_id} not found")

        base_connection = self.connections[exchange_id]

        # Clone the exchange instance
        exchange_class = type(base_connection.exchange)
        exchange = exchange_class(base_connection.exchange)

        # Create new session
        session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=base_connection.exchange.timeout / 1000),
            connector=aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
        )

        connection = ExchangeConnection(
            exchange_id=exchange_id,
            exchange=exchange,
            status=ExchangeStatus.HEALTHY,
            session=session,
            weight=base_connection.weight,
            region=base_connection.region,
            capabilities=base_connection.capabilities
        )

        return connection

    async def _close_connection(self, connection: ExchangeConnection):
        """Close a connection."""
        try:
            await connection.session.close()
            if hasattr(connection.exchange, 'close'):
                await connection.exchange.close()
        except Exception as e:
            self.logger.error(f"Error closing connection {connection.exchange_id}: {e}")

    @asynccontextmanager
    async def get_connection(self, exchange_id: Optional[str] = None,
                           priority: Priority = Priority.NORMAL):
        """Get a connection using the configured strategy."""
        connection = None
        try:
            if exchange_id:
                # Specific exchange requested
                connection = await self.connection_pool.get_connection(exchange_id, self)
            else:
                # Use load balancing strategy
                connection = await self._get_connection_by_strategy(priority)

            if not connection:
                raise ExchangeUnavailableError("No available connections")

            yield connection

        except Exception as e:
            self.logger.error(f"Error getting connection: {e}")
            raise
        finally:
            if connection:
                await self.connection_pool.return_connection(connection)

    async def _get_connection_by_strategy(self, priority: Priority) -> Optional[ExchangeConnection]:
        """Get connection based on load balancing strategy."""
        available_connections = [
            conn for conn in self.connections.values()
            if conn.is_healthy() and conn.status != ExchangeStatus.MAINTENANCE
        ]

        if not available_connections:
            return None

        if self.strategy == ConnectionStrategy.ROUND_ROBIN:
            return available_connections[int(time.time()) % len(available_connections)]
        elif self.strategy == ConnectionStrategy.LEAST_LATENCY:
            return min(available_connections, key=lambda x: x.latency)
        elif self.strategy == ConnectionStrategy.WEIGHTED_ROUND_ROBIN:
            # Weighted random selection
            total_weight = sum(conn.weight for conn in available_connections)
            if total_weight == 0:
                return available_connections[0]

            import random
            r = random.uniform(0, total_weight)
            cumulative = 0
            for conn in available_connections:
                cumulative += conn.weight
                if r <= cumulative:
                    return conn
            return available_connections[-1]
        elif self.strategy == ConnectionStrategy.LEAST_CONNECTIONS:
            return min(available_connections, key=lambda x: x.active_connections)
        else:
            return available_connections[0]

    async def execute_request(self, method: str, *args, exchange_id: Optional[str] = None,
                            priority: Priority = Priority.NORMAL, **kwargs) -> Any:
        """Execute a request on an exchange."""
        start_time = time.time()

        async with self.get_connection(exchange_id, priority) as connection:
            try:
                # Check rate limit
                if not await self.rate_limiter.acquire_permit(
                    connection.exchange_id, method, priority
                ):
                    raise RateLimitExceededError(f"Rate limit exceeded for {connection.exchange_id}.{method}")

                # Execute the request
                result = await self._execute_exchange_request(connection, method, *args, **kwargs)

                # Update metrics
                latency = (time.time() - start_time) * 1000
                connection.update_success(latency)
                self.request_times[connection.exchange_id].append(latency)

                # Record metrics
                self.metrics.record_request(
                    exchange=connection.exchange_id,
                    method=method,
                    success=True,
                    latency=latency
                )

                return result

            except RateLimitError as e:
                await self.rate_limiter.handle_rate_limit_error(connection.exchange_id, method)
                connection.update_error(str(e))
                self.error_counts[connection.exchange_id] += 1
                raise RateLimitExceededError(f"Rate limit error: {e}")

            except NetworkError as e:
                connection.update_error(str(e))
                self.error_counts[connection.exchange_id] += 1

                # Check if we need to mark connection as degraded
                if connection.consecutive_errors > 3:
                    connection.status = ExchangeStatus.DEGRADED

                raise ExchangeConnectionError(f"Network error: {e}")

            except ExchangeError as e:
                connection.update_error(str(e))
                self.error_counts[connection.exchange_id] += 1
                raise ExchangeConnectionError(f"Exchange error: {e}")

            except Exception as e:
                connection.update_error(str(e))
                self.error_counts[connection.exchange_id] += 1
                raise ExchangeConnectionError(f"Unexpected error: {e}")

    async def _execute_exchange_request(self, connection: ExchangeConnection,
                                      method: str, *args, **kwargs) -> Any:
        """Execute a request on a specific exchange."""
        exchange_method = getattr(connection.exchange, method)

        if asyncio.iscoroutinefunction(exchange_method):
            return await exchange_method(*args, **kwargs)
        else:
            # Execute synchronous method in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, exchange_method, *args, **kwargs)

    async def _health_check_loop(self):
        """Background health check loop."""
        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(30)  # Health check every 30 seconds
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
                await asyncio.sleep(5)

    async def _perform_health_checks(self):
        """Perform health checks on all connections."""
        tasks = []

        for connection in self.connections.values():
            task = asyncio.create_task(self._check_connection_health(connection))
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_connection_health(self, connection: ExchangeConnection):
        """Check health of a single connection."""
        try:
            start_time = time.time()

            # Use ping or fetch time as health check
            if hasattr(connection.exchange, 'ping'):
                await self._execute_exchange_request(connection, 'ping')
            else:
                await self._execute_exchange_request(connection, 'fetch_time')

            latency = (time.time() - start_time) * 1000

            # Update connection status based on health check
            if latency > 5000:  # 5 seconds
                connection.status = ExchangeStatus.DEGRADED
            elif latency > 10000:  # 10 seconds
                connection.status = ExchangeStatus.OFFLINE
            else:
                connection.status = ExchangeStatus.HEALTHY

        except Exception as e:
            self.logger.error(f"Health check failed for {connection.exchange_id}: {e}")
            connection.status = ExchangeStatus.OFFLINE
            connection.update_error(str(e))

    async def _metrics_loop(self):
        """Background metrics collection loop."""
        while self._running:
            try:
                await self._collect_metrics()
                await asyncio.sleep(60)  # Collect metrics every minute
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(5)

    async def _collect_metrics(self):
        """Collect and report metrics."""
        for exchange_id, connection in self.connections.items():
            # Calculate average latency
            if self.request_times[exchange_id]:
                avg_latency = sum(self.request_times[exchange_id]) / len(self.request_times[exchange_id])
            else:
                avg_latency = 0

            # Record metrics
            self.metrics.record_exchange_metrics(
                exchange_id=exchange_id,
                status=connection.status.value,
                latency=avg_latency,
                success_rate=connection.get_success_rate(),
                health_score=connection.health_score,
                active_connections=connection.active_connections
            )

    async def get_exchange_status(self, exchange_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of exchanges."""
        if exchange_id:
            if exchange_id in self.connections:
                connection = self.connections[exchange_id]
                return {
                    "exchange_id": connection.exchange_id,
                    "status": connection.status.value,
                    "latency": connection.latency,
                    "success_rate": connection.get_success_rate(),
                    "health_score": connection.health_score,
                    "active_connections": connection.active_connections,
                    "total_requests": connection.total_requests,
                    "error_count": connection.error_count,
                    "last_ping": connection.last_ping,
                    "region": connection.region,
                    "capabilities": connection.capabilities
                }
            return {}
        else:
            return {
                exchange_id: {
                    "status": conn.status.value,
                    "latency": conn.latency,
                    "success_rate": conn.get_success_rate(),
                    "health_score": conn.health_score,
                    "active_connections": conn.active_connections,
                    "total_requests": conn.total_requests,
                    "error_count": conn.error_count
                }
                for exchange_id, conn in self.connections.items()
            }

    async def close(self):
        """Close the exchange manager."""
        self._running = False

        # Cancel background tasks
        if self._health_check_task:
            self._health_check_task.cancel()
        if self._metrics_task:
            self._metrics_task.cancel()

        # Wait for tasks to complete
        if self._health_check_task or self._metrics_task:
            await asyncio.gather(
                self._health_check_task,
                self._metrics_task,
                return_exceptions=True
            )

        # Stop connection pool
        await self.connection_pool.stop()

        # Close all connections
        for connection in self.connections.values():
            await self._close_connection(connection)

        # Close Redis client
        if hasattr(self, 'redis_client'):
            await self.redis_client.close()

        self.connections.clear()
        self.logger.info("Exchange Manager closed")


# Global exchange manager instance
exchange_manager = ExchangeManager()