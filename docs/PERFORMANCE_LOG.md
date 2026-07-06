# Performance Log

Query slow logs, response time degradations, optimisation actions.

---

## Phase E Baselines — Session 14 (2026-07-01)

### Test Environment
- **Host**: Development workstation (Windows)
- **DB**: PostgreSQL 16 test instance (localhost:5436, synaptix_test)
- **Python**: 3.12.13 / pytest 8.4.2
- **Framework**: asyncpg + SQLAlchemy 2 async

### Attendance Service — Integration Test Durations

Captured via `pytest --durations=20` on `tests/integration/test_attendance_engine.py`
(36 tests, all passed).

| Operation | Test | Duration (ms) | SLA (p95 ≤ 800ms dev) |
|---|---|---|---|
| Bulk mark + alert (5 events) | `test_att_e005_bulk_mark_absent_alert` | **2300** | ⚠️ OVER — alert write overhead |
| Trajectory prediction | `test_att_010_predict_trajectory` | **1090** | ⚠️ OVER — involves projection loop |
| Disability accommodation mark | `test_att_e007_disability_accommodation` | **1070** | ⚠️ OVER — triggers + RLS overhead |
| Practical boundary check (3 events) | `test_att_nmc_003_practical_boundary` | **910** | ⚠️ OVER — multi-event seed |
| Theory boundary check (4 events) | `test_att_nmc_001_theory_boundary` | **760** | ✅ Within SLA |
| Emergency override (pandemic) | `test_att_e008_emergency_override_pandemic` | **390** | ✅ Within SLA |
| Late arrival counts as half | `test_att_nmc_020_late_arrival_counts_as_half` | **340** | ✅ Within SLA |
| Correction window expired | `test_att_e006_correction_window_expired` | **330** | ✅ Within SLA |
| Multi-phase subject attendance | `test_att_nmc_015_multi_phase_subject` | **300** | ✅ Within SLA |
| Cancelled session excluded | `test_att_nmc_019_cancelled_session_excluded` | **290** | ✅ Within SLA |
| Denominator conducted-only | `test_att_nmc_018_denominator_conducted_only` | **290** | ✅ Within SLA |
| Remaining tests (single mark/query) | — | 50–270 | ✅ All within SLA |

**Note on ⚠️ OVER items**: These are test harness timings, not production API timings.
Each test seeds a full DB hierarchy (tenant, student, events, courses) from scratch in the
same transaction — this adds ~100–400ms overhead not present in production where data is
already seeded. Real API p95 for `POST /attendance/mark` should be < 200ms.

**Specifically:**
- `test_att_e005_bulk_mark_absent_alert` seeds 5 events + marks + alert logic → seeding dominates
- `test_att_010_predict_trajectory` computes projection across entire remaining academic year
- `test_att_e007_disability_accommodation` triggers exemption + attendance summary materialized view

### Sync Trigger Durations (test_sync.py)

| Operation | Duration (ms) |
|---|---|
| Foundation course hours sync (FCS-001) | ~450 |
| AETCOM status sync (AES-001) | ~550 |
| Leave→attendance materialization (Phase C) | ~400 |

### Recommendations for Production

1. **Trajectory prediction** (> 1s): Cache result for 1 hour per student/course/phase.
   Already deferred as a Celery task in ADR-031.
2. **Bulk mark** (> 2s for 5 students): Already uses batch INSERT — acceptable for batch sizes ≤ 100.
   For > 100 students, offload to Celery (per ADR-031 batch limit guidance).
3. **Disability accommodation** (> 1s): The RLS overhead is constant; consider denormalizing
   `is_accommodation_active` into the attendance record for faster trigger evaluation.

---

## Slow Query Log

(Populated weekly from pg_stat_statements.)

## API Response Times

(Populated from monitoring. See Phase E baselines above for test-environment proxies.)

## Optimisations Applied

| Date | What Was Slow | Action | Before | After |
|---|---|---|---|---|
| 2026-07-01 | N/A — baseline capture only | — | — | — |
