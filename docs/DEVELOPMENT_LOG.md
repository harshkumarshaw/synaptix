# Development Log

Chronological record of all development sessions.

## 2026-06-27 — Phase 2 Electives & DOAP Task Coordination (Session 8)
**Agent:** Orchestrator (00)
**Duration:** ~10 mins
**Focus:** Orchestrate remaining Phase 2 tasks for Electives and DOAP session records.
- Decomposed Phase 2 tasks into schema, service, router, and testing layers.
- Assigned tasks to Backend (02), Testing (06), and NMC Compliance (11) agents in HANDOFF_NOTES.md.
- Created implementation plan and task list artifacts for the execution phase.

## 2026-06-27 — DevOps Checks & Integration Test Fixes (Session 7)
**Agent:** DevOps (09)
**Duration:** ~45 mins
**Focus:** Fix linter, formatting, test database migrations, and integration test seeding issues.
- Fixed 43 Ruff lint errors and reformatted 13 files using Black.
- Applied database migrations to local test database on port 5436.
- Added `subject_code` to `Course` model and updated raw SQL inserts in test files to match Phase 2 schema.
- Fixed `_seed_tenant`, `_seed_event`, `_seed_student`, and `_seed_batch_and_student` helpers in `test_leave.py` and `test_attendance.py` to use correct column names and unique roll numbers.
- Verified all 34 Academic and 5 Leave integration tests pass cleanly.

## 2026-06-20 — CI/CD Pipeline & Ruff Linter Fixes (Session 6)
**Agent:** Orchestrator (00)
**Duration:** ~30 mins
**Focus:** Resolve GitHub Actions CI failures, Ruff config deprecations, and test collection issues.
- Migrated Ruff linter configuration to `[tool.ruff.lint]` block.
- Applied Black formatting to 88 files.
- Restructured CI unit-tests job with PostgreSQL services and PYTHONPATH isolation.
- Fixed pytest-asyncio and NullPool configuration for stable test runs.

## 2026-06-20 — Academic & Logbook Connection Fixes (Session 5)
**Agent:** Orchestrator (00)
**Duration:** ~64 mins
**Focus:** Resolve connection pool leaks and schema join table inconsistencies.
- Configured NullPool engine for tests to prevent Windows Proactor event loop leaks.
- Resolved parameterized `SET LOCAL` queries in tenant isolation tests.
- Normalized join table schemas for `event_courses`, `event_faculty`, and `session_faculty`.

## 2026-06-20 — Phase 1A Scaffold Completed
**Agent:** Backend (02)
**Duration:** ~31 mins (Session 4)
**Focus:** Scaffoldsnx-workflow integration tests, fix transition validation checks and asset audit log primary keys. Configure global test database truncation isolation.
- Created `test_master_data_service.py`, `test_asset_service.py`, `test_full_lifecycle.py`, and `test_tenant_isolation.py`.
- Fixed state machine transition terminal step validations.
- Verified all 30/30 tests pass.

## 2026-06-20 — Academic & Institution Scaffolding
**Agent:** Orchestrator (00) + Database (05) + Backend (02) + Testing (06) + Documentation (10)
**Duration:** ~50 mins (Session 3)
**Focus:** Scaffold academic and institution microservices, migration files, and write initial integration tests.
- Created `snx-academic` and `snx-institution` services.
- Created migration `20260620_0005`.
- Verified academic and institution integration tests pass.

## 2026-06-20 — CryptContext & Role MFA Fixes
**Agent:** Backend (02) + Testing (06)
**Duration:** ~25 mins (Session 2)
**Focus:** Debug auth service test failures.
- Resolved CryptContext `NameError`.
- Set test user roles to Principal to satisfy MFA requirements.
- Confirmed all auth tests pass.

## 2026-06-20 — Framework Setup
**Agent:** Orchestrator (00)
**Duration:** ~1h (Session 1)
**Focus:** Project structure, packages/shared, snx-auth scaffold, and alembic base migrations setup.
- Initialised monorepo packages, config, RLS policies, and database connection.

## 2026-06-18 — Framework Setup
**Agent:** Human (Sila Singh Ghosh) + Claude (Anthropic)
**Duration:** ~4 hours
**Focus:** Initial framework setup
- Project structure created
- AGENTS.md drafted with 10 commandments
- Master specification v5.0 written
- 12 agent specifications created
- Convention files (5) created
- Test framework (3 files) created
- Documentation templates initialised
