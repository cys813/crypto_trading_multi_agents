import pytest
import asyncio
import time
from datetime import datetime
from news_collection.utils.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test cases for RateLimiter."""

    @pytest.mark.asyncio
    async def test_rate_limiter_basic(self):
        """Test basic rate limiting functionality."""
        limiter = RateLimiter(max_requests=5, time_window=60)

        # Should be able to make 5 requests immediately
        for i in range(5):
            await limiter.acquire()

        # 6th request should wait
        start_time = time.time()
        await limiter.acquire()
        elapsed = time.time() - start_time

        # Should have waited approximately 12 seconds (60/5)
        assert elapsed >= 10  # Allow some buffer

    @pytest.mark.asyncio
    async def test_rate_limiter_refill(self):
        """Test rate limiter token refill over time."""
        limiter = RateLimiter(max_requests=2, time_window=1)  # 2 requests per 1 second

        # Use up tokens
        await limiter.acquire()
        await limiter.acquire()

        # Should wait for refill
        start_time = time.time()
        await limiter.acquire()
        elapsed = time.time() - start_time

        assert elapsed >= 0.4  # Should wait at least 0.5 seconds (1/2)

        # After waiting 1 second, should have 2 tokens again
        await asyncio.sleep(0.6)  # Wait for remaining time

        # Should be able to make 2 requests quickly
        start_time = time.time()
        await limiter.acquire()
        await limiter.acquire()
        elapsed = time.time() - start_time

        assert elapsed < 0.1  # Should be very fast

    @pytest.mark.asyncio
    async def test_rate_limiter_concurrent(self):
        """Test rate limiter with concurrent requests."""
        limiter = RateLimiter(max_requests=3, time_window=60)

        # Start 5 concurrent requests
        tasks = [limiter.acquire() for _ in range(5)]
        start_time = time.time()

        await asyncio.gather(*tasks)
        elapsed = time.time() - start_time

        # Should take approximately 40 seconds total (2 extra requests * 20 seconds each)
        assert elapsed >= 35  # Allow some buffer

    @pytest.mark.asyncio
    async def test_rate_limiter_remaining_tokens(self):
        """Test getting remaining tokens."""
        limiter = RateLimiter(max_requests=10, time_window=60)

        assert limiter.get_remaining_tokens() == 10

        await limiter.acquire()
        assert limiter.get_remaining_tokens() == 9

        await limiter.acquire()
        assert limiter.get_remaining_tokens() == 8

    @pytest.mark.asyncio
    async def test_rate_limiter_partial_refill(self):
        """Test partial token refill."""
        limiter = RateLimiter(max_requests=10, time_window=10)  # 10 requests per 10 seconds

        # Use all tokens
        for _ in range(10):
            await limiter.acquire()

        assert limiter.get_remaining_tokens() == 0

        # Wait 3 seconds (should get 3 tokens back)
        await asyncio.sleep(3.1)

        # Should have some tokens back
        remaining = limiter.get_remaining_tokens()
        assert remaining >= 2  # Should have at least 2 tokens back
        assert remaining <= 4   # But not more than 3 + 1 buffer

    @pytest.mark.asyncio
    async def test_rate_limiter_full_refill(self):
        """Test full token refill after time window."""
        limiter = RateLimiter(max_requests=5, time_window=1)  # 5 requests per 1 second

        # Use all tokens
        for _ in range(5):
            await limiter.acquire()

        assert limiter.get_remaining_tokens() == 0

        # Wait for full refill
        await asyncio.sleep(1.1)

        # Should have all tokens back
        assert limiter.get_remaining_tokens() == 5

        # Should be able to make requests quickly again
        start_time = time.time()
        for _ in range(5):
            await limiter.acquire()
        elapsed = time.time() - start_time

        assert elapsed < 0.1  # Should be very fast

    @pytest.mark.asyncio
    async def test_rate_limiter_zero_requests(self):
        """Test rate limiter with zero requests."""
        limiter = RateLimiter(max_requests=0, time_window=60)

        # Should always wait
        start_time = time.time()
        await limiter.acquire()
        elapsed = time.time() - start_time

        assert elapsed >= 0.01  # Should wait at least a bit

    @pytest.mark.asyncio
    async def test_rate_limiter_single_request(self):
        """Test rate limiter with single request limit."""
        limiter = RateLimiter(max_requests=1, time_window=1)

        # First request should be fast
        start_time = time.time()
        await limiter.acquire()
        elapsed = time.time() - start_time
        assert elapsed < 0.1

        # Second request should wait
        start_time = time.time()
        await limiter.acquire()
        elapsed = time.time() - start_time
        assert elapsed >= 0.9  # Should wait ~1 second