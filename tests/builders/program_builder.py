from typing import List, Optional
from src.domain.models import Program, Structure
from src.domain.constants import DIMENSIONS
from src.domain.schema import PROGRAM_TO_BORDEREAU_DIMENSIONS


def build_program(
    name: str,
    structures: List[Structure],
    dimension_columns: Optional[List[str]] = None,
    underwriting_department: str = "test",
) -> Program:
    """
    Build a Program object directly in memory.

    Args:
        name: Program name
        structures: List of Structure objects
        dimension_columns: List of dimension column names.
            If None, uses the default DIMENSIONS from constants.
        underwriting_department: Underwriting department (defaults to "test" for tests)

    Returns:
        Program object ready to use

    Example:
        qs = build_quota_share(name="QS_30", cession_pct=0.30)
        program = build_program(
            name="SINGLE_QS_2024",
            structures=[qs],
            underwriting_department="aviation"
        )
    """
    if dimension_columns is None:
        # Aligne le comportement des builders sur le loader :
        # union des dimensions "bordereau" + clés de mapping programme (ex: BUSCL_LIMIT_CURRENCY_CD)
        dimension_columns = sorted(
            set(DIMENSIONS) | set(PROGRAM_TO_BORDEREAU_DIMENSIONS.keys())
        )

    return Program(
        name=name,
        structures=structures,
        dimension_columns=dimension_columns,
        underwriting_department=underwriting_department,
    )
