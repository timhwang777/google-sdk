"""Shared test fixtures and global pytest configuration."""

from unittest.mock import MagicMock

import google.auth.credentials
import pytest

from google_sdk import GoogleClient, SDKConfig

# ---------------------------------------------------------------------------
# Integration test opt-in
# ---------------------------------------------------------------------------
# Integration tests hit live Google APIs and create/delete real resources.
# They require ADC + Workspace setup (see tests/README.md), so they are
# skipped by default. Opt in with `--integration` or env var
# `RUN_INTEGRATION_TESTS=1`.


def pytest_addoption(parser):
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests against live Google APIs",
    )


def pytest_collection_modifyitems(config, items):
    import os

    enabled = config.getoption("--integration") or os.getenv("RUN_INTEGRATION_TESTS") == "1"
    if enabled:
        return

    skip_marker = pytest.mark.skip(
        reason="integration tests are opt-in: pass --integration or set RUN_INTEGRATION_TESTS=1"
    )
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_marker)


# ---------------------------------------------------------------------------
# Unit-test fixtures (mocked credentials, function-scoped)
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_creds():
    creds = MagicMock(spec=google.auth.credentials.Credentials)
    creds.valid = True
    creds.token = "fake_token"
    return creds


@pytest.fixture
def sdk_config():
    return SDKConfig(timeout=5.0)


@pytest.fixture
def google_client(mock_creds, sdk_config):
    return GoogleClient(mock_creds, config=sdk_config)
