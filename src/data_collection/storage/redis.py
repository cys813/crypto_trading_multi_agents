"""
Redis storage implementation for caching and real-time data access.

This module provides Redis-based caching for market data, supporting
various data types and optimized for high-frequency access patterns.
"""

import json
import logging
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import asyncio
import aioredis

from ..config.settings import get_settings


class RedisStorage:
    """Redis storage implementation for caching and real-time data."""

    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.redis: Optional[aioredis.Redis] = None
        self._connection_lock = asyncio.Lock()

    async def initialize(self):
        """Initialize Redis connection."""
        async with self._connection_lock:
            if self.redis is None:
                try:
                    self.redis = aioredis.from_url(
                        self.settings.redis_url,
                        encoding="utf-8",
                        decode_responses=True
                    )
                    # Test connection
                    await self.redis.ping()
                    self.logger.info("Redis connection established")
                except Exception as e:
                    self.logger.error(f"Failed to connect to Redis: {e}")
                    raise

    async def close(self):
        """Close Redis connection."""
        async with self._connection_lock:
            if self.redis:
                await self.redis.close()
                self.redis = None
                self.logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[str]:
        """Get a value from Redis."""
        try:
            if not self.redis:
                await self.initialize()

            value = await self.redis.get(key)
            return value
        except Exception as e:
            self.logger.error(f"Redis GET failed for key {key}: {e}")
            return None

    async def set(self, key: str, value: str, ttl: Optional[int] = None):
        """Set a value in Redis with optional TTL."""
        try:
            if not self.redis:
                await self.initialize()

            if ttl:
                await self.redis.setex(key, ttl, value)
            else:
                await self.redis.set(key, value)
        except Exception as e:
            self.logger.error(f"Redis SET failed for key {key}: {e}")

    async def delete(self, key: str):
        """Delete a key from Redis."""
        try:
            if not self.redis:
                await self.initialize()

            await self.redis.delete(key)
        except Exception as e:
            self.logger.error(f"Redis DELETE failed for key {key}: {e}")

    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis."""
        try:
            if not self.redis:
                await self.initialize()

            return await self.redis.exists(key) > 0
        except Exception as e:
            self.logger.error(f"Redis EXISTS failed for key {key}: {e}")
            return False

    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON data from Redis."""
        try:
            value = await self.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            self.logger.error(f"Redis GET JSON failed for key {key}: {e}")
            return None

    async def set_json(self, key: str, data: Any, ttl: Optional[int] = None):
        """Set JSON data in Redis with optional TTL."""
        try:
            json_data = json.dumps(data, default=str)
            await self.set(key, json_data, ttl)
        except Exception as e:
            self.logger.error(f"Redis SET JSON failed for key {key}: {e}")

    async def get_hash(self, key: str) -> Optional[Dict[str, str]]:
        """Get hash data from Redis."""
        try:
            if not self.redis:
                await self.initialize()

            return await self.redis.hgetall(key)
        except Exception as e:
            self.logger.error(f"Redis HGETALL failed for key {key}: {e}")
            return None

    async def set_hash(self, key: str, data: Dict[str, str], ttl: Optional[int] = None):
        """Set hash data in Redis with optional TTL."""
        try:
            if not self.redis:
                await self.initialize()

            await self.redis.hset(key, mapping=data)
            if ttl:
                await self.redis.expire(key, ttl)
        except Exception as e:
            self.logger.error(f"Redis HSET failed for key {key}: {e}")

    async def get_list(self, key: str) -> List[str]:
        """Get list data from Redis."""
        try:
            if not self.redis:
                await self.initialize()

            return await self.redis.lrange(key, 0, -1)
        except Exception as e:
            self.logger.error(f"Redis LRANGE failed for key {key}: {e}")
            return []

    async def set_list(self, key: str, data: List[str], ttl: Optional[int] = None):
        """Set list data in Redis with optional TTL."""
        try:
            if not self.redis:
                await self.initialize()

            # Delete existing list
            await self.redis.delete(key)
            # Add new elements
            if data:
                await self.redis.lpush(key, *data)
            if ttl:
                await self.redis.expire(key, ttl)
        except Exception as e:
            self.logger.error(f"Redis LPUSH failed for key {key}: {e}")

    async def add_to_set(self, key: str, value: str):
        """Add value to Redis set."""
        try:
            if not self.redis:
                await self.initialize()

            await self.redis.sadd(key, value)
        except Exception as e:
            self.logger.error(f"Redis SADD failed for key {key}: {e}")

    async def is_in_set(self, key: str, value: str) -> bool:
        """Check if value is in Redis set."""
        try:
            if not self.redis:
                await self.initialize()

            return await self.redis.sismember(key, value)
        except Exception as e:
            self.logger.error(f"Redis SISMEMBER failed for key {key}: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter in Redis."""
        try:
            if not self.redis:
                await self.initialize()

            return await self.redis.incrby(key, amount)
        except Exception as e:
            self.logger.error(f"Redis INCRBY failed for key {key}: {e}")
            return 0

    async def expire(self, key: str, ttl: int):
        """Set TTL for a key."""
        try:
            if not self.redis:
                await self.initialize()

            await self.redis.expire(key, ttl)
        except Exception as e:
            self.logger.error(f"Redis EXPIRE failed for key {key}: {e}")

    async def ttl(self, key: str) -> int:
        """Get TTL for a key."""
        try:
            if not self.redis:
                await self.initialize()

            return await self.redis.ttl(key)
        except Exception as e:
            self.logger.error(f"Redis TTL failed for key {key}: {e}")
            return -1

    async def keys(self, pattern: str) -> List[str]:
        """Get keys matching pattern."""
        try:
            if not self.redis:
                await self.initialize()

            return await self.redis.keys(pattern)
        except Exception as e:
            self.logger.error(f"Redis KEYS failed for pattern {pattern}: {e}")
            return []

    async def pipeline(self):
        """Get Redis pipeline for batch operations."""
        if not self.redis:
            await self.initialize()

        return self.redis.pipeline()

    async def cache_market_data(self, data_type: str, exchange: str, symbol: str,
                              data: Any, ttl: int = 300):
        """Cache market data with standardized key format."""
        try:
            key = f"{data_type}:{exchange}:{symbol}"
            await self.set_json(key, data, ttl)
        except Exception as e:
            self.logger.error(f"Failed to cache market data: {e}")

    async def get_cached_market_data(self, data_type: str, exchange: str, symbol: str) -> Optional[Any]:
        """Get cached market data."""
        try:
            key = f"{data_type}:{exchange}:{symbol}"
            return await self.get_json(key)
        except Exception as e:
            self.logger.error(f"Failed to get cached market data: {e}")
            return None

    async def cache_ohlcv_data(self, exchange: str, symbol: str, timeframe: str,
                             ohlcv_data: List[Dict], ttl: int = 300):
        """Cache OHLCV data."""
        try:
            key = f"ohlcv:{exchange}:{symbol}:{timeframe}"
            await self.set_json(key, ohlcv_data, ttl)
        except Exception as e:
            self.logger.error(f"Failed to cache OHLCV data: {e}")

    async def get_cached_ohlcv_data(self, exchange: str, symbol: str, timeframe: str) -> Optional[List[Dict]]:
        """Get cached OHLCV data."""
        try:
            key = f"ohlcv:{exchange}:{symbol}:{timeframe}"
            return await self.get_json(key)
        except Exception as e:
            self.logger.error(f"Failed to get cached OHLCV data: {e}")
            return None

    async def cache_ticker_data(self, exchange: str, symbol: str, ticker_data: Dict, ttl: int = 60):
        """Cache ticker data."""
        try:
            key = f"ticker:{exchange}:{symbol}"
            await self.set_json(key, ticker_data, ttl)
        except Exception as e:
            self.logger.error(f"Failed to cache ticker data: {e}")

    async def get_cached_ticker_data(self, exchange: str, symbol: str) -> Optional[Dict]:
        """Get cached ticker data."""
        try:
            key = f"ticker:{exchange}:{symbol}"
            return await self.get_json(key)
        except Exception as e:
            self.logger.error(f"Failed to get cached ticker data: {e}")
            return None

    async def cache_orderbook_data(self, exchange: str, symbol: str, orderbook_data: Dict, ttl: int = 30):
        """Cache order book data."""
        try:
            key = f"orderbook:{exchange}:{symbol}"
            await self.set_json(key, orderbook_data, ttl)
        except Exception as e:
            self.logger.error(f"Failed to cache order book data: {e}")

    async def get_cached_orderbook_data(self, exchange: str, symbol: str) -> Optional[Dict]:
        """Get cached order book data."""
        try:
            key = f"orderbook:{exchange}:{symbol}"
            return await self.get_json(key)
        except Exception as e:
            self.logger.error(f"Failed to get cached order book data: {e}")
            return None

    async def cache_trades_data(self, exchange: str, symbol: str, trades_data: List[Dict], ttl: int = 60):
        """Cache trades data."""
        try:
            key = f"trades:{exchange}:{symbol}"
            await self.set_json(key, trades_data, ttl)
        except Exception as e:
            self.logger.error(f"Failed to cache trades data: {e}")

    async def get_cached_trades_data(self, exchange: str, symbol: str) -> Optional[List[Dict]]:
        """Get cached trades data."""
        try:
            key = f"trades:{exchange}:{symbol}"
            return await self.get_json(key)
        except Exception as e:
            self.logger.error(f"Failed to get cached trades data: {e}")
            return None

    async def cache_last_timestamp(self, exchange: str, symbol: str, timeframe: str, timestamp: int):
        """Cache last timestamp for incremental updates."""
        try:
            key = f"last_timestamp:{exchange}:{symbol}:{timeframe}"
            await self.set(key, str(timestamp), ttl=86400)  # 24 hour TTL
        except Exception as e:
            self.logger.error(f"Failed to cache last timestamp: {e}")

    async def get_last_timestamp(self, exchange: str, symbol: str, timeframe: str) -> Optional[int]:
        """Get cached last timestamp."""
        try:
            key = f"last_timestamp:{exchange}:{symbol}:{timeframe}"
            timestamp_str = await self.get(key)
            return int(timestamp_str) if timestamp_str else None
        except Exception as e:
            self.logger.error(f"Failed to get cached last timestamp: {e}")
            return None

    async def cache_quality_score(self, data_type: str, exchange: str, symbol: str,
                               quality_score: float, ttl: int = 300):
        """Cache quality score."""
        try:
            key = f"quality:{data_type}:{exchange}:{symbol}"
            await self.set(key, str(quality_score), ttl)
        except Exception as e:
            self.logger.error(f"Failed to cache quality score: {e}")

    async def get_quality_score(self, data_type: str, exchange: str, symbol: str) -> Optional[float]:
        """Get cached quality score."""
        try:
            key = f"quality:{data_type}:{exchange}:{symbol}"
            score_str = await self.get(key)
            return float(score_str) if score_str else None
        except Exception as e:
            self.logger.error(f"Failed to get cached quality score: {e}")
            return None

    async def increment_collection_counter(self, exchange: str, data_type: str, status: str = 'success'):
        """Increment collection counter."""
        try:
            key = f"stats:{exchange}:{data_type}:{status}"
            await self.increment(key)
        except Exception as e:
            self.logger.error(f"Failed to increment collection counter: {e}")

    async def get_collection_stats(self, exchange: Optional[str] = None, data_type: Optional[str] = None) -> Dict[str, int]:
        """Get collection statistics."""
        try:
            stats = {}
            if exchange and data_type:
                # Get stats for specific exchange and data type
                success_key = f"stats:{exchange}:{data_type}:success"
                failure_key = f"stats:{exchange}:{data_type}:failure"
                stats['success'] = int(await self.get(success_key) or 0)
                stats['failure'] = int(await self.get(failure_key) or 0)
            else:
                # Get all stats
                pattern = "stats:*"
                keys = await self.keys(pattern)
                for key in keys:
                    parts = key.split(':')
                    if len(parts) == 4:
                        ex, dt, status = parts[1], parts[2], parts[3]
                        if ex not in stats:
                            stats[ex] = {}
                        if dt not in stats[ex]:
                            stats[ex][dt] = {'success': 0, 'failure': 0}
                        stats[ex][dt][status] = int(await self.get(key) or 0)

            return stats
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {e}")
            return {}

    async def cleanup_expired_keys(self, pattern: str = "*"):
        """Clean up expired keys."""
        try:
            if not self.redis:
                await self.initialize()

            keys = await self.keys(pattern)
            cleaned_count = 0

            for key in keys:
                ttl = await self.ttl(key)
                if ttl == -2:  # Key expired
                    await self.delete(key)
                    cleaned_count += 1

            if cleaned_count > 0:
                self.logger.info(f"Cleaned up {cleaned_count} expired keys")

        except Exception as e:
            self.logger.error(f"Failed to cleanup expired keys: {e}")

    async def get_cache_info(self) -> Dict[str, Any]:
        """Get Redis cache information."""
        try:
            if not self.redis:
                await self.initialize()

            info = await self.redis.info()
            return {
                'connected': True,
                'used_memory': info.get('used_memory_human', 'N/A'),
                'connected_clients': info.get('connected_clients', 0),
                'total_connections_received': info.get('total_connections_received', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_commands_processed': info.get('total_commands_processed', 0)
            }
        except Exception as e:
            self.logger.error(f"Failed to get cache info: {e}")
            return {'connected': False, 'error': str(e)}

    async def health_check(self) -> bool:
        """Perform Redis health check."""
        try:
            if not self.redis:
                await self.initialize()

            await self.redis.ping()
            return True
        except Exception as e:
            self.logger.error(f"Redis health check failed: {e}")
            return False