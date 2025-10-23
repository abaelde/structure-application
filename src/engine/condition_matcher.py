import pandas as pd
from typing import Optional, List, Dict, Any
from src.domain import Condition
from src.domain.policy import Policy


def _values_match(condition_values: list[str] | None, policy_value) -> bool:
    if condition_values is None:
        return True  # dimension non contrainte

    # Policy value can be None, string, or list of strings (for aviation CURRENCY)
    if policy_value is None or (
        isinstance(policy_value, float) and pd.isna(policy_value)
    ):
        return False  # condition impose un ensemble, mais la police n'a pas de valeur

    # Handle list of policy values (e.g., aviation CURRENCY)
    if isinstance(policy_value, (list, tuple, set)):
        # At least one policy value must match the condition
        return any(_values_match(condition_values, pv) for pv in policy_value)

    if not isinstance(policy_value, str):
        return False  # Strict: policy value must be a string

    # Normalisation légère
    pv = policy_value.strip()
    # Convert list -> set pour membership O(1)
    return pv in set(str(v).strip() for v in condition_values)


def _specificity_increment(condition_values: list[str] | None) -> float:
    if not condition_values:
        return 0.0
    n = len(condition_values)
    return 1.0 / n  # 1 si 1 valeur, 0.5 si 2, etc.


def match_condition(
    policy: Policy,
    conditions: List[Condition],
    dimension_columns: List[str],
) -> Optional[Condition]:
    matched = []
    for condition in conditions:
        ok = True
        score = 0.0
        for dimension in dimension_columns:
            cond_vals = condition.get_values(dimension)
            if cond_vals is not None and len(cond_vals) > 0:
                policy_val = policy.get_dimension_value(dimension)
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


def match_condition_with_details(
    policy: Policy,
    conditions: List[Condition],
    dimension_columns: List[str],
) -> tuple[Optional[Condition], Dict[str, Any]]:
    """
    Match condition with detailed information about why it matched or didn't match.
    Returns (matched_condition, matching_details)
    """
    matching_details = {
        "matched_condition": None,
        "matching_score": 0.0,
        "dimension_matches": {},
        "failed_conditions": [],
        "policy_values": {},
    }

    # Store policy values for reference
    for dimension in dimension_columns:
        matching_details["policy_values"][dimension] = policy.get_dimension_value(
            dimension
        )

    matched = []
    for condition in conditions:
        condition_details = {
            "condition": condition,
            "score": 0.0,
            "dimension_matches": {},
            "failed_dimensions": [],
        }

        ok = True
        for dimension in dimension_columns:
            cond_vals = condition.get_values(dimension)
            policy_val = policy.get_dimension_value(dimension)

            if cond_vals is not None and len(cond_vals) > 0:
                matches = _values_match(cond_vals, policy_val)
                condition_details["dimension_matches"][dimension] = {
                    "condition_values": cond_vals,
                    "policy_value": policy_val,
                    "matches": matches,
                }

                if matches:
                    condition_details["score"] += _specificity_increment(cond_vals)
                else:
                    ok = False
                    condition_details["failed_dimensions"].append(dimension)
            else:
                # No constraint on this dimension
                condition_details["dimension_matches"][dimension] = {
                    "condition_values": None,
                    "policy_value": policy_val,
                    "matches": True,
                }

        if ok:
            matched.append((condition, condition_details))
        else:
            matching_details["failed_conditions"].append(condition_details)

    if not matched:
        return None, matching_details

    # Sort by score and take the best match
    matched.sort(key=lambda x: x[1]["score"], reverse=True)
    best_match = matched[0]

    matching_details["matched_condition"] = best_match[0]
    matching_details["matching_score"] = best_match[1]["score"]
    matching_details["dimension_matches"] = best_match[1]["dimension_matches"]

    return best_match[0], matching_details
