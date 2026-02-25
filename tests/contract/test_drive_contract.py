"""Contract tests for DriveService public API."""

import inspect

from google_sdk.services.drive.client import DriveService


def test_list_files_signature():
    sig = inspect.signature(DriveService.list_files)
    params = sig.parameters
    assert "q" in params
    assert "page_size" in params
    assert "fields" in params
    assert "order_by" in params


def test_get_file_signature():
    sig = inspect.signature(DriveService.get_file)
    params = sig.parameters
    assert "file_id" in params


def test_create_file_signature():
    sig = inspect.signature(DriveService.create_file)
    params = sig.parameters
    assert "name" in params
    assert "content" in params
    assert "mime_type" in params
    assert "parents" in params
    assert "resumable" in params
    assert "on_progress" in params


def test_update_file_signature():
    sig = inspect.signature(DriveService.update_file)
    assert "file_id" in sig.parameters


def test_delete_file_signature():
    sig = inspect.signature(DriveService.delete_file)
    assert "file_id" in sig.parameters


def test_download_file_signature():
    sig = inspect.signature(DriveService.download_file)
    params = sig.parameters
    assert "file_id" in params
    assert "destination" in params


def test_export_file_signature():
    sig = inspect.signature(DriveService.export_file)
    params = sig.parameters
    assert "file_id" in params
    assert "mime_type" in params


def test_copy_file_signature():
    sig = inspect.signature(DriveService.copy_file)
    assert "file_id" in sig.parameters


def test_move_file_signature():
    sig = inspect.signature(DriveService.move_file)
    params = sig.parameters
    assert "file_id" in params
    assert "new_parent" in params


def test_create_folder_signature():
    sig = inspect.signature(DriveService.create_folder)
    assert "name" in sig.parameters


def test_list_permissions_signature():
    sig = inspect.signature(DriveService.list_permissions)
    assert "file_id" in sig.parameters


def test_create_permission_signature():
    sig = inspect.signature(DriveService.create_permission)
    params = sig.parameters
    assert "file_id" in params
    assert "role" in params
    assert "type" in params


def test_delete_permission_signature():
    sig = inspect.signature(DriveService.delete_permission)
    params = sig.parameters
    assert "file_id" in params
    assert "permission_id" in params
