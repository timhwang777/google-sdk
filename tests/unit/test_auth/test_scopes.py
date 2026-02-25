"""Tests for scope constants and auto_scopes()."""

from google_sdk.auth.scopes import CalendarScopes, DriveScopes, MeetScopes, auto_scopes


def test_drive_scope_constants():
    assert DriveScopes.FULL == "https://www.googleapis.com/auth/drive"
    assert DriveScopes.READONLY == "https://www.googleapis.com/auth/drive.readonly"
    assert DriveScopes.FILE == "https://www.googleapis.com/auth/drive.file"


def test_calendar_scope_constants():
    assert CalendarScopes.FULL == "https://www.googleapis.com/auth/calendar"
    assert CalendarScopes.READONLY == "https://www.googleapis.com/auth/calendar.readonly"


def test_meet_scope_constants():
    assert MeetScopes.FULL == "https://www.googleapis.com/auth/meetings.space.created"
    assert MeetScopes.READONLY == "https://www.googleapis.com/auth/meetings.space.readonly"


def test_auto_scopes_drive_only():
    scopes = auto_scopes(use_drive=True)
    assert DriveScopes.FULL in scopes
    assert CalendarScopes.FULL not in scopes
    assert MeetScopes.FULL not in scopes


def test_auto_scopes_calendar_only():
    scopes = auto_scopes(use_calendar=True)
    assert CalendarScopes.FULL in scopes
    assert DriveScopes.FULL not in scopes


def test_auto_scopes_meet_only():
    scopes = auto_scopes(use_meet=True)
    assert MeetScopes.FULL in scopes
    assert DriveScopes.FULL not in scopes


def test_auto_scopes_all_services():
    scopes = auto_scopes(use_drive=True, use_calendar=True, use_meet=True)
    assert DriveScopes.FULL in scopes
    assert CalendarScopes.FULL in scopes
    assert MeetScopes.FULL in scopes
    assert len(scopes) == 3


def test_auto_scopes_none_selected():
    scopes = auto_scopes()
    assert scopes == []


def test_auto_scopes_override():
    custom = ["https://www.googleapis.com/auth/drive.readonly"]
    scopes = auto_scopes(use_drive=True, override=custom)
    assert scopes == custom
    assert DriveScopes.FULL not in scopes
