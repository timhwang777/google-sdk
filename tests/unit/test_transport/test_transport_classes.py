"""Tests for SyncTransport, AsyncTransport, and transport Protocol."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import respx

from google_sdk._config import SDKConfig
from google_sdk._transport._base import AsyncTransportProtocol, Transport
from google_sdk._transport.async_transport import AsyncTransport
from google_sdk._transport.retry import AsyncRetryTransport
from google_sdk._transport.sync_transport import SyncTransport

# ── Transport Protocol isinstance checks ─────────────────────────────────────


def test_transport_protocol_isinstance():
    """SyncTransport satisfies the Transport protocol."""
    transport = SyncTransport()
    assert isinstance(transport, Transport)
    transport.close()


@pytest.mark.asyncio
async def test_async_transport_protocol_isinstance():
    """AsyncTransport satisfies the AsyncTransportProtocol."""
    transport = AsyncTransport()
    assert isinstance(transport, AsyncTransportProtocol)
    await transport.close()


# ── SyncTransport ─────────────────────────────────────────────────────────────


@respx.mock
def test_sync_transport_request():
    respx.get("https://example.com/test").mock(return_value=httpx.Response(200, json={"ok": True}))
    t = SyncTransport(SDKConfig())
    resp = t.request("GET", "https://example.com/test")
    assert resp.status_code == 200
    t.close()


@respx.mock
def test_sync_transport_context_manager():
    respx.get("https://example.com/").mock(return_value=httpx.Response(200, content=b"ok"))
    with SyncTransport(SDKConfig()) as t:
        assert isinstance(t, SyncTransport)


# ── AsyncTransport ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_async_transport_request():
    respx.get("https://example.com/test").mock(return_value=httpx.Response(200, json={"ok": True}))
    t = AsyncTransport(SDKConfig())
    resp = await t.request("GET", "https://example.com/test")
    assert resp.status_code == 200
    await t.close()


@pytest.mark.asyncio
@respx.mock
async def test_async_transport_context_manager():
    async with AsyncTransport(SDKConfig()) as t:
        assert isinstance(t, AsyncTransport)


# ── AsyncRetryTransport ───────────────────────────────────────────────────────


def make_async_mock_transport(status_codes: list[int]) -> MagicMock:
    transport = MagicMock()
    responses = [
        httpx.Response(code, content=b"{}", headers={"content-type": "application/json"})
        for code in status_codes
    ]
    transport.handle_async_request = AsyncMock(side_effect=responses)
    return transport


@pytest.mark.asyncio
async def test_async_retry_pass_through_200():
    from google_sdk._config import RetryConfig

    inner = make_async_mock_transport([200])
    cfg = RetryConfig(max_retries=3)
    retry = AsyncRetryTransport(inner, cfg)
    request = httpx.Request("GET", "https://example.com/")
    with patch("asyncio.sleep", new_callable=AsyncMock):
        resp = await retry.handle_async_request(request)
    assert resp.status_code == 200
    assert inner.handle_async_request.call_count == 1


@pytest.mark.asyncio
async def test_async_retry_on_500():
    from google_sdk._config import RetryConfig

    inner = make_async_mock_transport([500, 500, 200])
    cfg = RetryConfig(max_retries=3)
    retry = AsyncRetryTransport(inner, cfg)
    request = httpx.Request("GET", "https://example.com/")
    with patch("asyncio.sleep", new_callable=AsyncMock):
        resp = await retry.handle_async_request(request)
    assert resp.status_code == 200
    assert inner.handle_async_request.call_count == 3


@pytest.mark.asyncio
async def test_async_retry_respects_retry_after():
    from google_sdk._config import RetryConfig

    responses = [
        httpx.Response(
            429, content=b"{}", headers={"Retry-After": "3", "content-type": "application/json"}
        ),
        httpx.Response(200, content=b"{}", headers={"content-type": "application/json"}),
    ]
    inner = MagicMock()
    inner.handle_async_request = AsyncMock(side_effect=responses)
    cfg = RetryConfig(max_retries=3)
    retry = AsyncRetryTransport(inner, cfg)
    request = httpx.Request("GET", "https://example.com/")
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await retry.handle_async_request(request)
    mock_sleep.assert_called_once_with(3.0)


@pytest.mark.asyncio
async def test_async_retry_invalid_retry_after_uses_backoff():
    """When Retry-After is non-numeric, falls back to exponential backoff."""
    from google_sdk._config import RetryConfig

    responses = [
        httpx.Response(
            429,
            content=b"{}",
            headers={
                "Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT",
                "content-type": "application/json",
            },
        ),
        httpx.Response(200, content=b"{}", headers={"content-type": "application/json"}),
    ]
    inner = MagicMock()
    inner.handle_async_request = AsyncMock(side_effect=responses)
    cfg = RetryConfig(max_retries=3)
    retry = AsyncRetryTransport(inner, cfg)
    request = httpx.Request("GET", "https://example.com/")
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await retry.handle_async_request(request)
    mock_sleep.assert_called_once()
    assert mock_sleep.call_args[0][0] >= 0


@pytest.mark.asyncio
async def test_async_retry_aclose():
    from google_sdk._config import RetryConfig

    inner = MagicMock()
    inner.aclose = AsyncMock()
    cfg = RetryConfig()
    retry = AsyncRetryTransport(inner, cfg)
    await retry.aclose()
    inner.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_async_retry_max_exhaustion():
    from google_sdk._config import RetryConfig

    inner = make_async_mock_transport([503, 503, 503, 503])
    cfg = RetryConfig(max_retries=3)
    retry = AsyncRetryTransport(inner, cfg)
    request = httpx.Request("GET", "https://example.com/")
    with patch("asyncio.sleep", new_callable=AsyncMock):
        resp = await retry.handle_async_request(request)
    assert resp.status_code == 503
    assert inner.handle_async_request.call_count == 4


# ── RetryTransport invalid Retry-After ───────────────────────────────────────


def test_retry_invalid_retry_after_falls_back_to_backoff():
    """Retry-After with non-numeric value uses exponential backoff."""
    from unittest.mock import MagicMock, patch

    from google_sdk._config import RetryConfig
    from google_sdk._transport.retry import RetryTransport

    responses = [
        httpx.Response(
            429,
            content=b"{}",
            headers={
                "Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT",
                "content-type": "application/json",
            },
        ),
        httpx.Response(200, content=b"{}", headers={"content-type": "application/json"}),
    ]
    inner = MagicMock()
    inner.handle_request.side_effect = responses
    cfg = RetryConfig(max_retries=3)
    retry = RetryTransport(inner, cfg)
    request = httpx.Request("GET", "https://example.com/")
    with patch("time.sleep") as mock_sleep:
        resp = retry.handle_request(request)
    mock_sleep.assert_called_once()
    assert resp.status_code == 200


def test_retry_transport_close():
    from google_sdk._config import RetryConfig
    from google_sdk._transport.retry import RetryTransport

    inner = MagicMock()
    cfg = RetryConfig()
    retry = RetryTransport(inner, cfg)
    retry.close()
    inner.close.assert_called_once()
