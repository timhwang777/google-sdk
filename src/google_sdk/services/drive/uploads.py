"""Resumable upload handler for Google Drive."""

from __future__ import annotations

import logging
from collections.abc import Callable
from io import BytesIO
from typing import BinaryIO

import httpx

from google_sdk.services.drive.models import File, UploadProgress

logger = logging.getLogger("google_sdk.services.drive")

RESUMABLE_THRESHOLD = 5 * 1024 * 1024  # 5 MB
CHUNK_SIZE = 8 * 1024 * 1024  # 8 MiB


class ResumableUpload:
    """Handles resumable upload sessions for large files."""

    def __init__(
        self,
        url: str,
        headers: dict[str, str],
        name: str,
        content: bytes | BinaryIO,
        mime_type: str,
        metadata: dict,
        on_progress: Callable[[UploadProgress], None] | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._upload_url = url
        self._auth_headers = headers
        self._name = name
        self._mime_type = mime_type
        self._metadata = metadata
        self._on_progress = on_progress
        self._timeout = timeout

        if isinstance(content, bytes):
            self._content = BytesIO(content)
            self._total_bytes = len(content)
        else:
            content.seek(0, 2)  # Seek to end
            self._total_bytes = content.tell()
            content.seek(0)
            self._content = content

    def _initiate_session(self) -> str:
        """Initiate resumable upload and return session URI."""
        import json

        headers = {
            **self._auth_headers,
            "Content-Type": "application/json",
            "X-Upload-Content-Type": self._mime_type,
            "X-Upload-Content-Length": str(self._total_bytes),
        }
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(
                self._upload_url,
                headers=headers,
                content=json.dumps(self._metadata).encode(),
            )
        resp.raise_for_status()
        return resp.headers["Location"]

    def execute(self) -> File:
        """Execute the resumable upload, returning the created File."""
        session_uri = self._initiate_session()
        bytes_sent = 0

        with httpx.Client(timeout=self._timeout) as client:
            while bytes_sent < self._total_bytes:
                chunk = self._content.read(CHUNK_SIZE)
                if not chunk:
                    break
                chunk_end = bytes_sent + len(chunk) - 1
                headers = {
                    "Content-Range": f"bytes {bytes_sent}-{chunk_end}/{self._total_bytes}",
                    "Content-Type": self._mime_type,
                }
                resp = client.put(session_uri, content=chunk, headers=headers)

                if resp.status_code == 308:
                    # Incomplete — continue
                    range_header = resp.headers.get("Range", "")
                    if range_header:
                        bytes_sent = int(range_header.split("-")[1]) + 1
                    else:
                        bytes_sent += len(chunk)
                elif resp.status_code in (200, 201):
                    bytes_sent += len(chunk)
                    if self._on_progress:
                        self._on_progress(UploadProgress(bytes_sent, self._total_bytes))
                    return File.model_validate(resp.json())
                else:
                    resp.raise_for_status()

                if self._on_progress:
                    self._on_progress(UploadProgress(bytes_sent, self._total_bytes))

        raise RuntimeError("Upload ended without completion response")
