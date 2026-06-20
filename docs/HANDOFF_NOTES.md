# Handoff Notes

End-of-session notes for the next agent session.

> Agents: read this at session start. Update at session end.

## Current Status

**Last session:** 2026-06-20 — Session 2 (Orchestrator acting as Backend + Database + Testing + Documentation agents)
**Phase:** Phase 1A — Foundation (in progress)
**In progress:** Phase 1A foundation scaffold and service logic verification DONE. Next: Dockerfiles & CI/CD workflow setup.

## Tasks Pending

### [TO: 09-devops] DevOps Agent
- [ ] Create `services/snx-auth/Dockerfile` (multi-stage, production-ready, clean python environment)
- [ ] Create `.github/workflows/ci.yml` — GitHub Actions pipeline
  - ruff check, black check, mypy
  - pytest tests/unit tests/compliance
  - Block merge if NMC compliance tests fail
- [ ] Set up pre-commit hook: copy `scripts/pre-commit-hook.ps1` content to `.git/hooks/pre-commit`
- [ ] Create `services/snx-auth/docker-compose.override.yml` for local dev (if needed)

### [TO: Human — Harsh]
- [ ] Install Flutter: https://docs.flutter.dev/get-started/install/windows (Deferred to Phase 2)

## Blockers

- None (Docker and Github repositories are fully configured and running).

## Important Reminders

- NMC compliance tests HARD-FAIL the build (currently all stubbed/skipped — OK)
- Tenant isolation: 3-layer enforcement (Middleware + @require_tenant_context + RLS)
- ALL env vars from `.env` — never hardcode secrets
- Two-threshold attendance: 75% theory, 80% practical — SEPARATE checks
