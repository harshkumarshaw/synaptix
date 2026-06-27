# Architecture Decision Records (ADRs)

Every architectural decision documented as an ADR.

## ADR-001: Build with Single Developer + AI Agents

**Date:** 2026-06-18
**Status:** Accepted
**Context:** Sila is the sole developer. Project scope is 49 modules over 18 months.
**Decision:** Use Google Antigravity with 12 specialist agents. Build aggressive scaffolds first, iterate to production quality.
**Consequences:**
- (+) Velocity is high — code generation accelerated
- (-) Quality enforcement must be automated (hard-fail tests)
- (-) Human supervision required for architectural decisions
- Mitigation: Coverage manifest, NMC compliance hard-fail, specialist boundaries

## ADR-002: Service Grouping Strategy

**Date:** 2026-06-18
**Status:** Accepted
**Context:** 49 modules would mean 49 microservices — operational overhead too high.
**Decision:** Group into 12 deployable services. Each service contains multiple modules as FastAPI routers.
**Consequences:**
- (+) Manageable deployment, lower cost
- (+) Inter-module calls within a service are cheap
- (-) Cross-service calls require Pub/Sub or HTTP
- (-) If a service needs to be split later, refactoring required

## ADR-003: Two-Threshold Attendance Enforcement

**Date:** 2026-06-18
**Status:** Accepted
**Context:** NMC CBME mandates 75% theory + 80% practical separately, but v3.0 had single threshold.
**Decision:** Hard-coded two-threshold rule for MBBS. Configurable for other programmes.
**Consequences:**
- (+) NMC compliant by default
- (-) Cannot be relaxed without Principal exemption + audit log

## ADR-004: Monorepo with Single Migration Chain

**Date:** 2026-06-18
**Status:** Accepted
**Context:** Per-service migrations cause ordering conflicts.
**Decision:** Single Alembic migration chain in `services/_migrations/versions/`.
**Consequences:**
- (+) No ordering conflicts
- (-) All services share migration history (coordination needed)

## ADR-005: Cloud Run First, GKE Later

**Date:** 2026-06-18
**Status:** Accepted
**Context:** GKE has minimum cost floor; Cloud Run scales to zero.
**Decision:** Tier 1 uses Cloud Run. Migrate to GKE only when triggered (500+ concurrent users or 2nd institution).
**Consequences:**
- (+) Tier 1 cost ₹25-43K/month vs ₹58-91K with GKE
- (-) Cold start latency on first request (acceptable for academic system)

## ADR-006: PostgreSQL Row Level Security

**Date:** 2026-06-18
**Status:** Accepted
**Context:** Multi-tenant data leakage is the worst possible bug.
**Decision:** RLS on every tenant-scoped table. Three-layer enforcement: API Gateway, Middleware, RLS.
**Consequences:**
- (+) Defense in depth — even if middleware fails, DB blocks
- (-) Slight query overhead from RLS policies

## ADR-007: Local-First Development (₹0 Cost)

**Date:** 2026-06-18
**Status:** Accepted
**Context:** Solo developer needs zero-cost development environment.
**Decision:** Docker Compose with PostgreSQL only. No cloud during development. Deploy to GCP only for staging/production.
**Consequences:**
- (+) Zero cloud cost during development phase
- (+) Faster iteration (no network latency to cloud)
- (-) Some cloud-specific behaviour can't be tested locally (Pub/Sub, IAM)
- Mitigation: Cloud emulators (pubsub-emulator) for affected tests

## ADR-008: Two Active Curriculum Versions (CBME 2019 and 2023)

**Date:** 2026-06-18
**Status:** Accepted
**Context:** JMN 2023 batch on CBME 2019; 2024 batch onwards on CBME 2023.
**Decision:** Both versions coexist. Competency codes scoped to `curriculum_id`. No global uniqueness.
**Consequences:**
- (+) Backward compatibility for 2023 batch
- (-) Reports must always filter by curriculum_id

## ADR-009: Composite Foreign Keys for Tenant-Consistency

**Date:** 2026-06-20
**Status:** Accepted
**Context:** Standard Row Level Security (RLS) restricts row visibility per tenant but doesn't prevent referential integrity leakage (e.g. inserting an entity referencing a foreign key of a different tenant).
**Decision:** Enforce composite foreign keys containing `tenant_id` on all cross-table references in the `snx-workflow` service (and make it standard for future services). Add a unique constraint on `(tenant_id, id)` to referenced tables (`users`, `workflow_definitions`, `workflow_instances`).
**Consequences:**
- (+) Guarantees referential integrity tenant-consistency at the schema level.
- (-) Slightly more verbose index and constraint declarations.

## ADR-010: Immutable Workflow Definitions with Current Versioning Flag

**Date:** 2026-06-20
**Status:** Accepted
**Context:** Modifying steps in workflow definitions directly can break active in-flight instances.
**Decision:** Make all workflow definitions immutable. Modifications result in a new record with a bumped `version` integer. Designation of the active version is handled via an `is_current` BOOLEAN flag, restricted by a partial unique index on `(tenant_id, code)` where `is_current = TRUE` and `deleted_at IS NULL`.
**Consequences:**
- (+) Complete safety for in-flight instances.
- (+) Clean audit trail.
- (-) Version propagation must be handled during instantiation.

## ADR-011: Database Trigger for Workflow Transitions History Cache

**Date:** 2026-06-20
**Status:** Accepted
**Context:** Denormalized audit history JSONB caches can easily drift from the normalized `workflow_transitions` table if managed strictly in application code.
**Decision:** Enforce cache consistency via a PostgreSQL database trigger `trg_workflow_transitions_insert` which, upon insert into `workflow_transitions`, appends the transition details directly to the corresponding `workflow_instances.history` JSONB array.
**Consequences:**
- (+) Schema-level guarantee of history consistency.
- (-) Moves logic to database triggers, making local unit testing slightly more dependent on DB behaviour.

## ADR-012: Static Context Snapshot for Auditable Workflow Approvals

**Date:** 2026-06-20
**Status:** Accepted
**Context:** Source entities can change during the lifespan of an approval workflow, causing discrepancies between what the requester submitted and what the approver reviews.
**Decision:** Freeze the entity's data as a static `context` JSONB snapshot at workflow instance creation. The approval UI must display this frozen snapshot to ensure legal and audit compliance. Live changes can be shown only as a comparative diff.
**Consequences:**
- (+) Defensible audit trail.
- (-) Redundant data storage in `workflow_instances.context`.

## ADR-013: Attendance Category Schema Design

**Date:** 2026-06-20
**Status:** Accepted
**Context:** NMC CBME mandates separate thresholds for theory (75%) and practical/clinical/DOAP/ECE (80%) attendance. The system cannot determine which pool an event belongs to without explicit tagging on the schedule record.
**Decision:** Add `attendance_category` to the `events` table with a CHECK constraint: `CHECK (attendance_category IN ('theory', 'practical', 'clinical', 'doap', 'ece', 'aetcom', 'foundation_course', 'elective'))`.
**Consequences:**
- (+) Guarantees that attendance calculations partition events into the correct regulatory pools.
- (+) Simple query filtering during attendance aggregation.
- (-) Every event schedule record must be categorised at creation.

## ADR-014: Faculty Assignment Pattern for Events

**Date:** 2026-06-20
**Status:** Accepted
**Context:** Scheduling must assign faculty to events, supporting multiple faculty per session (e.g. for clinical postings/integration sessions), and handling reassignments when faculty resign or transfer.
**Decision:** Use a join table `event_faculty` (containing columns `tenant_id`, `event_id`, `faculty_id`) rather than a single `faculty_id` column or array. This table uses composite FKs referencing `events` and `faculty`.
**Consequences:**
- (+) Clean many-to-many relationship supporting multiple instructors per event.
- (+) Supports clean audit trail and reassignments when faculty resign/transfer (reassigning active rows).
- (-) Requires an extra query/join to retrieve assigned faculty for calendar events.

## ADR-015: Lesson Plan ↔ Workflow Engine Integration

**Date:** 2026-06-20
**Status:** Accepted
**Context:** Lesson plans must be submitted to HODs for approval. Maintaining a separate state machine or simple status string on `lesson_plans` leads to drift from the global workflow engine.
**Decision:** Integrate the Lesson Plan approval flow directly with `snx-workflow`. Create a `workflow_instance_id` column on `lesson_plans`, and denormalise `lesson_plans.status` as a read-through cache of the linked `workflow_instances.status`.
**Consequences:**
- (+) Reuses the robust, version-tracked workflow engine, ensuring complete audit trails and HOD sign-offs.
- (+) Prevents state machine duplication.
- (-) Introduces cross-service referencing between `snx-academic` and `snx-workflow`.

## ADR-016: Lesson Plan Versioning

**Date:** 2026-06-20
**Status:** Accepted
**Context:** Faculty revise lesson plans mid-semester. Editing a lesson plan directly destroys the history of what was previously approved and taught.
**Decision:** Apply the immutable versioning pattern matching `workflow_definitions` to `lesson_plans`. Each modification inserts a new row with an incremented `version` integer, maintaining a `is_current` BOOLEAN flag restricted by a partial unique index on `(tenant_id, course_id, code) WHERE is_current = TRUE AND deleted_at IS NULL`.
**Consequences:**
- (+) Preserves a perfect audit trail of all lesson plan revisions and approvals.
- (-) Requires soft-deleting previous current records and fetching version numbers.

## ADR-017: Horizontal Integration Sessions Strategy

**Date:** 2026-06-20
**Status:** Accepted
**Context:** Horizontal integration sessions combine multiple subjects (e.g. Anatomy + Physiology joint lecture). A single `course_id` foreign key on the `events` table cannot represent secondary subjects.
**Decision:** Keep `course_id` on the `events` table to represent the *primary* course (defining the primary subject and attendance category), and introduce an `event_courses` join table (containing `tenant_id`, `event_id`, `course_id`) to map all secondary integration courses.
**Consequences:**
- (+) Clean database normalization supporting horizontal integration.
- (+) Primary subject remains clear for NMC reporting.
- (-) Joins are required to fetch secondary subjects.

## ADR-018: Syllabus Coverage Triple-Metric Design

**Date:** 2026-06-20
**Status:** Accepted
**Context:** Syllabus coverage needs to represent both regulatory compliance and course execution metrics.
**Decision:** Implement a triple-metric design for syllabus coverage:
1. **Primary Metric (NMC-Reportable):** Competency coverage = `count(distinct competencies addressed in conducted sessions) / total core competencies in curriculum`.
2. **Topic Coverage:** `count(distinct conducted lesson_plans) / total lesson plans`.
3. **Hours Coverage:** `sum(sessions.actual_hours) / sum(lesson_plans.estimated_hours)`.
**Consequences:**
- (+) Highly accurate tracking of core competency attainment.
- (+) Redundant checks on actual instruction hours vs planned hours.
- (-) Slightly more complex database aggregation queries.

## ADR-019: Curriculum Migration Scoped as Audit Log in Phase 1B

**Date:** 2026-06-20
**Status:** Accepted
**Context:** Curriculum version migration (e.g., student moving from CBME 2019 to CBME 2023) is highly complex, involving credit mapping and bridge courses, and requires a full engine.
**Decision:** Scope Phase 1B to deliver ONLY the audit log piece (`curriculum_migration_audits`). Record `student_id`, `from_curriculum_id`, `to_curriculum_id`, `approved_by`, and a `migration_details` JSONB column. Defer the automatic execution migration engine to Phase 2.
**Consequences:**
- (+) Simplifies Phase 1B scope, focusing on schema safety and compliance audits.
- (-) Migration re-mappings must be input manually via the metadata log in JSONB for this phase.

## ADR-020: Extended Attendance Status Enum

**Date:** 2026-06-20
**Status:** Accepted
**Context:** To satisfy tests (such as ATT-007, ATT-NMC-020, and medical audit requirements EC-065), attendance status must support fine-grained states.
**Decision:** Enforce the following CHECK constraint in the `attendance` table: `status IN ('present', 'absent', 'late', 'excused', 'medical', 'official_duty', 'exempt')`.
**Consequences:**
- (+) Satisfies all compliance test definitions (ATT-007, late arrival half-attendance ATT-NMC-020).
- (+) Clean audit trails for medical leaves and sports duty.
- (-) Slightly more complex enum mapping in Python models.

## ADR-021: Attendance Event-Session Schema Binding

**Date:** 2026-06-20
**Status:** Accepted
**Context:** Enforcing the NMC denominator rule (ATT-NMC-018: denominator counts only conducted sessions, never planned; and ATT-NMC-019: cancelled events must be excluded) requires the system to join attendance back to both events (for planning, batches, dates, status) and sessions (as proof of conducted execution).
**Decision:** Add both `event_id` (NOT NULL) and `session_id` (NULL) to the `attendance` table. Require a composite foreign key on both, and add a database CHECK constraint ensuring that if `session_id` is provided, its underlying event matches the `event_id` of the attendance record.
**Consequences:**
- (+) Enforces complete referential integrity.
- (+) Allows attendance to be pre-created/marked when a class is active before the session record is fully finalized.
- (+) Denominator queries can instantly exclude cancelled events or non-conducted sessions.

## ADR-022: Attendance Summary Cache Structure

**Date:** 2026-06-20
**Status:** Accepted
**Context:** The attendance summary must partition by category to enforce the 75% theory and 80% practical split thresholds. It must also scope by `professional_phase` to support multi-phase subject aggregation (e.g. Community Medicine cross-phase ATT-NMC-015).
**Decision:** Key the `attendance_summary` table by `(tenant_id, student_id, course_id, professional_phase, attendance_category)`. Replace column-based theory/practical splits with generic counters (`sessions_conducted`, `sessions_present`, `sessions_excused`, `sessions_official_duty`, `sessions_medical`), and define the percentage column as a database-generated column calculated as:
`100.0 * (sessions_present + sessions_excused + sessions_official_duty + sessions_medical) / sessions_conducted`.
**Consequences:**
- (+) Scales nicely as categories and phases grow.
- (+) Fully supports multi-phase subject calculations and two-threshold checks.
- (-) Application logic must update the correct category row on attendance inserts.

## ADR-023: Logbook Internal Assessment (IA) Marks Contribution

**Date:** 2026-06-20
**Status:** Accepted
**Context:** NMC regulations require the logbook to contribute up to 20% of the student's IA marks (LOG-NMC-013), and to contribute 0% if the logbook is incomplete (LOG-NMC-014). This weight must be configurable per institution (LOG-NMC-017).
**Decision:** Add a new MDM configuration entity `subject_logbook_ia_weight` with a schema containing `(tenant_id, subject_code, professional_phase, curriculum_id, weight_pct)`. Enforce `weight_pct BETWEEN 0 AND 20`. In `logbook_service.py`, calculate `ia_marks` as `weight_pct * 100 / 100` (or appropriate maximum weight scale) if `is_complete` is `TRUE`, else `0.0`.
**Consequences:**
- (+) Full compliance with LOG-NMC-013, LOG-NMC-014, and LOG-NMC-017.
- (+) Keeps institutional configurations separated in master data.

## ADR-024: Exemption vs Disability Accommodation Split

**Date:** 2026-06-20
**Status:** Accepted
**Context:** Disability accommodations (ATT-E007 / EC-015) require long-running, permanent rules (date ranges, threshold overrides) and attachments (medical certs) approved by the Dean/Disability Cell. Single-session exemptions (ATT-NMC-016) are one-offs approved by the Principal.
**Decision:** Split these concepts into two tables:
1. `attendance_exemptions`: captures one-off session/event exemptions.
2. `attendance_accommodations`: captures long-running disability or medical accommodations. It includes `effective_from`, `effective_until`, `theory_threshold_override`, `practical_threshold_override`, `medical_certificate_asset_id`, and `workflow_instance_id`.
**Consequences:**
- (+) Clean separation of concerns.
- (+) Ensures auditing and medical document attachments are handled correctly.

## ADR-025: Unified Logbook Table for Regular and Elective Records

**Date:** 2026-06-20
**Status:** Accepted
**Context:** Elective logbook entries (EL-NMC-007) require the same competency taxonomies and sign-off signatures as regular courses. Declaring separate tables leads to duplicate validation and UI schemas.
**Decision:** Use a single `logbook_entries` table. Add a nullable `elective_id` column. If `elective_id` is set, the entry represents an elective logbook record and can be excluded from standard course-based syllabus metrics while still counting for elective eligibility checks.
**Consequences:**
- (+) Reuses validation rules, initials tracking, and sign-off services.
- (+) Clean database design.

## ADR-026: Electives Allocation Capacity and Block Uniqueness

**Date:** 2026-06-20
**Status:** Accepted
**Context:** A student must allocate to exactly one elective per block. Allocations must respect elective capacity limits (EL-NMC-004) without race conditions.
**Decision:** Enforce a unique constraint `UNIQUE (tenant_id, student_id, block)` on `elective_allocations`. During application allocation execution, lock the target elective row using `SELECT ... FOR UPDATE` before assessing current allocation count against `capacity`.
**Consequences:**
- (+) Guarantees no race conditions during peak registration.
- (+) Guarantees single allocation per block.

## ADR-027: Leave request to attendance materialization

**Date:** 2026-06-20
**Status:** Accepted
**Context:** When a student is granted leave (medical, academic, casual), their calendar schedule should automatically reflect their status rather than leaving it to manual faculty roll call, ensuring the student is not incorrectly marked absent.
**Decision:** Add a nullable `leave_request_id` column to the `attendance` table. Upon approval of a leave request, the `leave_service` invokes a hook to automatically create or update student attendance rows within the leave date range with the appropriate status (`medical` or `excused`).
**Consequences:**
- (+) Ensures automated, consistent leave synchronization in attendance pools.
- (+) Keeps the student from being falsely marked absent on roll calls.
- (-) Introduces automatic insertion logic on leave approval.

## ADR-028: Offline Sync Deferred to Phase 2.5

**Date:** 2026-06-20
**Status:** Accepted
**Context:** The complete offline transactional sync protocol (retries, backoffs, SQLite local database state integration) is a large-scope item that risks delaying the core compliance engine delivery for the current phase.
**Decision:** Defer the full mobile-server synchronization queue and protocol implementation to Phase 2.5. Keep all offline sync compliance tests (`ATT-SYNC-001` through `007`) marked as `xfail`. Add `original_marked_at` and `needs_review` columns to the database schema in Phase 2 so that the schema is forward-compatible.
**Consequences:**
- (+) Keeps current phase scope focused and deliverable.
- (+) Retains database schema forward-compatibility.
- (-) Mobile client sync cannot be tested end-to-end until Phase 2.5.

## ADR-029: Admission Module Deferred to Phase 2.5

**Date:** 2026-06-20
**Status:** Accepted
**Context:** The Admissions Module requires significant logic for category allocation quotas, NEET rank verification, Aadhaar consent, and WBUHS integration. Building it completely in Phase 2 would compromise attendance engine validation.
**Decision:** Defer the complete Admissions Module to Phase 2.5. Scaffold a minimal placeholder table `admission_applications` in Phase 2 containing only programmatic references (`applied_for_program_id`) to allow basic relationship mapping, and mark admissions compliance tests as `xfail` stubs.
**Consequences:**
- (+) Prevents scope creep in Phase 2.
- (+) Keeps the codebase compiling and relationship links valid.
- (-) Application processing must be handled manually or externally until Phase 2.5.

## Template for New ADRs

```markdown
## ADR-NNN: [Title]

**Date:** YYYY-MM-DD
**Status:** Proposed / Accepted / Deprecated / Superseded by ADR-XXX
**Context:** What is the situation?
**Decision:** What did we decide?
**Consequences:**
- (+) Positive consequence
- (-) Negative consequence
- Mitigation strategies
```

