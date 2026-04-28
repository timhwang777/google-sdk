"""Tests for CalendarService using respx mock."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import google.auth.credentials
import httpx
import respx

from google_sdk._config import SDKConfig
from google_sdk.services.calendar.client import _API_BASE, CalendarService
from google_sdk.services.calendar.models import Calendar, Event, FreeBusyResponse


def make_creds():
    creds = MagicMock(spec=google.auth.credentials.Credentials)
    creds.valid = True
    creds.token = "fake_token"
    return creds


def make_service():
    return CalendarService(make_creds(), SDKConfig())


CALENDAR_DATA = {
    "id": "primary",
    "summary": "My Calendar",
    "kind": "calendar#calendar",
}

EVENT_DATA = {
    "id": "event1",
    "summary": "Team Meeting",
    "start": {"dateTime": "2026-01-01T10:00:00Z"},
    "end": {"dateTime": "2026-01-01T11:00:00Z"},
    "status": "confirmed",
}


# ── Calendar operations ──────────────────────────────────────────────────────


@respx.mock
def test_list_calendars():
    respx.get(f"{_API_BASE}/users/me/calendarList").mock(
        return_value=httpx.Response(200, json={"items": [CALENDAR_DATA]})
    )
    svc = make_service()
    calendars = list(svc.list_calendars())
    assert len(calendars) == 1
    assert isinstance(calendars[0], Calendar)
    assert calendars[0].id == "primary"


@respx.mock
def test_list_calendars_pagination():
    page1 = {"items": [CALENDAR_DATA], "nextPageToken": "tok1"}
    page2 = {"items": [{**CALENDAR_DATA, "id": "cal2"}]}
    respx.get(f"{_API_BASE}/users/me/calendarList").mock(
        side_effect=[
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
        ]
    )
    svc = make_service()
    calendars = list(svc.list_calendars())
    assert len(calendars) == 2


@respx.mock
def test_get_calendar():
    respx.get(f"{_API_BASE}/calendars/primary").mock(
        return_value=httpx.Response(200, json=CALENDAR_DATA)
    )
    svc = make_service()
    cal = svc.get_calendar("primary")
    assert cal.id == "primary"
    assert cal.summary == "My Calendar"


@respx.mock
def test_get_calendar_default_primary():
    respx.get(f"{_API_BASE}/calendars/primary").mock(
        return_value=httpx.Response(200, json=CALENDAR_DATA)
    )
    svc = make_service()
    cal = svc.get_calendar()  # no argument → defaults to "primary"
    assert cal.id == "primary"


@respx.mock
def test_create_calendar():
    respx.post(f"{_API_BASE}/calendars").mock(return_value=httpx.Response(200, json=CALENDAR_DATA))
    svc = make_service()
    cal = svc.create_calendar("My Calendar")
    assert isinstance(cal, Calendar)


@respx.mock
def test_update_calendar():
    updated = {**CALENDAR_DATA, "summary": "Updated Calendar"}
    respx.patch(f"{_API_BASE}/calendars/primary").mock(
        return_value=httpx.Response(200, json=updated)
    )
    svc = make_service()
    cal = svc.update_calendar("primary", summary="Updated Calendar")
    assert cal.summary == "Updated Calendar"


@respx.mock
def test_delete_calendar():
    respx.delete(f"{_API_BASE}/calendars/cal123").mock(
        return_value=httpx.Response(204, content=b"")
    )
    svc = make_service()
    svc.delete_calendar("cal123")  # Should not raise


# ── Event operations ─────────────────────────────────────────────────────────


@respx.mock
def test_list_events():
    respx.get(f"{_API_BASE}/calendars/primary/events").mock(
        return_value=httpx.Response(200, json={"items": [EVENT_DATA]})
    )
    svc = make_service()
    events = list(svc.list_events())
    assert len(events) == 1
    assert isinstance(events[0], Event)
    assert events[0].id == "event1"


@respx.mock
def test_list_events_pagination():
    page1 = {"items": [EVENT_DATA], "nextPageToken": "tok1"}
    page2 = {"items": [{**EVENT_DATA, "id": "event2"}]}
    respx.get(f"{_API_BASE}/calendars/primary/events").mock(
        side_effect=[
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
        ]
    )
    svc = make_service()
    events = list(svc.list_events())
    assert len(events) == 2


@respx.mock
def test_list_events_with_time_range():
    route = respx.get(f"{_API_BASE}/calendars/primary/events").mock(
        return_value=httpx.Response(200, json={"items": []})
    )
    svc = make_service()
    time_min = datetime(2026, 1, 1, tzinfo=UTC)
    time_max = datetime(2026, 1, 31, tzinfo=UTC)
    list(svc.list_events(time_min=time_min, time_max=time_max))

    req = route.calls[0].request
    assert "timeMin" in str(req.url)
    assert "timeMax" in str(req.url)


@respx.mock
def test_list_events_with_q():
    route = respx.get(f"{_API_BASE}/calendars/primary/events").mock(
        return_value=httpx.Response(200, json={"items": []})
    )
    svc = make_service()
    list(svc.list_events(q="team meeting"))
    req = route.calls[0].request
    assert "q=team+meeting" in str(req.url) or "q=team%20meeting" in str(req.url)


@respx.mock
def test_get_event():
    respx.get(f"{_API_BASE}/calendars/primary/events/event1").mock(
        return_value=httpx.Response(200, json=EVENT_DATA)
    )
    svc = make_service()
    event = svc.get_event("primary", "event1")
    assert event.id == "event1"
    assert event.summary == "Team Meeting"


@respx.mock
def test_create_event():
    route = respx.post(f"{_API_BASE}/calendars/primary/events").mock(
        return_value=httpx.Response(200, json=EVENT_DATA)
    )
    svc = make_service()
    event = svc.create_event(
        summary="Team Meeting",
        start={"dateTime": "2026-01-01T10:00:00Z"},
        end={"dateTime": "2026-01-01T11:00:00Z"},
    )
    assert isinstance(event, Event)
    assert event.id == "event1"
    # No new params -> no query string sent.
    assert route.calls.last.request.url.query == b""


@respx.mock
def test_create_event_with_conference_and_send_updates():
    route = respx.post(f"{_API_BASE}/calendars/primary/events").mock(
        return_value=httpx.Response(200, json=EVENT_DATA)
    )
    svc = make_service()
    svc.create_event(
        conference_data_version=1,
        send_updates="all",
        summary="Team Meeting",
        conferenceData={"createRequest": {"requestId": "abc"}},
    )
    qs = route.calls.last.request.url.params
    assert qs["conferenceDataVersion"] == "1"
    assert qs["sendUpdates"] == "all"


@respx.mock
def test_quick_add():
    respx.post(f"{_API_BASE}/calendars/primary/events/quickAdd").mock(
        return_value=httpx.Response(200, json=EVENT_DATA)
    )
    svc = make_service()
    event = svc.quick_add("Team Meeting tomorrow at 10am")
    assert isinstance(event, Event)


@respx.mock
def test_update_event():
    updated = {**EVENT_DATA, "summary": "Updated Meeting"}
    respx.patch(f"{_API_BASE}/calendars/primary/events/event1").mock(
        return_value=httpx.Response(200, json=updated)
    )
    svc = make_service()
    event = svc.update_event("primary", "event1", summary="Updated Meeting")
    assert event.summary == "Updated Meeting"


@respx.mock
def test_delete_event():
    respx.delete(f"{_API_BASE}/calendars/primary/events/event1").mock(
        return_value=httpx.Response(204, content=b"")
    )
    svc = make_service()
    svc.delete_event("primary", "event1")  # Should not raise


# ── freebusy ─────────────────────────────────────────────────────────────────


@respx.mock
def test_freebusy():
    freebusy_response = {
        "kind": "calendar#freeBusy",
        "timeMin": "2026-01-01T00:00:00Z",
        "timeMax": "2026-01-02T00:00:00Z",
        "calendars": {
            "primary": {"busy": [{"start": "2026-01-01T10:00:00Z", "end": "2026-01-01T11:00:00Z"}]}
        },
    }
    respx.post(f"{_API_BASE}/freeBusy").mock(
        return_value=httpx.Response(200, json=freebusy_response)
    )
    svc = make_service()
    result = svc.freebusy(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 2, tzinfo=UTC),
        calendar_ids=["primary"],
    )
    assert isinstance(result, FreeBusyResponse)
    assert "primary" in result.calendars
    assert len(result.calendars["primary"].busy) == 1


@respx.mock
def test_freebusy_empty_busy():
    respx.post(f"{_API_BASE}/freeBusy").mock(
        return_value=httpx.Response(200, json={"calendars": {"primary": {"busy": []}}})
    )
    svc = make_service()
    result = svc.freebusy(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 2, tzinfo=UTC),
        calendar_ids=["primary"],
    )
    assert result.calendars["primary"].busy == []
