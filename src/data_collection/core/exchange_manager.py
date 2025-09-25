"""
Exchange Manager for managing multiple cryptocurrency exchanges.

This module provides a unified interface for managing connections to multiple
cryptocurrency exchanges using the CCXT library, with support for connection pooling,
rate limiting, and failover mechanisms.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import ccxt
from ccxt.base.exchange import Exchange
from ccxt.base.errors import NetworkError, ExchangeError, RateLimitError

from ..config.settings import get_settings
from ..models.database import get_session
from ..utils.metrics import MetricsCollector


class ExchangeManager:
    """Manages multiple cryptocurrency exchange connections."""

    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.metrics = MetricsCollector()

        # Exchange instances
        self.exchanges: Dict[str, Exchange] = {}
        self.exchange_status: Dict[str, Dict] = {}

        # Rate limiting and connection management
        self.rate_limiter: Dict[str, Dict] = {}
        self.connection_pools: Dict[str, List[Exchange]] = {}

        # Health monitoring
        self.last_health_check: Dict[str, datetime] = {}
        self.health_check_interval = 30  # seconds

        # Load exchange configurations
        self._load_exchange_configs()

        # Initialize background tasks
        self._background_tasks = []

    def _load_exchange_configs(self):
        """Load exchange configurations from settings."""
        for exchange_name, config in self.settings.EXCHANGE_CONFIGS.items():
            try:
                self._initialize_exchange(exchange_name, config)
                self.logger.info(f"Loaded configuration for {exchange_name}")
            except Exception as e:
                self.logger.error(f"Failed to initialize {exchange_name}: {e}")

    def _initialize_exchange(self, exchange_name: str, config: Dict[str, Any]):
        """Initialize a single exchange with given configuration."""
        try:
            # Get exchange class from CCXT
            exchange_class = getattr(ccxt, exchange_name)

            # Create exchange instance
            exchange = exchange_class(config)

            # Verify exchange is available
            if not exchange:
                raise ValueError(f"Exchange {exchange_name} not available in CCXT")

            # Store exchange instance
            self.exchanges[exchange_name] = exchange

            # Initialize rate limiter
            self.rate_limiter[exchange_name] = {
                'requests': 0,
                'last_reset': datetime.now(),
                'limit': config.get('rateLimit', 100)
            }

            # Initialize connection pool
            pool_size = max(1, min(5, self.settings.MAX_CONCURRENT_CONNECTIONS // 10))
            self.connection_pools[exchange_name] = []

            for i in range(pool_size):
                pool_exchange = exchange_class(config)
                pool_exchange.sandbox = config.get('sandbox', False)
                self.connection_pools[exchange_name].append(pool_exchange)

            # Initialize status
            self.exchange_status[exchange_name] = {
                'status': 'initialized',
                'last_check': datetime.now(),
                'error_count': 0,
                'success_count': 0,
                'latency': 0
            }

            self.logger.info(f"Initialized {exchange_name} with pool size {pool_size}")

        except Exception as e:
            self.logger.error(f"Failed to initialize {exchange_name}: {e}")
            raise

    async def get_exchange(self, exchange_name: str) -> Optional[Exchange]:
        """Get an exchange instance from the connection pool."""
        if exchange_name not in self.exchanges:
            self.logger.error(f"Exchange {exchange_name} not found")
            return None

        # Check rate limit
        if not self._check_rate_limit(exchange_name):
            await asyncio.sleep(0.1)  # Wait briefly
            return await self.get_exchange(exchange_name)

        # Get from connection pool
        if self.connection_pools[exchange_name]:
            exchange = self.connection_pools[exchange_name].pop(0)
            return exchange

        # Fallback to main instance
        return self.exchanges[exchange_name]

    async def return_exchange(self, exchange_name: str, exchange: Exchange):
        """Return an exchange instance to the connection pool."""
        if exchange_name in self.connection_pools:
            self.connection_pools[exchange_name].append(exchange)

    def _check_rate_limit(self, exchange_name: str) -> bool:
        """Check if rate limit allows for new requests."""
        if exchange_name not in self.rate_limiter:
            return True

        limiter = self.rate_limiter[exchange_name]
        now = datetime.now()

        # Reset counter if time window has passed
        if (now - limiter['last_reset']).total_seconds() >= 60:
            limiter['requests'] = 0
            limiter['last_reset'] = now

        # Check if within limit
        if limiter['requests'] < limiter['limit']:
            limiter['requests'] += 1
            return True

        return False

    async def execute_request(self, exchange_name: str, method: str, *args, **kwargs) -> Any:
        """Execute a request on an exchange with error handling and retries."""
        start_time = datetime.now()

        try:
            # Get exchange instance
            exchange = await self.get_exchange(exchange_name)
            if not exchange:
                raise ValueError(f"Exchange {exchange_name} not available")

            # Execute the method
            if hasattr(exchange, method):
                result = await getattr(exchange, method)(*args, **kwargs)

                # Update metrics
                latency = (datetime.now() - start_time).total_seconds() * 1000
                self.metrics.record_request(exchange_name, method, True, latency)

                # Update status
                if exchange_name in self.exchange_status:
                    self.exchange_status[exchange_name]['success_count'] += 1
                    self.exchange_status[exchange_name]['latency'] = latency
                    self.exchange_status[exchange_name]['last_check'] = datetime.now()

                return result
            else:
                raise AttributeError(f"Method {method} not found on {exchange_name}")

        except (NetworkError, RateLimitError) as e:
            # Handle network and rate limit errors
            self.logger.warning(f"Network/rate limit error on {exchange_name}.{method}: {e}")

            # Update metrics
            latency = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics.record_request(exchange_name, method, False, latency)

            # Update status
            if exchange_name in self.exchange_status:
                self.exchange_status[exchange_name]['error_count'] += 1

            # Retry logic
            retry_count = kwargs.get('retry_count', 0)
            if retry_count < self.settings.MAX_RETRIES:
                kwargs['retry_count'] = retry_count + 1
                await asyncio.sleep(self.settings.RETRY_DELAY / 1000)
                return await self.execute_request(exchange_name, method, *args, **kwargs)
            else:
                raise

        except ExchangeError as e:
            # Handle exchange-specific errors
            self.logger.error(f"Exchange error on {exchange_name}.{method}: {e}")

            # Update metrics
            latency = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics.record_request(exchange_name, method, False, latency)

            # Update status
            if exchange_name in self.exchange_status:
                self.exchange_status[exchange_name]['error_count'] += 1

            raise

        except Exception as e:
            # Handle unexpected errors
            self.logger.error(f"Unexpected error on {exchange_name}.{method}: {e}")

            # Update metrics
            latency = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics.record_request(exchange_name, method, False, latency)

            # Update status
            if exchange_name in self.exchange_status:
                self.exchange_status[exchange_name]['error_count'] += 1

            raise

        finally:
            # Return exchange to pool
            if 'exchange' in locals():
                await self.return_exchange(exchange_name, exchange)

    async def get_markets(self, exchange_name: str) -> List[Dict]:
        """Get markets information for an exchange."""
        return await self.execute_request(exchange_name, 'fetch_markets')

    async def get_ticker(self, exchange_name: str, symbol: str) -> Dict:
        """Get ticker information for a symbol."""
        return await self.execute_request(exchange_name, 'fetch_ticker', symbol)

    async def get_ohlcv(self, exchange_name: str, symbol: str, timeframe: str = '1m',
                       since: Optional[int] = None, limit: Optional[int] = None) -> List:
        """Get OHLCV data for a symbol."""
        return await self.execute_request(exchange_name, 'fetch_ohlcv', symbol, timeframe, since, limit)

    async def get_order_book(self, exchange_name: str, symbol: str, limit: Optional[int] = None) -> Dict:
        """Get order book data for a symbol."""
        return await self.execute_request(exchange_name, 'fetch_order_book', symbol, limit)

    async def get_trades(self, exchange_name: str, symbol: str, since: Optional[int] = None,
                        limit: Optional[int] = None) -> List:
        """Get recent trades for a symbol."""
        return await self.execute_request(exchange_name, 'fetch_trades', symbol, since, limit)

    async def get_balance(self, exchange_name: str) -> Dict:
        """Get account balance for an exchange."""
        return await self.execute_request(exchange_name, 'fetch_balance')

    async def get_positions(self, exchange_name: str) -> List[Dict]:
        """Get open positions for an exchange."""
        return await self.execute_request(exchange_name, 'fetch_positions')

    async def get_orders(self, exchange_name: str, symbol: Optional[str] = None) -> List[Dict]:
        """Get open orders for an exchange."""
        return await self.execute_request(exchange_name, 'fetch_open_orders', symbol)

    async def get_order_status(self, exchange_name: str, order_id: str, symbol: str) -> Dict:
        """Get order status for a specific order."""
        return await self.execute_request(exchange_name, 'fetch_order', order_id, symbol)

    async def get_all_exchanges(self) -> List[str]:
        """Get list of all available exchanges."""
        return list(self.exchanges.keys())

    async def get_exchange_status(self, exchange_name: str) -> Dict:
        """Get status information for an exchange."""
        if exchange_name not in self.exchange_status:
            return {'status': 'not_found'}

        status = self.exchange_status[exchange_name].copy()

        # Calculate success rate
        total_requests = status['success_count'] + status['error_count']
        if total_requests > 0:
            status['success_rate'] = status['success_count'] / total_requests
        else:
            status['success_rate'] = 0

        # Check if exchange is healthy
        time_since_last_check = (datetime.now() - status['last_check']).total_seconds()
        status['healthy'] = (
            time_since_last_check < self.health_check_interval * 2 and
            status['success_rate'] > 0.9
        )

        return status

    async def health_check(self, exchange_name: Optional[str] = None):
        """Perform health check on exchange(s)."""
        if exchange_name:
            exchanges_to_check = [exchange_name]
        else:
            exchanges_to_check = list(self.exchanges.keys())

        for exchange_name in exchanges_to_check:
            try:
                start_time = datetime.now()

                # Simple health check - get markets
                markets = await self.get_markets(exchange_name)

                if markets:
                    status = 'healthy'
                    error = None
                else:
                    status = 'unhealthy'
                    error = 'No markets returned'

                latency = (datetime.now() - start_time).total_seconds() * 1000

                # Update status
                if exchange_name in self.exchange_status:
                    self.exchange_status[exchange_name]['last_check'] = datetime.now()
                    self.exchange_status[exchange_name]['latency'] = latency
                    self.exchange_status[exchange_name]['status'] = status

                self.logger.info(f"Health check {exchange_name}: {status} ({latency:.2f}ms)")

            except Exception as e:
                self.logger.error(f"Health check failed for {exchange_name}: {e}")

                if exchange_name in self.exchange_status:
                    self.exchange_status[exchange_name]['status'] = 'unhealthy'
                    self.exchange_status[exchange_name]['last_check'] = datetime.now()

    async def start_health_monitoring(self):
        """Start background health monitoring."""
        async def health_monitor():
            while True:
                try:
                    await self.health_check()
                    await asyncio.sleep(self.health_check_interval)
                except Exception as e:
                    self.logger.error(f"Health monitoring error: {e}")
                    await asyncio.sleep(10)  # Wait before retrying

        # Start health monitoring task
        task = asyncio.create_task(health_monitor())
        self._background_tasks.append(task)

    async def close(self):
        """Close all exchange connections and cleanup resources."""
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        # Close exchange connections
        for exchange_name, exchange in self.exchanges.items():
            try:
                if hasattr(exchange, 'close'):
                    await exchange.close()
            except Exception as e:
                self.logger.error(f"Error closing {exchange_name}: {e}")

        # Clear data structures
        self.exchanges.clear()
        self.exchange_status.clear()
        self.rate_limiter.clear()
        self.connection_pools.clear()

        self.logger.info("Exchange manager closed")