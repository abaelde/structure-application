from typing import List, Optional
from src.domain.program import Program
from src.domain.structure import Structure
from src.domain.exclusion import ExclusionRule
from src.domain.schema import PROGRAM_TO_BORDEREAU_DIMENSIONS


def build_program(
    name: str,
    structures: List[Structure],
    dimension_columns: Optional[List[str]] = None,
    underwriting_department: str = "test",
    exclusions: Optional[List[ExclusionRule]] = None,
) -> Program:
    """
    Build a Program object directly in memory.

    Args:
        name: Program name
        structures: List of Structure objects
        dimension_columns: List of dimension column names.
            If None, uses the default dimensions from PROGRAM_TO_BORDEREAU_DIMENSIONS.
        underwriting_department: Underwriting department (defaults to "test" for tests)
        exclusions: List of ExclusionRule objects for program-level exclusions

    Returns:
        Program object ready to use

    Example:
        qs = build_quota_share(name="QS_30", cession_pct=0.30)
        exclusions = [
            ExclusionRule(
                values_by_dimension={"BUSCL_COUNTRY_CD": ["Iran"]}, 
                name="Sanctions Iran"
            )
        ]
        program = build_program(
            name="SINGLE_QS_2024",
            structures=[qs],
            underwriting_department="aviation",
            exclusions=exclusions
        )
    """
    if dimension_columns is None:
        # Utilise uniquement le schéma comme source de vérité pour les dimensions
        dimension_columns = sorted(PROGRAM_TO_BORDEREAU_DIMENSIONS.keys())

    return Program(
        name=name,
        structures=structures,
        dimension_columns=dimension_columns,
        underwriting_department=underwriting_department,
        exclusions=exclusions or [],
    )
