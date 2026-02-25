"""Tests for the credential resolution chain."""

from unittest.mock import MagicMock, patch

import google.auth.credentials
import google.auth.exceptions
import pytest

from google_sdk.auth import resolve_credentials
from google_sdk.exceptions import AuthenticationError


def make_mock_creds():
    creds = MagicMock(spec=google.auth.credentials.Credentials)
    creds.valid = True
    return creds


def test_explicit_credentials_returned_directly():
    creds = make_mock_creds()
    result = resolve_credentials(creds)
    assert result is creds


def test_adc_fallback():
    mock_creds = make_mock_creds()
    with patch("google.auth.default", return_value=(mock_creds, "project")) as mock_default:
        result = resolve_credentials()
    mock_default.assert_called_once()
    assert result is mock_creds


def test_service_account_file_fallback(tmp_path):
    sa_path = tmp_path / "service_account.json"
    sa_path.write_text("{}")  # Dummy file

    mock_creds = make_mock_creds()
    with (
        patch("google.auth.default", side_effect=google.auth.exceptions.DefaultCredentialsError),
        patch("google_sdk.auth._WELL_KNOWN_SA_PATH", sa_path),
        patch("google_sdk.auth.service_account", return_value=mock_creds) as mock_sa,
    ):
        result = resolve_credentials()
    mock_sa.assert_called_once()
    assert result is mock_creds


def test_raises_when_no_credentials(tmp_path):
    nonexistent = tmp_path / "nonexistent.json"
    with (
        patch("google.auth.default", side_effect=google.auth.exceptions.DefaultCredentialsError),
        patch("google_sdk.auth._WELL_KNOWN_SA_PATH", nonexistent),
        pytest.raises(AuthenticationError),
    ):
        resolve_credentials()
