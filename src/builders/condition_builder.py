from typing import Optional, Dict, Any
from src.domain.condition import Condition


def _as_list(x):
    """Convert value to list format for multi-value dimensions."""
    if x is None:
        return None
    if isinstance(x, (list, tuple, set)):
        return list(x)
    return [x]


def build_condition(
    cession_pct: Optional[float] = None,
    attachment: Optional[float] = None,
    limit: Optional[float] = None,
    signed_share: float = 1.0,
    country_cd: Optional[str | list[str]] = None,
    region: Optional[str | list[str]] = None,
    class_of_business_1: Optional[str | list[str]] = None,
    class_of_business_2: Optional[str | list[str]] = None,
    class_of_business_3: Optional[str | list[str]] = None,
    currency_cd: Optional[str | list[str]] = None,
    includes_hull: Optional[bool] = None,
    includes_liability: Optional[bool] = None,
    **kwargs,
) -> Condition:
    """
    Build a condition object directly in memory.

    Args:
        cession_pct: Cession percentage (for quota share)
        attachment: Attachment point (for excess of loss)
        limit: Limit (for excess of loss)
        signed_share: Reinsurer share (default 1.0 = 100%)
        country_cd: Country code (string or list of strings for multi-value conditions)
        region: Region (string or list of strings for multi-value conditions)
        class_of_business_1: Class of business level 1 (string or list of strings for multi-value conditions)
        class_of_business_2: Class of business level 2 (string or list of strings for multi-value conditions)
        class_of_business_3: Class of business level 3 (string or list of strings for multi-value conditions)
        currency_cd: Currency code (string or list of strings for multi-value conditions)
        includes_hull: Whether to include Hull exposure (default True, for Aviation only)
        includes_liability: Whether to include Liability exposure (default True, for Aviation only)
        **kwargs: Additional fields to include in condition data

    Returns:
        condition object ready to use
    """
    condition_data: Dict[str, Any] = {
        "CESSION_PCT": cession_pct,
        "ATTACHMENT_POINT_100": attachment,
        "LIMIT_100": limit,
        "SIGNED_SHARE_PCT": signed_share,
        "COUNTRY": _as_list(country_cd),
        "REGION": _as_list(region),
        "PRODUCT_TYPE_LEVEL_1": _as_list(class_of_business_1),
        "PRODUCT_TYPE_LEVEL_2": _as_list(class_of_business_2),
        "PRODUCT_TYPE_LEVEL_3": _as_list(class_of_business_3),
        "CURRENCY": _as_list(currency_cd),
        "INCLUDES_HULL": includes_hull,
        "INCLUDES_LIABILITY": includes_liability,
    }

    condition_data.update(kwargs)

    return Condition(condition_data)


# build_exclusion_condition removed - exclusions are now handled at program level
