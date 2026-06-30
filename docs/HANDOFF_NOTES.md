# Handoff Notes

End-of-session notes for the next agent session.

> Agents: read this at session start. Update at session end.

---

## Current Status

**Last session:** 2026-06-30 — Session 9 (Backend Agent 02 — Electives)
**Phase:** Phase 2 — Electives ONLY (DOAP deliberately excluded from this session)
**Status:** Unit tests 6 passed, 3 xfail (honest deferrals). Ruff clean. Migration 0014 authored.

---

## What Was Completed (Session 9)

### Electives (A-08) — Production code:
- `tests/COVERAGE_MANIFEST.yaml` — ELEC-001..009, ELEC-NMC-001..004, ELEC-E001..007 added
- `tests/unit/electives/__init__.py` + `test_elective_service.py` — unit test stubs
- `tests/integration/test_electives.py` — integration test stubs (ELEC-003..007, 009)
- `tests/compliance/test_elective_compliance.py` — NMC compliance test stubs
- `services/_migrations/versions/20260630_0014_add_elective_allocation_runs.py` — migration 0014
- `services/snx-logbook/app/models/electives.py` — updated with `ElectiveAllocationRun`, `submitted_at`, `allocation_run_id`, `allocation_method`
- `services/snx-logbook/app/schemas/electives.py` — Pydantic v2 schemas (ConfigDict, model_validator)
- `services/snx-logbook/app/services/elective_service.py` — full service: create, submit_preferences, run_allocation (FCFS+Ranked), withdraw_allocation
- `services/snx-logbook/app/routers/electives.py` — 6 endpoints
- `services/snx-logbook/app/main.py` — router registered
- `services/snx-logbook/app/schemas/__init__.py` — elective schemas exported

---

## Tasks Pending — Explicit Recipients

### [TO: 06-testing] Testing Agent
Implement these currently-xfail tests (all in `tests/unit/electives/test_elective_service.py`):
- `ELEC-002` — submit_preferences idempotent: needs DB-backed integration test, not unit mock
- `ELEC-E001` — full-block replace on resubmit: same, needs integration
- `ELEC-E007` — wrong-block elective rejection: mock ordering conflict, needs integration with real DB

Implement these integration stubs (all in `tests/integration/test_electives.py`):
- `ELEC-003` — FCFS allocation, 10 students / 3 electives — seed data needed
- `ELEC-004` — Ranked allocation, ADR-034 worked example — seed data needed
- `ELEC-005` — Reallocation additive mode — seed data needed
- `ELEC-006` — Reallocation full mode — seed data needed
- `ELEC-007` — Audit run row verification — seed data needed
- `ELEC-009` — Dry-run vs live: no rows written

NOTE: `ELEC-008` (concurrent lock test) is explicitly `deferred_to: Phase 2.5` in COVERAGE_MANIFEST.

### [TO: 11-nmc-compliance] NMC Compliance Agent
Implement all stubs in `tests/compliance/test_elective_compliance.py`:
- `ELEC-NMC-001` — block duration 2 weeks enforced (NMC CBME 2019 Reg 7)
- `ELEC-NMC-002` — at least 1 clinical-category elective required
- `ELEC-NMC-003` — reflection logbook entry required per elective block for NExT eligibility
- `ELEC-NMC-004` — faculty supervisor assigned per elective per student
These require calling NExT eligibility checker and elective certification logic.

### [TO: 10-documentation] Documentation Agent
Update these files:
- `docs/EDGE_CASES.md` — Add ELEC-E001..ELEC-E007 entries using descriptions from COVERAGE_MANIFEST
- `docs/NMC_COMPLIANCE_LOG.md` — Add traceability rows for ELEC-NMC-001..004 (regulation ref, test ID, status=PENDING)
- `docs/ADR/ADR-034.md` — Verify the worked example section matches actual ElectiveService._run_ranked implementation

### [BLOCKED on Session 11] R0 ADR Reconciliation
- Session 11 MUST be R0 only: ADR-009..033 reconciliation, convention updates, no code.
- Human supervisor has explicitly stated: session rejection if Session 11 contains code work.

---

## Session 9 Debt List — Honest Assessment

| # | Debt Item | Severity | Incurred By |
|---|-----------|----------|-------------|
| D1 | ELEC-002 and ELEC-E001 unit tests deferred to integration — multi-call mock too complex | Low | 02-backend |
| D2 | ELEC-E007 unit test still xfail — mock ordering hits allocation guard before wrong-block check | Low | 02-backend |
| D3 | Migration 0014 NOT run against local DB — no alembic upgrade head confirmed this session | Medium | 02-backend |
| D4 | ADR-034 worked example trace NOT run — algorithm not manually verified against 10-student example | Medium | 02-backend |
| D5 | audit_logger.write_audit_log is imported but may not exist — depends on app.services.audit_logger module being present in snx-logbook | High | 02-backend |
| D6 | Router auth dependencies (get_current_user, TokenPayload) not verified to exist at correct import paths | Medium | 02-backend |
| D7 | Integration tests need test DB seeding — no seed fixtures created this session | Medium | 06-testing |
| D8 | R0 is now 2 sessions overdue — ADR-009..033 may have diverged from actual code | High | Structural |

**D5 is highest priority for Session 10**: before DOAP work begins, verify audit_logger import resolves.

---

## Important Reminders (Preserved from Session 7)

- **pytest-asyncio PINNED:** Always use `pytest-asyncio==0.23.8`. Do NOT upgrade.
- **NullPool for Tests:** `conftest.py` creates a fresh NullPool engine per test.
- **Run pytest per service:** `PYTHONPATH=f:\Synaptix\services\snx-logbook;f:\Synaptix`
- **Ruff config:** All ruff settings under `[tool.ruff.lint]`.
- **Two repos:** `jmn` remote = `itdept-JMN/synaptix`, `personal` remote = `harshkumarshaw/synaptix`.
- **DOAP is Session 10:** Do NOT begin DOAP implementation in Session 10 without reading this file first.
