"""Authentication helpers for google-sdk.

Example::

    from google_sdk.auth import oauth, service_account, resolve_credentials

    # Service account
    creds = service_account("path/to/key.json", scopes=["..."])

    # OAuth user flow
    creds = oauth("client_secrets.json", scopes=["..."])

    # Auto-resolve credentials
    creds = resolve_credentials()
"""

from __future__ import annotations

import logging
from pathlib import Path

import google.auth
import google.auth.credentials
import google.auth.exceptions

from google_sdk.auth.oauth import oauth
from google_sdk.auth.service_account import service_account
from google_sdk.auth.token_store import EnvTokenStore, FileTokenStore, KeyringTokenStore, TokenStore
from google_sdk.exceptions import AuthenticationError

logger = logging.getLogger("google_sdk.auth")

__all__ = [
    "oauth",
    "service_account",
    "resolve_credentials",
    "TokenStore",
    "FileTokenStore",
    "KeyringTokenStore",
    "EnvTokenStore",
]

_WELL_KNOWN_SA_PATH = Path.home() / ".config" / "google-sdk" / "service_account.json"


def resolve_credentials(
    credentials: google.auth.credentials.Credentials | None = None,
    *,
    scopes: list[str] | None = None,
) -> google.auth.credentials.Credentials:
    """Resolve credentials via fallback chain.

    Resolution order:
    1. Explicit credentials passed in
    2. google.auth.default() (ADC — gcloud, Cloud Run, GCE, etc.)
    3. Service account file at ~/.config/google-sdk/service_account.json
    4. Raises AuthenticationError with clear message

    Args:
        credentials: Explicit credentials (short-circuits chain).
        scopes: Scopes to apply when loading service accounts.

    Returns:
        Resolved credentials.

    Raises:
        AuthenticationError: When no credentials can be resolved.
    """
    if credentials is not None:
        logger.debug("Using explicit credentials")
        return credentials

    # Try ADC
    try:
        creds, _ = google.auth.default(scopes=scopes)
        logger.debug("Using Application Default Credentials")
        return creds
    except google.auth.exceptions.DefaultCredentialsError:
        pass

    # Try well-known service account file
    if _WELL_KNOWN_SA_PATH.exists():
        logger.debug("Using service account file at %s", _WELL_KNOWN_SA_PATH)
        return service_account(_WELL_KNOWN_SA_PATH, scopes=scopes)

    raise AuthenticationError(
        "No credentials found. Provide one of:\n"
        "  1. Explicit credentials: GoogleClient(credentials=...)\n"
        "  2. GOOGLE_APPLICATION_CREDENTIALS env var pointing to a service account key\n"
        "  3. Run 'gcloud auth application-default login' for ADC\n"
        f"  4. Place a service account key at {_WELL_KNOWN_SA_PATH}"
    )
