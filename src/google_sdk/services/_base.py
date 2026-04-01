"""Base service class for Google API service implementations."""

from __future__ import annotations

import logging
from typing import Any, TypeVar

import google.auth.credentials
import google.auth.transport.requests
import httpx
from pydantic import BaseModel

from google_sdk._config import SDKConfig
from google_sdk.exceptions import (
    APIError,
    NotFoundError,
    PermissionError,
    QuotaExceededError,
    RateLimitError,
)

logger = logging.getLogger("google_sdk.services")

DRIVE_API_VERSION = "v3"
CALENDAR_API_VERSION = "v3"
MEET_API_VERSION = "v2"

M = TypeVar("M", bound=BaseModel)


def _raise_for_status(response: httpx.Response) -> None:
    """Raise appropriate SDK exception for error responses."""
    if response.status_code < 400:
        return
    try:
        body = response.json()
        error = body.get("error", {})
        message = error.get("message", response.text)
        errors = error.get("errors", [])
        request_id = response.headers.get("x-goog-request-id")
    except Exception:
        message = response.text
        errors = []
        request_id = None

    kwargs: dict[str, Any] = {
        "status_code": response.status_code,
        "errors": errors,
        "request_id": request_id,
    }

    if response.status_code in (404, 410):
        raise NotFoundError(message, **kwargs)
    if response.status_code == 403:
        raise PermissionError(message, **kwargs)
    if response.status_code == 429:
        # Check if quota exceeded
        is_quota = any(
            e.get("reason") in ("quotaExceeded", "dailyLimitExceeded", "rateLimitExceeded")
            for e in errors
        )
        if is_quota:
            raise QuotaExceededError(message, **kwargs)
        retry_after_str = response.headers.get("Retry-After")
        retry_after = float(retry_after_str) if retry_after_str else None
        raise RateLimitError(message, retry_after=retry_after, **kwargs)
    raise APIError(message, **kwargs)


class BaseService:
    """Base class for all Google API service wrappers."""

    _BASE_URL: str = ""

    def __init__(
        self,
        credentials: google.auth.credentials.Credentials,
        config: SDKConfig | None = None,
    ) -> None:
        self._credentials = credentials
        self._config = config or SDKConfig()

    def _get_headers(self) -> dict[str, str]:
        """Get auth headers, refreshing credentials if needed."""
        request = google.auth.transport.requests.Request()
        if not self._credentials.valid:
            self._credentials.refresh(request)
        token = self._credentials.token
        return {"Authorization": f"Bearer {token}"}

    def _get(self, path: str, **kwargs: Any) -> dict:
        import httpx

        url = self._BASE_URL + path
        headers = self._get_headers()
        with httpx.Client(timeout=self._config.timeout) as client:
            resp = client.get(url, headers=headers, **kwargs)
        _raise_for_status(resp)
        return resp.json()

    def _post(self, path: str, **kwargs: Any) -> dict:
        import httpx

        url = self._BASE_URL + path
        headers = self._get_headers()
        with httpx.Client(timeout=self._config.timeout) as client:
            resp = client.post(url, headers=headers, **kwargs)
        _raise_for_status(resp)
        return resp.json()

    def _patch(self, path: str, **kwargs: Any) -> dict:
        import httpx

        url = self._BASE_URL + path
        headers = self._get_headers()
        with httpx.Client(timeout=self._config.timeout) as client:
            resp = client.patch(url, headers=headers, **kwargs)
        _raise_for_status(resp)
        return resp.json()

    def _put(self, path: str, **kwargs: Any) -> dict:
        import httpx

        url = self._BASE_URL + path
        headers = self._get_headers()
        with httpx.Client(timeout=self._config.timeout) as client:
            resp = client.put(url, headers=headers, **kwargs)
        _raise_for_status(resp)
        return resp.json()

    def _delete(self, path: str, **kwargs: Any) -> httpx.Response:
        import httpx

        url = self._BASE_URL + path
        headers = self._get_headers()
        with httpx.Client(timeout=self._config.timeout) as client:
            resp = client.delete(url, headers=headers, **kwargs)
        _raise_for_status(resp)
        return resp

    def _parse(self, data: dict, model: type[M]) -> M:
        return model.model_validate(data)
