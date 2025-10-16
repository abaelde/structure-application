from typing import List, Optional
from src.domain.models import Program, Structure
# DIMENSIONS supprimé - utilisation directe des clés canoniques
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
        # Utilise uniquement le schéma comme source de vérité pour les dimensions
        dimension_columns = sorted(
            set(PROGRAM_TO_BORDEREAU_DIMENSIONS.keys()) | {"BUSCL_EXCLUDE_CD"}
        )

    return Program(
        name=name,
        structures=structures,
        dimension_columns=dimension_columns,
        underwriting_department=underwriting_department,
    )
