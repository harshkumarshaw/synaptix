# Phase 2 Schema Specification

**Status:** Draft — R0 baseline (cross-referenced against migrations 0011–0015)
**Created:** 2026-07-01 (Session 11)
**Last updated:** 2026-07-01

> This document is the canonical schema specification for all Phase 2 tables. It is the contract between schema design (R1) and migration files (R3).
> All DDL here is derived from the actual migration files. Discrepancies between this document and the migrations are noted explicitly.

---

## Migration Chain (Phase 2)

| Migration | File | Tables Added | Status |
|-----------|------|-------------|--------|
| 0011 | `20260620_0011_phase2_attendance_and_leave.py` | internship_rotations, leave_requests, attendance, attendance_summary, attendance_exemptions, attendance_accommodations | Applied |
| 0012 | `20260620_0012_phase2_logbook_electives_doap.py` | electives, elective_allocations, student_elective_preferences, logbook_entries, logbook_assessments, doap_session_records | Applied |
| 0013 | `20260620_0013_phase2_admissions.py` | admission_applications | Applied |
| 0014 | `20260630_0014_add_elective_allocation_runs.py` | elective_allocation_runs + alters: elective_allocations.id, elective_allocations.allocation_run_id, elective_allocations.allocation_method, student_elective_preferences.submitted_at | Applied |
| 0015 | `20260630_bf787ada4ee4_add_doap_evidence_and_notes.py` | alters: doap_session_records.evidence_asset_ids, doap_session_records.notes | Applied |

**Also in 0011:** `courses.subject_code` added as NULLABLE then made NOT NULL via inline backfill.

> **⚠️ SCHEMA DEVIATION (ADR-031 vs 0011):** ADR-031 mandated a two-step approach: add NULLABLE, run backfill script, then make NOT NULL in a follow-up migration. Migration 0011 instead adds, backfills inline (`UPDATE courses SET subject_code = SPLIT_PART(code, '-', 1)`), and immediately makes NOT NULL in a single migration. The deviation is **acceptable for dev/test** (backfill is simple prefix extraction), but production tenants with complex course codes will need the backfill script reviewed. Document in HANDOFF_NOTES.

---

## Tables Added in Phase 2

### 1. `internship_rotations` (scaffold — Phase 4 will extend)
**Migration:** 0011
**ADR:** ADR-033

```sql
CREATE TABLE internship_rotations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT,
    UNIQUE (tenant_id, id)
);
```

**RLS:** Enabled. Policy: `tenant_id = current_setting('snx.current_tenant_id')::UUID`
**Triggers:** `trg_internship_rotations_update` (fn_update_updated_at)
**Notes:** Scaffold only. `student_id`, `department`, `start_date`, `end_date`, `leave_days_used`, `status` columns are planned for Phase 4. The migration creates a minimal table to make the leave_requests FK valid (ADR-033).
**⚠️ DEVIATION from ADR-033 spec:** ADR-033 listed `student_id`, `department`, etc. as scaffold columns. The actual migration 0011 creates only `id`, `tenant_id`, timestamps. Phase 4 must add remaining columns via migration.

---

### 2. `leave_requests`
**Migration:** 0011
**ADR:** ADR-036

```sql
CREATE TABLE leave_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    student_id UUID NOT NULL,
    rotation_id UUID NULL,            -- FK to internship_rotations
    leave_type VARCHAR(30) NOT NULL CHECK (leave_type IN ('medical', 'academic', 'casual', 'other')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled')),
    workflow_instance_id UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    created_by UUID NULL,
    updated_by UUID NULL,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, rotation_id) REFERENCES internship_rotations(tenant_id, id) ON DELETE SET NULL,
    FOREIGN KEY (tenant_id, workflow_instance_id) REFERENCES workflow_instances(tenant_id, id) ON DELETE SET NULL
);

CREATE INDEX idx_leave_requests_student
    ON leave_requests (tenant_id, student_id, status) WHERE deleted_at IS NULL;
```

**RLS:** Enabled. **Triggers:** updated_at trigger.

---

### 3. `attendance`
**Migration:** 0011
**ADR:** ADR-020 (status enum), ADR-021 (event-session binding), ADR-037 (conflict resolution)

```sql
CREATE TABLE attendance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    student_id UUID NOT NULL,
    event_id UUID NOT NULL,
    session_id UUID NULL,             -- nullable; if set, must belong to event_id
    leave_request_id UUID NULL,       -- set when row was created by leave materialisation
    status VARCHAR(20) NOT NULL
        CHECK (status IN ('present', 'absent', 'late', 'excused', 'medical', 'official_duty', 'exempt')),
    attendance_category VARCHAR(30) NOT NULL
        CHECK (attendance_category IN ('theory', 'practical', 'clinical', 'doap', 'ece', 'aetcom', 'foundation_course', 'elective')),
    professional_phase VARCHAR(20) NOT NULL
        CHECK (professional_phase IN ('Phase I', 'Phase II', 'Phase III Part I', 'Phase III Part II')),
    method VARCHAR(20) NOT NULL DEFAULT 'manual'
        CHECK (method IN ('manual', 'qr', 'rfid', 'face', 'gps', 'biometric')),
    geo_lat NUMERIC(9,6) NULL,
    geo_lng NUMERIC(9,6) NULL,
    device_id VARCHAR(100) NULL,
    qr_token VARCHAR(255) NULL,
    exemption_batch_id UUID NULL,
    marked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    original_marked_at TIMESTAMPTZ NULL,  -- set for offline marks (actual mark time)
    needs_review BOOLEAN NOT NULL DEFAULT false,
    reviewed_by UUID NULL,
    reviewed_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    created_by UUID NULL,
    updated_by UUID NULL,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, event_id, student_id),  -- one live record per student per event
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, event_id) REFERENCES events(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, session_id) REFERENCES sessions(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, leave_request_id) REFERENCES leave_requests(tenant_id, id) ON DELETE SET NULL,
    FOREIGN KEY (tenant_id, reviewed_by) REFERENCES users(tenant_id, id) ON DELETE SET NULL
);

CREATE INDEX idx_attendance_student_event
    ON attendance (tenant_id, student_id, event_id) WHERE deleted_at IS NULL;
```

**RLS:** Enabled. **Triggers:** updated_at + `trg_verify_attendance_session_event` (BEFORE INSERT/UPDATE) + `trg_attendance_foundation_sync` (AFTER INSERT/UPDATE/DELETE) + `trg_attendance_aetcom_sync` (AFTER INSERT/UPDATE).

**⚠️ NOTE on unique constraint:** Migration 0011 uses `UNIQUE (tenant_id, event_id, student_id)` without a `WHERE deleted_at IS NULL` partial index. This means soft-deleted rows still count against uniqueness. R1/R3 should add the partial unique index and drop the full unique constraint.

---

### 4. `attendance_summary` (materialised cache)
**Migration:** 0011
**ADR:** ADR-022

```sql
CREATE TABLE attendance_summary (
    tenant_id UUID NOT NULL,
    student_id UUID NOT NULL,
    course_id UUID NOT NULL,
    professional_phase VARCHAR(20) NOT NULL,
    attendance_category VARCHAR(30) NOT NULL,
    sessions_conducted INTEGER NOT NULL DEFAULT 0,
    sessions_present INTEGER NOT NULL DEFAULT 0,
    sessions_excused INTEGER NOT NULL DEFAULT 0,
    sessions_official_duty INTEGER NOT NULL DEFAULT 0,
    sessions_medical INTEGER NOT NULL DEFAULT 0,
    attendance_pct NUMERIC(5,2) GENERATED ALWAYS AS (
        CASE
            WHEN sessions_conducted = 0 THEN 0.00
            ELSE ROUND(
                100.0 * (sessions_present + sessions_excused + sessions_official_duty + sessions_medical)::numeric
                / sessions_conducted, 2
            )
        END
    ) STORED,
    last_recalculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    PRIMARY KEY (tenant_id, student_id, course_id, professional_phase, attendance_category),
    FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, course_id) REFERENCES courses(tenant_id, id) ON DELETE CASCADE
);
```

**RLS:** Enabled. **Triggers:** updated_at trigger.

---

### 5. `attendance_exemptions`
**Migration:** 0011
**ADR:** ADR-024

```sql
CREATE TABLE attendance_exemptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    student_id UUID NOT NULL,
    event_id UUID NOT NULL,
    exemption_batch_id UUID NULL,      -- group ID for bulk exemptions
    reason TEXT NOT NULL,
    approved_by UUID NOT NULL,         -- must be Principal or equivalent role
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    created_by UUID NULL,
    updated_by UUID NULL,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, event_id) REFERENCES events(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, approved_by) REFERENCES users(tenant_id, id) ON DELETE RESTRICT
);
```

**RLS:** Enabled. **Triggers:** updated_at trigger.

---

### 6. `attendance_accommodations`
**Migration:** 0011
**ADR:** ADR-024

```sql
CREATE TABLE attendance_accommodations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    student_id UUID NOT NULL,
    effective_from DATE NOT NULL,
    effective_until DATE NOT NULL,
    attendance_category VARCHAR(30) NULL,   -- NULL = applies to all categories
    theory_threshold_override NUMERIC(5,2) NULL
        CHECK (theory_threshold_override <= 75.00),
    practical_threshold_override NUMERIC(5,2) NULL
        CHECK (practical_threshold_override <= 80.00),
    medical_certificate_asset_id UUID NULL,
    workflow_instance_id UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    created_by UUID NULL,
    updated_by UUID NULL,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, medical_certificate_asset_id)
        REFERENCES digital_assets(tenant_id, id) ON DELETE SET NULL,
    FOREIGN KEY (tenant_id, workflow_instance_id)
        REFERENCES workflow_instances(tenant_id, id) ON DELETE SET NULL
);
```

**RLS:** Enabled. **Triggers:** updated_at trigger.
**Note:** `theory_threshold_override <= 75.00` and `practical_threshold_override <= 80.00` enforce a minimum floor — accommodation can LOWER the threshold toward 50%, not RAISE it above the standard. This matches RPwD Act 2016 guidance (floor is 50%, ceiling is standard threshold).

---

### 7. `electives`
**Migration:** 0012
**ADR:** ADR-026, ADR-034

```sql
CREATE TABLE electives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    curriculum_id UUID NOT NULL,
    code VARCHAR(50) NOT NULL,
    title VARCHAR(150) NOT NULL,
    block VARCHAR(10) NOT NULL CHECK (block IN ('Block 1', 'Block 2')),
    elective_type VARCHAR(30) NOT NULL
        CHECK (elective_type IN ('pre_clinical', 'para_clinical', 'clinical', 'community', 'research')),
    capacity INTEGER NOT NULL DEFAULT 10,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    created_by UUID NULL,
    updated_by UUID NULL,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, curriculum_id, code),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, curriculum_id) REFERENCES curricula(tenant_id, id) ON DELETE RESTRICT
);
```

**RLS:** Enabled. **Triggers:** updated_at trigger.

---

### 8. `elective_allocations` (as of migration 0014)
**Migration:** 0012 created, 0014 altered
**ADR:** ADR-026, ADR-034

```sql
CREATE TABLE elective_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),   -- added in 0014
    tenant_id UUID NOT NULL,
    student_id UUID NOT NULL,
    elective_id UUID NOT NULL,
    block VARCHAR(10) NOT NULL CHECK (block IN ('Block 1', 'Block 2')),
    allocated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    supervisor_id UUID NULL,
    allocation_run_id UUID NULL,      -- added in 0014
    allocation_method VARCHAR(20) NULL   -- 'rank_1'..'rank_10' | 'fcfs' | 'manual'
        CHECK (allocation_method IN ('rank_1','rank_2','rank_3','rank_4','rank_5',
               'rank_6','rank_7','rank_8','rank_9','rank_10','fcfs','manual')
               OR allocation_method IS NULL),   -- added in 0014
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, student_id, block),  -- one allocation per block per student
    FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, elective_id) REFERENCES electives(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, supervisor_id) REFERENCES faculty(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (allocation_run_id) REFERENCES elective_allocation_runs(id) ON DELETE SET NULL
);

CREATE INDEX idx_elective_allocations_run_id
    ON elective_allocations (allocation_run_id) WHERE allocation_run_id IS NOT NULL;
```

**RLS:** Enabled. **Triggers:** updated_at trigger.

---

### 9. `elective_allocation_runs`
**Migration:** 0014
**ADR:** ADR-034

```sql
CREATE TABLE elective_allocation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    curriculum_id UUID NOT NULL,
    block VARCHAR(10) NOT NULL CHECK (block IN ('Block 1', 'Block 2')),
    algorithm_used VARCHAR(20) NOT NULL CHECK (algorithm_used IN ('fcfs', 'ranked')),
    triggered_by UUID NOT NULL,
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_dry_run BOOLEAN NOT NULL DEFAULT false,
    force_reallocate VARCHAR(20) NULL
        CHECK (force_reallocate IN ('additive', 'full') OR force_reallocate IS NULL),
    total_students INTEGER NOT NULL DEFAULT 0,
    total_allocated INTEGER NOT NULL DEFAULT 0,
    total_unallocated_pending_review INTEGER NOT NULL DEFAULT 0,
    run_duration_ms INTEGER NULL,
    results_summary JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, curriculum_id) REFERENCES curricula(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, triggered_by) REFERENCES users(tenant_id, id) ON DELETE RESTRICT
);

CREATE INDEX idx_allocation_runs_tenant_block
    ON elective_allocation_runs (tenant_id, curriculum_id, block, triggered_at);
```

**RLS:** Enabled. **Triggers:** updated_at trigger.

---

### 10. `student_elective_preferences` (as of migration 0014)
**Migration:** 0012 created, 0014 added submitted_at
**ADR:** ADR-034

```sql
CREATE TABLE student_elective_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    student_id UUID NOT NULL,
    elective_id UUID NOT NULL,
    block VARCHAR(10) NOT NULL CHECK (block IN ('Block 1', 'Block 2')),
    rank_position INTEGER NOT NULL CHECK (rank_position BETWEEN 1 AND 10),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),   -- added in 0014
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, student_id, block, rank_position),   -- no duplicate rank
    UNIQUE (tenant_id, student_id, block, elective_id),     -- no duplicate elective in same block
    FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, elective_id) REFERENCES electives(tenant_id, id) ON DELETE RESTRICT
);

CREATE INDEX idx_student_elective_preferences_submitted
    ON student_elective_preferences (tenant_id, student_id, block, submitted_at)
    WHERE deleted_at IS NULL;
```

**RLS:** Enabled. **Triggers:** updated_at trigger.
**Note:** Both unique constraints lack `WHERE deleted_at IS NULL` partial index. This means a soft-deleted preference blocks the rank/elective combination. R1 should add partial unique indexes.

---

### 11. `logbook_entries`
**Migration:** 0012
**ADR:** ADR-023, ADR-025, ADR-032

```sql
CREATE TABLE logbook_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    student_id UUID NOT NULL,
    elective_id UUID NULL,              -- NULL for regular entries
    subject_code VARCHAR(50) NULL,      -- NULL for elective entries (ADR-032)
    professional_phase VARCHAR(20) NOT NULL,
    competency_code VARCHAR(50) NOT NULL,
    nmc_level VARCHAR(2) NOT NULL CHECK (nmc_level IN ('K', 'KH', 'SH', 'P')),
    is_core BOOLEAN NOT NULL DEFAULT false,
    activity_date DATE NOT NULL,
    activity_name VARCHAR(150) NOT NULL,
    reflection TEXT NULL,
    rating VARCHAR(10) NULL CHECK (rating IN ('B', 'M', 'E')),
    attempt_type VARCHAR(10) NULL CHECK (attempt_type IN ('F', 'R', 'Re')),
    faculty_decision VARCHAR(10) NULL CHECK (faculty_decision IN ('C', 'R', 'Re')),
    faculty_initials VARCHAR(10) NULL,
    student_initials VARCHAR(10) NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'submitted', 'approved', 'rejected')),
    backdated BOOLEAN NOT NULL DEFAULT false,
    backdating_approved_by UUID NULL,
    signed_off_by UUID NULL,
    signed_off_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    created_by UUID NULL,
    updated_by UUID NULL,
    UNIQUE (tenant_id, id),
    -- Discriminator constraint (ADR-032): exactly one of elective_id or subject_code
    CHECK (
        (elective_id IS NULL AND subject_code IS NOT NULL) OR
        (elective_id IS NOT NULL AND subject_code IS NULL)
    ),
    FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, elective_id) REFERENCES electives(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, signed_off_by) REFERENCES faculty(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, backdating_approved_by) REFERENCES users(tenant_id, id) ON DELETE RESTRICT
);
```

**RLS:** Enabled. **Triggers:** updated_at trigger.

---

### 12. `logbook_assessments`
**Migration:** 0012
**ADR:** ADR-023

```sql
CREATE TABLE logbook_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    student_id UUID NOT NULL,
    subject_code VARCHAR(50) NOT NULL,
    professional_phase VARCHAR(20) NOT NULL,
    total_entries INTEGER NOT NULL DEFAULT 0,
    completed_entries INTEGER NOT NULL DEFAULT 0,
    ia_marks_pct NUMERIC(5,2) NOT NULL DEFAULT 0.00,
    ia_marks_awarded NUMERIC(6,2) NOT NULL DEFAULT 0.00,
    is_complete BOOLEAN NOT NULL DEFAULT false,
    signed_off_by UUID NULL,
    signed_off_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    created_by UUID NULL,
    updated_by UUID NULL,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, student_id, subject_code, professional_phase),
    FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, signed_off_by) REFERENCES faculty(tenant_id, id) ON DELETE RESTRICT
);
```

**RLS:** Enabled. **Triggers:** updated_at trigger.

---

### 13. `doap_session_records` (as of migration 0015)
**Migration:** 0012 created, 0015 added evidence_asset_ids and notes
**ADR:** ADR-035

```sql
CREATE TABLE doap_session_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    student_id UUID NOT NULL,
    session_id UUID NOT NULL,
    competency_code VARCHAR(50) NOT NULL,
    nmc_level VARCHAR(2) NOT NULL CHECK (nmc_level IN ('K', 'KH', 'SH', 'P')),
    is_core BOOLEAN NOT NULL DEFAULT false,
    stage VARCHAR(10) NOT NULL CHECK (stage IN ('D', 'O', 'A', 'P')),
    rating VARCHAR(10) NOT NULL CHECK (rating IN ('B', 'M', 'E')),
    attempt_type VARCHAR(10) NOT NULL CHECK (attempt_type IN ('F', 'R', 'Re')),
    faculty_decision VARCHAR(10) NOT NULL CHECK (faculty_decision IN ('C', 'R', 'Re')),
    faculty_id UUID NOT NULL,
    signed_off_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    evidence_asset_ids JSONB NOT NULL DEFAULT '[]',  -- added in 0015; array of UUID strings
    notes TEXT NULL,                                  -- added in 0015
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, session_id) REFERENCES sessions(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, faculty_id) REFERENCES faculty(tenant_id, id) ON DELETE RESTRICT
);
```

**RLS:** Enabled. **Triggers:** updated_at trigger.

---

### 14. `admission_applications` (placeholder)
**Migration:** 0013

> Schema not fully captured here — read migration 0013 directly. Placeholder only. No business logic until Phase 2.5.

---

## Tables Modified in Phase 2

### `courses` — `subject_code` column
**Migration:** 0011

```sql
ALTER TABLE courses ADD COLUMN subject_code VARCHAR(50) NULL;
UPDATE courses SET subject_code = SPLIT_PART(code, '-', 1);  -- dev/test backfill
ALTER TABLE courses ALTER COLUMN subject_code SET NOT NULL;
```

**⚠️ ADR-031 DEVIATION:** ADR-031 specified three separate steps. Migration 0011 collapses them into one with an inline backfill. For production with complex course codes, run `scripts/admin/backfill_subject_codes.py` after reverting the NOT NULL and before re-applying it.

---

## Views

### `subject_attendance_summary`
**Migration:** 0011

```sql
CREATE VIEW subject_attendance_summary AS
SELECT
    a.tenant_id,
    a.student_id,
    c.subject_code,
    a.attendance_category,
    SUM(a.sessions_conducted) AS total_conducted,
    SUM(a.sessions_present + a.sessions_excused + a.sessions_official_duty + a.sessions_medical) AS total_attended,
    CASE WHEN SUM(a.sessions_conducted) = 0 THEN 0.00
         ELSE ROUND(
             100.0 * SUM(a.sessions_present + a.sessions_excused + a.sessions_official_duty + a.sessions_medical)::numeric
             / SUM(a.sessions_conducted), 2
         )
    END AS aggregate_pct,
    MAX(a.last_recalculated_at) AS last_recalculated_at
FROM attendance_summary a
JOIN courses c ON c.tenant_id = a.tenant_id AND c.id = a.course_id
GROUP BY a.tenant_id, a.student_id, c.subject_code, a.attendance_category;
```

---

## Triggers

### `fn_verify_attendance_session_event` + `trg_verify_attendance_session_event`
**Migration:** 0011
**ADR:** ADR-021

Fires `BEFORE INSERT OR UPDATE ON attendance`. Validates that if `session_id` is provided, the session belongs to the `event_id` under the same `tenant_id`.

### `fn_sync_attendance_to_foundation_course` + `trg_attendance_foundation_sync`
**Migration:** 0011
**ADR:** ADR-030 (partially — Foundation Course is still trigger-based)

Fires `AFTER INSERT OR UPDATE OR DELETE ON attendance`. Recomputes `completed_hours` in `foundation_course_records` for `attendance_category = 'foundation_course'` records. Logs a compliance warning to `audit_log` if `completed_hours` drops below `required_hours` post-signoff.

**Note on AETCOM:** ADR-030 mandated service-layer sync for AETCOM. However, migration 0011 includes `fn_sync_attendance_to_aetcom` trigger as well. This is a **deviation from ADR-030**. The trigger updates `aetcom_records.status = 'reflection_submitted'` based on attendance. The full AETCOM logic (reflection + faculty signoff) remains in service-layer `aetcom_sync_service.py`. Both coexist for now — the trigger handles attendance-only sync, the service layer handles multi-condition status.

### `fn_events_after_insert_leave` + `trg_events_after_insert_leave`
**Migration:** 0011
**ADR:** ADR-036

Fires `AFTER INSERT ON events`. When a new event is created, automatically creates attendance rows with leave status for any students with active approved leave covering the event date.

---

## Service-Layer Sync Functions (not in migration, in service code)

| Function | File | Trigger Point |
|----------|------|---------------|
| `aetcom_sync_service.on_attendance_change()` | `services/snx-attendance/app/services/aetcom_sync_service.py` | Called from `attendance_service.mark_attendance()` |
| `leave_service.on_approval()` → `materialise_leave_to_attendance()` | `services/snx-leave/app/services/leave_service.py` | Called on leave status change to 'approved' |

---

## Known Schema Gaps / Issues to Address in R1

| # | Issue | Priority | ADR Reference |
|---|-------|----------|---------------|
| 1 | `attendance` unique constraint not partial (missing `WHERE deleted_at IS NULL`) | High | ADR-021 |
| 2 | `student_elective_preferences` unique constraints not partial | Medium | ADR-034 |
| 3 | `internship_rotations` missing scaffold columns (student_id, department, dates, status) | Medium | ADR-033 |
| 4 | `fn_sync_attendance_to_aetcom` trigger deviates from ADR-030 (service-layer mandate) | Low — acceptable coexistence | ADR-030 |
| 5 | `courses.subject_code` backfill may need review for production tenants with non-prefix codes | High (production only) | ADR-031 |
| 6 | `doap_session_records` has no `updated_at` trigger in downgrade path (minor) | Low | — |
| 7 | No `compliance_incidents` table in any migration (ADR-030 compliance incident logging uses `audit_log` instead) | Medium — acceptable substitution | ADR-030 |

---

## R1 Action Items

Before R1 schema finalisation:

1. Add `WHERE deleted_at IS NULL` partial unique indexes to `attendance`, `student_elective_preferences`
2. Add scaffold columns to `internship_rotations`  
3. Decide whether to keep `fn_sync_attendance_to_aetcom` trigger or remove it (service-layer only per ADR-030)
4. Add `compliance_incidents` table (referenced in ADR-030 spec; currently missing from migrations)
5. Verify `courses.subject_code` backfill strategy for production

These are schema-level decisions for R1 review — **do not create migration files until R1 is approved.**
