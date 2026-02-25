"""Tests for Google Meet data models."""

from google_sdk.services.meet.models import (
    DriveDestination,
    Participant,
    Recording,
    Space,
    SpaceConfig,
)


def test_space_config_defaults():
    cfg = SpaceConfig()
    assert cfg.access_type == "OPEN"
    assert cfg.entry_point_access == "ALL"


def test_space_config_alias():
    data = {"accessType": "RESTRICTED", "entryPointAccess": "CREATOR_APP_ONLY"}
    cfg = SpaceConfig.model_validate(data)
    assert cfg.access_type == "RESTRICTED"


def test_space_creation():
    data = {
        "name": "spaces/abc123",
        "meetingUri": "https://meet.google.com/abc-123",
        "meetingCode": "abc-123",
    }
    s = Space.model_validate(data)
    assert s.name == "spaces/abc123"
    assert s.meeting_uri == "https://meet.google.com/abc-123"
    assert s.meeting_code == "abc-123"


def test_participant_alias():
    data = {
        "name": "conferenceRecords/r1/participants/p1",
        "earliestStartTime": "2026-01-01T10:00:00Z",
        "latestEndTime": "2026-01-01T11:00:00Z",
        "signedinUser": {"user": "users/u1", "displayName": "Alice"},
    }
    p = Participant.model_validate(data)
    assert p.signin_user is not None
    assert p.signin_user.display_name == "Alice"
    assert p.earliest_start_time is not None


def test_recording_state():
    data = {"name": "recordings/r1", "state": "STARTED", "startTime": "2026-01-01T10:00:00Z"}
    r = Recording.model_validate(data)
    assert r.state == "STARTED"
    assert r.start_time is not None


def test_drive_destination_alias():
    data = {"file": "files/f1", "exportUri": "https://drive.google.com/..."}
    dd = DriveDestination.model_validate(data)
    assert dd.export_uri == "https://drive.google.com/..."
