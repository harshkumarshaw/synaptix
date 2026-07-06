from app.services.doap_validators import (
    validate_stage_progression,
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
