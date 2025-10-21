from typing import Dict
from src.domain import Program

# FIELDS supprimé - utilisation directe des clés canoniques
from src.domain.policy import Policy
from .exclusion_matcher import check_program_exclusions
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

    is_excl, reason = check_program_exclusions(
        policy, program, calculation_date=calculation_date
    )
    if is_excl:
        res = create_excluded_result(policy, program)
        res.exclusion_reason = reason
        return res

    run = StructureProcessor(
        policy, program, calculation_date=calculation_date
    ).process_structures()

    exposure = policy.exposure_bundle(program.underwriting_department).total

    # Enrichir le ProgramRunResult avec les métadonnées de la politique
    run.exposure = exposure
    run.effective_exposure = exposure
    run.insured_name = policy.get("INSURED_NAME")
    run.policy_inception_date = policy.get("INCEPTION_DT")
    run.policy_expiry_date = policy.get("EXPIRE_DT")
    run.exclusion_status = "included"

    return run
