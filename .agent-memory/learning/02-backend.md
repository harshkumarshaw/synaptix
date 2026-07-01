# 02-backend — Learning Memory

Accumulated learnings, patterns, and discoveries.

## Patterns Established

- **Database Test Isolation via Truncation:** Use a global database truncation routine in the `db_session` fixture (scoped to the test database) to guarantee clean, idempotent test states across unit, integration, and security suites.
- **Explicit SQLAlchemy Flushes:** Always execute `await db.flush()` after adding new model instances if their primary keys (such as generated UUIDs) need to be referenced in subsequent side-effect operations (e.g., audit logging) within the same transaction.

## Anti-patterns Discovered

- **Bypassing Terminal Step Validation:** Allowing direct transitions to terminal steps (`approved`, `rejected`, `cancelled`) without checking the definition's `next_steps` configuration breaks the state machine integrity. Enforce that *all* transitions must be explicitly defined.

## Useful Code Snippets

### DB Truncation Routine for Ephemeral Test DB
```python
await session.execute(text("ALTER TABLE audit_log DISABLE TRIGGER trg_audit_log_no_update"))
await session.execute(
    text(
        "TRUNCATE TABLE timetable_entries, timetable_slots, students, faculty, user_roles, "
        "workflow_transitions, workflow_instances, digital_assets, users, sections, "
        "batches, courses, departments, curricula, programs, academic_years, "
        "workflow_definitions, master_data_entities, audit_log CASCADE"
    )
)
await session.execute(text("ALTER TABLE audit_log ENABLE TRIGGER trg_audit_log_no_update"))
await session.commit()
```

## Cross-Agent Insights

- **Namespace Conflicts (Orchestrator/Testing):** Since all monorepo microservices use the root `app` folder, running pytest globally causes namespace collisions. Run tests for each service individually with its specific `PYTHONPATH` configuration.

## Session 9 Learnings (2026-06-30)

- **Pydantic v2 migration details:** `ConfigDict(from_attributes=True)` is the standard in Pydantic v2, while Pydantic v1 `class Config` is strictly banned. Cross-field validations must use `@model_validator(mode='after')` and return `self`.
- **Database row-level locking:** When performing concurrent updates or allocations, run queries using `FOR UPDATE NOWAIT` and catch `sqlalchemy.exc.OperationalError` to raise a `LockNotAvailableError` (mapped to HTTP 409 Conflict) instead of waiting indefinitely.
- **Complex unit test mocking:** Highly relational service methods performing multiple DB queries (like `submit_preferences`) have fragile and complex unit mocks. These are far more cleanly verified using full integration tests with a database backend rather than nested `AsyncMock` setups.

## Session 13 Learnings (2026-07-01)

- **PostgreSQL CheckConstraint alignment in workflow testing:** When creating workflow instances, `entity_type` must be one of the check constraint permitted values (e.g. `exemption_grant`) to ensure migrations/constraints pass on PostgreSQL, even when the stub model defines more permissive types.
- **Async lazy loading and MissingGreenlet errors:** In async tests, eager load relationships via `selectinload` to prevent lazy-load `MissingGreenlet` errors when accessing nested properties (e.g. `workflow.workflow_definition_code`).

