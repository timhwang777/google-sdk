"""Google API scope constants and auto-selection logic."""

from __future__ import annotations


class DriveScopes:
    FULL = "https://www.googleapis.com/auth/drive"
    READONLY = "https://www.googleapis.com/auth/drive.readonly"
    FILE = "https://www.googleapis.com/auth/drive.file"
    METADATA = "https://www.googleapis.com/auth/drive.metadata"
    METADATA_READONLY = "https://www.googleapis.com/auth/drive.metadata.readonly"
    APPDATA = "https://www.googleapis.com/auth/drive.appdata"


class CalendarScopes:
    FULL = "https://www.googleapis.com/auth/calendar"
    READONLY = "https://www.googleapis.com/auth/calendar.readonly"
    EVENTS = "https://www.googleapis.com/auth/calendar.events"
    EVENTS_READONLY = "https://www.googleapis.com/auth/calendar.events.readonly"


class MeetScopes:
    FULL = "https://www.googleapis.com/auth/meetings.space.created"
    READONLY = "https://www.googleapis.com/auth/meetings.space.readonly"


def auto_scopes(
    *,
    use_drive: bool = False,
    use_calendar: bool = False,
    use_meet: bool = False,
    override: list[str] | None = None,
) -> list[str]:
    """Return minimal scopes based on which services are used.

    Args:
        use_drive: Include Drive scopes.
        use_calendar: Include Calendar scopes.
        use_meet: Include Meet scopes.
        override: Override auto-selection with explicit scope list.

    Returns:
        List of OAuth scope strings.
    """
    if override is not None:
        return override
    scopes: list[str] = []
    if use_drive:
        scopes.append(DriveScopes.FULL)
    if use_calendar:
        scopes.append(CalendarScopes.FULL)
    if use_meet:
        scopes.append(MeetScopes.FULL)
    return scopes
