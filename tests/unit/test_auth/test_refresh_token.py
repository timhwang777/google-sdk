"""Tests for credentials_from_refresh_token()."""

from __future__ import annotations

import google.oauth2.credentials

from google_sdk.auth import credentials_from_refresh_token

SCOPES = ["https://www.googleapis.com/auth/drive"]


def test_returns_oauth_credentials_with_provided_fields():
    creds = credentials_from_refresh_token(
        client_id="cid",
        client_secret="csec",
        refresh_token="rtok",
        scopes=SCOPES,
    )
    assert isinstance(creds, google.oauth2.credentials.Credentials)
    assert creds.refresh_token == "rtok"
    assert creds.client_id == "cid"
    assert creds.client_secret == "csec"
    assert creds.scopes == SCOPES
    assert creds.token_uri == "https://oauth2.googleapis.com/token"


def test_no_access_token_until_refreshed():
    """No access token is set; google-auth will fetch one on first use."""
    creds = credentials_from_refresh_token(
        client_id="cid",
        client_secret="csec",
        refresh_token="rtok",
        scopes=SCOPES,
    )
    assert creds.token is None
    assert creds.valid is False


def test_token_uri_override():
    creds = credentials_from_refresh_token(
        client_id="cid",
        client_secret="csec",
        refresh_token="rtok",
        scopes=SCOPES,
        token_uri="https://example.test/oauth/token",
    )
    assert creds.token_uri == "https://example.test/oauth/token"
