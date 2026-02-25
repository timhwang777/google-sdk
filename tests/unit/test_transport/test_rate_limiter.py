"""Tests for the token bucket rate limiter."""

import time
from unittest.mock import patch

import pytest

from google_sdk._transport.rate_limiter import RateLimiter, TokenBucket


def test_token_bucket_allows_immediate():
    bucket = TokenBucket(rate=10.0)
    start = time.monotonic()
    bucket.acquire()
    elapsed = time.monotonic() - start
    assert elapsed < 0.1  # Should be nearly instant


def test_token_bucket_delays_when_empty():
    bucket = TokenBucket(rate=2.0)  # 2 per second
    # Drain the bucket
    with patch("time.sleep") as mock_sleep:
        # First call should be free
        bucket.acquire()
        # Manually drain tokens
        bucket._tokens = 0.0
        bucket.acquire()  # Should sleep
    mock_sleep.assert_called_once()
    wait = mock_sleep.call_args[0][0]
    assert wait > 0


def test_rate_limiter_no_limit():
    limiter = RateLimiter(default_rate=None)
    # Should not block
    start = time.monotonic()
    limiter.acquire("drive")
    elapsed = time.monotonic() - start
    assert elapsed < 0.05


def test_rate_limiter_per_service():
    limiter = RateLimiter(default_rate=100.0)
    # Should create separate buckets per service
    limiter.acquire("drive")
    limiter.acquire("calendar")
    assert "drive" in limiter._buckets
    assert "calendar" in limiter._buckets
    assert limiter._buckets["drive"] is not limiter._buckets["calendar"]


@pytest.mark.asyncio
async def test_rate_limiter_async():
    limiter = RateLimiter(default_rate=None)
    # Should not block
    await limiter.async_acquire("drive")
