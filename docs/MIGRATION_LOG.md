# Migration Log

Every database migration with rollback notes.

## Format

```markdown
### Migration: YYYYMMDD_revision_description

**Created:** YYYY-MM-DD
**Agent:** Database Agent
**Revision ID:** abc123
**Depends on:** def456

**Purpose:**
What this migration does and why.

**Changes:**
- Added table/column/index
- Removed ...
- Modified ...

**Data Migration:**
Backfill performed (or NONE).

**Rollback Tested:** Yes / No

**Verification:**
After applying, verify:
- Test: ...

**Related:**
- NMC ref: ...
- Audit ref: ...
- Commit: ...
```

## Migrations

### Migration: 20260620_0001_foundation_tables
**Created:** 2026-06-20
**Agent:** Database Agent (05)
**Revision ID:** 20260620_0001
**Depends on:** None

**Purpose:**
Initialize foundation tables including tenants, users, roles, user_roles, and partitioned append-only audit log. Enforce RLS on all tenant-scoped tables.

**Changes:**
- Created tables: tenants, users, roles, user_roles, audit_log (partitioned for 2026 and 2027)
- Added triggers for auto-updating updated_at
- Enabled RLS and created policies for user isolation
- Seeded JMN tenant and system roles

**Rollback Tested:** Yes

**Verification:**
- Connect to localhost:5435/synaptix_dev and verify public tables list

---

### Migration: 20260620_0002_create_academic_structure_tables
**Created:** 2026-06-20
**Agent:** Database Agent (05)
**Revision ID:** 20260620_0002
**Depends on:** 20260620_0001

**Purpose:**
Scaffold Module A-01 Academic Structure tables by creating academic_years, programs, and curricula tables.

**Changes:**
- Created tables: academic_years, programs, curricula
- Enabled RLS policies and tenant isolation filters
- Added triggers for auto-updating updated_at

**Rollback Tested:** Yes

**Verification:**
- Run alembic upgrade/downgrade cycles and check information_schema tables

---

### Migration: 20260620_0003_add_user_otp_fields
**Created:** 2026-06-20
**Agent:** Database Agent (05)
**Revision ID:** 20260620_0003
**Depends on:** 20260620_0002

**Purpose:**
Add otp_code and otp_expires_at columns to the users table to store OTP values in the database during verification.

**Changes:**
- Added columns `otp_code` (VARCHAR(10)) and `otp_expires_at` (TIMESTAMP WITH TIME ZONE) to the `users` table.

**Rollback Tested:** Yes

**Verification:**
- Check users table definition in postgres to confirm the new columns exist.

---

### Migration: 20260620_0004_add_role_soft_delete
**Created:** 2026-06-20
**Agent:** Database Agent (05)
**Revision ID:** 20260620_0004
**Depends on:** 20260620_0003

**Purpose:**
Add missing deleted_at column to roles and user_roles tables to support soft delete properties defined in SQLAlchemy TenantScopedBase model.

**Changes:**
- Added column `deleted_at` (TIMESTAMP WITH TIME ZONE) to `roles` table.
- Added column `deleted_at` (TIMESTAMP WITH TIME ZONE) to `user_roles` table.

**Rollback Tested:** Yes

**Verification:**
- Verify tests pass when accessing role-based SQLAlchemy operations.

---

### Migration: 20260620_0005_academic_and_institutional_tables
**Created:** 2026-06-20
**Agent:** Database Agent (05)
**Revision ID:** 20260620_0005
**Depends on:** 20260620_0004

**Purpose:**
Scaffold remaining Phase 1A foundation tables for academic structure, student lifecycles, and timetable slots/entries. Enforce RLS and auto-update triggers.

**Changes:**
- Created tables: `departments`, `faculty`, `courses`, `batches`, `sections`, `students`, `timetable_slots`, `timetable_entries`.
- Enabled RLS on all 8 tables.
- Created `tenant_isolation` policy per table to verify tenant isolation.
- Created `trg_{table}_update` before update trigger to automatically update `updated_at` timestamps.

**Rollback Tested:** Yes

**Verification:**
- Successfully run `alembic upgrade head` and confirmed transaction applied.

---

### Migration: 20260620_0006_master_data_tables
**Created:** 2026-06-20
**Agent:** Database Agent (05)
**Revision ID:** 20260620_0006
**Depends on:** 20260620_0005

**Purpose:**
Create F-02 Master Data Management tables, specifically the `master_data_entities` table, with support for curriculum-scoping and tenant isolation.

**Changes:**
- Created table: `master_data_entities` (tenant-scoped, with curriculum_id composite FK)
- Created composite unique index on `(tenant_id, category, code)` where deleted_at is null.
- Enabled RLS on the table.

**Rollback Tested:** Yes

**Verification:**
- Run database migrations and verify MDM service unit tests.

---

### Migration: 20260620_0007_workflow_engine_tables
**Created:** 2026-06-20
**Agent:** Database Agent (05)
**Revision ID:** 20260620_0007
**Depends on:** 20260620_0006

**Purpose:**
Scaffold F-03 Workflow Engine schema: definitions, instances, and transitions. Establish database triggers to append transitions automatically to the workflow instances history JSONB cache.

**Changes:**
- Added unique constraint on `(tenant_id, id)` on `users` table to support composite foreign keys.
- Created table: `workflow_definitions` (immutable versioning, with partial unique index for active versions).
- Created table: `workflow_instances` (with composite FKs for definitions, current assignee, and check constraints for entity types).
- Created table: `workflow_transitions`.
- Created trigger `trg_workflow_transitions_insert` and trigger function `fn_workflow_transitions_insert_history()` on `workflow_transitions`.
- Enabled RLS on all tables.

**Rollback Tested:** Yes

**Verification:**
- Verify workflow engine lifecycle unit and integration tests.

---

### Migration: 20260620_0008_digital_assets_tables
**Created:** 2026-06-20
**Agent:** Database Agent (05)
**Revision ID:** 20260620_0008
**Depends on:** 20260620_0007

**Purpose:**
Scaffold F-07 Digital Asset Repository database tables to support metadata, checksums, and tenant-scoped tracking of assets.

**Changes:**
- Created table: `digital_assets` (with BIGINT for file size and composite FK referencing users).
- Enabled RLS and triggers.

**Rollback Tested:** Yes

**Verification:**
- Verify asset upload and download unit tests.

---

### Migration: 20260620_0009_phase1b_academic_tables
**Created:** 2026-06-20
**Agent:** Orchestrator Agent (00)
**Revision ID:** 20260620_0009
**Depends on:** 20260620_0008

**Purpose:**
Scaffold and implement Phase 1B Academic Calendar, Lesson Plans, Session Tracking, and Curriculum Migrations. Enforce RLS, auto-update triggers, check constraints, composite foreign keys, and indexes.

**Changes:**
- Altered table `courses` to add `default_attendance_category` column.
- Added unique constraint on `(tenant_id, id)` on courses, batches, academic_years, faculty, and students tables to support composite FK references.
- Created tables: `events`, `event_courses`, `event_faculty`, `lesson_plans`, `sessions`, `session_faculty`, `curriculum_migration_audits`.
- Enabled RLS on all 7 tables.
- Added auto-update updated_at triggers on all tables.

**Rollback Tested:** Yes

**Verification:**
- Run academic service tests (`pytest.exe tests/unit/academic/...`) and verify they pass.

---

### Migration: 20260620_0010_phase1b_logbook_tables
**Created:** 2026-06-20
**Agent:** Orchestrator Agent (00)
**Revision ID:** 20260620_0010
**Depends on:** 20260620_0009

**Purpose:**
Scaffold and implement Foundation Course and AETCOM logbook records tracking.

**Changes:**
- Created tables: `foundation_course_records`, `aetcom_records`.
- Enabled RLS on both tables.
- Added check constraints for foundation course module names, aetcom record statuses, and professional phases.
- Added unique constraint `uq_aetcom_records_unique` on `(tenant_id, student_id, module_code, competency_code, professional_phase)` where `deleted_at` is null.

**Rollback Tested:** Yes

**Verification:**
- Run logbook service tests (`pytest.exe tests/unit/logbook/...`) and verify they pass.

---

### Migration: 20260630_0014_add_elective_allocation_runs
**Created:** 2026-06-30
**Agent:** Backend Agent (02)
**Revision ID:** 20260630_0014
**Depends on:** 20260620_0013

**Purpose:**
Add the `elective_allocation_runs` table to act as an audit trail for automated elective allocations (ADR-034), extend `elective_allocations` with run tracking and allocation methods, and add `submitted_at` to preferences for FCFS sorting.

**Changes:**
- Created table `elective_allocation_runs` with composite foreign keys, RLS enabled, and updated_at triggers.
- Altered table `elective_allocations`: dropped composite primary key, added surrogate `id` UUID primary key with `gen_random_uuid()` default, and added a unique constraint on `(tenant_id, id)` to align with the repository framework.
- Added column `allocation_run_id` (foreign key to `elective_allocation_runs`) and `allocation_method` (check constraint for ranks/fcfs/manual) to table `elective_allocations`.
- Added column `submitted_at` (TIMESTAMP WITH TIME ZONE) to table `student_elective_preferences`.

**Rollback Tested:** Yes

**Verification:**
- Unit tests pass, schema structure validated, and ADR-034 trace verified.

---

### Migration: 20260630_bf787ada4ee4_add_doap_evidence_and_notes
**Created:** 2026-06-30
**Agent:** Backend Agent (02)
**Revision ID:** bf787ada4ee4
**Depends on:** 20260630_0014

**Purpose:**
Add `evidence_asset_ids` (JSONB) and `notes` (TEXT) columns to the `doap_session_records` table to support procedural attachments and faculty comments (ADR-035).

**Changes:**
- Altered table `doap_session_records` to add `evidence_asset_ids` column of type `JSONB` with a default of `'[]'::jsonb`.
- Altered table `doap_session_records` to add `notes` column of type `TEXT` (nullable).

**Rollback Tested:** Yes

**Verification:**
- Run DOAP unit and integration tests (`pytest tests/unit/doap/ tests/integration/doap/`) and verify they pass.





