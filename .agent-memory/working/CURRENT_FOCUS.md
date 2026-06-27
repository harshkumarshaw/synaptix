# Current Focus

> Shared across all agents. Updated at every session.

## Current Phase

**Phase 2:** Attendance & Leave (A-10 / A-12 / A-08 / A-09) — Scaffolding & Integration Tests Passing

## Active Modules

- `packages/shared` — scaffold complete (logging, errors, db, auth)
- `services/snx-auth` — scaffold complete, business logic stubbed
- `services/snx-academic` — scaffold complete, Phase 1B Calendar & Planning + Phase 2 Attendance and Leave service/models completed
- `services/snx-institution` — scaffold complete
- `services/snx-workflow` — scaffold complete
- `services/snx-logbook` — scaffold complete, Phase 1B Foundation Course & AETCOM + Phase 2 Electives/DOAP models completed
- `services/_migrations` — all 13 migrations applied to dev/test databases

## Active Branch

`chore/devops-scaffolding`

## Recently Completed

- **2026-06-27 Session 8 (Orchestrator — Work Orchestrated):** Decomposed and distributed remaining Phase 2 tasks (Electives preference allocations and DOAP session records) to Backend (02), Testing (06), and NMC Compliance (11) agents. Generated the Phase 2 Implementation Plan and Task List artifacts.
- **2026-06-27 Session 7 (DevOps — Scaffolding & Integration Fixes Complete):** All Phase 2 migrations applied (0011-0013). Fixed linter, schema columns (added `subject_code` to `Course`), and integration test seeding issues (unique student roll numbers). All 34 Academic and 5 Leave integration tests pass cleanly.
- **2026-06-20 Session 6 (Orchestrator — CI Fix Complete):** ALL 5 GitHub Actions jobs now GREEN (✅ commit 1c13d10, run 27871964773). Fixed:
  1. Python syntax error in snx-logbook router
  2. Ruff config migrated to `[tool.ruff.lint]`, 88 files formatted with Black
  3. CI unit-tests job rewired with postgres:16 service container, alembic migration step, per-service PYTHONPATH isolation, coverage append
  4. `tests/conftest.py` db_session fixture: fresh NullPool engine per test, `@pytest_asyncio.fixture` → `async @pytest.fixture`
  5. Pinned `pytest-asyncio==0.23.8` to avoid Linux asyncio event loop isolation bug in 1.4.0
  All 29 tests pass; 83.67% coverage (≥80%).
- **2026-06-20 Session 4 (Backend):** Scaffolded `snx-workflow` service. All tests PASS.
- **2026-06-20 Session 3 (Orchestrator):** Scaffolded `snx-academic` and `snx-institution` services, migrations, and integration tests.
- **2026-06-20 Session 2 (Backend/Testing):** CryptContext fix + auth role MFA tests verification.
- **2026-06-20 Session 1 (Orchestrator):** Root project and packages scaffold.

## Up Next

1. **Backend Agent (02):** Implement schemas, service functions, and API routing for Electives and DOAP session records inside `services/snx-logbook`.
2. **Testing Agent (06):** Write unit and integration tests for Electives preferences, allocations, and DOAP records in `tests/unit/` and `tests/integration/`.
3. **NMC Compliance Agent (11):** Implement NMC v2023 compliance tests for Elective modules and attendance constraints.

## Blockers

- None
