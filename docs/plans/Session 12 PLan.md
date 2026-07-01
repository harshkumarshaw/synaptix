# Session 12 Plan — Schema Gap Resolution + Attendance Engine Compliance Testing

**Target Agent:** 02-backend (paired with Orchestrator)
**Estimated duration:** 4-5 hours of focused work
**Session structure:** Phase A (Schema Gap Resolution, 1 hour) → Phase B (Attendance Engine Test Implementation, 3 hours) → Phase C (Handoff and Documentation, 30 min)
**References:** `docs/PHASE2_SCHEMA.md`, `tests/COVERAGE_MANIFEST.yaml`

---

## Objectives

1. **Resolve 3 Schema Gaps:** Fix RLS/soft-delete unique constraint limitations and complete scaffolding columns in migration-compliant fashion.
2. **Attendance Engine Target (36 Tests):** Write and pass all 36 active-required tests for `attendance_engine` that are currently missing or marked as stubs/xfails.
3. **Verify Compliance:** Ensure all 5 verifier scripts pass cleanly.

---

## Phase A — Schema Gap Resolution (3 Gaps)

We will implement a new migration (e.g., `0016_resolve_schema_gaps.py`) to address the following 3 explicit database gaps documented in `docs/PHASE2_SCHEMA.md`:

### 1. Attendance Soft-Delete Uniqueness Gap
- **Issue:** The existing `uq_attendance_event_student` unique constraint on `attendance` is defined as `UNIQUE (tenant_id, event_id, student_id)`. Because it is a hard unique constraint, a soft-deleted row (`deleted_at IS NOT NULL`) prevents the student from having a new, active attendance record for that event.
- **Fix:** Drop the full unique constraint and replace it with a partial unique index:
  ```sql
  ALTER TABLE attendance DROP CONSTRAINT uq_attendance_event_student;
  CREATE UNIQUE INDEX uq_attendance_event_student_partial 
  ON attendance (tenant_id, event_id, student_id) 
  WHERE (deleted_at IS NULL);
  ```

### 2. Elective Preferences Soft-Delete Uniqueness Gap
- **Issue:** The constraints `uq_elective_preferences_rank` and `uq_elective_preferences_elective` on `student_elective_preferences` are hard unique constraints. Soft-deleted preferences prevent students from submitting new preferences using the same rank or elective.
- **Fix:** Drop the full constraints and replace with partial unique indexes:
  ```sql
  ALTER TABLE student_elective_preferences DROP CONSTRAINT uq_elective_preferences_rank;
  ALTER TABLE student_elective_preferences DROP CONSTRAINT uq_elective_preferences_elective;
  
  CREATE UNIQUE INDEX uq_elective_preferences_rank_partial 
  ON student_elective_preferences (tenant_id, student_id, block, rank_position) 
  WHERE (deleted_at IS NULL);
  
  CREATE UNIQUE INDEX uq_elective_preferences_elective_partial 
  ON student_elective_preferences (tenant_id, student_id, block, elective_id) 
  WHERE (deleted_at IS NULL);
  ```

### 3. Internship Rotations Scaffold Columns
- **Issue:** `internship_rotations` was created in migration `0011` as a blank placeholder table (only `id`, `tenant_id` and timestamps).
- **Fix:** Add the required scaffold columns to allow proper referencing by other modules:
  - `student_id` (UUID, NOT NULL, FK to students)
  - `department` (VARCHAR(100), NOT NULL)
  - `start_date` (DATE, NOT NULL)
  - `end_date` (DATE, NOT NULL)
  - `leave_days_used` (INTEGER, NOT NULL DEFAULT 0)
  - `status` (VARCHAR(30), NOT NULL DEFAULT 'scheduled')
  - Corresponding foreign keys and composite constraints.

---

## Phase B — Attendance Engine Test Implementation (36 Tests)

We will convert/implement the **36 active-required tests** that are currently failing/stubbed. The 5 tests that are already passing in the codebase (`ATT-001`, `ATT-002`, `ATT-007`, `ATT-008`, `ATT-E001`) will be preserved.

### Enumerated List of the 36 Target Tests

#### Part B.1: Critical/Integration Tests (2 Tests)
1. **`ATT-009`**: At-risk student list correctly identifies students below threshold
2. **`ATT-010`**: Attendance trajectory prediction works (improving/declining/stable)

#### Part B.2: NMC Compliance Thresholds & Categories (14 Tests)
3. **`ATT-NMC-001`**: Student with EXACTLY 75.00% theory attendance is ELIGIBLE for theory exam (NMC GMER 2019 §11.1)
4. **`ATT-NMC-002`**: Student with 74.99% theory attendance is BLOCKED for theory exam (NMC GMER 2019 §11.1)
5. **`ATT-NMC-003`**: Student with EXACTLY 80.00% practical attendance is ELIGIBLE for practical exam (NMC GMER 2019 §11.1)
6. **`ATT-NMC-004`**: Student with 79.99% practical attendance is BLOCKED for practical exam (NMC GMER 2019 §11.1)
7. **`ATT-NMC-005`**: Student with 76% theory AND 79% practical: theory eligible, practical blocked (Independent pool check)
8. **`ATT-NMC-006`**: Student with 74% theory AND 81% practical: theory blocked, practical eligible (Independent pool check)
9. **`ATT-NMC-007`**: Clinical posting attendance counted toward 80% practical pool, not 75% theory pool
10. **`ATT-NMC-008`**: DOAP session attendance counted toward 80% practical pool
11. **`ATT-NMC-009`**: ECE session attendance counted toward 80% practical pool
12. **`ATT-NMC-010`**: Theory lecture attendance counted toward 75% theory pool
13. **`ATT-NMC-011`**: Elective Block 1 attendance threshold is 75% (separate pool)
14. **`ATT-NMC-012`**: Elective Block 2 attendance threshold is 75% (separate pool)
15. **`ATT-NMC-016`**: Principal can grant attendance exemption with audit-logged reason
16. **`ATT-NMC-017`**: Exemption is audit-logged with reason, approver, and timestamp

#### Part B.3: Core Calculations & Denominators (3 Tests)
17. **`ATT-NMC-018`**: Attendance denominator counts ONLY conducted sessions, NEVER planned
18. **`ATT-NMC-019`**: Cancelled session does not count toward attendance denominator
19. **`ATT-NMC-020`**: Late arrival (configurable threshold) counts as half-attendance if configured

#### Part B.4: Business Logic & Edge Cases (17 Tests)
20. **`ATT-E003`**: Duplicate attendance entry (same student, same event) is rejected
21. **`ATT-E004`**: Attendance marked for cancelled event — flagged for admin review
22. **`ATT-E005`**: Bulk attendance change (>20 students marked absent at once) triggers confirmation/audit alert
23. **`ATT-E006`**: Attendance correction window: faculty can correct within 24h, after that needs HOD approval
24. **`ATT-E007`**: Student with disability accommodation: uses adjusted threshold per Dean approval
25. **`ATT-E008`**: Emergency override (pandemic): temporary threshold reduction applies
26. **`ATT-E009`**: Integration session attendance category inherits primary subject's category
27. **`ATT-E010`**: Lateral entry student: prior phase attendance not included in current pct calculation
28. **`ATT-E011`**: Detained student: attendance resets for repeated phase, prior phase retained as history
29. **`ATT-E012`**: Section change mid-year: attendance from both sections aggregated
30. **`ATT-E013`**: Multiple faculty per event: any faculty in faculty_ids can mark attendance
31. **`ATT-E014`**: Faculty resignation: future sessions reassigned, past sessions retain original faculty_id
32. **`ATT-E015`**: Phase transition: provisional status until prior exam results published
33. **`ATT-E016`**: Concurrent attendance writes from two devices: unique constraint prevents duplicates
34. **`ATT-NMC-013`**: AETCOM attendance tracked separately from theory and practical
35. **`ATT-NMC-014`**: Foundation Course attendance tracked separately
36. **`ATT-NMC-015`**: Multi-phase subject (Community Medicine) aggregates attendance across phases

---

## Phase C — Verification & Handoff (30 min)

1. **Verify all 5 verifier scripts pass:**
   - `verify_adr_sequence.py`
   - `verify_coverage_manifest.py` (target: missing attendance engine tests = 0)
   - `verify_edge_case_coverage.py`
   - `verify_compliance_coverage.py`
2. **Update Tracking Documents:**
   - `docs/CHANGELOG.md`
   - `docs/DEVELOPMENT_LOG.md`
   - `docs/sessions/2026-07-01-session-12.md`
   - `.agent-memory/working/CURRENT_FOCUS.md`
3. **Git Commit:** Commit changes with conventional commits style.