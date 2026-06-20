# Handoff Notes

End-of-session notes for the next agent session.

> Agents: read this at session start. Update at session end.

## Current Status

**Last session:** 2026-06-20 — Session 6 (Orchestrator Agent 00)  
**Phase:** Phase 1B — Calendar & Planning (Backend Development & Testing Complete)  
**Status:** GitHub Actions CI pipeline fixes committed and pushed to `chore/devops-scaffolding`. Awaiting verification that all 5 jobs pass on the remote runner.

## What Was Fixed (Session 6)

- **Syntax error** in `services/snx-logbook/app/routers/logbook.py` (parameter order)
- **Ruff linter config** migrated from deprecated top-level to `[tool.ruff.lint]` in `pyproject.toml`
- **Ruff linter rules** expanded to ignore FastAPI idioms (`ARG001/002`, `B008`, `B904`, `E501`, `PLC0415`, `PLR2004`, `PLW0603`, `SIM102`) globally; per-file ignores for tests and scripts
- **Black formatting** applied to 88 files
- **CI `unit-tests` job** rewritten to run each microservice with its own `PYTHONPATH` and `--cov-append`
- Local verification: 29/29 tests pass, 83.67% coverage ✓

## Tasks Pending

### [TO: Human — Harsh]
- [ ] Verify GitHub Actions run green on all 5 jobs after this push

### [TO: 09-devops] DevOps Agent
- [ ] Create `services/snx-academic/Dockerfile`
- [ ] Create `services/snx-institution/Dockerfile`
- [ ] Create `services/snx-workflow/Dockerfile`
- [ ] Create `services/snx-logbook/Dockerfile` (port 8006)
- [ ] Configure local pre-commit hook: copy `scripts/pre-commit-hook.ps1` to `.git/hooks/pre-commit`

### [TO: Human — Harsh]
- [ ] Install Flutter (Deferred to Phase 2)

## Blockers

- None

## Important Reminders

- **NullPool for Tests:** `conftest.py` configures `sqlalchemy.pool.NullPool` during test runs to avoid event loop closing issues on Windows.
- **Run pytest per service:** Always set `PYTHONPATH` to include the specific service directory when running that service's tests (e.g., `PYTHONPATH=.:services/snx-academic`).
- **Ruff config:** All ruff settings are now under `[tool.ruff.lint]` — the top-level `select`/`ignore` keys were deprecated and have been migrated.

