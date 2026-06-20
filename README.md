# Synaptix

> **Internal code:** SNX
> **Owner:** Nirmala Foundation
> **First institution:** JMN Medical College & Hospital, Kalyani, Nadia, West Bengal
> **Repository type:** Monorepo
> **Status:** Pre-Phase 1A — Framework Setup
> **Version:** 5.0 (master)

Synaptix is the Academic Operations & Intelligence Platform for the Nirmala Foundation group of institutions. It serves as the complete operational backbone for medical, nursing, allied health, pharmacy, engineering, and university programmes, with multi-tenant isolation, full NMC CBME compliance (2019 and 2023 curricula), offline-first mobile support, and AI-assisted operations.

This repository is built primarily by AI agents orchestrated through Google Antigravity, supervised by a solo developer-architect. The framework documents in this repository are **mandatory reading** for every agent at the start of every session.

---

## Quick Links

- [Master Specification](./AOIP_MASTER_SPEC_v5.md) — the definitive specification
- [Agent Rules](./AGENTS.md) — non-negotiable rules every agent must follow
- [First Session Guide](./FIRST_SESSION_GUIDE.md) — Day 1 walkthrough
- [Coding Standards](./conventions/CODING_STANDARDS.md)
- [API Design](./conventions/API_DESIGN.md)
- [Database Conventions](./conventions/DATABASE_CONVENTIONS.md)
- [Testing Strategy](./tests/TESTING_STRATEGY.md)
- [NMC Compliance Tests](./tests/NMC_COMPLIANCE_TESTS.md)
- [Edge Cases](./tests/EDGE_CASES.md)

## Project Structure

```
synaptix/
├── README.md                       # This file
├── AOIP_MASTER_SPEC_v5.md         # Definitive product specification
├── AGENTS.md                       # Root-level agent rules
├── .antigravity-rules              # Antigravity IDE configuration
├── FIRST_SESSION_GUIDE.md         # Day 1 walkthrough
├── docker-compose.yml              # Local dev environment
├── .env.example                    # Environment variable template
│
├── agents/                         # Specialist agent specifications
│   ├── 00-orchestrator.md
│   ├── 01-architect-agent.md
│   ├── 02-backend-agent.md
│   ├── 03-frontend-agent.md
│   ├── 04-mobile-agent.md
│   ├── 05-database-agent.md
│   ├── 06-testing-agent.md
│   ├── 07-security-agent.md
│   ├── 08-code-reviewer-agent.md
│   ├── 09-devops-agent.md
│   ├── 10-documentation-agent.md
│   └── 11-nmc-compliance-agent.md
│
├── .agent-memory/                  # Persistent agent memory
│   ├── working/                    # Current-session working memory
│   ├── incident/                   # Incident-based memory (bugs, failures)
│   └── learning/                   # Learning-based memory (patterns, discoveries)
│
├── docs/                           # All project documentation (auto-updated)
│   ├── ARCHITECTURE.md
│   ├── CHANGELOG.md
│   ├── DEVELOPMENT_LOG.md
│   ├── COMMAND_HISTORY.md
│   ├── BUG_LOG.md
│   ├── DECISIONS.md
│   ├── KNOWN_ISSUES.md
│   ├── MIGRATION_LOG.md
│   ├── AGENT_LEARNINGS.md
│   ├── DEPENDENCY_LOG.md
│   ├── COST_LOG.md
│   ├── UAT_LOG.md
│   ├── NMC_COMPLIANCE_LOG.md
│   ├── PERFORMANCE_LOG.md
│   ├── INCIDENT_LOG.md
│   ├── HANDOFF_NOTES.md
│   └── sessions/                   # Date-wise session logs
│
├── tests/                          # Comprehensive test framework
│   ├── COVERAGE_MANIFEST.yaml      # Mandatory test requirements
│   ├── NMC_COMPLIANCE_TESTS.md
│   ├── EDGE_CASES.md
│   ├── TESTING_STRATEGY.md
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── load/
│   ├── security/
│   └── compliance/
│
├── conventions/                    # Coding and architectural conventions
│   ├── CODING_STANDARDS.md
│   ├── API_DESIGN.md
│   ├── DATABASE_CONVENTIONS.md
│   ├── COMMIT_CONVENTIONS.md
│   └── ERROR_HANDLING.md
│
├── scripts/                        # Automation scripts
│   ├── setup-local-dev.sh
│   ├── setup-local-dev.ps1         # Windows version
│   ├── seed-nmc-data.sql
│   ├── pre-commit-hook.sh
│   ├── pre-commit-hook.ps1         # Windows version
│   └── update-docs.sh
│
├── services/                       # Backend services (12 grouped services)
│   ├── auth/
│   ├── academic/
│   ├── attendance/
│   ├── exam/
│   ├── clinical/
│   ├── logbook/
│   ├── institution/
│   ├── compliance/
│   ├── notification/
│   ├── workflow/
│   ├── analytics/
│   └── ai/
│
├── packages/
│   └── shared/                     # Shared libraries (auth, tenant, models, utils)
│
├── frontend-web/                   # Next.js 14 web application
├── frontend-mobile/                # Flutter 3 mobile application
└── infrastructure/                 # Terraform, Docker configs
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.12), SQLAlchemy 2, Pydantic v2 |
| Frontend Web | Next.js 14, React 18, TypeScript, Tailwind CSS |
| Mobile | Flutter 3 with drift (SQLite ORM) |
| Database | PostgreSQL 16 with Row Level Security |
| Cache (Tier 2+) | Redis 7 |
| Search (Tier 2+) | Elasticsearch 8 / PostgreSQL tsvector (Tier 1) |
| Message Bus | Google Pub/Sub (cloud) / In-process events (local) |
| Local Dev | Docker Compose (PostgreSQL only, no cloud needed) |
| Deployment | Google Cloud Run (Tier 1) → GKE Autopilot (Tier 3) |
| AI | Claude Sonnet 4.6 (primary), Gemini 3.5 Flash (fallback) |
| CI/CD | GitHub Actions |
| IaC | Terraform |
| Monitoring | Prometheus + Grafana, Google Cloud Logging |

## Development Philosophy

Synaptix is built by **AI agents under solo-developer supervision**. The framework enforces strict conventions because a single developer cannot manually review every line of agent-generated code. Quality is enforced through:

1. **Mandatory test coverage manifests** — every module has a YAML file listing required test cases. Build fails if any are missing.
2. **NMC compliance hard-fail** — any failing NMC compliance test blocks all commits.
3. **Tenant isolation by middleware** — agents cannot skip multi-tenant filtering because it's enforced at the framework level.
4. **Documentation as a build artefact** — agents must update docs after every session, or commits are blocked.
5. **Specialist agents with bounded scope** — each agent has a narrow specialisation and cannot modify files outside its domain without escalation.

## Build & Run (Local)

```bash
# Windows (PowerShell as Administrator)
.\scripts\setup-local-dev.ps1

# Then in your IDE / terminal
docker compose up -d
# Backend hot-reload runs on http://localhost:8000
# Frontend dev server runs on http://localhost:3000
```

## Status Tracking

| Phase | Target | Status |
|-------|--------|--------|
| Phase 0: Framework Setup | This week | 🟡 IN PROGRESS |
| Phase 1A: Foundation (Identity, MDM, Academic Structure) | Months 1–2 | ⚪ NOT STARTED |
| Phase 1B: Calendar & Planning | Months 3–4 | ⚪ NOT STARTED |
| Phase 2: Attendance & Admissions | Months 5–7 | ⚪ NOT STARTED |
| Phase 3: Exams & Resources | Months 8–9 | ⚪ NOT STARTED |
| Phase 4: Clinical & Medical Ed | Months 10–12 | ⚪ NOT STARTED |
| Phase 5: Compliance & Intelligence | Months 13–15 | ⚪ NOT STARTED |
| Phase 6: AI & Advanced | Months 16–18 | ⚪ NOT STARTED |

## Critical Reading Order for New Agents

When an agent begins a session, it MUST read these files in order:

1. `AGENTS.md` (root) — non-negotiable rules
2. `AOIP_MASTER_SPEC_v5.md` — what we're building
3. `.agent-memory/working/CURRENT_FOCUS.md` — what was being worked on
4. `agents/{agent-id}-{name}-agent.md` — agent's own specialisation
5. `.agent-memory/learning/{agent-id}.md` — what this agent has learned
6. `.agent-memory/incident/{agent-id}.md` — what has gone wrong before
7. `docs/HANDOFF_NOTES.md` — notes from the previous session
8. `conventions/` (relevant files for the task)
9. The relevant module spec or task description

## Contact & Governance

- **Project owner:** Sila Singh Ghosh, Chairperson, Nirmala Foundation
- **Solo developer-architect:** Sila Singh Ghosh
- **DPO (DPDP Act 2023):** _To be appointed before production launch_
- **Breach notification contacts:** _To be appointed before production launch_

---

*Synaptix — Built on Nirmala Foundation's commitment to A Legacy of Learning.*
