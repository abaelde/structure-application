from typing import Dict
from src.domain import FIELDS, Program
from src.domain.policy import Policy
from .condition_matcher import check_exclusion
from .policy_lifecycle import (
    create_inactive_result,
    create_excluded_result,
)
from .structure_orchestrator import StructureProcessor
from .results import ProgramRunResult


def apply_program(
    policy: Policy,
    program: Program,
    calculation_date: str,
) -> ProgramRunResult:

    is_policy_active, inactive_reason = policy.is_active(calculation_date)
    if not is_policy_active:
        return create_inactive_result(policy, program, inactive_reason)

    if check_exclusion(
        policy,
        program.all_conditions,
        program.dimension_columns,
    ):
        return create_excluded_result(policy, program)

    run = StructureProcessor(policy, program).process_structures()

    exposure = policy.exposure_bundle(program.underwriting_department).total
    
    # Enrichir le ProgramRunResult avec les métadonnées de la politique
    run.exposure = exposure
    run.effective_exposure = exposure
    run.insured_name = policy.get(FIELDS["INSURED_NAME"])
    run.policy_inception_date = policy.get(FIELDS["INCEPTION_DATE"])
    run.policy_expiry_date = policy.get(FIELDS["EXPIRY_DATE"])
    run.exclusion_status = "included"
    
    return run
