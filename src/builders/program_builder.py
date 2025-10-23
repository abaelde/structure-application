from typing import List, Optional
from src.domain.program import Program
from src.domain.structure import Structure
from src.domain.exclusion import ExclusionRule
# Plus besoin d'importer le mapping Snowflake pour la construction en mémoire


def build_program(
    name: str,
    structures: List[Structure],
    main_currency: str,
    dimension_columns: Optional[List[str]] = None,
    underwriting_department: str = "test",
    exclusions: Optional[List[ExclusionRule]] = None,
) -> Program:
    """
    Build a Program object directly in memory.

    Args:
        name: Program name
        structures: List of Structure objects
        main_currency: Main currency of the program (required). Validates
            that policies match this currency unless a specific condition allows otherwise.
        dimension_columns: List of dimension column names.
            If None, uses the default dimensions from PROGRAM_TO_SNOWFLAKE_COLUMNS.
        underwriting_department: Underwriting department (defaults to "test" for tests)
        exclusions: List of ExclusionRule objects for program-level exclusions

    Returns:
        Program object ready to use

    Example:
        qs = build_quota_share(name="QS_30", cession_pct=0.30)
        exclusions = [
            ExclusionRule(
                values_by_dimension={"COUNTRY": ["Iran"]},
                name="Sanctions Iran"
            )
        ]
        program = build_program(
            name="SINGLE_QS_2024",
            structures=[qs],
            main_currency="EUR",
            underwriting_department="aviation",
            exclusions=exclusions
        )
    """
    if dimension_columns is None:
        # Utilise les dimensions standard utilisées dans les conditions
        dimension_columns = [
            "COUNTRIES",
            "REGIONS", 
            "CURRENCY",
            "PRODUCT_TYPE_LEVEL_1",
            "PRODUCT_TYPE_LEVEL_2",
            "PRODUCT_TYPE_LEVEL_3"
        ]

    return Program(
        name=name,
        structures=structures,
        dimension_columns=dimension_columns,
        underwriting_department=underwriting_department,
        main_currency=main_currency,
        exclusions=exclusions or [],
    )
