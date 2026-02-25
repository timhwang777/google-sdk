"""Google Meet service exports."""

from google_sdk.services import ServiceRegistry
from google_sdk.services.meet.client import MeetService
from google_sdk.services.meet.models import (
    Participant,
    ParticipantSession,
    Recording,
    Space,
    SpaceConfig,
)

ServiceRegistry.register("meet")(MeetService)

__all__ = ["MeetService", "Space", "SpaceConfig", "Participant", "ParticipantSession", "Recording"]
