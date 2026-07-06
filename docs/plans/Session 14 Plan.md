# Session 14 Plan — Phase 2 Completion Sprint

**Target Agent:** 02-backend (with 06-testing coordination)
**Estimated duration:** 6-8 hours (this is a BIG session — block a full day)
**Session structure:** 6 phases, no breaks between phases except Phase A gate
**Scope:** R4 gap-closure + R5 complete (xfail audit, integration tests, compliance tightening, performance baseline, Phase 2 declaration)
**Goal:** EXIT THIS SESSION WITH PHASE 2 DECLARED COMPLETE

---

## Why This Session Is Big

After Session 13, every R4 module is implemented:
- R4.1 Attendance ✓ (Sessions 6-8, 12)
- R4.2 Leave ✓ (Sessions 7-8)
- R4.3 Electives ✓ (Session 9)
- R4.4 DOAP ✓ (Session 10)
- R4.5 Logbook ✓ (Session 13)
- R4.6 Admission ✓ (Session 13)

What remains is NOT implementation — it is **verification, integration, and cleanup**. These are tasks that benefit from being done in a single concentrated sprint rather than spread across sessions, because:

1. Integration tests touch ALL modules simultaneously — switching between sessions loses cross-module context
2. xfail audit is a sweep, not iterative work — doing it in pieces creates new xfails while removing old ones
3. Performance baselines should be captured on a stable codebase, not between changes
4. The Phase 2 declaration is a single checkpoint — it either passes or it doesn't

**If this session cannot complete everything:** anything remaining becomes Session 15 (cleanup only). But the goal is to finish here.

---

## Mandatory Session Start Protocol

```
SESSION START — Agent: 02-backend (Session 14 — Phase 2 Completion Sprint)
Files read: AGENTS.md ✓, HANDOFF_NOTES ✓, CURRENT_FOCUS ✓, agent spec ✓,
learning ✓, incidents ✓, Session 13 log ✓, DECISIONS.md ✓ (ADR-001 through 037),
phase2_test_categorisation.md ✓, PHASE2_SCHEMA.md ✓
Task: Phase 2 Completion Sprint — R4 gaps + R5 complete
Goal: Exit with Phase 2 declared complete (86 must-pass tests all passing)
```

---

## Phase A — Progress Gate (15 min)

### A.1 Record Current State

```powershell
# Run coverage manifest to get exact count
python scripts/verify_coverage_manifest.py 2>&1 | Tee-Object docs/verification/pre_sprint_$(Get-Date -Format yyyyMMdd).txt

# Run all tests to get current pass/fail counts
python -m pytest tests/ -v --tb=no -q 2>&1 | Tee-Object docs/verification/pre_sprint_tests_$(Get-Date -Format yyyyMMdd).txt

# Run compliance tests separately (these must ALL pass)
python -m pytest tests/compliance/ -v --tb=short 2>&1 | Tee-Object docs/verification/pre_sprint_compliance_$(Get-Date -Format yyyyMMdd).txt
```

Record in session log:

```markdown
## Session 14 Starting Position

- Total tests in manifest: NNN
- Must pass Phase 2: 86
- Currently passing: NN/86
- Currently xfail: NN
- Currently missing (no stub): NN
- Compliance tests: NN/NN passing
- Gap to close this session: NN tests
```

### A.2 Classify the Gap

Scan the pre-sprint test output. For every test NOT passing, classify:

| Category | Action | Estimated effort |
|----------|--------|-----------------|
| xfail with implementation done | Remove xfail marker, verify passes | 2 min each |
| xfail with implementation incomplete | Implement, then remove xfail | 15-30 min each |
| Missing stub (no test file) | Create stub + implement | 20-40 min each |
| Failing (not xfail, actually broken) | Debug and fix — highest priority | Variable |
| Deferred (has deferred_to in manifest) | Skip — not in Phase 2 scope | 0 min |

This classification determines the rest of the session. If the gap is mostly "remove xfail markers," this session finishes fast. If the gap is mostly "implement from scratch," it will be tight.

### A.3 Priority Order for the Gap

Work through tests in this priority order:

1. **Failing tests (broken)** — fix these FIRST, they may be blocking others
2. **Compliance tests not yet passing** — these are hard-fail; Phase 2 cannot complete without them
3. **xfail tests with implementation done** — quick wins, remove markers
4. **xfail tests needing implementation** — ordered by dependency (integration tests last, they need unit tests to pass first)
5. **Missing stubs** — create and implement

---

## Phase B — xfail Audit and Conversion (90-120 min)

### B.1 Find All xfail Markers

```powershell
# Find every xfail in the codebase
Select-String -Path "tests\**\*.py" -Pattern "@pytest.mark.xfail" -Recurse | ForEach-Object { $_.Line.Trim() }
```

For each xfail found, determine:

- **Test ID** (from the reason string or docstring)
- **Is the implementation complete?** (Does the service method exist and work?)
- **Is this test deferred?** (Does the manifest have `deferred_to:` for this ID?)

### B.2 Quick Wins — Remove xfail Where Implementation Exists

For each test where the underlying service code is already implemented:

1. Remove `@pytest.mark.xfail(reason="...")`
2. Replace `raise NotImplementedError("Stub")` with actual test code
3. Run the test in isolation: `pytest tests/path/test_file.py::test_name -v`
4. If it passes: move on
5. If it fails: debug, fix, re-run

Track your progress:

```markdown
## xfail Conversion Log

| Test ID | File | Action | Result |
|---------|------|--------|--------|
| ELEC-003 | tests/integration/test_electives.py | Removed xfail, implemented | PASS ✓ |
| ELEC-005 | tests/integration/test_electives.py | Removed xfail, implemented | PASS ✓ |
| DOAP-007 | tests/integration/doap/test_workflows.py | Removed xfail, needs fixture | BLOCKED — see B.3 |
| LOG-003 | tests/integration/logbook/test_workflows.py | Removed xfail, implemented | PASS ✓ |
| ... | ... | ... | ... |
```

### B.3 Blocked Tests — Decide: Implement or Defer

For tests that can't pass because of missing fixtures, infrastructure, or cross-module dependencies:

**Option 1 — Implement the fixture.** If the fixture is < 30 min of work (e.g., creating a `sample_workflow_instance` factory), do it now.

**Option 2 — Defer with explicit reason.** If the fixture requires substantial infrastructure (e.g., standing up a real workflow engine with definitions seeded), add `deferred_to: "Phase 2.5"` to the manifest and document why.

**Do NOT leave xfail markers without either passing or deferring.** After Phase B, every test in the codebase is in one of three states:
- Passing (green)
- Deferred (in manifest with `deferred_to:`)
- Not in Phase 2 scope (not in manifest at all)

No orphan xfails. No "I'll get to it later."

### B.4 Phase B Checkpoint

```powershell
# Count remaining xfails
Select-String -Path "tests\**\*.py" -Pattern "@pytest.mark.xfail" -Recurse | Measure-Object

# Should be ZERO for Phase 2 must-pass tests
# Only deferred tests (Phase 2.5/3/4) should remain xfailed
```

Record:
```markdown
## Post-xfail Audit

- xfail markers removed this session: NN
- Tests now passing: NN
- Tests newly deferred (with deferred_to): NN
- Remaining xfail markers: NN (all must have deferred_to in manifest)
```

---

## Phase C — Cross-Module Integration Tests (60-90 min)

These are the tests that verify modules work TOGETHER. They are the highest-value tests in the entire suite because they catch the integration failures that unit tests miss.

### C.1 Integration Test Scenarios

Create or extend `tests/integration/test_cross_module.py`:

#### Scenario 1: Attendance → AETCOM Sync → Logbook (ATT-NMC-013 related)

```python
async def test_attendance_aetcom_sync_to_logbook(test_db_session, seed_data):
    """
    Cross-module: Mark attendance for AETCOM session → 
    aetcom_sync_service updates aetcom_records → 
    logbook entry reflects module status.
    
    Modules touched: snx-attendance, snx-logbook
    ADRs: ADR-030 (AETCOM service-layer sync)
    """
    # 1. Create AETCOM event + session
    # 2. Mark student as present
    # 3. Verify aetcom_records.status updated
    # 4. Submit AETCOM reflection via logbook
    # 5. Faculty signoff on AETCOM module
    # 6. Verify aetcom_records.status = 'completed'
    # 7. Verify logbook_entry exists with correct subject_code
```

#### Scenario 2: Leave → Attendance Materialisation → Summary Update (ADR-036)

```python
async def test_leave_approval_materialises_attendance(test_db_session, seed_data):
    """
    Cross-module: Submit medical leave → approve → 
    attendance rows auto-created with status='medical' → 
    attendance_summary recalculated.
    
    ADRs: ADR-036 (Leave-to-Attendance Materialisation)
    """
    # 1. Create events for the leave window (3 days)
    # 2. Submit medical leave request for those dates
    # 3. Approve leave
    # 4. Verify attendance rows exist for all 3 events with status='medical'
    # 5. Verify attendance_summary reflects the medical absences
    # 6. Verify leave_request_id is set on attendance rows
```

#### Scenario 3: Elective Allocation → Audit Log (ADR-034)

```python
async def test_elective_allocation_audit_trail(test_db_session, seed_data):
    """
    Cross-module: Run elective allocation → 
    verify elective_allocation_runs row created →
    verify audit_log entries →
    verify allocation counts match expected.
    
    ADRs: ADR-034 (Elective Allocation Algorithm)
    """
    # 1. Seed electives, students, preferences
    # 2. Run ranked allocation
    # 3. Verify elective_allocation_runs row exists
    # 4. Verify audit_log has action='run_allocation'
    # 5. Verify allocation counts match ADR-034 worked example
```

#### Scenario 4: DOAP P-Certified → Logbook Entry (ADR-035)

```python
async def test_doap_certification_creates_logbook(test_db_session, seed_data):
    """
    Cross-module: Complete DOAP progression D→O→A→P with C decisions →
    verify logbook_entry auto-created at each stage →
    verify competency state = 'certified' after P stage.
    
    ADRs: ADR-035 (DOAP State Machine)
    """
    # 1. Record D with C decision → verify logbook entry
    # 2. Record O with C decision → verify logbook entry
    # 3. Record A with C decision → verify logbook entry
    # 4. Record P with C decision → verify logbook entry
    # 5. Query DOAP state → assert 'certified'
    # 6. Count logbook entries → assert 4
```

#### Scenario 5: Logbook IA → Exam Eligibility (LOG-NMC-012 + ATT-NMC-001)

```python
async def test_ia_marks_factor_into_exam_eligibility(test_db_session, seed_data):
    """
    Cross-module: Complete logbook entries → IA marks calculated →
    attendance threshold met → student exam eligibility confirmed.
    
    Full flow: logbook completion + attendance threshold = eligible.
    Either one failing = not eligible.
    """
    # 1. Mark attendance to exactly 75% theory
    # 2. Create and approve logbook entries for the subject
    # 3. Verify IA marks calculated correctly
    # 4. Check exam eligibility → should be ELIGIBLE
    # 5. Reduce attendance to 74.99% → eligibility BLOCKED
```

#### Scenario 6: Foundation Course Hours Sync (ATT-NMC-014 related)

```python
async def test_foundation_course_attendance_hours_sync(test_db_session, seed_data):
    """
    Cross-module: Mark Foundation Course attendance →
    trigger fn_sync_attendance_to_foundation_course →
    foundation_course_records.completed_hours updated →
    is_completed flag set when threshold reached.
    
    ADRs: Foundation Course trigger (PHASE2_SCHEMA.md)
    """
    # 1. Create Foundation Course events (total 100 hours required)
    # 2. Mark present for 50 hours worth of events
    # 3. Verify completed_hours = 50, is_completed = false
    # 4. Mark present for 50 more hours
    # 5. Verify completed_hours = 100, is_completed = true
    # 6. Soft-delete one attendance record
    # 7. Verify completed_hours reduced, compliance_incidents row created (if signoff exists)
```

### C.2 Test Data Fixtures

Most integration tests need seeded data. Create a shared fixture factory:

```python
# tests/conftest.py or tests/integration/conftest.py

@pytest.fixture
async def seed_data(test_db_session):
    """Seed a minimal but complete dataset for cross-module testing."""
    tenant = await create_tenant(test_db_session, name="JMN Medical College")
    program = await create_program(test_db_session, tenant, name="MBBS", code="MBBS")
    curriculum = await create_curriculum(test_db_session, tenant, program, version="CBME 2019")
    
    # Create 5 students
    students = [
        await create_student(test_db_session, tenant, program, name=f"Student {i}")
        for i in range(1, 6)
    ]
    
    # Create 3 faculty
    faculty = [
        await create_faculty(test_db_session, tenant, name=f"Dr Faculty {i}")
        for i in range(1, 4)
    ]
    
    # Create courses
    anatomy = await create_course(test_db_session, tenant, curriculum,
                                   code="ANAT", subject_code="ANAT",
                                   name="Anatomy", default_attendance_category="theory")
    physiology = await create_course(test_db_session, tenant, curriculum,
                                      code="PHYS", subject_code="PHYS",
                                      name="Physiology", default_attendance_category="theory")
    
    # Create events (10 theory events per course)
    anatomy_events = [
        await create_event(test_db_session, tenant, anatomy,
                           event_type="theory", status="conducted",
                           date=date.today() - timedelta(days=30-i))
        for i in range(10)
    ]
    
    # Assign faculty to courses
    await assign_faculty(test_db_session, tenant, faculty[0], anatomy)
    await assign_faculty(test_db_session, tenant, faculty[1], physiology)
    
    await test_db_session.flush()
    
    return SimpleNamespace(
        tenant=tenant, program=program, curriculum=curriculum,
        students=students, faculty=faculty,
        anatomy=anatomy, physiology=physiology,
        anatomy_events=anatomy_events,
    )
```

If these factory functions don't exist yet, create them. They're reusable across all integration tests. Estimated time: 30-45 min for the full fixture setup if starting from scratch.

### C.3 Run Integration Suite

```powershell
python -m pytest tests/integration/ -v --tb=short 2>&1 | Tee-Object docs/verification/integration_results_$(Get-Date -Format yyyyMMdd).txt
```

Target: ALL integration tests passing. If any fail, debug immediately — integration failures usually indicate a service-level bug that was hidden by unit test mocking.

### C.4 Phase C Checkpoint

```markdown
## Cross-Module Integration Results

- Integration tests run: NN
- Integration tests passing: NN
- Integration tests failing: NN (list each with reason)
- New bugs discovered: NN (filed as BUG-NNN in BUG_LOG.md)
```

---

## Phase D — Compliance Test Tightening (45-60 min)

### D.1 Audit Every Compliance Test

For each test in `tests/compliance/`:

1. **Read the test.** Does it actually verify the regulation, or is it testing something tangentially related?
2. **Check the boundary.** If the regulation says "minimum 75%", does the test verify both 75.00% (pass) AND 74.99% (fail)?
3. **Check the citation.** Is the NMC regulation reference in the docstring correct?
4. **Check the assertion.** Is the test asserting the RIGHT thing? (Not just "no error" but "specific expected outcome")

### D.2 Tighten Weak Tests

Common patterns to fix:

**Weak:**
```python
def test_threshold():
    result = check_eligibility(student_id, course_id)
    assert result is not None  # This proves nothing
```

**Strong:**
```python
def test_att_nmc_001_exactly_75_percent_is_eligible():
    """ATT-NMC-001: 75.00% theory = ELIGIBLE. NMC CBME 2019 Reg 9.3(a)."""
    # Seed: 100 conducted sessions, 75 present
    result = check_eligibility(student_id, course_id)
    assert result.theory_eligible is True
    assert result.theory_pct == Decimal("75.00")

def test_att_nmc_002_below_75_percent_is_blocked():
    """ATT-NMC-002: 74.99% theory = BLOCKED. NMC CBME 2019 Reg 9.3(a)."""
    # Seed: 10000 conducted sessions, 7499 present (74.99%)
    result = check_eligibility(student_id, course_id)
    assert result.theory_eligible is False
    assert result.theory_pct == Decimal("74.99")
```

### D.3 Run Compliance Suite

```powershell
python -m pytest tests/compliance/ -v --tb=short 2>&1 | Tee-Object docs/verification/compliance_final_$(Get-Date -Format yyyyMMdd).txt
```

**Target: 100% passing. No exceptions. This is the hard-fail suite.**

If ANY compliance test fails, it is the highest priority fix in this session. Do not proceed to Phase E until compliance is green.

### D.4 Update COMPLIANCE_LOG.md

For every compliance test that passes, update the "Last Verified" column in `docs/COMPLIANCE_LOG.md` with today's date:

```markdown
| Test ID | ... | Last Verified | Status |
|---------|-----|---------------|--------|
| ATT-NMC-001 | ... | 2026-07-01 | Passing |
| ATT-NMC-002 | ... | 2026-07-01 | Passing |
| ... | ... | ... | ... |
```

---

## Phase E — Performance Baseline (30-45 min)

### E.1 Write Performance Tests

Create `tests/performance/test_phase2_baselines.py`:

```python
"""Phase 2 performance baselines. NOT part of CI — run manually."""
import time
import pytest
from uuid import uuid4


class TestAttendancePerformance:
    
    async def test_bulk_attendance_mark_100_students(self, test_db_session, seed_data):
        """
        Baseline: Mark 100 students present for 1 event.
        Target: < 500ms
        """
        event = seed_data.anatomy_events[0]
        students = [await create_student(test_db_session, seed_data.tenant, 
                                          seed_data.program, name=f"Perf Student {i}")
                    for i in range(100)]
        
        start = time.perf_counter()
        
        service = AttendanceService(test_db_session)
        for student in students:
            await service.mark_attendance(
                tenant_id=seed_data.tenant.id,
                user_id=seed_data.faculty[0].id,
                student_id=student.id,
                event_id=event.id,
                status="present",
                method="manual",
            )
        await test_db_session.flush()
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        print(f"Bulk attendance (100 students): {elapsed_ms:.0f}ms")
        assert elapsed_ms < 500, f"Too slow: {elapsed_ms:.0f}ms (target: <500ms)"


class TestElectivePerformance:
    
    async def test_ranked_allocation_100_students_10_electives(self, test_db_session, seed_data):
        """
        Baseline: Allocate 100 students across 10 electives (capacity 15 each).
        Target: < 2000ms
        """
        # Seed 100 students, 10 electives, random preferences
        # ...
        
        start = time.perf_counter()
        
        service = ElectiveService(test_db_session)
        result = await service.run_allocation(
            curriculum_id=seed_data.curriculum.id,
            block="Block 1",
            algorithm="ranked",
            dry_run=False,
        )
        await test_db_session.flush()
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        print(f"Ranked allocation (100 students, 10 electives): {elapsed_ms:.0f}ms")
        assert elapsed_ms < 2000, f"Too slow: {elapsed_ms:.0f}ms (target: <2000ms)"


class TestSummaryPerformance:
    
    async def test_attendance_summary_query(self, test_db_session, seed_data):
        """
        Baseline: Query attendance summary for 1 student across all courses.
        Target: < 100ms
        """
        # Seed attendance data for student across 5 courses, 50 events each
        # ...
        
        start = time.perf_counter()
        
        service = AttendanceService(test_db_session)
        result = await service.get_student_summary(
            tenant_id=seed_data.tenant.id,
            student_id=seed_data.students[0].id,
        )
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        print(f"Summary query: {elapsed_ms:.0f}ms")
        assert elapsed_ms < 100, f"Too slow: {elapsed_ms:.0f}ms (target: <100ms)"
```

### E.2 Run Performance Tests

```powershell
python -m pytest tests/performance/ -v -s 2>&1 | Tee-Object docs/verification/performance_baseline_$(Get-Date -Format yyyyMMdd).txt
```

The `-s` flag shows print output (timing numbers).

### E.3 Document in PERFORMANCE_LOG.md

```markdown
# Performance Baselines — Phase 2

**Date:** YYYY-MM-DD
**Environment:** Local dev (Windows, PostgreSQL 16 via Docker, 16GB RAM)

| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| Bulk attendance mark (100 students × 1 event) | < 500ms | NNNms | PASS/FAIL |
| Ranked elective allocation (100 students × 10 electives) | < 2000ms | NNNms | PASS/FAIL |
| Attendance summary query (1 student, all courses) | < 100ms | NNms | PASS/FAIL |
| IA marks calculation (1 student, 1 subject) | < 50ms | NNms | PASS/FAIL |
| DOAP state computation (1 student, 1 competency) | < 50ms | NNms | PASS/FAIL |

**Notes:**
- Local dev performance. Production (Cloud Run) will differ.
- These are baselines, not SLAs. Phase 3 will set production targets.
```

### E.4 Phase E Checkpoint

Performance tests are NOT hard-fail for Phase 2 completion. If a test exceeds the target:
- Document it in PERFORMANCE_LOG.md
- File as KNOWN-ISSUE in docs/KNOWN_ISSUES.md
- Phase 3 optimisation task

Do NOT block Phase 2 declaration on performance.

---

## Phase F — Phase 2 Declaration (30 min)

This is the final gate. Phase 2 is declared complete if and only if ALL of the following are true.

### F.1 Final Verifier Run

```powershell
python scripts/verify_adr_sequence.py
python scripts/verify_coverage_manifest.py
python scripts/verify_edge_case_coverage.py
python scripts/verify_compliance_coverage.py
python scripts/check_secrets.py
python scripts/verify_docs_updated.py
```

Capture ALL output:

```powershell
# Combined final verification
$timestamp = Get-Date -Format yyyyMMdd
python scripts/verify_adr_sequence.py 2>&1 | Tee-Object docs/verification/phase2_final_adr_$timestamp.txt
python scripts/verify_coverage_manifest.py 2>&1 | Tee-Object docs/verification/phase2_final_coverage_$timestamp.txt
python scripts/verify_edge_case_coverage.py 2>&1 | Tee-Object docs/verification/phase2_final_edge_$timestamp.txt
python scripts/verify_compliance_coverage.py 2>&1 | Tee-Object docs/verification/phase2_final_compliance_$timestamp.txt
```

### F.2 Final Test Run

```powershell
python -m pytest tests/ -v --tb=short -q 2>&1 | Tee-Object docs/verification/phase2_final_tests_$timestamp.txt
```

### F.3 Phase 2 Completion Checklist

Every box must be checked:

- [ ] **ADR sequence:** ADR-001 through ADR-037, no gaps
- [ ] **Coverage manifest:** 0 missing tests (all must-pass tests present, all deferred tests have `deferred_to:`)
- [ ] **Compliance tests:** 100% passing (hard-fail — no exceptions)
- [ ] **Unit tests:** ≥ 95% of non-deferred Phase 2 tests passing
- [ ] **Integration tests:** All 6 cross-module scenarios passing
- [ ] **Edge case coverage:** Every EC-* in EDGE_CASES.md has at least one test
- [ ] **Compliance coverage:** Every test ID in COMPLIANCE_TESTS.md exists in tests/compliance/
- [ ] **No orphan xfails:** Every remaining xfail has `deferred_to:` in manifest
- [ ] **No --no-verify commits:** Check git log for any --no-verify since Session 9
- [ ] **Performance baselines captured:** docs/PERFORMANCE_LOG.md populated
- [ ] **PHASE2_SCHEMA.md:** Up to date with all migrations 0011-0016
- [ ] **COMPLIANCE_LOG.md:** "Last Verified" dates updated for all Phase 2 tests
- [ ] **CHANGELOG.md:** Entry "Phase 2 complete"
- [ ] **All verifiers pass**

### F.4 Phase 2 Score Card

Create `docs/verification/phase2_scorecard.md`:

```markdown
# Phase 2 Completion Scorecard

**Date:** YYYY-MM-DD
**Sessions:** 6-14 (9 sessions over N weeks)
**Status:** COMPLETE

## Test Summary

| Category | Total | Passing | Deferred | Missing |
|----------|-------|---------|----------|---------|
| Attendance Engine | NN | NN | NN | 0 |
| Leave Management | NN | NN | NN | 0 |
| Electives | NN | NN | NN | 0 |
| DOAP Skills | NN | NN | NN | 0 |
| Digital Logbook | NN | NN | NN | 0 |
| Admissions | NN | NN | 0 | 0 |
| **Total** | **NNN** | **NN** | **NN** | **0** |

## Compliance Tests

| Test ID | Regulation | Status | Last Verified |
|---------|-----------|--------|---------------|
| ATT-NMC-001 | NMC CBME 2019 Reg 9.3(a) | PASS | YYYY-MM-DD |
| ... | ... | ... | ... |

All NN compliance tests passing. 0 failures. 0 deferred.

## Architecture Decision Records

ADR-001 through ADR-037. No gaps. All Accepted.

## Known Deferrals (Phase 2.5+)

| Test ID | Deferred To | Reason |
|---------|-------------|--------|
| ATT-004 | Phase 2.5 | RFID hardware integration |
| ATT-005 | Phase 3 | Face recognition ML model |
| ... | ... | ... |

Total deferred: NN tests across Phase 2.5 (NN), Phase 3 (NN), Phase 4 (NN).

## Performance Baselines

| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| Bulk attendance (100) | < 500ms | NNNms | PASS |
| ... | ... | ... | ... |

## Framework Health

- Coverage manifest: CLEAN (0 missing)
- ADR sequence: CLEAN (no gaps)
- Edge case coverage: CLEAN (all EC-* have tests)
- Compliance coverage: CLEAN (all declared = implemented = logged)
- Secret scan: CLEAN
- Doc freshness: CLEAN

## Phase 3 Handoff

Phase 3 scope includes:
- Examination Management module
- Report generation
- Full admission verification engine
- Performance optimisation (if baselines failed)
- Deferred test implementations (Phase 2.5 items)
```

### F.5 Update HANDOFF_NOTES for Phase 3

```markdown
## PHASE 2 COMPLETE (YYYY-MM-DD)

Phase 2 has been declared complete per the Phase 2 Completion Scorecard
(docs/verification/phase2_scorecard.md).

All must-pass tests passing. All compliance tests green.
All ADRs documented. All verifiers clean.

### Phase 3 Prerequisites

Before Phase 3 begins:
1. Review the Phase 2 scorecard with the human supervisor
2. Agree on Phase 3 scope (Examination Management is the primary module)
3. Create a Phase 3 master plan (follow the same R0→R5 structure)
4. Address any Phase 2.5 items that became blocking for Phase 3

### Technical Debt Carried Forward

[DEBT D7] Subject code inference uses hardcoded mapping. Must be MDM-driven.
[DEBT D8] IA config reads from MDM with fallback defaults. MDM seeding needed.
[DEBT D9] LOG-NMC-008 (elective 4-week duration) needs full integration test.
[DEBT D10] Elective preference UI not built (backend-only allocation).
[DEBT DNN] [Any other debt items accumulated during Sessions 6-14]

### Deferred to Phase 2.5

[List all deferred_to: "Phase 2.5" tests with their descriptions]

### Deferred to Phase 3+

[List all deferred_to: "Phase 3" and "Phase 4" tests]
```

### F.6 Final Commit

```powershell
git add .
git commit -m "milestone: Phase 2 Complete

All R4 modules implemented and tested:
- R4.1 Attendance Engine (Sessions 6-8, 12)
- R4.2 Leave Management (Sessions 7-8)
- R4.3 Electives (Session 9)
- R4.4 DOAP Skills (Session 10)
- R4.5 Logbook Phase 2 (Session 13)
- R4.6 Admission Placeholder (Session 13)

R5 verification complete:
- NN/NN must-pass tests passing
- NN/NN compliance tests passing (100%)
- 6 cross-module integration tests passing
- Performance baselines captured
- All verifiers clean
- ADR-001 through ADR-037, no gaps

Deferred to Phase 2.5/3/4: NN tests (documented in manifest with deferred_to)

Phase 2 Scorecard: docs/verification/phase2_scorecard.md

Refs: All Phase 2 ADRs (020-037)
"
```

Do NOT use `--no-verify`.

### F.7 Session End Declaration

```
SESSION END — Agent: 02-backend (Session 14 — Phase 2 Completion Sprint)
Duration: ~X hours

=== PHASE 2 STATUS: COMPLETE ===

Phase A: Progress gate — started at NN/86 passing
Phase B: xfail audit — converted NN, deferred NN, 0 orphan xfails remaining
Phase C: Cross-module integration — 6/6 scenarios passing
Phase D: Compliance tightening — NN/NN compliance tests passing (100%)
Phase E: Performance baselines — captured in PERFORMANCE_LOG.md
Phase F: Declaration — Phase 2 scorecard committed

Final score: NN/86 must-pass tests passing (target: 86/86)
Compliance: NN/NN passing (target: 100%)
Deferred: NN tests to Phase 2.5/3/4

Files modified: ~NN
Tests converted from xfail: NN
Tests added: NN
Commits: N
Pre-commit hook: passed (no --no-verify)

PHASE 2 IS COMPLETE. Phase 3 planning begins next session.
```

---

## If Phase 2 Cannot Complete in This Session

If after 6-8 hours, some tests still cannot pass, there are two acceptable outcomes:

### Outcome A: Nearly Complete (≤ 5 tests remaining)

- Document the remaining tests in HANDOFF_NOTES
- Create Session 15 as a short cleanup session (1-2 hours max)
- Phase 2 is declared complete at end of Session 15

### Outcome B: Significant Gap Remains (> 5 tests)

- Document what's blocking each group
- Classify: is this a code bug, a fixture problem, or a specification gap?
- Code bugs: Session 15 fixes them
- Fixture problems: Session 15 builds the fixtures
- Specification gaps: escalate to human supervisor — the test may need re-scoping
- Phase 2 declaration moves to end of Session 15

### What Is NOT Acceptable

- Declaring Phase 2 complete with failing must-pass tests
- Converting must-pass tests to deferred without human supervisor approval
- Using --no-verify to force the commit through
- Skipping the compliance suite
- Skipping the scorecard

The scorecard is the evidence that Phase 2 is real. Without it, "Phase 2 complete" is a statement, not a fact.

---

## Quick Reference: Phase Timing Guide

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| A: Progress gate | 15 min | Current state documented |
| B: xfail audit | 90-120 min | 0 orphan xfails |
| C: Integration tests | 60-90 min | 6 cross-module scenarios passing |
| D: Compliance tightening | 45-60 min | 100% compliance green |
| E: Performance baseline | 30-45 min | PERFORMANCE_LOG populated |
| F: Declaration | 30 min | Scorecard committed, Phase 2 declared |
| **Total** | **4.5-6 hours** | **Phase 2 complete** |

If running behind, the phases to compress are E (performance) and parts of C (integration). The phases that CANNOT be compressed are B (xfail audit — it takes what it takes) and D (compliance — must be 100%).

---

*This is the finish line. 14 sessions of disciplined framework work. Close it out.*