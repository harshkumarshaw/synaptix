# Current Focus

> Shared across all agents. Updated at every session.

## Current Phase

**R1 IN PROGRESS (Session 13 complete).**
**Next:** Session 14 — Calendar, Planning & Cross-cutting tests.

## R1 Baseline (as of 2026-07-01 Session 13)

| Metric | Value |
|--------|-------|
| Active required tests | 189 |
| Implemented | 151 |
| Missing (Phase 2 remaining) | **38** |
| Deferred Phase 2.5 | 17 |
| Deferred Phase 3 | 41 |
| Deferred Phase 4 | 20 |

## Active Modules

- `packages/shared` — scaffold complete (logging, errors, db, auth)
- `services/snx-auth` — scaffold complete, business logic stubbed
- `services/snx-academic` — scaffold complete, Phase 1B + Phase 2 Attendance/Leave + Attendance Engine 100% PASSING (36 tests)
- `services/snx-institution` — scaffold complete
- `services/snx-workflow` — scaffold complete
- `services/snx-logbook` — Phase 2 Electives & DOAP COMPLETE

## Active Branch

`chore/devops-scaffolding`

## Recently Completed

- **2026-07-01 Session 13 (Backend Agent — Logbook & Admissions):**
  - Created Admissions placeholder ORM models, schemas, CRUD service, and router.
  - Corrected logbook stubs/services to support dynamic definitions and match PostgreSQL check constraints.
  - Implemented 24 new unit, compliance, and integration tests for Logbook and Admissions.
  - Session log: `docs/sessions/2026-07-01-session-13.md`
- **2026-07-01 Session 12 (Backend 02 — Attendance & Schema Gaps):**
  - Wrote migration 0016 fixing three database schema gaps (constraints, triggers, defaults).
  - Fixed and verified all 36 integration tests in `test_attendance_engine.py` (Tier 1: 22/22, Tier 2: 14/14).
  - Configured scoped checks in `scripts/pre-commit-hook.ps1`.
  - Added mypy overrides in `pyproject.toml` for shared package.
  - Session log: `docs/sessions/2026-07-01-session-12.md`
- **2026-07-01 Session 11 (Orchestrator — R0):** Verifier scripts, categorisation, baseline, `docs/sessions/2026-07-01-session-11.md`.
- **2026-06-30 Session 10 (Backend 02 — DOAP):** DOAP service, schemas, tests, migration 0015.

## Up Next (R1 Priority Order)

1. **Digital Logbook tests** — 14 NMC compliance (LOG-NMC-*) + 8 edge cases (LOG-E*) = 22 tests (Session 13)
2. **Calendar & Planning tests** — 9 calendar tests (CAL-*), 5 lesson plan (LPN-*), 3 session tracking (SES-*)
3. **Cross-cutting tests** — TNT-*, AUD-*, CUR-001/002/003, ACC-*, FCS-*, AES-*

## Blockers

- None. Pre-commit checks passing cleanly.
