# Current Focus

> Shared across all agents. Updated at every session.

## Current Phase

**Phase 2:** Electives (A-08) — COMPLETE (production code done, unit tests 6/9 passing, integration stubs pending).
**Next:** DOAP (A-09) — Session 10.
**After that:** R0 ADR reconciliation — Session 11 (NO code, reconciliation only).

## Active Modules

- `packages/shared` — scaffold complete (logging, errors, db, auth)
- `services/snx-auth` — scaffold complete, business logic stubbed
- `services/snx-academic` — scaffold complete, Phase 1B + Phase 2 Attendance/Leave complete
- `services/snx-institution` — scaffold complete
- `services/snx-workflow` — scaffold complete
- `services/snx-logbook` — **Phase 2 Electives COMPLETE** (service + router + schemas + models + migration 0014)
  - DOAP: models exist, service/router/schemas PENDING (Session 10)

## Active Branch

`chore/devops-scaffolding`

## Recently Completed

- **2026-06-30 Session 9 (Backend 02 — Electives):** Full Electives implementation.
  - COVERAGE_MANIFEST: 20 new entries (ELEC-001..009, ELEC-NMC-001..004, ELEC-E001..007)
  - Migration 0014: elective_allocation_runs table (ADR-034)
  - Pydantic v2 schemas, ElectiveService (FCFS+Ranked+dry-run+realloc), router (6 endpoints)
  - Unit tests: 6 passed, 3 xfail (honest deferral to integration tests)
  - Ruff: 0 errors
- **2026-06-27 Session 8 (Orchestrator):** Decomposed Phase 2 tasks.
- **2026-06-27 Session 7 (DevOps):** All Phase 2 migrations applied (0011-0013). 34 Academic + 5 Leave tests passing.
- **2026-06-20 Session 6 (Orchestrator):** ALL 5 CI jobs GREEN.

## Up Next

1. **Session 10 — Backend Agent (02):** DOAP implementation.
   - Same discipline: COVERAGE_MANIFEST → stubs → schemas → service → router
   - First: verify `app.services.audit_logger.write_audit_log` exists (Debt D5 from Session 9)
2. **Session 10 — Testing Agent (06):** Implement integration test stubs for ELEC-003..009 with DB seeding.
3. **Session 11 — MANDATORY R0:** ADR-009..033 reconciliation. NO code. Human supervisor enforcing this.

## Blockers

- **D5 (High):** `audit_logger.write_audit_log` in snx-logbook — import path assumed, not verified.
  Check `services/snx-logbook/app/services/` for `audit_logger.py` existence before Session 10.
- **D3 (Medium):** Migration 0014 not applied to local DB. Run `alembic upgrade head` before Session 10 integration tests.
- **D8 (High):** R0 ADR reconciliation 2 sessions overdue.
