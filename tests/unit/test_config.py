"""Tests for SDKConfig and RetryConfig."""

from google_sdk._config import RetryConfig, SDKConfig


def test_retry_config_defaults():
    cfg = RetryConfig()
    assert cfg.max_retries == 3
    assert cfg.max_backoff == 60.0
    assert cfg.retryable_status_codes == {429, 500, 502, 503, 504}


def test_retry_config_custom():
    cfg = RetryConfig(max_retries=5, max_backoff=30.0, retryable_status_codes={429, 503})
    assert cfg.max_retries == 5
    assert cfg.max_backoff == 30.0
    assert cfg.retryable_status_codes == {429, 503}


def test_sdk_config_defaults():
    cfg = SDKConfig()
    assert cfg.timeout == 30.0
    assert cfg.max_retries == 3
    assert cfg.max_backoff == 60.0
    assert cfg.rate_limit_per_second is None
    assert cfg.log_level == "WARNING"
    assert cfg.log_format == "text"


def test_sdk_config_custom():
    cfg = SDKConfig(timeout=10.0, max_retries=1, log_level="DEBUG", log_format="json")
    assert cfg.timeout == 10.0
    assert cfg.max_retries == 1
    assert cfg.log_level == "DEBUG"
    assert cfg.log_format == "json"


def test_sdk_config_retry_config():
    cfg = SDKConfig(max_retries=2, max_backoff=30.0)
    rc = cfg.retry_config()
    assert isinstance(rc, RetryConfig)
    assert rc.max_retries == 2
    assert rc.max_backoff == 30.0
