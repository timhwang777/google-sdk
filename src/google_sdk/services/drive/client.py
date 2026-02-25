"""Google Drive service client."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import BinaryIO

from google_sdk._pagination import PageIterator
from google_sdk.services._base import DRIVE_API_VERSION, BaseService
from google_sdk.services.drive.models import File, Folder, Permission, UploadProgress
from google_sdk.services.drive.uploads import RESUMABLE_THRESHOLD, ResumableUpload

logger = logging.getLogger("google_sdk.services.drive")

_UPLOAD_BASE = f"https://www.googleapis.com/upload/drive/{DRIVE_API_VERSION}/files"
_API_BASE = f"https://www.googleapis.com/drive/{DRIVE_API_VERSION}"


class DriveService(BaseService):
    """Client for Google Drive API v3."""

    _BASE_URL = _API_BASE

    # ── File operations ─────────────────────────────────────────────────────

    def list_files(
        self,
        *,
        q: str | None = None,
        page_size: int = 100,
        fields: str | None = None,
        order_by: str | None = None,
    ) -> PageIterator[File]:
        """List files in Drive.

        Returns:
            PageIterator yielding File objects.
        """
        params: dict = {"pageSize": page_size}
        if q:
            params["q"] = q
        if fields:
            params["fields"] = fields
        if order_by:
            params["orderBy"] = order_by

        def fetch_page(page_token: str | None) -> dict:
            p = dict(params)
            if page_token:
                p["pageToken"] = page_token
            return self._get("/files", params=p)

        return PageIterator(fetch_page, File, response_key="files")

    def get_file(self, file_id: str, *, fields: str | None = None) -> File:
        params = {}
        if fields:
            params["fields"] = fields
        data = self._get(f"/files/{file_id}", params=params)
        return self._parse(data, File)

    def create_file(
        self,
        name: str,
        *,
        content: bytes | BinaryIO | None = None,
        mime_type: str | None = None,
        parents: list[str] | None = None,
        resumable: bool | None = None,
        on_progress: Callable[[UploadProgress], None] | None = None,
    ) -> File:
        """Create a file in Drive.

        Automatically selects resumable upload for files >= 5 MB.
        """
        metadata: dict = {"name": name}
        if mime_type:
            metadata["mimeType"] = mime_type
        if parents:
            metadata["parents"] = parents

        if content is None:
            # Metadata-only file
            data = self._post("/files", json=metadata)
            return self._parse(data, File)

        # Determine upload strategy
        if isinstance(content, bytes):
            size = len(content)
        else:
            pos = content.tell()
            content.seek(0, 2)
            size = content.tell()
            content.seek(pos)

        use_resumable = resumable if resumable is not None else size >= RESUMABLE_THRESHOLD

        if use_resumable:
            upload = ResumableUpload(
                url=f"{_UPLOAD_BASE}?uploadType=resumable",
                headers=self._get_headers(),
                name=name,
                content=content,
                mime_type=mime_type or "application/octet-stream",
                metadata=metadata,
                on_progress=on_progress,
                timeout=self._config.timeout,
            )
            return upload.execute()
        else:
            # Simple multipart upload
            import httpx

            body_bytes = content if isinstance(content, bytes) else content.read()
            boundary = "boundary_abc123"
            import json

            meta_json = json.dumps(metadata).encode()
            body = (
                f"--{boundary}\r\nContent-Type: application/json\r\n\r\n".encode()
                + meta_json
                + f"\r\n--{boundary}\r\nContent-Type: {mime_type or 'application/octet-stream'}\r\n\r\n".encode()
                + body_bytes
                + f"\r\n--{boundary}--".encode()
            )
            headers = {
                **self._get_headers(),
                "Content-Type": f"multipart/related; boundary={boundary}",
            }
            with httpx.Client(timeout=self._config.timeout) as client:
                resp = client.post(
                    f"{_UPLOAD_BASE}?uploadType=multipart",
                    content=body,
                    headers=headers,
                )
            resp.raise_for_status()
            return self._parse(resp.json(), File)

    def update_file(self, file_id: str, **kwargs) -> File:
        data = self._patch(f"/files/{file_id}", json=kwargs)
        return self._parse(data, File)

    def delete_file(self, file_id: str) -> None:
        self._delete(f"/files/{file_id}")

    def download_file(
        self,
        file_id: str,
        *,
        destination: Path | BinaryIO | None = None,
    ) -> bytes | None:
        """Download file content."""
        import httpx

        url = f"{_API_BASE}/files/{file_id}"
        headers = self._get_headers()
        with httpx.Client(timeout=self._config.timeout) as client:
            resp = client.get(url, params={"alt": "media"}, headers=headers)
        resp.raise_for_status()
        if destination is None:
            return resp.content
        if isinstance(destination, Path):
            destination.write_bytes(resp.content)
            return None
        destination.write(resp.content)
        return None

    def export_file(
        self,
        file_id: str,
        mime_type: str,
        *,
        destination: Path | BinaryIO | None = None,
    ) -> bytes | None:
        """Export a Google Workspace file to a specific format."""
        import httpx

        url = f"{_API_BASE}/files/{file_id}/export"
        headers = self._get_headers()
        with httpx.Client(timeout=self._config.timeout) as client:
            resp = client.get(url, params={"mimeType": mime_type}, headers=headers)
        resp.raise_for_status()
        if destination is None:
            return resp.content
        if isinstance(destination, Path):
            destination.write_bytes(resp.content)
            return None
        destination.write(resp.content)
        return None

    def copy_file(
        self,
        file_id: str,
        *,
        name: str | None = None,
        parents: list[str] | None = None,
    ) -> File:
        body: dict = {}
        if name:
            body["name"] = name
        if parents:
            body["parents"] = parents
        data = self._post(f"/files/{file_id}/copy", json=body)
        return self._parse(data, File)

    def move_file(
        self,
        file_id: str,
        *,
        new_parent: str,
        remove_parents: list[str] | None = None,
    ) -> File:
        params = {"addParents": new_parent}
        if remove_parents:
            params["removeParents"] = ",".join(remove_parents)
        data = self._patch(f"/files/{file_id}", params=params)
        return self._parse(data, File)

    # ── Folder operations ────────────────────────────────────────────────────

    def create_folder(self, name: str, *, parents: list[str] | None = None) -> File:
        metadata: dict = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parents:
            metadata["parents"] = parents
        data = self._post("/files", json=metadata)
        return self._parse(data, Folder)

    # ── Permission operations ────────────────────────────────────────────────

    def list_permissions(self, file_id: str) -> list[Permission]:
        data = self._get(f"/files/{file_id}/permissions")
        return [Permission.model_validate(p) for p in data.get("permissions", [])]

    def create_permission(
        self,
        file_id: str,
        *,
        role: str,
        type: str,
        email_address: str | None = None,
    ) -> Permission:
        body: dict = {"role": role, "type": type}
        if email_address:
            body["emailAddress"] = email_address
        data = self._post(f"/files/{file_id}/permissions", json=body)
        return self._parse(data, Permission)

    def delete_permission(self, file_id: str, permission_id: str) -> None:
        self._delete(f"/files/{file_id}/permissions/{permission_id}")
