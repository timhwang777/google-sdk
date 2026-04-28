"""Tests for ResumableUpload handler."""

from __future__ import annotations

from io import BytesIO
from unittest.mock import patch

import httpx
import respx

from google_sdk.services.drive.models import File, UploadProgress
from google_sdk.services.drive.uploads import CHUNK_SIZE, RESUMABLE_THRESHOLD, ResumableUpload

SESSION_URI = (
    "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&upload_id=abc123"
)
INITIATE_URL = "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable"

FILE_DATA = {
    "id": "file1",
    "name": "test.txt",
    "mimeType": "text/plain",
    "kind": "drive#file",
}

AUTH_HEADERS = {"Authorization": "Bearer fake_token"}


def make_upload(content: bytes | BytesIO = b"hello world", **kwargs) -> ResumableUpload:
    return ResumableUpload(
        url=INITIATE_URL,
        headers=AUTH_HEADERS,
        name="test.txt",
        content=content,
        mime_type="text/plain",
        metadata={"name": "test.txt"},
        **kwargs,
    )


# ── Threshold constants ──────────────────────────────────────────────────────


def test_resumable_threshold_is_5mb():
    assert RESUMABLE_THRESHOLD == 5 * 1024 * 1024


def test_chunk_size_is_8mib():
    assert CHUNK_SIZE == 8 * 1024 * 1024


# ── ResumableUpload.__init__ ─────────────────────────────────────────────────


def test_init_with_bytes():
    content = b"hello"
    upload = make_upload(content=content)
    assert upload._total_bytes == 5


def test_init_with_file_object():
    content = BytesIO(b"hello world")
    upload = make_upload(content=content)
    assert upload._total_bytes == 11


# ── Session initiation ───────────────────────────────────────────────────────


@respx.mock
def test_initiate_session_returns_location_header():
    respx.post(INITIATE_URL).mock(
        return_value=httpx.Response(200, headers={"Location": SESSION_URI})
    )
    upload = make_upload(content=b"hello")
    uri = upload._initiate_session()
    assert uri == SESSION_URI


@respx.mock
def test_initiate_session_sends_auth_header():
    route = respx.post(INITIATE_URL).mock(
        return_value=httpx.Response(200, headers={"Location": SESSION_URI})
    )
    upload = make_upload(content=b"hello")
    upload._initiate_session()
    assert route.called
    req = route.calls[0].request
    assert req.headers["Authorization"] == "Bearer fake_token"


@respx.mock
def test_initiate_session_appends_fields_param():
    fields = "id,name,webViewLink,webContentLink"
    route = respx.post(
        f"{INITIATE_URL}&fields={fields}",
    ).mock(return_value=httpx.Response(200, headers={"Location": SESSION_URI}))
    upload = make_upload(content=b"hello", fields=fields)
    uri = upload._initiate_session()
    assert uri == SESSION_URI
    assert route.called


@respx.mock
def test_initiate_session_no_fields_keeps_url_unchanged():
    route = respx.post(INITIATE_URL).mock(
        return_value=httpx.Response(200, headers={"Location": SESSION_URI})
    )
    upload = make_upload(content=b"hello")
    upload._initiate_session()
    assert route.called
    assert b"fields=" not in route.calls.last.request.url.query


# ── execute() — single chunk upload ─────────────────────────────────────────


@respx.mock
def test_execute_single_chunk_returns_file():
    respx.post(INITIATE_URL).mock(
        return_value=httpx.Response(200, headers={"Location": SESSION_URI})
    )
    respx.put(SESSION_URI).mock(return_value=httpx.Response(200, json=FILE_DATA))

    upload = make_upload(content=b"small content")
    result = upload.execute()
    assert isinstance(result, File)
    assert result.id == "file1"


@respx.mock
def test_execute_sends_correct_content_range():
    content = b"hello world"
    respx.post(INITIATE_URL).mock(
        return_value=httpx.Response(200, headers={"Location": SESSION_URI})
    )
    route = respx.put(SESSION_URI).mock(return_value=httpx.Response(200, json=FILE_DATA))

    upload = make_upload(content=content)
    upload.execute()

    req = route.calls[0].request
    assert req.headers["Content-Range"] == f"bytes 0-{len(content) - 1}/{len(content)}"


@respx.mock
def test_execute_handles_201_response():
    respx.post(INITIATE_URL).mock(
        return_value=httpx.Response(200, headers={"Location": SESSION_URI})
    )
    respx.put(SESSION_URI).mock(return_value=httpx.Response(201, json=FILE_DATA))

    upload = make_upload(content=b"data")
    result = upload.execute()
    assert result.id == "file1"


# ── execute() — 308 resume handling ─────────────────────────────────────────


@respx.mock
def test_execute_handles_308_resume_incomplete():
    """308 means chunk received, continue uploading next chunk."""
    content = b"chunk1" + b"chunk2"
    respx.post(INITIATE_URL).mock(
        return_value=httpx.Response(200, headers={"Location": SESSION_URI})
    )
    respx.put(SESSION_URI).mock(
        side_effect=[
            httpx.Response(308, headers={"Range": "bytes=0-5"}),
            httpx.Response(200, json=FILE_DATA),
        ]
    )

    # Force 2 chunks by patching CHUNK_SIZE
    with patch("google_sdk.services.drive.uploads.CHUNK_SIZE", 6):
        upload = make_upload(content=content)
        result = upload.execute()

    assert result.id == "file1"


@respx.mock
def test_execute_308_without_range_header():
    """308 without Range header assumes all bytes_sent + chunk were received."""
    content = b"hello"
    respx.post(INITIATE_URL).mock(
        return_value=httpx.Response(200, headers={"Location": SESSION_URI})
    )
    respx.put(SESSION_URI).mock(
        side_effect=[
            httpx.Response(308),  # No Range header
            httpx.Response(200, json=FILE_DATA),
        ]
    )
    with patch("google_sdk.services.drive.uploads.CHUNK_SIZE", 3):
        upload = make_upload(content=content)
        result = upload.execute()

    assert result.id == "file1"


# ── Progress callback ────────────────────────────────────────────────────────


@respx.mock
def test_execute_calls_progress_callback():
    content = b"hello world"
    progress_calls: list[UploadProgress] = []

    respx.post(INITIATE_URL).mock(
        return_value=httpx.Response(200, headers={"Location": SESSION_URI})
    )
    respx.put(SESSION_URI).mock(return_value=httpx.Response(200, json=FILE_DATA))

    upload = make_upload(content=content, on_progress=progress_calls.append)
    upload.execute()

    assert len(progress_calls) >= 1
    last = progress_calls[-1]
    assert isinstance(last, UploadProgress)
    assert last.total_bytes == len(content)
