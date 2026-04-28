"""End-to-end workflow tests that combine multiple Google services."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest


@pytest.fixture(autouse=True)
def _workspace_required(workspace_account):
    """Workflows depend on Meet — gate the module on Workspace availability."""
    return workspace_account


def test_meeting_with_drive_folder(client, test_prefix, drive_cleanup, calendar_cleanup):
    """Simulate a real workflow: schedule a meeting, create a shared folder, link a Meet space.

    Steps:
    1. Create a Google Meet space
    2. Create a Drive folder for meeting materials
    3. Create a Calendar event referencing both
    4. Verify all three resources exist and are consistent
    """
    # 1. Meet space
    space = client.meet.create_space()
    assert space.meeting_uri

    # 2. Drive folder for meeting materials
    folder_name = f"{test_prefix}_meeting_materials"
    folder = client.drive.create_folder(folder_name)
    drive_cleanup.append(folder.id)

    # Upload a notes file into the folder
    notes = client.drive.create_file(
        f"{test_prefix}_notes.txt",
        content=b"Meeting agenda:\n1. Review integration tests",
        mime_type="text/plain",
        parents=[folder.id],
    )
    drive_cleanup.append(notes.id)

    # 3. Calendar event referencing the Meet link and folder
    start = datetime.now(UTC) + timedelta(hours=48)
    end = start + timedelta(hours=1)

    event = client.calendar.create_event(
        "primary",
        summary=f"{test_prefix}_team_sync",
        description=f"Meet: {space.meeting_uri}\nDocs: https://drive.google.com/drive/folders/{folder.id}",
        start={"dateTime": start.isoformat()},
        end={"dateTime": end.isoformat()},
    )
    calendar_cleanup.append(("primary", event.id))

    # 4. Verify
    assert event.id
    assert space.meeting_uri in event.description
    assert folder.id in event.description

    # Verify the notes file is inside the folder
    fetched_notes = client.drive.get_file(notes.id, fields="id,parents")
    assert folder.id in (fetched_notes.parents or [])
