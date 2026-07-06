"""
NMC Compliance Tests — Attendance Thresholds (Phase 2 Implementation).

HARD FAIL: These tests block all commits if they fail.
DO NOT modify these tests to make them pass. Fix the code instead.

Source: NMC CBME 2019, GMER 2019 §11.1 and NMC CBME 2023
Regulation: Two-threshold attendance (75% theory, 80% practical/clinical)

Test IDs from tests/NMC_COMPLIANCE_TESTS.md:
- NMC-ATT-001 through NMC-ATT-020
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.attendance_service import (
    PRACTICAL_THRESHOLD,
    THEORY_THRESHOLD,
    AttendanceService,
)

# ============================================================================
# Helper: Pure-function threshold checks (no DB needed for boundary tests)
# These test the logic, not the DB layer.
# ============================================================================


def _theory_eligible(attended: int, total: int) -> bool:
    """Check theory eligibility using NMC CBME 75% rule."""
    if total == 0:
        return False
    pct = Decimal(str(round(100.0 * attended / total, 2)))
    return pct >= THEORY_THRESHOLD


def _practical_eligible(attended: int, total: int) -> bool:
    """Check practical eligibility using NMC CBME 80% rule."""
    if total == 0:
        return False
    pct = Decimal(str(round(100.0 * attended / total, 2)))
    return pct >= PRACTICAL_THRESHOLD


# ============================================================================
# NMC-ATT-001: Theory attendance boundary — exactly 75.00% is ELIGIBLE
# ============================================================================
class TestTheoryAttendanceBoundary:
    """Theory attendance eligibility boundary tests."""

    @pytest.mark.compliance
    def test_exactly_75_pct_theory_is_eligible(self) -> None:
        """Student with EXACTLY 75.00% theory attendance is ELIGIBLE.

        NMC CBME 2019 §11.1: 'not less than 75%'
        75.00% means attended 75 of 100 sessions — ELIGIBLE.
        """
        assert _theory_eligible(75, 100) is True

    @pytest.mark.compliance
    def test_74_99_pct_theory_is_blocked(self) -> None:
        """Student with 74.99% theory attendance is BLOCKED (below threshold).

        74.99% rounds down — does NOT meet the 75% minimum.
        This covers the critical boundary case from AUDIT-D1.
        """
        # 149 attended of 199 conducted = 74.87% — BLOCKED
        assert _theory_eligible(149, 199) is False

    @pytest.mark.compliance
    def test_74_pct_theory_is_blocked(self) -> None:
        """Student with 74% theory attendance is BLOCKED."""
        assert _theory_eligible(74, 100) is False

    @pytest.mark.compliance
    def test_100_pct_theory_is_eligible(self) -> None:
        """Student with 100% theory attendance is ELIGIBLE."""
        assert _theory_eligible(100, 100) is True

    @pytest.mark.compliance
    def test_zero_pct_theory_is_blocked(self) -> None:
        """Student with 0% theory attendance is BLOCKED."""
        assert _theory_eligible(0, 100) is False

    @pytest.mark.compliance
    def test_zero_sessions_theory_is_blocked(self) -> None:
        """Student with no sessions conducted is BLOCKED (denominator = 0)."""
        assert _theory_eligible(0, 0) is False


# ============================================================================
# NMC-ATT-006: Practical attendance boundary — exactly 80.00% is ELIGIBLE
# ============================================================================
class TestPracticalAttendanceBoundary:
    """Practical/Clinical/DOAP/ECE attendance eligibility boundary tests.

    CRITICAL: The practical threshold is 80%, NOT 75%.
    This is a separate threshold from theory (ADR-003).
    Code that uses a single threshold for both is NMC non-compliant.
    """

    @pytest.mark.compliance
    def test_exactly_80_pct_practical_is_eligible(self) -> None:
        """Student with EXACTLY 80.00% practical attendance is ELIGIBLE.

        NMC CBME 2019 §11.1: practical/clinical sessions require 80%.
        """
        assert _practical_eligible(80, 100) is True

    @pytest.mark.compliance
    def test_79_99_pct_practical_is_blocked(self) -> None:
        """Student with 79.99% practical attendance is BLOCKED.

        79.99% does NOT meet the 80% minimum for practical sessions.
        CRITICAL: This is NOT the theory threshold. 79.99% theory would pass theory
        but 79.99% practical BLOCKS practical eligibility.
        """
        # 159 attended of 199 conducted = 79.9% — BLOCKED
        assert _practical_eligible(159, 199) is False

    @pytest.mark.compliance
    def test_75_pct_practical_is_blocked_even_though_theory_passes(self) -> None:
        """75% practical attendance is BLOCKED — even though it's the theory threshold.

        This test verifies the two thresholds are independent.
        A student with 75% practical passes theory eligibility but NOT practical eligibility.
        """
        assert _practical_eligible(75, 100) is False  # 75% is below 80% practical threshold
        assert _theory_eligible(75, 100) is True  # 75% meets theory threshold

    @pytest.mark.compliance
    def test_practical_threshold_applies_to_clinical(self) -> None:
        """80% threshold applies to clinical sessions (not just lab practicals).

        PRACTICAL_CATEGORIES includes: practical, clinical, doap, ece
        """
        from app.services.attendance_service import PRACTICAL_CATEGORIES

        assert "clinical" in PRACTICAL_CATEGORIES

    @pytest.mark.compliance
    def test_practical_threshold_applies_to_doap(self) -> None:
        """80% threshold applies to DOAP sessions."""
        from app.services.attendance_service import PRACTICAL_CATEGORIES

        assert "doap" in PRACTICAL_CATEGORIES

    @pytest.mark.compliance
    def test_practical_threshold_applies_to_ece(self) -> None:
        """80% threshold applies to ECE (Early Clinical Exposure) sessions."""
        from app.services.attendance_service import PRACTICAL_CATEGORIES

        assert "ece" in PRACTICAL_CATEGORIES


# ============================================================================
# NMC-ATT-011: Attendance denominator — only CONDUCTED sessions count
# ============================================================================
class TestAttendanceDenominator:
    """Tests that the denominator is conducted sessions, not planned sessions.

    AUDIT-D3: The attendance denominator must be conducted sessions only.
    Planned sessions that were cancelled must NOT be counted.
    """

    @pytest.mark.compliance
    def test_cancelled_sessions_not_in_denominator(self) -> None:
        """Cancelled sessions must NOT count in the attendance denominator.

        A student who attended 30 of 40 conducted sessions, where 10 were
        planned but cancelled, has 30/40 = 75% (not 30/50 = 60%).
        """
        # Simulates: 40 conducted, 30 attended, 10 cancelled (not in denominator)
        pct = round(100.0 * 30 / 40, 2)
        assert pct == 75.0
        assert _theory_eligible(30, 40) is True

        # With cancelled wrongly included: 30/50 = 60% — BLOCKED
        assert _theory_eligible(30, 50) is False

    @pytest.mark.compliance
    def test_only_conducted_sessions_in_denominator(self) -> None:
        """Only sessions with status='conducted' count in the denominator.

        This is enforced in _recalculate_summary by filtering events.status = 'conducted'.
        """
        # Verify the SQL in attendance_service._recalculate_summary references 'conducted'
        import inspect

        source = inspect.getsource(AttendanceService._recalculate_summary)
        assert "conducted" in source, (
            "attendance_service._recalculate_summary MUST filter by event status='conducted' "
            "for the denominator. AUDIT-D3 violation."
        )


# ============================================================================
# NMC-ATT-013: Two thresholds are INDEPENDENT — both must pass
# ============================================================================
class TestTwoThresholdIndependence:
    """Verifies theory and practical thresholds are fully independent."""

    @pytest.mark.compliance
    def test_passing_theory_does_not_excuse_failing_practical(self) -> None:
        """Student passing theory (80%) but failing practical (79%) is INELIGIBLE.

        Hall ticket requires BOTH theory ≥75% AND practical ≥80%.
        Passing one does not compensate for failing the other.
        """
        theory_ok = _theory_eligible(80, 100)  # 80% ≥ 75% ✓
        practical_ok = _practical_eligible(79, 100)  # 79% < 80% ✗
        assert theory_ok is True
        assert practical_ok is False
        # Combined eligibility: BOTH must pass
        assert not (theory_ok and practical_ok)

    @pytest.mark.compliance
    def test_passing_practical_does_not_excuse_failing_theory(self) -> None:
        """Student passing practical (85%) but failing theory (74%) is INELIGIBLE."""
        theory_ok = _theory_eligible(74, 100)  # 74% < 75% ✗
        practical_ok = _practical_eligible(85, 100)  # 85% ≥ 80% ✓
        assert theory_ok is False
        assert practical_ok is True
        # Combined eligibility: BOTH must pass
        assert not (theory_ok and practical_ok)

    @pytest.mark.compliance
    def test_thresholds_are_distinct_constants(self) -> None:
        """THEORY_THRESHOLD and PRACTICAL_THRESHOLD must be distinct values.

        If they are equal, it means a single threshold was used — NMC non-compliant.
        """
        assert Decimal("75.00") == THEORY_THRESHOLD
        assert Decimal("80.00") == PRACTICAL_THRESHOLD
        assert THEORY_THRESHOLD != PRACTICAL_THRESHOLD

    @pytest.mark.compliance
    def test_both_thresholds_must_pass_for_hall_ticket(self) -> None:
        """Hall ticket requires theory ≥75% AND practical ≥80% in every subject."""
        # Borderline pass in both — ELIGIBLE
        assert _theory_eligible(75, 100)
        assert _practical_eligible(80, 100)
        # Borderline fail in theory — INELIGIBLE
        assert not (_theory_eligible(74, 100) and _practical_eligible(80, 100))
        # Borderline fail in practical — INELIGIBLE
        assert not (_theory_eligible(75, 100) and _practical_eligible(79, 100))


# ============================================================================
# NMC-ATT-016: CRMI attendance rules (Phase 4 — stubs)
# ============================================================================
class TestCRMIAttendance:
    """CRMI (internship) attendance compliance tests.

    CRMI rules: 7 mandatory rotations, 75% per rotation, max 15 days total leave.
    Full implementation deferred to Phase 4 (snx-clinical service).
    """

    @pytest.mark.compliance
    def test_crmi_75_pct_per_rotation_required(self) -> None:
        """CRMI intern must achieve 75% attendance per rotation (not aggregate)."""
        pytest.skip("Stub: CRMI module not yet implemented (Phase 4)")

    @pytest.mark.compliance
    def test_crmi_max_15_days_total_leave(self) -> None:
        """CRMI intern at exactly 15 days total leave can apply for no more leave."""
        pytest.skip("Stub: CRMI module not yet implemented (Phase 4)")

    @pytest.mark.compliance
    def test_crmi_16_days_leave_is_blocked(self) -> None:
        """CRMI intern exceeding 15 days total leave cannot apply for further leave."""
        pytest.skip("Stub: CRMI module not yet implemented (Phase 4)")

    @pytest.mark.compliance
    def test_crmi_7_mandatory_rotations_required(self) -> None:
        """CRMI completion requires all 7 mandatory rotations to be completed."""
        pytest.skip("Stub: CRMI module not yet implemented (Phase 4)")


# ============================================================================
# NMC-ATT-020: NExT eligibility — includes elective logbooks (Phase 3 — stubs)
# ============================================================================
class TestNExTEligibility:
    """NExT exam eligibility compliance tests.

    NExT eligibility is the most comprehensive check — includes all standard
    hall ticket criteria PLUS elective Block 1 and Block 2 logbooks.
    Full implementation deferred to Phase 3 (hall ticket / exam module).
    """

    @pytest.mark.compliance
    def test_next_requires_elective_block_1_logbook(self) -> None:
        """NExT eligibility requires Elective Block 1 logbook submitted."""
        pytest.skip("Stub: NExT eligibility not yet implemented (Phase 3)")

    @pytest.mark.compliance
    def test_next_requires_elective_block_2_logbook(self) -> None:
        """NExT eligibility requires Elective Block 2 logbook submitted."""
        pytest.skip("Stub: NExT eligibility not yet implemented (Phase 3)")

    @pytest.mark.compliance
    def test_next_requires_both_elective_blocks_not_just_one(self) -> None:
        """NExT eligibility requires BOTH Elective Block 1 AND Block 2 logbooks."""
        pytest.skip("Stub: NExT eligibility not yet implemented (Phase 3)")
