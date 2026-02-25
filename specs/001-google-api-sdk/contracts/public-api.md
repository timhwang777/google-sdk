# Public API Contract: google_sdk

**Phase 1 Output** | **Date**: 2026-02-23

## Top-Level Exports (`google_sdk`)

```python
from google_sdk import GoogleClient, AsyncGoogleClient
from google_sdk.auth import service_account, oauth
```

## Client Interface

```python
class GoogleClient:
    def __init__(
        self,
        credentials: google.auth.credentials.Credentials,
        *,
        token_store: TokenStore | None = None,
        config: SDKConfig | None = None,
    ) -> None: ...

    @cached_property
    def drive(self) -> DriveService: ...

    @cached_property
    def calendar(self) -> CalendarService: ...

    @cached_property
    def meet(self) -> MeetService: ...

    def __enter__(self) -> Self: ...
    def __exit__(self, *args) -> None: ...
    def close(self) -> None: ...


class AsyncGoogleClient:
    """Identical interface, async methods return coroutines/async iterators."""
    ...
    async def __aenter__(self) -> Self: ...
    async def __aexit__(self, *args) -> None: ...
    async def close(self) -> None: ...
```

## Auth Helpers

```python
def service_account(
    key_path: str | Path,
    *,
    scopes: list[str] | None = None,
    subject: str | None = None,
) -> google.oauth2.service_account.Credentials: ...

def oauth(
    client_secrets: str | Path,
    scopes: list[str],
    *,
    token_store: TokenStore | None = None,
) -> google.oauth2.credentials.Credentials: ...
```

## TokenStore ABC

```python
class TokenStore(ABC):
    @abstractmethod
    def load(self, key: str) -> TokenData | None: ...
    @abstractmethod
    def save(self, key: str, token: TokenData) -> None: ...
    @abstractmethod
    def delete(self, key: str) -> None: ...

class FileTokenStore(TokenStore): ...    # Default, ~/.config/google-sdk/tokens.json
class KeyringTokenStore(TokenStore): ... # Optional, requires google-sdk[keyring]
class EnvTokenStore(TokenStore): ...     # Read-only, from env vars
```

## DriveService

```python
class DriveService:
    def list_files(
        self, *, q: str | None = None, page_size: int = 100,
        fields: str | None = None, order_by: str | None = None,
    ) -> PageIterator[File]: ...

    def get_file(self, file_id: str, *, fields: str | None = None) -> File: ...
    def create_file(self, name: str, *, content: bytes | BinaryIO | None = None,
                    mime_type: str | None = None, parents: list[str] | None = None,
                    resumable: bool | None = None,
                    on_progress: Callable[[UploadProgress], None] | None = None) -> File: ...
    def update_file(self, file_id: str, **kwargs) -> File: ...
    def delete_file(self, file_id: str) -> None: ...
    def download_file(self, file_id: str, *, destination: Path | BinaryIO | None = None) -> bytes | None: ...
    def export_file(self, file_id: str, mime_type: str, *, destination: Path | BinaryIO | None = None) -> bytes | None: ...
    def copy_file(self, file_id: str, *, name: str | None = None, parents: list[str] | None = None) -> File: ...
    def move_file(self, file_id: str, *, new_parent: str, remove_parents: list[str] | None = None) -> File: ...

    # Folders
    def create_folder(self, name: str, *, parents: list[str] | None = None) -> File: ...

    # Permissions
    def list_permissions(self, file_id: str) -> list[Permission]: ...
    def create_permission(self, file_id: str, *, role: str, type: str,
                          email_address: str | None = None) -> Permission: ...
    def delete_permission(self, file_id: str, permission_id: str) -> None: ...
```

## CalendarService

```python
class CalendarService:
    def list_calendars(self) -> PageIterator[Calendar]: ...
    def get_calendar(self, calendar_id: str = "primary") -> Calendar: ...
    def create_calendar(self, summary: str, **kwargs) -> Calendar: ...
    def update_calendar(self, calendar_id: str, **kwargs) -> Calendar: ...
    def delete_calendar(self, calendar_id: str) -> None: ...

    def list_events(
        self, calendar_id: str = "primary", *,
        time_min: datetime | None = None, time_max: datetime | None = None,
        q: str | None = None, single_events: bool = True,
        order_by: str | None = None,
    ) -> PageIterator[Event]: ...
    def get_event(self, calendar_id: str, event_id: str) -> Event: ...
    def create_event(self, calendar_id: str = "primary", **kwargs) -> Event: ...
    def quick_add(self, text: str, *, calendar_id: str = "primary") -> Event: ...
    def update_event(self, calendar_id: str, event_id: str, **kwargs) -> Event: ...
    def delete_event(self, calendar_id: str, event_id: str) -> None: ...

    def freebusy(self, time_min: datetime, time_max: datetime,
                 calendar_ids: list[str]) -> FreeBusyResponse: ...
```

## MeetService

```python
class MeetService:
    def create_space(self, *, config: SpaceConfig | None = None) -> Space: ...
    def get_space(self, space_name: str) -> Space: ...
    def update_space(self, space_name: str, **kwargs) -> Space: ...
    def end_active_conference(self, space_name: str) -> None: ...

    def list_participants(self, conference_record: str) -> PageIterator[Participant]: ...
    def get_participant(self, name: str) -> Participant: ...
    def list_participant_sessions(self, participant_name: str) -> PageIterator[ParticipantSession]: ...

    def list_recordings(self, conference_record: str) -> PageIterator[Recording]: ...
    def get_recording(self, name: str) -> Recording: ...
```

## Logging Configuration

```python
# Users configure via standard logging
import logging
logging.getLogger("google_sdk").setLevel(logging.DEBUG)

# Or via SDK config
config = SDKConfig(log_level="DEBUG", log_format="json")
client = GoogleClient(creds, config=config)
```

## Logger Hierarchy

```
google_sdk              # Root SDK logger
google_sdk.auth         # Auth flows, token refresh (credentials redacted)
google_sdk.transport    # HTTP requests/responses at DEBUG
google_sdk.retry        # Retry attempts, backoff timing
google_sdk.services.drive
google_sdk.services.calendar
google_sdk.services.meet
```

## Error Hierarchy

```python
class GoogleSDKError(Exception): ...
class AuthenticationError(GoogleSDKError): ...
class TokenStoreError(GoogleSDKError): ...
class APIError(GoogleSDKError):
    status_code: int
    message: str
    errors: list[dict]
    request_id: str | None
class NotFoundError(APIError): ...      # 404
class PermissionError(APIError): ...    # 403
class RateLimitError(APIError): ...     # 429
class QuotaExceededError(APIError): ... # 429 with quota reason
class ValidationError(GoogleSDKError): ...
```
