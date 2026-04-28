"""Integration tests for CalendarService against live Google Calendar API."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from google_sdk.exceptions import NotFoundError
from google_sdk.services.calendar.models import Calendar, Event, FreeBusyResponse

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _future_dt(hours: int = 1) -> datetime:
    """Return a timezone-aware datetime in the near future."""
    return datetime.now(UTC) + timedelta(hours=hours)


# ---------------------------------------------------------------------------
# Calendar CRUD
# ---------------------------------------------------------------------------


def test_list_calendars(client):
    """list_calendars returns an iterable containing at least the primary calendar."""
    calendars = list(client.calendar.list_calendars())
    assert len(calendars) >= 1
    assert all(isinstance(c, Calendar) for c in calendars)


def test_get_primary_calendar(client):
    """get_calendar('primary') returns a Calendar with expected fields."""
    cal = client.calendar.get_calendar("primary")
    assert isinstance(cal, Calendar)
    assert cal.summary  # primary calendar always has a summary


def test_create_and_delete_calendar(client, test_prefix):
    """Create a secondary calendar, verify it, then delete it.

    Note: Google Calendar deletion is eventually consistent — a deleted
    calendar can remain readable for tens of seconds. We rely on
    ``delete_calendar`` raising on API failure rather than polling
    ``get_calendar``, which would make the test flaky.
    """
    summary = f"{test_prefix}_test_cal"
    cal = client.calendar.create_calendar(summary)

    assert cal.id
    assert cal.summary == summary

    client.calendar.delete_calendar(cal.id)


def test_update_calendar(client, test_prefix, calendar_cleanup):
    """Create a calendar, update its summary, and verify."""
    cal = client.calendar.create_calendar(f"{test_prefix}_update_cal")
    calendar_cleanup.append(("calendar", cal.id))

    new_summary = f"{test_prefix}_updated_cal"
    updated = client.calendar.update_calendar(cal.id, summary=new_summary)
    assert updated.summary == new_summary


# ---------------------------------------------------------------------------
# Event CRUD
# ---------------------------------------------------------------------------


def test_create_and_get_event(client, test_prefix, calendar_cleanup):
    """Create an event on primary calendar, then fetch it by ID."""
    start = _future_dt(2)
    end = _future_dt(3)

    event = client.calendar.create_event(
        "primary",
        summary=f"{test_prefix}_event",
        start={"dateTime": start.isoformat()},
        end={"dateTime": end.isoformat()},
    )
    calendar_cleanup.append(("primary", event.id))

    assert event.id
    assert event.summary == f"{test_prefix}_event"

    fetched = client.calendar.get_event("primary", event.id)
    assert fetched.id == event.id


def test_quick_add(client, test_prefix, calendar_cleanup):
    """quick_add parses natural language into an event."""
    event = client.calendar.quick_add(f"{test_prefix} meeting tomorrow at 3pm")
    calendar_cleanup.append(("primary", event.id))

    assert event.id
    assert isinstance(event, Event)


def test_update_event(client, test_prefix, calendar_cleanup):
    """Create an event, update its summary, verify the change."""
    start = _future_dt(4)
    end = _future_dt(5)

    event = client.calendar.create_event(
        "primary",
        summary=f"{test_prefix}_before",
        start={"dateTime": start.isoformat()},
        end={"dateTime": end.isoformat()},
    )
    calendar_cleanup.append(("primary", event.id))

    new_summary = f"{test_prefix}_after"
    updated = client.calendar.update_event("primary", event.id, summary=new_summary)
    assert updated.summary == new_summary


def test_delete_event(client, test_prefix):
    """Create an event, delete it, verify it's gone."""
    start = _future_dt(6)
    end = _future_dt(7)

    event = client.calendar.create_event(
        "primary",
        summary=f"{test_prefix}_delete_me",
        start={"dateTime": start.isoformat()},
        end={"dateTime": end.isoformat()},
    )

    client.calendar.delete_event("primary", event.id)

    with pytest.raises(NotFoundError):
        client.calendar.get_event("primary", event.id)


# ---------------------------------------------------------------------------
# List events with filters
# ---------------------------------------------------------------------------


def test_list_events_with_time_filter(client, test_prefix, calendar_cleanup):
    """Create an event in a known time window and filter for it."""
    start = _future_dt(24)
    end = _future_dt(25)

    event = client.calendar.create_event(
        "primary",
        summary=f"{test_prefix}_filtered",
        start={"dateTime": start.isoformat()},
        end={"dateTime": end.isoformat()},
    )
    calendar_cleanup.append(("primary", event.id))

    time_min = start - timedelta(minutes=30)
    time_max = end + timedelta(minutes=30)

    events = list(
        client.calendar.list_events(
            "primary",
            time_min=time_min,
            time_max=time_max,
            single_events=True,
        )
    )

    ids = [e.id for e in events]
    assert event.id in ids


# ---------------------------------------------------------------------------
# FreeBusy
# ---------------------------------------------------------------------------


def test_freebusy(client):
    """Query freebusy for the primary calendar — should return a valid response."""
    now = datetime.now(UTC)
    response = client.calendar.freebusy(
        time_min=now,
        time_max=now + timedelta(hours=1),
        calendar_ids=["primary"],
    )
    assert isinstance(response, FreeBusyResponse)
    assert "primary" in response.calendars
