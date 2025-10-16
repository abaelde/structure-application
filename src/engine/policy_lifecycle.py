import pandas as pd
from typing import Dict, Any, Tuple, Optional
from src.domain import FIELDS
from src.domain.policy import Policy


def check_policy_status(
    policy: Policy, calculation_date: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    return policy.is_active(calculation_date)


def create_non_covered_result(
    policy_data: Dict[str, Any], exclusion_status: str, exclusion_reason: str
) -> Dict[str, Any]:
    exposure = policy_data.get(FIELDS["EXPOSURE"])

    return {
        FIELDS["INSURED_NAME"]: policy_data.get(FIELDS["INSURED_NAME"]),
        "exposure": exposure,
        "effective_exposure": 0.0,
        "cession_to_layer_100pct": 0.0,
        "cession_to_reinsurer": 0.0,
        "retained_by_cedant": 0.0,
        "policy_inception_date": policy_data.get(FIELDS["INCEPTION_DATE"]),
        "policy_expiry_date": policy_data.get(FIELDS["EXPIRY_DATE"]),
        "structures_detail": [],
        "exclusion_status": exclusion_status,
        "exclusion_reason": exclusion_reason,
    }


def create_inactive_result(
    policy_data: Dict[str, Any], inactive_reason: str
) -> Dict[str, Any]:
    return create_non_covered_result(policy_data, "inactive", inactive_reason)


def create_excluded_result(policy_data: Dict[str, Any]) -> Dict[str, Any]:
    return create_non_covered_result(policy_data, "excluded", "Matched exclusion rule")
