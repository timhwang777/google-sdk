"""Google Calendar service exports."""

from google_sdk.services import ServiceRegistry
from google_sdk.services.calendar.client import CalendarService
from google_sdk.services.calendar.models import Calendar, Event, FreeBusyResponse

ServiceRegistry.register("calendar")(CalendarService)

__all__ = ["CalendarService", "Calendar", "Event", "FreeBusyResponse"]
