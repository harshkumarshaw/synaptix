# Synaptix Framework — Initial Inventory

> Generated: 2026-06-18
> Total files: 90
> Status: Phase 0 Framework Setup Complete

This document inventories every file in the initial framework. Use it as a reference for what's available.

## Root Level (8 files)

| File | Purpose |
|------|---------|
| `README.md` | Project front door, status tracking, agent reading order |
| `AGENTS.md` | **MANDATORY**: 10 Commandments + session protocols for all agents |
| `AOIP_MASTER_SPEC_v5.md` | Definitive specification (49 modules, 12 services, 3 tiers, NMC compliance) |
| `FIRST_SESSION_GUIDE.md` | Day 1 walkthrough for Sila — start here |
| `.antigravity-rules` | Antigravity IDE configuration (stack, conventions, agent boundaries) |
| `.env.example` | Environment variable template |
| `docker-compose.yml` | Local dev environment (PostgreSQL, optional Redis, Adminer, Mailhog) |
| `INVENTORY.md` | This file |

## Agents (12 files)

Specialist agent specifications with bounded scope, model assignments, and session protocols.

| File | Specialisation | Model |
|------|---------------|-------|
| `agents/00-orchestrator-agent.md` | Task coordinator | claude-opus-4-6 |
| `agents/01-architect-agent.md` | System architect, ADRs | claude-opus-4-6 |
| `agents/02-backend-agent.md` | FastAPI services | claude-sonnet-4-6 |
| `agents/03-frontend-agent.md` | Next.js web app | claude-sonnet-4-6 |
| `agents/04-mobile-agent.md` | Flutter mobile | claude-sonnet-4-6 |
| `agents/05-database-agent.md` | PostgreSQL, migrations | claude-opus-4-6 |
| `agents/06-testing-agent.md` | All tests, coverage enforcement | claude-sonnet-4-6 |
| `agents/07-security-agent.md` | Auth, RBAC, DPDP | claude-opus-4-6 |
| `agents/08-code-reviewer-agent.md` | Code quality reviewer | claude-opus-4-6 |
| `agents/09-devops-agent.md` | Docker, Cloud Run, CI/CD | claude-sonnet-4-6 |
| `agents/10-documentation-agent.md` | Doc auto-updater | gemini-3-5-flash |
| `agents/11-nmc-compliance-agent.md` | NMC CBME regulation validator | claude-opus-4-6 |

## Agent Memory (38 files)

Persistent memory split into three categories per agent:

```
.agent-memory/
├── working/        # Current session state (12 + CURRENT_FOCUS + QUESTIONS = 14 files)
├── learning/       # Accumulated patterns and discoveries (12 files)
└── incident/       # Failures and near-misses (12 files)
```

## Conventions (5 files)

| File | Covers |
|------|--------|
| `conventions/CODING_STANDARDS.md` | Python 3.12, TypeScript strict, Flutter, SQL |
| `conventions/API_DESIGN.md` | URL versioning, response envelope, pagination, errors |
| `conventions/DATABASE_CONVENTIONS.md` | RLS, naming, migrations, indexes, partitioning |
| `conventions/COMMIT_CONVENTIONS.md` | Conventional Commits with agent attribution |
| `conventions/ERROR_HANDLING.md` | 3-layer error system, SynaptixError base, error codes |

## Tests (4 root files + 6 subdirectories)

The testing framework that solves the "agents don't cover edge cases" problem:

| File | Purpose |
|------|---------|
| `tests/COVERAGE_MANIFEST.yaml` | **SOURCE OF TRUTH** for required tests. Hard-fail enforcement. |
| `tests/NMC_COMPLIANCE_TESTS.md` | Every NMC regulation → test mapping. Hard-fail. |
| `tests/EDGE_CASES.md` | 100+ edge cases catalogued. Each maps to a test. |
| `tests/TESTING_STRATEGY.md` | Pyramid, naming, mocking, mutation testing setup |

Subdirectories (currently empty, agents will populate):
- `tests/unit/`
- `tests/integration/`
- `tests/e2e/`
- `tests/load/`
- `tests/security/`
- `tests/compliance/`

## Documentation (17 files)

All auto-updated by Documentation Agent after every session:

| File | Updated When |
|------|--------------|
| `docs/ARCHITECTURE.md` | Architectural changes |
| `docs/CHANGELOG.md` | Every commit |
| `docs/DEVELOPMENT_LOG.md` | Every session |
| `docs/COMMAND_HISTORY.md` | Every command run |
| `docs/BUG_LOG.md` | Bug found |
| `docs/DECISIONS.md` | Architectural decision (ADR) |
| `docs/KNOWN_ISSUES.md` | Issue identified but not yet fixed |
| `docs/MIGRATION_LOG.md` | Migration created |
| `docs/AGENT_LEARNINGS.md` | Agent corrected or discovers pattern |
| `docs/DEPENDENCY_LOG.md` | Package added |
| `docs/COST_LOG.md` | Monthly cloud/AI costs |
| `docs/UAT_LOG.md` | UAT session conducted |
| `docs/NMC_COMPLIANCE_LOG.md` | NMC regulation implemented |
| `docs/PERFORMANCE_LOG.md` | Performance issue or optimisation |
| `docs/INCIDENT_LOG.md` | Production incident |
| `docs/HANDOFF_NOTES.md` | End of every session (next agent reads at start) |
| `docs/sessions/TEMPLATE.md` | Template for new session logs |

## Scripts (7 files)

| File | Purpose |
|------|---------|
| `scripts/setup-local-dev.ps1` | One-command local dev setup (Windows) |
| `scripts/pre-commit-hook.ps1` | All quality gates: lint, types, tests, NMC, secrets, docs |
| `scripts/init-db.sql` | PostgreSQL extensions + initial tenant (JMN) |
| `scripts/verify_coverage_manifest.py` | Hard-fail if any required test missing |
| `scripts/check_secrets.py` | Hard-fail if hardcoded secrets detected |
| `scripts/verify_docs_updated.py` | Hard-fail if docs not updated when code changes |
| `scripts/update-docs.ps1` | Session-end helper |

## Empty Service Directories (Created, not populated)

Awaiting agent implementation:

```
services/                    # 12 backend services
frontend-web/               # Next.js 14 app
frontend-mobile/            # Flutter 3 app
packages/shared/            # Shared libraries (auth, db, errors, logging)
infrastructure/             # Terraform, Cloud Run configs
```

## Critical Reading Order for First Session

1. `FIRST_SESSION_GUIDE.md` (you, Sila — start here)
2. `AGENTS.md` (you, then every agent every session)
3. `AOIP_MASTER_SPEC_v5.md` (you, then agents per task)
4. `.agent-memory/working/CURRENT_FOCUS.md` (agents at session start)
5. Per-task: relevant agent spec + conventions + tests

## Quality Enforcement Summary

Five layers prevent quality drift:

1. **Coverage Manifest** (YAML) → every module has required test list → build fails if any missing
2. **NMC Compliance Tests** → every regulation has a test → hard-fail blocks all commits
3. **Tenant Isolation** → enforced at 3 layers (Gateway, Middleware, RLS) → agents cannot skip
4. **Documentation as Build Artefact** → pre-commit hook rejects commits without doc updates
5. **Specialist Boundaries** → agents cannot modify files outside their scope

## NMC Regulatory Coverage

Hard-coded enforcement of:

- Two-threshold attendance (75% theory + 80% practical, separately) — ADR-003
- Logbook submitted + assessed as prerequisite for summative exam
- Logbook contributes up to 20% of IA marks
- K/KH/SH/P competency taxonomy with is_core (Y/N) per curriculum
- CRMI: 7 mandatory rotations, 75% per rotation, max 15 days leave total
- NExT additionally requires elective Block 1 + Block 2 logbooks
- Attendance denominator = conducted sessions only (never planned) — AUDIT-D3
- Foundation Course (Phase I start, 1 month)
- AETCOM (longitudinal across all phases)
- ECE (Phase I only)
- Electives (2 × 4 weeks after Phase III Part I exam, 75% threshold, logbook required)

## Curriculum Versioning

Both CBME 2019 (JMN 2023 batch) and CBME 2023 (JMN 2024+ batches) coexist. Competency codes scoped per curriculum_id, never globally — ADR-008.

## Cost Profile

- **Phase 0 (now):** ₹0/month (local Docker)
- **Phase 1A-2 (months 1-7):** ₹0/month (still local for dev)
- **Tier 1 MVP (after Phase 2):** ₹25,000-43,000/month (Cloud Run, scale-to-zero)
- **Tier 2 (5+ institutions or 500+ users):** ₹93,000-1,60,000/month
- **Tier 3 (enterprise scale):** ₹1,72,000-3,21,000/month

## Open Items Requiring Sila's Input Before Production

- [ ] DPO (Data Protection Officer) appointment (DPDP Act 2023)
- [ ] Breach notification contacts (2-3 people)
- [ ] Anthropic API key (deferred)
- [ ] Gemini API key (deferred)
- [ ] Domain name (placeholder: `platform.jmn.edu.in`)
- [ ] WhatsApp Business API provider (Gupshup vs Twilio India)
- [ ] SMS gateway provider (Textlocal vs Gupshup vs MSG91)
- [ ] GCP project name (to be created when deploying)

---

*Framework setup complete. Phase 1A awaits.*
