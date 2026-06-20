# Handoff Notes

End-of-session notes for the next agent session.

> Agents: read this at session start. Update at session end.

## Current Status

**Last session:** 2026-06-20 — Session 1 (Orchestrator acting as Backend + Database agents)
**Phase:** Phase 1A — Foundation (in progress)
**In progress:** Phase 1A foundation scaffold DONE. Next: implementation of auth service + Docker setup.

## Tasks Pending

### [TO: 05-database] Database Agent
- [ ] Start Docker Desktop first: `docker compose up -d postgres`
- [ ] Run migration: `$env:PYTHONPATH="F:\Synaptix"; alembic upgrade head`
- [ ] Verify migration applied: connect to localhost:5432 (user: snx, pass: snx_dev_pass) and check tables exist
- [ ] Verify RLS policies are in place: run `SELECT tablename, policyname FROM pg_policies;`
- [ ] Create migration for `academic_years`, `programs`, `curricula` tables (Phase 1A Module A-01)

### [TO: 02-backend] Backend Agent
- [ ] Create `services/snx-auth/app/models/` directory
- [ ] Create `services/snx-auth/app/models/user.py` — SQLAlchemy User model (inheriting TenantScopedBase)
- [ ] Create `services/snx-auth/app/models/tenant.py` — SQLAlchemy Tenant model
- [ ] Implement `AuthService.login()` — bcrypt password check + DB user lookup
- [ ] Implement `AuthService.request_otp()` — OTP generation (store in DB, SMS stub)
- [ ] Implement `AuthService.verify_otp()` — OTP check + token issuance
- [ ] Add integration tests for login/OTP flows

### [TO: 09-devops] DevOps Agent
- [ ] Create `services/snx-auth/Dockerfile` (multi-stage, production-ready)
- [ ] Create `.github/workflows/ci.yml` — GitHub Actions pipeline
  - ruff check, black check, mypy
  - pytest tests/unit tests/compliance
  - Block merge if NMC compliance tests fail
- [ ] Set up pre-commit hook: copy `scripts/pre-commit-hook.ps1` content to `.git/hooks/pre-commit`
- [ ] Create `services/snx-auth/docker-compose.override.yml` for local dev

### [TO: Human — Harsh]
- [ ] **Start Docker Desktop** (required before any `docker compose` commands)
- [ ] **Create GitHub private repo** at https://github.com/new (name: `synaptix`, visibility: Private)
- [ ] Run initial commit and push:
  ```powershell
  git add .
  git commit -m "feat(foundation): Phase 1A scaffold — packages/shared + snx-auth + migrations

  Initial Phase 1A implementation including:
  - packages/shared: logging, errors, db (session + base), auth (JWT, tenant context, deps)
  - services/snx-auth: FastAPI scaffold with all auth endpoints
  - services/_migrations: foundation tables (tenants, users, roles, user_roles, audit_log) with RLS
  - tests: 20 unit tests passing, 23 NMC compliance stubs

  Co-authored-by: backend-agent <02@synaptix.local>
  Co-authored-by: database-agent <05@synaptix.local>"
  git remote add origin https://github.com/YOUR_USERNAME/synaptix.git
  git push -u origin main
  ```
- [ ] Install Flutter: https://docs.flutter.dev/get-started/install/windows

## Blockers

- Docker Desktop must be started manually before any DB work
- GitHub repo URL not yet known (user creating it)

## Important Reminders

- NMC compliance tests HARD-FAIL the build (currently all stubbed/skipped — OK)
- Tenant isolation: 3-layer enforcement (Middleware + @require_tenant_context + RLS)
- ALL env vars from `.env` — never hardcode secrets
- Two-threshold attendance: 75% theory, 80% practical — SEPARATE checks

## Cross-Agent Messages

[TO: 05-database] The migration in `services/_migrations/versions/20260620_0001_foundation_tables.py` needs to be applied with `alembic upgrade head` AFTER Docker is running. The alembic.ini is at project root.

[TO: 02-backend] The User model must inherit from `TenantScopedBase` (in `packages/shared/db/base.py`). Do NOT inherit from Base directly. The tenant_id FK is already on TenantScopedBase.

