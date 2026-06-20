# Current Focus

> Shared across all agents. Updated at every session.

## Current Phase

**Phase 1A:** Foundation Modules — In Progress

## Active Modules

- `packages/shared` — scaffold complete (logging, errors, db, auth)
- `services/snx-auth` — scaffold complete, business logic stubbed
- `services/_migrations` — first migration (foundation tables) created

## Active Branch

`main` (initial setup)

## Recently Completed

- 2026-06-20 Session 1: Environment setup + packages/shared + snx-auth scaffold + first migration

## Up Next

1. **Human:** Start Docker Desktop, run `docker compose up -d postgres`
2. **Human:** Create GitHub repo (private) at github.com/new, push initial commit
3. **Database Agent (05):** Run `alembic upgrade head` to apply foundation migration
4. **Backend Agent (02):** Implement auth service login/OTP/MFA methods + User model
5. **DevOps Agent (09):** Create Dockerfiles + GitHub Actions CI
6. **Flutter installation:** Deferred to Phase 2

## Blockers

- Docker Desktop not yet started (manual action by Harsh)
- GitHub repo not yet created (manual action by Harsh)
