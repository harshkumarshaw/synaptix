# Current Focus

> Shared across all agents. Updated at every session.

## Current Phase

**Phase 2:** Electives (A-08) & DOAP (A-09) — COMPLETE (production code, unit tests, integration tests, and compliance tests passing).
**Next:** R0 ADR reconciliation — Session 11 (NO code, reconciliation only).

## Active Modules

- `packages/shared` — scaffold complete (logging, errors, db, auth)
- `services/snx-auth` — scaffold complete, business logic stubbed
- `services/snx-academic` — scaffold complete, Phase 1B + Phase 2 Attendance/Leave complete
- `services/snx-institution` — scaffold complete
- `services/snx-workflow` — scaffold complete
- `services/snx-logbook` — **Phase 2 Electives & DOAP COMPLETE** (service + router + schemas + models + migrations 0014, 0015)

## Active Branch

`chore/devops-scaffolding`

## Recently Completed

- **2026-06-30 Session 10 (Backend 02 — Session 9 Debt & DOAP):** 
  - Resolved model-schema drift, SQLite JSONB type mapping, uppercase audit action constraint.
  - Added 14 DOAP entries to COVERAGE_MANIFEST.yaml.
  - Created migration 0015 adding DOAP evidence asset IDs and notes columns.
  - Implemented DOAP Pydantic schemas, stage progression validator, DoapService, and API router.
  - Wrote and verified 17 DOAP test cases (all passing).
- **2026-06-30 Session 9 (Backend 02 — Electives):** Full Electives implementation.
- **2026-06-27 Session 8 (Orchestrator):** Decomposed Phase 2 tasks.

## Up Next

1. **Session 11 — MANDATORY R0:** ADR-009..033 reconciliation. NO code. Human supervisor enforcing this.

## Blockers

- None. All previous debt items (D3, D5) are fully resolved.

