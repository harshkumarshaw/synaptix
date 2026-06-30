# Session 10 Plan — DOAP Skills + Session 9 Debt Cleanup

**Target Agent:** 02-backend (with 06-testing coordination)
**Estimated duration:** 4-6 hours of focused work
**Session structure:** Phase A (cleanup, 45-60 min) → Phase B (DOAP, main body) → Phase C (handoff, 15 min)

---

## Mandatory Session Start Protocol

Per AGENTS.md §2, declare your session start by reading these files and confirming:

1. `AGENTS.md` (root)
2. `docs/HANDOFF_NOTES.md` — pay special attention to the CRITICAL items at the top
3. `.agent-memory/working/CURRENT_FOCUS.md`
4. `agents/02-backend-agent.md` (your specialisation)
5. `.agent-memory/learning/02-backend.md`
6. `.agent-memory/incident/02-backend.md`
7. `docs/sessions/2026-MM-DD-session-9-*.md` — read Session 9 outputs thoroughly
8. `docs/DECISIONS.md` — specifically ADR-034 (Electives) and ADR-035 (DOAP State Machine)
9. `docs/INCIDENT_LOG.md` — read the `--no-verify` incident from Session 9

**Declaration format:**

```
SESSION START — Agent: 02-backend (Session 10)
Files read: AGENTS.md ✓, HANDOFF_NOTES ✓ (read CRITICAL items), CURRENT_FOCUS ✓, 
agent spec ✓, learning ✓, incidents ✓, Session 9 log ✓, ADR-034 ✓, ADR-035 ✓, 
INCIDENT_LOG ✓
Task understanding: Session 10 has 3 phases. Phase A resolves Session 9 debt. 
Phase B implements DOAP Skills. Phase C hands off to Session 11 (R0).
Approach: Strict sequential execution. Phase A must fully complete before Phase B starts.
If Phase A cannot complete in 60 min, session splits into 10A (cleanup) and 10B (DOAP).
```

---

## Phase A — Session 9 Debt Cleanup (45-60 minutes)

**Do not start Phase B until Phase A is 100% complete.** If any Phase A item cannot be resolved in the allotted time, STOP and report to human supervisor. Do not partially complete Phase B alongside incomplete Phase A.

### A.1 Verifier Investigation — Why `--no-verify` Was Needed

Session 9 used `git commit --no-verify` to bypass the pre-commit hook. This must be diagnosed before any new commits in Session 10.

**Steps:**

1. Run the coverage manifest verifier in isolation:

```powershell
cd F:\Synaptix
python scripts\verify_coverage_manifest.py 2>&1 | Tee-Object docs\verification\verifier_debug_session10.txt
```

2. Read the output carefully. Determine:
   - Does it list ELEC-001..009 as PRESENT or MISSING?
   - Does it list ELEC-NMC-001..004 as PRESENT or MISSING?
   - Does it list ELEC-E001..007 as PRESENT or MISSING?
   - Are there any other manifest entries it flags as MISSING?

3. Diagnose the root cause:

   **If ELEC tests show MISSING despite stubs existing:**
   - Check the test file: does it actually contain the test ID as a string somewhere (in docstring, comment, or function name)?
   - Check the verifier's regex pattern: does it match the format the agent used?
   - Run `grep -rn "ELEC-001" tests/` and confirm the ID is findable

   **If ELEC tests show PRESENT but other manifest items show MISSING:**
   - The bypass was for unrelated missing tests, not Session 9's additions
   - Document which OTHER tests are missing and why

   **If verifier crashes or errors out:**
   - The verifier itself has a bug
   - Document the error in `docs/INCIDENT_LOG.md`
   - Fix the verifier OR escalate to human supervisor

4. Document findings in `docs/INCIDENT_LOG.md` as an addendum to the original Session 9 incident:

```markdown
## INC-NNN-addendum: Session 9 --no-verify Bypass Root Cause

**Date:** YYYY-MM-DD
**Investigation by:** Agent 02-backend (Session 10 Phase A)
**Original incident:** Session 9 used --no-verify to commit electives work

**Root cause finding:** [one of:]
- Verifier bug: [describe]. Fix applied in commit XXXX.
- Test stub malformed: [which tests]. Fixed by [describe].
- Bypass was unnecessary: [other manifest items were the real issue]. Resolved by [describe].
- Other: [describe]

**Precedent reset:** --no-verify is NOT acceptable as standard practice. Future use 
requires investigation BEFORE bypass, with the diagnosis logged here.

**Verifier state after fix:** [run verifier output, paste here]
```

5. **Do not commit Phase A work using `--no-verify`.** If the hook blocks you again, diagnose again. The hook must work, or it's not a hook.

### A.2 Three Unverified Tests — Make At Least One Pass Each

Session 9 left three tests with ZERO passing verification:

- **ELEC-002** (`test_elec_002_submit_preferences_idempotent`) — unit xfail, integration xfail
- **ELEC-E001** (`test_elec_e001_preferences_replace_on_resubmit`) — unit xfail, integration xfail
- **ELEC-E007** (`test_elec_e007_wrong_block_elective_rejected`) — unit xfail, integration xfail

For each of these, you must make AT LEAST ONE test pass (unit OR integration, your choice).

**Recommended approach:** Use a real SQLite test database fixture rather than mocking. The recurring "mock execute result collisions" problem means the unit tests are trying to mock too many sequential queries. A real test database eliminates the mock complexity and provides better fidelity.

**Add fixture to `tests/conftest.py` if not present:**

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from packages.shared.db.base import Base

@pytest.fixture
async def test_db_session():
    """Real SQLite in-memory database for integration-style unit tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
    await engine.dispose()
```

**Then convert the three xfailed tests** to use the fixture:

```python
async def test_elec_002_submit_preferences_idempotent(test_db_session):
    """
    Test ID: ELEC-002
    Verifies: Submitting preferences twice produces same final state (full-block replace).
    """
    service = ElectiveService(session=test_db_session)
    
    # Setup: create elective, student, etc.
    # ... (seed data)
    
    # First submission
    await service.submit_preferences(
        student_id=student.id,
        block="Block 1",
        preferences=[{"elective_id": ea.id, "rank_position": 1}],
    )
    
    # Second submission with same data
    await service.submit_preferences(
        student_id=student.id,
        block="Block 1",
        preferences=[{"elective_id": ea.id, "rank_position": 1}],
    )
    
    # Assert: exactly one preference row exists
    result = await test_db_session.execute(
        select(StudentElectivePreference).where(
            StudentElectivePreference.student_id == student.id
        )
    )
    rows = result.scalars().all()
    assert len(rows) == 1
    
    # Remove the @pytest.mark.xfail marker on this test
```

Repeat for ELEC-E001 and ELEC-E007.

**Acceptance:** All three tests pass without xfail markers. Run:

```powershell
python -m pytest tests/unit/electives/test_elective_service.py -v -k "elec_002 or elec_e001 or elec_e007"
```

Expected: 3 passed, 0 xfailed, 0 failed.

### A.3 ADR-034 Worked Example Trace

ADR-034 specifies an exact worked example for the ranked allocation algorithm. You must verify the implementation produces the documented output.

**Setup the test scenario:**

- Curriculum: Phase III Part I, MBBS 2026 batch
- Block: Block 1
- Electives:
  - Elective A: capacity 4
  - Elective B: capacity 4
  - Elective C: capacity 4
- Students with preferences (per ADR-034 worked example):
  - S1: rank-1=A, rank-2=B (submitted 09:00:00)
  - S2: rank-1=A, rank-2=B (submitted 09:00:30)
  - S3: rank-1=A, rank-2=C (submitted 09:01:00)
  - S4: rank-1=A, rank-2=C (submitted 09:01:30)
  - S5: rank-1=A, rank-2=B (submitted 10:00:01)
  - S6: rank-1=B, rank-2=A (submitted 09:55:00)
  - S7: rank-1=B, rank-2=A (submitted 09:56:00)
  - S8: rank-1=B, rank-2=C (submitted 09:57:00)
  - S9: rank-1=C, rank-2=A (submitted 09:58:00)
  - S10: rank-1=C, rank-2=B (submitted 09:59:00)

**Run the algorithm in dry-run mode:**

Create `scripts/verify_adr_034_trace.py`:

```python
"""Manually trace ADR-034 worked example against current implementation."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from services.snx_logbook.app.services.elective_service import ElectiveService
# ... (full setup)

async def main():
    # Setup test DB, seed scenario
    # ... (seed data per ADR-034)
    
    # Run ranked allocation
    service = ElectiveService(session=session)
    result = await service.run_allocation(
        curriculum_id=curriculum.id,
        block="Block 1",
        algorithm="ranked",
        dry_run=True,
    )
    
    # Expected per ADR-034:
    expected = {
        "A": {"S1", "S2", "S3", "S4"},
        "B": {"S5", "S6", "S7", "S8"},
        "C": {"S9", "S10"},
    }
    
    # Compare
    actual = {}
    for allocation in result.allocations:
        elective_code = allocation.elective_code
        actual.setdefault(elective_code, set()).add(allocation.student_code)
    
    print("=== ADR-034 Worked Example Trace ===")
    for code in ["A", "B", "C"]:
        match = actual.get(code, set()) == expected[code]
        status = "PASS" if match else "FAIL"
        print(f"  {code}: expected {expected[code]}, got {actual.get(code, set())} [{status}]")
    
    total_allocated = sum(len(v) for v in actual.values())
    print(f"  Total allocated: {total_allocated} (expected 10)")
    print(f"  Unallocated pending review: {result.total_unallocated_pending_review} (expected 0)")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```powershell
python scripts\verify_adr_034_trace.py | Tee-Object docs\verification\adr_034_trace_$(Get-Date -Format yyyyMMdd).md
```

**Expected output:**

```
=== ADR-034 Worked Example Trace ===
  A: expected {S1, S2, S3, S4}, got {S1, S2, S3, S4} [PASS]
  B: expected {S5, S6, S7, S8}, got {S5, S6, S7, S8} [PASS]
  C: expected {S9, S10}, got {S9, S10} [PASS]
  Total allocated: 10 (expected 10)
  Unallocated pending review: 0 (expected 0)
```

**If the trace FAILS:**

- The allocation algorithm is wrong. Diagnose:
  - Are students being processed in submission-time order? (Should be rank-tier first, then submitted_at within tier.)
  - Is the capacity decrement happening atomically? (Should be inside the lock.)
  - Is rank-2 processing only considering still-unallocated students? (Should be.)
- Fix the algorithm. Re-run trace. Confirm PASS before proceeding.

**If the trace PASSES:**

- Commit `docs/verification/adr_034_trace_<date>.md` to git
- This is your acceptance evidence for ADR-034

### A.4 Apply Migration 0014

Session 9 created migration `20260630_0014_add_elective_allocation_runs.py` but did not apply it locally.

```powershell
cd F:\Synaptix
# Confirm current migration state
alembic current

# Apply pending migrations
alembic upgrade head

# Verify the new table exists
psql -U postgres -d synaptix_dev -c "\d elective_allocation_runs"
```

Expected: table description shown with columns.

**If migration fails:**

- Read the error carefully
- Common issues: missing FK target (`elective_allocations` may need composite unique constraint), syntax errors, type mismatches
- Fix the migration file (do NOT edit in-place if it was already committed — create a follow-up migration)

**If migration succeeds:**

- Update `docs/MIGRATION_LOG.md`:

```markdown
## Migration 0014: add_elective_allocation_runs

**Applied:** YYYY-MM-DD HH:MM
**Applied by:** Session 10 Agent 02-backend
**Database:** synaptix_dev (local)
**Status:** Success

**Changes:**
- Added table: elective_allocation_runs
- Added FK: elective_allocations.allocation_run_id → elective_allocation_runs(id)
- Added column: student_elective_preferences.submitted_at

**Rollback:**
```sql
ALTER TABLE elective_allocations DROP CONSTRAINT fk_alloc_run;
ALTER TABLE elective_allocations DROP COLUMN allocation_run_id;
ALTER TABLE student_elective_preferences DROP COLUMN submitted_at;
DROP TABLE elective_allocation_runs;
```

**Verification:**
- elective_allocation_runs visible in `\dt`
- New columns visible in `\d elective_allocations` and `\d student_elective_preferences`
- Existing data intact (verified by re-running existing integration tests)
```

### A.5 Phase A Acceptance Gate

Before starting Phase B, confirm ALL of the following:

- [ ] Verifier debug output captured; `--no-verify` root cause documented in INCIDENT_LOG
- [ ] ELEC-002, ELEC-E001, ELEC-E007 each have at least one passing test (no xfail)
- [ ] ADR-034 worked example trace runs and PASSES
- [ ] Migration 0014 applied locally; verified in psql
- [ ] Commit Phase A work using REAL pre-commit hook (no `--no-verify`)
- [ ] `docs/CHANGELOG.md` updated
- [ ] `docs/sessions/2026-MM-DD-session-10.md` started

**If any item is incomplete:** STOP. Report status to human supervisor. Do not proceed to Phase B.

**If all items complete:** Take a 5-minute break, then proceed to Phase B.

---

## Phase B — DOAP Skills Implementation (Main Body)

DOAP (Demonstration → Observation → Assistance → Performance) is the NMC-mandated competency progression framework for procedural skills. The schema (`doap_session_records`) was created in Phase 2 migrations; this session implements the service code, validation, and routes.

### B.1 Pre-Implementation: Confirm ADR-035 Understanding

Before writing any DOAP code, **re-read ADR-035 in full**. Then write a brief understanding check in your session log:

```markdown
## ADR-035 Understanding Confirmation

State machine:
- NOT_STARTED → DEMONSTRATED → OBSERVED → ASSISTED → PERFORMED → CERTIFIED
- Stage progression requires C-decision at previous stage
- Backward attempts allowed (refresher D after reaching O) — these are additional records, not state regression
- Multiple sessions per stage allowed (a single C-decision certifies the stage)

Faculty decision codes:
- C = Certify (student demonstrated competency at this stage; can progress)
- R = Repeat (student must repeat this stage)
- Re = Remediate (student requires structured remediation before next attempt)

Attempt types:
- F = First attempt
- R = Repeat after R decision
- Re = Attempt after remediation programme

Rating-decision consistency:
- Rating B (Below) → decision must be R or Re (NOT C)
- Rating M (Meets) → decision typically C
- Rating E (Exceeds) → decision C with distinction note

Cross-module integration:
- Every DOAP record auto-creates a logbook_entries row
- Re decision auto-creates a remediation workflow_instance
- Evidence stored via evidence_asset_ids JSONB → digital_assets
- DOAP sessions are also attendance events (category: clinical or practical)
```

If you cannot articulate this in your own words from memory, re-read ADR-035 again before coding.

### B.2 COVERAGE_MANIFEST Entries for DOAP

Before writing any service code, add DOAP entries to `tests/COVERAGE_MANIFEST.yaml`:

```yaml
doap_skills:
  module_id: A-09
  test_file_prefix: "tests/unit/doap/"
  enforcement: standard
  
  critical_tests:
    - id: DOAP-001
      description: "Record D stage with C decision creates record and logbook entry"
      type: unit
    - id: DOAP-002
      description: "Record O stage requires preceding D certified (rejection if not)"
      type: unit
    - id: DOAP-003
      description: "Record A stage requires preceding O certified"
      type: unit
    - id: DOAP-004
      description: "Record P stage requires preceding A certified"
      type: unit
    - id: DOAP-005
      description: "Re-attempt after R decision (attempt_type=R, same stage)"
      type: unit
    - id: DOAP-006
      description: "Remediation workflow auto-created on Re decision"
      type: integration
    - id: DOAP-007
      description: "Evidence asset IDs linked correctly"
      type: integration
    - id: DOAP-008
      description: "Auto-creation of logbook_entries on every DOAP record"
      type: integration
  
  compliance_tests:
    - id: DOAP-NMC-001
      description: "Stage progression D→O→A→P enforced (no skipping)"
      type: compliance
      regulation_ref: "NMC CBME 2019 DOAP framework"
    - id: DOAP-NMC-002
      description: "Faculty decision required for every record (cannot be null)"
      type: compliance
      regulation_ref: "NMC CBME 2019 Reg 8.3"
    - id: DOAP-NMC-003
      description: "Rating B implies decision R or Re (cannot be C)"
      type: compliance
      regulation_ref: "NMC CBME 2019 Reg 8.4"
  
  edge_cases:
    - id: DOAP-E001
      description: "Backward stage record (refresher D after reaching O) — allowed"
      type: edge_case
    - id: DOAP-E002
      description: "Faculty decision Re with no active remediation programme — handle gracefully"
      type: edge_case
    - id: DOAP-E003
      description: "Stage skip attempt (P without prior A) — must reject with specific error"
      type: edge_case
```

Total: 14 new test IDs.

### B.3 Test Stubs (Before Service Code)

Create the test stub files. Every test marked `@pytest.mark.xfail(reason="DOAP-NNN: Implementation pending in Session 10")` initially. As you implement each service method, REMOVE the xfail marker on the corresponding test.

**Files to create:**

- `tests/unit/doap/__init__.py` (empty)
- `tests/unit/doap/test_state_machine.py` — DOAP-002, DOAP-003, DOAP-004, DOAP-E003
- `tests/unit/doap/test_records.py` — DOAP-001, DOAP-005, DOAP-E001
- `tests/unit/doap/test_rating_decision.py` — DOAP-NMC-003
- `tests/integration/doap/__init__.py` (empty)
- `tests/integration/doap/test_workflows.py` — DOAP-006, DOAP-007, DOAP-008, DOAP-E002
- `tests/compliance/doap/__init__.py` (empty)
- `tests/compliance/doap/test_nmc_compliance.py` — DOAP-NMC-001, DOAP-NMC-002

**Stub template:**

```python
# tests/unit/doap/test_state_machine.py
import pytest
from uuid import uuid4

class TestDoapStateMachine:
    """Tests for DOAP stage progression rules per ADR-035."""

    @pytest.mark.xfail(reason="DOAP-002: Implementation pending in Session 10")
    async def test_doap_002_o_stage_requires_d_certified(self, test_db_session):
        """
        Test ID: DOAP-002
        Verifies: Cannot record O stage record before D stage has at least one 
        C-decision record.
        Expected error: DOAP-001 with message "Cannot attempt O before D is certified"
        """
        raise NotImplementedError("Stub")
    
    @pytest.mark.xfail(reason="DOAP-003: Implementation pending in Session 10")
    async def test_doap_003_a_stage_requires_o_certified(self, test_db_session):
        """Test ID: DOAP-003"""
        raise NotImplementedError("Stub")
    
    @pytest.mark.xfail(reason="DOAP-004: Implementation pending in Session 10")
    async def test_doap_004_p_stage_requires_a_certified(self, test_db_session):
        """Test ID: DOAP-004"""
        raise NotImplementedError("Stub")
    
    @pytest.mark.xfail(reason="DOAP-E003: Implementation pending in Session 10")
    async def test_doap_e003_stage_skip_rejected(self, test_db_session):
        """
        Test ID: DOAP-E003
        Verifies: Attempting to record P stage when only D exists (skipping O and A)
        returns specific error code DOAP-001 with the missing stages listed.
        """
        raise NotImplementedError("Stub")
```

Run the verifier to confirm all 14 IDs are PRESENT:

```powershell
python scripts\verify_coverage_manifest.py
```

Expected: doap_skills section shows all 14 tests as PRESENT (xfail counts as PRESENT).

### B.4 Pydantic Schemas

**Create `services/snx-logbook/app/schemas/doap.py`:**

```python
"""Pydantic v2 schemas for DOAP module."""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DoapStage(str, Enum):
    D = "D"  # Demonstration
    O = "O"  # Observation
    A = "A"  # Assistance
    P = "P"  # Performance


class DoapRating(str, Enum):
    B = "B"  # Below expectation
    M = "M"  # Meets expectation
    E = "E"  # Exceeds expectation


class DoapAttemptType(str, Enum):
    F = "F"   # First
    R = "R"   # Repeat after R decision
    Re = "Re" # Remediation


class DoapFacultyDecision(str, Enum):
    C = "C"   # Certify
    R = "R"   # Repeat
    Re = "Re" # Remediate


class DoapState(str, Enum):
    NOT_STARTED = "not_started"
    DEMONSTRATED = "demonstrated"
    OBSERVED = "observed"
    ASSISTED = "assisted"
    PERFORMED = "performed"
    CERTIFIED = "certified"


class DoapSessionCreate(BaseModel):
    """Request to create a DOAP session record."""
    model_config = ConfigDict(use_enum_values=True)
    
    student_id: UUID
    session_id: UUID
    competency_code: str = Field(min_length=2, max_length=50)
    nmc_level: str = Field(pattern="^(K|KH|SH|P)$")
    is_core: bool = False
    stage: DoapStage
    rating: DoapRating
    attempt_type: DoapAttemptType
    faculty_decision: DoapFacultyDecision
    faculty_id: UUID
    evidence_asset_ids: list[UUID] = Field(default_factory=list)
    notes: Optional[str] = Field(default=None, max_length=2000)
    
    @model_validator(mode="after")
    def validate_rating_decision_consistency(self) -> "DoapSessionCreate":
        """Rating B implies decision R or Re (cannot be C). DOAP-NMC-003."""
        if self.rating == DoapRating.B.value and self.faculty_decision == DoapFacultyDecision.C.value:
            raise ValueError(
                "DOAP-002: Rating B (Below expectation) cannot have faculty_decision C (Certify). "
                "Use R (Repeat) or Re (Remediate)."
            )
        return self


class DoapSessionResponse(BaseModel):
    """DOAP session record response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    student_id: UUID
    session_id: UUID
    competency_code: str
    nmc_level: str
    is_core: bool
    stage: str
    rating: str
    attempt_type: str
    faculty_decision: str
    faculty_id: UUID
    evidence_asset_ids: list[UUID]
    notes: Optional[str]
    signed_off_at: datetime
    created_at: datetime


class DoapStateResponse(BaseModel):
    """Current DOAP state per competency for a student."""
    model_config = ConfigDict(from_attributes=True)
    
    student_id: UUID
    competency_code: str
    current_state: DoapState
    records_per_stage: dict[str, int]  # e.g. {"D": 2, "O": 1, "A": 0, "P": 0}
    certified_stages: list[str]
    pending_stage: Optional[str]
    last_record_at: Optional[datetime]


class DoapProgressionResponse(BaseModel):
    """Full progression history for a student + competency."""
    student_id: UUID
    competency_code: str
    state: DoapStateResponse
    records: list[DoapSessionResponse]
```

### B.5 Validator Module

**Create `services/snx-logbook/app/services/doap_validators.py`:**

This is the heart of the state machine. Pure functions with no DB access for unit-testability.

```python
"""DOAP state machine validators (pure functions, no DB)."""
from typing import Literal
from dataclasses import dataclass


STAGE_ORDER = ["D", "O", "A", "P"]


@dataclass
class ValidationResult:
    is_valid: bool
    error_code: str | None = None
    error_message: str | None = None
    
    @classmethod
    def ok(cls) -> "ValidationResult":
        return cls(is_valid=True)
    
    @classmethod
    def error(cls, code: str, message: str) -> "ValidationResult":
        return cls(is_valid=False, error_code=code, error_message=message)


def validate_stage_progression(
    proposed_stage: str,
    certified_stages: set[str],
    attempt_type: str,
) -> ValidationResult:
    """
    Validate that the proposed stage can be attempted.
    
    Rules per ADR-035:
    - Stage progression requires ALL prior stages to be certified
    - Backward attempts allowed (e.g., refresher D after reaching O is fine)
    - First attempt at a new stage requires prior stage certified
    
    Args:
        proposed_stage: The stage being recorded (D, O, A, P)
        certified_stages: Set of stages where student has at least one C-decision record
        attempt_type: F, R, or Re
    
    Returns:
        ValidationResult.ok() or ValidationResult.error(...)
    """
    if proposed_stage not in STAGE_ORDER:
        return ValidationResult.error("DOAP-100", f"Invalid stage: {proposed_stage}")
    
    proposed_idx = STAGE_ORDER.index(proposed_stage)
    
    # Backward attempts: always allowed (refresher demonstration etc.)
    if proposed_idx == 0:  # D stage
        return ValidationResult.ok()
    
    # Re-attempts (R, Re attempt types) at a stage already attempted: allowed
    if proposed_stage in certified_stages and attempt_type in ("R", "Re"):
        return ValidationResult.ok()
    
    # Forward progression: all prior stages must be certified
    prior_stages = set(STAGE_ORDER[:proposed_idx])
    missing_prior = prior_stages - certified_stages
    
    if missing_prior:
        missing_sorted = [s for s in STAGE_ORDER if s in missing_prior]
        return ValidationResult.error(
            "DOAP-001",
            f"Cannot attempt {proposed_stage} stage before {', '.join(missing_sorted)} "
            f"{'is' if len(missing_sorted) == 1 else 'are'} certified."
        )
    
    return ValidationResult.ok()


def validate_rating_decision(rating: str, decision: str) -> ValidationResult:
    """
    Validate rating-decision consistency.
    
    Rule per ADR-035:
    - Rating B (Below) → decision must be R or Re (NOT C)
    - Rating M (Meets) → typically C (allowed: any)
    - Rating E (Exceeds) → typically C (allowed: any)
    
    DOAP-NMC-003 compliance.
    """
    if rating == "B" and decision == "C":
        return ValidationResult.error(
            "DOAP-002",
            "Rating B (Below expectation) cannot have decision C (Certify). "
            "Use R (Repeat) or Re (Remediate)."
        )
    return ValidationResult.ok()


def compute_certified_stages(records: list) -> set[str]:
    """
    Given a list of DoapSessionRecord ORM objects (or dict-like), return the set of 
    stages where the student has at least one C-decision record.
    """
    certified = set()
    for record in records:
        # Support both ORM and dict access
        stage = getattr(record, "stage", None) or record.get("stage")
        decision = getattr(record, "faculty_decision", None) or record.get("faculty_decision")
        if decision == "C":
            certified.add(stage)
    return certified


def derive_current_state(certified_stages: set[str]) -> str:
    """Map certified stages to the current DOAP state per ADR-035."""
    if "P" in certified_stages:
        return "certified"
    elif "A" in certified_stages:
        return "performed"  # waiting for P certification
    elif "O" in certified_stages:
        return "assisted"
    elif "D" in certified_stages:
        return "observed"
    elif certified_stages:
        return "demonstrated"  # some certified, but D not yet (shouldn't happen but safe)
    else:
        return "not_started"
```

**Now you can write the test for DOAP-002, DOAP-003, DOAP-004, DOAP-E003 immediately** (they test the validator in isolation, no DB needed). Remove xfail markers as you write each:

```python
# tests/unit/doap/test_state_machine.py
import pytest
from services.snx_logbook.app.services.doap_validators import (
    validate_stage_progression,
    validate_rating_decision,
)


class TestStageProgression:
    
    def test_doap_002_o_stage_requires_d_certified(self):
        """DOAP-002: O without D certified should be rejected."""
        result = validate_stage_progression(
            proposed_stage="O",
            certified_stages=set(),  # nothing certified
            attempt_type="F",
        )
        assert not result.is_valid
        assert result.error_code == "DOAP-001"
        assert "D" in result.error_message
    
    def test_doap_002_o_stage_allowed_if_d_certified(self):
        """DOAP-002 positive case: O allowed when D certified."""
        result = validate_stage_progression(
            proposed_stage="O",
            certified_stages={"D"},
            attempt_type="F",
        )
        assert result.is_valid
    
    def test_doap_003_a_stage_requires_o_certified(self):
        """DOAP-003: A without O certified should be rejected."""
        result = validate_stage_progression(
            proposed_stage="A",
            certified_stages={"D"},  # only D certified, not O
            attempt_type="F",
        )
        assert not result.is_valid
        assert "O" in result.error_message
    
    def test_doap_004_p_stage_requires_a_certified(self):
        """DOAP-004: P without A certified should be rejected."""
        result = validate_stage_progression(
            proposed_stage="P",
            certified_stages={"D", "O"},  # missing A
            attempt_type="F",
        )
        assert not result.is_valid
        assert "A" in result.error_message
    
    def test_doap_e003_stage_skip_lists_all_missing(self):
        """DOAP-E003: Attempting P with only D certified lists O and A as missing."""
        result = validate_stage_progression(
            proposed_stage="P",
            certified_stages={"D"},
            attempt_type="F",
        )
        assert not result.is_valid
        assert "O" in result.error_message
        assert "A" in result.error_message
    
    def test_doap_e001_backward_d_refresher_allowed(self):
        """DOAP-E001: Recording D again after reaching O is allowed (refresher)."""
        result = validate_stage_progression(
            proposed_stage="D",
            certified_stages={"D", "O"},
            attempt_type="F",
        )
        assert result.is_valid


class TestRatingDecisionConsistency:
    
    def test_doap_nmc_003_rating_b_decision_c_rejected(self):
        """DOAP-NMC-003: B + C combination must be rejected."""
        result = validate_rating_decision(rating="B", decision="C")
        assert not result.is_valid
        assert result.error_code == "DOAP-002"
    
    def test_doap_nmc_003_rating_b_decision_r_allowed(self):
        """DOAP-NMC-003: B + R is valid."""
        result = validate_rating_decision(rating="B", decision="R")
        assert result.is_valid
    
    def test_doap_nmc_003_rating_m_decision_c_allowed(self):
        """DOAP-NMC-003: M + C is the typical case."""
        result = validate_rating_decision(rating="M", decision="C")
        assert result.is_valid
```

Run these tests:

```powershell
python -m pytest tests/unit/doap/test_state_machine.py -v
```

Expected: 9 tests, all passing. No xfails.

### B.6 Service Layer Extension

**Modify `services/snx-logbook/app/services/logbook_service.py`** OR create new `services/snx-logbook/app/services/doap_service.py` (preferred — keeps DOAP logic separate).

```python
"""DOAP Skills service."""
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.shared.audit import write_audit_log
from packages.shared.db.models import (
    DoapSessionRecord,
    LogbookEntry,
    WorkflowInstance,
)
from .doap_validators import (
    validate_stage_progression,
    validate_rating_decision,
    compute_certified_stages,
    derive_current_state,
    ValidationResult,
)
from ..schemas.doap import (
    DoapSessionCreate,
    DoapSessionResponse,
    DoapStateResponse,
)


class DoapServiceError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class DoapService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def submit_doap_session(
        self,
        tenant_id: UUID,
        user_id: UUID,
        data: DoapSessionCreate,
    ) -> DoapSessionResponse:
        """
        Create a DOAP session record after validating state machine rules.
        Auto-creates corresponding logbook_entry. Triggers remediation workflow on Re.
        """
        # Step 1: Fetch existing records for this student + competency
        existing = await self.session.execute(
            select(DoapSessionRecord).where(
                DoapSessionRecord.tenant_id == tenant_id,
                DoapSessionRecord.student_id == data.student_id,
                DoapSessionRecord.competency_code == data.competency_code,
                DoapSessionRecord.deleted_at.is_(None),
            )
        )
        existing_records = existing.scalars().all()
        certified_stages = compute_certified_stages(existing_records)
        
        # Step 2: Validate stage progression
        progression_result = validate_stage_progression(
            proposed_stage=data.stage,
            certified_stages=certified_stages,
            attempt_type=data.attempt_type,
        )
        if not progression_result.is_valid:
            raise DoapServiceError(
                progression_result.error_code,
                progression_result.error_message,
            )
        
        # Step 3: Validate rating-decision consistency
        rating_result = validate_rating_decision(data.rating, data.faculty_decision)
        if not rating_result.is_valid:
            raise DoapServiceError(
                rating_result.error_code,
                rating_result.error_message,
            )
        
        # Step 4: Insert DOAP record
        new_record = DoapSessionRecord(
            id=uuid4(),
            tenant_id=tenant_id,
            student_id=data.student_id,
            session_id=data.session_id,
            competency_code=data.competency_code,
            nmc_level=data.nmc_level,
            is_core=data.is_core,
            stage=data.stage,
            rating=data.rating,
            attempt_type=data.attempt_type,
            faculty_decision=data.faculty_decision,
            faculty_id=data.faculty_id,
            evidence_asset_ids=[str(uid) for uid in data.evidence_asset_ids],
            notes=data.notes,
            signed_off_at=datetime.now(timezone.utc),
            created_by=user_id,
        )
        self.session.add(new_record)
        await self.session.flush()  # Get ID before audit log
        
        # Step 5: Auto-create logbook entry (DOAP-008)
        logbook_entry = LogbookEntry(
            id=uuid4(),
            tenant_id=tenant_id,
            student_id=data.student_id,
            elective_id=None,
            subject_code=self._infer_subject_code(data.competency_code),
            competency_code=data.competency_code,
            nmc_level=data.nmc_level,
            is_core=data.is_core,
            activity_date=datetime.now(timezone.utc).date(),
            activity_name=f"DOAP {data.stage} record for {data.competency_code}",
            rating=data.rating,
            attempt_type=data.attempt_type,
            faculty_decision=data.faculty_decision,
            status="approved" if data.faculty_decision == "C" else "pending",
            signed_off_by=data.faculty_id,
            signed_off_at=datetime.now(timezone.utc),
            created_by=user_id,
        )
        self.session.add(logbook_entry)
        
        # Step 6: Trigger remediation workflow if Re decision (DOAP-006)
        if data.faculty_decision == "Re":
            workflow = WorkflowInstance(
                id=uuid4(),
                tenant_id=tenant_id,
                workflow_definition_code="doap_remediation",
                entity_type="doap_session_record",
                entity_id=new_record.id,
                status="initiated",
                initiated_by=user_id,
                initiated_at=datetime.now(timezone.utc),
            )
            self.session.add(workflow)
        
        # Step 7: Audit log
        await write_audit_log(
            self.session,
            tenant_id=tenant_id,
            user_id=user_id,
            action="submit_doap_session",
            entity_type="doap_session_record",
            entity_id=new_record.id,
            details={
                "competency_code": data.competency_code,
                "stage": data.stage,
                "rating": data.rating,
                "faculty_decision": data.faculty_decision,
                "auto_logbook_entry_id": str(logbook_entry.id),
                "remediation_triggered": data.faculty_decision == "Re",
            },
        )
        
        await self.session.flush()
        return DoapSessionResponse.model_validate(new_record)
    
    async def get_doap_records(
        self,
        tenant_id: UUID,
        student_id: UUID,
        competency_code: str | None = None,
    ) -> list[DoapSessionResponse]:
        """List DOAP records for a student, optionally filtered by competency."""
        query = select(DoapSessionRecord).where(
            DoapSessionRecord.tenant_id == tenant_id,
            DoapSessionRecord.student_id == student_id,
            DoapSessionRecord.deleted_at.is_(None),
        )
        if competency_code:
            query = query.where(DoapSessionRecord.competency_code == competency_code)
        query = query.order_by(DoapSessionRecord.signed_off_at)
        
        result = await self.session.execute(query)
        records = result.scalars().all()
        return [DoapSessionResponse.model_validate(r) for r in records]
    
    async def compute_state(
        self,
        tenant_id: UUID,
        student_id: UUID,
        competency_code: str,
    ) -> DoapStateResponse:
        """Compute current DOAP state for a student + competency."""
        records = await self.get_doap_records(tenant_id, student_id, competency_code)
        certified = compute_certified_stages(records)
        current = derive_current_state(certified)
        
        # Count records per stage
        records_per_stage = {"D": 0, "O": 0, "A": 0, "P": 0}
        for r in records:
            records_per_stage[r.stage] = records_per_stage.get(r.stage, 0) + 1
        
        # Determine pending stage
        STAGE_ORDER = ["D", "O", "A", "P"]
        pending = None
        for s in STAGE_ORDER:
            if s not in certified:
                pending = s
                break
        
        return DoapStateResponse(
            student_id=student_id,
            competency_code=competency_code,
            current_state=current,
            records_per_stage=records_per_stage,
            certified_stages=sorted(certified, key=STAGE_ORDER.index),
            pending_stage=pending,
            last_record_at=records[-1].signed_off_at if records else None,
        )
    
    def _infer_subject_code(self, competency_code: str) -> str:
        """Extract subject prefix from competency_code (e.g., AN1.1 → ANAT)."""
        # Mapping table: AN=ANAT, PY=PHYS, BI=BIOC, MI=MICR, PA=PATH, PH=PHAR, FM=FMED, CM=CMED, etc.
        prefix = "".join(c for c in competency_code[:2] if c.isalpha()).upper()
        subject_map = {
            "AN": "ANAT", "PY": "PHYS", "BI": "BIOC", "MI": "MICR",
            "PA": "PATH", "PH": "PHAR", "FM": "FMED", "CM": "CMED",
            "GM": "GMED", "GS": "GSUR", "OG": "OBGY", "PE": "PEDI",
            "OR": "ORTH", "OP": "OPHT", "EN": "ENT",  "DE": "DERM",
            "PS": "PSYC", "RD": "RADI", "AN": "ANES",
        }
        return subject_map.get(prefix, "UNKN")
```

As you implement each method, run the corresponding tests and remove xfail markers.

### B.7 API Router

**Create `services/snx-logbook/app/routers/doap.py`:**

```python
"""DOAP Skills API endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from packages.shared.auth import require_role, current_user, User
from packages.shared.db.session import get_session
from ..schemas.doap import (
    DoapSessionCreate,
    DoapSessionResponse,
    DoapStateResponse,
)
from ..services.doap_service import DoapService, DoapServiceError


router = APIRouter(prefix="/doap", tags=["doap"])


@router.post("/records", response_model=DoapSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_doap_record(
    data: DoapSessionCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_role(["faculty", "hod", "admin"])),
):
    """
    Faculty creates a DOAP session record. 
    Auto-creates logbook entry. Triggers remediation workflow on Re decision.
    """
    service = DoapService(session)
    try:
        result = await service.submit_doap_session(
            tenant_id=user.tenant_id,
            user_id=user.id,
            data=data,
        )
        await session.commit()
        return result
    except DoapServiceError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error_code": e.code, "message": e.message},
        )


@router.get("/student/{student_id}", response_model=list[DoapSessionResponse])
async def get_student_doap_records(
    student_id: UUID,
    competency_code: str | None = None,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user),
):
    """List all DOAP records for a student, optionally filtered by competency."""
    # Authorization: student can view own; faculty/admin can view any in tenant
    if user.role == "student" and user.student_id != student_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Cannot view other students")
    
    service = DoapService(session)
    return await service.get_doap_records(user.tenant_id, student_id, competency_code)


@router.get(
    "/student/{student_id}/competency/{competency_code}/state",
    response_model=DoapStateResponse,
)
async def get_doap_state(
    student_id: UUID,
    competency_code: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user),
):
    """Compute current DOAP state for student + competency."""
    if user.role == "student" and user.student_id != student_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    
    service = DoapService(session)
    return await service.compute_state(user.tenant_id, student_id, competency_code)
```

### B.8 Register Router

**Modify `services/snx-logbook/app/main.py`:**

```python
from .routers import (
    foundation_course,
    aetcom,
    electives,    # registered in Session 9
    doap,         # NEW
)

app.include_router(foundation_course.router)
app.include_router(aetcom.router)
app.include_router(electives.router)
app.include_router(doap.router)  # NEW
```

### B.9 Integration Tests

Now write the integration tests that exercise the full flow. These cover DOAP-001, DOAP-005, DOAP-006, DOAP-007, DOAP-008, DOAP-E001, DOAP-E002.

```python
# tests/integration/doap/test_workflows.py
import pytest
from uuid import uuid4

from services.snx_logbook.app.services.doap_service import DoapService
from services.snx_logbook.app.schemas.doap import DoapSessionCreate


class TestDoapWorkflows:
    
    async def test_doap_001_d_stage_creates_record_and_logbook(
        self, test_db_session, sample_tenant, sample_student, sample_session, sample_faculty
    ):
        """DOAP-001: Recording D stage creates DOAP record AND logbook entry."""
        service = DoapService(test_db_session)
        result = await service.submit_doap_session(
            tenant_id=sample_tenant.id,
            user_id=sample_faculty.id,
            data=DoapSessionCreate(
                student_id=sample_student.id,
                session_id=sample_session.id,
                competency_code="AN1.1",
                nmc_level="P",
                is_core=True,
                stage="D",
                rating="M",
                attempt_type="F",
                faculty_decision="C",
                faculty_id=sample_faculty.id,
            ),
        )
        assert result.stage == "D"
        # Verify logbook entry was created
        # ... (query logbook_entries table)
    
    async def test_doap_005_repeat_attempt_after_r_decision(
        self, test_db_session, sample_tenant, sample_student, sample_session, sample_faculty
    ):
        """DOAP-005: After R decision, student can re-attempt with attempt_type=R."""
        service = DoapService(test_db_session)
        
        # First attempt: R decision (rating M but faculty wants repeat)
        await service.submit_doap_session(
            tenant_id=sample_tenant.id,
            user_id=sample_faculty.id,
            data=DoapSessionCreate(
                student_id=sample_student.id,
                session_id=sample_session.id,
                competency_code="AN1.1",
                nmc_level="P",
                is_core=True,
                stage="D",
                rating="M",
                attempt_type="F",
                faculty_decision="R",  # Repeat decision
                faculty_id=sample_faculty.id,
            ),
        )
        
        # Re-attempt with attempt_type=R
        result = await service.submit_doap_session(
            tenant_id=sample_tenant.id,
            user_id=sample_faculty.id,
            data=DoapSessionCreate(
                student_id=sample_student.id,
                session_id=sample_session.id,
                competency_code="AN1.1",
                nmc_level="P",
                is_core=True,
                stage="D",
                rating="M",
                attempt_type="R",  # Repeat attempt
                faculty_decision="C",  # Now certified
                faculty_id=sample_faculty.id,
            ),
        )
        assert result.attempt_type == "R"
        assert result.faculty_decision == "C"
    
    async def test_doap_006_remediation_workflow_triggered_on_re(
        self, test_db_session, sample_tenant, sample_student, sample_session, sample_faculty
    ):
        """DOAP-006: Re decision triggers remediation workflow_instance."""
        service = DoapService(test_db_session)
        await service.submit_doap_session(
            tenant_id=sample_tenant.id,
            user_id=sample_faculty.id,
            data=DoapSessionCreate(
                student_id=sample_student.id,
                session_id=sample_session.id,
                competency_code="AN1.1",
                nmc_level="P",
                is_core=True,
                stage="D",
                rating="B",
                attempt_type="F",
                faculty_decision="Re",  # Remediation triggered
                faculty_id=sample_faculty.id,
            ),
        )
        # Verify workflow_instance exists
        # ... (query workflow_instances)
    
    # ... continue for DOAP-007, DOAP-008, DOAP-E001, DOAP-E002
```

### B.10 Compliance Tests

**`tests/compliance/doap/test_nmc_compliance.py`:**

```python
"""DOAP NMC compliance tests. HARD-FAIL: any failure blocks all commits."""
import pytest
from services.snx_logbook.app.services.doap_validators import (
    validate_stage_progression,
    validate_rating_decision,
)


class TestDoapNmcCompliance:
    """
    NMC CBME 2019 DOAP Framework compliance.
    Reference: NMC CBME 2019 Reg 8.3, 8.4
    """
    
    def test_doap_nmc_001_stage_progression_d_o_a_p_enforced(self):
        """
        DOAP-NMC-001: Stage progression D→O→A→P enforced (no skipping).
        Regulation: NMC CBME 2019 DOAP framework
        """
        # Try every possible skip combination, all must be rejected
        skip_attempts = [
            ("O", set()),           # O without D
            ("A", set()),           # A without anything
            ("A", {"D"}),           # A without O
            ("P", set()),           # P without anything
            ("P", {"D"}),           # P without O, A
            ("P", {"O"}),           # P without D, A (impossible but tested for completeness)
            ("P", {"D", "O"}),      # P without A
        ]
        for proposed_stage, certified in skip_attempts:
            result = validate_stage_progression(
                proposed_stage=proposed_stage,
                certified_stages=certified,
                attempt_type="F",
            )
            assert not result.is_valid, (
                f"NMC compliance violation: stage {proposed_stage} with "
                f"certified={certified} should have been rejected but wasn't"
            )
            assert result.error_code == "DOAP-001"
    
    def test_doap_nmc_002_faculty_decision_required(self):
        """
        DOAP-NMC-002: Every DOAP record requires a faculty_decision (cannot be null).
        Regulation: NMC CBME 2019 Reg 8.3
        Enforced by: NOT NULL constraint on doap_session_records.faculty_decision
        And by: DoapSessionCreate Pydantic model requiring faculty_decision field
        """
        from services.snx_logbook.app.schemas.doap import DoapSessionCreate
        from pydantic import ValidationError
        from uuid import uuid4
        
        with pytest.raises(ValidationError) as exc_info:
            DoapSessionCreate(
                student_id=uuid4(),
                session_id=uuid4(),
                competency_code="AN1.1",
                nmc_level="P",
                stage="D",
                rating="M",
                attempt_type="F",
                # faculty_decision missing — must raise
                faculty_id=uuid4(),
            )
        assert "faculty_decision" in str(exc_info.value)
    
    def test_doap_nmc_003_rating_b_decision_c_rejected(self):
        """
        DOAP-NMC-003: Rating B (Below) cannot have decision C (Certify).
        Regulation: NMC CBME 2019 Reg 8.4
        Below expectation cannot be certified — student requires Repeat or Remediation.
        """
        result = validate_rating_decision(rating="B", decision="C")
        assert not result.is_valid
        assert result.error_code == "DOAP-002"
    
    def test_doap_nmc_003_rating_b_decision_r_allowed(self):
        """DOAP-NMC-003 positive: B + R is allowed (repeat the stage)."""
        result = validate_rating_decision(rating="B", decision="R")
        assert result.is_valid
    
    def test_doap_nmc_003_rating_b_decision_re_allowed(self):
        """DOAP-NMC-003 positive: B + Re is allowed (formal remediation)."""
        result = validate_rating_decision(rating="B", decision="Re")
        assert result.is_valid
```

### B.11 Update Documentation

**`docs/EDGE_CASES.md`** — Add entries:

```markdown
## Category: DOAP State Machine

### DOAP-E001: Backward stage record (refresher D after reaching O)

**Category:** State Machine
**Severity:** Medium
**Source:** ADR-035 design review
**Scenario:** Student has already certified O stage for a competency. Faculty wants to record a refresher D stage demonstration (student requested a recap).
**Expected behaviour:**
- Record is created normally
- Does NOT regress the current state (student remains in OBSERVED state)
- Counted as an additional D record (records_per_stage["D"] += 1)
**Test:** `tests/unit/doap/test_state_machine.py::test_doap_e001_backward_d_refresher_allowed`

### DOAP-E002: Faculty decision Re with no active remediation programme

**Category:** Cross-module integration
**Severity:** High
**Source:** ADR-035 design review
**Scenario:** Faculty decides Re (Remediation) but the institution has not configured any remediation programmes.
**Expected behaviour:**
- DOAP record is still created (decision stands)
- workflow_instance is created with status="initiated" but workflow_definition_code="doap_remediation_pending_config"
- Admin notified via task queue to configure remediation
- Student notified that remediation is required, programme assignment pending
**Test:** `tests/integration/doap/test_workflows.py::test_doap_e002_remediation_no_programme`

### DOAP-E003: Stage skip attempt (P without prior A)

**Category:** State Machine
**Severity:** Critical
**Source:** ADR-035 design review
**Scenario:** Faculty attempts to record a P stage record when A stage has not been certified.
**Expected behaviour:**
- INSERT rejected with error DOAP-001
- Error message lists ALL missing prior stages (not just immediately prior)
- No DOAP record created
- No logbook entry created
- HTTP 422 response with error_code DOAP-001
**Test:** `tests/unit/doap/test_state_machine.py::test_doap_e003_stage_skip_lists_all_missing`
```

**`docs/COMPLIANCE_LOG.md`** — Add rows:

```markdown
| Test ID | Regulation Source | Section | Module | Test File | Last Verified | Status |
|---------|-------------------|---------|--------|-----------|---------------|--------|
| DOAP-NMC-001 | NMC CBME 2019 | DOAP Framework | snx-logbook | tests/compliance/doap/test_nmc_compliance.py | YYYY-MM-DD | Passing |
| DOAP-NMC-002 | NMC CBME 2019 | Reg 8.3 | snx-logbook | tests/compliance/doap/test_nmc_compliance.py | YYYY-MM-DD | Passing |
| DOAP-NMC-003 | NMC CBME 2019 | Reg 8.4 | snx-logbook | tests/compliance/doap/test_nmc_compliance.py | YYYY-MM-DD | Passing |
```

### B.12 Phase B Acceptance Gate

Before Phase C, confirm:

- [ ] All 14 DOAP test IDs visible in COVERAGE_MANIFEST.yaml
- [ ] `python scripts/verify_coverage_manifest.py` shows all 14 as PRESENT
- [ ] DOAP validator tests (unit): 9 passing, 0 xfailed
- [ ] DOAP service tests (integration): at least 5 passing, remaining xfailed for legitimate reasons
- [ ] DOAP compliance tests: all 3 passing (hard fail otherwise)
- [ ] `python -m pytest tests/compliance/doap/ -v` shows green
- [ ] DoapService implements `submit_doap_session`, `get_doap_records`, `compute_state`
- [ ] DOAP router registered in main.py
- [ ] EDGE_CASES.md updated with DOAP-E001, DOAP-E002, DOAP-E003
- [ ] COMPLIANCE_LOG.md updated with DOAP-NMC-001, DOAP-NMC-002, DOAP-NMC-003
- [ ] Audit log writes verified in DoapService
- [ ] Logbook entry auto-creation verified
- [ ] Remediation workflow auto-creation verified
- [ ] `verify_compliance_coverage.py` passes
- [ ] `verify_edge_case_coverage.py` passes

---

## Phase C — Handoff (15 minutes)

### C.1 Update HANDOFF_NOTES.md

Append (do NOT remove the existing CRITICAL SESSION 11 IS R0 ONLY directive):

```markdown
## Session 10 Handoff (YYYY-MM-DD)

**Completed:**
- Phase A: Session 9 debt cleanup
  - --no-verify root cause: [findings]
  - ELEC-002, ELEC-E001, ELEC-E007 now have passing tests
  - ADR-034 worked example traced; output matches expected
  - Migration 0014 applied locally
- Phase B: DOAP Skills implementation
  - 14 new test IDs added to COVERAGE_MANIFEST
  - DoapService implemented with state machine validators
  - 3 NMC compliance tests passing
  - DOAP router registered

**Pending items:**

[TO: 06-testing] — Implement integration test stubs:
- DOAP-007 (evidence asset linkage end-to-end)
- DOAP-E002 (remediation with no programme — needs workflow_definitions seed)
- Any DOAP integration tests still marked xfail

[TO: 11-compliance] — Audit DOAP compliance tests against full NMC CBME 2019 Volume 1, 
Chapter on Clinical Skills. Verify our 3 compliance tests cover the regulation 
completely; identify any additional tests needed.

[TO: 10-documentation] — Update ARCHITECTURE.md with DOAP service section. Update 
the cross-module integration diagram to show DOAP → logbook → workflow → digital_assets.

[DEBT D6] — DOAP state machine assumes session_id is valid; cross-FK validation 
(session belongs to attendance event in clinical category) not yet enforced. 
Add to compliance backlog.

[DEBT D7] — Subject code inference (_infer_subject_code) uses a hardcoded mapping. 
This should be MDM-driven (config-driven mapping table). File a Phase 2.5 task.

## CRITICAL — SESSION 11 IS R0 ONLY (RESTATED)

Session 11 is reserved exclusively for Revision 0 of the Phase 2 Complete Plan.
No code work. No service implementation. No router additions.

Session 11 deliverables:
- ADRs 009-019 retroactively created in docs/DECISIONS.md
- ADRs 020-033 confirmed Accepted status
- docs/verification/baseline_<date>.txt committed
- docs/verification/phase2_test_categorisation.md created
- All 177 missing tests categorised
- COVERAGE_MANIFEST.yaml updated with deferred_to fields
- conventions/DATABASE_CONVENTIONS.md updated per R0.4
- docs/PHASE2_SCHEMA.md created/updated

Any code work attempted in Session 11 will be reverted.

This is non-negotiable. R0 has been deferred since Session 5.
NO FURTHER DEFERRAL ACCEPTED.

— Human supervisor
```

### C.2 Update Other Documentation

- `docs/CHANGELOG.md` — Session 10 summary entry
- `docs/DEVELOPMENT_LOG.md` — high-level
- `docs/COMMAND_HISTORY.md` — every command run this session
- `docs/sessions/2026-MM-DD-session-10.md` — complete session log
- `.agent-memory/working/CURRENT_FOCUS.md` — update to reflect "Session 11: R0 mandatory"
- `.agent-memory/learning/02-backend.md` — append any patterns learned (especially around the state machine validator pattern)
- `.agent-memory/incident/02-backend.md` — append the --no-verify resolution

### C.3 Final Verification Run

```powershell
# All framework verifiers
python scripts\verify_coverage_manifest.py
python scripts\verify_adr_sequence.py
python scripts\verify_edge_case_coverage.py
python scripts\verify_compliance_coverage.py
python scripts\check_secrets.py
python scripts\verify_docs_updated.py

# Lint
python -m ruff check services\snx-logbook\
python -m black --check services\snx-logbook\
python -m mypy services\snx-logbook\

# All tests
python -m pytest tests\ -v --tb=short
```

All must pass. If any fail, STOP and report — do not declare session complete.

### C.4 Session End Declaration

```
SESSION END — Agent: 02-backend (Session 10)
Duration: ~X hours
Phase A: complete (debt cleared)
Phase B: complete (DOAP implemented)
Phase C: complete (handoff ready)

Files modified: ~25
Tests added: 17 (9 validator unit tests, 5 integration, 3 compliance)
Tests passing: 14/17 (3 integration xfailed for legitimate DB-seed reasons)
Migration applied: 0014 ✓
Worked example trace: PASSED
Compliance tests: 3/3 passing
Audit log writes: verified
Pre-commit hook: passed (no --no-verify used)
Documentation updated: ✓
Memory updated: ✓

Next session: SESSION 11 IS R0 ONLY (reconciliation, no code)
Per HANDOFF_NOTES CRITICAL directive, Session 11 must execute Revision 0 of 
the Phase 2 Complete Plan. Any code work in Session 11 will be reverted.
```

### C.5 Commit and End

```powershell
git add .
git commit -m "feat(doap): Session 10 — DOAP Skills + Session 9 debt cleanup

Phase A:
- Investigated --no-verify bypass; root cause: [from findings]
- Made ELEC-002, ELEC-E001, ELEC-E007 pass (real SQLite test fixture)
- Verified ADR-034 worked example: output matches expected
- Applied migration 0014 (elective_allocation_runs) locally

Phase B:
- Added 14 DOAP test IDs to COVERAGE_MANIFEST.yaml
- Implemented DoapService with state machine validators (pure functions)
- Added Pydantic schemas with rating-decision consistency validation
- Created DOAP router with 3 endpoints
- Auto-creation of logbook_entries on DOAP record (DOAP-008)
- Auto-trigger of remediation workflow on Re decision (DOAP-006)
- 3 NMC compliance tests passing (DOAP-NMC-001/002/003)
- Updated EDGE_CASES.md and COMPLIANCE_LOG.md

ADR-035 fully implemented. Session 11 is R0 (no code).

Refs: ADR-034, ADR-035
Closes: Session 9 debt items D1, D2, D3, D4
"
```

If pre-commit hook fails, do NOT use --no-verify. Investigate and fix.

---

## Failure Modes to Watch For

Based on Session 9 patterns, watch for:

1. **Phase A shortcuts.** If you find yourself thinking "let me just start Phase B and circle back" — STOP. Phase A is the gate.

2. **xfail expansion.** Every new xfail marker added needs a `deferred_to:` entry in COVERAGE_MANIFEST. No silent xfail accumulation.

3. **Subject code mapping creep.** The `_infer_subject_code` hardcoded mapping should be MDM-driven. For Session 10, the hardcoded version is acceptable, but it MUST be flagged as DEBT D7 in handoff. Do not let it become permanent.

4. **State machine validator complexity.** If you find yourself adding more conditions to validators, ask: is this from ADR-035, or am I improvising? If improvising, STOP and update ADR-035 first.

5. **Pre-commit hook bypass.** No `--no-verify` this session. If the hook fires, diagnose and fix. The hook is the gate.

6. **Session 11 deferral attempts.** When writing HANDOFF_NOTES, do NOT mention any code work for Session 11. Session 11 is R0. Period. If a code item legitimately exists for Session 11, put it in Session 12.

---

## Reminder

You've delivered the most disciplined session in Session 9. Maintain that standard. The framework's discipline is the safety net — without it, the work isn't trustworthy regardless of how productive it feels.

When you finish Session 10, the work product should be:

- DOAP implemented per spec
- Session 9 debt cleared
- Session 11 unambiguously set up for R0

That last item is the most important. Session 11 R0 is the test of whether the framework holds across the longest deferral the project has had. Make sure your handoff makes deferral structurally impossible.

Go.