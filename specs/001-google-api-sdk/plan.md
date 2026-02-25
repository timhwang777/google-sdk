# Implementation Plan: Google API Python SDK

**Branch**: `001-google-api-sdk` | **Date**: 2026-02-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-google-api-sdk/spec.md`

## Summary

Build a modern Python SDK (`google-sdk`) for Google Drive, Calendar, and Meet APIs. The SDK uses httpx for HTTP transport, Pydantic v2 for typed response models, manual sync and async client implementations sharing a common base, and a pluggable auth layer built on `google-auth`/`google-auth-oauthlib` with a novel `TokenStore` abstraction. Package management and task execution use `uv`.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: httpx, pydantic v2, google-auth, google-auth-oauthlib, respx (test), vcrpy (test)
**Package Manager**: uv (for dependency management, virtual environments, and command execution)
**Storage**: N/A (library — token storage via pluggable TokenStore backends)
**Testing**: pytest + respx (unit) + VCR.py (integration), run via `uv run pytest`
**Linting**: ruff check + ruff format, run via `uv run ruff check .` and `uv run ruff format .`
**Target Platform**: Cross-platform Python library (Linux, macOS, Windows)
**Project Type**: Library (published as `google-sdk` on PyPI)
**Performance Goals**: SDK overhead < 2x raw HTTP round-trip time; import+init < 500ms
**Constraints**: Thread-safe sync client, coroutine-safe async client; pinned Google API versions per release
**Scale/Scope**: 3 Google services (Drive, Calendar, Meet) in v1; designed for easy service addition

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality (KISS & DRY) | PASS | Single async codebase + unasync eliminates duplication. Service-per-module separation follows single responsibility. BaseService + BaseResource provide DRY foundations. |
| II. Test-Driven Development | PASS | Three-tier test strategy (unit/integration/contract) planned. 90%+ coverage target. TDD workflow will be enforced during implementation. |
| III. Testing Standards | PASS | Tests organized into `tests/unit/`, `tests/integration/`, `tests/contract/`. Contract tests validate public API against Google services. respx for mocking, VCR.py for recorded interactions. |
| IV. User Experience Consistency | PASS | snake_case functions, PascalCase classes. Actionable error messages with status code + suggestion. Docstrings with examples on all public modules. |
| V. Security | PASS | Credentials loaded from files/env/keychain, never hardcoded. Input validation on all public methods. OAuth minimal scopes auto-selected. Credential redaction in logs. |
| VI. Performance | PASS | Batch requests deferred to v2 (spec clarification). Retry with exponential backoff. Response caching deferred (not in v1 spec). Pagination via iterators bounds memory. Rate limiting at transport level. |

**Constitution violations requiring justification:**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Batch operations deferred (Constitution VI) | v1 scope decision — batch support explicitly out-of-scope per clarification. Transport layer designed for future batch support. | Including batch in v1 would significantly increase scope without addressing the primary use cases. |
| Response caching deferred (Constitution VI) | Not in v1 spec requirements. Can be added as middleware in v2 without breaking changes. | Adding caching increases complexity and requires cache invalidation strategy per service. |

## Project Structure

### Documentation (this feature)

```text
specs/001-google-api-sdk/
├── plan.md              # This file
├── research.md          # Phase 0 output (complete)
├── data-model.md        # Phase 1 output (complete)
├── quickstart.md        # Phase 1 output (complete)
├── contracts/           # Phase 1 output (complete)
│   └── public-api.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
└── google_sdk/
    ├── __init__.py              # Exports GoogleClient, AsyncGoogleClient
    ├── _client.py               # BaseClient shared logic
    ├── _config.py               # SDKConfig, RetryConfig dataclasses
    ├── _version.py              # __version__
    ├── auth/
    │   ├── __init__.py          # Exports service_account, oauth
    │   ├── _base.py             # Abstract CredentialProvider
    │   ├── oauth.py             # User OAuth 2.0 flow helpers
    │   ├── service_account.py   # Service account helpers
    │   ├── token_store.py       # TokenStore ABC + FileTokenStore, KeyringTokenStore, EnvTokenStore
    │   └── scopes.py            # Scope constants per service, auto-selection logic
    ├── _transport/
    │   ├── __init__.py
    │   ├── _base.py             # Abstract Transport protocol
    │   ├── sync_transport.py    # httpx.Client-based
    │   ├── async_transport.py   # httpx.AsyncClient-based
    │   ├── retry.py             # Exponential backoff middleware
    │   └── rate_limiter.py      # Per-service token bucket
    ├── _pagination.py           # PageIterator / AsyncPageIterator
    ├── _models/
    │   └── base.py              # BaseResource Pydantic model
    ├── services/
    │   ├── __init__.py          # Service registry
    │   ├── _base.py             # BaseService class
    │   ├── drive/
    │   │   ├── __init__.py
    │   │   ├── client.py        # DriveService / AsyncDriveService
    │   │   ├── models.py        # File, Folder, Permission, UploadProgress
    │   │   └── uploads.py       # ResumableUpload handler
    │   ├── calendar/
    │   │   ├── __init__.py
    │   │   ├── client.py        # CalendarService / AsyncCalendarService
    │   │   └── models.py        # Calendar, Event, Attendee, FreeBusy*
    │   └── meet/
    │       ├── __init__.py
    │       ├── client.py        # MeetService / AsyncMeetService
    │       └── models.py        # Space, Participant, Recording
    ├── exceptions.py            # GoogleSDKError hierarchy
    └── py.typed                 # PEP 561 marker

tests/
├── unit/
│   ├── test_auth/
│   ├── test_transport/
│   ├── test_pagination.py
│   ├── test_models/
│   └── test_services/
│       ├── test_drive/
│       ├── test_calendar/
│       └── test_meet/
├── integration/
│   └── cassettes/              # VCR.py recorded interactions
├── contract/
│   ├── test_drive_contract.py
│   ├── test_calendar_contract.py
│   └── test_meet_contract.py
├── benchmarks/
│   ├── bench_transport_overhead.py
│   └── bench_pagination_memory.py
├── conftest.py
└── factories.py                # Pydantic model factories for test data

pyproject.toml                  # uv project config, dependencies, build
uv.lock                         # uv lock file
```

**Structure Decision**: Single-project library layout with `src/` layout (PEP 517/518 compliant). `src/google_sdk/` is the package root. `uv` manages dependencies, virtual environment, and script execution. The `src/` layout prevents accidental imports from the working directory during testing.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Batch operations deferred | Out-of-scope for v1 per spec clarification | Transport designed for future extensibility |
| Response caching deferred | Not in v1 requirements | Can be added as transport middleware later |
