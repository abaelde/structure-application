from typing import Dict, Any, Optional
from src.domain import FIELDS, Program
from .section_matcher import check_exclusion
from .policy_lifecycle import check_policy_status, create_inactive_result, create_excluded_result
from .structure_orchestrator import process_structures


def apply_program(
    policy_data: Dict[str, Any], program: Program, calculation_date: Optional[str] = None
) -> Dict[str, Any]:
    exposure = policy_data.get(FIELDS["EXPOSURE"])
    structures = program.structures
    dimension_columns = program.dimension_columns
    
    is_policy_active, inactive_reason = check_policy_status(policy_data, calculation_date)
    
    if not is_policy_active:
        return create_inactive_result(policy_data, inactive_reason)
    
    is_excluded = check_exclusion(policy_data, program.all_sections, dimension_columns)
    
    if is_excluded:
        return create_excluded_result(policy_data)

    structures_detail, total_cession_to_layer_100pct, total_cession_to_reinsurer = process_structures(
        structures, policy_data, dimension_columns, exposure
    )

    return {
        FIELDS["INSURED_NAME"]: policy_data.get(FIELDS["INSURED_NAME"]),
        "exposure": exposure,
        "effective_exposure": exposure,
        "cession_to_layer_100pct": total_cession_to_layer_100pct,
        "cession_to_reinsurer": total_cession_to_reinsurer,
        "retained_by_cedant": exposure - total_cession_to_layer_100pct,
        "policy_inception_date": policy_data.get(FIELDS["INCEPTION_DATE"]),
        "policy_expiry_date": policy_data.get(FIELDS["EXPIRY_DATE"]),
        "structures_detail": structures_detail,
        "exclusion_status": "included",
    }



