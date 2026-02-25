# Quickstart: google_sdk

## Install

```bash
uv add google-sdk
# With OS keychain support:
uv add google-sdk[keyring]
```

## Service Account (server-to-server)

```python
from google_sdk import GoogleClient
from google_sdk.auth import service_account

creds = service_account("/path/to/key.json", scopes=["drive", "calendar", "meet"])

with GoogleClient(creds) as client:
    # Drive: list files
    for file in client.drive.list_files(q="mimeType='application/pdf'"):
        print(file.name, file.size)

    # Calendar: upcoming events
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    for event in client.calendar.list_events(time_min=now):
        print(event.summary, event.start.date_time)

    # Meet: create a meeting
    space = client.meet.create_space()
    print(space.meeting_uri)
```

## OAuth (desktop app)

```python
from google_sdk import GoogleClient
from google_sdk.auth import oauth
from google_sdk.auth.token_store import KeyringTokenStore

creds = oauth(
    "client_secret.json",
    scopes=["drive.readonly", "calendar"],
    token_store=KeyringTokenStore(),
)

with GoogleClient(creds) as client:
    files = list(client.drive.list_files())
```

## Async Usage

```python
from google_sdk import AsyncGoogleClient
from google_sdk.auth import service_account

creds = service_account("/path/to/key.json", scopes=["drive"])

async with AsyncGoogleClient(creds) as client:
    async for file in client.drive.list_files():
        print(file.name)

    await client.drive.create_file("report.pdf", content=data, resumable=True)
```

## Upload with Progress

```python
def on_progress(p):
    print(f"{p.percentage:.1f}% ({p.bytes_sent}/{p.total_bytes})")

client.drive.create_file("large.zip", content=open("large.zip", "rb"),
                         on_progress=on_progress)
```

## Logging

```python
import logging

# See all SDK activity
logging.getLogger("google_sdk").setLevel(logging.DEBUG)

# Or just transport (HTTP requests/responses)
logging.getLogger("google_sdk.transport").setLevel(logging.DEBUG)

# JSON format for production
from google_sdk import GoogleClient, SDKConfig
config = SDKConfig(log_level="DEBUG", log_format="json")
client = GoogleClient(creds, config=config)
```

## Error Handling

```python
from google_sdk.exceptions import NotFoundError, RateLimitError, APIError

try:
    file = client.drive.get_file("nonexistent")
except NotFoundError:
    print("File not found")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
except APIError as e:
    print(f"API error {e.status_code}: {e.message}")
```
