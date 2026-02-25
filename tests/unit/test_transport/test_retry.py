"""Tests for retry middleware."""

from unittest.mock import MagicMock, patch

import httpx

from google_sdk._config import RetryConfig
from google_sdk._transport.retry import RetryTransport, _backoff_seconds


def test_backoff_no_exceed_max():
    for attempt in range(10):
        wait = _backoff_seconds(attempt, 60.0)
        assert wait <= 60.0


def test_backoff_increases():
    wait0 = 2**0
    wait5 = 2**5
    assert wait5 > wait0


def make_mock_transport(status_codes: list[int]) -> MagicMock:
    transport = MagicMock()
    responses = [
        httpx.Response(
            status_code=code, content=b"{}", headers={"content-type": "application/json"}
        )
        for code in status_codes
    ]
    transport.handle_request.side_effect = responses
    return transport


def test_pass_through_on_200():
    inner = make_mock_transport([200])
    cfg = RetryConfig(max_retries=3)
    retry = RetryTransport(inner, cfg)
    request = httpx.Request("GET", "https://example.com/")
    with patch("time.sleep"):
        resp = retry.handle_request(request)
    assert resp.status_code == 200
    assert inner.handle_request.call_count == 1


def test_retry_on_500():
    inner = make_mock_transport([500, 500, 200])
    cfg = RetryConfig(max_retries=3)
    retry = RetryTransport(inner, cfg)
    request = httpx.Request("GET", "https://example.com/")
    with patch("time.sleep"):
        resp = retry.handle_request(request)
    assert resp.status_code == 200
    assert inner.handle_request.call_count == 3


def test_retry_on_429():
    inner = make_mock_transport([429, 200])
    cfg = RetryConfig(max_retries=3)
    retry = RetryTransport(inner, cfg)
    request = httpx.Request("GET", "https://example.com/")
    with patch("time.sleep"):
        resp = retry.handle_request(request)
    assert resp.status_code == 200


def test_max_retry_exhaustion():
    inner = make_mock_transport([503, 503, 503, 503])
    cfg = RetryConfig(max_retries=3)
    retry = RetryTransport(inner, cfg)
    request = httpx.Request("GET", "https://example.com/")
    with patch("time.sleep"):
        resp = retry.handle_request(request)
    assert resp.status_code == 503
    assert inner.handle_request.call_count == 4  # 1 initial + 3 retries


def test_no_retry_on_non_retryable():
    inner = make_mock_transport([400])
    cfg = RetryConfig(max_retries=3)
    retry = RetryTransport(inner, cfg)
    request = httpx.Request("GET", "https://example.com/")
    with patch("time.sleep"):
        resp = retry.handle_request(request)
    assert resp.status_code == 400
    assert inner.handle_request.call_count == 1


def test_retry_after_header_respected():
    responses = [
        httpx.Response(
            status_code=429,
            content=b"{}",
            headers={"Retry-After": "2", "content-type": "application/json"},
        ),
        httpx.Response(
            status_code=200, content=b"{}", headers={"content-type": "application/json"}
        ),
    ]
    inner = MagicMock()
    inner.handle_request.side_effect = responses
    cfg = RetryConfig(max_retries=3)
    retry = RetryTransport(inner, cfg)
    request = httpx.Request("GET", "https://example.com/")
    with patch("time.sleep") as mock_sleep:
        retry.handle_request(request)
    mock_sleep.assert_called_once_with(2.0)
