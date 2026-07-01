# Current Focus

> Shared across all agents. Updated at every session.

## Current Phase

**R0 COMPLETE (2026-07-01 Session 11).**
**Next:** R1 — Schema finalisation, service scaffolding, and test implementation. Target: 86 missing tests → 0.

## R0 Baseline (as of 2026-07-01)

| Metric | Value |
|--------|-------|
| Active required tests | 185 |
| Implemented | 99 |
| Missing (Phase 2 must close) | **86** |
| Deferred Phase 2.5 | 17 |
| Deferred Phase 3 | 41 |
| Deferred Phase 4 | 20 |

## Active Modules

- `packages/shared` — scaffold complete (logging, errors, db, auth)
- `services/snx-auth` — scaffold complete, business logic stubbed
- `services/snx-academic` — scaffold complete, Phase 1B + Phase 2 Attendance/Leave complete
- `services/snx-institution` — scaffold complete
- `services/snx-workflow` — scaffold complete
- `services/snx-logbook` — Phase 2 Electives & DOAP COMPLETE

## Active Branch

`chore/devops-scaffolding`

## Recently Completed

- **2026-07-01 Session 11 (Orchestrator — R0):**
  - Created `scripts/verify_edge_case_coverage.py` and `scripts/verify_compliance_coverage.py` (full AgentForge pattern)
  - Updated `scripts/verify_coverage_manifest.py` to respect `deferred_to` fields
  - Created `docs/verification/phase2_test_categorisation.md` (all descriptions from manifest)
  - Added 78 `deferred_to` fields to `tests/COVERAGE_MANIFEST.yaml`
  - Created `docs/PHASE2_SCHEMA.md` — cross-referenced schema spec for migrations 0011–0015
  - Appended 3 new sections to `conventions/DATABASE_CONVENTIONS.md`
  - Session log: `docs/sessions/2026-07-01-session-11.md`
- **2026-06-30 Session 10 (Backend 02 — DOAP):** DOAP service, schemas, tests, migration 0015.
- **2026-06-30 Session 9 (Backend 02 — Electives):** Full Electives implementation.

## Up Next (R1 Priority Order)

1. **Fix schema gaps** (from PHASE2_SCHEMA.md):
   - Add partial unique index to `attendance` (WHERE deleted_at IS NULL)
   - Add partial unique indexes to `student_elective_preferences`
   - Add scaffold columns to `internship_rotations`
2. **Attendance Engine tests** — 20 NMC compliance tests (ATT-NMC-*) + 16 edge cases (ATT-E*) = 36 tests
3. **Digital Logbook tests** — 14 NMC compliance (LOG-NMC-*) + 8 edge cases (LOG-E*) = 22 tests
4. **Calendar & Planning tests** — 9 calendar tests (CAL-*), 5 lesson plan (LPN-*), 3 session tracking (SES-*)
5. **Cross-cutting tests** — TNT-*, AUD-*, CUR-001/002/003, ACC-*, FCS-*, AES-*

## Blockers

- None. R0 complete. R1 can start immediately.
