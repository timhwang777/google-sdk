"""Integration tests for DriveService against live Google Drive API."""

from __future__ import annotations

import io
import itertools

import pytest

from google_sdk.exceptions import NotFoundError
from google_sdk.services.drive.models import File, Permission

# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


def test_list_files(client):
    """list_files returns an iterable of File objects."""
    files = list(itertools.islice(client.drive.list_files(page_size=5), 5))
    # The account may have zero files, but iteration itself should work.
    for f in files:
        assert isinstance(f, File)


# ---------------------------------------------------------------------------
# Create / Get
# ---------------------------------------------------------------------------


def test_create_and_get_file(client, test_prefix, drive_cleanup):
    """Create a plain text file, then retrieve it by ID."""
    name = f"{test_prefix}_hello.txt"
    created = client.drive.create_file(name, content=b"hello world", mime_type="text/plain")
    drive_cleanup.append(created.id)

    assert created.id
    assert created.name == name

    fetched = client.drive.get_file(created.id)
    assert fetched.id == created.id
    assert fetched.name == name


# ---------------------------------------------------------------------------
# Upload / Download
# ---------------------------------------------------------------------------


def test_upload_and_download(client, test_prefix, drive_cleanup):
    """Upload content and download it back — bytes should round-trip."""
    payload = b"integration test payload 1234567890"
    name = f"{test_prefix}_roundtrip.txt"

    created = client.drive.create_file(name, content=payload, mime_type="text/plain")
    drive_cleanup.append(created.id)

    downloaded = client.drive.download_file(created.id)
    assert downloaded == payload


def test_upload_binary_io(client, test_prefix, drive_cleanup):
    """Upload from a BinaryIO stream."""
    payload = b"stream upload test"
    name = f"{test_prefix}_stream.txt"

    created = client.drive.create_file(name, content=io.BytesIO(payload), mime_type="text/plain")
    drive_cleanup.append(created.id)

    downloaded = client.drive.download_file(created.id)
    assert downloaded == payload


# ---------------------------------------------------------------------------
# Folder
# ---------------------------------------------------------------------------


def test_create_folder(client, test_prefix, drive_cleanup):
    """Create a folder and verify its MIME type."""
    name = f"{test_prefix}_folder"
    folder = client.drive.create_folder(name)
    drive_cleanup.append(folder.id)

    assert folder.id
    assert folder.mime_type == "application/vnd.google-apps.folder"


# ---------------------------------------------------------------------------
# Copy
# ---------------------------------------------------------------------------


def test_copy_file(client, test_prefix, drive_cleanup):
    """Copy a file and verify the copy exists with the new name."""
    original = client.drive.create_file(
        f"{test_prefix}_original.txt", content=b"copy me", mime_type="text/plain"
    )
    drive_cleanup.append(original.id)

    copy_name = f"{test_prefix}_copied.txt"
    copied = client.drive.copy_file(original.id, name=copy_name)
    drive_cleanup.append(copied.id)

    assert copied.id != original.id
    assert copied.name == copy_name


# ---------------------------------------------------------------------------
# Move
# ---------------------------------------------------------------------------


def test_move_file(client, test_prefix, drive_cleanup):
    """Move a file into a new folder."""
    folder = client.drive.create_folder(f"{test_prefix}_move_dest")
    drive_cleanup.append(folder.id)

    f = client.drive.create_file(
        f"{test_prefix}_movable.txt", content=b"move me", mime_type="text/plain"
    )
    drive_cleanup.append(f.id)

    moved = client.drive.move_file(f.id, new_parent=folder.id)
    assert folder.id in (moved.parents or [])


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def test_update_file(client, test_prefix, drive_cleanup):
    """Rename a file via update_file."""
    original_name = f"{test_prefix}_before.txt"
    new_name = f"{test_prefix}_after.txt"

    f = client.drive.create_file(original_name, content=b"update me", mime_type="text/plain")
    drive_cleanup.append(f.id)

    updated = client.drive.update_file(f.id, name=new_name)
    assert updated.name == new_name


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_file(client, test_prefix):
    """Delete a file and verify it's gone (NotFoundError on get)."""
    f = client.drive.create_file(
        f"{test_prefix}_delete_me.txt", content=b"bye", mime_type="text/plain"
    )

    client.drive.delete_file(f.id)

    with pytest.raises(NotFoundError):
        client.drive.get_file(f.id)


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------


def test_list_permissions(client, test_prefix, drive_cleanup):
    """List permissions on a newly created file — should have at least the owner."""
    f = client.drive.create_file(
        f"{test_prefix}_perms.txt", content=b"perms", mime_type="text/plain"
    )
    drive_cleanup.append(f.id)

    perms = client.drive.list_permissions(f.id)
    assert isinstance(perms, list)
    assert len(perms) >= 1
    assert all(isinstance(p, Permission) for p in perms)


def test_create_and_delete_permission(client, test_prefix, drive_cleanup):
    """Grant 'anyone with the link' reader permission, then revoke it."""
    f = client.drive.create_file(
        f"{test_prefix}_share.txt", content=b"share me", mime_type="text/plain"
    )
    drive_cleanup.append(f.id)

    perm = client.drive.create_permission(f.id, role="reader", type="anyone")
    assert perm.id
    assert perm.role == "reader"

    client.drive.delete_permission(f.id, perm.id)

    # Verify only owner permission remains
    remaining = client.drive.list_permissions(f.id)
    assert all(p.id != perm.id for p in remaining)


# ---------------------------------------------------------------------------
# Export (Google Docs → PDF)
# ---------------------------------------------------------------------------


def test_export_file(client, test_prefix, drive_cleanup):
    """Create a Google Doc and export it as PDF."""
    doc = client.drive.create_file(
        f"{test_prefix}_exportable",
        mime_type="application/vnd.google-apps.document",
    )
    drive_cleanup.append(doc.id)

    pdf_bytes = client.drive.export_file(doc.id, "application/pdf")
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    # PDF files start with %PDF
    assert pdf_bytes[:5] == b"%PDF-"
