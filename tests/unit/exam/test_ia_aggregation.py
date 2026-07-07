import pytest


class TestIAAggregation:
    @pytest.mark.xfail(reason="IA-001: Implementation pending Phase 3 R4")
    async def test_ia_001_logbook_contribution(self, test_db_session):
        """
        Test ID: IA-001
        Module: ia_aggregation
        Verifies: Logbook completion IA contribution (up to 20%).
        """
        raise NotImplementedError("Stub")

    @pytest.mark.xfail(reason="IA-002: Implementation pending Phase 3 R4")
    async def test_ia_002_viva_contribution(self, test_db_session):
        """
        Test ID: IA-002
        Module: ia_aggregation
        Verifies: Viva scores IA contribution (30%).
        """
        raise NotImplementedError("Stub")

    @pytest.mark.xfail(reason="IA-003: Implementation pending Phase 3 R4")
    async def test_ia_003_practical_contribution(self, test_db_session):
        """
        Test ID: IA-003
        Module: ia_aggregation
        Verifies: Practical exam scores IA contribution (30%).
        """
        raise NotImplementedError("Stub")

    @pytest.mark.xfail(reason="IA-004: Implementation pending Phase 3 R4")
    async def test_ia_004_clinical_contribution(self, test_db_session):
        """
        Test ID: IA-004
        Module: ia_aggregation
        Verifies: Clinical posting evaluation IA contribution (20%).
        """
        raise NotImplementedError("Stub")

    @pytest.mark.xfail(reason="IA-005: Implementation pending Phase 3 R4")
    async def test_ia_005_mdm_weights(self, test_db_session):
        """
        Test ID: IA-005
        Module: ia_aggregation
        Verifies: MDM configuration of subject-specific weights.
        """
        raise NotImplementedError("Stub")

    @pytest.mark.xfail(reason="IA-006: Implementation pending Phase 3 R4")
    async def test_ia_006_capping_validation(self, test_db_session):
        """
        Test ID: IA-006
        Module: ia_aggregation
        Verifies: Capping total IA contribution at 20% validation.
        """
        raise NotImplementedError("Stub")

    @pytest.mark.xfail(reason="IA-007: Implementation pending Phase 3 R4")
    async def test_ia_007_aggregate_batch(self, test_db_session):
        """
        Test ID: IA-007
        Module: ia_aggregation
        Verifies: Aggregate IA calculations for whole batch.
        """
        raise NotImplementedError("Stub")

    @pytest.mark.xfail(reason="IA-008: Implementation pending Phase 3 R4")
    async def test_ia_008_missing_marks_zero(self, test_db_session):
        """
        Test ID: IA-008
        Module: ia_aggregation
        Verifies: Missing sub-component marks treated as zero in aggregation.
        """
        raise NotImplementedError("Stub")

    @pytest.mark.xfail(reason="IA-010: Implementation pending Phase 3 R4")
    async def test_ia_010_historical_records_retained(self, test_db_session):
        """
        Test ID: IA-010
        Module: ia_aggregation
        Verifies: Historical IA records retained on re-calculation.
        """
        raise NotImplementedError("Stub")
