"""OAuth 2.0 user authentication flow."""

from __future__ import annotations

import logging
from pathlib import Path

import google.oauth2.credentials
from google.auth.transport.requests import Request

from google_sdk.auth.token_store import FileTokenStore, TokenData, TokenStore

logger = logging.getLogger("google_sdk.auth")


def _scopes_key(scopes: list[str]) -> str:
    return ",".join(sorted(scopes))


def oauth(
    client_secrets: str | Path,
    scopes: list[str],
    *,
    token_store: TokenStore | None = None,
) -> google.oauth2.credentials.Credentials:
    """Authenticate via OAuth 2.0, using cached tokens when available.

    Args:
        client_secrets: Path to client_secrets.json file.
        scopes: List of OAuth scopes to request.
        token_store: Token storage backend (default: FileTokenStore).

    Returns:
        Valid OAuth2 credentials.
    """
    from google_auth_oauthlib.flow import InstalledAppFlow

    store = token_store or FileTokenStore()
    key = _scopes_key(scopes)

    # Try cached token
    cached = store.load(key)
    if cached is not None:
        creds = google.oauth2.credentials.Credentials(
            token=cached.token,
            refresh_token=cached.refresh_token,
            token_uri=cached.token_uri or "https://oauth2.googleapis.com/token",
            client_id=cached.client_id,
            client_secret=cached.client_secret,
            scopes=cached.scopes or scopes,
        )
        if creds.valid:
            logger.debug("Using cached OAuth token")
            return creds
        if creds.expired and creds.refresh_token:
            logger.debug("Refreshing expired OAuth token")
            creds.refresh(Request())
            _save_creds(store, key, creds)
            return creds

    # Run new OAuth flow
    logger.debug("Starting new OAuth flow")
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), scopes)
    creds = flow.run_local_server(port=0)
    _save_creds(store, key, creds)
    return creds


def _save_creds(store: TokenStore, key: str, creds: google.oauth2.credentials.Credentials) -> None:
    token_data = TokenData(
        token=creds.token or "",
        refresh_token=creds.refresh_token,
        token_uri=creds.token_uri,
        client_id=creds.client_id,
        client_secret=creds.client_secret,
        scopes=list(creds.scopes or []),
        expiry=creds.expiry,
    )
    store.save(key, token_data)
