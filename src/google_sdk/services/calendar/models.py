"""Google Calendar data models."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from google_sdk._models.base import BaseModel, BaseResource


class Calendar(BaseResource):
    """Represents a Google Calendar."""

    summary: str = ""
    description: str | None = None
    time_zone: str | None = Field(None, alias="timeZone")
    location: str | None = None
    primary: bool = False


class EventDateTime(BaseModel):
    """Represents either a timed or all-day event time."""

    model_config = {"extra": "allow", "populate_by_name": True}

    date_time: datetime | None = Field(None, alias="dateTime")
    date: str | None = None
    time_zone: str | None = Field(None, alias="timeZone")


class Attendee(BaseModel):
    """Represents a calendar event attendee."""

    model_config = {"extra": "allow", "populate_by_name": True}

    email: str = ""
    display_name: str | None = Field(None, alias="displayName")
    response_status: str = Field("needsAction", alias="responseStatus")
    organizer: bool = False
    self_: bool = Field(False, alias="self")
    optional: bool = False


class EventPerson(BaseModel):
    """Represents an event organizer or creator."""

    model_config = {"extra": "allow", "populate_by_name": True}

    email: str | None = None
    display_name: str | None = Field(None, alias="displayName")
    self_: bool = Field(False, alias="self")


class ReminderOverride(BaseModel):
    """Represents a reminder override."""

    model_config = {"extra": "allow", "populate_by_name": True}

    method: str = ""  # email|popup
    minutes: int = 0


class EventReminders(BaseModel):
    """Represents event reminder settings."""

    model_config = {"extra": "allow", "populate_by_name": True}

    use_default: bool = Field(True, alias="useDefault")
    overrides: list[ReminderOverride] = Field(default_factory=list)


class EntryPoint(BaseModel):
    """Represents a conference entry point."""

    model_config = {"extra": "allow", "populate_by_name": True}

    entry_point_type: str = Field("", alias="entryPointType")
    uri: str = ""
    label: str | None = None


class ConferenceSolution(BaseModel):
    """Represents a conference solution."""

    model_config = {"extra": "allow", "populate_by_name": True}

    name: str = ""
    icon_uri: str | None = Field(None, alias="iconUri")


class ConferenceData(BaseModel):
    """Represents conference data for an event."""

    model_config = {"extra": "allow", "populate_by_name": True}

    conference_id: str | None = Field(None, alias="conferenceId")
    entry_points: list[EntryPoint] = Field(default_factory=list, alias="entryPoints")
    conference_solution: ConferenceSolution | None = Field(None, alias="conferenceSolution")


class Event(BaseResource):
    """Represents a Google Calendar event."""

    summary: str | None = None
    description: str | None = None
    location: str | None = None
    start: EventDateTime | None = None
    end: EventDateTime | None = None
    status: str = "confirmed"
    attendees: list[Attendee] = Field(default_factory=list)
    recurrence: list[str] | None = None
    recurring_event_id: str | None = Field(None, alias="recurringEventId")
    html_link: str | None = Field(None, alias="htmlLink")
    hangout_link: str | None = Field(None, alias="hangoutLink")
    conference_data: ConferenceData | None = Field(None, alias="conferenceData")
    organizer: EventPerson | None = None
    creator: EventPerson | None = None
    reminders: EventReminders | None = None
    created: datetime | None = None
    updated: datetime | None = None


class TimePeriod(BaseModel):
    """Represents a time period."""

    model_config = {"extra": "allow", "populate_by_name": True}

    start: datetime
    end: datetime


class FreeBusyCalendar(BaseModel):
    """FreeBusy information for a single calendar."""

    model_config = {"extra": "allow", "populate_by_name": True}

    busy: list[TimePeriod] = Field(default_factory=list)
    errors: list[dict] = Field(default_factory=list)


class FreeBusyResponse(BaseModel):
    """Response from the freebusy query endpoint."""

    model_config = {"extra": "allow", "populate_by_name": True}

    calendars: dict[str, FreeBusyCalendar] = Field(default_factory=dict)


class FreeBusyRequest(BaseModel):
    """Request body for freebusy queries."""

    model_config = {"extra": "allow", "populate_by_name": True}

    time_min: datetime = Field(alias="timeMin")
    time_max: datetime = Field(alias="timeMax")
    items: list[dict] = Field(default_factory=list)
    time_zone: str | None = Field(None, alias="timeZone")
