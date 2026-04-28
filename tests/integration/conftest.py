"""Integration-test fixtures and guards.

These tests hit live Google APIs and create/delete real resources in the
authenticated user's account. The opt-in is the top-level `--integration`
flag (see tests/conftest.py). This conftest adds the second guard:
credentials must actually resolve, and the resolved credentials must carry
the scopes the tests need.

Layout:
    - `pytestmark = integration` is applied to every test in this directory.
    - Session-scoped `client` fixture is shared across all integration tests.
    - `drive_cleanup` / `calendar_cleanup` collect resource IDs for teardown.
"""

from __future__ import annotations

import contextlib
import os
import time

import pytest

from google_sdk import GoogleClient, SDKConfig
from google_sdk.auth import resolve_credentials
from google_sdk.auth.scopes import CalendarScopes, DriveScopes, MeetScopes
from google_sdk.exceptions import AuthenticationError
from google_sdk.exceptions import PermissionError as SDKPermissionError

# Every test in this directory is an integration test.
pytestmark = pytest.mark.integration


REQUIRED_SCOPES = [DriveScopes.FULL, CalendarScopes.FULL, MeetScopes.FULL]


# ---------------------------------------------------------------------------
# Credential / client fixtures (session-scoped — resolve once)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def credentials():
    """Resolve Google credentials. Skip the entire session if unavailable.

    Resolution chain (delegated to ``google_sdk.auth.resolve_credentials``):
        1. ``GOOGLE_APPLICATION_CREDENTIALS`` env var → service account file
        2. ADC (``gcloud auth application-default login``)
        3. Well-known SA path at ``~/.config/google-sdk/service_account.json``
    """
    try:
        return resolve_credentials(scopes=REQUIRED_SCOPES)
    except AuthenticationError as exc:
        pytest.skip(
            "No Google credentials available for integration tests. "
            "Run `gcloud auth application-default login` with the Drive/"
            "Calendar/Meet scopes, or set GOOGLE_APPLICATION_CREDENTIALS. "
            f"See tests/README.md for setup. ({exc})",
            allow_module_level=True,
        )


@pytest.fixture(scope="session")
def sdk_config():
    """SDKConfig with a generous timeout for live API calls.

    Overrides the function-scoped, ``timeout=5`` config defined in
    ``tests/conftest.py`` for tests inside this directory only.
    """
    return SDKConfig(
        timeout=float(os.getenv("GOOGLE_SDK_TIMEOUT", "60")),
        max_retries=int(os.getenv("GOOGLE_SDK_MAX_RETRIES", "3")),
    )


@pytest.fixture(scope="session")
def client(credentials, sdk_config):
    """Session-wide GoogleClient. Closed automatically after all tests."""
    with GoogleClient(credentials, config=sdk_config) as c:
        yield c


# ---------------------------------------------------------------------------
# Workspace-only guard for Meet
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def workspace_account(client):
    """Skip if the authenticated account can't access the Meet API.

    Meet REST API requires a Google Workspace account. Personal Gmail
    accounts get 403 PERMISSION_DENIED on `spaces.create`. Probe once per
    session; tests that depend on Meet should consume this fixture.
    """
    try:
        space = client.meet.create_space()
    except SDKPermissionError as exc:
        pytest.skip(
            f"Meet API requires a Google Workspace account ({exc}). "
            "Skipping Meet integration tests.",
            allow_module_level=True,
        )
    except Exception as exc:
        pytest.skip(f"Meet API probe failed: {exc}", allow_module_level=True)
    return space


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_prefix():
    """Unique prefix for resources created during this test run.

    Tests should prefix every resource name with this value so orphaned
    resources are easy to identify and clean up manually.
    """
    return f"_sdk_test_{int(time.time())}"


@pytest.fixture()
def drive_cleanup(client):
    """Collect Drive file/folder IDs and delete them after the test."""
    file_ids: list[str] = []
    yield file_ids
    for fid in reversed(file_ids):
        with contextlib.suppress(Exception):
            client.drive.delete_file(fid)


@pytest.fixture()
def calendar_cleanup(client):
    """Collect calendar/event IDs for teardown.

    Append ``("calendar", calendar_id)`` for calendar deletion, or
    ``(calendar_id, event_id)`` for event deletion.
    """
    items: list[tuple[str, str]] = []
    yield items
    for a, b in reversed(items):
        with contextlib.suppress(Exception):
            if a == "calendar":
                client.calendar.delete_calendar(b)
            else:
                client.calendar.delete_event(a, b)
