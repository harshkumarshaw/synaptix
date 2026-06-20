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

