"""SDK configuration models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    max_backoff: float = 60.0
    retryable_status_codes: set[int] = field(default_factory=lambda: {429, 500, 502, 503, 504})


@dataclass
class SDKConfig:
    """Global SDK configuration."""

    timeout: float = 120.0
    max_retries: int = 3
    max_backoff: float = 60.0
    rate_limit_per_second: float | None = None
    log_level: str = "WARNING"
    log_format: str = "text"  # "text" | "json"

    def retry_config(self) -> RetryConfig:
        return RetryConfig(
            max_retries=self.max_retries,
            max_backoff=self.max_backoff,
        )
