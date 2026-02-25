"""Exception hierarchy for google-sdk.

All SDK exceptions inherit from GoogleSDKError.
"""

from __future__ import annotations


class GoogleSDKError(Exception):
    """Base exception for all google-sdk errors."""


class AuthenticationError(GoogleSDKError):
    """Raised when authentication fails or no credentials can be resolved."""


class TokenStoreError(GoogleSDKError):
    """Raised when token store operations fail."""


class APIError(GoogleSDKError):
    """Raised when the Google API returns an error response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 0,
        errors: list[dict] | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors: list[dict] = errors or []
        self.request_id = request_id

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"status_code={self.status_code}, "
            f"message={self.message!r}, "
            f"request_id={self.request_id!r})"
        )


class NotFoundError(APIError):
    """Raised on HTTP 404 responses."""

    def __init__(self, message: str = "Resource not found", **kwargs) -> None:
        kwargs.setdefault("status_code", 404)
        super().__init__(message, **kwargs)


class PermissionError(APIError):  # noqa: A001
    """Raised on HTTP 403 responses."""

    def __init__(self, message: str = "Permission denied", **kwargs) -> None:
        kwargs.setdefault("status_code", 403)
        super().__init__(message, **kwargs)


class RateLimitError(APIError):
    """Raised on HTTP 429 responses."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: float | None = None,
        **kwargs,
    ) -> None:
        kwargs.setdefault("status_code", 429)
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class QuotaExceededError(APIError):
    """Raised when Google API quota is exceeded (429 with quota reason)."""

    def __init__(self, message: str = "Quota exceeded", **kwargs) -> None:
        kwargs.setdefault("status_code", 429)
        super().__init__(message, **kwargs)


class ValidationError(GoogleSDKError):
    """Raised when request or response validation fails."""
