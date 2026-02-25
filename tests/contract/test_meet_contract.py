"""Contract tests for MeetService public API."""

import inspect

from google_sdk.services.meet.client import MeetService


def test_create_space_signature():
    sig = inspect.signature(MeetService.create_space)
    assert "config" in sig.parameters


def test_get_space_signature():
    sig = inspect.signature(MeetService.get_space)
    assert "space_name" in sig.parameters


def test_update_space_signature():
    sig = inspect.signature(MeetService.update_space)
    assert "space_name" in sig.parameters


def test_end_active_conference_signature():
    sig = inspect.signature(MeetService.end_active_conference)
    assert "space_name" in sig.parameters


def test_list_participants_signature():
    sig = inspect.signature(MeetService.list_participants)
    assert "conference_record" in sig.parameters


def test_get_participant_signature():
    sig = inspect.signature(MeetService.get_participant)
    assert "name" in sig.parameters


def test_list_participant_sessions_signature():
    sig = inspect.signature(MeetService.list_participant_sessions)
    assert "participant_name" in sig.parameters


def test_list_recordings_signature():
    sig = inspect.signature(MeetService.list_recordings)
    assert "conference_record" in sig.parameters


def test_get_recording_signature():
    sig = inspect.signature(MeetService.get_recording)
    assert "name" in sig.parameters
