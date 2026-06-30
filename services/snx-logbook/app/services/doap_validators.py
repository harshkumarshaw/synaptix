"""DOAP state machine validators (pure functions, no DB)."""

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
    # Any attempt at D is always allowed.
    # If the stage is lower than the highest certified stage, it's a refresher, hence allowed.
    highest_certified_idx = -1
    for stage in certified_stages:
        if stage in STAGE_ORDER:
            highest_certified_idx = max(highest_certified_idx, STAGE_ORDER.index(stage))

    if proposed_idx == 0 or proposed_idx < highest_certified_idx:
        return ValidationResult.ok()

    # Re-attempts (R, Re attempt types) at a stage already attempted/certified: allowed
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
            f"{'is' if len(missing_sorted) == 1 else 'are'} certified.",
        )

    return ValidationResult.ok()


def validate_rating_decision(rating: str, decision: str) -> ValidationResult:
    """
    Validate rating-decision consistency.

    Rule per ADR-035:
    - Rating B (Below) -> decision must be R or Re (NOT C)
    - Rating M (Meets) -> typically C (allowed: any)
    - Rating E (Exceeds) -> typically C (allowed: any)

    DOAP-NMC-003 compliance.
    """
    if rating == "B" and decision == "C":
        return ValidationResult.error(
            "DOAP-002",
            "Rating B (Below expectation) cannot have decision C (Certify). "
            "Use R (Repeat) or Re (Remediate).",
        )
    return ValidationResult.ok()


def compute_certified_stages(records: list) -> set[str]:
    """
    Given a list of DoapSessionRecord ORM objects (or dict-like), return the set of
    stages where the student has at least one C-decision record.
    """
    certified = set()
    for record in records:
        # Support both ORM and dict/object access
        stage = getattr(record, "stage", None)
        if stage is None and isinstance(record, dict):
            stage = record.get("stage")
        elif stage is None:
            # Maybe schema object
            stage = getattr(record, "stage", None)

        decision = getattr(record, "faculty_decision", None)
        if decision is None and isinstance(record, dict):
            decision = record.get("faculty_decision")
        elif decision is None:
            # Maybe schema object
            decision = getattr(record, "faculty_decision", None)

        if decision == "C" and stage:
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
        return "demonstrated"  # D certified or some certified but not all
    else:
        return "not_started"
