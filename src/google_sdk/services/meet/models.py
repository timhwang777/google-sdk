"""Google Meet data models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from google_sdk._models.base import BaseResource


class SpaceConfig(BaseModel):
    """Configuration for a Meet space."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    access_type: str = Field("OPEN", alias="accessType")
    entry_point_access: str = Field("ALL", alias="entryPointAccess")


class Space(BaseResource):
    """Represents a Google Meet space."""

    name: str = ""
    meeting_uri: str | None = Field(None, alias="meetingUri")
    meeting_code: str | None = Field(None, alias="meetingCode")
    config: SpaceConfig | None = None


class SignInUser(BaseModel):
    """Represents a signed-in Meet participant."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    user: str | None = None
    display_name: str | None = Field(None, alias="displayName")


class AnonymousUser(BaseModel):
    """Represents an anonymous Meet participant."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    display_name: str | None = Field(None, alias="displayName")


class PhoneUser(BaseModel):
    """Represents a phone dial-in Meet participant."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    display_name: str | None = Field(None, alias="displayName")


class Participant(BaseResource):
    """Represents a Meet conference participant."""

    earliest_start_time: datetime | None = Field(None, alias="earliestStartTime")
    latest_end_time: datetime | None = Field(None, alias="latestEndTime")
    signin_user: SignInUser | None = Field(None, alias="signedinUser")
    anonymous_user: AnonymousUser | None = Field(None, alias="anonymousUser")
    phone_user: PhoneUser | None = Field(None, alias="phoneUser")


class ParticipantSession(BaseResource):
    """Represents a single session of a Meet participant."""

    start_time: datetime | None = Field(None, alias="startTime")
    end_time: datetime | None = Field(None, alias="endTime")


class DriveDestination(BaseModel):
    """Represents a Drive location for a recording."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    file: str | None = None
    export_uri: str | None = Field(None, alias="exportUri")


class Recording(BaseResource):
    """Represents a Meet conference recording."""

    state: str | None = None  # STARTED|ENDED
    start_time: datetime | None = Field(None, alias="startTime")
    end_time: datetime | None = Field(None, alias="endTime")
    drive_destination: DriveDestination | None = Field(None, alias="driveDestination")
