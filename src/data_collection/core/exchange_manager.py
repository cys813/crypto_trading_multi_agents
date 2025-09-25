"""
Exchange Manager - Manages connections to multiple cryptocurrency exchanges.

This module provides a unified interface for managing connections to various
cryptocurrency exchanges using the CCXT library.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import ccxt.async_support as ccxt
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExchangeConfig:
    """Configuration for exchange connection."""
    name: str
    api_key: Optional[str] = None
    secret: Optional[str] = None
    passphrase: Optional[str] = None
    sandbox: bool = False
    rate_limit: int = 120  # requests per minute
    timeout: int = 10000  # milliseconds


class ExchangeManager:
    """Manages multiple exchange connections with load balancing and failover."""

    def __init__(self, config: Dict[str, ExchangeConfig]):
        self.config = config
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.connection_stats: Dict[str, Dict[str, Any]] = {}
        self.last_usage: Dict[str, datetime] = {}
        self.is_initialized = False

    async def initialize(self):
        """Initialize all exchange connections."""
        logger.info("Initializing exchange manager...")

        for name, exchange_config in self.config.items():
            try:
                await self._create_exchange(name, exchange_config)
                self.connection_stats[name] = {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'last_success': None,
                    'last_error': None,
                    'consecutive_failures': 0,
                    'is_healthy': True
                }
                self.last_usage[name] = datetime.min
                logger.info(f"Successfully initialized {name} exchange")

            except Exception as e:
                logger.error(f"Failed to initialize {name} exchange: {e}")
                self.connection_stats[name] = {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'last_success': None,
                    'last_error': str(e),
                    'consecutive_failures': 1,
                    'is_healthy': False
                }

        self.is_initialized = True
        logger.info(f"Exchange manager initialized with {len(self.exchanges)} exchanges")

    async def _create_exchange(self, name: str, config: ExchangeConfig):
        """Create and configure an exchange instance."""
        exchange_class = getattr(ccxt, name.lower())

        exchange = exchange_class({
            'apiKey': config.api_key,
            'secret': config.secret,
            'password': config.passphrase,
            'sandbox': config.sandbox,
            'timeout': config.timeout,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
                'adjustForTimeDifference': True,
            }
        })

        # Test connection
        await exchange.load_markets()
        self.exchanges[name] = exchange

    async def get_exchange(self, name: str) -> ccxt.Exchange:
        """Get an exchange instance with health check."""
        if not self.is_initialized:
            await self.initialize()

        if name not in self.exchanges:
            raise ValueError(f"Exchange {name} not found")

        exchange = self.exchanges[name]

        # Health check
        if not await self._check_exchange_health(name):
            logger.warning(f"Exchange {name} is unhealthy, attempting recovery...")
            await self._recover_exchange(name)

        return exchange

    async def _check_exchange_health(self, name: str) -> bool:
        """Check if an exchange is healthy."""
        try:
            exchange = self.exchanges[name]
            await exchange.fetch_time()
            return True
        except Exception as e:
            logger.warning(f"Health check failed for {name}: {e}")
            self.connection_stats[name]['is_healthy'] = False
            self.connection_stats[name]['last_error'] = str(e)
            self.connection_stats[name]['consecutive_failures'] += 1
            return False

    async def _recover_exchange(self, name: str):
        """Attempt to recover an unhealthy exchange."""
        try:
            config = self.config[name]

            # Create new exchange instance
            exchange_class = getattr(ccxt, name.lower())
            exchange = exchange_class({
                'apiKey': config.api_key,
                'secret': config.secret,
                'password': config.passphrase,
                'sandbox': config.sandbox,
                'timeout': config.timeout,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                    'adjustForTimeDifference': True,
                }
            })

            # Test new connection
            await exchange.load_markets()

            # Replace old exchange
            if name in self.exchanges:
                await self.exchanges[name].close()

            self.exchanges[name] = exchange
            self.connection_stats[name]['is_healthy'] = True
            self.connection_stats[name]['consecutive_failures'] = 0
            self.connection_stats[name]['last_success'] = datetime.now()

            logger.info(f"Successfully recovered {name} exchange")

        except Exception as e:
            logger.error(f"Failed to recover {name} exchange: {e}")

    async def execute_request(self, exchange_name: str, method: str, *args, **kwargs):
        """Execute a request with rate limiting and error handling."""
        if exchange_name not in self.exchanges:
            raise ValueError(f"Exchange {exchange_name} not found")

        # Rate limiting
        await self._wait_for_rate_limit(exchange_name)

        stats = self.connection_stats[exchange_name]
        stats['total_requests'] += 1

        try:
            exchange = self.exchanges[exchange_name]
            method_func = getattr(exchange, method)
            result = await method_func(*args, **kwargs)

            stats['successful_requests'] += 1
            stats['last_success'] = datetime.now()
            stats['consecutive_failures'] = 0
            stats['is_healthy'] = True

            self.last_usage[exchange_name] = datetime.now()

            return result

        except Exception as e:
            stats['failed_requests'] += 1
            stats['last_error'] = str(e)
            stats['consecutive_failures'] += 1

            if stats['consecutive_failures'] > 3:
                stats['is_healthy'] = False

            logger.error(f"Request failed for {exchange_name}: {e}")
            raise

    async def _wait_for_rate_limit(self, exchange_name: str):
        """Wait if rate limit would be exceeded."""
        config = self.config[exchange_name]
        last_usage = self.last_usage[exchange_name]

        time_since_last_use = (datetime.now() - last_usage).total_seconds()
        min_interval = 60.0 / config.rate_limit

        if time_since_last_use < min_interval:
            wait_time = min_interval - time_since_last_use
            await asyncio.sleep(wait_time)

    async def get_best_exchange(self, symbol: str) -> str:
        """Get the best exchange for a symbol based on health and load."""
        available_exchanges = []

        for name in self.exchanges:
            if self.connection_stats[name]['is_healthy']:
                available_exchanges.append(name)

        if not available_exchanges:
            raise RuntimeError("No healthy exchanges available")

        # Simple load balancing - choose the least recently used
        best_exchange = min(available_exchanges, key=lambda x: self.last_usage[x])
        return best_exchange

    async def close_all(self):
        """Close all exchange connections."""
        logger.info("Closing all exchange connections...")

        for name, exchange in self.exchanges.items():
            try:
                await exchange.close()
                logger.info(f"Closed {name} exchange connection")
            except Exception as e:
                logger.error(f"Error closing {name} exchange: {e}")

        self.exchanges.clear()
        self.is_initialized = False

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get connection statistics for all exchanges."""
        return self.connection_stats.copy()

    async def get_markets(self, exchange_name: str) -> Dict[str, Any]:
        """Get markets for a specific exchange."""
        exchange = await self.get_exchange(exchange_name)
        return exchange.markets

    async def get_ticker(self, exchange_name: str, symbol: str) -> Dict[str, Any]:
        """Get ticker for a symbol on a specific exchange."""
        return await self.execute_request(exchange_name, 'fetch_ticker', symbol)

    async def get_orderbook(self, exchange_name: str, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get orderbook for a symbol on a specific exchange."""
        return await self.execute_request(exchange_name, 'fetch_order_book', symbol, limit)

    async def get_trades(self, exchange_name: str, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trades for a symbol on a specific exchange."""
        return await self.execute_request(exchange_name, 'fetch_trades', symbol, limit)

    async def get_ohlcv(self, exchange_name: str, symbol: str, timeframe: str = '1m',
                       since: Optional[int] = None, limit: int = 100) -> List[List[float]]:
        """Get OHLCV data for a symbol on a specific exchange."""
        return await self.execute_request(exchange_name, 'fetch_ohlcv', symbol, timeframe, since, limit)