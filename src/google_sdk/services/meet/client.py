"""Google Meet service client."""

from __future__ import annotations

import logging

from google_sdk._pagination import PageIterator
from google_sdk.services._base import MEET_API_VERSION, BaseService
from google_sdk.services.meet.models import (
    Participant,
    ParticipantSession,
    Recording,
    Space,
    SpaceConfig,
)

logger = logging.getLogger("google_sdk.services.meet")

_API_BASE = f"https://meet.googleapis.com/{MEET_API_VERSION}"


class MeetService(BaseService):
    """Client for Google Meet REST API v2."""

    _BASE_URL = _API_BASE

    # ── Space operations ─────────────────────────────────────────────────────

    def create_space(self, *, config: SpaceConfig | None = None) -> Space:
        body: dict = {}
        if config:
            body["config"] = config.model_dump(by_alias=True, exclude_none=True)
        data = self._post("/spaces", json=body)
        return self._parse(data, Space)

    def get_space(self, space_name: str) -> Space:
        space_name = space_name.removeprefix("spaces/")
        data = self._get(f"/spaces/{space_name}")
        return self._parse(data, Space)

    def update_space(self, space_name: str, **kwargs) -> Space:
        space_name = space_name.removeprefix("spaces/")
        data = self._patch(f"/spaces/{space_name}", json=kwargs)
        return self._parse(data, Space)

    def end_active_conference(self, space_name: str) -> None:
        space_name = space_name.removeprefix("spaces/")
        self._post(f"/spaces/{space_name}:endActiveConference", json={})

    # ── Participant operations ───────────────────────────────────────────────

    def list_participants(self, conference_record: str) -> PageIterator[Participant]:
        def fetch_page(page_token: str | None) -> dict:
            params = {}
            if page_token:
                params["pageToken"] = page_token
            return self._get(f"/conferenceRecords/{conference_record}/participants", params=params)

        return PageIterator(fetch_page, Participant, response_key="participants")

    def get_participant(self, name: str) -> Participant:
        data = self._get(f"/{name}")
        return self._parse(data, Participant)

    def list_participant_sessions(self, participant_name: str) -> PageIterator[ParticipantSession]:
        def fetch_page(page_token: str | None) -> dict:
            params = {}
            if page_token:
                params["pageToken"] = page_token
            return self._get(f"/{participant_name}/participantSessions", params=params)

        return PageIterator(fetch_page, ParticipantSession, response_key="participantSessions")

    # ── Recording operations ─────────────────────────────────────────────────

    def list_recordings(self, conference_record: str) -> PageIterator[Recording]:
        def fetch_page(page_token: str | None) -> dict:
            params = {}
            if page_token:
                params["pageToken"] = page_token
            return self._get(f"/conferenceRecords/{conference_record}/recordings", params=params)

        return PageIterator(fetch_page, Recording, response_key="recordings")

    def get_recording(self, name: str) -> Recording:
        data = self._get(f"/{name}")
        return self._parse(data, Recording)
