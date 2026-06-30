from app.services.doap_validators import validate_rating_decision


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
