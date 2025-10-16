import pandas as pd
from typing import Dict, Any, Optional, List
from src.domain import Condition
from src.domain.dimension_mapping import get_policy_value


def _values_match(condition_values: list[str] | None, policy_value) -> bool:
    if condition_values is None:
        return True  # dimension non contrainte
    pv = None if policy_value is None or (isinstance(policy_value, float) and pd.isna(policy_value)) else str(policy_value)
    if pv is None:
        return False  # condition impose un ensemble, mais la police n'a pas de valeur
    # Normalisation légère (au besoin, on peut upper())
    pv = pv.strip()
    # Convert list -> set pour membership O(1)
    return pv in set(str(v).strip() for v in condition_values)

def _specificity_increment(condition_values: list[str] | None) -> float:
    if not condition_values:
        return 0.0
    n = len(condition_values)
    return 1.0 / n  # 1 si 1 valeur, 0.5 si 2, etc.


def check_exclusion(
    policy_data: Dict[str, Any], conditions: List[Condition], dimension_columns: List[str], line_of_business: str = None
) -> bool:
    for condition in conditions:
        if not condition.is_exclusion():
            continue
        matches = True
        for dimension in dimension_columns:
            if dimension == "BUSCL_EXCLUDE_CD":
                continue
            cond_vals = condition.get_values(dimension)
            if cond_vals is not None and len(cond_vals) > 0:
                policy_val = get_policy_value(policy_data, dimension, line_of_business)
                if not _values_match(cond_vals, policy_val):
                    matches = False
                    break
        if matches:
            return True
    return False


def match_condition(
    policy_data: Dict[str, Any], conditions: List[Condition], dimension_columns: List[str], line_of_business: str = None
) -> Optional[Condition]:
    matched = []
    for condition in conditions:
        if condition.is_exclusion():
            continue
        ok = True
        score = 0.0
        for dimension in dimension_columns:
            cond_vals = condition.get_values(dimension)
            if cond_vals is not None and len(cond_vals) > 0:
                policy_val = get_policy_value(policy_data, dimension, line_of_business)
                if not _values_match(cond_vals, policy_val):
                    ok = False
                    break
                score += _specificity_increment(cond_vals)
        if ok:
            matched.append((condition, score))
    if not matched:
        return None
    matched.sort(key=lambda x: x[1], reverse=True)
    return matched[0][0]
