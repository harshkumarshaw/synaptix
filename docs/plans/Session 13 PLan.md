# Session 13 Plan — Logbook Phase 2 Extensions + Admission Placeholder

**Target Agent:** 02-backend
**Estimated duration:** 5-7 hours of focused work
**Session structure:** Phase A (R0/S11 review, 20 min) → Phase B (Logbook extensions, main body) → Phase C (Admission placeholder, 45 min) → Phase D (handoff, 15 min)
**Scope:** R4.5 (Logbook Phase 2 extensions) + R4.6 (Admission placeholder)
**References:** Phase 2 Complete Plan §R4.7, §R4.8; ADR-032, ADR-035; COVERAGE_MANIFEST digital_logbook section

---

## Why These Two Are Bundled

Logbook Phase 2 extensions (R4.5) is estimated at 2-3 sessions, but most of the heavy Logbook infrastructure already exists from Sessions 7-10: the `logbook_entries` table, the `logbook_assessments` table, the `LogbookService` class, and the DOAP integration. What remains is specific business logic methods.

Admission Placeholder (R4.6) is minimal CRUD with no business logic — under 1 hour of work.

Bundling saves a session without compromising quality, because the Logbook work has clear acceptance criteria and the Admission work is trivially scoped.

If Phase B runs longer than expected (>4 hours), defer Phase C to Session 13. Do not rush Logbook to fit Admission in.

---

## Mandatory Session Start Protocol

Per AGENTS.md §2:

1. Read `AGENTS.md` (root)
2. Read `docs/HANDOFF_NOTES.md` — check Session 11 outcomes, any flagged items
3. Read `.agent-memory/working/CURRENT_FOCUS.md` — should show R0 complete with Phase 2 completion target numbers
4. Read `agents/02-backend-agent.md`
5. Read `.agent-memory/learning/02-backend.md`
6. Read `.agent-memory/incident/02-backend.md`
7. Read `docs/sessions/2026-*-session-11.md` — confirm R0 actually completed
8. Read `docs/DECISIONS.md` — confirm ADR-001 through ADR-037 exist, no gaps
9. Read `docs/verification/phase2_test_categorisation.md` — note the Phase 2 completion target
10. Read `docs/PHASE2_SCHEMA.md` — the logbook_entries and logbook_assessments schemas you'll implement against

**Declaration format:**

```
SESSION START — Agent: 02-backend (Session 13)
Files read: AGENTS.md ✓, HANDOFF_NOTES ✓, CURRENT_FOCUS ✓, agent spec ✓, 
learning ✓, incidents ✓, Session 11 log ✓, DECISIONS.md ✓ (ADR-001 through 037),
phase2_test_categorisation.md ✓ (Phase 2 target: NN tests must pass),
PHASE2_SCHEMA.md ✓ (logbook_entries + logbook_assessments schemas reviewed)
Task: R4.5 Logbook Phase 2 extensions + R4.6 Admission placeholder
```

---

## Phase A — Session 11 Review Gate (20 min)

Before any implementation work, verify that R0 actually completed.

### A.1 Confirm R0 Completion

Check that these files exist and are non-empty:

```powershell
# ADR sequence intact
python scripts/verify_adr_sequence.py

# Baselines exist
dir docs\verification\baseline_*.txt

# Test categorisation exists
type docs\verification\phase2_test_categorisation.md | Select-Object -First 20

# PHASE2_SCHEMA exists
type docs\PHASE2_SCHEMA.md | Select-Object -First 10
```

**If R0 is NOT complete** (any verifier fails, any file missing): STOP. Do not proceed to Phase B. Report to human supervisor. Session 13 becomes R0 completion, not Logbook work.

**If R0 IS complete:** Record the Phase 2 completion target numbers from `phase2_test_categorisation.md` in your session log:

```markdown
## Phase 2 Completion Baseline (from R0)

- Total tests in manifest: NNN
- Must pass in Phase 2: NN
- Currently passing: NN
- Remaining to implement: NN
- Deferred to Phase 2.5: NN
- Deferred to Phase 3+: NN
```

These numbers are your context for this session. After Session 13, the "Currently passing" number should increase.

### A.2 Read Logbook Schema

Read the `logbook_entries` and `logbook_assessments` table definitions from `docs/PHASE2_SCHEMA.md`. Note specifically:

- `logbook_entries.subject_code` is NULLABLE (per ADR-032)
- `logbook_entries.faculty_initials`, `student_initials`, `faculty_decision` columns exist
- `logbook_entries.backdated` boolean and `backdating_approved_by` UUID columns exist
- `logbook_entries.status` enum: 'pending', 'submitted', 'approved', 'rejected'
- `logbook_assessments.ia_marks_pct` and `ia_marks_awarded` are separate columns (per ADR-023)
- `logbook_assessments.is_complete` boolean

If any of these columns do NOT exist in the actual migration/model, note the discrepancy and decide whether to add them (migration 0016) or work around them.

---

## Phase B — Logbook Phase 2 Extensions (Main Body, 3-4 hours)

### B.1 COVERAGE_MANIFEST Entries (15 min)

Verify the following test IDs exist in `tests/COVERAGE_MANIFEST.yaml` under `digital_logbook:`. If missing, add them now:

```yaml
digital_logbook:
  module_id: A-10
  test_file_prefix: "tests/unit/logbook/"
  enforcement: standard
  
  critical_tests:
    - id: LOG-001
      description: "Create regular logbook entry with all required fields"
      type: unit
    - id: LOG-002
      description: "Create elective logbook entry (subject_code NULL, elective_id set)"
      type: unit
    - id: LOG-003
      description: "Faculty signoff workflow (pending → submitted → approved)"
      type: integration
    - id: LOG-004
      description: "IA marks calculation (ia_marks_pct × subject_ia_max = ia_marks_awarded)"
      type: unit
    - id: LOG-005
      description: "Backdating > 7 days flags needs_review=true"
      type: unit
    - id: LOG-006
      description: "Backdating > 30 days routes to HOD via workflow"
      type: integration
  
  compliance_tests:
    - id: LOG-NMC-008
      description: "Elective logbook entries span 4 weeks (2 blocks × 2 weeks)"
      type: compliance
      regulation_ref: "NMC CBME 2019 Reg 7.3"
    - id: LOG-NMC-009
      description: "Faculty initials required on signed-off entries (non-null, non-empty)"
      type: compliance
      regulation_ref: "NMC CBME 2019 Reg 8.7"
    - id: LOG-NMC-010
      description: "Student initials required on submitted entries (non-null, non-empty)"
      type: compliance
      regulation_ref: "NMC CBME 2019 Reg 8.7"
    - id: LOG-NMC-011
      description: "Faculty decision C/R/Re recorded on every signed-off entry"
      type: compliance
      regulation_ref: "NMC CBME 2019 Reg 8.7"
    - id: LOG-NMC-012
      description: "IA contribution capped at 20% of subject IA max marks"
      type: compliance
      regulation_ref: "NMC CBME 2019 Reg 12.4 Internal Assessment"
  
  edge_cases:
    - id: LOG-E001
      description: "Elective discriminator: elective_id set requires subject_code NULL (and vice versa)"
      type: edge_case
    - id: LOG-E002
      description: "Backdating exactly 7 days — should NOT flag (boundary: > 7, not >= 7)"
      type: edge_case
    - id: LOG-E003
      description: "Multiple faculty signoffs to same entry — only latest counts"
      type: edge_case
```

Total: 12 test IDs for Logbook Phase 2.

### B.2 Test Stubs (30 min)

Create test stub files with `@pytest.mark.xfail` markers. Remove markers as each function is implemented.

**Files to create (or extend if they already exist from earlier sessions):**

```
tests/unit/logbook/test_entries.py          — LOG-001, LOG-002, LOG-E001
tests/unit/logbook/test_backdating.py       — LOG-005, LOG-E002
tests/unit/logbook/test_ia_calculation.py   — LOG-004
tests/unit/logbook/test_signoff.py          — LOG-E003
tests/integration/logbook/test_workflows.py — LOG-003, LOG-006
tests/compliance/logbook/test_nmc_compliance.py — LOG-NMC-008..012
```

**Stub pattern:**

```python
# tests/unit/logbook/test_entries.py
import pytest
from uuid import uuid4
from datetime import date, timedelta


class TestLogbookEntries:
    
    @pytest.mark.xfail(reason="LOG-001: Implementation pending in Session 13")
    async def test_log_001_create_regular_entry(self, test_db_session):
        """
        Test ID: LOG-001
        Module: digital_logbook (A-10)
        
        Verifies:
        - Create logbook entry with subject_code set, elective_id NULL
        - All required fields populated (competency_code, nmc_level, activity_date, activity_name)
        - Status defaults to 'pending'
        - is_core flag set correctly
        - Rating initially NULL (set during signoff)
        - Audit log entry created
        """
        raise NotImplementedError("Stub")
    
    @pytest.mark.xfail(reason="LOG-002: Implementation pending in Session 13")
    async def test_log_002_create_elective_entry(self, test_db_session):
        """
        Test ID: LOG-002
        Edge cases referenced: LOG-E001
        
        Verifies:
        - Create logbook entry with elective_id set, subject_code NULL
        - CHECK constraint chk_logbook_entries_elective satisfied
        - Elective_id references a valid allocated elective for the student
        """
        raise NotImplementedError("Stub")
```

Run the coverage manifest verifier:

```powershell
python scripts/verify_coverage_manifest.py
```

Expected: LOG-001..006, LOG-NMC-008..012, LOG-E001..003 all show as PRESENT.

### B.3 Pydantic Schemas (30 min)

**Extend or create `services/snx-logbook/app/schemas/logbook_phase2.py`:**

If this file already exists from earlier sessions, extend it. If not, create it.

```python
"""Pydantic v2 schemas for Logbook Phase 2 extensions."""
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator


class LogbookEntryCreate(BaseModel):
    """Request to create a logbook entry."""
    model_config = ConfigDict(use_enum_values=True)
    
    student_id: UUID
    
    # Discriminator: exactly one of these must be set (per ADR-032)
    subject_code: Optional[str] = Field(default=None, max_length=50)
    elective_id: Optional[UUID] = None
    
    professional_phase: str = Field(pattern="^(Phase I|Phase II|Phase III Part I|Phase III Part II)$")
    competency_code: str = Field(min_length=2, max_length=50)
    nmc_level: str = Field(pattern="^(K|KH|SH|P)$")
    is_core: bool = False
    
    activity_date: date
    activity_name: str = Field(min_length=1, max_length=150)
    reflection: Optional[str] = Field(default=None, max_length=5000)
    
    @model_validator(mode="after")
    def validate_elective_discriminator(self) -> "LogbookEntryCreate":
        """
        ADR-032: exactly one of subject_code or elective_id must be set.
        Maps to CHECK constraint chk_logbook_entries_elective on the table.
        """
        has_subject = self.subject_code is not None
        has_elective = self.elective_id is not None
        
        if has_subject == has_elective:
            raise ValueError(
                "LOG-VALIDATION-001: Exactly one of subject_code or elective_id "
                "must be set. Got both." if has_subject else
                "LOG-VALIDATION-001: Exactly one of subject_code or elective_id "
                "must be set. Got neither."
            )
        return self


class LogbookEntryResponse(BaseModel):
    """Logbook entry response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    student_id: UUID
    subject_code: Optional[str]
    elective_id: Optional[UUID]
    professional_phase: str
    competency_code: str
    nmc_level: str
    is_core: bool
    activity_date: date
    activity_name: str
    reflection: Optional[str]
    rating: Optional[str]
    attempt_type: Optional[str]
    faculty_decision: Optional[str]
    faculty_initials: Optional[str]
    student_initials: Optional[str]
    status: str
    backdated: bool
    backdating_approved_by: Optional[UUID]
    signed_off_by: Optional[UUID]
    signed_off_at: Optional[datetime]
    created_at: datetime


class LogbookSignoffRequest(BaseModel):
    """Faculty signoff request for a logbook entry."""
    rating: str = Field(pattern="^(B|M|E)$")
    faculty_decision: str = Field(pattern="^(C|R|Re)$")
    faculty_initials: str = Field(min_length=1, max_length=10)
    feedback: Optional[str] = Field(default=None, max_length=2000)
    
    @model_validator(mode="after")
    def validate_rating_decision(self) -> "LogbookSignoffRequest":
        """Rating B cannot have decision C (same rule as DOAP — DOAP-NMC-003)."""
        if self.rating == "B" and self.faculty_decision == "C":
            raise ValueError(
                "LOG-VALIDATION-002: Rating B (Below expectation) cannot have "
                "faculty_decision C (Certify)."
            )
        return self


class LogbookEntrySubmitRequest(BaseModel):
    """Student submission of a logbook entry for faculty review."""
    student_initials: str = Field(min_length=1, max_length=10)


class LogbookAssessmentResponse(BaseModel):
    """Logbook assessment (IA marks) response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    student_id: UUID
    subject_code: str
    professional_phase: str
    total_entries: int
    completed_entries: int
    ia_marks_pct: float
    ia_marks_awarded: float
    is_complete: bool
    signed_off_by: Optional[UUID]
    signed_off_at: Optional[datetime]


class IAMarksCalculation(BaseModel):
    """Internal representation for IA marks calculation."""
    subject_code: str
    professional_phase: str
    total_entries: int
    completed_entries: int
    completion_pct: float          # completed / total × 100
    ia_weight_pct: float           # configured weight (0-20%)
    subject_ia_max: float          # max marks for this subject's IA
    ia_marks_awarded: float        # (completion_pct / 100) × (ia_weight_pct / 100) × subject_ia_max
    capped_at_20_pct: bool         # whether the cap was applied
```

### B.4 Service Layer — Logbook Extensions (90-120 min)

This is the main implementation work. Extend `LogbookService` (or create a new service class if the file is getting too large).

**Methods to implement:**

#### B.4.1 `create_entry(tenant_id, user_id, data: LogbookEntryCreate) → LogbookEntryResponse`

Core logbook entry creation with:

1. **Elective discriminator validation** — the Pydantic validator catches this at schema level, but also enforce at service level (belt and suspenders)

2. **Elective ownership validation** — if elective_id is set, verify the student has an allocation for that elective:
```python
if data.elective_id:
    allocation = await session.scalar(
        select(ElectiveAllocation).where(
            ElectiveAllocation.tenant_id == tenant_id,
            ElectiveAllocation.student_id == data.student_id,
            ElectiveAllocation.elective_id == data.elective_id,
            ElectiveAllocation.deleted_at.is_(None),
        )
    )
    if not allocation:
        raise LogbookServiceError(
            "LOG-002", "Student is not allocated to this elective"
        )
```

3. **Backdating detection** — compare `activity_date` with `today`:
```python
from datetime import date, timedelta

gap_days = (date.today() - data.activity_date).days

entry.backdated = gap_days > 7

if gap_days > 30:
    # Route to HOD via workflow engine
    workflow = WorkflowInstance(
        workflow_definition_code="logbook_backdating_hod_review",
        entity_type="logbook_entry",
        entity_id=entry.id,
        status="initiated",
        ...
    )
    session.add(workflow)
    entry.status = "pending"  # Cannot be submitted until HOD approves backdate
elif gap_days > 7:
    entry.needs_review = True  # Faculty must explicitly approve the backdate
    entry.status = "pending"
else:
    entry.status = "pending"  # Normal flow
```

4. **Core vs non-core** — set `is_core` from the input. No auto-detection (the student/faculty selects this when creating the entry; the NMC competency matrix determines what's core vs non-core, and that mapping is in MDM, not hardcoded).

5. **Audit log** — write to audit_log table.

6. **Auto-set professional_phase** — validate that the student's current phase matches `data.professional_phase`. If mismatch, reject.

#### B.4.2 `submit_entry(tenant_id, user_id, entry_id, data: LogbookEntrySubmitRequest) → LogbookEntryResponse`

Student submits their entry for faculty review:

1. **Validate entry exists** and belongs to student
2. **Validate status is 'pending'** (cannot submit already-submitted or approved entries)
3. **Record student_initials** — LOG-NMC-010 compliance
4. **Transition status** → 'submitted'
5. **Audit log**

```python
async def submit_entry(
    self, tenant_id: UUID, student_id: UUID, entry_id: UUID,
    data: LogbookEntrySubmitRequest,
) -> LogbookEntryResponse:
    entry = await self._get_entry(tenant_id, entry_id)
    
    if entry.student_id != student_id:
        raise LogbookServiceError("LOG-AUTH-001", "Entry does not belong to this student")
    
    if entry.status != "pending":
        raise LogbookServiceError("LOG-003", f"Cannot submit entry in '{entry.status}' status")
    
    if entry.backdated and entry.backdating_approved_by is None and (date.today() - entry.activity_date).days > 30:
        raise LogbookServiceError(
            "LOG-004", "Backdated entry (>30 days) requires HOD approval before submission"
        )
    
    entry.student_initials = data.student_initials
    entry.status = "submitted"
    entry.updated_at = datetime.now(timezone.utc)
    entry.updated_by = student_id
    
    await write_audit_log(self.session, tenant_id, student_id, "submit_logbook_entry",
                          "logbook_entry", entry.id, {"student_initials": data.student_initials})
    
    await self.session.flush()
    return LogbookEntryResponse.model_validate(entry)
```

#### B.4.3 `signoff_entry(tenant_id, faculty_id, entry_id, data: LogbookSignoffRequest) → LogbookEntryResponse`

Faculty signs off on a submitted entry:

1. **Validate entry exists** and status is 'submitted'
2. **Validate faculty authorisation** — faculty must be assigned to the course (via faculty_course_assignments) or be the designated supervisor (for elective entries)
3. **Record faculty_initials** — LOG-NMC-009 compliance
4. **Record faculty_decision** (C/R/Re) — LOG-NMC-011 compliance
5. **Record rating** (B/M/E)
6. **Rating-decision consistency** — B + C is invalid (same rule as DOAP-NMC-003)
7. **Transition status** → 'approved' if decision=C, or 'rejected' if decision=R/Re
8. **Set signed_off_by, signed_off_at**
9. **Trigger IA recalculation** for the student's subject/phase
10. **Audit log**

```python
async def signoff_entry(
    self, tenant_id: UUID, faculty_id: UUID, entry_id: UUID,
    data: LogbookSignoffRequest,
) -> LogbookEntryResponse:
    entry = await self._get_entry(tenant_id, entry_id)
    
    if entry.status != "submitted":
        raise LogbookServiceError("LOG-005", f"Cannot sign off entry in '{entry.status}' status")
    
    # Faculty authorisation check
    await self._verify_faculty_authorisation(tenant_id, faculty_id, entry)
    
    # Apply signoff
    entry.rating = data.rating
    entry.faculty_decision = data.faculty_decision
    entry.faculty_initials = data.faculty_initials
    entry.signed_off_by = faculty_id
    entry.signed_off_at = datetime.now(timezone.utc)
    entry.status = "approved" if data.faculty_decision == "C" else "rejected"
    entry.updated_at = datetime.now(timezone.utc)
    entry.updated_by = faculty_id
    
    await self.session.flush()
    
    # Recalculate IA marks for this subject/phase
    if entry.subject_code:  # Regular entries (not elective)
        await self._recalculate_ia_marks(
            tenant_id, entry.student_id, entry.subject_code, entry.professional_phase
        )
    
    await write_audit_log(self.session, tenant_id, faculty_id, "signoff_logbook_entry",
                          "logbook_entry", entry.id, {
                              "rating": data.rating,
                              "faculty_decision": data.faculty_decision,
                              "new_status": entry.status,
                          })
    
    await self.session.flush()
    return LogbookEntryResponse.model_validate(entry)
```

#### B.4.4 `_recalculate_ia_marks(tenant_id, student_id, subject_code, professional_phase)`

The IA (Internal Assessment) marks calculation. This is the most NMC-critical method in this session.

**Formula per NMC CBME 2019 Reg 12.4:**

```
total_entries = count of logbook_entries for (student, subject, phase) with status='approved'
completed_entries = count of those where faculty_decision = 'C'
completion_pct = completed_entries / total_entries × 100  (0 if total_entries = 0)

ia_weight_pct = configured weight for logbook IA (0-20%, from MDM config per subject)
subject_ia_max = max IA marks for this subject (from MDM config per subject)

ia_marks_awarded = (completion_pct / 100) × (ia_weight_pct / 100) × subject_ia_max
```

**The 20% cap (LOG-NMC-012):**

Logbook contribution to IA is CAPPED at 20% of the subject's total IA marks. This means:

```python
ia_marks_awarded = min(
    (completion_pct / 100) * (ia_weight_pct / 100) * subject_ia_max,
    0.20 * subject_ia_max  # Hard cap at 20%
)
```

If the MDM configuration sets `ia_weight_pct` to more than 20% (institutional error), the system enforces the 20% cap anyway and logs a compliance_incidents row.

**Implementation:**

```python
async def _recalculate_ia_marks(
    self, tenant_id: UUID, student_id: UUID,
    subject_code: str, professional_phase: str,
) -> None:
    """Recalculate logbook_assessments row for the given student/subject/phase."""
    
    # Count approved entries
    total_q = await self.session.execute(
        select(func.count(LogbookEntry.id)).where(
            LogbookEntry.tenant_id == tenant_id,
            LogbookEntry.student_id == student_id,
            LogbookEntry.subject_code == subject_code,
            LogbookEntry.professional_phase == professional_phase,
            LogbookEntry.status == "approved",
            LogbookEntry.deleted_at.is_(None),
        )
    )
    total_entries = total_q.scalar() or 0
    
    # Count certified entries (faculty_decision = 'C')
    completed_q = await self.session.execute(
        select(func.count(LogbookEntry.id)).where(
            LogbookEntry.tenant_id == tenant_id,
            LogbookEntry.student_id == student_id,
            LogbookEntry.subject_code == subject_code,
            LogbookEntry.professional_phase == professional_phase,
            LogbookEntry.status == "approved",
            LogbookEntry.faculty_decision == "C",
            LogbookEntry.deleted_at.is_(None),
        )
    )
    completed_entries = completed_q.scalar() or 0
    
    # Get MDM config for this subject
    ia_weight_pct, subject_ia_max = await self._get_ia_config(
        tenant_id, subject_code, professional_phase
    )
    
    # Calculate
    completion_pct = (completed_entries / total_entries * 100) if total_entries > 0 else 0.0
    raw_marks = (completion_pct / 100) * (ia_weight_pct / 100) * subject_ia_max
    
    # Enforce 20% cap (LOG-NMC-012)
    cap = Decimal("0.20") * subject_ia_max
    ia_marks_awarded = min(Decimal(str(raw_marks)), cap)
    
    capped = raw_marks > float(cap)
    if capped:
        # Log compliance concern if MDM config exceeds 20%
        await self.session.execute(
            insert(ComplianceIncident).values(
                tenant_id=tenant_id,
                student_id=student_id,
                incident_type="ia_weight_exceeds_20_pct",
                severity="medium",
                details={
                    "subject_code": subject_code,
                    "configured_weight_pct": float(ia_weight_pct),
                    "cap_applied": True,
                },
            )
        )
    
    # Upsert logbook_assessments row
    existing = await self.session.scalar(
        select(LogbookAssessment).where(
            LogbookAssessment.tenant_id == tenant_id,
            LogbookAssessment.student_id == student_id,
            LogbookAssessment.subject_code == subject_code,
            LogbookAssessment.professional_phase == professional_phase,
        )
    )
    
    if existing:
        existing.total_entries = total_entries
        existing.completed_entries = completed_entries
        existing.ia_marks_pct = float(ia_weight_pct)
        existing.ia_marks_awarded = float(ia_marks_awarded)
        existing.is_complete = (total_entries > 0 and completed_entries == total_entries)
        existing.updated_at = datetime.now(timezone.utc)
    else:
        self.session.add(LogbookAssessment(
            tenant_id=tenant_id,
            student_id=student_id,
            subject_code=subject_code,
            professional_phase=professional_phase,
            total_entries=total_entries,
            completed_entries=completed_entries,
            ia_marks_pct=float(ia_weight_pct),
            ia_marks_awarded=float(ia_marks_awarded),
            is_complete=(total_entries > 0 and completed_entries == total_entries),
        ))
    
    await self.session.flush()


async def _get_ia_config(
    self, tenant_id: UUID, subject_code: str, professional_phase: str,
) -> tuple[Decimal, Decimal]:
    """
    Get IA weight percentage and subject IA max from MDM config.
    
    Falls back to defaults if MDM config not found:
    - ia_weight_pct: 10.0 (10% of IA from logbook)
    - subject_ia_max: 40.0 (typical NMC IA max)
    
    TODO (D7-related): This should read from MDM config tables.
    For Session 13, use fallback defaults with a warning log.
    """
    # Try MDM first
    config = await self.session.scalar(
        select(MdmConfig).where(
            MdmConfig.tenant_id == tenant_id,
            MdmConfig.config_key == f"ia_config.{subject_code}.{professional_phase}",
        )
    )
    
    if config and config.config_value:
        return (
            Decimal(str(config.config_value.get("ia_weight_pct", 10.0))),
            Decimal(str(config.config_value.get("subject_ia_max", 40.0))),
        )
    
    # Fallback defaults
    import logging
    logging.warning(
        "MDM config not found for IA: %s/%s. Using defaults (10%%, 40 marks).",
        subject_code, professional_phase,
    )
    return Decimal("10.0"), Decimal("40.0")
```

#### B.4.5 `get_student_entries(tenant_id, student_id, filters) → list[LogbookEntryResponse]`

Simple query with optional filters:

- `subject_code` (optional)
- `professional_phase` (optional)
- `status` (optional)
- `competency_code` (optional)
- `is_core` (optional)
- `date_from`, `date_to` (optional)

Standard pagination. Return list of LogbookEntryResponse.

#### B.4.6 `get_ia_assessment(tenant_id, student_id, subject_code, professional_phase) → LogbookAssessmentResponse`

Read the logbook_assessments row for a student/subject/phase. If no row exists (no entries yet), return a zero-value response.

### B.5 API Router (30 min)

**Create or extend `services/snx-logbook/app/routers/logbook.py`:**

```python
"""Logbook Phase 2 API endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from packages.shared.auth import require_role, current_user, User
from packages.shared.db.session import get_session
from ..schemas.logbook_phase2 import (
    LogbookEntryCreate, LogbookEntryResponse,
    LogbookEntrySubmitRequest, LogbookSignoffRequest,
    LogbookAssessmentResponse,
)
from ..services.logbook_service import LogbookService, LogbookServiceError


router = APIRouter(prefix="/logbook", tags=["logbook"])


@router.post("/entries", response_model=LogbookEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_logbook_entry(
    data: LogbookEntryCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_role(["student"])),
):
    """Student creates a new logbook entry."""
    service = LogbookService(session)
    try:
        result = await service.create_entry(user.tenant_id, user.id, data)
        await session.commit()
        return result
    except LogbookServiceError as e:
        await session.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail={"error_code": e.code, "message": e.message})


@router.patch("/entries/{entry_id}/submit", response_model=LogbookEntryResponse)
async def submit_logbook_entry(
    entry_id: UUID,
    data: LogbookEntrySubmitRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_role(["student"])),
):
    """Student submits entry for faculty review. Records student initials."""
    service = LogbookService(session)
    try:
        result = await service.submit_entry(user.tenant_id, user.student_id, entry_id, data)
        await session.commit()
        return result
    except LogbookServiceError as e:
        await session.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail={"error_code": e.code, "message": e.message})


@router.patch("/entries/{entry_id}/signoff", response_model=LogbookEntryResponse)
async def signoff_logbook_entry(
    entry_id: UUID,
    data: LogbookSignoffRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_role(["faculty", "hod", "admin"])),
):
    """Faculty signs off on a submitted logbook entry. Records decision and initials."""
    service = LogbookService(session)
    try:
        result = await service.signoff_entry(user.tenant_id, user.id, entry_id, data)
        await session.commit()
        return result
    except LogbookServiceError as e:
        await session.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail={"error_code": e.code, "message": e.message})


@router.get("/entries", response_model=list[LogbookEntryResponse])
async def list_logbook_entries(
    student_id: UUID,
    subject_code: str | None = None,
    professional_phase: str | None = None,
    entry_status: str | None = Query(None, alias="status"),
    competency_code: str | None = None,
    is_core: bool | None = None,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user),
):
    """List logbook entries for a student with optional filters."""
    # Auth: student sees own; faculty/admin sees any in tenant
    if user.role == "student" and user.student_id != student_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    
    service = LogbookService(session)
    return await service.get_student_entries(
        user.tenant_id, student_id,
        subject_code=subject_code,
        professional_phase=professional_phase,
        status=entry_status,
        competency_code=competency_code,
        is_core=is_core,
    )


@router.get("/assessments/{student_id}/{subject_code}/{professional_phase}",
            response_model=LogbookAssessmentResponse)
async def get_ia_assessment(
    student_id: UUID,
    subject_code: str,
    professional_phase: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_user),
):
    """Get IA marks assessment for a student's subject/phase."""
    if user.role == "student" and user.student_id != student_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    
    service = LogbookService(session)
    return await service.get_ia_assessment(
        user.tenant_id, student_id, subject_code, professional_phase
    )
```

Register router in `main.py` if not already registered.

### B.6 Unit Tests — Remove xfail (60-90 min)

As you implement each method, convert the corresponding test from xfail to real test.

**Priority order for test conversion:**

1. **LOG-E001** (elective discriminator) — validates ADR-032; pure validation test
2. **LOG-001** (regular entry creation) — core CRUD
3. **LOG-002** (elective entry creation) — validates elective ownership
4. **LOG-005** (backdating > 7 days) — boundary test
5. **LOG-E002** (backdating exactly 7 days) — boundary edge case
6. **LOG-004** (IA calculation) — most complex; test in isolation

**Critical test: LOG-004 IA Calculation**

```python
class TestIACalculation:
    
    async def test_log_004_ia_marks_calculation(self, test_db_session):
        """
        Test ID: LOG-004
        Verifies: IA marks = (completion_pct / 100) × (ia_weight_pct / 100) × subject_ia_max
        
        Setup:
        - 10 logbook entries for ANAT/Phase I, all approved
        - 7 with faculty_decision = C, 3 with R
        - MDM config: ia_weight_pct = 15%, subject_ia_max = 40
        
        Expected:
        - total_entries = 10
        - completed_entries = 7
        - completion_pct = 70.0
        - ia_marks_awarded = 0.70 × 0.15 × 40 = 4.20
        """
        # ... seed data, run _recalculate_ia_marks, assert
    
    async def test_log_nmc_012_ia_cap_at_20_pct(self, test_db_session):
        """
        Test ID: LOG-NMC-012
        Compliance: NMC CBME 2019 Reg 12.4
        
        Verifies: If ia_weight_pct is configured above 20%, the system caps at 20%.
        
        Setup:
        - MDM config: ia_weight_pct = 25% (institutional misconfiguration)
        - subject_ia_max = 40
        - All entries completed (100%)
        
        Expected:
        - ia_marks_awarded = 0.20 × 40 = 8.00 (NOT 0.25 × 40 = 10.00)
        - compliance_incidents row created with incident_type = 'ia_weight_exceeds_20_pct'
        """
        # ... seed data, run, assert cap applied and incident logged
```

### B.7 Compliance Tests (30 min)

**`tests/compliance/logbook/test_nmc_compliance.py`:**

```python
"""Logbook NMC compliance tests. HARD-FAIL."""
import pytest
from datetime import date, timedelta
from uuid import uuid4
from pydantic import ValidationError

from services.snx_logbook.app.schemas.logbook_phase2 import (
    LogbookEntryCreate, LogbookSignoffRequest, LogbookEntrySubmitRequest,
)


class TestLogbookNmcCompliance:
    
    def test_log_nmc_009_faculty_initials_required_on_signoff(self):
        """
        LOG-NMC-009: Faculty initials required on signed-off entries.
        NMC CBME 2019 Reg 8.7
        """
        with pytest.raises(ValidationError) as exc_info:
            LogbookSignoffRequest(
                rating="M",
                faculty_decision="C",
                faculty_initials="",  # Empty string should fail min_length=1
            )
        assert "faculty_initials" in str(exc_info.value)
    
    def test_log_nmc_010_student_initials_required_on_submit(self):
        """
        LOG-NMC-010: Student initials required on submitted entries.
        NMC CBME 2019 Reg 8.7
        """
        with pytest.raises(ValidationError) as exc_info:
            LogbookEntrySubmitRequest(
                student_initials="",  # Empty string should fail min_length=1
            )
        assert "student_initials" in str(exc_info.value)
    
    def test_log_nmc_011_faculty_decision_required_on_signoff(self):
        """
        LOG-NMC-011: Faculty decision C/R/Re required.
        NMC CBME 2019 Reg 8.7
        """
        with pytest.raises(ValidationError):
            LogbookSignoffRequest(
                rating="M",
                # faculty_decision missing
                faculty_initials="DR",
            )
    
    def test_log_nmc_011_invalid_decision_rejected(self):
        """LOG-NMC-011: Invalid faculty decision value rejected."""
        with pytest.raises(ValidationError):
            LogbookSignoffRequest(
                rating="M",
                faculty_decision="X",  # Invalid
                faculty_initials="DR",
            )
    
    async def test_log_nmc_012_ia_cap_at_20_pct(self, test_db_session):
        """
        LOG-NMC-012: IA contribution capped at 20% of subject IA max.
        NMC CBME 2019 Reg 12.4
        See LOG-004 test for calculation verification.
        """
        # This test is the compliance-enforcement version of LOG-004
        # ... (implementation same as LOG-004 cap test above)
        pass  # Implement alongside LOG-004
    
    def test_log_nmc_008_elective_discriminator_enforced(self):
        """
        LOG-NMC-008 related: Elective entries must have elective_id set and
        subject_code NULL (per ADR-032).
        """
        # Both set — should fail
        with pytest.raises(ValidationError):
            LogbookEntryCreate(
                student_id=uuid4(),
                subject_code="ANAT",
                elective_id=uuid4(),  # Both set
                professional_phase="Phase I",
                competency_code="AN1.1",
                nmc_level="P",
                activity_date=date.today(),
                activity_name="Test",
            )
        
        # Neither set — should fail
        with pytest.raises(ValidationError):
            LogbookEntryCreate(
                student_id=uuid4(),
                # Both missing
                professional_phase="Phase I",
                competency_code="AN1.1",
                nmc_level="P",
                activity_date=date.today(),
                activity_name="Test",
            )
```

### B.8 Phase B Acceptance Gate

Before Phase C:

- [ ] COVERAGE_MANIFEST has all 12 LOG test IDs
- [ ] `python scripts/verify_coverage_manifest.py` shows all LOG IDs as PRESENT
- [ ] LOG-001, LOG-002 (entry creation): passing
- [ ] LOG-004 (IA calculation): passing with worked example
- [ ] LOG-005, LOG-E002 (backdating): passing with boundary test
- [ ] LOG-E001 (elective discriminator): passing
- [ ] LOG-NMC-009, LOG-NMC-010, LOG-NMC-011 (signature compliance): passing
- [ ] LOG-NMC-012 (20% IA cap): passing
- [ ] LOG-003, LOG-006 (workflow integration): xfail acceptable if workflow engine fixtures unavailable
- [ ] LOG-E003 (multiple signoffs): xfail acceptable
- [ ] Audit log writes verified for all mutating endpoints
- [ ] Router registered in main.py
- [ ] Logbook router endpoints respond correctly to manual testing
- [ ] Pre-commit hook passes (no --no-verify)

Target: 9 of 12 tests passing, 3 xfail for legitimate integration reasons.

---

## Phase C — Admission Placeholder (45 min)

This is R4.6 — minimal CRUD for admission_applications. No business logic beyond basic creation and listing.

### C.1 Schema

```python
# services/snx-academic/app/schemas/admissions.py (or wherever admissions live)
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class AdmissionApplicationCreate(BaseModel):
    application_number: str = Field(min_length=1, max_length=50)
    student_name: str = Field(min_length=1, max_length=150)
    applied_for_program_id: UUID

class AdmissionApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    application_number: str
    student_name: str
    applied_for_program_id: UUID
    created_at: datetime
```

### C.2 Service

Minimal CRUD service:
- `create_application(tenant_id, user_id, data)` — creates row, audit log
- `list_applications(tenant_id, filters)` — paginated list
- `get_application(tenant_id, application_id)` — single fetch

No workflow. No verification engine. No consent management. Those are Phase 2.5.

### C.3 Router

```python
POST /admissions/applications — create (admin role)
GET  /admissions/applications — list (admin role)
GET  /admissions/applications/{id} — get (admin role)
```

### C.4 Manifest Entries

Add to COVERAGE_MANIFEST:

```yaml
admissions:
  module_id: I-02
  test_file_prefix: "tests/unit/admissions/"
  enforcement: standard
  
  critical_tests:
    - id: ADM-001
      description: "Create admission application"
      type: unit
    - id: ADM-002
      description: "List admission applications with pagination"
      type: unit
    - id: ADM-003
      description: "Get admission application by ID"
      type: unit
    - id: ADM-004
      description: "Unique application_number per tenant enforced"
      type: unit
```

Create stubs, implement, remove xfail. Target: all 4 passing.

### C.5 Phase C Acceptance Gate

- [ ] ADM-001..004 all passing
- [ ] Router registered
- [ ] Audit log writes for create
- [ ] Phase 2.5 items documented in HANDOFF_NOTES (verification engine, consent, document upload)

---

## Phase D — Handoff (15 min)

### D.1 Update docs/EDGE_CASES.md

Add entries for LOG-E001, LOG-E002, LOG-E003 following the standard format.

### D.2 Update docs/COMPLIANCE_LOG.md

Add rows for LOG-NMC-008 through LOG-NMC-012 with traceability.

### D.3 Update HANDOFF_NOTES.md

```markdown
## Session 13 Complete — Logbook Phase 2 + Admission Placeholder (YYYY-MM-DD)

**Completed:**
- R4.5: Logbook Phase 2 extensions (create, submit, signoff, IA calculation, backdating)
- R4.6: Admission placeholder (minimal CRUD)
- 12 LOG tests: N passing, M xfail
- 4 ADM tests: all passing
- IA calculation verified with worked example (70% completion, 15% weight, 40 max → 4.20 awarded)
- 20% IA cap compliance test passing

**Phase 2 completion progress:**
- Before Session 13: NN tests passing
- After Session 13: NN tests passing (+NN)
- Remaining to reach target: NN

**Pending items:**

[TO: 06-testing] — Integration test implementations:
- LOG-003 (faculty signoff workflow — needs workflow_instance fixture)
- LOG-006 (backdating > 30 days routes to HOD — needs workflow fixture)
- LOG-E003 (multiple signoffs — needs multi-user fixture)

[TO: 11-compliance] — Audit LOG-NMC compliance tests against NMC CBME 2019 Volume 1.
Verify our 5 compliance tests cover Reg 7.3, 8.7, 12.4 completely.

[TO: 10-documentation] — Update ARCHITECTURE.md with logbook Phase 2 service section.

[DEBT D8] — IA config reads from MDM with fallback defaults. MDM config seeding needed
before production. Logged as Phase 2.5 task.

[DEBT D9] — LOG-NMC-008 (elective 4-week duration) test is schema-level only. Full
integration test requires elective allocation + logbook entry spanning 4 weeks. Deferred
to integration testing session.

### Next sessions:

Session 13: R4 gap-closure + integration testing
- AETCOM integration items
- Cross-module integration tests
- xfail conversion sprint

Session 14: R5 — Compliance tightening + Phase 2 completion review
```

### D.4 Update Tracking Docs

- `docs/CHANGELOG.md`
- `docs/DEVELOPMENT_LOG.md`
- `docs/COMMAND_HISTORY.md`
- `docs/sessions/YYYY-MM-DD-session-12.md`
- `.agent-memory/working/CURRENT_FOCUS.md`
- `.agent-memory/learning/02-backend.md`

### D.5 Final Verification + Commit

```powershell
python scripts/verify_coverage_manifest.py
python scripts/verify_adr_sequence.py
python scripts/verify_edge_case_coverage.py
python scripts/verify_compliance_coverage.py
python scripts/check_secrets.py

python -m ruff check services/snx-logbook/
python -m black --check services/snx-logbook/

python -m pytest tests/ -v --tb=short
```

Commit without `--no-verify`.

### D.6 Session End Declaration

```
SESSION END — Agent: 02-backend (Session 13)
Duration: ~X hours

Phase A: R0 verified complete ✓
Phase B: Logbook Phase 2 extensions — N/12 tests passing
Phase C: Admission placeholder — 4/4 tests passing
Phase D: Handoff complete

Files modified: ~NN
Tests added: 16 (12 logbook + 4 admission)
Tests passing: NN/16 (M xfail for legitimate integration reasons)
Compliance tests: N/N passing
Audit log writes: verified
Pre-commit hook: passed (no --no-verify)
Documentation updated: ✓
Memory updated: ✓

Phase 2 completion progress: NN/NN target tests passing (NN remaining)

Next session (13): R4 gap-closure + integration testing sprint
```

---

## Acceptance Criteria Checklist

- [ ] R0 completion verified in Phase A gate
- [ ] COVERAGE_MANIFEST has all 12 LOG + 4 ADM test IDs
- [ ] LOG-001, LOG-002 (entry creation) passing
- [ ] LOG-004 (IA calculation) passing with worked example
- [ ] LOG-005, LOG-E002 (backdating) passing
- [ ] LOG-E001 (elective discriminator) passing
- [ ] LOG-NMC-009, 010, 011 (signature compliance) passing
- [ ] LOG-NMC-012 (20% IA cap) passing with compliance_incidents verification
- [ ] ADM-001..004 all passing
- [ ] All routers registered in main.py
- [ ] Audit log writes on all mutating endpoints
- [ ] EDGE_CASES.md updated with LOG-E001..003
- [ ] COMPLIANCE_LOG.md updated with LOG-NMC-008..012
- [ ] Phase 2 completion progress numbers documented
- [ ] All verifiers pass
- [ ] Committed without --no-verify

---

## Failure Modes to Watch For

1. **IA calculation precision.** Use `Decimal` throughout, not `float`. Currency-style arithmetic rules apply to marks. Rounding errors at 20% cap boundary are compliance violations.

2. **Backdating boundary off-by-one.** The rule is `> 7 days`, NOT `>= 7 days`. Exactly 7 days should NOT flag. Test LOG-E002 explicitly verifies this boundary. Get it right.

3. **Signoff overwrite.** If a faculty signs off an entry, then a different faculty tries to sign off the same entry, what happens? LOG-E003 tests this. The answer should be: reject with "entry already signed off" error. Re-signoff requires the original signoff to be reverted first (via a separate endpoint, not implemented in Session 13).

4. **Elective entry without allocation.** A student creating a logbook entry for an elective they're not allocated to should be rejected at service level, not just at DB FK level. The service validation gives a better error message.

5. **MDM config absence.** The _get_ia_config method uses fallback defaults. This is acceptable for Session 13 but MUST be flagged as debt (D8). Production deployment requires MDM seeding.

6. **Admission scope creep.** The agent may want to add verification workflow, document upload, consent forms to the Admission module. Reject any scope beyond CRUD. Those are Phase 2.5. The placeholder exists only to satisfy the module presence in the architecture.

---

*After Session 13, R4 is nearly complete. Sessions 13-14 close the gaps and begin R5.*