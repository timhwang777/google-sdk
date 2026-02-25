<!--
  Sync Impact Report
  ==================
  Version change: 0.0.0 → 1.0.0 (MAJOR - initial ratification)
  Added principles:
    - I. Code Quality (KISS & DRY)
    - II. Test-Driven Development (NON-NEGOTIABLE)
    - III. Testing Standards
    - IV. User Experience Consistency
    - V. Security
    - VI. Performance
  Added sections:
    - Development Workflow
    - Security & Performance Standards
  Removed sections: none
  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ no changes needed
    - .specify/templates/spec-template.md ✅ no changes needed
    - .specify/templates/tasks-template.md ✅ no changes needed
  Follow-up TODOs: none
-->

# Google Service Wrapper Constitution

## Core Principles

### I. Code Quality (KISS & DRY)

- All code MUST follow the KISS principle: prefer the simplest
  solution that satisfies requirements. Complexity MUST be justified
  in PR descriptions when deviating.
- All code MUST follow the DRY principle: extract shared logic into
  reusable modules. Duplication across two or more call sites MUST
  be refactored into a single source of truth.
- Functions MUST do one thing. Maximum function length: 50 lines
  (excluding docstrings). Exceptions require justification.
- Type hints MUST be used on all public function signatures.
- Code MUST pass `ruff` linting and `ruff format` with zero warnings
  before merge.

### II. Test-Driven Development (NON-NEGOTIABLE)

- TDD is mandatory for all feature work. The Red-Green-Refactor
  cycle MUST be strictly followed:
  1. Write a failing test that defines the desired behavior.
  2. Write the minimum code to make the test pass.
  3. Refactor while keeping all tests green.
- No production code MUST be written without a corresponding
  failing test first.
- Test coverage for new code MUST be at minimum 90% line coverage.
- Tests MUST be deterministic, isolated, and fast (unit test suite
  MUST complete in under 30 seconds).

### III. Testing Standards

- Tests MUST be organized into three tiers:
  - **Unit tests** (`tests/unit/`): isolated, no I/O, no network.
  - **Integration tests** (`tests/integration/`): test component
    interactions, may use test doubles for external services.
  - **Contract tests** (`tests/contract/`): validate API contracts
    against Google service interfaces.
- All public API surfaces MUST have contract tests.
- Test names MUST follow the pattern
  `test_<unit>_<scenario>_<expected_outcome>`.
- Mocks and stubs MUST be used for external Google API calls in
  unit and integration tests. Real API calls are permitted only
  in explicitly marked end-to-end tests.

### IV. User Experience Consistency

- All public-facing APIs MUST follow a consistent naming convention:
  `snake_case` for functions and variables, `PascalCase` for classes.
- Error messages MUST be actionable: state what went wrong, why,
  and how the user can fix it.
- All public modules MUST include docstrings with usage examples.
- Breaking changes to public APIs MUST follow semantic versioning
  and include a migration guide.
- CLI interfaces (if any) MUST provide `--help` output and support
  both human-readable and JSON output formats.

### V. Security

- Credentials and secrets MUST never be hardcoded or committed.
  All secrets MUST be loaded from environment variables or a
  secrets manager.
- All user-supplied input MUST be validated and sanitized before
  use in API calls or file operations.
- Dependencies MUST be pinned to exact versions in lock files.
  Dependency updates MUST be reviewed for security advisories.
- OAuth scopes MUST follow the principle of least privilege:
  request only the minimum scopes required for each operation.
- Security-sensitive operations MUST log audit events (without
  logging sensitive data).

### VI. Performance

- API wrapper methods SHOULD support batch operations where the
  underlying Google API supports batching. Batch support MAY be
  deferred if the transport layer is designed for future extensibility
  (document deferral in plan.md).
- Network calls MUST implement retry logic with exponential
  backoff and configurable timeout values.
- Response caching SHOULD be available for read-heavy operations
  with configurable TTL. Caching MAY be deferred if the transport
  middleware architecture supports future addition without breaking
  changes (document deferral in plan.md).
- Memory usage MUST be bounded: large result sets MUST use
  pagination or streaming rather than loading all results into
  memory.
- Performance-critical paths MUST include benchmark tests in
  `tests/benchmarks/`.

## Security & Performance Standards

- OWASP Top 10 vulnerabilities MUST be considered during code
  review for any code handling external input.
- All HTTP connections MUST use TLS. Certificate validation
  MUST NOT be disabled outside of test environments.
- Rate limiting MUST be implemented to respect Google API quotas.
  Quota usage MUST be observable via logging or metrics.
- Startup time for the library MUST remain under 500ms for
  standard import and initialization.

## Development Workflow

- All changes MUST go through pull request review before merge.
- PRs MUST pass all CI checks: linting, type checking, and the
  full test suite (unit + integration + contract).
- Commit messages MUST follow Conventional Commits format
  (e.g., `feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
- Branch naming MUST follow the pattern `<type>/<short-description>`
  (e.g., `feat/sheets-batch-update`, `fix/auth-token-refresh`).
- Each PR MUST reference the associated issue or task ID.
- Constitution compliance MUST be verified as part of every
  code review. Violations MUST be flagged before approval.

## Governance

- This constitution supersedes all other development practices
  for this project. In case of conflict, the constitution wins.
- Amendments require:
  1. A written proposal documenting the change and rationale.
  2. Review and approval by at least one maintainer.
  3. A migration plan if existing code is affected.
  4. Version bump following semantic versioning (see below).
- Versioning policy:
  - MAJOR: principle removal or backward-incompatible redefinition.
  - MINOR: new principle added or existing principle materially
    expanded.
  - PATCH: wording clarification, typo fix, non-semantic change.
- Compliance review: every PR review MUST include a constitution
  compliance check. Reviewers MUST verify that new code adheres
  to all applicable principles.

**Version**: 1.1.0 | **Ratified**: 2026-02-23 | **Last Amended**: 2026-02-23
