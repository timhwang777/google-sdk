"""Tests for MeetService using respx mock."""

from __future__ import annotations

from unittest.mock import MagicMock

import google.auth.credentials
import httpx
import respx

from google_sdk._config import SDKConfig
from google_sdk.services.meet.client import _API_BASE, MeetService
from google_sdk.services.meet.models import (
    Participant,
    ParticipantSession,
    Recording,
    Space,
    SpaceConfig,
)


def make_creds():
    creds = MagicMock(spec=google.auth.credentials.Credentials)
    creds.valid = True
    creds.token = "fake_token"
    return creds


def make_service():
    return MeetService(make_creds(), SDKConfig())


SPACE_DATA = {
    "name": "spaces/abc123",
    "meetingUri": "https://meet.google.com/abc-xyz-123",
    "meetingCode": "abc-xyz-123",
}

PARTICIPANT_DATA = {
    "name": "conferenceRecords/r1/participants/p1",
    "earliestStartTime": "2026-01-01T10:00:00Z",
    "latestEndTime": "2026-01-01T11:00:00Z",
}

SESSION_DATA = {
    "name": "conferenceRecords/r1/participants/p1/participantSessions/s1",
    "startTime": "2026-01-01T10:00:00Z",
    "endTime": "2026-01-01T10:30:00Z",
}

RECORDING_DATA = {
    "name": "conferenceRecords/r1/recordings/rec1",
    "state": "ENDED",
    "startTime": "2026-01-01T10:00:00Z",
    "endTime": "2026-01-01T11:00:00Z",
}


# ── Space operations ─────────────────────────────────────────────────────────


@respx.mock
def test_create_space():
    respx.post(f"{_API_BASE}/spaces").mock(return_value=httpx.Response(200, json=SPACE_DATA))
    svc = make_service()
    space = svc.create_space()
    assert isinstance(space, Space)
    assert space.name == "spaces/abc123"
    assert space.meeting_uri == "https://meet.google.com/abc-xyz-123"


@respx.mock
def test_create_space_with_config():
    respx.post(f"{_API_BASE}/spaces").mock(return_value=httpx.Response(200, json=SPACE_DATA))
    svc = make_service()
    config = SpaceConfig(access_type="TRUSTED")
    space = svc.create_space(config=config)
    assert isinstance(space, Space)


@respx.mock
def test_get_space():
    respx.get(f"{_API_BASE}/spaces/abc123").mock(return_value=httpx.Response(200, json=SPACE_DATA))
    svc = make_service()
    space = svc.get_space("abc123")
    assert space.name == "spaces/abc123"
    assert space.meeting_code == "abc-xyz-123"


@respx.mock
def test_update_space():
    updated = {**SPACE_DATA, "config": {"accessType": "RESTRICTED"}}
    respx.patch(f"{_API_BASE}/spaces/abc123").mock(return_value=httpx.Response(200, json=updated))
    svc = make_service()
    space = svc.update_space("abc123", config={"accessType": "RESTRICTED"})
    assert isinstance(space, Space)


@respx.mock
def test_end_active_conference():
    respx.post(f"{_API_BASE}/spaces/abc123:endActiveConference").mock(
        return_value=httpx.Response(200, json={})
    )
    svc = make_service()
    svc.end_active_conference("abc123")  # Should not raise


# ── Participant operations ───────────────────────────────────────────────────


@respx.mock
def test_list_participants():
    respx.get(f"{_API_BASE}/conferenceRecords/r1/participants").mock(
        return_value=httpx.Response(200, json={"participants": [PARTICIPANT_DATA]})
    )
    svc = make_service()
    participants = list(svc.list_participants("r1"))
    assert len(participants) == 1
    assert isinstance(participants[0], Participant)
    assert participants[0].name == "conferenceRecords/r1/participants/p1"


@respx.mock
def test_list_participants_pagination():
    page1 = {"participants": [PARTICIPANT_DATA], "nextPageToken": "tok1"}
    page2 = {"participants": [{**PARTICIPANT_DATA, "name": "conferenceRecords/r1/participants/p2"}]}
    respx.get(f"{_API_BASE}/conferenceRecords/r1/participants").mock(
        side_effect=[
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
        ]
    )
    svc = make_service()
    participants = list(svc.list_participants("r1"))
    assert len(participants) == 2


@respx.mock
def test_get_participant():
    name = "conferenceRecords/r1/participants/p1"
    respx.get(f"{_API_BASE}/{name}").mock(return_value=httpx.Response(200, json=PARTICIPANT_DATA))
    svc = make_service()
    participant = svc.get_participant(name)
    assert isinstance(participant, Participant)


@respx.mock
def test_list_participant_sessions():
    participant_name = "conferenceRecords/r1/participants/p1"
    respx.get(f"{_API_BASE}/{participant_name}/participantSessions").mock(
        return_value=httpx.Response(200, json={"participantSessions": [SESSION_DATA]})
    )
    svc = make_service()
    sessions = list(svc.list_participant_sessions(participant_name))
    assert len(sessions) == 1
    assert isinstance(sessions[0], ParticipantSession)


# ── Recording operations ─────────────────────────────────────────────────────


@respx.mock
def test_list_recordings():
    respx.get(f"{_API_BASE}/conferenceRecords/r1/recordings").mock(
        return_value=httpx.Response(200, json={"recordings": [RECORDING_DATA]})
    )
    svc = make_service()
    recordings = list(svc.list_recordings("r1"))
    assert len(recordings) == 1
    assert isinstance(recordings[0], Recording)
    assert recordings[0].state == "ENDED"


@respx.mock
def test_list_recordings_pagination():
    page1 = {"recordings": [RECORDING_DATA], "nextPageToken": "tok1"}
    page2 = {"recordings": [{**RECORDING_DATA, "name": "conferenceRecords/r1/recordings/rec2"}]}
    respx.get(f"{_API_BASE}/conferenceRecords/r1/recordings").mock(
        side_effect=[
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
        ]
    )
    svc = make_service()
    recordings = list(svc.list_recordings("r1"))
    assert len(recordings) == 2


@respx.mock
def test_get_recording():
    name = "conferenceRecords/r1/recordings/rec1"
    respx.get(f"{_API_BASE}/{name}").mock(return_value=httpx.Response(200, json=RECORDING_DATA))
    svc = make_service()
    recording = svc.get_recording(name)
    assert isinstance(recording, Recording)
    assert recording.state == "ENDED"
