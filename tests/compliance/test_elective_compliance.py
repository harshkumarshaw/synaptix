"""
Elective NMC compliance test stubs — Session 9.

Tests ELEC-NMC-001..004 verify NMC CBME 2019/2023 Regulation 7 (Electives).
All stubs @pytest.mark.xfail — implementation delegated to Session 11-nmc-compliance agent.

Regulation refs:
  ELEC-NMC-001: NMC CBME Regulations 2019, Reg 7 — two blocks of 2 weeks (4 weeks total)
  ELEC-NMC-002: NMC CBME Regulations 2019, Reg 7 — at least one clinical category
  ELEC-NMC-003: NMC CBME Regulations 2019, Reg 7.5 — reflection mandatory per block
  ELEC-NMC-004: NMC CBME Regulations 2019, Reg 7.6 — faculty supervisor mandatory

Run with:
    PYTHONPATH=.:services/snx-logbook pytest tests/compliance/test_elective_compliance.py -v
"""

from __future__ import annotations

import uuid

import pytest


# ---------------------------------------------------------------------------
# ELEC-NMC-001: Elective duration — 2 blocks × 2 weeks = 4 weeks total
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=False,
    reason="ELEC-NMC-001: Elective duration enforcement not yet implemented — delegated to 11-nmc-compliance",
)
@pytest.mark.asyncio
async def test_elec_nmc_001_elective_duration_four_weeks() -> None:
    """
    ELEC-NMC-001: NMC CBME 2019 Reg 7 — Elective blocks must total 4 weeks (2 × 2 weeks).
    Validator must reject an elective configuration where block_duration_weeks != 2.
    """
    from app.services.elective_service import ElectiveService
    from app.schemas.electives import ElectiveCreate

    # Block duration = 1 week — must raise compliance error
    payload = ElectiveCreate(
        curriculum_id=uuid.uuid4(),
        code="ELEC-TEST-01",
        title="Test Elective",
        block="Block 1",
        elective_type="clinical",
        capacity=10,
        block_duration_weeks=1,  # violates NMC CBME 2019 Reg 7
    )
    # TODO (11-nmc-compliance): assert compliance validator raises NMC-ELEC-001
    assert False, "NMC compliance check not yet implemented"


# ---------------------------------------------------------------------------
# ELEC-NMC-002: At least one clinical-category elective required
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=False,
    reason="ELEC-NMC-002: Clinical elective requirement not yet implemented — delegated to 11-nmc-compliance",
)
@pytest.mark.asyncio
async def test_elec_nmc_002_at_least_one_clinical_elective() -> None:
    """
    ELEC-NMC-002: NMC CBME 2019 Reg 7 — Student must be allocated ≥1 clinical-category
    elective across Block 1 and Block 2 combined.
    """
    # TODO (11-nmc-compliance): create student with two non-clinical elective allocations,
    # call eligibility checker, assert SNX-NMC-ELEC-002 raised.
    assert False, "NMC compliance check not yet implemented"


# ---------------------------------------------------------------------------
# ELEC-NMC-003: Reflection entry mandatory per elective block
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=False,
    reason="ELEC-NMC-003: Reflection requirement check not yet implemented — delegated to 11-nmc-compliance",
)
@pytest.mark.asyncio
async def test_elec_nmc_003_reflection_required_per_block() -> None:
    """
    ELEC-NMC-003: NMC CBME 2019 Reg 7.5 — Student without a reflection logbook_entry
    for an allocated elective block is NOT eligible for NExT.
    """
    # TODO (11-nmc-compliance): create allocation with no logbook_entry (elective_id set),
    # call NExT eligibility check, assert blocked with reason ELEC-NMC-003.
    assert False, "NMC compliance check not yet implemented"


# ---------------------------------------------------------------------------
# ELEC-NMC-004: Faculty supervisor assigned per elective per student
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=False,
    reason="ELEC-NMC-004: Faculty supervisor requirement not yet implemented — delegated to 11-nmc-compliance",
)
@pytest.mark.asyncio
async def test_elec_nmc_004_faculty_supervisor_required() -> None:
    """
    ELEC-NMC-004: NMC CBME 2019 Reg 7.6 — Each elective allocation must have a
    supervisor_id assigned before the elective block can be certified complete.
    """
    # TODO (11-nmc-compliance): create allocation with supervisor_id=None,
    # call elective_certification_check, assert SNX-NMC-ELEC-004 raised.
    assert False, "NMC compliance check not yet implemented"
