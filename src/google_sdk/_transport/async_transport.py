"""Asynchronous HTTP transport using httpx."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from google_sdk._config import SDKConfig
from google_sdk._transport.rate_limiter import RateLimiter
from google_sdk._transport.retry import AsyncRetryTransport

logger = logging.getLogger("google_sdk.transport")


class AsyncTransport:
    """Async HTTP transport with retry and rate limiting."""

    def __init__(self, config: SDKConfig | None = None) -> None:
        self._config = config or SDKConfig()
        self._rate_limiter = RateLimiter(self._config.rate_limit_per_second)
        retry_cfg = self._config.retry_config()
        inner = httpx.AsyncHTTPTransport()
        retry_transport = AsyncRetryTransport(inner, retry_cfg)
        self._client = httpx.AsyncClient(
            transport=retry_transport,
            timeout=self._config.timeout,
        )

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        await self._rate_limiter.async_acquire()
        logger.debug("%s %s", method, url)
        response = await self._client.request(method, url, **kwargs)
        logger.debug("Response %d for %s %s", response.status_code, method, url)
        return response

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncTransport:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
