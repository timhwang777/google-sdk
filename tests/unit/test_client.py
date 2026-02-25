"""Tests for GoogleClient and AsyncGoogleClient."""

from unittest.mock import MagicMock

import google.auth.credentials
import pytest

from google_sdk import AsyncGoogleClient, GoogleClient, SDKConfig


def make_creds():
    creds = MagicMock(spec=google.auth.credentials.Credentials)
    creds.valid = True
    creds.token = "fake_token"
    return creds


# ── GoogleClient ─────────────────────────────────────────────────────────────


def test_google_client_init():
    creds = make_creds()
    client = GoogleClient(creds)
    assert client._credentials is creds
    assert client._config is not None


def test_google_client_context_manager():
    creds = make_creds()
    with GoogleClient(creds) as client:
        assert isinstance(client, GoogleClient)


def test_google_client_close():
    creds = make_creds()
    client = GoogleClient(creds)
    client.close()
    assert client._closed is True


def test_google_client_drive_cached_property():
    creds = make_creds()
    client = GoogleClient(creds)
    drive1 = client.drive
    drive2 = client.drive
    assert drive1 is drive2  # cached_property


def test_google_client_calendar_cached_property():
    creds = make_creds()
    client = GoogleClient(creds)
    cal1 = client.calendar
    cal2 = client.calendar
    assert cal1 is cal2


def test_google_client_meet_cached_property():
    creds = make_creds()
    client = GoogleClient(creds)
    meet1 = client.meet
    meet2 = client.meet
    assert meet1 is meet2


def test_google_client_with_config():
    creds = make_creds()
    config = SDKConfig(timeout=10.0)
    client = GoogleClient(creds, config=config)
    assert client._config.timeout == 10.0


# ── AsyncGoogleClient ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_async_google_client_context_manager():
    creds = make_creds()
    async with AsyncGoogleClient(creds) as client:
        assert isinstance(client, AsyncGoogleClient)


@pytest.mark.asyncio
async def test_async_google_client_close():
    creds = make_creds()
    client = AsyncGoogleClient(creds)
    await client.close()
    assert client._closed is True


def test_async_google_client_drive_cached_property():
    creds = make_creds()
    client = AsyncGoogleClient(creds)
    drive1 = client.drive
    drive2 = client.drive
    assert drive1 is drive2
