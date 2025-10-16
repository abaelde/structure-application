import pandas as pd
from typing import Dict, Any, Optional, List
from src.domain import Condition
from src.domain.dimension_mapping import get_policy_value


def map_currency_condition(
    condition_value: Any,
    policy_data: Dict[str, Any],
    line_of_business: str
) -> bool:
    """
    Map currency condition from program (BUSCL_LIMIT_CURRENCY_CD) to bordereau columns
    using the new dimension mapping system.
    
    Args:
        condition_value: The currency value from the program condition
        policy_data: The policy data from the bordereau
        line_of_business: The line of business (aviation/casualty)
    
    Returns:
        bool: True if the currency condition matches, False otherwise
    """
    if pd.isna(condition_value):
        return True
    
    # Use the new dimension mapping system
    policy_currency = get_policy_value(policy_data, "BUSCL_LIMIT_CURRENCY_CD", line_of_business)
    
    # If currency is not found in bordereau, condition matches (default regime)
    if policy_currency is None:
        return True
    
    return policy_currency == condition_value


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

            condition_value = condition.get(dimension)
            if pd.notna(condition_value):
                # Special handling for currency matching
                if dimension == "BUSCL_LIMIT_CURRENCY_CD":
                    if not map_currency_condition(condition_value, policy_data, line_of_business):
                        matches = False
                        break
                else:
                    # Standard dimension matching using new mapping system
                    policy_value = get_policy_value(policy_data, dimension, line_of_business)
                    if policy_value != condition_value:
                        matches = False
                        break

        if matches:
            return True

    return False


def match_condition(
    policy_data: Dict[str, Any], conditions: List[Condition], dimension_columns: List[str], line_of_business: str = None
) -> Optional[Condition]:
    matched_conditions = []

    for condition in conditions:
        if condition.is_exclusion():
            continue

        matches = True
        specificity = 0

        for dimension in dimension_columns:
            condition_value = condition.get(dimension)

            if pd.notna(condition_value):
                # Special handling for currency matching
                if dimension == "BUSCL_LIMIT_CURRENCY_CD":
                    if not map_currency_condition(condition_value, policy_data, line_of_business):
                        matches = False
                        break
                else:
                    # Standard dimension matching using new mapping system
                    policy_value = get_policy_value(policy_data, dimension, line_of_business)
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
