# Current Focus

> Shared across all agents. Updated at every session.

## Current Phase

**Phase 1B:** Calendar & Planning — In Progress (Backend Development & Testing Complete)

## Active Modules

- `packages/shared` — scaffold complete (logging, errors, db, auth)
- `services/snx-auth` — scaffold complete, business logic stubbed
- `services/snx-academic` — scaffold complete, Phase 1B Calendar & Planning features complete
- `services/snx-institution` — scaffold complete
- `services/snx-workflow` — scaffold complete
- `services/snx-logbook` — scaffold complete, Phase 1B Foundation Course & AETCOM tracking complete
- `services/_migrations` — all 10 migrations applied to dev/test databases

## Active Branch

`chore/devops-scaffolding`

## Recently Completed

- **2026-06-20 Session 6 (Orchestrator):** Fixed all GitHub Actions CI failures. Resolved Python syntax error in snx-logbook router, migrated ruff config to `[tool.ruff.lint]`, added FastAPI-appropriate linter ignores, formatted 88 files with Black. Rewrote CI `unit-tests` job to use isolated PYTHONPATH per microservice with `--cov-append`. All 29 unit tests pass. Coverage 83.67% (threshold 80%). Ruff: 0 errors. Black: clean.
- **2026-06-20 Session 4 (Backend):** Scaffolded `snx-workflow` service. Resolved transition state machine validations and database audit log UUID generation. Created 7 new unit, integration, and security tests. Optimized test isolation by introducing table truncation in `db_session` conftest fixture. All tests PASS.
- **2026-06-20 Session 3 (Orchestrator):** Scaffolded `snx-academic` and `snx-institution` services, migrations, and integration tests.
- **2026-06-20 Session 2 (Backend/Testing):** CryptContext fix + auth role MFA tests verification.
- **2026-06-20 Session 1 (Orchestrator):** Root project and packages scaffold.

## Up Next

1. **All agents:** Verify GitHub Actions passes green on all 5 jobs (lint, unit-tests, nmc-compliance, secret-scan, docker-build) after this push.
2. **DevOps Agent (09):** Create/verify Dockerfiles for remaining microservices (snx-academic, snx-institution, snx-workflow, snx-logbook).
3. **Orchestrator:** Begin Phase 2 planning per AOIP_MASTER_SPEC_v5.md.

## Blockers

- None
