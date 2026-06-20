# 00-orchestrator — Incident Memory

Failures, near-misses, and what NOT to do.

## Incidents

- **Join Table Schema Mismatch (2026-06-20):** Join tables `event_faculty`, `event_courses`, and `session_faculty` were created without `id`, `created_at`, `updated_at`, or `deleted_at` columns, but the corresponding SQLAlchemy models inherited from `TenantScopedBase` which automatically maps these columns. This caused a `ProgrammingError` on all database operations on these tables.
- **Workflow Entity Type Constraint Violation (2026-06-20):** Passing `"lesson_plan"` instead of `"lesson_plan_approval"` in workflow instance entity type triggered a database check constraint violation (`chk_workflow_instances_entity_type`).

## Things That Failed

- Reusing the database engine with default connection pooling in Windows function-scoped tests. It resulted in `RuntimeError: Event loop is closed` on subsequent tests.

## Things to Avoid

- Avoid omitting `id` and timestamp columns in any table, even join tables, when the corresponding SQLAlchemy model inherits from `TenantScopedBase`. Keep migration schemas in exact lockstep with SQLAlchemy base models.
