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

### [ESCALATION] Invoke Backend Agent (02) for Phase 2 Implementation
The DevOps agent (09) task of validating DevOps checks, linter issues, and database constraint seeding errors is completed. The next step is implementing the core application logic (Elective allocations and DOAP session records) inside `services/snx-logbook`, which is outside the DevOps Agent's scope. Please invoke the Backend Agent (02) or Orchestrator (00).

### [TO: 00-orchestrator / 02-backend] Next Session
- [ ] Implement `services/snx-logbook/app/services/elective_service.py` and `services/snx-logbook/app/routers/electives.py`
- [ ] Implement DOAP session recording service functions and routing endpoints
- [ ] Connect routers in `services/snx-logbook/app/main.py`
- [ ] Create tests for electives and DOAP skills.

## Blockers

- None

## Important Reminders

- **pytest-asyncio PINNED:** Always use `pytest-asyncio==0.23.8`. Do NOT upgrade until the 1.4.x loop scope API stabilises.
- **NullPool for Tests:** `conftest.py` creates a fresh NullPool engine per test and disposes it at teardown.
- **Run pytest per service:** Always set `PYTHONPATH` to include the specific service directory (e.g., `PYTHONPATH=.:services/snx-academic`).
- **Ruff config:** All ruff settings are under `[tool.ruff.lint]` — top-level keys were deprecated and migrated.
- **Two repos:** `jmn` remote = `itdept-JMN/synaptix` (org), `personal` remote = `harshkumarshaw/synaptix`.
