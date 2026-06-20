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
