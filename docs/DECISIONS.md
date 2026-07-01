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

## ADR-030: AETCOM Sync via Service Layer (not DB Trigger)

**Date:** 2026-06-20
**Status:** Accepted (Retroactive — formalised 2026-07-01 in Session 11)
**Deciders:** Human supervisor + Backend Agent 02
**Context:** AETCOM module completion depends on three independent conditions: attendance at AETCOM sessions, student reflection submission, and faculty sign-off. This non-linear, cross-table logic is unsuitable for a database trigger, which would require querying multiple tables and implementing complex conditional branching in PL/pgSQL.
**Decision:** AETCOM sync is implemented in service-layer Python (`aetcom_sync_service.on_attendance_change()`), not as a database trigger. Called from: `attendance_service.mark_attendance()`, `logbook_service.submit_aetcom_reflection()`, `logbook_service.signoff_aetcom_module()`.
**Alternatives Considered:**
- Database trigger on `attendance` table (rejected: cross-module, non-linear, would need to query logbook + signoff tables from within a trigger — architecturally fragile)
- Scheduled job to periodically recompute AETCOM status (rejected: introduces latency and makes status stale)
**Consequences:**
- (+) Clean separation of concerns — AETCOM logic stays in Python where it can be tested easily
- (+) Unit-testable without a database
- (-) Must be explicitly called from every entry point that can change AETCOM status — easy to miss
- Mitigation: Documented caller list in service file docstring

## ADR-031: Two-Phase NOT NULL Migration for courses.subject_code

**Date:** 2026-06-20
**Status:** Accepted (Retroactive — formalised 2026-07-01 in Session 11)
**Deciders:** Human supervisor + Backend Agent 02
**Context:** Adding `subject_code` to the existing `courses` table. The column must ultimately be NOT NULL (every course must have a subject code), but existing rows in the database have no value. A DEFAULT of `'ANAT'` would incorrectly mark all existing courses as Anatomy, corrupting data.
**Decision:** Three-step migration: (1) Add column as NULLABLE in the schema migration. (2) Run admin backfill script (`scripts/admin/backfill_subject_codes.py`) per tenant with explicit per-course mapping. (3) A follow-up migration adds the NOT NULL constraint after backfill is verified.
**Alternatives Considered:**
- DEFAULT 'ANAT' (rejected: silently corrupts data — all existing courses become Anatomy)
- DEFAULT 'TBD' sentinel value (rejected: 'TBD' is not a valid subject code; would break CHECK constraints downstream)
- Single-step migration with inline data fix (rejected: requires all courses to be pre-seeded, which is not guaranteed in production)
**Consequences:**
- (+) No data corruption; backfill is explicit and auditable per tenant
- (+) Backfill failure doesn't block the schema migration
- (-) Two-step process requires coordination between ops and deployment teams
- (-) Schema is temporarily nullable; service code must handle NULL during the gap

## ADR-032: Logbook Elective Discriminator — NULLABLE subject_code

**Date:** 2026-06-20
**Status:** Accepted (Retroactive — formalised 2026-07-01 in Session 11)
**Deciders:** Human supervisor + Backend Agent 02
**Context:** `logbook_entries` stores both regular course entries (with `subject_code`) and elective entries (with `elective_id`). A discriminator is needed. The original plan used a sentinel value `subject_code = 'ELECTIVE'` which is fragile and breaks subject-code-based queries.
**Decision:** Make `subject_code` NULLABLE. Enforce a CHECK constraint: `(elective_id IS NULL AND subject_code IS NOT NULL) OR (elective_id IS NOT NULL AND subject_code IS NULL)`. Exactly one of the two must be non-null on any given row.
**Alternatives Considered:**
- Sentinel string `'ELECTIVE'` (rejected: magic string, must be excluded from all subject-code aggregation queries, error-prone)
- Separate `elective_logbook_entries` table (rejected: duplicates validation rules, sign-off service, and portfolio queries)
- Boolean `is_elective` flag (rejected: doesn't enforce mutual exclusivity with subject_code)
**Consequences:**
- (+) Structurally enforces mutual exclusivity at the database level
- (+) Queries filtering by subject_code naturally exclude elective entries (WHERE subject_code IS NOT NULL)
- (-) Application code must always set exactly one of the two columns, never both and never neither

## ADR-033: internship_rotations Scaffolded in Phase 2 for FK Validity

**Date:** 2026-06-20
**Status:** Accepted (Retroactive — formalised 2026-07-01 in Session 11)
**Deciders:** Human supervisor + Backend Agent 02
**Context:** `leave_requests` has a nullable FK to `internship_rotations` (for CRMI intern leave cap enforcement). The full internship/CRMI module is scoped to Phase 4. Without the table existing, the FK cannot be declared, breaking the schema.
**Decision:** Create a minimal scaffold table (`id`, `tenant_id`, `student_id`, `department`, `start_date`, `end_date`, `leave_days_used`, `status`) in Phase 2 to make the FK valid. Phase 4 adds the full CRMI rotation logic, scheduling, assessment, and completion certificate workflow, expanding the table.
**Alternatives Considered:**
- Defer `rotation_id` column to Phase 4 (rejected: loses the intern leave cap link for the duration of Phase 2–3, creating technical debt in leave management)
- Remove FK and use application-level check (rejected: breaks composite FK discipline from ADR-009; cross-tenant reference risk)
**Consequences:**
- (+) Leave management can enforce the 15-day CRMI leave cap in Phase 2
- (+) FK integrity maintained throughout
- (-) Scaffold table has no business logic until Phase 4; must not be exposed in public API

## ADR-034: Elective Allocation Algorithm (FCFS + Ranked)

**Date:** 2026-06-23
**Status:** Accepted (Retroactive — formalised 2026-07-01 in Session 11)
**Deciders:** Human supervisor + Backend Agent 02
**Context:** NMC CBME 2019 mandates two 2-week elective blocks during Phase III Part I. Students rank preferences; the allocator assigns based on preferences and capacity. Prior iteration used FCFS only; the ranked algorithm was deferred. Session 9 implemented both.
**Decision:** Two algorithms implemented, selectable per tenant via MDM configuration (`mdm.elective_allocation_algorithm`):
- **FCFS (`first_come_first_served`)**: processes preferences ordered by `submitted_at ASC`. Default for institutions without sophisticated needs.
- **Ranked (`ranked`)**: processes rank-by-rank across all students. Rank-1 for everyone first, then rank-2 for still-unallocated students, etc. Tie-breaking within a rank tier: earliest `submitted_at`, then deterministic hash of `student_id + allocation_run_id`.

Operational endpoint: `POST /electives/allocate` with `dry_run` flag, `algorithm` selection, `force_reallocate` modes (additive/full). Cross-block constraint: same `elective_id` cannot be allocated in both Block 1 and Block 2 for a student. Every run creates an `elective_allocation_runs` audit row.

**Worked example (Ranked, verified in Session 10 Phase A):** 10 students, 3 electives (A/B/C capacity 4). Pass rank-1: S1-S4→A (A full), S6-S8→B, S9-S10→C, S5 skipped. Pass rank-2: S5→B (S5's rank-2). Result: A=4, B=4, C=2, 0 unallocated.
**Alternatives Considered:**
- FCFS only (rejected: doesn't respect student preference rankings; penalises late submitters systematically)
- Random assignment (rejected: no audit trail, NMC inspection concern)
- Lottery system (rejected: not aligned with NMC CBME 2019 preference-based framework)
**Consequences:**
- (+) Both algorithms satisfy NMC requirements for elective allocation transparency
- (+) MDM-configurable — institutions can choose without code change
- (+) Full audit trail per allocation run
- (-) Ranked algorithm is O(students × ranks × electives) — must be a background job for large batches
- (-) Concurrent allocation triggers require row-level FOR UPDATE lock to prevent double-allocation

## ADR-035: DOAP State Machine (D→O→A→P Progression)

**Date:** 2026-06-30
**Status:** Accepted (Retroactive — formalised 2026-07-01 in Session 11)
**Deciders:** Human supervisor + Backend Agent 02
**Context:** NMC CBME 2019 mandates the DOAP (Demonstration → Observation → Assistance → Performance) progression for procedural skills. The schema was approved in Phase 2 v3, but the state machine — what transitions are valid — was not formally specified.
**Decision:** State machine with stages NOT_STARTED → DEMONSTRATED → OBSERVED → ASSISTED → PERFORMED → CERTIFIED. Implemented as pure validator functions (`doap_validators.py`) for testability.

Rules:
- Stage progression requires at least one C-decision record at ALL prior stages
- Backward attempts allowed (refresher D after reaching O) — these don't regress state
- Multiple sessions per stage allowed
- Faculty decision codes: C (Certify), R (Repeat), Re (Remediate)
- Attempt types: F (First), R (Repeat), Re (Remediation)
- Rating B + decision C is INVALID (validated as DOAP-NMC-003 compliance)

Cross-module integration: auto-creates `logbook_entries`; Re decision auto-creates `workflow_instance` for remediation; evidence via `evidence_asset_ids JSONB` column.
**Alternatives Considered:**
- Database-level state enforcement via trigger (rejected: complex multi-table query in trigger; hard to unit test)
- Status column with ad-hoc checks in each endpoint (rejected: duplicates logic across routes; misses edge cases)
**Consequences:**
- (+) Pure validator functions are fully unit-testable without a database
- (+) State machine is explicit and auditable
- (-) Service code must call validators consistently — missing a call site creates a compliance gap

## ADR-036: Leave-to-Attendance Materialisation

**Date:** 2026-06-20
**Status:** Accepted (Retroactive — formalised 2026-07-01 in Session 11)
**Deciders:** Human supervisor + Backend Agent 02
**Context:** When a student's leave is approved, attendance rows must be automatically created or updated for events during the leave window, so the student is not incorrectly marked absent.
**Decision:** Materialisation happens at leave approval time (status `pending` → `approved`) via service-layer function `leave_service.on_approval()`.

Status mapping: medical leave → `'medical'`; academic/casual/other → `'excused'`.

Conflict rules:
- If no attendance row exists for an event in the leave window: CREATE with leave status
- If attendance row exists with status != `'present'`: UPDATE to leave status, set `needs_review=true`
- If attendance row exists with status == `'present'`: DO NOT override (student actually attended despite approved leave; log warning to needs_review queue)

Future events: When a new event is created within an existing approved leave window, an event-creation hook checks for active leaves and auto-creates the attendance row.

Rejection rollback: When a previously-approved leave is rejected or cancelled, materialised attendance rows are soft-deleted and a `compliance_incidents` row is logged.
**Alternatives Considered:**
- Database trigger on `leave_requests` status change (rejected: cross-module query from trigger; would need to query events table which may be in a different schema/service)
- Nightly batch materialisation (rejected: leave approved today should reflect in attendance today, not tomorrow)
**Consequences:**
- (+) Consistent, real-time attendance reflection of approved leaves
- (+) Protects students from false absent counts
- (-) Leave approval is slightly slower (materialisation is synchronous within the approval transaction)
- (-) Must handle rollback on approval failure to avoid partial materialisation

## ADR-037: Attendance Conflict Resolution Semantics

**Date:** 2026-06-20
**Status:** Accepted (Retroactive — formalised 2026-07-01 in Session 11)
**Deciders:** Human supervisor + Backend Agent 02
**Context:** The same attendance can be marked twice — faculty A marks present, faculty B marks absent due to misidentification; or offline + online sync collision. A deterministic resolution rule is required.
**Decision:** Conflict resolution key: **latest of MAX(original_marked_at, marked_at) wins**.

Worked examples:
1. **Two online marks**: Faculty A at 10:00, Faculty B at 11:00. B wins (later wall-clock).
2. **Online then offline-sync**: Faculty A online at 10:00; Faculty B offline at 09:30, syncs at 12:00. MAX(09:30, 12:00) = 12:00 > 10:00: B wins. BUT marked_at - original_marked_at > 2 hours: flag `needs_review`.
3. **Two offline syncs**: A marked at 09:00, synced at 14:00; B marked at 09:05, synced at 13:00. MAX(09:00, 14:00) = 14:00 > 13:00: A wins. BOTH flagged `needs_review` (different original times within 5 minutes is suspicious).

`needs_review` flagging triggers when: (a) original_marked_at times differ by < 10 minutes, (b) sync gap > 2 hours, (c) status changes from present to non-present.

Implementation: Service-layer Python (not ON CONFLICT SQL — too complex for SQL expression). Unique constraint `UNIQUE (tenant_id, event_id, student_id) WHERE deleted_at IS NULL` prevents duplicate live rows.
**Alternatives Considered:**
- Last-write-wins by `marked_at` only (rejected: disadvantages offline marks which sync late even if made earlier)
- Faculty seniority-based resolution (rejected: NMC doesn't recognise hierarchical attendance authority)
- Manual reconciliation always (rejected: creates admin bottleneck at scale)
**Consequences:**
- (+) Deterministic and auditable — same inputs always produce same winner
- (+) Offline faculty not systematically disadvantaged
- (-) Sync gap > 2h always triggers needs_review, creating noise for legitimate rural offline use cases
- Mitigation: needs_review queue is a triage tool, not a block; attendance is materialised immediately

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

