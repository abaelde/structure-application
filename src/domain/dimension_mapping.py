"""
Dimension mapping basé sur une source de vérité unique (schema.py).
"""

from typing import Dict, Any, Optional, List
from src.domain.schema import PROGRAM_TO_BORDEREAU_DIMENSIONS


def get_policy_value( # AURE encore utile ?
    policy_data: Dict[str, Any], dimension: str, uw_dept: Optional[str] = None
) -> Optional[Any]:
    mapping = PROGRAM_TO_BORDEREAU_DIMENSIONS.get(dimension)
    if mapping is None:
        return policy_data.get(dimension)
    if isinstance(mapping, str):
        return policy_data.get(mapping)
    if isinstance(mapping, dict):
        if uw_dept in mapping:
            return policy_data.get(mapping[uw_dept])
    return None


def is_dimension_optional(dimension: str) -> bool:
    return True


def validate_program_bordereau_compatibility(
    program_dimensions: List[str],
    bordereau_columns: List[str],
    uw_dept: Optional[str],
) -> tuple[List[str], List[str]]:
    warnings: List[str] = []
    errors: List[str] = []
    for dimension in program_dimensions:
        if not can_map_dimension(dimension, bordereau_columns, uw_dept):
            warnings.append(
                f"Dimension '{dimension}' non trouvée dans le bordereau - régime par défaut appliqué"
            )
    return errors, warnings


def can_map_dimension(
    dimension: str, bordereau_columns: List[str], uw_dept: Optional[str]
) -> bool:
    mapping = PROGRAM_TO_BORDEREAU_DIMENSIONS.get(dimension)
    if mapping is None:
        return dimension in bordereau_columns
    if isinstance(mapping, str):
        return mapping in bordereau_columns
    if isinstance(mapping, dict):
        if uw_dept in mapping:
            return mapping[uw_dept] in bordereau_columns
    return False


def validate_aviation_currency_consistency(
    bordereau_columns: List[str], uw_dept: Optional[str]
) -> List[str]:
    if uw_dept != "aviation":
        return []
    warnings: List[str] = []
    has_hull = "HULL_CURRENCY" in bordereau_columns
    has_liability = "LIABILITY_CURRENCY" in bordereau_columns
    if has_hull and has_liability:
        warnings.append(
            "⚠️  Aviation : Vérifiez que HULL_CURRENCY et LIABILITY_CURRENCY sont identiques dans vos données"
        )
        warnings.append(
            "   Si elles diffèrent, le système prendra HULL_CURRENCY par défaut"
        )
    return warnings


def get_all_mappable_dimensions(
    bordereau_columns: List[str], uw_dept: Optional[str]
) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for dim, mapping in PROGRAM_TO_BORDEREAU_DIMENSIONS.items():
        if isinstance(mapping, str):
            if mapping in bordereau_columns:
                out[dim] = mapping
        elif isinstance(mapping, dict):
            if uw_dept in mapping:
                m = mapping[uw_dept]
                if m in bordereau_columns:
                    out[dim] = m
    return out
