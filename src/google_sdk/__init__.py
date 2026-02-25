"""google-sdk — Python SDK for Google Drive, Calendar, and Meet APIs.

Example::

    from google_sdk import GoogleClient
    from google_sdk.auth import service_account

    creds = service_account("key.json")
    with GoogleClient(creds) as client:
        for file in client.drive.list_files():
            print(file.name)
"""

from google_sdk._client import AsyncGoogleClient, GoogleClient
from google_sdk._config import SDKConfig
from google_sdk._version import __version__

__all__ = ["GoogleClient", "AsyncGoogleClient", "SDKConfig", "__version__"]
