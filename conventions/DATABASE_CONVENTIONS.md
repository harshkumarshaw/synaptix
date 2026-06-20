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
