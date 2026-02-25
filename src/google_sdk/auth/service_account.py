"""Service account authentication helper."""

from __future__ import annotations

import logging
from pathlib import Path

import google.oauth2.service_account

logger = logging.getLogger("google_sdk.auth")


def service_account(
    key_path: str | Path,
    *,
    scopes: list[str] | None = None,
    subject: str | None = None,
) -> google.oauth2.service_account.Credentials:
    """Create service account credentials from a key file.

    Args:
        key_path: Path to service account JSON key file.
        scopes: OAuth scopes to request. Defaults to full access scopes.
        subject: Email address to impersonate (domain delegation).

    Returns:
        Service account credentials.
    """
    from google_sdk.auth.scopes import CalendarScopes, DriveScopes, MeetScopes

    default_scopes = scopes or [DriveScopes.FULL, CalendarScopes.FULL, MeetScopes.FULL]

    logger.debug("Loading service account credentials from %s", key_path)
    creds = google.oauth2.service_account.Credentials.from_service_account_file(
        str(key_path),
        scopes=default_scopes,
    )
    if subject:
        creds = creds.with_subject(subject)
    return creds
