# Session 15 Plan — Phase 2 Final Cleanup (Short Session)

**Target Agent:** 02-backend or 06-testing
**Estimated duration:** 1-2 hours maximum
**Goal:** Close the 4 known issues from Session 14, make Phase 2 airtight, then STOP.

---

## This Is a Cleanup Session, Not a Feature Session

Session 14 declared Phase 2 complete with 178/178 coverage and 0 failures. Four minor issues remain. Fix them, commit, and stop. Do not start Phase 2.5 or Phase 3 work in this session.

---

## Task 1: FCS-002 Trigger Migration Patch (15 min)

The Foundation Course trigger references `actor_id` but the column is `actor_user_id`.

Create migration `0017_fix_fcs_trigger_column.py`:

```sql
CREATE OR REPLACE FUNCTION fn_sync_attendance_to_foundation_course()
RETURNS TRIGGER AS $$
-- [same trigger body but with actor_user_id instead of actor_id]
$$ LANGUAGE plpgsql;
```

Apply locally:
```powershell
alembic upgrade head
```

Run the FCS-002 test to confirm it passes:
```powershell
pytest tests/integration/test_sync.py::test_fcs_002 -v
```

Update `docs/MIGRATION_LOG.md` with migration 0017.

---

## Task 2: Remove 12 xpassed Stubs (15 min)

These are tests that were marked `@pytest.mark.xfail` but now pass because the underlying implementation landed. The xfail marker is stale.

```powershell
# Find all xpassed tests
pytest tests/ --tb=no -q 2>&1 | Select-String "XPASS"
```

For each xpassed test:
1. Open the file
2. Remove the `@pytest.mark.xfail(reason="...")` decorator
3. Verify the test still passes without the marker

After removing all 12:
```powershell
pytest tests/ -v --tb=short -q
# Expected: 0 xpassed (all converted to regular passes)
```

---

## Task 3: LEV-002/003 Async Race Fix (15-20 min)

Leave state transition tests have an async race condition. Typical fix:

```python
# Before (racy):
await service.approve_leave(leave_id)
result = await service.get_leave(leave_id)
assert result.status == "approved"

# After (explicit flush):
await service.approve_leave(leave_id)
await session.flush()
await session.refresh(leave_request)
assert leave_request.status == "approved"
```

Or use `await session.commit()` followed by a fresh query in a new session scope.

Run the leave tests in isolation to confirm:
```powershell
pytest tests/integration/test_leave*.py -v
```

---

## Task 4: ELEC SQLite → PostgreSQL Fixture (15-20 min)

`test_elective_service.py` uses SQLite which doesn't support some PostgreSQL features (partial unique indexes, FOR UPDATE locks). Switch to the async PostgreSQL test fixture.

```python
# Change from:
@pytest.fixture
async def test_db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    ...

# To:
@pytest.fixture
async def test_db_session():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/synaptix_test"
    )
    ...
```

Or better — use the project's shared test fixture from `tests/conftest.py` if one exists for PostgreSQL.

Run elective tests:
```powershell
pytest tests/unit/electives/test_elective_service.py -v
```

---

## Final Verification (10 min)

```powershell
# All verifiers
python scripts/verify_adr_sequence.py
python scripts/verify_coverage_manifest.py
python scripts/verify_edge_case_coverage.py
python scripts/verify_compliance_coverage.py
python scripts/check_secrets.py

# Full test suite
pytest tests/ -v --tb=short -q

# Expected: 0 failed, 0 xpassed, minimal xfailed (only deferred tests)
```

---

## Update Scorecard (5 min)

Update `docs/verification/phase2_scorecard.md` with final numbers:

```markdown
## Final Numbers (Post-Cleanup)

| Metric | Session 14 | Session 15 (Final) |
|--------|-----------|-------------------|
| Coverage verifier | 178/178 (100%) | 178/178 (100%) |
| Tests passing | 109 | NN (should be 121 = 109 + 12 xpassed) |
| Tests xfailed | 14 | NN (should decrease) |
| Tests xpassed | 12 | 0 (all converted) |
| Tests FAILED | 0 | 0 |

Known issues resolved:
- FCS-002 trigger column: FIXED (migration 0017)
- 12 xpassed stubs: FIXED (markers removed)
- LEV async race: FIXED
- ELEC SQLite fixture: FIXED
```

---

## Commit (5 min)

```powershell
git add .
git commit -m "fix: Session 15 — Phase 2 final cleanup

- Migration 0017: fix FCS trigger column (actor_id → actor_user_id)
- Remove 12 stale xfail markers (tests now pass)
- Fix LEV-002/003 async race in leave state transitions
- Switch ELEC tests from SQLite to PostgreSQL fixture

Phase 2 is now fully clean. 0 known issues remaining.

Refs: Session 14 known issues list
"
```

No `--no-verify`.

---

## Session End Declaration

```
SESSION END — Agent: {id} (Session 15 — Phase 2 Final Cleanup)
Duration: ~1-2 hours

4 known issues: ALL RESOLVED
Tests passing: NN (up from 109)
Tests xpassed: 0 (down from 12)
Tests FAILED: 0
Coverage: 178/178 (100%)
All verifiers: CLEAN

PHASE 2 IS FULLY COMPLETE. No remaining known issues.
Next: Phase 2.5 or Phase 3 planning (separate session).
```

---

## What Comes After Session 15

Phase 2 is done. Before the next implementation session, you need a PLANNING session:

### Option A: Phase 2.5 (Deferred Items)

If there are Phase 2 features needed before Phase 3 can start:
- 11 deferred tests from Session 14 (MDM templates, calendar edge cases, lesson plan retention)
- 78 hardware/mobile deferred tests (RFID, GPS, biometric, offline sync)
- Technical debt items D7-D10

Estimate: 3-5 sessions

### Option B: Phase 3 (Examination Management)

If Phase 2 deferrals can wait:
- Create Phase 3 master plan (same R0→R5 structure as Phase 2)
- Primary module: Examination Management
- Secondary: Report generation, full admission engine

Estimate: 10-15 sessions using the same framework

### Option C: Deploy Phase 2 to Staging

If the priority is getting Phase 2 in front of users:
- Cloud Run deployment configuration
- Database migration strategy for production
- Seed data for JMN Medical College
- UAT planning

The human supervisor decides which path. The framework is ready for any of them.