# Current Focus

> Shared across all agents. Updated at every session.

## Current Phase

**Phase 1A:** Foundation Modules — In Progress (Backend Services Scaffold Complete)

## Active Modules

- `packages/shared` — scaffold complete (logging, errors, db, auth)
- `services/snx-auth` — scaffold complete, business logic stubbed
- `services/snx-academic` — scaffold complete (departments, faculty, courses, batches, sections, timetables)
- `services/snx-institution` — scaffold complete (profiles, departments, students, faculty)
- `services/snx-workflow` — scaffold complete (F-02 MDM, F-03 Workflow Engine, F-07 Digital Assets)
- `services/_migrations` — all 8 migrations (foundation, academic, workflow tables) applied to dev/test databases

## Active Branch

`main`

## Recently Completed

- **2026-06-20 Session 4 (Backend):** Scaffolded `snx-workflow` service. Resolved transition state machine validations and database audit log UUID generation. Created 7 new unit, integration, and security tests. Optimized test isolation by introducing table truncation in `db_session` conftest fixture. All tests PASS.
- **2026-06-20 Session 3 (Orchestrator):** Scaffolded `snx-academic` and `snx-institution` services, migrations, and integration tests.
- **2026-06-20 Session 2 (Backend/Testing):** CryptContext fix + auth role MFA tests verification.
- **2026-06-20 Session 1 (Orchestrator):** Root project and packages scaffold.

## Up Next

1. **DevOps Agent (09):** Create Dockerfiles for `snx-auth`, `snx-academic`, `snx-institution`, and `snx-workflow` microservices.
2. **DevOps Agent (09):** Setup `.github/workflows/ci.yml` pipeline validating lint rules and running test suites.
3. **DevOps Agent (09):** Configure local pre-commit hook validation script.

## Blockers

- None
