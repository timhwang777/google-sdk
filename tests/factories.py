"""Test factories for Pydantic models."""

from __future__ import annotations

from google_sdk.services.calendar.models import Attendee, Calendar, Event
from google_sdk.services.drive.models import File, Folder, Permission
from google_sdk.services.meet.models import Participant, Recording, Space


def make_file(**kwargs) -> File:
    defaults = {
        "id": "file1",
        "name": "test.txt",
        "mimeType": "text/plain",
        "kind": "drive#file",
    }
    defaults.update(kwargs)
    return File.model_validate(defaults)


def make_folder(**kwargs) -> Folder:
    defaults = {
        "id": "folder1",
        "name": "My Folder",
        "kind": "drive#file",
    }
    defaults.update(kwargs)
    return Folder.model_validate(defaults)


def make_permission(**kwargs) -> Permission:
    defaults = {
        "id": "perm1",
        "type": "user",
        "role": "writer",
        "emailAddress": "user@example.com",
    }
    defaults.update(kwargs)
    return Permission.model_validate(defaults)


def make_calendar(**kwargs) -> Calendar:
    defaults = {
        "id": "primary",
        "summary": "My Calendar",
        "kind": "calendar#calendarListEntry",
    }
    defaults.update(kwargs)
    return Calendar.model_validate(defaults)


def make_event(**kwargs) -> Event:
    defaults = {
        "id": "event1",
        "summary": "Test Event",
        "start": {"dateTime": "2026-01-01T10:00:00Z"},
        "end": {"dateTime": "2026-01-01T11:00:00Z"},
        "status": "confirmed",
    }
    defaults.update(kwargs)
    return Event.model_validate(defaults)


def make_attendee(**kwargs) -> Attendee:
    defaults = {"email": "attendee@example.com"}
    defaults.update(kwargs)
    return Attendee.model_validate(defaults)


def make_space(**kwargs) -> Space:
    defaults = {
        "name": "spaces/abc123",
        "meetingUri": "https://meet.google.com/abc-xyz-123",
        "meetingCode": "abc-xyz-123",
    }
    defaults.update(kwargs)
    return Space.model_validate(defaults)


def make_participant(**kwargs) -> Participant:
    defaults = {
        "name": "conferenceRecords/r1/participants/p1",
        "earliestStartTime": "2026-01-01T10:00:00Z",
    }
    defaults.update(kwargs)
    return Participant.model_validate(defaults)


def make_recording(**kwargs) -> Recording:
    defaults = {
        "name": "conferenceRecords/r1/recordings/rec1",
        "state": "ENDED",
        "startTime": "2026-01-01T10:00:00Z",
        "endTime": "2026-01-01T11:00:00Z",
    }
    defaults.update(kwargs)
    return Recording.model_validate(defaults)
