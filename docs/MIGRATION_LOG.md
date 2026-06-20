# Migration Log

Every database migration with rollback notes.

## Format

```markdown
### Migration: YYYYMMDD_revision_description

**Created:** YYYY-MM-DD
**Agent:** Database Agent
**Revision ID:** abc123
**Depends on:** def456

**Purpose:**
What this migration does and why.

**Changes:**
- Added table/column/index
- Removed ...
- Modified ...

**Data Migration:**
Backfill performed (or NONE).

**Rollback Tested:** Yes / No

**Verification:**
After applying, verify:
- Test: ...

**Related:**
- NMC ref: ...
- Audit ref: ...
- Commit: ...
```

## Migrations

### Migration: 20260620_0001_foundation_tables
**Created:** 2026-06-20
**Agent:** Database Agent (05)
**Revision ID:** 20260620_0001
**Depends on:** None

**Purpose:**
Initialize foundation tables including tenants, users, roles, user_roles, and partitioned append-only audit log. Enforce RLS on all tenant-scoped tables.

**Changes:**
- Created tables: tenants, users, roles, user_roles, audit_log (partitioned for 2026 and 2027)
- Added triggers for auto-updating updated_at
- Enabled RLS and created policies for user isolation
- Seeded JMN tenant and system roles

**Rollback Tested:** Yes

**Verification:**
- Connect to localhost:5435/synaptix_dev and verify public tables list

---

### Migration: 20260620_0002_create_academic_structure_tables
**Created:** 2026-06-20
**Agent:** Database Agent (05)
**Revision ID:** 20260620_0002
**Depends on:** 20260620_0001

**Purpose:**
Scaffold Module A-01 Academic Structure tables by creating academic_years, programs, and curricula tables.

**Changes:**
- Created tables: academic_years, programs, curricula
- Enabled RLS policies and tenant isolation filters
- Added triggers for auto-updating updated_at

**Rollback Tested:** Yes

**Verification:**
- Run alembic upgrade/downgrade cycles and check information_schema tables

---

### Migration: 20260620_0003_add_user_otp_fields
**Created:** 2026-06-20
**Agent:** Database Agent (05)
**Revision ID:** 20260620_0003
**Depends on:** 20260620_0002

**Purpose:**
Add otp_code and otp_expires_at columns to the users table to store OTP values in the database during verification.

**Changes:**
- Added columns `otp_code` (VARCHAR(10)) and `otp_expires_at` (TIMESTAMP WITH TIME ZONE) to the `users` table.

**Rollback Tested:** Yes

**Verification:**
- Check users table definition in postgres to confirm the new columns exist.

---

### Migration: 20260620_0004_add_role_soft_delete
**Created:** 2026-06-20
**Agent:** Database Agent (05)
**Revision ID:** 20260620_0004
**Depends on:** 20260620_0003

**Purpose:**
Add missing deleted_at column to roles and user_roles tables to support soft delete properties defined in SQLAlchemy TenantScopedBase model.

**Changes:**
- Added column `deleted_at` (TIMESTAMP WITH TIME ZONE) to `roles` table.
- Added column `deleted_at` (TIMESTAMP WITH TIME ZONE) to `user_roles` table.

**Rollback Tested:** Yes

**Verification:**
- Verify tests pass when accessing role-based SQLAlchemy operations.



