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

(None yet.)
