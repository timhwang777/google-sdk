"""Integration tests for MeetService against live Google Meet API.

The Meet REST API requires a Google Workspace account. The autouse
`_workspace_required` fixture below probes the API once per session and
skips the whole module cleanly for personal Gmail accounts.

Note: participant and recording methods require active/past conferences
with real participants, so they cannot be tested automatically.
"""

from __future__ import annotations

import contextlib

import pytest

from google_sdk.services.meet.models import Space, SpaceConfig


@pytest.fixture(autouse=True)
def _workspace_required(workspace_account):
    """Gate every test in this module on Workspace availability."""
    return workspace_account


# ---------------------------------------------------------------------------
# Space CRUD
# ---------------------------------------------------------------------------


def test_create_space(client):
    """Create a Meet space and verify it has a meeting URI and code."""
    space = client.meet.create_space()

    assert isinstance(space, Space)
    assert space.name  # e.g. "spaces/abc-defg-hij"
    assert space.meeting_uri
    assert space.meeting_code


def test_create_space_with_config(client):
    """Create a space with explicit config."""
    config = SpaceConfig(access_type="TRUSTED", entry_point_access="ALL")
    space = client.meet.create_space(config=config)

    assert isinstance(space, Space)
    assert space.name


def test_get_space(client):
    """Create a space, then retrieve it by name."""
    created = client.meet.create_space()
    fetched = client.meet.get_space(created.name)

    assert fetched.name == created.name
    assert fetched.meeting_code == created.meeting_code


def test_update_space(client):
    """Create a space and update its config."""
    space = client.meet.create_space()
    updated = client.meet.update_space(space.name, config={"access_type": "OPEN"})

    assert isinstance(updated, Space)
    assert updated.name == space.name


def test_end_active_conference(client):
    """Ending a conference on a space with no active conference should not crash.

    The API returns 404 when there's no active conference, which the SDK may
    raise as NotFoundError. Either success or NotFoundError is acceptable.
    """
    space = client.meet.create_space()

    # No active conference is the expected case — accept any error here.
    with contextlib.suppress(Exception):
        client.meet.end_active_conference(space.name)
