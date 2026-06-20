# Handoff Notes

End-of-session notes for the next agent session.

> Agents: read this at session start. Update at session end.

## Current Status

**Last session:** 2026-06-20 — Session 5 (Orchestrator Agent 00)
**Phase:** Phase 1B — Calendar & Planning (Backend Development & Testing Complete)
**In progress:** Phase 1B service foundations and database schemas are fully in place and verified. All 39 tests (21 auth + 2 academic/institution + 7 workflow/MDM/asset + 6 academic-planning + 2 logbook-service + 1 compliance stubs) pass cleanly.

## Tasks Pending

### [TO: 09-devops] DevOps Agent
- [ ] Create `services/snx-auth/Dockerfile` (if not done)
- [ ] Create `services/snx-academic/Dockerfile` (if not done)
- [ ] Create `services/snx-institution/Dockerfile` (if not done)
- [ ] Create `services/snx-workflow/Dockerfile` (if not done)
- [ ] Create `services/snx-logbook/Dockerfile` (Ensure port 8006 mapping)
- [ ] Create `.github/workflows/ci.yml` — GitHub Actions pipeline
  - Verify formatting and linting (black, ruff, mypy)
  - Execute test suites independently using isolated PYTHONPATH parameters for each service:
    - Auth: `PYTHONPATH=.:services/snx-auth pytest tests/integration/test_auth_service.py tests/unit/test_jwt_utils.py`
    - Academic: `PYTHONPATH=.:services/snx-academic pytest tests/unit/academic/ tests/integration/test_calendar_engine.py tests/integration/test_lesson_plan_service.py tests/security/academic/test_tenant_isolation.py`
    - Institution: `PYTHONPATH=.:services/snx-institution pytest tests/integration/test_institution_service.py`
    - Workflow: `PYTHONPATH=.:services/snx-workflow pytest tests/unit/workflow/ tests/integration/workflow/ tests/security/workflow/ tests/unit/mdm/ tests/unit/assets/`
    - Logbook: `PYTHONPATH=.:services/snx-logbook pytest tests/unit/logbook/test_aetcom_uniqueness.py tests/integration/test_logbook_service.py`
  - Block merge if any compliance or regression tests fail
- [ ] Set up pre-commit hook: copy `scripts/pre-commit-hook.ps1` content to `.git/hooks/pre-commit`

### [TO: Human — Harsh]
- [ ] Install Flutter (Deferred to Phase 2)

## Blockers

- None

## Important Reminders

- **NullPool for Tests:** To avoid event loop closing issues on Windows, `conftest.py` configures the database connection pool as `sqlalchemy.pool.NullPool` during test runs, and cleanly disposes of the engine in a session-scoped teardown.
- **Run pytest Individually:** Do not run pytest globally due to `app` namespace conflicts; run tests for each service with its corresponding `PYTHONPATH`.
