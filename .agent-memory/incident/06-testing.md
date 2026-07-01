# 06-testing — Incident Memory

Failures, near-misses, and what NOT to do.

## Incidents

### 2026-07-01 — Session 14: FCS-002 trigger bug (actor_id vs actor_user_id)
**Test**: `test_fcs_002_trigger_blocks_hours_reduction_after_signoff`
**Symptom**: `UndefinedColumnError: column "actor_id" of relation "audit_log" does not exist`
**Root Cause**: Migration `20260620_0011_phase2_attendance_and_leave.py` function
`fn_sync_attendance_to_foundation_course` inserts into `audit_log` using column name `actor_id`
but the actual schema column is `actor_user_id`.
**Action**: Test marked `xfail(strict=False)`. Fix requires migration patch renaming `actor_id`→`actor_user_id`
in the trigger body. Logged in INCIDENT_LOG.md.
**Status**: PENDING — needs migration 0017 to fix trigger function.

## Things That Failed

- `ON CONFLICT (tenant_id, event_id, student_id)` on `attendance` table — no such unique constraint exists.
  Only `(tenant_id, id)` is unique. Use plain INSERT or pre-check existence.
- `faculty` table has NO `employment_type` or `status` columns — only `designation`, `employee_id` (NOT NULL), `is_active`.
- `lesson_plans.nmc_competency_level` is `VARCHAR(2)` with CHECK constraint `IN ('K', 'KH', 'SH', 'P')`.
  Do NOT use human-readable strings like `'Must Know'`.
- `foundation_course_records.module_name` has CHECK constraint:
  `IN ('orientation', 'skills_acquisition', 'professional_development', 'language_computer', 'sports_yoga', 'hospital_visits')`
- `asyncpg` requires `datetime.time` objects for TIME columns — NOT string `'09:00'`.
- `audit_log.actor_user_id` has a FK to `users(id)`. Must seed a real user before calling `write_audit_log`.

## Things to Avoid

- Never use `strftime()` output as parameter for asyncpg TIME columns — pass `datetime.time` directly.
- Never guess constraint values — always check migration files or `inspect()` the actual DB.
- Never assume `ON CONFLICT` clause works without a unique/exclusion constraint covering those columns.
