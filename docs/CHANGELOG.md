# Changelog — Synaptix

All notable changes to this project are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/).
This project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added — Session 9 (2026-06-30) — Electives A-08 Backend Implementation

**COVERAGE_MANIFEST**
- Added ELEC-001..009 (critical), ELEC-NMC-001..004 (compliance), ELEC-E001..007 (edge cases)

**Migration**
- `20260630_0014_add_elective_allocation_runs.py`: adds `elective_allocation_runs` table (ADR-034 audit trail), adds `allocation_run_id` + `allocation_method` to `elective_allocations`, adds `submitted_at` to `student_elective_preferences`. Full upgrade/downgrade path.

**SQLAlchemy Models** (`services/snx-logbook/app/models/electives.py`)
- Added `ElectiveAllocationRun` model (audit run table per ADR-034)
- Added `submitted_at`, `allocation_run_id`, `allocation_method` to existing models

**Pydantic v2 Schemas** (`services/snx-logbook/app/schemas/electives.py`)
- `ElectiveCreate`, `ElectiveResponse`, `PreferencesSubmitRequest`, `PreferenceItem`, `PreferenceResponse`, `AllocationRunRequest`, `AllocationRunResponse`, `AllocationResponse`
- All use `ConfigDict(from_attributes=True)`; cross-field rules via `@model_validator(mode='after')`

**ElectiveService** (`services/snx-logbook/app/services/elective_service.py`)
- `create_elective()`, `submit_preferences()` (full-block replace), `get_student_preferences()`, `run_allocation()` (FCFS + Ranked + dry-run + realloc), `withdraw_allocation()`
- Deterministic tie-breaking via SHA-256(student_id || run_id)
- Row-level `FOR UPDATE NOWAIT` locking + 30s statement timeout
- Audit log writes on all mutating operations

**API Router** (`services/snx-logbook/app/routers/electives.py`)
- 6 endpoints: create, submit preferences, get preferences, run allocation, get allocations, withdraw
- Registered in `main.py` under `/api/v1`

**Test Stubs Created**
- `tests/unit/electives/test_elective_service.py` — 9 tests; 6 passing, 3 xfail (honest deferral to integration)
- `tests/integration/test_electives.py` — 7 xfail integration stubs (ELEC-003..009 minus 008)
- `tests/compliance/test_elective_compliance.py` — 4 xfail NMC compliance stubs

### Added — Session 7 (DevOps Validation & Phase 2 Scaffold Fixes)

**DevOps & CI/CD Pipeline**
- Upgraded GitHub Actions Workflow (`.github/workflows/ci.yml`) to enforce Node 24 (`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true`) and upgraded `codecov/codecov-action` to `@v5`.
- Resolved 43 Python Ruff linter errors (mostly unused imports, Yoda conditions, and assertions) and ran Black formatter over the entire codebase to maintain strict formatting quality.

**Database schema & Models**
- Added missing `subject_code` column to the `Course` SQLAlchemy model in `services/snx-academic/app/models/course.py` with an auto-population initializer to split from the course code (e.g. `"ANAT-101"` -> `"ANAT"`).
- Applied all database migrations (migrations 0011 to 0013) to the test database on port `5436`.
- Configured `tests/conftest.py` table truncation list to include Phase 2 tables, maintaining test isolation.

**Integration Tests Fixes**
- Fixed raw SQL course and tenant insert queries in integration tests to align with the actual database schema (replacing outdated columns like `plan` and `program_type`).
- Corrected student and batch seeding helper functions (`_seed_student`, `_seed_batch_and_student`) in `test_leave.py` and `test_attendance.py` to generate unique roll numbers and emails, preventing unique key conflicts.
- Updated `LeaveService` test instantiations to use correct `user_id` as the actor ID instead of `student_id` (fixing foreign key constraint violations on the `audit_log` table).
- Verified that all 34 Academic and 5 Leave integration tests pass cleanly and run successfully.

### Fixed — Session 6 (GitHub Actions CI Pipeline Repair)

**Linting & Formatting**
- Fixed Python syntax error in `services/snx-logbook/app/routers/logbook.py`: moved `phase: Optional[str] = None` parameter after non-default `Annotated[...]` parameters.
- Migrated `[tool.ruff]` linter configuration from deprecated top-level keys to `[tool.ruff.lint]` / `[tool.ruff.lint.per-file-ignores]`.
- Added comprehensive ruff ignore rules for FastAPI idioms (`ARG001/002`, `B008`, `B904`, `PLC0415`, `PLR2004`, `PLW0603`, `SIM102`, `E501`) and per-file ignores for `tests/**`, `**/schemas/**`, `scripts/**`.
- Formatted 88 Python files with Black; all 154 files now clean.
- Ruff: 0 errors. Black: 0 diffs.

**CI Workflow**
- Rewrote `unit-tests` job in `.github/workflows/ci.yml` to run each microservice's unit tests with its own isolated `PYTHONPATH` (resolving `ModuleNotFoundError: No module named 'app'` on the CI runner).
- Used `--cov-append` to accumulate coverage across all four test passes; coverage threshold check runs only on the final step.
- Local verification: 29/29 unit tests passing, total coverage **83.67%** (threshold 80%) ✓.

### Added — Session 5 (Phase 1B Calendar & Planning Redesign & Fixes)

**Database Migrations & Schema Standards**
- Corrected database migration `20260620_0009_phase1b_academic_tables` by adding standard `id` (primary key), `created_at`, `updated_at`, and `deleted_at` columns to `event_courses`, `event_faculty`, and `session_faculty` join tables to conform to `AGENTS.md` SQL conventions.

**Services & Models**
- Removed `primary_key=True` from foreign key references in `EventFaculty`, `EventCourse`, and `SessionFaculty` models to correctly inherit the single primary key `id` from `TenantScopedBase`.
- Updated code validation pattern in `LessonPlanCreate` schema to allow dots/periods (e.g., `"AN-1.1"`) so that standard CBME competency codes are accepted.
- Updated `submit_for_approval` in `LessonPlanService` to use `"lesson_plan_approval"` as the workflow entity type to satisfy the `chk_workflow_instances_entity_type` database check constraint.
- Added `Tenant` model stub to `snx-logbook` models package to allow resolution of the global `tenants` table foreign key inside `TenantScopedBase`.

**Test Tooling & Infrastructure**
- Updated `tests/conftest.py` `db_session` fixture to configure the SQLAlchemy async engine with `NullPool` for testing. This resolves socket GC `ResourceWarning` and unclosed event loop `RuntimeError` leaks when running multiple test suites on Windows/Proactor loop.
- Added session-scoped `cleanup_database_engine` autouse fixture to `tests/conftest.py` ensuring connection pool/engine resources are disposed of cleanly.
- Updated `tests/unit/academic/test_integration_sessions.py` to expect `pydantic.ValidationError` directly on schema construction rather than at the service boundary.
- Verified all unit, integration, security, and NMC compliance stub test suites run successfully (all 39 tests passing).

### Added — Session 4 (Workflow Engine, MDM, Assets Scaffolding & Fixes)

**Services & Modules**
- Scaffolded `snx-workflow` service on port `8010` for F-02 Master Data Management, F-03 Workflow Engine, and F-07 Digital Asset Repository.
- Added SQLAlchemy async services: `MasterDataService`, `WorkflowService`, and `AssetService` supporting LocalStorage file writing.

**Database Migrations**
- Added migration `20260620_0006_master_data_tables.py` for `master_data_entities` table.
- Added migration `20260620_0007_workflow_engine_tables.py` for `workflow_definitions`, `workflow_instances`, and `workflow_transitions` tables. Includes AFTER INSERT history trigger `trg_workflow_transitions_insert`.
- Added migration `20260620_0008_digital_assets_tables.py` for `digital_assets` table.

**Tests & Test Tooling**
- Modified `tests/conftest.py` db_session fixture to run table truncation (with `DISABLE TRIGGER` safety for append-only logs) before every test to enforce database test isolation.
- Created `tests/unit/workflow/test_definition_versioning.py` for version progression tests.
- Created `tests/unit/workflow/test_transitions.py` for role/next_steps transition checks.
- Created `tests/integration/workflow/test_full_lifecycle.py` checking end-to-end steps and JSONB trigger-based history log synchronization.
- Created `tests/security/workflow/test_tenant_isolation.py` verifying RLS row isolation.
- Created `tests/unit/mdm/test_master_data_service.py` verifying MDM CRUD and sort orders.
- Created `tests/unit/assets/test_asset_service.py` verifying file uploads/downloads with LocalStorage.

### Fixed — Session 4
- Corrected workflow transition check in `submit_transition` to block state progression to terminal steps (`approved`/`rejected`/`cancelled`) unless explicitly defined as permitted in definition's `next_steps`.
- Fixed `NullViolationError` on audit log writing by executing `db.flush()` on asset uploads to populate autogenerated UUID primary keys before passing them to the audit log writer.

### Added — Session 3 (Academic & Institutional Foundations)

- Added migration `20260620_0005_academic_and_institutional_tables.py` for departments, faculty, courses, batches, sections, students, timetable slots, and timetable entries.
- Scaffolded `snx-academic` service on port `8002`.
- Scaffolded `snx-institution` service on port `8007`.
- Created integration tests `test_academic_service.py` and `test_institution_service.py`.

### Fixed — Session 2 (Auth Integration Test and CryptContext Fixes)

- Removed invalid `pwd_context` definition in `auth_service.py` to prevent `NameError`.
- Updated test setup in `test_auth_service.py` to use native `bcrypt` library directly.
- Refactored `db_session` fixture in `tests/conftest.py` to yield session from factory, avoiding `get_session_with_tenant` context transaction wrapper, which prevented multiple commits inside tests.
- Switched test role from `faculty` to `principal` to properly verify MFA-required flows in `test_auth_service.py`.

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
