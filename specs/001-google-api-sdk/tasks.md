# Tasks: Google API Python SDK

**Input**: Design documents from `/specs/001-google-api-sdk/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/public-api.md

**Tests**: Required per Constitution Principle II (TDD is NON-NEGOTIABLE). Red-Green-Refactor cycle enforced.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization with uv, directory structure, and tooling

- [X] T001 Initialize uv project with `uv init` and configure pyproject.toml with project metadata, Python 3.11+ requirement, and dependencies (httpx, pydantic>=2.0, google-auth, google-auth-oauthlib) plus dev dependencies (pytest, respx, vcrpy, ruff) in pyproject.toml
- [X] T002 Create source directory structure per plan.md: src/google_sdk/ with subdirectories auth/, _transport/, _models/, services/drive/, services/calendar/, services/meet/ and all __init__.py files
- [X] T003 [P] Create test directory structure: tests/unit/test_auth/, tests/unit/test_transport/, tests/unit/test_models/, tests/unit/test_services/test_drive/, tests/unit/test_services/test_calendar/, tests/unit/test_services/test_meet/, tests/integration/, tests/contract/, tests/conftest.py, tests/factories.py
- [X] T004 [P] Configure ruff in pyproject.toml with linting and formatting rules, add py.typed marker at src/google_sdk/py.typed
- [X] T005 [P] Create src/google_sdk/_version.py with __version__ = "0.1.0"

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T006 [P] Write unit tests for exception hierarchy in tests/unit/test_exceptions.py — test GoogleSDKError, AuthenticationError, TokenStoreError, APIError (with status_code, message, errors, request_id), NotFoundError, PermissionError, RateLimitError, QuotaExceededError, ValidationError per contracts/public-api.md
- [X] T007 [P] Write unit tests for SDKConfig and RetryConfig in tests/unit/test_config.py — test defaults (timeout=30.0, max_retries=3, max_backoff=60.0, retryable codes={429,500,502,503,504}), custom values, validation
- [X] T008 [P] Write unit tests for BaseResource model in tests/unit/test_models/test_base.py — test extra="allow", populate_by_name=True, camelCase alias mapping, unknown field acceptance
- [X] T009 [P] Write unit tests for retry middleware in tests/unit/test_transport/test_retry.py — test exponential backoff with jitter on 429/500/502/503/504, respect Retry-After header, pass-through on non-retryable codes, max retry exhaustion
- [X] T010 [P] Write unit tests for rate limiter in tests/unit/test_transport/test_rate_limiter.py — test token bucket per-service limiting, delay behavior when bucket empty, configurable rate
- [X] T011 [P] Write unit tests for async pagination in tests/unit/test_pagination.py — test AsyncPageIterator yields items across pages, handles empty pages, stops on no nextPageToken, manual page access via .pages

### Implementation for Foundational

- [X] T012 [P] Implement exception hierarchy in src/google_sdk/exceptions.py per contracts/public-api.md error hierarchy: GoogleSDKError base, AuthenticationError, TokenStoreError, APIError(status_code, message, errors, request_id), NotFoundError(404), PermissionError(403), RateLimitError(429 with retry_after), QuotaExceededError, ValidationError
- [X] T013 [P] Implement SDKConfig and RetryConfig in src/google_sdk/_config.py per data-model.md transport/config models
- [X] T014 [P] Implement BaseResource Pydantic model in src/google_sdk/_models/base.py with model_config extra="allow", populate_by_name=True, id and kind fields per data-model.md
- [X] T015 [P] Implement PageResponse[T] generic model in src/google_sdk/_models/base.py with items: list[T] and next_page_token field with alias="nextPageToken"
- [X] T016 Implement abstract Transport protocol in src/google_sdk/_transport/_base.py with request(method, url, **kwargs) method signature
- [X] T017 Implement async transport in src/google_sdk/_transport/async_transport.py using httpx.AsyncClient with configurable timeout from SDKConfig
- [X] T018 Implement retry middleware in src/google_sdk/_transport/retry.py wrapping transport with exponential backoff + jitter per research.md R7 — wait = min(2^n + random_ms, max_backoff), retry on {429, 500, 502, 503, 504}, respect Retry-After header
- [X] T019 Implement rate limiter in src/google_sdk/_transport/rate_limiter.py with per-service token bucket per research.md R13
- [X] T020 Implement AsyncPageIterator in src/google_sdk/_pagination.py that tracks nextPageToken, fetches subsequent pages on demand, yields Pydantic model instances, and exposes .pages for manual page access per contracts/public-api.md
- [X] T021 Implement BaseService class in src/google_sdk/services/_base.py with transport reference, base_url construction, and helper methods for GET/POST/PUT/PATCH/DELETE that return parsed Pydantic models
- [X] T022 Implement service registry in src/google_sdk/services/__init__.py with @ServiceRegistry.register decorator per research report pattern
- [X] T023 [P] Implement scope constants and auto-selection logic in src/google_sdk/auth/scopes.py — define scope URLs for drive, calendar, meet; implement auto_scopes() that returns minimal scopes based on which services are used, with developer override per spec FR-022
- [X] T024 [P] Define Google API version constants in src/google_sdk/services/_base.py — DRIVE_API_VERSION = "v3", CALENDAR_API_VERSION = "v3", MEET_API_VERSION = "v2"; BaseService constructs base_url using these constants per FR-020
- [X] T025 Verify all foundational tests pass with `uv run pytest tests/unit/test_exceptions.py tests/unit/test_config.py tests/unit/test_models/ tests/unit/test_transport/ tests/unit/test_pagination.py -v`

**Checkpoint**: Foundation ready — exception hierarchy, transport with retry/rate limiting, pagination, base models, base service, scope management all working. User story implementation can now begin.

---

## Phase 3: User Story 1 — Authenticate and Initialize the SDK (Priority: P1) 🎯 MVP

**Goal**: Developer authenticates with OAuth 2.0, service account, or ADC credentials and initializes a client that transparently handles token caching and refresh.

**Independent Test**: Provide valid credentials → SDK obtains and caches token → subsequent calls reuse cached token → expired tokens auto-refresh.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T026 [P] [US1] Write unit tests for TokenStore ABC and FileTokenStore in tests/unit/test_auth/test_token_store.py — test save/load/delete cycle, file creation with correct permissions, scope-keyed storage, missing file returns None
- [X] T027 [P] [US1] Write unit tests for EnvTokenStore in tests/unit/test_auth/test_token_store.py — test read-only load from env vars, save raises error, delete raises error
- [X] T028 [P] [US1] Write unit tests for oauth() helper in tests/unit/test_auth/test_oauth.py — test cached token reuse, expired token refresh, new token flow triggers InstalledAppFlow, token saved to store after flow
- [X] T029 [P] [US1] Write unit tests for service_account() helper in tests/unit/test_auth/test_service_account.py — test key file loading, scopes applied, with_subject() for domain delegation
- [X] T030 [P] [US1] Write unit tests for credential resolution chain in tests/unit/test_auth/test_resolve.py — test each fallback step (explicit → env → ADC via google.auth.default() mock → service account file → AuthenticationError), test clear error when no credentials found
- [X] T031 [P] [US1] Write unit tests for GoogleClient in tests/unit/test_client.py — test init with credentials, context manager (__enter__/__exit__), close() shuts down transport, cached_property services (drive, calendar, meet), thread safety of client instance
- [X] T032 [P] [US1] Write contract tests for auth public API in tests/contract/test_auth_contract.py — verify service_account() and oauth() function signatures match contracts/public-api.md, TokenStore ABC has load/save/delete

### Implementation for User Story 1

- [X] T033 [P] [US1] Implement TokenData model in src/google_sdk/auth/token_store.py per data-model.md — token, refresh_token, token_uri, client_id, client_secret, scopes, expiry fields
- [X] T034 [US1] Implement TokenStore ABC with load/save/delete methods in src/google_sdk/auth/token_store.py, then FileTokenStore (default, ~/.config/google-sdk/tokens.json with 0o600 perms) and EnvTokenStore (read-only from env vars) per research.md R5
- [X] T035 [P] [US1] Implement KeyringTokenStore in src/google_sdk/auth/token_store.py with lazy import of keyring library, raising ImportError with install hint if not available
- [X] T036 [US1] Implement oauth() helper in src/google_sdk/auth/oauth.py — wrap InstalledAppFlow.run_local_server() with TokenStore integration: check cached → refresh if expired → run flow if needed → save to store, per research report auth pattern
- [X] T037 [US1] Implement service_account() helper in src/google_sdk/auth/service_account.py — load key file, apply scopes, support with_subject() for domain delegation per spec FR-018
- [X] T038 [US1] Implement credential resolution chain in src/google_sdk/auth/__init__.py — resolve_credentials() that tries: explicit credentials → environment variables → google.auth.default() (ADC) → service account file from well-known path → raise AuthenticationError with clear message, per FR-001
- [X] T039 [US1] Implement GoogleClient in src/google_sdk/_client.py — init with credentials + optional token_store + SDKConfig, create SyncTransport, expose drive/calendar/meet as @cached_property, implement __enter__/__exit__/close, thread-safe per spec FR-019
- [X] T040 [US1] Implement AsyncGoogleClient in src/google_sdk/_client.py — identical to GoogleClient but using AsyncTransport, __aenter__/__aexit__/async close, coroutine-safe per spec FR-019
- [X] T041 [US1] Implement sync transport in src/google_sdk/_transport/sync_transport.py using httpx.Client with configurable timeout, wrapped with retry and rate limiter middleware
- [X] T042 [US1] Wire up top-level exports in src/google_sdk/__init__.py — export GoogleClient, AsyncGoogleClient, SDKConfig and in src/google_sdk/auth/__init__.py — export service_account, oauth, resolve_credentials
- [X] T043 [US1] Verify all US1 tests pass with `uv run pytest tests/unit/test_auth/ tests/unit/test_client.py tests/contract/test_auth_contract.py -v`

**Checkpoint**: Authentication fully functional — OAuth flow, service accounts, ADC, credential resolution chain, token caching/refresh, client initialization all working. SDK can make authenticated requests.

---

## Phase 4: User Story 2 — Manage Google Drive Files (Priority: P1)

**Goal**: Developer lists, searches, uploads, downloads, and manages files/permissions in Google Drive through typed methods.

**Independent Test**: Upload a file → list files confirms it appears → download it → verify content integrity → manage permissions.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T044 [P] [US2] Write unit tests for Drive models in tests/unit/test_services/test_drive/test_models.py — test File, Folder, Permission, UploadProgress model creation, alias mapping (mimeType→mime_type, createdTime→created_time), extra field acceptance, Folder default mime_type
- [X] T045 [P] [US2] Write unit tests for DriveService in tests/unit/test_services/test_drive/test_client.py using respx — test list_files (with q, pagination), get_file, create_file (simple upload <5MB), create_file (resumable >=5MB), update_file, delete_file, download_file, export_file, copy_file, move_file, create_folder, list_permissions, create_permission, delete_permission
- [X] T046 [P] [US2] Write unit tests for ResumableUpload in tests/unit/test_services/test_drive/test_uploads.py using respx — test initiate session, chunk upload with Content-Range, 308 resume handling, progress callback, completion on 200/201, resume from interruption
- [X] T047 [P] [US2] Write contract tests for DriveService in tests/contract/test_drive_contract.py — verify method signatures match contracts/public-api.md DriveService section

### Implementation for User Story 2

- [X] T048 [P] [US2] Implement Drive models in src/google_sdk/services/drive/models.py per data-model.md — File (extending BaseResource), Folder (extending File with default mime_type), Permission, UploadProgress
- [X] T049 [US2] Implement ResumableUpload handler in src/google_sdk/services/drive/uploads.py per research.md R8 — initiate session URI, upload 8 MiB chunks with Content-Range, handle 308 resume, progress callback, auto-select simple vs resumable at 5 MB threshold
- [X] T050 [US2] Implement DriveService in src/google_sdk/services/drive/client.py — all methods per contracts/public-api.md: list_files (returns PageIterator[File]), get_file, create_file (delegates to simple or resumable upload), update_file, delete_file, download_file, export_file, copy_file, move_file, create_folder, list_permissions, create_permission, delete_permission
- [X] T051 [US2] Wire up Drive service exports in src/google_sdk/services/drive/__init__.py and register with service registry
- [X] T052 [US2] Verify all US2 tests pass with `uv run pytest tests/unit/test_services/test_drive/ tests/contract/test_drive_contract.py -v`

**Checkpoint**: Drive fully functional — file CRUD, uploads (simple + resumable with progress), downloads, exports, permission management all working.

---

## Phase 5: User Story 5 — Sync/Async Dual Support (Priority: P2)

**Goal**: Both sync and async clients expose identical API surfaces via manual shared-base implementations.

**Independent Test**: Perform same operation (list Drive files) via sync and async client → verify identical results and behavior.

### Tests for User Story 5

- [X] T053 [P] [US5] Write unit tests for sync/async parity in tests/unit/test_sync_async_parity.py — test that GoogleClient.drive.list_files() and AsyncGoogleClient.drive.list_files() return equivalent results using respx mocks, test context manager protocols (__enter__ vs __aenter__), test sync PageIterator (__iter__/__next__) mirrors async behavior

### Implementation for User Story 5

- [X] T054 [US5] Verify sync PageIterator in src/google_sdk/_pagination.py has __iter__/__next__ that mirrors AsyncPageIterator behavior using sync transport (implementation started in foundational T020, finalized here with sync variant)
- [X] T055 [US5] Verify sync/async parity tests pass with `uv run pytest tests/unit/test_sync_async_parity.py -v`

**Checkpoint**: Both sync and async clients fully functional with identical behavior.

---

## Phase 6: User Story 3 — Manage Google Calendar Events (Priority: P2)

**Goal**: Developer creates, reads, updates, and deletes calendar events with support for recurring events, attendees, and free/busy queries.

**Independent Test**: Create an event → retrieve it → update it → delete it → query free/busy.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T056 [P] [US3] Write unit tests for Calendar models in tests/unit/test_services/test_calendar/test_models.py — test Calendar, Event, EventDateTime, Attendee, EventPerson, EventReminders, ReminderOverride, ConferenceData, EntryPoint, ConferenceSolution, FreeBusyRequest, FreeBusyResponse, FreeBusyCalendar, TimePeriod model creation and alias mapping
- [X] T057 [P] [US3] Write unit tests for CalendarService in tests/unit/test_services/test_calendar/test_client.py using respx — test list_calendars, get_calendar, create_calendar, update_calendar, delete_calendar, list_events (with time_min/max, q, pagination), get_event, create_event, quick_add, update_event, delete_event, freebusy
- [X] T058 [P] [US3] Write contract tests for CalendarService in tests/contract/test_calendar_contract.py — verify method signatures match contracts/public-api.md CalendarService section

### Implementation for User Story 3

- [X] T059 [P] [US3] Implement Calendar models in src/google_sdk/services/calendar/models.py per data-model.md — Calendar, Event, EventDateTime, Attendee, EventPerson, EventReminders, ReminderOverride, ConferenceData, EntryPoint, ConferenceSolution, FreeBusyRequest, FreeBusyResponse, FreeBusyCalendar, TimePeriod
- [X] T060 [US3] Implement CalendarService in src/google_sdk/services/calendar/client.py — all methods per contracts/public-api.md: list_calendars, get_calendar, create_calendar, update_calendar, delete_calendar, list_events (returns PageIterator[Event]), get_event, create_event, quick_add, update_event, delete_event, freebusy
- [X] T061 [US3] Wire up Calendar service exports in src/google_sdk/services/calendar/__init__.py and register with service registry
- [X] T062 [US3] Verify all US3 tests pass with `uv run pytest tests/unit/test_services/test_calendar/ tests/contract/test_calendar_contract.py -v`

**Checkpoint**: Calendar fully functional — calendar CRUD, event CRUD, recurring events, attendees, free/busy queries all working.

---

## Phase 7: User Story 4 — Manage Google Meet Meetings (Priority: P3)

**Goal**: Developer creates meeting spaces, generates meeting links, and retrieves participant and recording information.

**Independent Test**: Create a meeting space → retrieve details → get join link.

### Tests for User Story 4

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T063 [P] [US4] Write unit tests for Meet models in tests/unit/test_services/test_meet/test_models.py — test Space, SpaceConfig, Participant, SignInUser, AnonymousUser, PhoneUser, ParticipantSession, Recording, DriveDestination model creation and alias mapping
- [X] T064 [P] [US4] Write unit tests for MeetService in tests/unit/test_services/test_meet/test_client.py using respx — test create_space, get_space, update_space, end_active_conference, list_participants, get_participant, list_participant_sessions, list_recordings, get_recording
- [X] T065 [P] [US4] Write contract tests for MeetService in tests/contract/test_meet_contract.py — verify method signatures match contracts/public-api.md MeetService section

### Implementation for User Story 4

- [X] T066 [P] [US4] Implement Meet models in src/google_sdk/services/meet/models.py per data-model.md — Space, SpaceConfig, Participant, SignInUser, AnonymousUser, PhoneUser, ParticipantSession, Recording, DriveDestination
- [X] T067 [US4] Implement MeetService in src/google_sdk/services/meet/client.py — all methods per contracts/public-api.md: create_space, get_space, update_space, end_active_conference, list_participants, get_participant, list_participant_sessions, list_recordings, get_recording
- [X] T068 [US4] Wire up Meet service exports in src/google_sdk/services/meet/__init__.py and register with service registry
- [X] T069 [US4] Verify all US4 tests pass with `uv run pytest tests/unit/test_services/test_meet/ tests/contract/test_meet_contract.py -v`

**Checkpoint**: Meet fully functional — space creation, participant queries, recording access all working.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T070 [P] Implement structured logging with per-component loggers in src/google_sdk/_transport/async_transport.py and src/google_sdk/auth/oauth.py — logger hierarchy google_sdk.auth, google_sdk.transport, google_sdk.retry, google_sdk.services.{drive,calendar,meet} per contracts/public-api.md, credential redaction in transport logger, optional JSON formatter per SDKConfig.log_format
- [X] T071 [P] Add docstrings with usage examples to all public modules: src/google_sdk/__init__.py, src/google_sdk/auth/__init__.py, all service client.py files, src/google_sdk/exceptions.py per Constitution IV
- [X] T072 [P] Write integration tests with VCR.py cassettes in tests/integration/ — record and replay full auth → list files → upload → download flow, filter sensitive headers (authorization, cookie) and query params (access_token) per research.md R9
- [X] T073 [P] Create test factories in tests/factories.py — factory functions for all Pydantic models (make_file, make_event, make_space, etc.) with sensible defaults and easy overrides per research report
- [X] T074 [P] Create transport overhead benchmark in tests/benchmarks/bench_transport_overhead.py — measure SDK round-trip vs raw httpx round-trip for 100 requests, assert overhead < 2x per SC-002
- [X] T075 [P] Create pagination memory benchmark in tests/benchmarks/bench_pagination_memory.py — iterate 100 pages, measure peak memory per page stays constant (no growth beyond current page data) per SC-004
- [X] T076 Run full test suite with `uv run pytest --tb=short -v` and verify 90%+ coverage with `uv run pytest --cov=google_sdk --cov-report=term-missing`
- [X] T077 Run linting with `uv run ruff check src/ tests/` and formatting with `uv run ruff format src/ tests/`, fix any issues
- [X] T078 Validate quickstart.md code examples compile and type-check by extracting snippets and running `uv run python -c "..."` for import verification

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 Auth (Phase 3)**: Depends on Foundational — BLOCKS US2, US3, US4 (need authenticated client)
- **US2 Drive (Phase 4)**: Depends on US1 (needs working client + auth)
- **US5 Sync/Async (Phase 5)**: Depends on US2 (needs at least one service to validate parity)
- **US3 Calendar (Phase 6)**: Depends on US1 (can run in parallel with US2/US4)
- **US4 Meet (Phase 7)**: Depends on US1 (can run in parallel with US2/US3)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 Auth (P1)**: Depends on Foundational — MUST complete first (all other stories need auth)
- **US2 Drive (P1)**: Depends on US1 — can run in parallel with US3, US4
- **US3 Calendar (P2)**: Depends on US1 — can run in parallel with US2, US4
- **US4 Meet (P3)**: Depends on US1 — can run in parallel with US2, US3
- **US5 Sync/Async (P2)**: Depends on US2 — needs a working service to validate

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD per Constitution II)
- Models before services
- Services before wiring/exports
- Verification step at end of each story

### Parallel Opportunities

- T003, T004, T005 can run in parallel (Phase 1)
- T006–T011 can all run in parallel (Phase 2 tests)
- T012–T015, T023, T024 can run in parallel (Phase 2 implementation — different files)
- T026–T032 can all run in parallel (US1 tests)
- T033, T035 can run in parallel (US1 token store implementations)
- T044–T047 can all run in parallel (US2 tests)
- T048 can run in parallel with T049 (US2 models + uploads)
- After US1 completes: US2, US3, US4 can proceed in parallel
- T056–T058 can all run in parallel (US3 tests)
- T063–T065 can all run in parallel (US4 tests)
- T070–T075 can all run in parallel (Polish)

---

## Parallel Example: User Story 2 (Drive)

```bash
# Launch all US2 tests in parallel (TDD - write first, must fail):
Task: "Unit tests for Drive models in tests/unit/test_services/test_drive/test_models.py"
Task: "Unit tests for DriveService in tests/unit/test_services/test_drive/test_client.py"
Task: "Unit tests for ResumableUpload in tests/unit/test_services/test_drive/test_uploads.py"
Task: "Contract tests in tests/contract/test_drive_contract.py"

# Then launch models in parallel:
Task: "Drive models in src/google_sdk/services/drive/models.py"
Task: "ResumableUpload in src/google_sdk/services/drive/uploads.py"

# Then sequential (depends on models):
Task: "DriveService in src/google_sdk/services/drive/client.py"
Task: "Wire up exports in src/google_sdk/services/drive/__init__.py"
```

---

## Implementation Strategy

### MVP First (US1 Auth + US2 Drive)

1. Complete Phase 1: Setup (T001–T005)
2. Complete Phase 2: Foundational (T006–T025)
3. Complete Phase 3: US1 Auth (T026–T043)
4. Complete Phase 4: US2 Drive (T044–T052)
5. **STOP and VALIDATE**: Authenticated client can list/upload/download Drive files
6. Deploy/demo if ready — this is a usable SDK

### Incremental Delivery

1. Setup + Foundational → Core infrastructure ready
2. Add US1 Auth → Authenticate with Google (MVP foundation)
3. Add US2 Drive → Full Drive file management (MVP!)
4. Add US5 Sync/Async → Both calling patterns validated
5. Add US3 Calendar → Calendar event management
6. Add US4 Meet → Meeting space management
7. Polish → Logging, docs, benchmarks, coverage, linting

### Parallel Team Strategy

With multiple developers after US1 completes:
- Developer A: US2 Drive
- Developer B: US3 Calendar
- Developer C: US4 Meet
- Then: US5 Sync/Async validation (needs at least one service)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- TDD is mandatory (Constitution II) — write failing tests before implementation
- All commands run via `uv run` (package manager requirement)
- Commit after each task or logical group using Conventional Commits
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
