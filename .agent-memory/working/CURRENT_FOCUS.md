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

- **2026-06-20 Session 5 (Orchestrator):** Fixed database schema join table definitions (`event_courses`, `event_faculty`, `session_faculty`) in migrations and SQLAlchemy models. Resolved Pydantic schema validation for lesson plan code formats (allowing dots) and workflow entity check constraints. Introduced `NullPool` and clean engine teardown in `conftest.py` to prevent event loop closing warnings/errors in pytest. All 39 tests across all services pass.
- **2026-06-20 Session 4 (Backend):** Scaffolded `snx-workflow` service. Resolved transition state machine validations and database audit log UUID generation. Created 7 new unit, integration, and security tests. Optimized test isolation by introducing table truncation in `db_session` conftest fixture. All tests PASS.
- **2026-06-20 Session 3 (Orchestrator):** Scaffolded `snx-academic` and `snx-institution` services, migrations, and integration tests.
- **2026-06-20 Session 2 (Backend/Testing):** CryptContext fix + auth role MFA tests verification.
- **2026-06-20 Session 1 (Orchestrator):** Root project and packages scaffold.

## Up Next

1. **DevOps Agent (09):** Create/verify Dockerfiles for all microservices.
2. **DevOps Agent (09):** Setup `.github/workflows/ci.yml` pipeline validating lint rules and running test suites.
3. **DevOps Agent (09):** Configure local pre-commit hook validation script.

## Blockers

- None
