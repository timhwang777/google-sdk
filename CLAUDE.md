# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Python SDK (`google-sdk` v0.1.0) wrapping Google Drive, Calendar, and Meet APIs. Built on httpx + Pydantic v2 + google-auth. Python 3.11+.

## Commands

```bash
uv run pytest                # run all tests (261 tests)
uv run pytest tests/unit/test_client.py          # single file
uv run pytest tests/unit/test_client.py -k "test_name"  # single test
uv run ruff check .          # lint
uv run ruff format .         # format
uv sync --dev                # install deps
```

## Architecture

```
GoogleClient / AsyncGoogleClient  (_client.py)
  ├── .drive / .calendar / .meet  (lazy @cached_property)
  │     └── BaseService  (services/_base.py)
  │           ├── _get/_post/_patch/_put/_delete → httpx
  │           ├── _raise_for_status → exception mapping
  │           └── _parse(data, model) → Pydantic validation
  ├── Transport stack  (_transport/)
  │     └── RateLimiter → RetryTransport → httpx.HTTPTransport
  └── Auth  (auth/)
        ├── service_account() / oauth() / resolve_credentials()
        └── Token stores: File, Env, Keyring
```

**Key patterns:**
- Services inherit `BaseService` which handles auth header injection, credential refresh, error mapping, and Pydantic parsing
- `PageIterator[T]` / `AsyncPageIterator[T]` provide lazy pagination via callback pattern (`_fetch_page`)
- Models extend `BaseResource` (Pydantic) with `extra="allow"` and camelCase↔snake_case aliasing
- Transport layer stacks middleware: rate limiting (token bucket) → retry (exponential backoff + jitter) → httpx
- `AsyncGoogleClient` has async lifecycle but service methods are synchronous in v0.1.0

**Exception hierarchy:** `GoogleSDKError` → `AuthenticationError` | `TokenStoreError` | `ValidationError` | `APIError` → `NotFoundError`(404) | `PermissionError`(403) | `RateLimitError`(429) | `QuotaExceededError`(429)

## Code Style

- Line length: 100 chars (ruff)
- Rule sets: E, F, I, UP, B, SIM
- Pydantic v2 models with `model_config = ConfigDict(populate_by_name=True)`

## Test Structure

- `tests/unit/` — mocked HTTP via respx
- `tests/contract/` — VCR cassettes
- `tests/integration/` — live API (requires credentials)
- `tests/benchmarks/` — performance scripts
- `tests/conftest.py` — shared fixtures; `tests/factories.py` — test data builders
