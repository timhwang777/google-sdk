"""Google Calendar service client."""

from __future__ import annotations

import logging
from datetime import datetime

from google_sdk._pagination import PageIterator
from google_sdk.services._base import CALENDAR_API_VERSION, BaseService
from google_sdk.services.calendar.models import (
    Calendar,
    Event,
    FreeBusyResponse,
)

logger = logging.getLogger("google_sdk.services.calendar")

_API_BASE = f"https://www.googleapis.com/calendar/{CALENDAR_API_VERSION}"


class CalendarService(BaseService):
    """Client for Google Calendar API v3."""

    _BASE_URL = _API_BASE

    # ── Calendar operations ──────────────────────────────────────────────────

    def list_calendars(self) -> PageIterator[Calendar]:
        def fetch_page(page_token: str | None) -> dict:
            params = {}
            if page_token:
                params["pageToken"] = page_token
            return self._get("/users/me/calendarList", params=params)

        return PageIterator(fetch_page, Calendar, response_key="items")

    def get_calendar(self, calendar_id: str = "primary") -> Calendar:
        data = self._get(f"/calendars/{calendar_id}")
        return self._parse(data, Calendar)

    def create_calendar(self, summary: str, **kwargs) -> Calendar:
        body = {"summary": summary, **kwargs}
        data = self._post("/calendars", json=body)
        return self._parse(data, Calendar)

    def update_calendar(self, calendar_id: str, **kwargs) -> Calendar:
        data = self._patch(f"/calendars/{calendar_id}", json=kwargs)
        return self._parse(data, Calendar)

    def delete_calendar(self, calendar_id: str) -> None:
        self._delete(f"/calendars/{calendar_id}")

    # ── Event operations ─────────────────────────────────────────────────────

    def list_events(
        self,
        calendar_id: str = "primary",
        *,
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        q: str | None = None,
        single_events: bool = True,
        order_by: str | None = None,
    ) -> PageIterator[Event]:
        params: dict = {"singleEvents": single_events}
        if time_min:
            params["timeMin"] = time_min.isoformat()
        if time_max:
            params["timeMax"] = time_max.isoformat()
        if q:
            params["q"] = q
        if order_by:
            params["orderBy"] = order_by

        def fetch_page(page_token: str | None) -> dict:
            p = dict(params)
            if page_token:
                p["pageToken"] = page_token
            return self._get(f"/calendars/{calendar_id}/events", params=p)

        return PageIterator(fetch_page, Event, response_key="items")

    def get_event(self, calendar_id: str, event_id: str) -> Event:
        data = self._get(f"/calendars/{calendar_id}/events/{event_id}")
        return self._parse(data, Event)

    def create_event(self, calendar_id: str = "primary", **kwargs) -> Event:
        data = self._post(f"/calendars/{calendar_id}/events", json=kwargs)
        return self._parse(data, Event)

    def quick_add(self, text: str, *, calendar_id: str = "primary") -> Event:
        data = self._post(
            f"/calendars/{calendar_id}/events/quickAdd",
            params={"text": text},
        )
        return self._parse(data, Event)

    def update_event(self, calendar_id: str, event_id: str, **kwargs) -> Event:
        data = self._patch(f"/calendars/{calendar_id}/events/{event_id}", json=kwargs)
        return self._parse(data, Event)

    def delete_event(self, calendar_id: str, event_id: str) -> None:
        self._delete(f"/calendars/{calendar_id}/events/{event_id}")

    def freebusy(
        self,
        time_min: datetime,
        time_max: datetime,
        calendar_ids: list[str],
    ) -> FreeBusyResponse:
        body = {
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "items": [{"id": cid} for cid in calendar_ids],
        }
        data = self._post("/freeBusy", json=body)
        return FreeBusyResponse.model_validate(data)
