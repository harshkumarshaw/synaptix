import pytest


class TestExamModeration:
    @pytest.mark.xfail(reason="RES-005: Implementation pending Phase 3 R4")
    async def test_res_005_two_examiners(self, test_db_session):
        """
        Test ID: RES-005
        Module: exam_results
        Verifies: Multi-examiner moderation: average of two if <=15% diff.
        """
        raise NotImplementedError("Stub")

    @pytest.mark.xfail(reason="RES-006: Implementation pending Phase 3 R4")
    async def test_res_006_three_examiners(self, test_db_session):
        """
        Test ID: RES-006
        Module: exam_results
        Verifies: Multi-examiner moderation: third examiner if >15% diff.
        """
        raise NotImplementedError("Stub")

    @pytest.mark.xfail(reason="RES-009: Implementation pending Phase 3 R4")
    async def test_res_009_grace_marks_limits(self, test_db_session):
        """
        Test ID: RES-009
        Module: exam_results
        Verifies: Grace marks policy: up to 5 marks applied automatically.
        """
        raise NotImplementedError("Stub")
