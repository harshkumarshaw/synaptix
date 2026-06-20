# 02-backend — Incident Memory

Failures, near-misses, and what NOT to do.

## Incidents

- **Audit Log Append-Only Conflict during Test Cleanup:** Previous runs wrote to `audit_log` with `actor_user_id` referencing a test user. When subsequent integration tests attempted to clean up the `users` table via `DELETE`, PostgreSQL triggered an `ON DELETE SET NULL` reference update on `audit_log`, which was blocked by the append-only trigger (`trg_audit_log_no_update`), causing the entire test cleanup transaction to abort.
- **Null Reference on Audit Log Insertion:** Creating a digital asset and writing to the audit log immediately after failed because `asset.id` was not yet populated by SQLAlchemy, violating the `resource_id` NOT NULL constraint on `audit_log`.

## Things That Failed

- Deleting from parent tables (`users`) while `audit_log` references them in an append-only environment.
- Accessing generated `id` fields of added entities without calling `session.flush()`.

## Things to Avoid

- Avoid manual user/tenant deletion in individual tests without considering append-only logging tables.
- Never write to database-enforced dependency tables (such as audit logs) using newly added ORM objects without flushing them first.
