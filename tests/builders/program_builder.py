from typing import List, Optional
from src.domain.models import Program, Structure
from src.domain.constants import DIMENSIONS


def build_program(
    name: str,
    structures: List[Structure],
    dimension_columns: Optional[List[str]] = None,
) -> Program:
    """
    Build a Program object directly in memory.
    
    Args:
        name: Program name
        structures: List of Structure objects
        dimension_columns: List of dimension column names.
            If None, uses the default DIMENSIONS from constants.
    
    Returns:
        Program object ready to use
    
    Example:
        qs = build_quota_share(name="QS_30", cession_pct=0.30)
        program = build_program(
            name="SINGLE_QS_2024",
            structures=[qs]
        )
    """
    if dimension_columns is None:
        dimension_columns = DIMENSIONS.copy()
    
    return Program(
        name=name,
        structures=structures,
        dimension_columns=dimension_columns,
    )

