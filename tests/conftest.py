"""Shared test fixtures."""

from unittest.mock import MagicMock

import google.auth.credentials
import pytest

from google_sdk import GoogleClient, SDKConfig


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
