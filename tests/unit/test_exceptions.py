"""Tests for the exception hierarchy."""

from google_sdk.exceptions import (
    APIError,
    AuthenticationError,
    GoogleSDKError,
    NotFoundError,
    PermissionError,
    QuotaExceededError,
    RateLimitError,
    TokenStoreError,
    ValidationError,
)


def test_google_sdk_error_is_base():
    err = GoogleSDKError("base error")
    assert isinstance(err, Exception)
    assert str(err) == "base error"


def test_authentication_error():
    err = AuthenticationError("no creds")
    assert isinstance(err, GoogleSDKError)


def test_token_store_error():
    err = TokenStoreError("can't read")
    assert isinstance(err, GoogleSDKError)


def test_api_error_fields():
    err = APIError(
        "bad request", status_code=400, errors=[{"reason": "invalid"}], request_id="req-1"
    )
    assert err.status_code == 400
    assert err.message == "bad request"
    assert err.errors == [{"reason": "invalid"}]
    assert err.request_id == "req-1"
    assert str(err) == "bad request"


def test_api_error_defaults():
    err = APIError("oops")
    assert err.status_code == 0
    assert err.errors == []
    assert err.request_id is None


def test_not_found_error():
    err = NotFoundError()
    assert isinstance(err, APIError)
    assert err.status_code == 404


def test_not_found_error_custom_message():
    err = NotFoundError("file missing", status_code=404)
    assert err.message == "file missing"


def test_permission_error():
    err = PermissionError()
    assert isinstance(err, APIError)
    assert err.status_code == 403


def test_rate_limit_error():
    err = RateLimitError(retry_after=5.0)
    assert isinstance(err, APIError)
    assert err.status_code == 429
    assert err.retry_after == 5.0


def test_rate_limit_error_no_retry_after():
    err = RateLimitError()
    assert err.retry_after is None


def test_quota_exceeded_error():
    err = QuotaExceededError()
    assert isinstance(err, APIError)
    assert err.status_code == 429


def test_validation_error():
    err = ValidationError("bad input")
    assert isinstance(err, GoogleSDKError)


def test_repr():
    err = APIError("msg", status_code=500, request_id="abc")
    assert "500" in repr(err)
    assert "abc" in repr(err)
