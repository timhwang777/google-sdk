"""Construct OAuth user credentials from a stored refresh token.

Useful for server-side environments (Django, Cloud Run, etc.) where the
OAuth client ID/secret and a long-lived refresh token are stored in env
vars or a database — no browser flow needed at request time.
"""

from __future__ import annotations

import logging

import google.oauth2.credentials

logger = logging.getLogger("google_sdk.auth")


def credentials_from_refresh_token(
    *,
    client_id: str,
    client_secret: str,
    refresh_token: str,
    scopes: list[str],
    token_uri: str = "https://oauth2.googleapis.com/token",
) -> google.oauth2.credentials.Credentials:
    """Build OAuth user credentials from a stored refresh token.

    The returned object has no access token yet; it will be refreshed
    transparently on first use by ``BaseService._get_headers``.

    Args:
        client_id: OAuth 2.0 client ID.
        client_secret: OAuth 2.0 client secret.
        refresh_token: Long-lived refresh token previously granted by the user.
        scopes: OAuth scopes the refresh token was granted for.
        token_uri: Google's token endpoint (override only for testing).

    Returns:
        Credentials suitable for passing to ``GoogleClient(credentials=...)``.
    """
    return google.oauth2.credentials.Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=scopes,
    )
