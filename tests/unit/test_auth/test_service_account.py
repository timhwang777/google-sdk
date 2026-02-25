"""Tests for the service_account() helper function."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import google.oauth2.service_account

from google_sdk.auth.scopes import CalendarScopes, DriveScopes, MeetScopes
from google_sdk.auth.service_account import service_account

# ── service_account() ────────────────────────────────────────────────────────


def test_service_account_loads_key_file():
    """Credentials are loaded from the specified key file."""
    mock_creds = MagicMock(spec=google.oauth2.service_account.Credentials)
    mock_creds.with_subject.return_value = mock_creds

    with patch(
        "google.oauth2.service_account.Credentials.from_service_account_file",
        return_value=mock_creds,
    ) as mock_load:
        result = service_account("key.json")

    mock_load.assert_called_once()
    call_args = mock_load.call_args
    assert call_args[0][0] == "key.json"
    assert result is mock_creds


def test_service_account_accepts_path_object():
    """service_account() accepts a Path object as key_path."""
    mock_creds = MagicMock(spec=google.oauth2.service_account.Credentials)

    with patch(
        "google.oauth2.service_account.Credentials.from_service_account_file",
        return_value=mock_creds,
    ) as mock_load:
        service_account(Path("/path/to/key.json"))

    call_args = mock_load.call_args
    assert call_args[0][0] == "/path/to/key.json"


def test_service_account_applies_default_scopes():
    """When no scopes provided, all three service scopes are used."""
    mock_creds = MagicMock(spec=google.oauth2.service_account.Credentials)

    with patch(
        "google.oauth2.service_account.Credentials.from_service_account_file",
        return_value=mock_creds,
    ) as mock_load:
        service_account("key.json")

    call_kwargs = mock_load.call_args[1]
    scopes = call_kwargs["scopes"]
    assert DriveScopes.FULL in scopes
    assert CalendarScopes.FULL in scopes
    assert MeetScopes.FULL in scopes


def test_service_account_applies_custom_scopes():
    """Explicitly provided scopes override the defaults."""
    mock_creds = MagicMock(spec=google.oauth2.service_account.Credentials)
    custom_scopes = ["https://www.googleapis.com/auth/drive.readonly"]

    with patch(
        "google.oauth2.service_account.Credentials.from_service_account_file",
        return_value=mock_creds,
    ) as mock_load:
        service_account("key.json", scopes=custom_scopes)

    call_kwargs = mock_load.call_args[1]
    assert call_kwargs["scopes"] == custom_scopes


def test_service_account_no_subject_by_default():
    """with_subject() is NOT called when no subject is given."""
    mock_creds = MagicMock(spec=google.oauth2.service_account.Credentials)

    with patch(
        "google.oauth2.service_account.Credentials.from_service_account_file",
        return_value=mock_creds,
    ):
        result = service_account("key.json")

    mock_creds.with_subject.assert_not_called()
    assert result is mock_creds


def test_service_account_with_subject_for_domain_delegation():
    """with_subject() is called when subject is provided (domain delegation)."""
    mock_creds = MagicMock(spec=google.oauth2.service_account.Credentials)
    delegated_creds = MagicMock(spec=google.oauth2.service_account.Credentials)
    mock_creds.with_subject.return_value = delegated_creds

    with patch(
        "google.oauth2.service_account.Credentials.from_service_account_file",
        return_value=mock_creds,
    ):
        result = service_account("key.json", subject="admin@example.com")

    mock_creds.with_subject.assert_called_once_with("admin@example.com")
    assert result is delegated_creds
