"""Tests for sync/async client parity (US5)."""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock

import google.auth.credentials
import httpx
import pytest
import respx

from google_sdk import AsyncGoogleClient, GoogleClient
from google_sdk._config import SDKConfig
from google_sdk._pagination import AsyncPageIterator, PageIterator
from google_sdk.services.drive.client import _API_BASE as DRIVE_API_BASE

FILE_DATA = {
    "id": "file1",
    "name": "test.txt",
    "mimeType": "text/plain",
    "kind": "drive#file",
}


def make_creds():
    creds = MagicMock(spec=google.auth.credentials.Credentials)
    creds.valid = True
    creds.token = "fake_token"
    return creds


# ── Context manager protocols ────────────────────────────────────────────────


def test_sync_client_context_manager():
    creds = make_creds()
    with GoogleClient(creds) as client:
        assert client._closed is False
    assert client._closed is True


@pytest.mark.asyncio
async def test_async_client_context_manager():
    creds = make_creds()
    async with AsyncGoogleClient(creds) as client:
        assert client._closed is False
    assert client._closed is True


# ── PageIterator sync __iter__ / __next__ ────────────────────────────────────


def test_page_iterator_supports_iteration():
    pages_data = [{"files": [FILE_DATA]}]

    def fetch_page(token):
        return pages_data.pop(0) if pages_data else {"files": []}

    from google_sdk.services.drive.models import File

    pi = PageIterator(fetch_page, File, response_key="files")
    assert hasattr(pi, "__iter__")
    assert hasattr(pi, "__next__")

    files = list(pi)
    assert len(files) == 1
    assert files[0].id == "file1"


def test_page_iterator_next_protocol():
    from google_sdk.services.drive.models import File

    def fetch_page(token):
        if token is None:
            return {"files": [FILE_DATA], "nextPageToken": None}
        return {"files": []}

    pi = PageIterator(fetch_page, File, response_key="files")
    first = next(pi)
    assert first.id == "file1"
    with pytest.raises(StopIteration):
        next(pi)


# ── AsyncPageIterator supports async iteration ───────────────────────────────


@pytest.mark.asyncio
async def test_async_page_iterator_supports_async_iteration():
    from google_sdk.services.drive.models import File

    async def fetch_page(token):
        return {"files": [FILE_DATA]}

    api = AsyncPageIterator(fetch_page, File, response_key="files")
    assert hasattr(api, "__aiter__")

    files = [f async for f in api]
    assert len(files) == 1
    assert files[0].id == "file1"


# ── Sync and async Drive list_files return equivalent results ────────────────


@respx.mock
def test_sync_drive_list_files():
    respx.get(f"{DRIVE_API_BASE}/files").mock(
        return_value=httpx.Response(200, json={"files": [FILE_DATA]})
    )
    creds = make_creds()
    client = GoogleClient(creds, config=SDKConfig())
    files = list(client.drive.list_files())
    assert len(files) == 1
    assert files[0].id == "file1"
    assert files[0].name == "test.txt"


@respx.mock
@pytest.mark.asyncio
async def test_async_drive_list_files():
    respx.get(f"{DRIVE_API_BASE}/files").mock(
        return_value=httpx.Response(200, json={"files": [FILE_DATA]})
    )
    creds = make_creds()
    # AsyncGoogleClient uses same underlying DriveService (sync for now)
    client = AsyncGoogleClient(creds, config=SDKConfig())
    files = list(client.drive.list_files())
    assert len(files) == 1
    assert files[0].id == "file1"
    assert files[0].name == "test.txt"


# ── Client interface parity ──────────────────────────────────────────────────


def test_both_clients_expose_drive_service():
    creds = make_creds()
    sync_client = GoogleClient(creds)
    async_client = AsyncGoogleClient(creds)
    assert hasattr(sync_client, "drive")
    assert hasattr(async_client, "drive")


def test_both_clients_expose_calendar_service():
    creds = make_creds()
    sync_client = GoogleClient(creds)
    async_client = AsyncGoogleClient(creds)
    assert hasattr(sync_client, "calendar")
    assert hasattr(async_client, "calendar")


def test_both_clients_expose_meet_service():
    creds = make_creds()
    sync_client = GoogleClient(creds)
    async_client = AsyncGoogleClient(creds)
    assert hasattr(sync_client, "meet")
    assert hasattr(async_client, "meet")


def test_sync_client_has_enter_exit():
    creds = make_creds()
    client = GoogleClient(creds)
    assert hasattr(client, "__enter__")
    assert hasattr(client, "__exit__")
    assert not inspect.iscoroutinefunction(client.__enter__)


def test_async_client_has_aenter_aexit():
    creds = make_creds()
    client = AsyncGoogleClient(creds)
    assert hasattr(client, "__aenter__")
    assert hasattr(client, "__aexit__")
    assert inspect.iscoroutinefunction(client.__aenter__)
    assert inspect.iscoroutinefunction(client.__aexit__)
