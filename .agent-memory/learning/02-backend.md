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
