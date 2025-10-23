"""
Snowflake schema module - handles mapping between domain objects and Snowflake tables.

This module is responsible ONLY for serialization/deserialization between domain objects
and Snowflake database tables. It is completely separate from bordereau reading concerns.
"""

from typing import Dict, Set, Optional, Union
import pandas as pd


# Mapping "program dimensions" -> "Snowflake columns" (with LOB support)
PROGRAM_TO_SNOWFLAKE_COLUMNS: Dict[str, Union[str, Dict[str, str]]] = {
    "COUNTRY": "COUNTRIES",
    "REGION": "REGIONS",
    "PRODUCT_TYPE_LEVEL_1": "PRODUCT_TYPE_LEVEL_1",
    "PRODUCT_TYPE_LEVEL_2": "PRODUCT_TYPE_LEVEL_2",
    "PRODUCT_TYPE_LEVEL_3": "PRODUCT_TYPE_LEVEL_3",
    "CURRENCY": {
        "aviation": "HULL_CURRENCY",
        "casualty": "CURRENCIES",
        "test": "CURRENCIES"
    },
}

# Certain "flags" that travel with dimensions in conditions
DIM_FLAGS: Set[str] = {"INCLUDES_HULL", "INCLUDES_LIABILITY"}


def _choose_for_lob(val: Union[str, Dict[str, str]], uw_dept: Optional[str]) -> str:
    """Select the physical column corresponding to the LOB (fallback: first item)."""
    if isinstance(val, str):
        return val
    lob = (uw_dept or "").lower()
    if lob in val:
        return val[lob]
    # Stable fallback if LOB is not in the dict
    return next(iter(val.values()))


def domain_to_snowflake_map(uw_dept: Optional[str]) -> Dict[str, str]:
    """
    Map {program_dimension -> snowflake_column} for a specific LOB.
    
    Args:
        uw_dept: The underwriting department/LOB
        
    Returns:
        Dictionary mapping domain dimensions to Snowflake column names
    """
    out: Dict[str, str] = {}
    for k, v in PROGRAM_TO_SNOWFLAKE_COLUMNS.items():
        out[k] = _choose_for_lob(v, uw_dept)
    return out


def snowflake_to_domain_map(uw_dept: Optional[str]) -> Dict[str, str]:
    """
    Inverse of domain_to_snowflake_map: {snowflake_column -> program_dimension}.
    
    Args:
        uw_dept: The underwriting department/LOB
        
    Returns:
        Dictionary mapping Snowflake column names to domain dimensions
    """
    fwd = domain_to_snowflake_map(uw_dept)
    return {snowflake: program for program, snowflake in fwd.items()}


def physical_dim_names(*, include_flags: bool = False) -> Set[str]:
    """
    Set of possible Snowflake column names (all LOBs combined).
    
    Args:
        include_flags: Whether to include dimension flags
        
    Returns:
        Set of physical column names
    """
    names: Set[str] = set()
    for v in PROGRAM_TO_SNOWFLAKE_COLUMNS.values():
        if isinstance(v, dict):
            names.update(v.values())
        else:
            names.add(v)
    if include_flags:
        names |= DIM_FLAGS
    return names


def dims_in(df: pd.DataFrame, *, include_flags: bool = False) -> list[str]:
    """
    Ordered list of 'dimension' columns present in a conditions/exclusions DataFrame (physical).
    
    Args:
        df: The DataFrame to analyze
        include_flags: Whether to include dimension flags
        
    Returns:
        List of dimension column names present in the DataFrame
    """
    if df is None or df.empty:
        return []
    phys = physical_dim_names(include_flags=include_flags)
    return [c for c in df.columns if c in phys]


def present_snowflake_mapping(
    snowflake_columns: set[str], uw_dept: Optional[str]
) -> Dict[str, str]:
    """
    {program_dimension -> snowflake_column} for dimensions REALLY present
    in a given Snowflake table.
    
    Args:
        snowflake_columns: Available columns in the Snowflake table
        uw_dept: The underwriting department/LOB
        
    Returns:
        Dictionary mapping domain dimensions to available Snowflake columns
    """
    mapping = domain_to_snowflake_map(uw_dept)
    return {k: v for k, v in mapping.items() if v in snowflake_columns}


# Backward compatibility aliases
def program_to_snowflake_map(uw_dept: Optional[str]) -> Dict[str, str]:
    """Backward compatibility alias for domain_to_snowflake_map."""
    return domain_to_snowflake_map(uw_dept)


def snowflake_to_program_map(uw_dept: Optional[str]) -> Dict[str, str]:
    """Backward compatibility alias for snowflake_to_domain_map."""
    return snowflake_to_domain_map(uw_dept)
