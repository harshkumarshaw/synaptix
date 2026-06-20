# Handoff Notes

End-of-session notes for the next agent session.

> Agents: read this at session start. Update at session end.

## Current Status

**Last session:** 2026-06-20 — Session 6 (Orchestrator Agent 00)
**Phase:** Phase 1B — Calendar & Planning (Backend Development & Testing Complete)
**Status:** ALL 5 GitHub Actions CI jobs PASS. Both `itdept-JMN/synaptix` and `harshkumarshaw/synaptix` repos are in sync at commit `1c13d10`.

## What Was Fixed (Session 6 — Full CI Green)

- **Syntax error** in `services/snx-logbook/app/routers/logbook.py`
- **Ruff linter config** migrated from deprecated top-level to `[tool.ruff.lint]` in `pyproject.toml`
- **Black formatting** applied to 88 files
- **CI `unit-tests` job** rewritten:
  - `postgres:16` service container (port 5436:5432) with health check
  - `alembic upgrade head` migration step before tests
  - Per-service PYTHONPATH isolation with `--cov-append`
- **`tests/conftest.py`** `db_session` fixture:
  - Fresh `NullPool` engine per test (prevents cross-test connection reuse)
  - Changed `@pytest_asyncio.fixture` to plain `async @pytest.fixture` (anyio loop compatibility)
- **`pytest-asyncio==0.23.8` pinned** in `pyproject.toml` and `ci.yml`:
  - `pytest-asyncio 1.4.0` introduced breaking `asyncio_default_test_loop_scope=function` default
  - On Linux SelectorEventLoop this causes `RuntimeError: Future attached to a different loop` with asyncpg
  - Stable 0.23.8 uses shared session loop — the SQLAlchemy-recommended approach
- Local: 29/29 tests pass, 83.67% coverage
- CI run `27871964773`: Unit Tests OK, Lint OK, NMC Compliance OK, Secret Scan OK, Docker Build OK

## Tasks Pending

### [TO: 09-devops] DevOps Agent
- [ ] Create `services/snx-academic/Dockerfile`
- [ ] Create `services/snx-institution/Dockerfile`
- [ ] Create `services/snx-workflow/Dockerfile`
- [ ] Create `services/snx-logbook/Dockerfile` (port 8006)
- [ ] Configure local pre-commit hook: copy `scripts/pre-commit-hook.ps1` to `.git/hooks/pre-commit`
- [ ] Update GitHub Actions to use `actions/checkout@v4` on Node.js 24 (currently shows Node.js 20 deprecation warnings)

### [TO: 00-orchestrator] Next Session
- [ ] Begin Phase 2 planning per `AOIP_MASTER_SPEC_v5.md`
  - Attendance Engine (two-threshold: 75% theory, 80% practical)
  - Student Portal
  - Faculty Dashboard
- [ ] Promote any shared utilities from service-level to `packages/shared/`

### [TO: Human — Harsh]
- [ ] Install Flutter (Deferred to Phase 2)

## Blockers

- None

## Important Reminders

- **pytest-asyncio PINNED:** Always use `pytest-asyncio==0.23.8`. Do NOT upgrade until the 1.4.x loop scope API stabilises.
- **NullPool for Tests:** `conftest.py` creates a fresh NullPool engine per test and disposes it at teardown.
- **Run pytest per service:** Always set `PYTHONPATH` to include the specific service directory (e.g., `PYTHONPATH=.:services/snx-academic`).
- **Ruff config:** All ruff settings are under `[tool.ruff.lint]` — top-level keys were deprecated and migrated.
- **Two repos:** `jmn` remote = `itdept-JMN/synaptix` (org), `personal` remote = `harshkumarshaw/synaptix`.
