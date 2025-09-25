import asyncio
import time
from typing import Optional
import logging


class RateLimiter:
    """Rate limiter implementation using token bucket algorithm."""

    def __init__(self, max_requests: int, time_window: int):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.tokens = max_requests
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger(__name__)

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        async with self._lock:
            await self._refill()

            if self.tokens <= 0:
                wait_time = self._calculate_wait_time()
                self.logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                await self._refill()

            self.tokens -= 1

    async def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill

        if elapsed >= self.time_window:
            # Refill all tokens
            self.tokens = self.max_requests
            self.last_refill = now
        else:
            # Partial refill based on elapsed time
            refill_amount = (elapsed / self.time_window) * self.max_requests
            self.tokens = min(self.max_requests, self.tokens + refill_amount)

    def _calculate_wait_time(self) -> float:
        """Calculate wait time until next token is available."""
        return self.time_window / self.max_requests

    def get_remaining_tokens(self) -> int:
        """Get remaining tokens (thread-safe version not implemented for simplicity)."""
        return int(self.tokens)