# Implementation Plan — Phase 1B: Calendar & Planning Redesign

Scaffold and implement **Phase 1B: Calendar & Planning** modules with robust schemas matching all NMC compliance requirements. This phase supports Academic Calendar Engine (`A-04`), Lesson Plan Engine (`A-05`), Session Tracking (`A-06`), Curriculum Version Migration Engine (`A-02`), and Foundation Course & AETCOM tracking (`A-07`).

---

## User Review Required

The following schema corrections, design mappings, and architectural decisions have been made to address NMC compliance gaps before writing any code:

> [!IMPORTANT]
> **1. Events & Courses Normalization (Single Source of Truth)**
> - **Removed `events.course_id` entirely** from the `events` table (Option a) to prevent drift and redundant storage of the primary course.
> - The `event_courses` join table maps all courses for an event. A partial unique index: `UNIQUE (tenant_id, event_id) WHERE is_primary = TRUE` guarantees that exactly one course is marked as the primary course per event.
> - **Copied Category Inheritance:** Added `default_attendance_category` to the `courses` table (Phase 1A patch). On event creation, application code in `calendar_service.py` copies `default_attendance_category` from the primary course to `events.attendance_category` (EC-014 compliance).
> - **Composite FKs:** `events.parent_event_id` and `events.cancelled_by` use composite FKs to prevent cross-tenant leakage.
>
> **2. Faculty & Session Assignment**
> - Replaced single `faculty_id` in `events` and `sessions` with join tables `event_faculty` and `session_faculty` to support multiple instructors.
> - Made `sessions.lesson_plan_id` nullable, adding `session_reason` for unplanned sessions (remedial, makeup).
>
> **3. Lesson Plan Versioning & Validation**
> - **Immutability without Soft Delete:** Old versions are NOT soft-deleted. They remain in the table with `is_current = FALSE` and `deleted_at = NULL`. Only the active one has `is_current = TRUE`.
> - **Scoping:** Lesson plan `code` is human-supplied (validating against regex `^[A-Z0-9_-]{3,50}$`) and scoped per-course.
> - **Uniqueness:** Changed partial unique index to `UNIQUE (tenant_id, course_id, curriculum_id, code) WHERE is_current = TRUE AND deleted_at IS NULL` (includes `curriculum_id` for curriculum-scoped uniqueness).
> - **Rejection Flow:** If rejected, `is_current` is updated to `FALSE` on the rejected version. The next draft must be created as a new version record.
> - **Approval Cache:** Links `lesson_plans.workflow_instance_id` to `workflow_instances.id`. The status is a denormalized cache.
>
> **4. Foundation Course & AETCOM Longitudinal Tracking**
> - **Foundation Course:** Added `required_hours` (NUMERIC) and `signoff_received_at` (TIMESTAMPTZ) to make rows self-describing. Enforced module name check constraints (`orientation`, `skills_acquisition`, etc.).
> - **AETCOM Records:** Clarified module:competency is 1:N (multiple competencies per module). Added unique constraint: `UNIQUE (tenant_id, student_id, module_code, competency_code, professional_phase) WHERE deleted_at IS NULL`.
>
> **5. Standard Audit Log Actor Columns**
> - Treated `created_by` / `updated_by` as denormalized UUID fields (no database FK constraint to prevent cascading deletion block conflicts on append-only tables).

---

## Proposed Changes

### Database Migrations

#### [NEW] [20260620_0009_phase1b_academic_tables.py](file:///f:/Synaptix/services/_migrations/versions/20260620_0009_phase1b_academic_tables.py)
* **Table:** `courses` (Alteration to add Phase 1A patch)
  - Add column `default_attendance_category` VARCHAR(30) NOT NULL CHECK (default_attendance_category IN ('theory', 'practical', 'clinical', 'doap', 'ece', 'aetcom', 'foundation_course', 'elective'))
* **Table:** `events`
  - `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
  - `tenant_id` UUID NOT NULL
  - `batch_id` UUID NOT NULL
  - `academic_year_id` UUID NOT NULL
  - `title` VARCHAR(150) NOT NULL
  - `description` TEXT
  - `event_type` VARCHAR(30) NOT NULL CHECK (event_type IN ('lecture', 'practical', 'doap', 'ece', 'clinical_posting', 'foundation_course', 'aetcom', 'examination'))
  - `attendance_category` VARCHAR(30) NOT NULL CHECK (attendance_category IN ('theory', 'practical', 'clinical', 'doap', 'ece', 'aetcom', 'foundation_course', 'elective'))
  - `professional_phase` VARCHAR(20) NOT NULL CHECK (professional_phase IN ('Phase I', 'Phase II', 'Phase III Part I', 'Phase III Part II'))
  - `date` DATE NOT NULL
  - `start_time` TIME NOT NULL
  - `end_time` TIME NOT NULL
  - `status` VARCHAR(20) NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'conducted', 'cancelled', 'rescheduled'))
  - `parent_event_id` UUID NULL
  - `cancellation_reason` TEXT NULL
  - `cancelled_by` UUID NULL
  - Standard timestamps & denormalized actor columns (`deleted_at`, `created_by`, `updated_by`)
  - **Composite FKs:**
    - `FOREIGN KEY (tenant_id, batch_id) REFERENCES batches(tenant_id, id) ON DELETE RESTRICT`
    - `FOREIGN KEY (tenant_id, academic_year_id) REFERENCES academic_years(tenant_id, id) ON DELETE RESTRICT`
    - `FOREIGN KEY (tenant_id, parent_event_id) REFERENCES events(tenant_id, id) ON DELETE SET NULL`
    - `FOREIGN KEY (tenant_id, cancelled_by) REFERENCES users(tenant_id, id) ON DELETE SET NULL`
* **Table:** `event_courses` (Primary and Secondary courses join table)
  - `tenant_id` UUID NOT NULL
  - `event_id` UUID NOT NULL
  - `course_id` UUID NOT NULL
  - `is_primary` BOOLEAN NOT NULL DEFAULT FALSE
  - PRIMARY KEY (`tenant_id`, `event_id`, `course_id`)
  - **Composite FKs:**
    - `FOREIGN KEY (tenant_id, event_id) REFERENCES events(tenant_id, id) ON DELETE CASCADE`
    - `FOREIGN KEY (tenant_id, course_id) REFERENCES courses(tenant_id, id) ON DELETE RESTRICT`
  - **Constraints & Indexes:**
    - UNIQUE index on `(tenant_id, event_id)` WHERE `is_primary = TRUE` (enforces exactly one primary course).
* **Table:** `event_faculty` (Join Table)
  - `tenant_id` UUID NOT NULL
  - `event_id` UUID NOT NULL
  - `faculty_id` UUID NOT NULL
  - PRIMARY KEY (`tenant_id`, `event_id`, `faculty_id`)
  - **Composite FKs:**
    - `FOREIGN KEY (tenant_id, event_id) REFERENCES events(tenant_id, id) ON DELETE CASCADE`
    - `FOREIGN KEY (tenant_id, faculty_id) REFERENCES faculty(tenant_id, id) ON DELETE RESTRICT`
* **Table:** `lesson_plans` (Immutable Versioned)
  - `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
  - `tenant_id` UUID NOT NULL
  - `course_id` UUID NOT NULL
  - `curriculum_id` UUID NOT NULL
  - `code` VARCHAR(50) NOT NULL
  - `version` INTEGER NOT NULL DEFAULT 1
  - `is_current` BOOLEAN NOT NULL DEFAULT TRUE
  - `topic` VARCHAR(150) NOT NULL
  - `description` TEXT
  - `estimated_hours` NUMERIC(4, 2) NOT NULL DEFAULT 1.0
  - `competency_code` VARCHAR(50) NULL
  - `nmc_competency_level` VARCHAR(2) NOT NULL CHECK (nmc_competency_level IN ('K', 'KH', 'SH', 'P'))
  - `is_core` BOOLEAN NOT NULL DEFAULT FALSE
  - `status` VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'pending_approval', 'approved', 'rejected'))
  - `workflow_instance_id` UUID NULL
  - Standard timestamps & denormalized actor columns
  - **Composite FKs:**
    - `FOREIGN KEY (tenant_id, course_id) REFERENCES courses(tenant_id, id) ON DELETE RESTRICT`
    - `FOREIGN KEY (tenant_id, curriculum_id) REFERENCES curricula(tenant_id, id) ON DELETE RESTRICT`
    - `FOREIGN KEY (tenant_id, workflow_instance_id) REFERENCES workflow_instances(tenant_id, id) ON DELETE SET NULL`
  - **Constraints & Indexes:**
    - UNIQUE index on `(tenant_id, course_id, curriculum_id, code)` WHERE `is_current = TRUE` AND `deleted_at IS NULL`
* **Table:** `sessions`
  - `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
  - `tenant_id` UUID NOT NULL
  - `event_id` UUID NOT NULL
  - `lesson_plan_id` UUID NULL (Nullable to support unplanned sessions)
  - `session_reason` TEXT NULL (Required when `lesson_plan_id` is null)
  - `conducted_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
  - `actual_hours` NUMERIC(4, 2) NOT NULL DEFAULT 1.0
  - `remarks` TEXT
  - Standard timestamps & denormalized actor columns
  - **Composite FKs:**
    - `FOREIGN KEY (tenant_id, event_id) REFERENCES events(tenant_id, id) ON DELETE RESTRICT`
    - `FOREIGN KEY (tenant_id, lesson_plan_id) REFERENCES lesson_plans(tenant_id, id) ON DELETE RESTRICT`
* **Table:** `session_faculty` (Join Table)
  - `tenant_id` UUID NOT NULL
  - `session_id` UUID NOT NULL
  - `faculty_id` UUID NOT NULL
  - PRIMARY KEY (`tenant_id`, `session_id`, `faculty_id`)
  - **Composite FKs:**
    - `FOREIGN KEY (tenant_id, session_id) REFERENCES sessions(tenant_id, id) ON DELETE CASCADE`
    - `FOREIGN KEY (tenant_id, faculty_id) REFERENCES faculty(tenant_id, id) ON DELETE RESTRICT`
* **Table:** `curriculum_migration_audits` (Audit log only)
  - `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
  - `tenant_id` UUID NOT NULL
  - `student_id` UUID NOT NULL
  - `from_curriculum_id` UUID NOT NULL
  - `to_curriculum_id` UUID NOT NULL
  - `migrated_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
  - `approved_by` UUID NOT NULL
  - `migration_details` JSONB NULL
  - Standard timestamps & denormalized actor columns
  - **Composite FKs:**
    - `FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT`
    - `FOREIGN KEY (tenant_id, from_curriculum_id) REFERENCES curricula(tenant_id, id) ON DELETE RESTRICT`
    - `FOREIGN KEY (tenant_id, to_curriculum_id) REFERENCES curricula(tenant_id, id) ON DELETE RESTRICT`
    - `FOREIGN KEY (tenant_id, approved_by) REFERENCES users(tenant_id, id) ON DELETE RESTRICT`

* **Indexes:**
  - `idx_events_batch_date`: `events(tenant_id, batch_id, date)`
  - `idx_events_year_phase`: `events(tenant_id, academic_year_id, professional_phase)`
  - `idx_events_status`: `events(tenant_id, status) WHERE deleted_at IS NULL`
  - `idx_lesson_plans_course_status`: `lesson_plans(tenant_id, course_id, status)`
  - `idx_lesson_plans_curriculum_comp`: `lesson_plans(tenant_id, curriculum_id, competency_code)`
  - `idx_sessions_event`: `sessions(tenant_id, event_id)`
  - `idx_session_faculty`: `session_faculty(tenant_id, faculty_id)`

#### [NEW] [20260620_0010_phase1b_logbook_tables.py](file:///f:/Synaptix/services/_migrations/versions/20260620_0010_phase1b_logbook_tables.py)
* **Table:** `foundation_course_records`
  - `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
  - `tenant_id` UUID NOT NULL
  - `student_id` UUID NOT NULL
  - `module_name` VARCHAR(100) NOT NULL CHECK (module_name IN ('orientation', 'skills_acquisition', 'professional_development', 'language_computer', 'sports_yoga', 'hospital_visits'))
  - `completed_hours` NUMERIC(4, 2) NOT NULL DEFAULT 0.0
  - `required_hours` NUMERIC(4, 2) NOT NULL
  - `is_completed` BOOLEAN NOT NULL DEFAULT FALSE
  - `signoff_received_at` TIMESTAMPTZ NULL
  - `signed_off_by` UUID NULL
  - Standard timestamps & denormalized actor columns
  - **Composite FKs:**
    - `FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT`
    - `FOREIGN KEY (tenant_id, signed_off_by) REFERENCES faculty(tenant_id, id) ON DELETE RESTRICT`
* **Table:** `aetcom_records`
  - `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
  - `tenant_id` UUID NOT NULL
  - `student_id` UUID NOT NULL
  - `module_code` VARCHAR(30) NOT NULL (e.g. 'Module 1.1')
  - `competency_code` VARCHAR(50) NOT NULL (e.g. 'COM-1.1')
  - `professional_phase` VARCHAR(20) NOT NULL CHECK (professional_phase IN ('Phase I', 'Phase II', 'Phase III Part I', 'Phase III Part II'))
  - `status` VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'reflection_submitted', 'completed'))
  - `reflection_text` TEXT NULL
  - `signed_off_by` UUID NULL
  - `signed_off_at` TIMESTAMPTZ NULL
  - Standard timestamps & denormalized actor columns
  - **Composite FKs:**
    - `FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id) ON DELETE RESTRICT`
    - `FOREIGN KEY (tenant_id, signed_off_by) REFERENCES faculty(tenant_id, id) ON DELETE RESTRICT`
  - **Constraints:**
    - `UNIQUE (tenant_id, student_id, module_code, competency_code, professional_phase) WHERE deleted_at IS NULL`

---

### `snx-academic` Service Updates

Modify and add code files in [services/snx-academic](file:///f:/Synaptix/services/snx-academic/):
* **Models:**
  - `calendar.py`: `Event`, `EventFaculty`, `EventCourse` models.
  - `lesson_plan.py`: `LessonPlan` versioned model.
  - `session.py`: `Session`, `SessionFaculty` models.
  - `curriculum_migration.py`: `CurriculumMigrationAudit` model.
* **Services:**
  - `calendar_service.py`: Copies `default_attendance_category` from the primary course to `events.attendance_category`. Validates holiday conflict (`EC-113`), room booking conflict (`EC-115`), and rescheduling (`EC-110`). Writes to `audit_log` on event creation/updates/cancellations.
  - `lesson_plan_service.py`: Versioning logic (inserting new current version record, updating old version's `is_current` to `FALSE` in same transaction). Initiates `"lesson_plan_approval"` workflow.
  - `session_tracking_service.py`: Marks conducted sessions (verifying `session_reason` if `lesson_plan_id` is null). Calculates coverage metrics.
* **Routers:** Mount endpoints `/events`, `/lesson-plans`, `/sessions`, `/curriculum-migrations`.

---

### `snx-logbook` Service Scaffold

Scaffold the new microservice app in [services/snx-logbook](file:///f:/Synaptix/services/snx-logbook/) (Port `8006`):
* Standard files: `pyproject.toml`, `Dockerfile`, `app/config.py`, `app/main.py`.
* `app/models/logbook.py` mounting `FoundationCourseRecord` and `AetcomRecord`.
* `app/services/logbook_service.py` implementing AETCOM reflection submissions, faculty sign-off, and foundation course progress checks. Writes to `audit_log` for completed modules and sign-offs.

---

### Seeding

#### [NEW] [seed_m2_data.py](file:///f:/Synaptix/scripts/seed_m2_data.py)
* Seeds both CBME 2019 competencies (for repeating Phase II) and CBME 2023 competencies.
* Seeds lesson plan templates and AETCOM modules for JMN Medical College dev environment.
* Seeds the `"lesson_plan_approval"` workflow definition.

---

## Architectural Decisions (docs/DECISIONS.md)

- **ADR-013:** Attendance Category Schema Design
- **ADR-014:** Faculty Assignment Pattern for Events (join table `event_faculty`)
- **ADR-015:** Lesson Plan ↔ Workflow Engine Integration (denormalised status cache)
- **ADR-016:** Lesson Plan Versioning (immutable versioning with `is_current` flag)
- **ADR-017:** Horizontal Integration Sessions Strategy (join table `event_courses` with `is_primary`)
- **ADR-018:** Syllabus Coverage Triple-Metric Design (Primary: competency attainment; Secondary: topics and hours)
- **ADR-019:** Curriculum Migration Scoped as Audit Log in Phase 1B (execution engine deferred)

---

## Verification Plan

### Automated Tests
Run tests independently for each service:
```powershell
# snx-academic tests
$env:PYTHONPATH="F:\Synaptix;F:\Synaptix\services\snx-academic"
.\.venv\Scripts\pytest.exe tests/unit/academic/test_event_validation.py
.\.venv\Scripts\pytest.exe tests/unit/academic/test_lesson_plan_versioning.py
.\.venv\Scripts\pytest.exe tests/unit/academic/test_integration_sessions.py
.\.venv\Scripts\pytest.exe tests/integration/test_calendar_engine.py
.\.venv\Scripts\pytest.exe tests/integration/test_lesson_plan_service.py
.\.venv\Scripts\pytest.exe tests/security/academic/test_tenant_isolation.py

# snx-logbook tests
$env:PYTHONPATH="F:\Synaptix;F:\Synaptix\services\snx-logbook"
.\.venv\Scripts\pytest.exe tests/unit/logbook/test_aetcom_uniqueness.py
.\.venv\Scripts\pytest.exe tests/integration/test_logbook_service.py

# Compliance stubs tests
$env:PYTHONPATH="F:\Synaptix;F:\Synaptix\services\snx-academic"
.\.venv\Scripts\pytest.exe tests/compliance/test_nmc_compliance_stubs.py
```
