"""Google Drive data models."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from google_sdk._models.base import BaseResource


class File(BaseResource):
    """Represents a Google Drive file."""

    name: str = ""
    mime_type: str = Field("", alias="mimeType")
    size: int | None = None
    created_time: datetime | None = Field(None, alias="createdTime")
    modified_time: datetime | None = Field(None, alias="modifiedTime")
    parents: list[str] | None = None
    web_view_link: str | None = Field(None, alias="webViewLink")
    trashed: bool = False


class Folder(File):
    """Represents a Google Drive folder."""

    mime_type: str = Field("application/vnd.google-apps.folder", alias="mimeType")


class Permission(BaseResource):
    """Represents a Drive file permission."""

    type: str = ""  # user|group|domain|anyone
    role: str = ""  # owner|organizer|writer|commenter|reader
    email_address: str | None = Field(None, alias="emailAddress")
    domain: str | None = None
    display_name: str | None = Field(None, alias="displayName")


class UploadProgress:
    """Progress information for resumable uploads."""

    def __init__(self, bytes_sent: int, total_bytes: int) -> None:
        self.bytes_sent = bytes_sent
        self.total_bytes = total_bytes
        self.percentage = (bytes_sent / total_bytes * 100) if total_bytes > 0 else 0.0
