"""Base Pydantic models for Google API resources."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseResource(BaseModel):
    """Base class for all Google API resource models.

    Accepts extra fields (Google APIs add fields over time),
    supports both snake_case and camelCase field names.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str = ""
    kind: str | None = None


class PageResponse(BaseModel, Generic[T]):
    """Generic wrapper for paginated Google API responses."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    items: list[T] = Field(default_factory=list)
    next_page_token: str | None = Field(None, alias="nextPageToken")
