"""Extended tests for DriveService covering upload, download, export, and move paths."""

from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock, patch

import google.auth.credentials
import httpx
import respx

from google_sdk._config import SDKConfig
from google_sdk.services.drive.client import _API_BASE, _UPLOAD_BASE, DriveService
from google_sdk.services.drive.models import File

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


def make_service():
    return DriveService(make_creds(), SDKConfig())


# ── list_files with optional params ─────────────────────────────────────────


@respx.mock
def test_list_files_with_q():
    route = respx.get(f"{_API_BASE}/files").mock(
        return_value=httpx.Response(200, json={"files": [FILE_DATA]})
    )
    svc = make_service()
    list(svc.list_files(q="name='test.txt'"))
    req = route.calls[0].request
    assert "q=" in str(req.url)


@respx.mock
def test_list_files_with_fields():
    route = respx.get(f"{_API_BASE}/files").mock(
        return_value=httpx.Response(200, json={"files": []})
    )
    svc = make_service()
    list(svc.list_files(fields="files(id,name)"))
    req = route.calls[0].request
    assert "fields=" in str(req.url)


@respx.mock
def test_list_files_with_order_by():
    route = respx.get(f"{_API_BASE}/files").mock(
        return_value=httpx.Response(200, json={"files": []})
    )
    svc = make_service()
    list(svc.list_files(order_by="name"))
    req = route.calls[0].request
    assert "orderBy=name" in str(req.url)


@respx.mock
def test_get_file_with_fields():
    route = respx.get(f"{_API_BASE}/files/file1").mock(
        return_value=httpx.Response(200, json=FILE_DATA)
    )
    svc = make_service()
    svc.get_file("file1", fields="id,name")
    req = route.calls[0].request
    assert "fields=id%2Cname" in str(req.url) or "fields=id,name" in str(req.url)


# ── create_file with simple upload ──────────────────────────────────────────


@respx.mock
def test_create_file_simple_upload_small_bytes():
    """Files < 5MB use simple multipart upload."""
    respx.post(f"{_UPLOAD_BASE}?uploadType=multipart").mock(
        return_value=httpx.Response(200, json=FILE_DATA)
    )
    svc = make_service()
    content = b"small file content"
    f = svc.create_file("test.txt", content=content, mime_type="text/plain")
    assert f.id == "file1"


@respx.mock
def test_create_file_simple_upload_with_file_object():
    """BytesIO under 5MB uses simple upload."""
    respx.post(f"{_UPLOAD_BASE}?uploadType=multipart").mock(
        return_value=httpx.Response(200, json=FILE_DATA)
    )
    svc = make_service()
    content = BytesIO(b"file data")
    f = svc.create_file("test.txt", content=content)
    assert isinstance(f, File)


@respx.mock
def test_create_file_resumable_upload_large_bytes():
    """Files >= 5MB use ResumableUpload."""
    svc = make_service()
    big_content = b"x" * (5 * 1024 * 1024 + 1)  # 5MB + 1 byte

    mock_file = MagicMock(spec=File)
    mock_file.id = "bigfile1"
    with patch("google_sdk.services.drive.client.ResumableUpload") as MockUpload:
        mock_instance = MagicMock()
        mock_instance.execute.return_value = mock_file
        MockUpload.return_value = mock_instance
        f = svc.create_file("big.bin", content=big_content)

    MockUpload.assert_called_once()
    mock_instance.execute.assert_called_once()
    assert f is mock_file


@respx.mock
def test_create_file_forced_resumable():
    """resumable=True forces resumable upload even for small files."""
    svc = make_service()
    small_content = b"tiny"

    mock_file = MagicMock(spec=File)
    with patch("google_sdk.services.drive.client.ResumableUpload") as MockUpload:
        mock_instance = MagicMock()
        mock_instance.execute.return_value = mock_file
        MockUpload.return_value = mock_instance
        svc.create_file("file.txt", content=small_content, resumable=True)

    MockUpload.assert_called_once()


@respx.mock
def test_create_file_forced_simple_upload():
    """resumable=False forces simple upload even for large files."""
    respx.post(f"{_UPLOAD_BASE}?uploadType=multipart").mock(
        return_value=httpx.Response(200, json=FILE_DATA)
    )
    svc = make_service()
    big_content = b"x" * (5 * 1024 * 1024 + 1)
    with patch("google_sdk.services.drive.client.ResumableUpload") as MockUpload:
        svc.create_file("big.bin", content=big_content, resumable=False)
    MockUpload.assert_not_called()


# ── download_file with destination ──────────────────────────────────────────


@respx.mock
def test_download_file_to_path(tmp_path):
    respx.get(f"{_API_BASE}/files/file1").mock(
        return_value=httpx.Response(200, content=b"file data")
    )
    svc = make_service()
    dest = tmp_path / "downloaded.txt"
    result = svc.download_file("file1", destination=dest)
    assert result is None
    assert dest.read_bytes() == b"file data"


@respx.mock
def test_download_file_to_binary_io():
    respx.get(f"{_API_BASE}/files/file1").mock(
        return_value=httpx.Response(200, content=b"file data")
    )
    svc = make_service()
    buf = BytesIO()
    result = svc.download_file("file1", destination=buf)
    assert result is None
    assert buf.getvalue() == b"file data"


# ── export_file ──────────────────────────────────────────────────────────────


@respx.mock
def test_export_file_returns_bytes():
    respx.get(f"{_API_BASE}/files/gdoc1/export").mock(
        return_value=httpx.Response(200, content=b"%PDF-1.4...")
    )
    svc = make_service()
    result = svc.export_file("gdoc1", "application/pdf")
    assert result == b"%PDF-1.4..."


@respx.mock
def test_export_file_to_path(tmp_path):
    respx.get(f"{_API_BASE}/files/gdoc1/export").mock(
        return_value=httpx.Response(200, content=b"pdf content")
    )
    svc = make_service()
    dest = tmp_path / "doc.pdf"
    result = svc.export_file("gdoc1", "application/pdf", destination=dest)
    assert result is None
    assert dest.read_bytes() == b"pdf content"


@respx.mock
def test_export_file_to_binary_io():
    respx.get(f"{_API_BASE}/files/gdoc1/export").mock(
        return_value=httpx.Response(200, content=b"spreadsheet")
    )
    svc = make_service()
    buf = BytesIO()
    result = svc.export_file("gdoc1", "text/csv", destination=buf)
    assert result is None
    assert buf.getvalue() == b"spreadsheet"


# ── move_file ────────────────────────────────────────────────────────────────


@respx.mock
def test_move_file():
    respx.patch(f"{_API_BASE}/files/file1").mock(
        return_value=httpx.Response(200, json={**FILE_DATA, "parents": ["folder2"]})
    )
    svc = make_service()
    f = svc.move_file("file1", new_parent="folder2")
    assert isinstance(f, File)


@respx.mock
def test_move_file_with_remove_parents():
    route = respx.patch(f"{_API_BASE}/files/file1").mock(
        return_value=httpx.Response(200, json=FILE_DATA)
    )
    svc = make_service()
    svc.move_file("file1", new_parent="folder2", remove_parents=["folder1"])
    req = route.calls[0].request
    assert "removeParents" in str(req.url)


# ── copy_file with parents ───────────────────────────────────────────────────


@respx.mock
def test_copy_file_with_parents():
    respx.post(f"{_API_BASE}/files/file1/copy").mock(
        return_value=httpx.Response(200, json={**FILE_DATA, "id": "copy2"})
    )
    svc = make_service()
    f = svc.copy_file("file1", parents=["folder1"])
    assert f.id == "copy2"
