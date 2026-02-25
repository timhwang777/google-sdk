"""Google Drive service exports."""

from google_sdk.services import ServiceRegistry
from google_sdk.services.drive.client import DriveService
from google_sdk.services.drive.models import File, Folder, Permission, UploadProgress

ServiceRegistry.register("drive")(DriveService)

__all__ = ["DriveService", "File", "Folder", "Permission", "UploadProgress"]
