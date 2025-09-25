"""
Storage module for data persistence and caching.

This module provides storage implementations for different backends
including TimescaleDB for time-series data and Redis for caching.
"""

from .redis import RedisStorage

__all__ = [
    'RedisStorage'
]