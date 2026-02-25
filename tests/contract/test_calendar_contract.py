"""Contract tests for CalendarService public API."""

import inspect

from google_sdk.services.calendar.client import CalendarService


def test_list_calendars_signature():
    sig = inspect.signature(CalendarService.list_calendars)
    # No required params beyond self
    assert len(sig.parameters) == 1  # just self


def test_get_calendar_signature():
    sig = inspect.signature(CalendarService.get_calendar)
    assert "calendar_id" in sig.parameters


def test_create_calendar_signature():
    sig = inspect.signature(CalendarService.create_calendar)
    assert "summary" in sig.parameters


def test_update_calendar_signature():
    sig = inspect.signature(CalendarService.update_calendar)
    assert "calendar_id" in sig.parameters


def test_delete_calendar_signature():
    sig = inspect.signature(CalendarService.delete_calendar)
    assert "calendar_id" in sig.parameters


def test_list_events_signature():
    sig = inspect.signature(CalendarService.list_events)
    params = sig.parameters
    assert "calendar_id" in params
    assert "time_min" in params
    assert "time_max" in params
    assert "q" in params
    assert "single_events" in params


def test_get_event_signature():
    sig = inspect.signature(CalendarService.get_event)
    params = sig.parameters
    assert "calendar_id" in params
    assert "event_id" in params


def test_create_event_signature():
    sig = inspect.signature(CalendarService.create_event)
    assert "calendar_id" in sig.parameters


def test_quick_add_signature():
    sig = inspect.signature(CalendarService.quick_add)
    params = sig.parameters
    assert "text" in params
    assert "calendar_id" in params


def test_update_event_signature():
    sig = inspect.signature(CalendarService.update_event)
    params = sig.parameters
    assert "calendar_id" in params
    assert "event_id" in params


def test_delete_event_signature():
    sig = inspect.signature(CalendarService.delete_event)
    params = sig.parameters
    assert "calendar_id" in params
    assert "event_id" in params


def test_freebusy_signature():
    sig = inspect.signature(CalendarService.freebusy)
    params = sig.parameters
    assert "time_min" in params
    assert "time_max" in params
    assert "calendar_ids" in params
