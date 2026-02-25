"""Retry middleware with exponential backoff and jitter."""

from __future__ import annotations

import logging
import random
import time

import httpx

from google_sdk._config import RetryConfig

logger = logging.getLogger("google_sdk.retry")


def _backoff_seconds(attempt: int, max_backoff: float) -> float:
    """Calculate wait time: min(2^n + random_ms, max_backoff)."""
    jitter = random.random()  # 0.0–1.0 seconds
    return min(2**attempt + jitter, max_backoff)


class RetryTransport(httpx.BaseTransport):
    """Sync retry middleware wrapping an httpx transport."""

    def __init__(self, transport: httpx.BaseTransport, config: RetryConfig) -> None:
        self._transport = transport
        self._config = config

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        for attempt in range(self._config.max_retries + 1):
            response = self._transport.handle_request(request)
            if response.status_code not in self._config.retryable_status_codes:
                return response
            if attempt == self._config.max_retries:
                logger.warning(
                    "Max retries (%d) exhausted for %s %s",
                    self._config.max_retries,
                    request.method,
                    request.url,
                )
                return response
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    wait = float(retry_after)
                except ValueError:
                    wait = _backoff_seconds(attempt, self._config.max_backoff)
            else:
                wait = _backoff_seconds(attempt, self._config.max_backoff)
            logger.debug(
                "Retrying request (attempt %d/%d) after %.2fs — status %d",
                attempt + 1,
                self._config.max_retries,
                wait,
                response.status_code,
            )
            time.sleep(wait)
        # unreachable
        return response  # type: ignore[return-value]

    def close(self) -> None:
        self._transport.close()


class AsyncRetryTransport(httpx.AsyncBaseTransport):
    """Async retry middleware wrapping an httpx async transport."""

    def __init__(self, transport: httpx.AsyncBaseTransport, config: RetryConfig) -> None:
        self._transport = transport
        self._config = config

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        import asyncio

        for attempt in range(self._config.max_retries + 1):
            response = await self._transport.handle_async_request(request)
            if response.status_code not in self._config.retryable_status_codes:
                return response
            if attempt == self._config.max_retries:
                logger.warning(
                    "Max retries (%d) exhausted for %s %s",
                    self._config.max_retries,
                    request.method,
                    request.url,
                )
                return response
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    wait = float(retry_after)
                except ValueError:
                    wait = _backoff_seconds(attempt, self._config.max_backoff)
            else:
                wait = _backoff_seconds(attempt, self._config.max_backoff)
            logger.debug(
                "Async retrying (attempt %d/%d) after %.2fs — status %d",
                attempt + 1,
                self._config.max_retries,
                wait,
                response.status_code,
            )
            await asyncio.sleep(wait)
        return response  # type: ignore[return-value]

    async def aclose(self) -> None:
        await self._transport.aclose()
