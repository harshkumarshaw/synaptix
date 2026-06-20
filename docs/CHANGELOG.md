# Changelog — Synaptix

All notable changes to this project are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/).
This project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-06-20

### Added — Session 1 (Phase 1A Foundation Scaffold)

**Environment**
- Python 3.12.13 installed via `uv` — pinned in `.python-version`
- Root `pyproject.toml` with monorepo config, ruff, black, mypy, pytest settings
- `uv` 0.11.23 installed as Python package manager
- Git repository initialized (`main` branch)

**packages/shared — Shared Library**
- `logging.py` — Structured logger using structlog (all services must use this, no print())
- `errors.py` — Full SynaptixError domain error hierarchy (30+ error classes with SNX-XXX-NNN codes)
- `db/base.py` — SQLAlchemy 2.0 declarative bases: `TenantScopedBase`, `GlobalBase`, `TimestampMixin`, `SoftDeleteMixin`
- `db/session.py` — Async session factory + `set_tenant_context()` for Row Level Security
- `auth/tenant_context.py` — `TenantContextMiddleware` + `@require_tenant_context` decorator
- `auth/jwt.py` — JWT create/decode with MFA role enforcement
- `auth/dependencies.py` — `get_current_user` + `require_roles()` FastAPI dependencies

**services/snx-auth — Auth Service Scaffold**
- FastAPI app with lifespan manager, CORS, TenantContextMiddleware, domain error handlers
- `config.py` — pydantic-settings Settings class (all env vars, no hardcoding)
- `routers/auth.py` — All auth endpoints: login, OTP request/verify, token refresh, MFA, /me, logout
- `schemas/auth.py` — Pydantic v2 request/response models
- `services/auth_service.py` — Business logic stub with typed method signatures and TODOs

**Database Migrations**
- `alembic.ini` — Monorepo single migration chain (ADR-004)
- `services/_migrations/env.py` — Async Alembic env with RLS support
- Migration `20260620_0001` — Foundation tables: tenants, users, roles, user_roles, audit_log
  - Full RLS policies on all tenant-scoped tables
  - Append-only audit_log with trigger enforcement
  - Partitioned audit_log (2026, 2027 partitions)
  - JMN seed tenant + 13 system roles

**Tests**
- `tests/conftest.py` — Shared pytest fixtures
- `tests/unit/test_jwt_utils.py` — 20 JWT unit tests (all PASSING)
- `tests/compliance/test_attendance_thresholds.py` — 23 NMC compliance stubs (skipped pending Phase 2 implementation)

## [0.0.1] - 2026-06-18

### Added
- Project scaffolding
- AGENTS.md with non-negotiable rules
- AOIP_MASTER_SPEC_v5.md (definitive specification)
- 12 specialist agent specifications
- 5 convention files
- Test framework (COVERAGE_MANIFEST.yaml, NMC_COMPLIANCE_TESTS.md, EDGE_CASES.md)
- Documentation templates
- Local development environment (docker-compose)
- Pre-commit hooks
