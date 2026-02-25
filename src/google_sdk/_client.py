"""Google SDK client implementations (sync and async)."""

from __future__ import annotations

import threading
from functools import cached_property
from typing import Any, Self

import google.auth.credentials

from google_sdk._config import SDKConfig
from google_sdk.auth.token_store import TokenStore


class GoogleClient:
    """Synchronous Google API client.

    Example::

        from google_sdk import GoogleClient
        from google_sdk.auth import service_account

        creds = service_account("key.json")
        with GoogleClient(creds) as client:
            files = list(client.drive.list_files())
    """

    def __init__(
        self,
        credentials: google.auth.credentials.Credentials,
        *,
        token_store: TokenStore | None = None,
        config: SDKConfig | None = None,
    ) -> None:
        self._credentials = credentials
        self._token_store = token_store
        self._config = config or SDKConfig()
        self._lock = threading.Lock()
        self._closed = False

    @cached_property
    def drive(self):
        """Access the Drive service."""
        from google_sdk.services.drive.client import DriveService

        return DriveService(self._credentials, self._config)

    @cached_property
    def calendar(self):
        """Access the Calendar service."""
        from google_sdk.services.calendar.client import CalendarService

        return CalendarService(self._credentials, self._config)

    @cached_property
    def meet(self):
        """Access the Meet service."""
        from google_sdk.services.meet.client import MeetService

        return MeetService(self._credentials, self._config)

    def close(self) -> None:
        """Release resources."""
        with self._lock:
            self._closed = True

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncGoogleClient:
    """Asynchronous Google API client.

    Example::

        from google_sdk import AsyncGoogleClient
        from google_sdk.auth import service_account

        creds = service_account("key.json")
        async with AsyncGoogleClient(creds) as client:
            async for file in client.drive.list_files():
                print(file.name)
    """

    def __init__(
        self,
        credentials: google.auth.credentials.Credentials,
        *,
        token_store: TokenStore | None = None,
        config: SDKConfig | None = None,
    ) -> None:
        self._credentials = credentials
        self._token_store = token_store
        self._config = config or SDKConfig()
        self._closed = False

    @cached_property
    def drive(self):
        """Access the Drive service."""
        from google_sdk.services.drive.client import DriveService

        return DriveService(self._credentials, self._config)

    @cached_property
    def calendar(self):
        """Access the Calendar service."""
        from google_sdk.services.calendar.client import CalendarService

        return CalendarService(self._credentials, self._config)

    @cached_property
    def meet(self):
        """Access the Meet service."""
        from google_sdk.services.meet.client import MeetService

        return MeetService(self._credentials, self._config)

    async def close(self) -> None:
        """Release resources."""
        self._closed = True

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
