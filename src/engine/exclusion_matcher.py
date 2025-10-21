from typing import Optional
from src.domain.program import Program
from src.domain.policy import Policy

def check_program_exclusions(policy: Policy, program: Program, *, calculation_date: Optional[str] = None) -> tuple[bool, Optional[str]]:
    """
    Returns (is_excluded, reason)
    """
    if not program.exclusions:
        return False, None

    mapping = program.dimension_columns  # program dimensions (logical names)
    # Build a dict {dim -> dim} (already logical) for ExclusionRule.matches signature
    dim_map = {d: d for d in mapping}

    for rule in program.exclusions:
        if rule.matches(policy, dim_map, calculation_date=calculation_date):
            return True, rule.name or "Matched exclusion rule"
    return False, None
