"""
Dimension mapping basé sur une source de vérité unique (schema.py).
"""

from typing import Dict, Any, Optional, List
from src.domain.schema import PROGRAM_TO_BORDEREAU_DIMENSIONS


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
