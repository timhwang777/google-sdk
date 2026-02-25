# google-sdk (v0.1.0)

Python SDK for Google Drive, Calendar, and Meet APIs.

This repository is the current `0.1.0` implementation. It provides:

- Typed service clients for Drive, Calendar, and Meet (Pydantic models).
- Multiple auth entry points (service account, OAuth desktop flow, ADC resolution).
- Automatic pagination via iterators.
- Drive uploads with automatic simple vs resumable strategy (5 MB threshold).
- Structured exception hierarchy for common Google API error categories.
- A tested codebase (261 tests passing on February 25, 2026).

## Requirements

- Python `>=3.11`
- `httpx`
- `pydantic>=2`
- `google-auth`
- `google-auth-oauthlib`

## Install

Install from source (recommended in this repo):

```bash
uv sync --dev
```

Or editable install:

```bash
pip install -e .
```

Optional keyring-backed OAuth token storage:

```bash
pip install -e ".[keyring]"
```

## Quick Start (Service Account)

```python
from google_sdk import GoogleClient
from google_sdk.auth import service_account

creds = service_account("/path/to/service-account.json")

with GoogleClient(creds) as client:
    for file in client.drive.list_files(page_size=10):
        print(file.id, file.name)
```

## Authentication

### 1) Service Account

```python
from google_sdk.auth import service_account
from google_sdk.auth.scopes import DriveScopes

creds = service_account(
    "/path/to/service-account.json",
    scopes=[DriveScopes.READONLY],
)
```

Domain-wide delegation is supported via `subject`:

```python
creds = service_account("/path/to/service-account.json", subject="admin@example.com")
```

### 2) OAuth (Installed App Flow)

```python
from google_sdk.auth import oauth
from google_sdk.auth.scopes import CalendarScopes, DriveScopes

creds = oauth(
    "client_secrets.json",
    scopes=[DriveScopes.READONLY, CalendarScopes.FULL],
)
```

By default, OAuth tokens are cached at:

- `~/.config/google-sdk/tokens.json`

### 3) Credential Auto-Resolution

```python
from google_sdk.auth import resolve_credentials

creds = resolve_credentials()
```

Resolution order:

1. Explicit credentials passed to `resolve_credentials()`
2. Application Default Credentials (`google.auth.default()`)
3. `~/.config/google-sdk/service_account.json`
4. Raises `AuthenticationError`

## Token Storage Backends

- `FileTokenStore`: default JSON file store (`0600` permissions).
- `EnvTokenStore`: read-only store from `GOOGLE_TOKEN_<KEY>` env vars.
- `KeyringTokenStore`: system keychain backend (requires `keyring` extra).

## Client Types

### `GoogleClient` (sync)

```python
from google_sdk import GoogleClient

with GoogleClient(creds) as client:
    events = list(client.calendar.list_events())
```

### `AsyncGoogleClient` (async context manager)

```python
from google_sdk import AsyncGoogleClient

async with AsyncGoogleClient(creds) as client:
    participants = list(client.meet.list_participants("abc"))
```

Important for `v0.1.0`:

- `AsyncGoogleClient` supports async lifecycle (`async with`, `await close()`).
- Service methods exposed via `client.drive`, `client.calendar`, and `client.meet` are currently synchronous.

## Service Coverage

### Drive (`client.drive`)

- `list_files`, `get_file`, `create_file`, `update_file`, `delete_file`
- `download_file`, `export_file`
- `copy_file`, `move_file`, `create_folder`
- `list_permissions`, `create_permission`, `delete_permission`

Upload behavior:

- `< 5 MB`: multipart upload.
- `>= 5 MB`: resumable upload (or force with `resumable=True`).
- Progress callback support via `on_progress(UploadProgress)`.

Example:

```python
from google_sdk.services.drive.models import UploadProgress

def on_progress(p: UploadProgress) -> None:
    print(f"{p.percentage:.1f}% ({p.bytes_sent}/{p.total_bytes})")

with open("large.zip", "rb") as fh:
    created = client.drive.create_file(
        "large.zip",
        content=fh,  # or pass bytes
        on_progress=on_progress,
    )
```

### Calendar (`client.calendar`)

- `list_calendars`, `get_calendar`, `create_calendar`, `update_calendar`, `delete_calendar`
- `list_events`, `get_event`, `create_event`, `quick_add`, `update_event`, `delete_event`
- `freebusy`

Example:

```python
from datetime import UTC, datetime, timedelta

now = datetime.now(UTC)
later = now + timedelta(days=7)

for event in client.calendar.list_events(time_min=now, time_max=later, order_by="startTime"):
    print(event.summary, event.start)
```

### Meet (`client.meet`)

- `create_space`, `get_space`, `update_space`, `end_active_conference`
- `list_participants`, `get_participant`, `list_participant_sessions`
- `list_recordings`, `get_recording`

Example:

```python
space = client.meet.create_space()
print(space.meeting_uri)
```

## Pagination

List operations return `PageIterator[T]`:

```python
files_iter = client.drive.list_files(page_size=100)

for file in files_iter:
    print(file.name)
```

You can iterate per page:

```python
for page in client.drive.list_files().pages:
    print(f"received page with {len(page)} files")
```

## Configuration

Pass `SDKConfig` to control runtime behavior:

```python
from google_sdk import GoogleClient, SDKConfig

config = SDKConfig(
    timeout=30.0,
    max_retries=3,
    max_backoff=60.0,
    rate_limit_per_second=None,
    log_level="WARNING",
    log_format="text",  # "text" | "json"
)

client = GoogleClient(creds, config=config)
```

## Error Handling

All SDK-specific exceptions inherit from `GoogleSDKError`.

Common API exceptions:

- `APIError`
- `NotFoundError` (404)
- `PermissionError` (403)
- `RateLimitError` (429, includes `retry_after` when available)
- `QuotaExceededError` (quota-related 429 responses)

Example:

```python
from google_sdk.exceptions import APIError, NotFoundError, RateLimitError

try:
    file = client.drive.get_file("missing-id")
except NotFoundError:
    print("File not found")
except RateLimitError as e:
    print(f"Rate limited; retry_after={e.retry_after}")
except APIError as e:
    print(f"API error {e.status_code}: {e}")
```

## Development

Run tests:

```bash
uv run pytest -q
```

Current repository status:

- `261 passed in 0.72s` (run on February 25, 2026)

Lint:

```bash
uv run ruff check .
```

Format:

```bash
uv run ruff format .
```

Benchmarks:

```bash
uv run python tests/benchmarks/bench_transport_overhead.py
uv run python tests/benchmarks/bench_pagination_memory.py
```

## Project Layout

```text
src/google_sdk/
  auth/                # auth helpers and token stores
  services/
    drive/             # Drive client + models + upload logic
    calendar/          # Calendar client + models
    meet/              # Meet client + models
  _transport/          # retry/rate-limit transport utilities
  _pagination.py       # sync + async iterators
  exceptions.py        # SDK exception hierarchy
tests/
  unit/
  contract/
  benchmarks/
```
