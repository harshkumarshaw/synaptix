# Session 16 Plan — Phase 2.5: MDM Seeding + Deferred Tests

**Target Agent:** 02-backend
**Estimated duration:** 4-5 hours
**Runs in parallel with:** Session F1 (Frontend Agent 03)
**Goal:** Resolve technical debt D7/D8, seed MDM for JMN, implement 11 deferred tests from Session 14

---

## Parallel Track Notice

This session runs SIMULTANEOUSLY with Session F1 (Frontend scaffold). The two agents work independently:

- **Backend Agent (02):** This plan. Works in `services/`, `tests/`, `scripts/`, `docs/`
- **Frontend Agent (03):** Session F1. Works in `frontend-web/`

No file conflicts. No coordination needed except at commit time (merge both into main).

---

## Mandatory Session Start Protocol

```
SESSION START — Agent: 02-backend (Session 16 — Phase 2.5)
Files read: AGENTS.md ✓, HANDOFF_NOTES ✓, CURRENT_FOCUS ✓, agent spec ✓,
learning ✓, incidents ✓, Session 15 log ✓, phase2_scorecard.md ✓,
COVERAGE_MANIFEST.yaml ✓ (11 deferred tests identified)
Task: Phase 2.5 — MDM seeding, technical debt D7/D8, 11 deferred tests
Parallel: Frontend Agent running Session F1 concurrently
```

---

## Phase A — Technical Debt D7 + D8: MDM-Driven Configuration (90-120 min)

### Context

Two hardcoded patterns exist in the codebase that should be configuration-driven:

- **D7 (Session 10):** `DoapService._infer_subject_code()` uses a hardcoded `prefix → subject_code` mapping. Should read from MDM.
- **D8 (Session 13):** `LogbookService._get_ia_config()` uses fallback defaults (10% weight, 40 max marks). Should read from MDM config tables.

Both need the same infrastructure: a properly seeded MDM configuration layer.

### A.1 MDM Config Schema Review

The `mdm_configs` table should already exist from Phase 1A migrations. Verify:

```powershell
# Check if table exists
psql -U postgres -d synaptix_dev -c "\d mdm_configs"
```

If it exists, confirm the schema supports:
```sql
-- Expected structure
mdm_configs (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    config_key VARCHAR(200) NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    UNIQUE (tenant_id, config_key)
)
```

If the table does NOT exist, create migration `0018_mdm_configs.py` with this schema.

### A.2 MDM Config Service

Create or extend `packages/shared/mdm/config_service.py`:

```python
"""MDM Configuration Service — reads tenant-scoped config from mdm_configs table."""
from decimal import Decimal
from typing import Any, TypeVar, overload
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class MdmConfigService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(
        self, tenant_id: UUID, key: str, default: Any = None
    ) -> Any:
        """Get a config value by key. Returns default if not found."""
        from packages.shared.db.models import MdmConfig  # avoid circular

        result = await self.session.scalar(
            select(MdmConfig).where(
                MdmConfig.tenant_id == tenant_id,
                MdmConfig.config_key == key,
            )
        )
        if result and result.config_value is not None:
            return result.config_value
        return default

    async def get_subject_code_mapping(self, tenant_id: UUID) -> dict[str, str]:
        """
        Get competency prefix → subject_code mapping.
        Replaces hardcoded D7 mapping in DoapService.
        """
        mapping = await self.get(
            tenant_id,
            "competency.prefix_to_subject_code",
            default=self._default_subject_mapping(),
        )
        return mapping

    async def get_ia_config(
        self, tenant_id: UUID, subject_code: str, professional_phase: str
    ) -> tuple[Decimal, Decimal]:
        """
        Get IA weight percentage and subject IA max marks.
        Replaces hardcoded D8 fallbacks in LogbookService.
        """
        config = await self.get(
            tenant_id,
            f"ia_config.{subject_code}.{professional_phase}",
            default=None,
        )
        if config:
            return (
                Decimal(str(config.get("ia_weight_pct", 10.0))),
                Decimal(str(config.get("subject_ia_max", 40.0))),
            )

        # Try subject-level default (without phase)
        config = await self.get(
            tenant_id,
            f"ia_config.{subject_code}",
            default=None,
        )
        if config:
            return (
                Decimal(str(config.get("ia_weight_pct", 10.0))),
                Decimal(str(config.get("subject_ia_max", 40.0))),
            )

        # Global default
        return Decimal("10.0"), Decimal("40.0")

    async def get_attendance_thresholds(
        self, tenant_id: UUID, attendance_category: str
    ) -> Decimal:
        """Get attendance threshold for a category."""
        defaults = {
            "theory": Decimal("75.00"),
            "practical": Decimal("80.00"),
            "clinical": Decimal("80.00"),
            "doap": Decimal("80.00"),
            "ece": Decimal("80.00"),
            "aetcom": Decimal("75.00"),
            "foundation_course": Decimal("75.00"),
            "elective": Decimal("75.00"),
        }
        config = await self.get(
            tenant_id,
            f"attendance.threshold.{attendance_category}",
            default=None,
        )
        if config:
            return Decimal(str(config))
        return defaults.get(attendance_category, Decimal("75.00"))

    @staticmethod
    def _default_subject_mapping() -> dict[str, str]:
        """NMC CBME 2019 standard prefix mapping."""
        return {
            "AN": "ANAT", "PY": "PHYS", "BI": "BIOC", "MI": "MICR",
            "PA": "PATH", "PH": "PHAR", "FM": "FMED", "CM": "CMED",
            "GM": "GMED", "GS": "GSUR", "OG": "OBGY", "PE": "PEDI",
            "OR": "ORTH", "OP": "OPHT", "EN": "ENT",  "DE": "DERM",
            "PS": "PSYC", "RD": "RADI", "AS": "ANES",
        }
```

### A.3 Replace Hardcoded Mappings

**Fix D7 — DoapService:**

```python
# services/snx-logbook/app/services/doap_service.py

# BEFORE (hardcoded):
def _infer_subject_code(self, competency_code: str) -> str:
    prefix = "".join(c for c in competency_code[:2] if c.isalpha()).upper()
    subject_map = {"AN": "ANAT", "PY": "PHYS", ...}  # hardcoded
    return subject_map.get(prefix, "UNKN")

# AFTER (MDM-driven):
async def _infer_subject_code(self, tenant_id: UUID, competency_code: str) -> str:
    mdm = MdmConfigService(self.session)
    mapping = await mdm.get_subject_code_mapping(tenant_id)
    prefix = "".join(c for c in competency_code[:2] if c.isalpha()).upper()
    subject_code = mapping.get(prefix)
    if not subject_code:
        import logging
        logging.warning("No subject_code mapping for prefix '%s'. Using 'UNKN'.", prefix)
    return subject_code or "UNKN"
```

Update all callers of `_infer_subject_code` to pass `tenant_id` and `await` the result.

**Fix D8 — LogbookService:**

```python
# services/snx-logbook/app/services/logbook_service.py

# BEFORE (hardcoded fallback):
async def _get_ia_config(self, tenant_id, subject_code, phase):
    config = await self.session.scalar(select(MdmConfig).where(...))
    if config and config.config_value:
        return (...)
    # Fallback defaults
    return Decimal("10.0"), Decimal("40.0")

# AFTER (using MdmConfigService):
async def _get_ia_config(self, tenant_id, subject_code, phase):
    mdm = MdmConfigService(self.session)
    return await mdm.get_ia_config(tenant_id, subject_code, phase)
```

### A.4 JMN Medical College MDM Seed Script

Create `scripts/admin/seed_jmn_mdm.py`:

```python
"""Seed MDM configuration for JMN Medical College."""
import asyncio
import json
from uuid import UUID
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.dialects.postgresql import insert

# JMN tenant_id — get from database or set as constant
JMN_TENANT_ID = UUID("...")  # Fill from actual DB

MDM_CONFIGS = [
    # Subject code mapping
    {
        "config_key": "competency.prefix_to_subject_code",
        "config_value": {
            "AN": "ANAT", "PY": "PHYS", "BI": "BIOC", "MI": "MICR",
            "PA": "PATH", "PH": "PHAR", "FM": "FMED", "CM": "CMED",
            "GM": "GMED", "GS": "GSUR", "OG": "OBGY", "PE": "PEDI",
            "OR": "ORTH", "OP": "OPHT", "EN": "ENT",  "DE": "DERM",
            "PS": "PSYC", "RD": "RADI", "AS": "ANES",
        },
        "description": "NMC CBME 2019 competency prefix → subject code mapping",
    },

    # IA configs per subject (Phase I subjects)
    *[
        {
            "config_key": f"ia_config.{subj}",
            "config_value": {"ia_weight_pct": 10.0, "subject_ia_max": 40.0},
            "description": f"IA configuration for {subj} (default 10% weight, 40 max marks)",
        }
        for subj in ["ANAT", "PHYS", "BIOC"]
    ],

    # IA configs (Phase II subjects — higher IA max for clinical)
    *[
        {
            "config_key": f"ia_config.{subj}",
            "config_value": {"ia_weight_pct": 15.0, "subject_ia_max": 60.0},
            "description": f"IA configuration for {subj} (15% weight, 60 max marks)",
        }
        for subj in ["PATH", "PHAR", "MICR", "FMED"]
    ],

    # Attendance thresholds (NMC defaults)
    *[
        {
            "config_key": f"attendance.threshold.{cat}",
            "config_value": threshold,
            "description": f"Attendance threshold for {cat} ({threshold}%)",
        }
        for cat, threshold in [
            ("theory", 75.00), ("practical", 80.00), ("clinical", 80.00),
            ("doap", 80.00), ("ece", 80.00), ("aetcom", 75.00),
            ("foundation_course", 75.00), ("elective", 75.00),
        ]
    ],

    # Elective allocation algorithm
    {
        "config_key": "elective.allocation_algorithm",
        "config_value": "ranked",
        "description": "Elective allocation algorithm: fcfs or ranked",
    },

    # Backdating thresholds
    {
        "config_key": "logbook.backdating.review_threshold_days",
        "config_value": 7,
        "description": "Logbook entries backdated more than N days require faculty review",
    },
    {
        "config_key": "logbook.backdating.hod_threshold_days",
        "config_value": 30,
        "description": "Logbook entries backdated more than N days route to HOD",
    },

    # Late attendance
    {
        "config_key": "attendance.late_threshold_minutes",
        "config_value": 15,
        "description": "Minutes after session start before marking as 'late'",
    },
    {
        "config_key": "attendance.late_counts_as_half",
        "config_value": False,
        "description": "Whether late arrival counts as 0.5 attendance",
    },

    # Correction window
    {
        "config_key": "attendance.correction_window_hours",
        "config_value": 24,
        "description": "Hours within which faculty can correct attendance without HOD approval",
    },
]


async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/synaptix_dev")
    async_session = async_sessionmaker(engine)

    async with async_session() as session:
        for config in MDM_CONFIGS:
            await session.execute(
                insert(MdmConfig)
                .values(
                    tenant_id=JMN_TENANT_ID,
                    config_key=config["config_key"],
                    config_value=json.dumps(config["config_value"]) if not isinstance(config["config_value"], str) else config["config_value"],
                    description=config["description"],
                )
                .on_conflict_do_update(
                    index_elements=["tenant_id", "config_key"],
                    set_={"config_value": config["config_value"], "description": config["description"]},
                )
            )
        await session.commit()
        print(f"Seeded {len(MDM_CONFIGS)} MDM configs for JMN Medical College")


if __name__ == "__main__":
    asyncio.run(main())
```

### A.5 Verify D7/D8 Resolution

Run existing DOAP and Logbook tests to confirm the MDM-driven approach doesn't break anything:

```powershell
pytest tests/unit/doap/ tests/unit/logbook/ tests/compliance/doap/ tests/compliance/logbook/ -v --tb=short
```

All must pass. If any break due to the refactor (missing MDM seed in test fixtures), update the `seed_deps` fixture to include MDM config rows.

### A.6 Phase A Acceptance

- [ ] `MdmConfigService` created in `packages/shared/mdm/`
- [ ] D7 fixed: `_infer_subject_code` reads from MDM
- [ ] D8 fixed: `_get_ia_config` reads from MDM
- [ ] `scripts/admin/seed_jmn_mdm.py` created and runs successfully
- [ ] All existing DOAP + Logbook tests still pass
- [ ] No hardcoded subject mappings or IA defaults remain in service code

---

## Phase B — 11 Deferred Tests Implementation (120-150 min)

These 11 tests were deferred to Phase 2.5 in Session 14. Now implement them.

### B.1 MDM Tests (4 tests)

Create or extend `tests/unit/mdm/test_mdm.py`:

**MDM-004:** Reference constraints on delete
```python
async def test_mdm_004_reference_constraint_on_delete(test_db_session, seed_deps):
    """MDM-004: Deleting a referenced MDM entry is blocked by FK constraints."""
    # Seed a config that's referenced by a course or attendance record
    # Attempt delete → assert IntegrityError
```

**MDM-005:** Medical onboarding templates
```python
async def test_mdm_005_medical_onboarding_templates(test_db_session, seed_deps):
    """MDM-005: Medical department onboarding templates exist in MDM seed."""
    mdm = MdmConfigService(test_db_session)
    template = await mdm.get(seed_deps.tenant.id, "onboarding.template.medical")
    assert template is not None
    assert "documents_required" in template
```

**MDM-006:** Nursing onboarding templates (same pattern)

**MDM-007:** CSV import validation
```python
async def test_mdm_007_csv_import_validation(test_db_session, seed_deps):
    """MDM-007: CSV import rejects malformed rows and reports line numbers."""
    # Test the CSV import utility (if it exists) or create a minimal one
    # Import a CSV with 3 valid rows and 2 invalid → assert 3 imported, 2 rejected with line numbers
```

### B.2 Calendar Edge Cases (5 tests)

Extend `tests/integration/test_calendar_engine.py`:

**CAL-E003:** Bulk event generation
```python
async def test_cal_e003_bulk_event_generation(test_db_session, seed_deps):
    """CAL-E003: Generate 30 recurring weekly events in one call."""
    service = CalendarService(test_db_session)
    events = await service.bulk_create_recurring(
        tenant_id=seed_deps.tenant.id,
        course_id=seed_deps.anatomy.id,
        recurrence="weekly",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 12, 31),
        day_of_week=1,  # Monday
        start_time=time(9, 0),
        end_time=time(10, 0),
    )
    assert len(events) >= 26  # ~26 Mondays in 6 months
    # Verify each event has correct date progression
    for i in range(1, len(events)):
        assert (events[i].event_date - events[i-1].event_date).days == 7
```

**CAL-E004:** Holiday conflict warning
```python
async def test_cal_e004_holiday_conflict_warning(test_db_session, seed_deps):
    """CAL-E004: Creating event on a holiday returns warning (not block)."""
    # Seed a holiday on 2026-08-15 (Independence Day)
    # Create event on 2026-08-15 → assert warning in response, event still created
```

**CAL-E005:** Faculty leave conflict
```python
async def test_cal_e005_faculty_leave_conflict(test_db_session, seed_deps):
    """CAL-E005: Event scheduled when assigned faculty has approved leave shows warning."""
    # Seed approved leave for faculty on date X
    # Create event on date X with that faculty → assert warning
```

**CAL-E006:** Room double-booking
```python
async def test_cal_e006_room_double_booking(test_db_session, seed_deps):
    """CAL-E006: Two events in same room at same time → rejected."""
    # Create event A in Room 101, 9-10am
    # Create event B in Room 101, 9:30-10:30am → assert conflict error
```

**CAL-E007:** Phase boundary validation
```python
async def test_cal_e007_phase_boundary_validation(test_db_session, seed_deps):
    """CAL-E007: Event date outside the course's professional phase boundary → warning."""
    # Course belongs to Phase I (dates Aug 2026 - Jul 2027)
    # Create event in Aug 2028 → assert warning about phase boundary
```

### B.3 Lesson Plan Edge Cases (2 tests)

Extend `tests/unit/academic/test_lesson_plan_versioning.py`:

**LPN-E001:** Older version retention
```python
async def test_lpn_e001_older_version_retains_conducted_sessions(test_db_session, seed_deps):
    """LPN-E001: When a lesson plan is versioned, conducted sessions reference the OLD version."""
    # Create lesson plan v1, link a conducted session to it
    # Create lesson plan v2 (v1.is_current=False, v2.is_current=True)
    # Verify the conducted session still references v1, not v2
    # Verify v1 is NOT deleted (retained for audit)
```

**LPN-E002:** Unapproved lesson plan warning
```python
async def test_lpn_e002_unapproved_plan_compliance_warning(test_db_session, seed_deps):
    """LPN-E002: Logging a session against an unapproved lesson plan generates compliance warning."""
    # Create lesson plan with status='draft' (not approved)
    # Log a conducted session referencing it → assert compliance_incidents row created
```

### B.4 Update COVERAGE_MANIFEST

For each of the 11 tests: remove the `deferred_to: "Phase 2.5"` line from the manifest entry (the test is now implemented, not deferred).

### B.5 Phase B Acceptance

```powershell
# Run all 11 newly-implemented tests
pytest tests/unit/mdm/ tests/integration/test_calendar_engine.py tests/unit/academic/test_lesson_plan_versioning.py -v -k "mdm_004 or mdm_005 or mdm_006 or mdm_007 or cal_e003 or cal_e004 or cal_e005 or cal_e006 or cal_e007 or lpn_e001 or lpn_e002"

# Verify manifest
python scripts/verify_coverage_manifest.py
```

- [ ] All 11 tests passing
- [ ] `deferred_to: "Phase 2.5"` removed from these 11 manifest entries
- [ ] Coverage manifest verifier passes

---

## Phase C — Verification + Handoff (20 min)

### C.1 Full Test Suite

```powershell
pytest tests/ -v --tb=short -q 2>&1 | Tee-Object docs/verification/phase25_tests_$(Get-Date -Format yyyyMMdd).txt
```

### C.2 All Verifiers

```powershell
python scripts/verify_coverage_manifest.py
python scripts/verify_adr_sequence.py
python scripts/verify_edge_case_coverage.py
python scripts/verify_compliance_coverage.py
python scripts/check_secrets.py
```

### C.3 Update Progress

```markdown
## Phase 2.5 Progress (Session 16)

- Tests passing before: 122
- Tests passing after: NN (target: 133 = 122 + 11)
- Technical debt resolved: D7, D8
- Deferred tests remaining: NN (should be 0 for Phase 2.5 category)
- Phase 2.5 status: 1 of 3 sessions complete
```

### C.4 Update Documentation

- `docs/CHANGELOG.md` — Session 16 entry
- `docs/HANDOFF_NOTES.md`:

```markdown
## Session 16 Complete (YYYY-MM-DD)

**Backend track:**
- D7 resolved: subject code mapping now MDM-driven
- D8 resolved: IA config now MDM-driven
- MDM seed script created for JMN Medical College
- 11 deferred tests implemented and passing
- MdmConfigService created as shared package

**Parallel frontend track:**
- Session F1 [status from frontend agent]

[TO: 02-backend] Session 17: Hardware attendance method stubs (RFID, GPS, biometric)
[TO: 03-frontend] Session F2: Attendance UI (mark attendance, view summaries)

[DEBT resolved] D7: Subject code mapping — CLOSED
[DEBT resolved] D8: IA config fallbacks — CLOSED
```

### C.5 Commit

```powershell
git add services/ packages/ scripts/ tests/ docs/
git commit -m "feat(mdm): Session 16 — Phase 2.5 MDM seeding + 11 deferred tests

- Created MdmConfigService in packages/shared/mdm/
- D7 resolved: DoapService._infer_subject_code now reads from MDM
- D8 resolved: LogbookService._get_ia_config now reads from MDM
- Created scripts/admin/seed_jmn_mdm.py with full JMN configuration
- Implemented 11 previously-deferred tests:
  MDM-004..007, CAL-E003..E007, LPN-E001..E002
- Removed deferred_to markers from 11 manifest entries
- All tests passing, all verifiers clean

Phase 2.5: 1/3 sessions complete.
Refs: Technical debt D7, D8
"
```

No `--no-verify`.

### C.6 Session End

```
SESSION END — Agent: 02-backend (Session 16)
Duration: ~X hours

Phase A: MDM infrastructure + D7/D8 resolution — COMPLETE
Phase B: 11 deferred tests implemented — ALL PASSING
Phase C: Verification + handoff — COMPLETE

Tests passing: NN (up from 122)
Deferred tests resolved: 11 (now 0 remaining for Phase 2.5 category)
Technical debt closed: D7, D8
MDM seed script: scripts/admin/seed_jmn_mdm.py

Next backend session (17): Hardware attendance stubs
Next frontend session (F2): Attendance UI

Phase 2.5: 1/3 sessions complete.
```

---

## Session 17 Preview (Backend — next after this)

Session 17 completes Phase 2.5 with hardware attendance method stubs:

- `AttendanceMethodHandler` interface
- RFID, GPS, biometric handler stubs with mock responses
- 17 deferred hardware tests implemented
- Phase 2.5 scorecard

## Session F2 Preview (Frontend — next after F1)

Session F2 connects the dashboard to real APIs:

- Faculty attendance marking page (student list, checkboxes, submit)
- Student attendance summary page (per-subject percentages)
- Dashboard stat cards populated from API calls
- React Query hooks for attendance endpoints