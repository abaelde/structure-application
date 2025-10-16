from typing import Dict
from src.domain import FIELDS
from src.domain.models import Program
from src.domain.policy import Policy


def create_non_covered_result(
    policy: Policy, program: Program, exclusion_status: str, exclusion_reason: str
) -> Dict[str, any]:
    exposure = policy.exposure_bundle(program.underwriting_department).total

    return {
        FIELDS["INSURED_NAME"]: policy.get(FIELDS["INSURED_NAME"]),
        "exposure": exposure,
        "effective_exposure": 0.0,
        "cession_to_layer_100pct": 0.0,
        "cession_to_reinsurer": 0.0,
        "retained_by_cedant": 0.0,
        "policy_inception_date": policy.get(FIELDS["INCEPTION_DATE"]),
        "policy_expiry_date": policy.get(FIELDS["EXPIRY_DATE"]),
        "structures_detail": [],
        "exclusion_status": exclusion_status,
        "exclusion_reason": exclusion_reason,
    }


def create_inactive_result(
    policy: Policy, program: Program, inactive_reason: str
) -> Dict[str, any]:
    return create_non_covered_result(policy, program, "inactive", inactive_reason)


def create_excluded_result(policy: Policy, program: Program) -> Dict[str, any]:
    return create_non_covered_result(policy, program, "excluded", "Matched exclusion rule")
