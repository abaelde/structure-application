import pandas as pd
from typing import Dict, Any, Optional, List
from src.domain import condition


def check_exclusion(
    policy_data: Dict[str, Any], conditions: List[condition], dimension_columns: List[str]
) -> bool:
    for condition in conditions:
        if not condition.is_exclusion():
            continue

        matches = True
        for dimension in dimension_columns:
            if dimension == "BUSCL_EXCLUDE_CD":
                continue

            condition_value = condition.get(dimension)
            if pd.notna(condition_value):
                policy_value = policy_data.get(dimension)
                if policy_value != condition_value:
                    matches = False
                    break

        if matches:
            return True

    return False


def match_condition(
    policy_data: Dict[str, Any], conditions: List[condition], dimension_columns: List[str]
) -> Optional[condition]:
    matched_conditions = []

    for condition in conditions:
        if condition.is_exclusion():
            continue

        matches = True
        specificity = 0

        for dimension in dimension_columns:
            condition_value = condition.get(dimension)

            if pd.notna(condition_value):
                policy_value = policy_data.get(dimension)
                if policy_value != condition_value:
                    matches = False
                    break
                specificity += 1

        if matches:
            matched_conditions.append((condition, specificity))

    if not matched_conditions:
        return None

    matched_conditions.sort(key=lambda x: x[1], reverse=True)
    return matched_conditions[0][0]
