# Tests

This directory contains four test suites with very different runtime
characteristics.

```
tests/
├── conftest.py            # global fixtures + the --integration opt-in flag
├── factories.py           # test data builders
├── unit/                  # mocked HTTP via respx (fast, default)
├── contract/              # VCR cassettes pinning request/response shape
├── integration/           # live calls to real Google APIs (opt-in)
└── benchmarks/            # ad-hoc performance scripts
```

## Quick start

```bash
uv sync --dev               # install all dev deps

uv run pytest               # unit + contract (default; ~260 tests, no creds needed)
uv run pytest tests/unit    # just unit tests
uv run ruff check .         # lint
```

Integration tests are **opt-in** and require Google credentials — they will
not run on a default `pytest` invocation.

---

## Unit tests — `tests/unit/`

- HTTP mocked via [`respx`](https://github.com/lundberg/respx)
- Fast (sub-second), deterministic, no network
- The function-scoped `sdk_config` and `mock_creds` fixtures live in the
  top-level `tests/conftest.py`

Run a single test:

```bash
uv run pytest tests/unit/test_client.py -k "test_name"
```

## Contract tests — `tests/contract/`

VCR cassettes pin the exact wire format the SDK expects from Google. They
replay recorded HTTP traffic — no live network calls. Run alongside the
unit suite by default.

## Integration tests — `tests/integration/`

These hit live Google APIs. They create real Drive files, Calendar events,
and Meet spaces in the authenticated account, then delete them in
fixtures. Treat them as destructive and only point them at a test
account / test GCP project.

### Prerequisites

**1. A dedicated GCP test project** with these APIs enabled:

- Google Drive API
- Google Calendar API
- Google Meet REST API

> Use a throwaway project. Tests create and delete real resources, and a
> dropped cleanup leaves orphaned files behind.

**2. Application Default Credentials (ADC)** — easiest local path:

```bash
gcloud auth application-default login \
  --scopes=https://www.googleapis.com/auth/drive,\
https://www.googleapis.com/auth/calendar,\
https://www.googleapis.com/auth/meetings.space.created
```

This writes credentials to
`~/.config/gcloud/application_default_credentials.json`, which
`google_sdk.auth.resolve_credentials()` discovers automatically.

**Alternative — service account file:**

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

The SDK's resolver picks this up first, before falling back to ADC.

**3. A Google Workspace account** is required for the Meet API.
Personal Gmail accounts will be auto-skipped for `test_meet.py` and
`test_workflows.py` (Meet returns 403). Drive and Calendar tests work
with both Workspace and personal accounts.

### Running

Integration tests are **gated by two layers**:

| Guard | What it checks | What happens on failure |
|-------|----------------|-------------------------|
| `--integration` flag (or `RUN_INTEGRATION_TESTS=1` env var) | The user explicitly opted in | Tests are marked skipped at collection time |
| `credentials` fixture | `resolve_credentials()` returns valid creds with required scopes | Whole integration session is skipped with a setup hint |
| `workspace_account` fixture (Meet + workflows only) | Meet API is reachable | Just those modules skip; Drive and Calendar still run |

```bash
# Run all integration tests
uv run pytest --integration tests/integration -v

# Or via env var (handy in CI)
RUN_INTEGRATION_TESTS=1 uv run pytest tests/integration -v

# Single service
uv run pytest --integration tests/integration/test_drive.py -v

# Single test
uv run pytest --integration tests/integration/test_drive.py::test_create_and_get_file -v

# Run everything (unit + contract + integration)
uv run pytest --integration
```

### Optional environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `GOOGLE_APPLICATION_CREDENTIALS` | unset | Path to a service-account JSON key |
| `RUN_INTEGRATION_TESTS` | unset | Set to `1` as an alternative to `--integration` |
| `GOOGLE_SDK_TIMEOUT` | `60` | Per-request HTTP timeout (seconds) for live tests |
| `GOOGLE_SDK_MAX_RETRIES` | `3` | Max retries for the integration-test client |

### Resource naming and cleanup

Every resource created during a test run is prefixed with
`_sdk_test_<unix_timestamp>` (the session-scoped `test_prefix` fixture).
This makes orphans easy to spot and remove if a run is interrupted before
the cleanup fixtures fire.

**Manual cleanup if needed:**

- **Drive** — search for `_sdk_test_` in your Drive UI and delete matches
- **Calendar** — look for calendars/events with `_sdk_test_` in the
  summary
- **Meet** — spaces are ephemeral; no manual cleanup needed

### Adding a new integration test

1. Create resources inside the test — no shared state across tests
2. Use the `drive_cleanup` / `calendar_cleanup` fixtures to register IDs
   for automatic teardown:
   ```python
   def test_something(client, test_prefix, drive_cleanup):
       f = client.drive.create_file(f"{test_prefix}_x.txt", content=b"...")
       drive_cleanup.append(f.id)
       ...
   ```
3. Prefix every resource name with `test_prefix`
4. Keep tests under ~30 seconds; live API calls aren't cheap

## Benchmarks — `tests/benchmarks/`

Standalone scripts, not collected by pytest. Run directly:

```bash
uv run python tests/benchmarks/bench_pagination_memory.py
uv run python tests/benchmarks/bench_transport_overhead.py
```

---

## CI notes

To run integration tests in GitHub Actions:

1. Store a service-account key as an Actions secret
2. Write it to a file and set `GOOGLE_APPLICATION_CREDENTIALS`
3. Run `RUN_INTEGRATION_TESTS=1 uv run pytest tests/integration`

Default CI for PRs should run only unit + contract (`uv run pytest`) —
they're hermetic and fast.
