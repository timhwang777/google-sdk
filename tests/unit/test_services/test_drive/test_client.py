"""Tests for DriveService using respx mock."""

from unittest.mock import MagicMock

import google.auth.credentials
import httpx
import respx

from google_sdk._config import SDKConfig
from google_sdk.services.drive.client import _API_BASE, DriveService
from google_sdk.services.drive.models import File, Folder


def make_creds():
    creds = MagicMock(spec=google.auth.credentials.Credentials)
    creds.valid = True
    creds.token = "fake_token"
    return creds


def make_service():
    return DriveService(make_creds(), SDKConfig())


FILE_DATA = {
    "id": "file1",
    "name": "test.txt",
    "mimeType": "text/plain",
    "kind": "drive#file",
}

FILE_LIST_DATA = {
    "files": [FILE_DATA],
    "nextPageToken": None,
}

PERMISSION_DATA = {
    "id": "perm1",
    "type": "user",
    "role": "writer",
    "emailAddress": "user@example.com",
}


@respx.mock
def test_list_files():
    respx.get(f"{_API_BASE}/files").mock(
        return_value=httpx.Response(200, json={"files": [FILE_DATA]})
    )
    svc = make_service()
    files = list(svc.list_files())
    assert len(files) == 1
    assert files[0].id == "file1"
    assert isinstance(files[0], File)


@respx.mock
def test_list_files_pagination():
    page1 = {"files": [{"id": "f1", "name": "a.txt"}], "nextPageToken": "tok1"}
    page2 = {"files": [{"id": "f2", "name": "b.txt"}]}
    respx.get(f"{_API_BASE}/files").mock(
        side_effect=[
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
        ]
    )
    svc = make_service()
    files = list(svc.list_files())
    assert len(files) == 2


@respx.mock
def test_get_file():
    respx.get(f"{_API_BASE}/files/file1").mock(return_value=httpx.Response(200, json=FILE_DATA))
    svc = make_service()
    f = svc.get_file("file1")
    assert f.id == "file1"
    assert f.name == "test.txt"


@respx.mock
def test_create_file_metadata_only():
    respx.post(f"{_API_BASE}/files").mock(return_value=httpx.Response(200, json=FILE_DATA))
    svc = make_service()
    f = svc.create_file("test.txt")
    assert f.id == "file1"


@respx.mock
def test_update_file():
    updated = {**FILE_DATA, "name": "updated.txt"}
    respx.patch(f"{_API_BASE}/files/file1").mock(return_value=httpx.Response(200, json=updated))
    svc = make_service()
    f = svc.update_file("file1", name="updated.txt")
    assert f.name == "updated.txt"


@respx.mock
def test_delete_file():
    respx.delete(f"{_API_BASE}/files/file1").mock(return_value=httpx.Response(204, content=b""))
    svc = make_service()
    svc.delete_file("file1")  # Should not raise


@respx.mock
def test_download_file():
    respx.get(f"{_API_BASE}/files/file1").mock(
        return_value=httpx.Response(200, content=b"file content")
    )
    svc = make_service()
    content = svc.download_file("file1")
    assert content == b"file content"


@respx.mock
def test_copy_file():
    respx.post(f"{_API_BASE}/files/file1/copy").mock(
        return_value=httpx.Response(200, json={**FILE_DATA, "id": "copy1"})
    )
    svc = make_service()
    f = svc.copy_file("file1", name="copy.txt")
    assert f.id == "copy1"


@respx.mock
def test_create_folder():
    folder_data = {**FILE_DATA, "mimeType": "application/vnd.google-apps.folder"}
    respx.post(f"{_API_BASE}/files").mock(return_value=httpx.Response(200, json=folder_data))
    svc = make_service()
    folder = svc.create_folder("My Folder")
    assert isinstance(folder, Folder)


@respx.mock
def test_list_permissions():
    respx.get(f"{_API_BASE}/files/file1/permissions").mock(
        return_value=httpx.Response(200, json={"permissions": [PERMISSION_DATA]})
    )
    svc = make_service()
    perms = svc.list_permissions("file1")
    assert len(perms) == 1
    assert perms[0].id == "perm1"


@respx.mock
def test_create_permission():
    respx.post(f"{_API_BASE}/files/file1/permissions").mock(
        return_value=httpx.Response(200, json=PERMISSION_DATA)
    )
    svc = make_service()
    perm = svc.create_permission("file1", role="writer", type="user", email_address="u@e.com")
    assert perm.id == "perm1"


@respx.mock
def test_delete_permission():
    respx.delete(f"{_API_BASE}/files/file1/permissions/perm1").mock(
        return_value=httpx.Response(204, content=b"")
    )
    svc = make_service()
    svc.delete_permission("file1", "perm1")  # Should not raise


# ── Folder lookup helpers ────────────────────────────────────────────────────

FOLDER_DATA = {
    "id": "fold1",
    "name": "MyFolder",
    "mimeType": "application/vnd.google-apps.folder",
    "parents": ["root"],
}


@respx.mock
def test_find_folder_returns_match():
    route = respx.get(f"{_API_BASE}/files").mock(
        return_value=httpx.Response(200, json={"files": [FOLDER_DATA]})
    )
    svc = make_service()
    folder = svc.find_folder("MyFolder")
    assert isinstance(folder, Folder)
    assert folder.id == "fold1"
    q = route.calls.last.request.url.params["q"]
    assert "name = 'MyFolder'" in q
    assert "mimeType = 'application/vnd.google-apps.folder'" in q
    assert "trashed = false" in q
    assert "in parents" not in q


@respx.mock
def test_find_folder_returns_none_when_missing():
    respx.get(f"{_API_BASE}/files").mock(
        return_value=httpx.Response(200, json={"files": []})
    )
    svc = make_service()
    assert svc.find_folder("Nope") is None


@respx.mock
def test_find_folder_filters_by_parent():
    route = respx.get(f"{_API_BASE}/files").mock(
        return_value=httpx.Response(200, json={"files": [FOLDER_DATA]})
    )
    svc = make_service()
    svc.find_folder("MyFolder", parent_id="parent123")
    q = route.calls.last.request.url.params["q"]
    assert "'parent123' in parents" in q


@respx.mock
def test_find_folder_escapes_single_quotes_in_name():
    route = respx.get(f"{_API_BASE}/files").mock(
        return_value=httpx.Response(200, json={"files": []})
    )
    svc = make_service()
    svc.find_folder("a'b")
    q = route.calls.last.request.url.params["q"]
    assert "name = 'a\\'b'" in q


@respx.mock
def test_get_or_create_folder_returns_existing():
    """When a folder already exists, no POST is issued."""
    list_route = respx.get(f"{_API_BASE}/files").mock(
        return_value=httpx.Response(200, json={"files": [FOLDER_DATA]})
    )
    create_route = respx.post(f"{_API_BASE}/files").mock(
        return_value=httpx.Response(200, json=FOLDER_DATA)
    )
    svc = make_service()
    folder = svc.get_or_create_folder("MyFolder")
    assert folder.id == "fold1"
    assert list_route.called
    assert not create_route.called


@respx.mock
def test_get_or_create_folder_creates_when_missing():
    respx.get(f"{_API_BASE}/files").mock(
        return_value=httpx.Response(200, json={"files": []})
    )
    create_route = respx.post(f"{_API_BASE}/files").mock(
        return_value=httpx.Response(200, json=FOLDER_DATA)
    )
    svc = make_service()
    folder = svc.get_or_create_folder("MyFolder", parent_id="parent123")
    assert isinstance(folder, Folder)
    assert folder.id == "fold1"
    assert create_route.called
    body = create_route.calls.last.request.read()
    assert b'"parents":["parent123"]' in body
