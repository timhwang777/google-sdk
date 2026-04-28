"""Tests for Google Drive data models."""

from google_sdk.services.drive.models import File, Folder, Permission, UploadProgress


def test_file_defaults():
    f = File()
    assert f.name == ""
    assert f.trashed is False
    assert f.size is None


def test_file_alias_mapping():
    data = {
        "id": "file1",
        "name": "test.pdf",
        "mimeType": "application/pdf",
        "createdTime": "2026-01-01T00:00:00Z",
        "modifiedTime": "2026-01-02T00:00:00Z",
        "webViewLink": "https://drive.google.com/file/d/file1/view",
        "webContentLink": "https://drive.google.com/uc?id=file1&export=download",
    }
    f = File.model_validate(data)
    assert f.id == "file1"
    assert f.mime_type == "application/pdf"
    assert f.created_time is not None
    assert f.web_view_link == "https://drive.google.com/file/d/file1/view"
    assert f.web_content_link == "https://drive.google.com/uc?id=file1&export=download"


def test_file_web_content_link_default_none():
    f = File.model_validate({"id": "x", "name": "x"})
    assert f.web_content_link is None


def test_file_extra_field_acceptance():
    data = {"id": "1", "newField": "value"}
    f = File.model_validate(data)
    assert f.id == "1"


def test_folder_default_mime_type():
    folder = Folder(id="f1", name="My Folder")
    assert folder.mime_type == "application/vnd.google-apps.folder"


def test_folder_inherits_file():
    assert issubclass(Folder, File)


def test_permission_alias_mapping():
    data = {
        "id": "p1",
        "type": "user",
        "role": "writer",
        "emailAddress": "user@example.com",
        "displayName": "Test User",
    }
    p = Permission.model_validate(data)
    assert p.email_address == "user@example.com"
    assert p.display_name == "Test User"


def test_upload_progress():
    up = UploadProgress(bytes_sent=500, total_bytes=1000)
    assert up.bytes_sent == 500
    assert up.total_bytes == 1000
    assert up.percentage == 50.0


def test_upload_progress_zero_total():
    up = UploadProgress(bytes_sent=0, total_bytes=0)
    assert up.percentage == 0.0
