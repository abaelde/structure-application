from typing import Dict
from src.domain import FIELDS
from src.domain.models import Program
from src.domain.policy import Policy
from .results import ProgramRunResult, RunTotals


def create_non_covered_result(
    policy: Policy, program: Program, exclusion_status: str, exclusion_reason: str
) -> ProgramRunResult:
    exposure = policy.exposure_bundle(program.underwriting_department).total
    
    # Créer un ProgramRunResult vide avec les métadonnées d'exclusion
    run_result = ProgramRunResult()
    
    # Ajouter les métadonnées d'exclusion au résultat
    run_result.exclusion_status = exclusion_status
    run_result.exclusion_reason = exclusion_reason
    run_result.exposure = exposure
    run_result.effective_exposure = 0.0  # Pour les politiques inactives/exclues, effective_exposure = 0
    run_result.insured_name = policy.get(FIELDS["INSURED_NAME"])
    run_result.policy_inception_date = policy.get(FIELDS["INCEPTION_DATE"])
    run_result.policy_expiry_date = policy.get(FIELDS["EXPIRY_DATE"])
    
    return run_result


def create_inactive_result(
    policy: Policy, program: Program, inactive_reason: str
) -> ProgramRunResult:
    return create_non_covered_result(policy, program, "inactive", inactive_reason)


def create_excluded_result(policy: Policy, program: Program) -> ProgramRunResult:
    return create_non_covered_result(policy, program, "excluded", "Matched exclusion rule")
