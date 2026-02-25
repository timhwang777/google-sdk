"""Synchronous HTTP transport using httpx."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from google_sdk._config import SDKConfig
from google_sdk._transport.rate_limiter import RateLimiter
from google_sdk._transport.retry import RetryTransport

logger = logging.getLogger("google_sdk.transport")


class SyncTransport:
    """Sync HTTP transport with retry and rate limiting."""

    def __init__(self, config: SDKConfig | None = None) -> None:
        self._config = config or SDKConfig()
        rate_limiter = RateLimiter(self._config.rate_limit_per_second)
        retry_cfg = self._config.retry_config()
        inner = httpx.HTTPTransport()
        retry_transport = RetryTransport(inner, retry_cfg)
        self._client = httpx.Client(
            transport=retry_transport,
            timeout=self._config.timeout,
        )
        self._rate_limiter = rate_limiter

    def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        self._rate_limiter.acquire()
        logger.debug("%s %s", method, url)
        response = self._client.request(method, url, **kwargs)
        logger.debug("Response %d for %s %s", response.status_code, method, url)
        return response

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> SyncTransport:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
