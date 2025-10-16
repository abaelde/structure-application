from typing import Dict
from src.domain import FIELDS, Program
from src.domain.policy import Policy
from .condition_matcher import check_exclusion
from .policy_lifecycle import (
    create_inactive_result,
    create_excluded_result,
)
from .structure_orchestrator import process_structures


def apply_program(
    policy: Policy,
    program: Program,
    calculation_date: str,
) -> Dict[str, any]:
    # Exposition (et composants) calculés côté Policy
    components = policy.exposure_components(program.underwriting_department)
    exposure = components.total
    structures = program.structures
    dimension_columns = program.dimension_columns

    is_policy_active, inactive_reason = policy.is_active(calculation_date)

    if not is_policy_active:
        return create_inactive_result(policy.raw, inactive_reason)

    if check_exclusion(policy, program.all_conditions, dimension_columns, program.underwriting_department):
        return create_excluded_result(policy.raw)

    structures_detail, total_cession_to_layer_100pct, total_cession_to_reinsurer = (
        process_structures(structures, policy, dimension_columns, exposure, program.underwriting_department)
    )

    return {
        FIELDS["INSURED_NAME"]: policy.get(FIELDS["INSURED_NAME"]),
        "exposure": exposure,
        "effective_exposure": exposure,
        "cession_to_layer_100pct": total_cession_to_layer_100pct,
        "cession_to_reinsurer": total_cession_to_reinsurer,
        "retained_by_cedant": exposure - total_cession_to_layer_100pct,
        "policy_inception_date": policy.get(FIELDS["INCEPTION_DATE"]),
        "policy_expiry_date": policy.get(FIELDS["EXPIRY_DATE"]),
        "structures_detail": structures_detail,
        "exclusion_status": "included",
    }
