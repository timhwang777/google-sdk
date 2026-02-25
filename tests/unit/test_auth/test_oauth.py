"""Tests for the oauth() helper function."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import google.oauth2.credentials

from google_sdk.auth.oauth import _scopes_key, oauth
from google_sdk.auth.token_store import FileTokenStore, TokenData

SCOPES = ["https://www.googleapis.com/auth/drive"]


def make_token_data(**kwargs) -> TokenData:
    defaults = {
        "token": "access_token_abc",
        "refresh_token": "refresh_token_xyz",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "client123",
        "client_secret": "secret456",
        "scopes": SCOPES,
        "expiry": None,
    }
    defaults.update(kwargs)
    return TokenData(**defaults)


# ── _scopes_key ──────────────────────────────────────────────────────────────


def test_scopes_key_sorts():
    key = _scopes_key(["b_scope", "a_scope"])
    assert key == "a_scope,b_scope"


def test_scopes_key_single():
    key = _scopes_key(["only_scope"])
    assert key == "only_scope"


# ── oauth() — cached token ────────────────────────────────────────────────────


def test_oauth_returns_cached_valid_token(tmp_path):
    """When a valid token is cached, it is returned without starting a new flow."""
    store = FileTokenStore(tmp_path / "tokens.json")
    key = _scopes_key(SCOPES)
    store.save(key, make_token_data())

    with (
        patch("google_auth_oauthlib.flow.InstalledAppFlow") as mock_flow,
        patch(
            "google.oauth2.credentials.Credentials.valid",
            new_callable=lambda: property(lambda self: True),
        ),
    ):
        creds = oauth("fake_secrets.json", SCOPES, token_store=store)

    mock_flow.from_client_secrets_file.assert_not_called()
    assert creds.token == "access_token_abc"


def test_oauth_refreshes_expired_token(tmp_path):
    """Expired tokens with a refresh_token are refreshed, not re-authenticated."""
    store = FileTokenStore(tmp_path / "tokens.json")
    key = _scopes_key(SCOPES)
    # Store a token with a past expiry
    expired_expiry = datetime(2020, 1, 1, tzinfo=UTC)
    store.save(key, make_token_data(expiry=expired_expiry))

    with (
        patch(
            "google.oauth2.credentials.Credentials.valid",
            new_callable=lambda: property(lambda self: False),
        ),
        patch(
            "google.oauth2.credentials.Credentials.expired",
            new_callable=lambda: property(lambda self: True),
        ),
        patch("google.oauth2.credentials.Credentials.refresh") as mock_refresh,
        patch("google_auth_oauthlib.flow.InstalledAppFlow") as mock_flow,
    ):
        # After refresh, token becomes valid
        mock_refresh.return_value = None
        oauth("fake_secrets.json", SCOPES, token_store=store)

    mock_flow.from_client_secrets_file.assert_not_called()
    mock_refresh.assert_called_once()


def test_oauth_runs_new_flow_when_no_cache(tmp_path):
    """When no token is cached, InstalledAppFlow is launched."""
    store = FileTokenStore(tmp_path / "tokens.json")

    mock_creds = MagicMock(spec=google.oauth2.credentials.Credentials)
    mock_creds.token = "new_access_token"
    mock_creds.refresh_token = "new_refresh_token"
    mock_creds.token_uri = "https://oauth2.googleapis.com/token"
    mock_creds.client_id = "cid"
    mock_creds.client_secret = "csec"
    mock_creds.scopes = SCOPES
    mock_creds.expiry = None

    mock_flow_instance = MagicMock()
    mock_flow_instance.run_local_server.return_value = mock_creds

    with patch("google_auth_oauthlib.flow.InstalledAppFlow") as mock_flow_cls:
        mock_flow_cls.from_client_secrets_file.return_value = mock_flow_instance
        creds = oauth("fake_secrets.json", SCOPES, token_store=store)

    mock_flow_cls.from_client_secrets_file.assert_called_once_with("fake_secrets.json", SCOPES)
    mock_flow_instance.run_local_server.assert_called_once_with(port=0)
    assert creds.token == "new_access_token"


def test_oauth_saves_token_after_new_flow(tmp_path):
    """New tokens obtained via flow are persisted to the token store."""
    store = FileTokenStore(tmp_path / "tokens.json")
    key = _scopes_key(SCOPES)

    mock_creds = MagicMock(spec=google.oauth2.credentials.Credentials)
    mock_creds.token = "saved_token"
    mock_creds.refresh_token = "saved_refresh"
    mock_creds.token_uri = "https://oauth2.googleapis.com/token"
    mock_creds.client_id = "cid"
    mock_creds.client_secret = "csec"
    mock_creds.scopes = SCOPES
    mock_creds.expiry = None

    mock_flow_instance = MagicMock()
    mock_flow_instance.run_local_server.return_value = mock_creds

    with patch("google_auth_oauthlib.flow.InstalledAppFlow") as mock_flow_cls:
        mock_flow_cls.from_client_secrets_file.return_value = mock_flow_instance
        oauth("fake_secrets.json", SCOPES, token_store=store)

    saved = store.load(key)
    assert saved is not None
    assert saved.token == "saved_token"


def test_oauth_uses_default_file_store_when_none_given(tmp_path):
    """When token_store=None, a FileTokenStore is created automatically."""
    mock_creds = MagicMock(spec=google.oauth2.credentials.Credentials)
    mock_creds.token = "tok"
    mock_creds.refresh_token = "ref"
    mock_creds.token_uri = "https://oauth2.googleapis.com/token"
    mock_creds.client_id = "cid"
    mock_creds.client_secret = "csec"
    mock_creds.scopes = SCOPES
    mock_creds.expiry = None

    mock_flow_instance = MagicMock()
    mock_flow_instance.run_local_server.return_value = mock_creds

    with (
        patch("google_auth_oauthlib.flow.InstalledAppFlow") as mock_flow_cls,
        patch("google_sdk.auth.oauth.FileTokenStore") as mock_store_cls,
    ):
        mock_store_instance = MagicMock()
        mock_store_instance.load.return_value = None
        mock_store_cls.return_value = mock_store_instance
        mock_flow_cls.from_client_secrets_file.return_value = mock_flow_instance

        oauth("fake_secrets.json", SCOPES)

    mock_store_cls.assert_called_once()
