"""Per-service token bucket rate limiter."""

from __future__ import annotations

import threading
import time


class TokenBucket:
    """Simple token bucket for rate limiting."""

    def __init__(self, rate: float) -> None:
        """
        Args:
            rate: Tokens per second (= max requests per second).
        """
        self._rate = rate
        self._tokens = rate
        self._last = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until a token is available."""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            self._last = now
            self._tokens = min(self._rate, self._tokens + elapsed * self._rate)
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return
            # Need to wait
            deficit = 1.0 - self._tokens
            wait = deficit / self._rate
            self._tokens = 0.0
        time.sleep(wait)

    async def async_acquire(self) -> None:
        """Async version — yields to event loop while waiting."""
        import asyncio

        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            self._last = now
            self._tokens = min(self._rate, self._tokens + elapsed * self._rate)
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return
            deficit = 1.0 - self._tokens
            wait = deficit / self._rate
            self._tokens = 0.0
        await asyncio.sleep(wait)


class RateLimiter:
    """Per-service rate limiter backed by token buckets."""

    def __init__(self, default_rate: float | None = None) -> None:
        self._default_rate = default_rate
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def _get_bucket(self, service: str) -> TokenBucket | None:
        if self._default_rate is None:
            return None
        with self._lock:
            if service not in self._buckets:
                self._buckets[service] = TokenBucket(self._default_rate)
            return self._buckets[service]

    def acquire(self, service: str = "default") -> None:
        bucket = self._get_bucket(service)
        if bucket:
            bucket.acquire()

    async def async_acquire(self, service: str = "default") -> None:
        bucket = self._get_bucket(service)
        if bucket:
            await bucket.async_acquire()
