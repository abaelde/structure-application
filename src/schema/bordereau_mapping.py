"""
Bordereau mapping module - handles mapping between domain dimensions and bordereau columns.

This module is responsible ONLY for reading dimension values from bordereau rows.
It is completely separate from Snowflake serialization concerns.
"""

from typing import Iterable, Dict, List, Optional, Union


# Mapping of domain dimensions to physical bordereau columns by LOB
_LOB_MAP = {
    "casualty": {
        "COUNTRY": ["COUNTRY"],
        "REGION": ["REGION"],
        "PRODUCT_TYPE_LEVEL_1": ["PRODUCT_TYPE_LEVEL_1"],
        "PRODUCT_TYPE_LEVEL_2": ["PRODUCT_TYPE_LEVEL_2"],
        "PRODUCT_TYPE_LEVEL_3": ["PRODUCT_TYPE_LEVEL_3"],
        "CURRENCY": ["ORIGINAL_CURRENCY"],
    },
    "test": {
        "COUNTRY": ["COUNTRY"],
        "REGION": ["REGION"],
        "PRODUCT_TYPE_LEVEL_1": ["PRODUCT_TYPE_LEVEL_1"],
        "PRODUCT_TYPE_LEVEL_2": ["PRODUCT_TYPE_LEVEL_2"],
        "PRODUCT_TYPE_LEVEL_3": ["PRODUCT_TYPE_LEVEL_3"],
        "CURRENCY": ["ORIGINAL_CURRENCY"],
    },
    "aviation": {
        "COUNTRY": ["COUNTRY"],
        "REGION": ["REGION"],
        "PRODUCT_TYPE_LEVEL_1": ["PRODUCT_TYPE_LEVEL_1"],
        "PRODUCT_TYPE_LEVEL_2": ["PRODUCT_TYPE_LEVEL_2"],
        "PRODUCT_TYPE_LEVEL_3": ["PRODUCT_TYPE_LEVEL_3"],
        # Key difference: aviation has separate hull and liability currencies
        "CURRENCY": ["HULL_CURRENCY", "LIAB_CURRENCY"],
    },
}


def _get_lob_mapping(uw_dept: str) -> Dict[str, List[str]]:
    """Get the mapping for a specific LOB (Line of Business)."""
    return _LOB_MAP.get((uw_dept or "").lower(), _LOB_MAP["test"])


def columns_for_dimension(domain_key: str, uw_dept: str) -> List[str]:
    """
    Get the physical column names in the bordereau for a given domain dimension.
    
    Args:
        domain_key: The domain dimension name (e.g., "CURRENCY", "COUNTRY")
        uw_dept: The underwriting department/LOB (e.g., "aviation", "casualty")
        
    Returns:
        List of physical column names in the bordereau
    """
    return _get_lob_mapping(uw_dept).get(domain_key, [])


def read_dimension_values(row: dict, domain_key: str, uw_dept: str) -> List[str]:
    """
    Read dimension values from a bordereau row.
    
    Args:
        row: The bordereau row as a dictionary
        domain_key: The domain dimension name
        uw_dept: The underwriting department/LOB
        
    Returns:
        List of non-empty string values for the dimension
    """
    cols = columns_for_dimension(domain_key, uw_dept)
    vals = []
    
    for col in cols:
        val = row.get(col)
        if val is None:
            continue
            
        if isinstance(val, (list, tuple, set)):
            vals.extend([str(x).strip() for x in val if str(x).strip()])
        else:
            vals.append(str(val).strip())
    
    # Deduplicate while preserving order
    out, seen = [], set()
    for val in vals:
        if val and val not in seen:
            seen.add(val)
            out.append(val)
    
    return out


def present_mapping(bordereau_columns: Iterable[str], uw_dept: str) -> Dict[str, List[str]]:
    """
    Present the mapping between domain dimensions and available bordereau columns.
    
    Args:
        bordereau_columns: Available columns in the bordereau
        uw_dept: The underwriting department/LOB
        
    Returns:
        Dictionary mapping domain dimensions to available bordereau columns
    """
    mapping = _get_lob_mapping(uw_dept)
    available_cols = set(bordereau_columns)
    
    return {
        domain_key: [col for col in cols if col in available_cols]
        for domain_key, cols in mapping.items()
    }


def get_supported_dimensions(uw_dept: str) -> List[str]:
    """
    Get all supported domain dimensions for a given LOB.
    
    Args:
        uw_dept: The underwriting department/LOB
        
    Returns:
        List of supported domain dimension names
    """
    return list(_get_lob_mapping(uw_dept).keys())
