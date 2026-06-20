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

