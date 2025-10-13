import pandas as pd
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
from src.domain import FIELDS


def check_policy_status(
    policy_data: Dict[str, Any], calculation_date: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    policy_expiry_date = policy_data.get(FIELDS["EXPIRY_DATE"])
    
    if calculation_date is None:
        calculation_date = datetime.now().strftime("%Y-%m-%d")
    
    is_policy_active = True
    inactive_reason = None
    
    if policy_expiry_date:
        try:
            expiry_dt = pd.to_datetime(policy_expiry_date)
            calc_dt = pd.to_datetime(calculation_date)
            
            if expiry_dt <= calc_dt:
                is_policy_active = False
                inactive_reason = f"Policy expired on {expiry_dt.date()} (calculation date: {calc_dt.date()})"
        except Exception as e:
            pass
    
    return is_policy_active, inactive_reason


def create_non_covered_result(
    policy_data: Dict[str, Any],
    exclusion_status: str,
    exclusion_reason: str
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

