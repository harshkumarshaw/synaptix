# Database Conventions — Synaptix

## PostgreSQL Version
PostgreSQL 16. We use:
- UUID v4 primary keys (`gen_random_uuid()`)
- JSONB for flexible structured data
- TIMESTAMPTZ for all timestamps (stored as UTC)
- Row Level Security on every tenant-scoped table
- Foreign keys with explicit `ON DELETE` behaviour
- Indexes on every column used in WHERE/JOIN/ORDER BY

## Naming

- Tables: plural snake_case (`students`, `attendance_records`)
- Columns: snake_case
- Primary key: always `id UUID`
- Foreign keys: `{singular_table}_id`
- Indexes: `idx_{table}_{columns}` (e.g., `idx_attendance_student_subject`)
- Unique constraints: `uq_{table}_{columns}`
- Check constraints: `chk_{table}_{description}`
- Functions: `fn_{description}` (e.g., `fn_calc_attendance_pct`)
- Triggers: `trg_{table}_{event}_{action}` (e.g., `trg_attendance_insert_summary`)

## Every Tenant-Scoped Table Must Have

```sql
CREATE TABLE table_name (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    -- business columns
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ  -- soft delete; NULL = active
);

-- Mandatory: composite unique constraint to support composite foreign keys
ALTER TABLE table_name ADD CONSTRAINT uq_table_name_tenant_id_id UNIQUE (tenant_id, id);

-- Mandatory: index tenant_id
CREATE INDEX idx_table_name_tenant ON table_name(tenant_id) WHERE deleted_at IS NULL;

-- Mandatory: enable RLS
ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON table_name
    USING (tenant_id = current_setting('snx.current_tenant_id', true)::UUID);

-- Mandatory: auto-update updated_at
CREATE TRIGGER trg_table_name_update
    BEFORE UPDATE ON table_name
    FOR EACH ROW EXECUTE FUNCTION fn_update_updated_at();
```

## Migration Conventions (Alembic)

### One Chain for the Whole Monorepo

All migrations live in `services/_migrations/versions/`. NOT per-service. This prevents ordering conflicts.

### Migration File Format

```python
"""Add two-threshold attendance support.

Revision ID: 20260618_a1b2c3
Revises: 20260617_x9y8z7
Created: 2026-06-18

Refs: AUDIT-G1, NMC GMER 2019 §11.1
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260618_a1b2c3'
down_revision = '20260617_x9y8z7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('events', sa.Column(
        'attendance_category',
        sa.String(30),
        nullable=False,
        server_default='theory'
    ))
    op.create_index(
        'idx_events_attendance_category',
        'events',
        ['attendance_category']
    )
    # Backfill data if needed
    op.execute("UPDATE events SET attendance_category = 'practical' WHERE event_type = 'practical_session'")


def downgrade() -> None:
    op.drop_index('idx_events_attendance_category', 'events')
    op.drop_column('events', 'attendance_category')
```

### Migration Rules

1. EVERY migration must have a working `downgrade()`
2. Test both `upgrade()` and `downgrade()` before committing
3. Backfill data in the same migration as schema changes
4. Document the reason in the docstring with references (audit IDs, NMC sections)
5. Update `docs/MIGRATION_LOG.md` after creating

## Row Level Security

```sql
-- Set tenant context at session start (done by middleware)
SET LOCAL snx.current_tenant_id = 'tenant-uuid-here';

-- All queries automatically filtered:
SELECT * FROM students;  -- only sees students of current tenant
```

The middleware in `packages/shared/db/session.py` sets this on every request. Never bypass.

## Performance

### Indexes

Every column appearing in:
- WHERE clause
- JOIN ON
- ORDER BY
- GROUP BY

Must have an index. Composite indexes for multi-column filtering.

### Avoid N+1

Use `selectinload` (separate query, IN clause) or `joinedload` (LEFT JOIN):

```python
# selectinload — better for one-to-many
stmt = select(Student).options(selectinload(Student.attendance_records))

# joinedload — better for many-to-one
stmt = select(Attendance).options(joinedload(Attendance.student))
```

### Materialised Views

For expensive aggregations (attendance percentages), use materialised views:

```sql
CREATE MATERIALIZED VIEW attendance_summary AS
SELECT
    student_id,
    subject_code,
    attendance_category,
    COUNT(*) FILTER (WHERE status = 'present') AS attended,
    COUNT(*) AS total,
    100.0 * COUNT(*) FILTER (WHERE status = 'present') / NULLIF(COUNT(*), 0) AS pct
FROM attendance a
JOIN events e ON e.id = a.event_id
WHERE e.status = 'conducted'  -- only conducted sessions count
GROUP BY student_id, subject_code, attendance_category;

CREATE UNIQUE INDEX ON attendance_summary(student_id, subject_code, attendance_category);

-- Refresh periodically or via trigger
REFRESH MATERIALIZED VIEW CONCURRENTLY attendance_summary;
```

### Partitioning

Large tables partitioned by `academic_year_id`:

```sql
CREATE TABLE attendance (
    ...
) PARTITION BY RANGE (academic_year_id);

CREATE TABLE attendance_2024_2025 PARTITION OF attendance
    FOR VALUES FROM ('uuid-2024-2025-start') TO ('uuid-2024-2025-end');
```

## Audit Log (Append-Only)

```sql
-- Prevent UPDATE
CREATE OR REPLACE FUNCTION fn_audit_log_no_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_log_no_update
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION fn_audit_log_no_update();
```

## DPDP Act 2023 Compliance

- Personal data fields tagged with comment `-- PII`
- Aadhaar stored as `aadhaar_hash` (never plaintext)
- Soft delete preserves data for 7-year retention
- After retention period: personal fields anonymised, business data preserved

---

## Cross-Reference Integrity Triggers

**Added:** Session 11 (R0.4) — formalises ADR-021 pattern

### When to Use Triggers Instead of CHECK Constraints

PostgreSQL `CHECK` constraints **cannot** reference other tables (subqueries forbidden in CHECK). When you need to validate that a FK value satisfies a cross-table condition, use a `BEFORE INSERT OR UPDATE` trigger with `RAISE EXCEPTION`.

**Rule:** If your validation requires `SELECT ... FROM another_table`, it is a trigger, not a CHECK.

### Pattern

```sql
CREATE OR REPLACE FUNCTION fn_verify_{table}_{condition}()
RETURNS TRIGGER AS $$
BEGIN
    IF <condition involving NEW row> THEN
        IF NOT EXISTS (
            SELECT 1 FROM {other_table}
            WHERE id = NEW.{fk_column}
              AND tenant_id = NEW.tenant_id
              AND {additional_condition}
        ) THEN
            RAISE EXCEPTION
                '{fk_column} % does not satisfy {condition} under tenant %',
                NEW.{fk_column}, NEW.tenant_id
            USING ERRCODE = '23514';  -- check_violation
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_verify_{table}_{condition}
BEFORE INSERT OR UPDATE OF {relevant_columns} ON {table}
FOR EACH ROW
EXECUTE FUNCTION fn_verify_{table}_{condition}();
```

### Real Example: Attendance Session-Event Consistency

```sql
-- fn_verify_attendance_session_event validates that session_id belongs to event_id
-- (Cannot be a CHECK because it queries the sessions table)
CREATE OR REPLACE FUNCTION fn_verify_attendance_session_event()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.session_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM sessions
            WHERE id = NEW.session_id
              AND tenant_id = NEW.tenant_id
              AND event_id = NEW.event_id
              AND deleted_at IS NULL
        ) THEN
            RAISE EXCEPTION
                'session_id % does not belong to event_id % under tenant %',
                NEW.session_id, NEW.event_id, NEW.tenant_id
            USING ERRCODE = '23514';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_verify_attendance_session_event
BEFORE INSERT OR UPDATE OF session_id, event_id, tenant_id ON attendance
FOR EACH ROW
EXECUTE FUNCTION fn_verify_attendance_session_event();
```

### Trigger Naming Convention

- Function: `fn_verify_{table}_{what_is_being_verified}`
- Trigger: `trg_verify_{table}_{what_is_being_verified}`
- Always `BEFORE INSERT OR UPDATE` — never AFTER for validation triggers
- Specify only the columns that can violate the constraint in `UPDATE OF ...`

---

## Composite Foreign Key Requirements

**Added:** Session 11 (R0.4) — formalises ADR-009

### Core Rule

Every tenant-scoped table **MUST** have a `UNIQUE (tenant_id, id)` constraint in addition to its primary key. This enables composite FKs from other tables.

```sql
-- Every tenant-scoped table must have:
UNIQUE (tenant_id, id)
```

### Why

A simple `FOREIGN KEY (student_id) REFERENCES students(id)` does NOT enforce tenant isolation — it allows cross-tenant references (e.g., row in tenant A referencing a student from tenant B if the student_id happens to match). Composite FKs enforce that the FK stays within the same tenant.

### All Cross-Table FKs Must Be Composite

```sql
-- WRONG — cross-tenant reference possible:
FOREIGN KEY (student_id) REFERENCES students(id)

-- CORRECT — both tenant and ID must match:
FOREIGN KEY (tenant_id, student_id) REFERENCES students(tenant_id, id)
```

### Migration Template: Add UNIQUE Constraint to Existing Table

When you discover a table missing the `UNIQUE (tenant_id, id)` constraint:

```sql
-- Migration: add the composite unique constraint
ALTER TABLE {table_name}
    ADD CONSTRAINT uq_{table_name}_tenant_id UNIQUE (tenant_id, id);

-- Then any table that FK-references it must update its FK:
ALTER TABLE {referencing_table}
    DROP CONSTRAINT {old_fk_name},
    ADD CONSTRAINT {new_fk_name}
        FOREIGN KEY (tenant_id, {fk_column})
        REFERENCES {table_name}(tenant_id, id)
        ON DELETE {action};
```

### Checklist for New Tables

Before finalising any new table:

- [ ] `UNIQUE (tenant_id, id)` constraint present
- [ ] All FKs to other tenant-scoped tables are composite (tenant_id + target_id)
- [ ] RLS policy uses `tenant_id = current_setting('snx.current_tenant_id', true)::UUID`
- [ ] FK names follow convention: `fk_{table}_{target_column}` or Alembic-generated

---

## Trigger vs Service Layer Decision Matrix

**Added:** Session 11 (R0.4) — formalises ADR-030

### Decision Rule

| Characteristic | Use DB Trigger | Use Service Layer |
|---------------|----------------|-------------------|
| Scope | Single table, or two closely related tables in same migration | Cross-module, cross-service |
| Query complexity | Simple WHERE, single JOIN | Multi-step logic, conditional branching across 3+ tables |
| Business logic | None — pure data derivation | Yes — workflow steps, business rules |
| Testability | Hard (requires live DB) | Easy (Python unit test) |
| HTTP/external calls needed | No | Yes |
| Timing requirement | Must fire atomically with data change | Can be eventually consistent (< 2s) |
| Example | `fn_update_updated_at`, `fn_audit_log_no_update` | `aetcom_sync_service.on_attendance_change()` |

### Use Trigger For

- **Simple derived data within a single table** — `updated_at` recalculation, `is_completed = (hours >= required_hours)`
- **Append-only audit log writes** — `audit_log` inserts on data changes (see Audit Trail section)
- **Cross-reference integrity validation** — `fn_verify_attendance_session_event` pattern (see above)
- **Simple fanout** — creating attendance rows for a new event from existing leave approvals

### Use Service Layer For

- **Cross-module synchronisation** — AETCOM status depends on attendance + reflection + faculty sign-off (three independent tables across two services)
- **Business workflow steps** — leave approval triggers attendance materialisation, which may require creating/updating multiple rows with conflict resolution
- **Anything requiring HTTP calls** — notifications, external audit system writes
- **Complex conditional logic** — DOAP state machine, elective allocation algorithm
- **Operations that must be unit-testable without a database** — pure Python functions are far easier to test than PL/pgSQL

### Anti-Pattern: Heavy Trigger

If a trigger function is more than 30 lines of PL/pgSQL, has more than 2 JOINs, or branches on 3+ conditions, it should be moved to the service layer. Heavy triggers:

- Create hidden coupling between tables (change one table, break a trigger on another)
- Are hard to test (require full DB setup)
- Accumulate technical debt (hard to debug in production)
- Can cause unexpected lock chains

### Canonical Examples

**Trigger (correct):**
```sql
-- Simple derived column update: total_allocated += 1 when an allocation row is inserted
-- This is in-transaction, simple arithmetic, single table
CREATE OR REPLACE FUNCTION fn_update_elective_capacity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE electives SET capacity_remaining = capacity_remaining - 1
    WHERE tenant_id = NEW.tenant_id AND id = NEW.elective_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**Service layer (correct):**
```python
# AETCOM sync: requires attendance table + aetcom_records + reflection_submissions
# Three tables, non-linear logic, must be testable without DB
async def on_attendance_change(
    session: AsyncSession,
    tenant_id: UUID,
    student_id: UUID,
    attendance_record: Attendance,
) -> None:
    """Update aetcom_records.status when attendance changes."""
    if attendance_record.attendance_category != 'aetcom':
        return
    new_status = await compute_aetcom_status(session, tenant_id, student_id, ...)
    await session.execute(
        update(AetcomRecord).where(...).values(status=new_status, ...)
    )
```
