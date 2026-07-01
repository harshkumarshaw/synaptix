# Session 11 Plan — R0 Framework Reconciliation (Complete)

**Target Agent:** 00-orchestrator or 02-backend (documentation-only session)
**Estimated duration:** 5-7 hours of focused work
**Session structure:** 9 sequential steps, no code, no migrations
**Scope:** Documentation, analysis, and framework reconciliation ONLY

---

## Why This Session Exists

R0 (Framework Reconciliation) has been deferred since Session 5. It was explicitly scheduled for Session 11 with a non-negotiable directive from the human supervisor. This session closes the longest-running framework debt in Phase 2.

R0 is NOT a quick doc cleanup. It is the analytical foundation that makes Phase 2 measurable, auditable, and completable. Without R0:

- There is no baseline to measure Phase 2 completion against
- There is no specification document an NMC inspector can read
- There is no categorisation of which tests must pass vs which are deferred
- The ADR audit trail has gaps that break traceability

This is 5-7 hours of disciplined documentation work. Treat it with the same seriousness as a code session.

---

## Mandatory Session Start Protocol

Per AGENTS.md §2:

1. Read `AGENTS.md` (root)
2. Read `docs/HANDOFF_NOTES.md` — the CRITICAL SESSION 11 IS R0 ONLY directive
3. Read `.agent-memory/working/CURRENT_FOCUS.md`
4. Read your agent specialisation file
5. Read `.agent-memory/learning/{your-id}.md`
6. Read `.agent-memory/incident/{your-id}.md`
7. Read `docs/DECISIONS.md` — note the LAST ADR number present
8. Read `docs/plans/Phase2 Complete Implementation Plan.md` — specifically R0.1 through R0.5
9. Read `tests/COVERAGE_MANIFEST.yaml` — note which entries have `deferred_to:` and which don't

**Declaration format:**

```
SESSION START — Agent: {id} (Session 11 — R0 Reconciliation)
Files read: AGENTS.md ✓, HANDOFF_NOTES ✓, CURRENT_FOCUS ✓, agent spec ✓, 
learning ✓, incidents ✓, DECISIONS.md ✓ (last ADR: ADR-NNN), 
Phase 2 Plan R0 section ✓, COVERAGE_MANIFEST ✓
Task: R0 Framework Reconciliation — 9 steps, documentation only, no code
Scope constraint: NO service code, NO migration files, NO test file changes
```

---

## STEP 1: ADR Gap Verification (30-60 min)

The entire reason R0 exists is because ADRs 009-019 were flagged as missing across three review iterations (the ADR-008 → ADR-020 gap). Before creating any new ADRs, verify the current state.

### 1a. Run the ADR verifier

```powershell
cd F:\Synaptix
python scripts/verify_adr_sequence.py
```

Record the EXACT output in your session log.

### 1b. If the verifier reports GAPS between ADR-001 and ADR-029

Create every missing ADR using the specifications below. Each retroactive ADR must use:

```markdown
## ADR-NNN: [Title]

**Date:** [Best estimate from session logs — when was this actually decided?]
**Status:** Accepted (Retroactive — formalised YYYY-MM-DD in Session 11)
**Deciders:** Human supervisor + Agent {id}
```

The 11 potentially missing ADRs and their content:

**ADR-009: Composite Foreign Key Strategy for Tenant Integrity**

- Context: Multi-tenant system needs structural prevention of cross-tenant FK relationships
- Decision: All cross-table FKs include tenant_id as composite. Target tables expose UNIQUE (tenant_id, id). This makes cross-tenant FK violations structurally impossible at the database level, not just at application level.
- Alternatives: Application-level tenant checks only (rejected: single layer of defence); database-per-tenant (rejected: operational complexity at current scale)
- Consequences: (+) Three-layer tenant isolation. (-) Every new table needs UNIQUE (tenant_id, id) added. (-) Composite FKs are verbose in migration files.

**ADR-010: Immutable Versioning Pattern via is_current Flag**

- Context: Entities like curricula and lesson plans need version history without losing prior versions
- Decision: Versioned entities use append-only rows with `is_current = TRUE` on the active version. Previous versions retained with `is_current = FALSE`. Enforced via partial unique index: `UNIQUE (tenant_id, entity_key) WHERE is_current = TRUE AND deleted_at IS NULL`.
- Alternatives: Soft-delete and replace (rejected: loses version history); separate version table (rejected: query complexity for current version); temporal tables (rejected: PostgreSQL support insufficient)
- Consequences: (+) Full audit trail of all versions. (+) Easy rollback (swap is_current flags). (-) Queries must filter `WHERE is_current = TRUE` by default.

**ADR-011: workflow_transitions Dual-Write with JSONB History**

- Context: Workflow state changes need both queryable relational records AND a compact history for display
- Decision: State changes write to both `workflow_transitions` table (relational, one row per transition) AND an inline JSONB `history` array on `workflow_instances`. Both writes happen in the same database transaction for atomicity.
- Alternatives: Relational only (rejected: history display requires N+1 queries); JSONB only (rejected: hard to query transitions across instances)
- Consequences: (+) Fast history display from JSONB. (+) Queryable transitions for reporting. (-) Dual-write adds complexity and must be atomic.

**ADR-012: Abstract StorageProvider Interface for Digital Assets**

- Context: Digital assets need to work with local filesystem in development and cloud storage (GCS) in production
- Decision: Digital assets module exposes abstract `StorageProvider` interface with `upload()`, `download()`, `delete()`, `get_url()` methods. `LocalStorageProvider` for dev, `GCSStorageProvider` for production. Provider selected via environment variable.
- Alternatives: Direct GCS SDK calls everywhere (rejected: breaks local dev); S3-compatible API for both (rejected: adds unnecessary abstraction layer for local)
- Consequences: (+) Zero-cost local development. (+) Provider swap requires no service code changes. (-) Interface must be maintained as providers are added.

**ADR-013: attendance_category Enum Schema Design**

- Context: Attendance records need to track category (theory, practical, clinical, etc.) for threshold calculations
- Decision: Single VARCHAR column `attendance_category` with CHECK constraint listing valid values, rather than separate boolean columns (is_theory, is_practical, etc.).
- Values: 'theory', 'practical', 'clinical', 'doap', 'ece', 'aetcom', 'foundation_course', 'elective'
- Alternatives: Boolean columns per category (rejected: adding a category requires migration); separate category table with FK (rejected: over-normalisation for a fixed set)
- Consequences: (+) Adding a category = one ALTER TABLE. (+) Cleaner queries. (-) CHECK constraint must be updated when adding categories.

**ADR-014: Faculty-Course Assignment via Junction Table**

- Context: Faculty need to be assigned to courses, with support for multiple faculty per course and historical tracking
- Decision: Faculty assigned to courses via `faculty_course_assignments` junction table with composite PK (tenant_id, faculty_id, course_id), effective dates, and role designation. NOT a direct FK from courses to faculty.
- Alternatives: Direct FK (rejected: only one faculty per course); JSONB array of faculty_ids (rejected: not queryable, no referential integrity)
- Consequences: (+) Multiple faculty per course. (+) Historical assignment tracking via effective dates. (+) Role designation (primary, guest, substitute). (-) Additional JOIN required for course queries.

**ADR-015: Lesson Plan to Workflow Engine Integration**

- Context: Lesson plans require an approval workflow (draft → submitted → approved → published)
- Decision: Lesson plans use the generic workflow engine (workflow_instances + workflow_transitions) instead of a bespoke lesson_plan_approvals table. One workflow engine serves all entity types.
- Alternatives: Bespoke approval table (rejected: duplicates workflow engine logic); status column with no audit trail (rejected: NMC inspection requires approval evidence)
- Consequences: (+) Single workflow engine for all approval flows. (+) Full audit trail. (-) Requires workflow_definition seed for lesson_plan type.

**ADR-016: Lesson Plan Versioning Strategy**

- Context: Lesson plans need versioning (faculty revises plan mid-semester)
- Decision: Uses the is_current pattern from ADR-010. Partial unique index: `UNIQUE (tenant_id, course_id, topic) WHERE is_current = TRUE AND deleted_at IS NULL`. Previous versions retained for audit.
- Alternatives: In-place update with audit log (rejected: loses full version content); Git-like diff storage (rejected: over-engineering for document-sized content)
- Consequences: (+) Full version history. (+) Easy comparison between versions. (-) Storage grows with versions (acceptable for text content).

**ADR-017: Integration Sessions via event_courses Junction**

- Context: Some teaching sessions span multiple courses (e.g., integrated teaching of Anatomy + Physiology). Need to model multi-course events.
- Decision: Multi-course integration sessions modelled via `event_courses` junction table. The `primary_course_id` column on `events` is removed; primary designation is a boolean flag on the junction row.
- Alternatives: Keep primary_course_id + secondary array (rejected: arbitrary limit on courses); duplicate event per course (rejected: attendance tracking nightmare)
- Consequences: (+) Unlimited courses per event. (+) Clear primary designation. (-) Additional JOIN for course queries.

**ADR-018: Syllabus Coverage Triple-Metric Tracking**

- Context: NMC inspection requires evidence that syllabus was planned, taught, AND assessed
- Decision: Syllabus coverage tracked across three independent dimensions: topics_planned (from lesson plans), topics_taught (from conducted events), topics_assessed (from assessments). All three must be queryable independently.
- Alternatives: Single coverage percentage (rejected: doesn't distinguish "planned but not taught" from "taught but not assessed"); binary taught/not-taught (rejected: loses assessment dimension)
- Consequences: (+) Precise inspection reports. (+) Gap identification (planned but not taught, taught but not assessed). (-) Three tracking dimensions add complexity.

**ADR-019: Curriculum Migration as Audit Log Only**

- Context: When migrating students from CBME 2019 to CBME 2023 curriculum, how to handle historical records
- Decision: Migration creates audit log entries recording "student X moved from curriculum A to curriculum B on date D." Historical academic records (attendance, marks, logbook) remain under the curriculum in which they were recorded. No retroactive data modification.
- Alternatives: Retroactive relabelling (rejected: falsifies historical records); dual-curriculum period (rejected: attendance thresholds become ambiguous)
- Consequences: (+) Historical integrity preserved. (+) Clean audit trail. (-) Reports must handle students with records under multiple curricula.

### 1c. If the verifier reports NO gaps (ADR-001 through ADR-029 all present)

List every ADR title from 001 to 029 in the session log as evidence:

```markdown
## ADR Verification Evidence

ADR-001: [title]
ADR-002: [title]
...
ADR-029: [title]

All present. No gaps. Verified by verify_adr_sequence.py output [attached].
```

---

## STEP 2: Create ADRs 030-037 (60-90 min)

Create 8 new ADRs in `docs/DECISIONS.md` using `templates/ADR_TEMPLATE.md` format.

### ADR-030: AETCOM Sync via Service Layer (not DB Trigger)

- **Context:** AETCOM module completion depends on attendance + reflection submission + faculty sign-off. This is non-linear logic unsuitable for a database trigger.
- **Decision:** AETCOM sync is implemented in service-layer Python (`aetcom_sync_service.on_attendance_change()`), not as a database trigger. Called from: attendance_service.mark_attendance(), logbook_service.submit_aetcom_reflection(), logbook_service.signoff_aetcom_module().
- **Alternatives:** Database trigger (rejected: cross-module, non-linear, would need to query multiple tables)
- **Status:** Accepted
- **Source:** Phase 2 Complete Plan R0.3

### ADR-031: Two-Phase NOT NULL Migration for courses.subject_code

- **Context:** Adding `subject_code` to existing `courses` table. Column is NOT NULL but existing rows have no value. Cannot use DEFAULT 'ANAT' (would incorrectly mark all courses as Anatomy).
- **Decision:** Three-step migration: (1) Add column as NULLABLE. (2) Run admin backfill script (`scripts/admin/backfill_subject_codes.py`) per tenant. (3) Follow-up migration adds NOT NULL constraint after backfill verified.
- **Alternatives:** DEFAULT 'ANAT' (rejected: data corruption); DEFAULT 'TBD' sentinel (rejected: TBD is not a valid subject code)
- **Status:** Accepted
- **Source:** Phase 2 Complete Plan R0.3

### ADR-032: Logbook Elective Discriminator — NULLABLE subject_code

- **Context:** logbook_entries stores both regular entries (with subject_code) and elective entries (with elective_id). Need a discriminator pattern.
- **Decision:** Make subject_code NULLABLE. CHECK constraint: `(elective_id IS NULL AND subject_code IS NOT NULL) OR (elective_id IS NOT NULL AND subject_code IS NULL)`. This replaces the original sentinel value approach (subject_code = 'ELECTIVE') which was fragile.
- **Alternatives:** Sentinel string 'ELECTIVE' (rejected: magic string, fragile); separate tables (rejected: complicates portfolio queries)
- **Status:** Accepted
- **Source:** Phase 2 Complete Plan R0.3

### ADR-033: internship_rotations Scaffolded in Phase 2 for FK Validity

- **Context:** leave_requests has FK to internship_rotations (for CRMI intern leave caps), but the full internship module is Phase 4.
- **Decision:** Create a minimal scaffold table (id, tenant_id, student_id, department, dates, status) in Phase 2 to make the FK valid. Phase 4 adds the full CRMI rotation logic, expanding the table.
- **Alternatives:** Defer rotation_id column to Phase 4 (rejected: loses the link for leave requests now); remove FK and use application-level check (rejected: breaks composite FK discipline)
- **Status:** Accepted
- **Source:** Phase 2 Complete Plan R0.3

### ADR-034: Elective Allocation Algorithm (FCFS + Ranked)

- **Context:** NMC CBME 2019 mandates two 2-week elective blocks. Students rank preferences; allocator assigns based on preferences and capacity.
- **Decision:** Two algorithms implemented, selectable per tenant via MDM configuration:
  - FCFS (first_come_first_served): default. Processes preferences ordered by submitted_at.
  - Ranked (ranked): processes rank-by-rank across all students. Rank-1 for everyone first, then rank-2 for unallocated students, etc. Tie-breaking within a rank tier: earliest submitted_at, then deterministic hash.
- **Operational endpoint:** POST /electives/allocate with dry_run flag, algorithm selection, force_reallocate modes (additive/full).
- **Cross-block constraint:** Same elective_id cannot be allocated in both Block 1 and Block 2 for a student.
- **Audit:** Every run creates an elective_allocation_runs row.
- **Worked example:** 10 students, 3 electives (A/B/C capacity 4). Expected: A=4 (S1-S4), B=4 (S5-S8), C=2 (S9-S10), 0 unallocated. Verified in Session 10 Phase A.
- **Status:** Accepted
- **Source:** Phase 2 Complete Plan R1.2

### ADR-035: DOAP State Machine (D→O→A→P Progression)

- **Context:** NMC CBME 2019 mandates DOAP progression for procedural skills.
- **Decision:** State machine with stages NOT_STARTED → DEMONSTRATED → OBSERVED → ASSISTED → PERFORMED → CERTIFIED. Implemented as pure validator functions (doap_validators.py) for testability.
- **Rules:**
  - Stage progression requires ALL prior stages to have at least one C-decision record
  - Backward attempts allowed (refresher D after reaching O)
  - Multiple sessions per stage allowed
  - Faculty decision codes: C (Certify), R (Repeat), Re (Remediate)
  - Attempt types: F (First), R (Repeat), Re (Remediation)
  - Rating B + decision C is INVALID (DOAP-NMC-003 compliance)
- **Cross-module integration:** Auto-creates logbook_entries; Re decision auto-creates remediation workflow_instance; evidence via JSONB asset IDs.
- **Status:** Accepted
- **Source:** Phase 2 Complete Plan R1.3

### ADR-036: Leave-to-Attendance Materialisation

- **Context:** When a student's leave is approved, attendance rows must be automatically created/updated for events during the leave window.
- **Decision:** Materialisation happens at leave approval time (status pending → approved) via service-layer function `leave_service.on_approval()`.
- **Status mapping:** medical leave → attendance status 'medical'; academic/casual/other → 'excused'.
- **Conflict rules:**
  - If no attendance row exists for an event in the leave window: CREATE with leave status
  - If attendance row exists with status != 'present': UPDATE to leave status, set needs_review=true
  - If attendance row exists with status == 'present': DO NOT override (student actually attended despite approved leave; log warning)
- **Future events:** When a new event is created within an existing approved leave window, an event-creation hook checks for active leaves and auto-creates the attendance row.
- **Rejection rollback:** When a previously-approved leave is rejected or cancelled, materialised attendance rows are soft-deleted and a compliance_incidents row is logged.
- **Status:** Accepted
- **Source:** Phase 2 Complete Plan R1.4

### ADR-037: Attendance Conflict Resolution Semantics

- **Context:** Same attendance can be marked twice (faculty A marks present, faculty B marks absent; or offline + online sync collision). Need deterministic resolution.
- **Decision:** Conflict resolution key: latest of MAX(original_marked_at, marked_at) wins.
- **Worked examples:**
  - Two online marks: Faculty A at 10:00, Faculty B at 11:00. B wins (later wall-clock).
  - Online then offline-sync: Faculty A online at 10:00; Faculty B offline at 09:30, syncs at 12:00. B wins (MAX(09:30, 12:00) = 12:00 > 10:00). But marked_at - original_marked_at > 2 hours: flag needs_review.
  - Two offline syncs: A marked at 09:00, synced at 14:00; B marked at 09:05, synced at 13:00. A wins (MAX(09:00, 14:00) = 14:00 > 13:00). BOTH flagged needs_review (different original times within 5 minutes is suspicious).
- **Implementation:** Service-layer Python (not ON CONFLICT SQL — too complex for SQL expression). Unique constraint UNIQUE (tenant_id, event_id, student_id) WHERE deleted_at IS NULL prevents duplicate live rows.
- **needs_review flagging:** Flagged when (a) existing row had different original_marked_at within 10 minutes, (b) sync gap > 2 hours, (c) status changes from present to non-present.
- **Status:** Accepted
- **Source:** Phase 2 Complete Plan R1.5

### Post-Step 2 Verification

```powershell
python scripts/verify_adr_sequence.py
```

Expected output: `ADR-001 through ADR-037: all present. No gaps detected.`

If it doesn't output this, fix before proceeding.

---

## STEP 3: Verifier Baseline Capture (15-20 min)

Create the verification directory and capture baselines:

```powershell
New-Item -ItemType Directory -Force -Path docs\verification

python scripts/verify_adr_sequence.py 2>&1 | Tee-Object docs/verification/baseline_adr_$(Get-Date -Format yyyyMMdd).txt

python scripts/verify_coverage_manifest.py 2>&1 | Tee-Object docs/verification/baseline_coverage_$(Get-Date -Format yyyyMMdd).txt

python scripts/verify_edge_case_coverage.py 2>&1 | Tee-Object docs/verification/baseline_edge_cases_$(Get-Date -Format yyyyMMdd).txt

python scripts/verify_compliance_coverage.py 2>&1 | Tee-Object docs/verification/baseline_compliance_$(Get-Date -Format yyyyMMdd).txt
```

These files are the Phase 2 measurement baseline. Commit them. Do NOT delete them later. R5 (Phase 2 completion) will compare final state against these baselines.

Record the key numbers in your session log:

```markdown
## Verifier Baseline (YYYY-MM-DD)

- ADR sequence: ADR-001 through ADR-037 (no gaps)
- Coverage manifest: X total tests, Y present, Z missing, W deferred
- Edge case coverage: X catalogued, Y with tests, Z without
- Compliance coverage: X declared, Y implemented, Z logged
```

---

## STEP 4: Test Categorisation (60-90 min)

This is the most important analytical work in R0. Read the coverage manifest verifier output from Step 3. For every test ID in the manifest, categorise it.

Create `docs/verification/phase2_test_categorisation.md`:

```markdown
# Phase 2 Test Categorisation

**Date:** YYYY-MM-DD
**Created by:** Agent {id}, Session 11
**Baseline verifier run:** docs/verification/baseline_coverage_YYYYMMDD.txt

## Summary

| Category | Count |
|----------|-------|
| Already passing | NN |
| Must pass in Phase 2 (currently xfail or missing) | NN |
| Deferred to Phase 2.5 | NN |
| Deferred to Phase 3+ | NN |
| **Total in manifest** | **NNN** |

## Categorisation Rules Applied

- **Must pass Phase 2:** Feature is implemented or should be implemented before Phase 2 completion. Test must pass.
- **Phase 2.5:** Offline mobile sync, RFID hardware, GPS geofencing, biometric integration — hardware/mobile dependencies that cannot be tested without physical devices or mobile app.
- **Phase 3+:** Face recognition, advanced analytics, full admission verification engine, recurring invoice engine — features not yet scoped.
- **Default rule:** When in doubt, categorise as "Must pass Phase 2." Stricter is safer.

## Full Categorisation Table

| Test ID | Module | Current Status | Must Pass Phase 2? | Deferral Target | Reason for Deferral |
|---------|--------|----------------|---------------------|-----------------|---------------------|
```

Then populate the table with EVERY test ID from COVERAGE_MANIFEST.yaml. For each:

- **Current Status:** one of `passing`, `xfail`, `missing` (no stub exists), `deferred` (already has deferred_to)
- **Must Pass Phase 2?:** `Yes` or `No`
- **Deferral Target:** blank if must-pass; `Phase 2.5` or `Phase 3` if deferred
- **Reason for Deferral:** specific reason (not just "deferred")

### Categorisation guidance per module

**Attendance Engine (A-11):**
- ATT-001, ATT-002, ATT-003 (manual + QR marking): Must pass Phase 2
- ATT-004 (RFID): Phase 2.5 — hardware integration
- ATT-005 (face recognition): Phase 3 — ML model required
- ATT-006 (GPS geofencing): Phase 2.5 — mobile app required
- ATT-007 (biometric): Phase 3 — hardware integration
- ATT-008..010 (summary, view, conflict): Must pass Phase 2
- ATT-NMC-001..005, ATT-NMC-015: Must pass Phase 2 — compliance is non-deferrable
- ATT-E001..E010: Must pass Phase 2 — edge cases for implemented features

**Leave Management (A-12):**
- All LEAVE tests: Must pass Phase 2 (feature is fully implemented)

**Electives (A-08):**
- All ELEC tests: Must pass Phase 2 (feature is fully implemented)
- Exception: ELEC tests requiring mobile preference submission UI → Phase 2.5

**DOAP Skills (A-09):**
- All DOAP tests: Must pass Phase 2 (feature is fully implemented)
- Exception: DOAP-007 (evidence asset linkage) if digital asset upload not yet working → Phase 2.5

**Digital Logbook (A-10):**
- All LOG tests: Must pass Phase 2 (feature should be implemented in Sessions 12-13)

**Any test IDs from Phase 1A/1B modules:**
- Categorise based on whether the feature exists in code. If code exists, test must pass.

---

## STEP 5: Update COVERAGE_MANIFEST with deferred_to Fields (30-45 min)

For every test categorised as "Phase 2.5" or "Phase 3+" in Step 4, add the `deferred_to:` field to the corresponding entry in `tests/COVERAGE_MANIFEST.yaml`.

Example before:
```yaml
    - id: ATT-004
      description: "RFID-based attendance marking"
      type: unit
```

Example after:
```yaml
    - id: ATT-004
      description: "RFID-based attendance marking"
      type: unit
      deferred_to: "Phase 2.5"
```

After updating ALL deferred tests, re-run the coverage manifest verifier:

```powershell
python scripts/verify_coverage_manifest.py 2>&1 | Tee-Object docs/verification/post_deferral_coverage_$(Get-Date -Format yyyyMMdd).txt
```

Compare the missing test count against the baseline from Step 3:

```markdown
## Deferral Impact

- Baseline missing tests: Z
- After deferral acknowledgement: Z' (Z' should be significantly lower)
- Delta: Z - Z' tests now acknowledged as deferred
- Remaining "must implement": Z' tests
```

This Z' number is your Phase 2 completion target. R5 succeeds when Z' = 0.

---

## STEP 6: Create docs/PHASE2_SCHEMA.md (60-90 min)

Create a single reference document containing the complete Phase 2 database schema specification. This is NOT a migration file — it is the SPEC that migrations implement. This is the document you hand to an NMC inspector or a new developer.

### 6a. Document structure

```markdown
# Phase 2 Database Schema Specification

**Version:** 1.0
**Date:** YYYY-MM-DD
**Status:** Implemented (migrations 0011-0014)
**Author:** Session 11 reconciliation

## Overview

Phase 2 adds 15 tables, modifies 1 table, creates 1 view, and adds 2 database triggers
to support Attendance, Leave, Electives, DOAP Skills, Digital Logbook, and Admission modules.

## Tables Added

### 1. attendance
[Full column list with types, constraints, FKs, indexes]

### 2. attendance_summary
[Full DDL including GENERATED ALWAYS AS column]

### 3. attendance_exemptions
...

### 4. attendance_accommodations
...

### 5. leave_requests
...

### 6. electives
...

### 7. elective_allocations
...

### 8. student_elective_preferences
[Include the block column and both unique indexes from R0.3 corrections]

### 9. elective_allocation_runs
[From migration 0014]

### 10. logbook_entries
[With NULLABLE subject_code per ADR-032]

### 11. logbook_assessments
...

### 12. doap_session_records
[Including evidence_asset_ids JSONB]

### 13. admission_applications
[Placeholder — minimal schema]

### 14. internship_rotations
[Scaffold per ADR-033]

### 15. compliance_incidents
[From R0.3 Foundation Course trigger rewrite]

## Tables Modified

### courses
- Added: subject_code VARCHAR(50) NULL (NOT NULL added post-backfill per ADR-031)

## Views

### subject_attendance_summary
[Full CREATE VIEW DDL]

## Triggers

### fn_sync_attendance_to_foundation_course
[Corrected version from Phase 2 Plan R0.3 — uses events for hours calculation,
logs to compliance_incidents instead of RAISE EXCEPTION]

### fn_verify_attendance_session_event
[From Phase 2 Plan R0.3 — validates session_id belongs to event_id]

## Service-Layer Sync Functions

### aetcom_sync_service.on_attendance_change()
[Per ADR-030 — called from attendance marking, logbook reflection, faculty signoff]

### leave_service.on_approval()
[Per ADR-036 — materialises attendance rows for leave window]

### attendance_service.on_marked()
[Calls aetcom_sync if category=aetcom; calls Foundation Course trigger indirectly]
```

### 6b. Cross-reference against actual migrations

After writing the schema spec, cross-reference every table against the actual migration files (0011-0014). For ANY discrepancy between the spec and the migration, note it clearly:

```markdown
> ⚠️ DISCREPANCY: Migration 0012 defines elective_allocations.allocated_at as TIMESTAMPTZ
> but this spec (per Phase 2 Plan) says TIMESTAMP. Reconciliation needed before Phase 2
> completion. Filed as item in HANDOFF_NOTES.
```

If no discrepancies found, state explicitly:

```markdown
> ✅ Schema spec cross-referenced against migrations 0011-0014. No discrepancies found.
```

---

## STEP 7: Convention Updates (30 min)

Append 3 new sections to `conventions/DATABASE_CONVENTIONS.md`.

### Section: Cross-Reference Integrity Triggers

```markdown
## Cross-Reference Integrity Triggers

PostgreSQL does NOT allow subqueries in CHECK constraints. When you need to validate
that a column value in one table is consistent with a value in another table, use a
BEFORE INSERT/UPDATE trigger instead.

### Pattern

```sql
CREATE OR REPLACE FUNCTION fn_verify_{table}_{column}_consistency()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.{nullable_column} IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM {target_table}
            WHERE id = NEW.{nullable_column}
              AND tenant_id = NEW.tenant_id
              AND {consistency_column} = NEW.{consistency_value}
              AND deleted_at IS NULL
        ) THEN
            RAISE EXCEPTION '{column} % does not belong to {parent} %',
                NEW.{nullable_column}, NEW.{consistency_value}
            USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_verify_{table}_{column}
BEFORE INSERT OR UPDATE OF {nullable_column}, {consistency_value} ON {table}
FOR EACH ROW
EXECUTE FUNCTION fn_verify_{table}_{column}_consistency();
```

### Example: attendance.session_id must belong to attendance.event_id

See `fn_verify_attendance_session_event` in PHASE2_SCHEMA.md.

### When NOT to use this pattern

If the integrity can be expressed as a simple CHECK on a single table's columns
(e.g., `CHECK (end_date > start_date)`), use a CHECK constraint. Triggers are
for cross-table validation only.
```

### Section: Composite Foreign Key Requirements

```markdown
## Composite Foreign Key Requirements

In the Synaptix multi-tenant architecture, every cross-table foreign key MUST be
composite (tenant_id + target_id) to prevent cross-tenant references.

### Rule

1. Every tenant-scoped table MUST have: `UNIQUE (tenant_id, id)`
2. Every FK to a tenant-scoped table MUST be: `FOREIGN KEY (tenant_id, target_id) REFERENCES target_table(tenant_id, id)`
3. Never use a single-column FK to a tenant-scoped table

### Migration template for adding to existing tables

```sql
-- Add composite unique if missing
ALTER TABLE {table_name}
    ADD CONSTRAINT uq_{table_name}_tenant_id_id UNIQUE (tenant_id, id);
```

### Rationale

Single-column FKs (just target_id) allow a row in tenant A to reference a row
in tenant B if both happen to have the same UUID. Composite FKs make this
structurally impossible at the database level.

See ADR-009 for the full decision record.
```

### Section: Trigger vs Service Layer Decision Matrix

```markdown
## Trigger vs Service Layer Decision Matrix

| Use Case | Trigger | Service Layer | Reason |
|----------|---------|---------------|--------|
| Derived column update (same table) | ✓ | | Simple, no cross-table logic |
| Cross-reference integrity validation | ✓ | | Must enforce at DB level |
| Audit log append | ✓ | | Fire-and-forget, no business logic |
| Cross-module synchronisation | | ✓ | Multiple tables, potentially multiple services |
| Business workflow steps | | ✓ | Complex branching, external calls possible |
| Anything requiring HTTP calls | | ✓ | Triggers cannot make HTTP calls |
| Non-linear completion logic | | ✓ | E.g., AETCOM (depends on attendance + reflection + signoff) |

### Rule of thumb

If the logic fits in 20 lines of PL/pgSQL and touches only the current table
(or one directly-related table), use a trigger. Otherwise, use service-layer code.

### Examples

- Foundation Course hours recalculation → trigger (reads attendance, updates foundation_course_records)
- AETCOM module completion → service layer (reads attendance + logbook + signoff, non-linear logic)
- Leave-to-attendance materialisation → service layer (creates rows in attendance, may create workflow_instances)

See ADR-030 for the AETCOM decision rationale.
```

---

## STEP 8: Tracking Documents Update (15 min)

Update all standard tracking documents:

### docs/CHANGELOG.md

```markdown
## [Session 11] — YYYY-MM-DD

### Documentation
- Completed R0 Framework Reconciliation
- Created/verified ADRs 001-037 (no gaps)
- Created docs/PHASE2_SCHEMA.md — complete Phase 2 database specification
- Created docs/verification/phase2_test_categorisation.md
- Captured verifier baselines in docs/verification/
- Updated COVERAGE_MANIFEST.yaml with deferred_to fields for N deferred tests
- Added 3 sections to conventions/DATABASE_CONVENTIONS.md
- Phase 2 completion target established: N tests must pass
```

### docs/DEVELOPMENT_LOG.md

Add Session 11 entry with high-level summary.

### docs/COMMAND_HISTORY.md

Record every command run this session.

### docs/sessions/YYYY-MM-DD-session-11.md

Create complete session log using `templates/SESSION_LOG_TEMPLATE.md`.

### .agent-memory/working/CURRENT_FOCUS.md

```markdown
# Current Focus

**Last updated:** YYYY-MM-DD
**Last updated by:** Agent {id} (Session 11)

## Current Phase

R0 COMPLETE. Phase 2 ongoing.

## Phase 2 Completion Target

- Total tests in manifest: NNN
- Must pass in Phase 2: NN
- Currently passing: NN
- Remaining to implement: NN
- Deferred to Phase 2.5: NN
- Deferred to Phase 3+: NN

## Next Session (12)

R4.5 — Logbook Phase 2 extensions:
- IA marks calculation (cap 20%)
- Backdating rules (>7 days flag, >30 days HOD)
- NMC signature fields validation
- Tests: LOG-001..006, LOG-NMC-008..012

## R0 Status

COMPLETE. All acceptance criteria satisfied.
Verifier baselines captured. Test categorisation done.
ADR audit trail intact (001-037, no gaps).
```

### docs/HANDOFF_NOTES.md

Remove the "CRITICAL SESSION 11 IS R0 ONLY" directive (it has been satisfied). Replace with:

```markdown
## Session 11 Complete — R0 Reconciliation Done (YYYY-MM-DD)

R0 Framework Reconciliation is COMPLETE. The longest-running framework debt in
Phase 2 is now closed. ADR audit trail is intact. Verifier baselines are captured.
Test categorisation establishes the Phase 2 completion target.

**Phase 2 completion target: NN tests must pass (currently NN passing, NN remaining).**

### Next sessions:

[TO: 02-backend] Session 12: R4.5 — Logbook Phase 2 extensions
  - IA marks calculation, backdating rules, NMC signature fields
  - Coverage manifest entries: LOG-001..006, LOG-NMC-008..012
  - Test stubs first, then service code

[TO: 02-backend] Session 13: R4.6 — Admission placeholder (minimal CRUD)

[TO: 02-backend] Session 14: R4 gap-closure — integration items, xfail conversion

[TO: 06-testing] — Pending test implementations from Sessions 9-10:
  - ELEC integration tests (ELEC-003..007, ELEC-009)
  - DOAP integration tests (DOAP-006, DOAP-007, DOAP-E002)

[TO: 11-compliance] — Audit compliance tests:
  - Verify ELEC-NMC-001..004 against full NMC CBME 2019 regulation text
  - Verify DOAP-NMC-001..003 against full NMC CBME 2019 regulation text
  - Identify any missing compliance tests

[DISCREPANCY] — If any schema discrepancies were found in Step 6b, list them here
with resolution plan.

[DEBT] — Subject code inference in DOAP service uses hardcoded mapping (D7 from
Session 10). Must be MDM-driven by Phase 2.5.
```

---

## STEP 9: Final Verification (10 min)

Run ALL verifiers one final time:

```powershell
python scripts/verify_adr_sequence.py
python scripts/verify_coverage_manifest.py
python scripts/verify_edge_case_coverage.py
python scripts/verify_compliance_coverage.py
python scripts/check_secrets.py
```

ALL must pass. If any fail, STOP and fix before committing.

Then commit:

```powershell
git add .
git commit -m "docs: Session 11 — R0 Framework Reconciliation complete

- ADRs 001-037 verified sequential, no gaps
- ADRs 030-037 created (AETCOM sync, subject_code migration, NULLABLE discriminator,
  internship_rotations scaffold, elective allocation, DOAP state machine,
  leave-to-attendance materialisation, conflict resolution)
- Verifier baselines captured in docs/verification/
- Phase 2 test categorisation: NN must-pass, NN deferred
- COVERAGE_MANIFEST updated with deferred_to fields
- docs/PHASE2_SCHEMA.md created with complete schema spec
- conventions/DATABASE_CONVENTIONS.md: 3 new sections
- R0 acceptance criteria: all satisfied

This closes the R0 framework debt deferred since Session 5.
Phase 2 completion target: NN tests must pass.

Refs: Phase 2 Complete Plan R0.1-R0.5
"
```

Do NOT use `--no-verify`. If the pre-commit hook fails, diagnose and fix.

---

## Session End Declaration

```
SESSION END — Agent: {id} (Session 11 — R0 Reconciliation)
Duration: ~X hours
Scope: Documentation only — no code, no migrations, no test changes

ADRs created/verified: 037 total (no gaps)
Verifier baselines: 4 files captured in docs/verification/
Test categorisation: NN must-pass / NN deferred / NNN total
Schema specification: docs/PHASE2_SCHEMA.md (15 tables, 1 view, 2 triggers)
Convention updates: 3 new sections in DATABASE_CONVENTIONS.md
Pre-commit hook: passed (no --no-verify)
Documentation updated: ✓
Memory updated: ✓

R0 STATUS: COMPLETE
Phase 2 completion target: NN tests must pass

Next session (12): R4.5 — Logbook Phase 2 extensions
```

---

## Acceptance Criteria Checklist

Every item must be true before declaring Session 11 complete:

- [ ] `docs/DECISIONS.md` contains ADR-001 through ADR-037 with no gaps
- [ ] `python scripts/verify_adr_sequence.py` confirms no gaps
- [ ] ADR-036 (Leave-to-Attendance Materialisation) exists with conflict rules and worked example
- [ ] ADR-037 (Attendance Conflict Resolution) exists with 3 worked examples
- [ ] `docs/verification/` contains 4+ baseline files from Step 3
- [ ] `docs/verification/phase2_test_categorisation.md` exists with complete table covering every manifest entry
- [ ] Summary table shows counts for: already passing, must-pass, Phase 2.5, Phase 3+
- [ ] `tests/COVERAGE_MANIFEST.yaml` has `deferred_to:` fields for ALL deferred tests
- [ ] Post-deferral verifier run shows reduced missing count vs baseline (delta documented)
- [ ] `docs/PHASE2_SCHEMA.md` exists with all 15 tables, 1 view, 2 triggers fully specified
- [ ] Schema spec cross-referenced against migrations 0011-0014 (discrepancies noted or clean bill)
- [ ] `conventions/DATABASE_CONVENTIONS.md` has 3 new sections (triggers, composite FKs, decision matrix)
- [ ] All 5 verifiers pass in Step 9
- [ ] Committed without `--no-verify`
- [ ] Session log complete in `docs/sessions/`
- [ ] HANDOFF_NOTES updated with Session 12 scope and deferred items
- [ ] CURRENT_FOCUS updated with Phase 2 completion target numbers

**If any item cannot be completed:** Do NOT skip it and declare the session done. Report what's blocking. R0 partial completion defeats the purpose — R0 either happened or it didn't.

---

## Failure Modes to Watch For

1. **Transcription without understanding.** Do not copy ADR content mechanically from the Phase 2 Plan. Read each decision. Verify it matches what was actually implemented. If implementation diverges from the plan (e.g., the agent made a different choice in Session 8), the ADR documents what was ACTUALLY decided, not what the plan proposed.

2. **Optimistic test categorisation.** Do not categorise tests as "Phase 2.5" to make the must-pass count smaller. If the feature is implemented, the test must pass. Phase 2.5 is for genuine hardware/mobile dependencies only.

3. **Skipping the schema cross-reference.** Step 6b requires comparing PHASE2_SCHEMA.md against actual migrations. This is where you discover if the implementation matches the spec. Do not skip this comparison.

4. **Rushing to finish.** R0 is 5-7 hours of work. If you finish in 2 hours, you skipped something. Re-read the acceptance criteria checklist.

5. **Creating ADRs for decisions not yet made.** ADRs 030-037 are for decisions that HAVE BEEN made (in the plan or in code). If you encounter a decision that hasn't been made yet, do NOT create an ADR with Status: Proposed — instead, write it to `.agent-memory/working/QUESTIONS.md` and flag in HANDOFF_NOTES.

---

*R0 is the foundation that makes Phase 2 measurable. Without it, "Phase 2 complete" is a feeling, not a fact. After this session, it's a number.*