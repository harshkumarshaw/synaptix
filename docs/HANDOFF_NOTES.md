# Handoff Notes

End-of-session notes for the next agent session.

> Agents: read this at session start. Update at session end.

## Current Status

**Last session:** 2026-06-20 — Session 4 (Backend Agent 02)
**Phase:** Phase 1A — Foundation (Scaffolding Phase Complete)
**In progress:** Phase 1A service foundations and database schemas are fully in place and verified. All 30 tests (21 auth + 2 academic/institution + 7 workflow/MDM/asset) pass.

## Tasks Pending

### [TO: 09-devops] DevOps Agent
- [ ] Create `services/snx-auth/Dockerfile`
- [ ] Create `services/snx-academic/Dockerfile`
- [ ] Create `services/snx-institution/Dockerfile`
- [ ] Create `services/snx-workflow/Dockerfile` (Ensure bind-mount capability to `/app/storage/assets`)
- [ ] Create `.github/workflows/ci.yml` — GitHub Actions pipeline
  - Verify formatting and linting (black, ruff, mypy)
  - Execute test suites independently using isolated PYTHONPATH parameters for each service:
    - Auth: `PYTHONPATH=.:services/snx-auth pytest tests/integration/test_auth_service.py tests/unit/test_jwt_utils.py`
    - Academic: `PYTHONPATH=.:services/snx-academic pytest tests/integration/test_academic_service.py`
    - Institution: `PYTHONPATH=.:services/snx-institution pytest tests/integration/test_institution_service.py`
    - Workflow: `PYTHONPATH=.:services/snx-workflow pytest tests/unit/workflow/ tests/integration/workflow/ tests/security/workflow/ tests/unit/mdm/ tests/unit/assets/`
  - Block merge if any compliance or regression tests fail
- [ ] Set up pre-commit hook: copy `scripts/pre-commit-hook.ps1` content to `.git/hooks/pre-commit`

### [TO: Human — Harsh]
- [ ] Install Flutter (Deferred to Phase 2)

## Blockers

- None

## Important Reminders

- **Test Database Isolation:** The database isolation is handled by table truncation in `db_session` conftest fixture (disabling the `trg_audit_log_no_update` trigger on the append-only table prior to truncation).
- **Run pytest Individually:** Do not run pytest globally due to `app` namespace conflicts; run tests for each service with its corresponding `PYTHONPATH`.
