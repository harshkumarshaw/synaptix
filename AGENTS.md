# AGENTS.md — Non-Negotiable Rules for All Synaptix Agents

> **This file is mandatory reading at the start of EVERY agent session.**
> Violation of any rule in this file results in immediate session termination and rollback.

---

## 1. Identity & Context

You are an AI agent working on **Synaptix**, a multi-tenant Academic Operating System for Nirmala Foundation's medical and educational institutions. The platform is built with:

- Backend: FastAPI (Python 3.12) + SQLAlchemy 2 + PostgreSQL 16
- Frontend: Next.js 14 + TypeScript + Tailwind CSS
- Mobile: Flutter 3 + drift (SQLite)
- Deployment: Cloud Run → GKE
- Internal product code: **SNX**

You are operating under **solo-developer supervision**. The human supervising you cannot review every line of your output. Therefore, you MUST follow these rules without exception.

---

## 2. Mandatory Session Start Protocol

At the start of EVERY session, you MUST:

1. Read this file (`AGENTS.md`) completely
2. Read `AOIP_MASTER_SPEC_v5.md` (or at minimum the sections relevant to your task)
3. Read `.agent-memory/working/CURRENT_FOCUS.md` to understand current work state
4. Read your agent specialisation file at `agents/{your-id}-{your-name}-agent.md`
5. Read your personal memory files:
   - `.agent-memory/learning/{your-id}.md` (what you've learned)
   - `.agent-memory/incident/{your-id}.md` (what has gone wrong)
6. Read `docs/HANDOFF_NOTES.md` for messages from the previous session
7. Read the relevant convention files in `conventions/`
8. Declare your read of these files in the first response of the session

Format your declaration as:
```
SESSION START — Agent: {agent-id} {agent-name}
Files read: AGENTS.md ✓, MASTER_SPEC ✓, CURRENT_FOCUS ✓, agent spec ✓, learning ✓, incident ✓, HANDOFF_NOTES ✓
Task understanding: {brief}
```

If you skip this protocol, the human supervisor must terminate your session.

---

## 3. The Ten Commandments (Hard Rules — Never Violate)

### Commandment 1: Tenant Isolation is Sacred
Every database query, every API endpoint, every cache key MUST be scoped by `tenant_id`. Multi-tenant data leakage is the worst possible bug in this system. If you cannot determine the tenant context for an operation, STOP and escalate.

The middleware in `packages/shared/auth/tenant_context.py` enforces this automatically. **Never bypass it.** Never write a raw SQL query that doesn't include `tenant_id` filtering. Never create an API endpoint without the `@require_tenant_context` decorator.

### Commandment 2: NMC Compliance Tests Hard-Fail the Build
The NMC compliance test suite at `tests/compliance/` is sacrosanct. If your changes cause any NMC compliance test to fail, the build will fail and your commit will be rejected. Do not modify NMC compliance tests to make them pass. If a test seems wrong, escalate to the human supervisor — do not "fix" it yourself.

### Commandment 3: Two-Threshold Attendance is Mandatory for MBBS
For MBBS programmes, attendance has TWO thresholds enforced separately:
- **75% minimum** for theory attendance
- **80% minimum** for practical/clinical/DOAP/ECE attendance

Never write code that uses a single threshold for MBBS. Never default to 75% for practical attendance.

### Commandment 4: No Hardcoded Secrets, Ever
API keys, passwords, database URLs, JWT secrets, encryption keys MUST come from environment variables or Google Secret Manager. Never commit a `.env` file with real values. Never paste a secret into a docstring, comment, or test.

If you discover a hardcoded secret in existing code, log it in `docs/INCIDENT_LOG.md` immediately and replace it with an environment variable reference.

### Commandment 5: Update Documentation Before Committing
Before any commit, you MUST update:
- `docs/CHANGELOG.md` — what changed
- `docs/sessions/YYYY-MM-DD-session-N.md` — your session log
- `docs/DEVELOPMENT_LOG.md` — high-level summary
- `.agent-memory/working/CURRENT_FOCUS.md` — current state
- Any other relevant log file (BUG_LOG, MIGRATION_LOG, DEPENDENCY_LOG, etc.)

The pre-commit hook at `scripts/pre-commit-hook.ps1` will reject your commit if these are not updated.

### Commandment 6: Stay Within Your Specialisation
You have a specialisation defined in your agent file. Do NOT modify files outside your specialisation without escalating to the human supervisor or the orchestrator agent. Specifically:

- Backend agent: do not modify `frontend-web/` or `frontend-mobile/`
- Frontend agent: do not modify `services/` (backend) directly
- Mobile agent: do not modify backend services or web frontend
- Database agent: do not modify business logic in services
- Testing agent: can read everything but only modify `tests/`
- Security/Reviewer agent: can read everything but only adds annotations/reviews

If your task requires changes outside your specialisation, STOP and escalate.

### Commandment 7: Never Modify Shared Library Without Approval
`packages/shared/` is sacred ground. Changes here affect every service. Do NOT modify shared library code unless:
- The task explicitly authorises it, AND
- The human supervisor has approved the change, AND
- All affected services' tests pass

If you need a new shared utility, create it in your current service first. The human or orchestrator will promote it to shared if appropriate.

### Commandment 8: Test Coverage Manifest is Mandatory
Every module has a section in `tests/COVERAGE_MANIFEST.yaml` listing required test cases. After writing any code, you MUST:
- Implement every test case listed for that module
- Run `python scripts/verify_coverage_manifest.py {module}` to confirm
- Fix any missing tests before committing

The test enforcement agent runs this check pre-commit. If you skip tests, the build fails.

### Commandment 9: No Breaking Changes Without Migration
If your changes break an existing API contract or database schema, you MUST:
- Create a migration script (Alembic for DB, version bump for API)
- Document the breaking change in `docs/CHANGELOG.md` under "BREAKING"
- Update `docs/MIGRATION_LOG.md` with rollback instructions
- Bump the API version (v1 → v2) and maintain v1 with deprecation warning

### Commandment 10: When in Doubt, Stop and Ask
You are not authorised to make significant architectural decisions. If you encounter:
- An ambiguous requirement
- A conflict between two parts of the spec
- A test that seems wrong
- A regulatory question (NMC, NAAC, DPDP)
- A data model design question
- A security implication you're uncertain about

STOP. Write your question to `.agent-memory/working/QUESTIONS.md` and end the session. The human supervisor will answer before the next session.

---

## 4. Code Quality Standards (Non-Negotiable)

### Python
- Python 3.12 only
- Type hints on every function signature
- Pydantic v2 for all data validation
- SQLAlchemy 2.0 syntax (declarative style with `Mapped[]`)
- `ruff` for linting, `black` for formatting (both run pre-commit)
- `mypy --strict` for type checking — no `Any` types except where unavoidable
- Docstrings in Google style for every public function
- No `print()` — use the structured logger from `packages/shared/logging`

### TypeScript
- TypeScript strict mode enabled
- No `any` types
- Functional React components with hooks (no class components)
- Tailwind utility classes (no inline styles, no CSS modules unless approved)
- ESLint + Prettier (run pre-commit)
- Components in PascalCase, hooks in camelCase with `use` prefix

### SQL
- snake_case for all table and column names
- Plural table names (`students`, not `student`)
- Foreign keys named `{referenced_table_singular}_id`
- Every table must have `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
- Every tenant-scoped table must have `tenant_id UUID NOT NULL`
- Every table must have `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- Every table that supports updates must have `updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- Row Level Security policy on every tenant-scoped table

### Commits
- Conventional Commits format: `<type>(<scope>): <subject>`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`
- Subject in imperative mood, lowercase, no period at end
- Body explains the WHY, not the WHAT
- Footer references issue numbers and breaking changes
- Sign commits with your agent ID: `Co-authored-by: {agent-name} <{agent-id}@synaptix.local>`

Example:
```
feat(attendance): add two-threshold eligibility check for MBBS

NMC CBME 2019/2023 mandates 75% theory and 80% practical attendance
as separate thresholds. Previously the system used a single 75%
threshold which incorrectly passed students with insufficient
practical attendance.

Refs: AUDIT-G1
Co-authored-by: backend-agent <02@synaptix.local>
```

---

## 5. Mandatory Session End Protocol

Before ending a session, you MUST:

1. Update `.agent-memory/working/CURRENT_FOCUS.md` with current state
2. Append to `.agent-memory/learning/{your-id}.md` any new patterns or discoveries
3. Append to `.agent-memory/incident/{your-id}.md` any failures or near-misses
4. Update `docs/sessions/YYYY-MM-DD-session-N.md` with complete session log
5. Update `docs/CHANGELOG.md` with summary
6. Update `docs/COMMAND_HISTORY.md` with every bash/terminal command run
7. Update `docs/HANDOFF_NOTES.md` with explicit notes for the next session
8. Run all relevant tests and confirm they pass
9. Commit your work (if not already committed)
10. Declare session end:

```
SESSION END — Agent: {agent-id} {agent-name}
Duration: ~{X} minutes
Files modified: {count}
Tests added: {count}
Tests passing: {count}/{count}
Commits made: {count}
Documentation updated: ✓
Memory updated: ✓
Next session should: {brief instruction}
```

---

## 6. Communication With Other Agents

You communicate with other agents asynchronously through files:

- `.agent-memory/working/CURRENT_FOCUS.md` — shared current focus
- `docs/HANDOFF_NOTES.md` — explicit messages to next session
- `docs/sessions/YYYY-MM-DD-session-N.md` — your session log (visible to all)
- `.agent-memory/learning/shared.md` — cross-agent learnings

If you need another specialist agent to do work, do NOT do it yourself. Instead:
- Add a task to `docs/HANDOFF_NOTES.md` addressed to that agent
- End your session
- The human supervisor or orchestrator will invoke the appropriate agent

---

## 7. Error Handling Philosophy

Synaptix handles errors at three levels:

1. **Validation errors** (Pydantic) — return 400 with structured error
2. **Business logic errors** — raise domain-specific exceptions (e.g., `AttendanceShortfallError`)
3. **System errors** — let them bubble up, the global handler logs and returns 500

Every domain exception must:
- Inherit from `SynaptixError` (in `packages/shared/errors`)
- Have a unique error code (e.g., `SNX-ATT-001`)
- Be documented in `conventions/ERROR_HANDLING.md`
- Have a corresponding test in `tests/`

Never swallow exceptions silently. Never use bare `except:` clauses. Always log with structured context.

---

## 8. Performance Standards

- API p95 response time: < 500ms (production), < 800ms (development)
- Database queries: must use indexes for any WHERE clause filtering
- N+1 queries: forbidden. Use `selectinload` or `joinedload` in SQLAlchemy.
- Cache invalidation: tenant-scoped, never global
- Background jobs: anything > 2 seconds should be a Celery task or Cloud Run Job

---

## 9. Security Standards

- All user input MUST be validated through Pydantic models
- All database queries MUST use parameterised queries (SQLAlchemy ORM enforces this)
- All API endpoints MUST require authentication except `/health`, `/ready`, and public auth endpoints
- MFA REQUIRED for admin, principal, dean, controller_of_examinations roles
- Audit log writes are mandatory for: data modifications, login attempts, permission changes, exemption grants
- Audit log table is APPEND-ONLY (enforced by PostgreSQL trigger)

---

## 10. NMC CBME Awareness

Synaptix supports two curriculum versions simultaneously:

- **NMC CBME 2019** — for JMN's 2023 admission batch (currently in Phase II)
- **NMC CBME 2023** — for JMN's 2024 admission batch onwards

Both curricula must coexist. Both have valid competency banks. Both have valid phase structures. Code must NEVER assume a single curriculum version.

Refer to `tests/NMC_COMPLIANCE_TESTS.md` for every regulation that must be enforced.

---

## 11. Escalation Path

When you cannot proceed:

1. First — re-read this AGENTS.md and the master spec
2. Second — check `.agent-memory/learning/` and `.agent-memory/incident/` for prior solutions
3. Third — check `docs/DECISIONS.md` for existing architectural decisions
4. Fourth — if still stuck, write to `.agent-memory/working/QUESTIONS.md` and end the session

NEVER:
- Guess at requirements
- Invent a regulation that isn't in the spec
- Assume a default that wasn't explicitly set
- Make architectural decisions on your own

---

## 12. Final Rule: This File Updates Over Time

This file is version-controlled. If the human supervisor updates it, the new version takes effect immediately. You are not authorised to modify this file yourself. If you believe a rule needs to change, write your reasoning to `docs/HANDOFF_NOTES.md` with the prefix `[AGENTS.md PROPOSAL]`.

---

**Last updated:** 2026-06-18 (initial framework setup)
**Updated by:** Sila Singh Ghosh (project owner)
