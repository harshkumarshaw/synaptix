# Handoff Notes

End-of-session notes for the next agent session.

> Agents: read this at session start. Update at session end.

## Current Status

**Last session:** 2026-06-27 — Session 7 (DevOps Agent 09)
**Phase:** Phase 2 — Attendance & Leave
**Status:** All unit and integration tests PASS. All 13 migrations are applied.

## What Was Fixed & Scaffolded (Session 7)

- **Linter & Formatting:** Fixed 43 Ruff errors and ran Black formatter. All files conform to standards.
- **Academic Course Model:** Added missing `subject_code` with automatic value parser to allow correct data validation and seeding.
- **Integration Test Seeding:**
  - Standardized raw SQL course inserts in integration tests.
  - Resolved `uq_students_tenant_roll_number` constraint conflicts in `test_attendance.py` and `test_leave.py` by seeding unique student roll numbers dynamically from UUIDs.
  - Corrected `LeaveService` test instantiation to use valid user ID as actor ID.
- **Database Migrations:** Applied migrations `0011`, `0012`, `0013` to local test database.

## Tasks Pending

### [TO: 02-backend] Backend Agent
- [ ] Implement Pydantic schemas in `services/snx-logbook/app/schemas/electives.py` and `logbook_phase2.py`.
- [ ] Implement `ElectiveService` in `services/snx-logbook/app/services/elective_service.py` with student preference ranking validations (1-10) and admin-triggered capacity-locked allocation (`with_for_update`).
- [ ] Implement API routers in `services/snx-logbook/app/routers/electives.py` and register them in `services/snx-logbook/app/main.py`.
- [ ] Extend `LogbookService` in `services/snx-logbook/app/services/logbook_service.py` to support Phase 2 core vs non-core DOAP session validations, stage checks (D/O/A/P), and rating checks (B/M/E).

### [TO: 06-testing] Testing Agent
- [ ] Implement unit and integration tests for Electives preferences and capacity-locked allocation in `tests/unit/electives/` and `tests/integration/test_electives.py`.
- [ ] Implement unit/integration tests for DOAP session ratings, stages, and faculty decisions in `tests/unit/doap/` and `tests/integration/test_doap.py`.

### [TO: 11-nmc-compliance] NMC Compliance Agent
- [ ] Implement compliance checks verifying that elective block configurations match NMC v2023 regulations (two blocks of 4 weeks each, 75% minimum attendance threshold enforced per block).

## Blockers

- None

## Important Reminders

- **pytest-asyncio PINNED:** Always use `pytest-asyncio==0.23.8`. Do NOT upgrade until the 1.4.x loop scope API stabilises.
- **NullPool for Tests:** `conftest.py` creates a fresh NullPool engine per test and disposes it at teardown.
- **Run pytest per service:** Always set `PYTHONPATH` to include the specific service directory (e.g., `PYTHONPATH=.:services/snx-academic`).
- **Ruff config:** All ruff settings are under `[tool.ruff.lint]` — top-level keys were deprecated and migrated.
- **Two repos:** `jmn` remote = `itdept-JMN/synaptix` (org), `personal` remote = `harshkumarshaw/synaptix`.
