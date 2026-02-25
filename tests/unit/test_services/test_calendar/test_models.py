"""Tests for Google Calendar data models."""

from google_sdk.services.calendar.models import (
    Attendee,
    Calendar,
    ConferenceData,
    Event,
    EventDateTime,
    FreeBusyResponse,
)


def test_calendar_defaults():
    c = Calendar(id="primary", summary="My Calendar")
    assert c.summary == "My Calendar"
    assert c.primary is False
    assert c.description is None


def test_calendar_alias():
    data = {"id": "c1", "summary": "Work", "timeZone": "America/New_York"}
    c = Calendar.model_validate(data)
    assert c.time_zone == "America/New_York"


def test_event_datetime_alias():
    data = {"dateTime": "2026-01-01T10:00:00Z", "timeZone": "UTC"}
    edt = EventDateTime.model_validate(data)
    assert edt.date_time is not None
    assert edt.time_zone == "UTC"


def test_attendee_defaults():
    a = Attendee(email="test@example.com")
    assert a.response_status == "needsAction"
    assert a.organizer is False
    assert a.optional is False


def test_attendee_alias():
    data = {"email": "a@b.com", "displayName": "Alice", "responseStatus": "accepted", "self": True}
    a = Attendee.model_validate(data)
    assert a.display_name == "Alice"
    assert a.response_status == "accepted"
    assert a.self_ is True


def test_event_creation():
    data = {
        "id": "evt1",
        "summary": "Meeting",
        "start": {"dateTime": "2026-01-01T10:00:00Z"},
        "end": {"dateTime": "2026-01-01T11:00:00Z"},
    }
    e = Event.model_validate(data)
    assert e.id == "evt1"
    assert e.summary == "Meeting"
    assert e.start is not None


def test_event_attendees_default():
    e = Event.model_validate({"id": "1"})
    assert e.attendees == []


def test_conference_data_alias():
    data = {
        "conferenceId": "conf1",
        "entryPoints": [{"entryPointType": "video", "uri": "https://meet.google.com/abc"}],
        "conferenceSolution": {"name": "Google Meet"},
    }
    cd = ConferenceData.model_validate(data)
    assert cd.conference_id == "conf1"
    assert len(cd.entry_points) == 1
    assert cd.conference_solution.name == "Google Meet"


def test_freebusy_response():
    data = {
        "calendars": {
            "primary": {"busy": [{"start": "2026-01-01T10:00:00Z", "end": "2026-01-01T11:00:00Z"}]}
        }
    }
    resp = FreeBusyResponse.model_validate(data)
    assert "primary" in resp.calendars
    assert len(resp.calendars["primary"].busy) == 1
