"""Tests for BaseService error handling (404, 403, 429, 500)."""

from __future__ import annotations

from unittest.mock import MagicMock

import google.auth.credentials
import httpx
import pytest
import respx

from google_sdk._config import SDKConfig
from google_sdk.exceptions import (
    APIError,
    NotFoundError,
    PermissionError,
    QuotaExceededError,
    RateLimitError,
)
from google_sdk.services.drive.client import _API_BASE, DriveService


def make_creds():
    creds = MagicMock(spec=google.auth.credentials.Credentials)
    creds.valid = True
    creds.token = "fake_token"
    return creds


def make_service():
    return DriveService(make_creds(), SDKConfig())


@respx.mock
def test_404_raises_not_found_error():
    respx.get(f"{_API_BASE}/files/missing").mock(
        return_value=httpx.Response(
            404,
            json={"error": {"message": "File not found", "errors": []}},
        )
    )
    svc = make_service()
    with pytest.raises(NotFoundError) as exc_info:
        svc.get_file("missing")
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.message.lower()


@respx.mock
def test_403_raises_permission_error():
    respx.get(f"{_API_BASE}/files/locked").mock(
        return_value=httpx.Response(
            403,
            json={"error": {"message": "Permission denied", "errors": []}},
        )
    )
    svc = make_service()
    with pytest.raises(PermissionError) as exc_info:
        svc.get_file("locked")
    assert exc_info.value.status_code == 403


@respx.mock
def test_429_raises_rate_limit_error():
    respx.get(f"{_API_BASE}/files/rate").mock(
        return_value=httpx.Response(
            429,
            json={"error": {"message": "Rate limit exceeded", "errors": []}},
        )
    )
    svc = make_service()
    with pytest.raises(RateLimitError) as exc_info:
        svc.get_file("rate")
    assert exc_info.value.status_code == 429


@respx.mock
def test_429_with_retry_after_header():
    respx.get(f"{_API_BASE}/files/rate").mock(
        return_value=httpx.Response(
            429,
            json={"error": {"message": "Rate limited", "errors": []}},
            headers={"Retry-After": "5"},
        )
    )
    svc = make_service()
    with pytest.raises(RateLimitError) as exc_info:
        svc.get_file("rate")
    assert exc_info.value.retry_after == 5.0


@respx.mock
def test_429_quota_exceeded():
    respx.get(f"{_API_BASE}/files/quota").mock(
        return_value=httpx.Response(
            429,
            json={
                "error": {
                    "message": "Quota exceeded",
                    "errors": [{"reason": "quotaExceeded"}],
                }
            },
        )
    )
    svc = make_service()
    with pytest.raises(QuotaExceededError):
        svc.get_file("quota")


@respx.mock
def test_500_raises_api_error():
    respx.get(f"{_API_BASE}/files/broken").mock(
        return_value=httpx.Response(
            500,
            json={"error": {"message": "Internal server error", "errors": []}},
        )
    )
    svc = make_service()
    with pytest.raises(APIError) as exc_info:
        svc.get_file("broken")
    assert exc_info.value.status_code == 500


@respx.mock
def test_error_with_request_id_header():
    respx.get(f"{_API_BASE}/files/broken").mock(
        return_value=httpx.Response(
            500,
            json={"error": {"message": "Error", "errors": []}},
            headers={"x-goog-request-id": "req-abc-123"},
        )
    )
    svc = make_service()
    with pytest.raises(APIError) as exc_info:
        svc.get_file("broken")
    assert exc_info.value.request_id == "req-abc-123"


@respx.mock
def test_error_with_non_json_response():
    """Non-JSON error responses are handled gracefully."""
    respx.get(f"{_API_BASE}/files/broken").mock(
        return_value=httpx.Response(500, content=b"Internal Server Error")
    )
    svc = make_service()
    with pytest.raises(APIError):
        svc.get_file("broken")
