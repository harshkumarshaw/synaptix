import pytest


class TestExamGrading:
    @pytest.mark.xfail(reason="RES-001: Implementation pending Phase 3 R4")
    async def test_res_001_distinction(self, test_db_session):
        """
        Test ID: RES-001
        Module: exam_results
        Verifies: Grading: Distinction (>=75%) calculation.
        """
        raise NotImplementedError("Stub")

    @pytest.mark.xfail(reason="RES-002: Implementation pending Phase 3 R4")
    async def test_res_002_pass(self, test_db_session):
        """
        Test ID: RES-002
        Module: exam_results
        Verifies: Grading: Pass (50%-74%) calculation.
        """
        raise NotImplementedError("Stub")

    @pytest.mark.xfail(reason="RES-003: Implementation pending Phase 3 R4")
    async def test_res_003_fail(self, test_db_session):
        """
        Test ID: RES-003
        Module: exam_results
        Verifies: Grading: Fail (<50%) calculation.
        """
        raise NotImplementedError("Stub")

    @pytest.mark.xfail(reason="RES-004: Implementation pending Phase 3 R4")
    async def test_res_004_independent_pass(self, test_db_session):
        """
        Test ID: RES-004
        Module: exam_results
        Verifies: Theory and practical parts evaluated and passed independently.
        """
        raise NotImplementedError("Stub")

    @pytest.mark.xfail(reason="EXM-010: Implementation pending Phase 3 R4")
    async def test_exm_010_grace_marks(self, test_db_session):
        """
        Test ID: EXM-010
        Module: examination_management
        Verifies: Grace marks policy correctly applied.
        """
        raise NotImplementedError("Stub")
