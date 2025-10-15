import pandas as pd
from typing import Dict, Any, Optional, List
from src.domain import condition, CURRENCY_COLUMN_ALIASES


def map_currency_condition(
    condition_value: Any,
    policy_data: Dict[str, Any],
    line_of_business: str
) -> bool:
    """
    Map currency condition from program (BUSCL_LIMIT_CURRENCY_CD) to bordereau columns
    based on line of business.
    
    Args:
        condition_value: The currency value from the program condition
        policy_data: The policy data from the bordereau
        line_of_business: The line of business (aviation/casualty)
    
    Returns:
        bool: True if the currency condition matches, False otherwise
    """
    if pd.isna(condition_value):
        return True
    
    line_of_business_lower = line_of_business.lower() if line_of_business else ""
    
    if line_of_business_lower == "aviation":
        # Aviation: Check if condition currency matches either HULL_CURRENCY or LIABILITY_CURRENCY
        hull_currency = policy_data.get("HULL_CURRENCY")
        liability_currency = policy_data.get("LIABILITY_CURRENCY")
        
        return (hull_currency == condition_value or liability_currency == condition_value)
    
    elif line_of_business_lower == "casualty":
        # Casualty: Check if condition currency matches CURRENCY
        currency = policy_data.get("CURRENCY")
        return currency == condition_value
    
    # Fallback: try to match with any currency column
    currency_columns = CURRENCY_COLUMN_ALIASES.get(line_of_business_lower, ["CURRENCY"])
    for col in currency_columns:
        if policy_data.get(col) == condition_value:
            return True
    
    return False


def check_exclusion(
    policy_data: Dict[str, Any], conditions: List[condition], dimension_columns: List[str], line_of_business: str = None
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
                    # Standard dimension matching
                    policy_value = policy_data.get(dimension)
                    if policy_value != condition_value:
                        matches = False
                        break

        if matches:
            return True

    return False


def match_condition(
    policy_data: Dict[str, Any], conditions: List[condition], dimension_columns: List[str], line_of_business: str = None
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
                # Special handling for currency matching
                if dimension == "BUSCL_LIMIT_CURRENCY_CD":
                    if not map_currency_condition(condition_value, policy_data, line_of_business):
                        matches = False
                        break
                else:
                    # Standard dimension matching
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
