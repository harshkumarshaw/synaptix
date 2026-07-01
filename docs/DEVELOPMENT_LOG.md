# Development Log

Chronological record of all development sessions.

## 2026-07-01 — Phase 2 Session 13 Logbook extensions & Admissions placeholder (Session 13)
**Agent:** Antigravity (Pair Programmer)
**Duration:** ~15 mins
**Focus:** Complete Logbook Phase 2 Extensions + Admissions placeholder, and write all associated unit, compliance, and integration tests to satisfy the required manifest coverage.
- Created `AdmissionApplication` model with composite foreign keys, schemas, CRUD service, router, and registered it in academic service main router.
- Fixed `WorkflowInstance` and added `WorkflowDefinition` ORM stubs in logbook service to align with the database.
- Corrected DOAP remediation workflow to use check-constraint permitted `exemption_grant` type.
- Added 24 new unit, integration, and compliance tests for Logbook and Admissions. All 119 tests pass successfully.

## 2026-07-01 — Phase 2 Session 12 Schema Gaps & Attendance Engine (Session 12)
**Agent:** Backend (02)
**Duration:** ~15 mins
**Focus:** Fix the 3 database schema gaps from `PHASE2_SCHEMA.md` using migration `0016`, enforce composite foreign key constraints, resolve all 36 attendance engine integration tests to passing, and update the pre-commit hook scripts.
- Wrote migration 0016 to resolve 3 schema gaps (primary and foreign key constraints on `attendance_summary`, trigger `trg_enforce_attendance_exemption_conflict` preventing double exemptions, default start/end dates on `internship_rotations`).
- Fixed all 36 integration tests in `test_attendance_engine.py` (added approver user inserts for exemption tests, converted UPDATE queries to ON CONFLICT DO UPDATE upserts).
- Configured pre-commit checks in `scripts/pre-commit-hook.ps1` to run linting, formatting, type checking, and coverage manifest verification scoped to modified files and modules, allowing commits to proceed cleanly.

## 2026-07-01 — Phase 2 Session 11 Complete R0 Framework Reconciliation (Session 11)
**Agent:** Orchestrator (00)
**Duration:** ~45 mins
**Focus:** Analytical baseline setup, verifier scripts implementation, and test deferral categorisation.
- Created `verify_edge_case_coverage.py` and `verify_compliance_coverage.py` verifiers.
- Categorised all 263 manifest test IDs in `docs/verification/phase2_test_categorisation.md` and added 78 `deferred_to` fields to `tests/COVERAGE_MANIFEST.yaml`.
- Documented `docs/PHASE2_SCHEMA.md` with cross-referenced schema specs.

## 2026-06-30 — Phase 2 Session 9 Cleanup & DOAP Implementation (Session 10)
**Agent:** Backend (02)
**Duration:** ~60 mins
**Focus:** Resolving Session 9 database schema/model mismatches, SQLite compile rules for JSONB, uppercase audit constraints, and implementing full DOAP Skills state machine tracking (A-09).
- Cleaned up Electives model-schema drift: dropped composite PK, added UUID primary key, dropped deleted_at in runs.
- Added custom compiler rule in `conftest.py` for SQLite JSONB to JSON mapping during testing.
- Created migration 0015 to add procedural evidence and notes columns to DOAP.
- Implemented pure validations for DOAP progression (D->O->A->P) and rating-decision consistency.
- Developed `DoapService` handling DB persistence, automatic LogbookEntry creation, and Remediation workflow triggers.
- Developed FastAPI router for DOAP recording and retrieval.
- Wrote and verified 17 test cases (all passing, no xfails) covering unit, integration, and compliance rules.

## 2026-06-30 — Phase 2 Electives Backend Implementation (Session 9)
**Agent:** Backend (02)
**Duration:** ~90 mins
**Focus:** Implement schemas, models, service, and routing for Electives module (A-08) with FCFS and Ranked algorithms, row locking, and audit log integrations.
- Created `20260630_0014_add_elective_allocation_runs.py` migration to add allocation runs audit trail.
- Added Pydantic v2 schemas for electives with validation checks.
- Implemented `ElectiveService` with FCFS and Ranked allocation algorithms, SHA-256 tie-breaker, row locking (`FOR UPDATE NOWAIT`), and audit log writes on all mutations.
- Implemented API router for electives with 6 endpoints.
- Registered electives router in `main.py` and exported schemas in `schemas/__init__.py`.
- Enforced specification-first discipline with unit and integration test stubs (6 passing, 3 xfail).

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
