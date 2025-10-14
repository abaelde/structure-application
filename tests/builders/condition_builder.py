from typing import Optional, Dict, Any
from src.domain.models import condition
from src.domain.constants import DIMENSIONS


def build_condition(
    cession_pct: Optional[float] = None,
    attachment: Optional[float] = None,
    limit: Optional[float] = None,
    signed_share: Optional[float] = 1.0,
    exclude_cd: Optional[str] = None,
    entity_name_ced: Optional[str] = None,
    pol_risk_name_ced: Optional[str] = None,
    country_cd: Optional[str] = None,
    region: Optional[str] = None,
    class_of_business_1: Optional[str] = None,
    class_of_business_2: Optional[str] = None,
    class_of_business_3: Optional[str] = None,
    currency_cd: Optional[str] = None,
    includes_hull: Optional[bool] = None,
    includes_liability: Optional[bool] = None,
    **kwargs
) -> condition:
    """
    Build a condition object directly in memory.
    
    Args:
        cession_pct: Cession percentage (for quota share)
        attachment: Attachment point (for excess of loss)
        limit: Limit (for excess of loss)
        signed_share: Reinsurer share (default 1.0 = 100%)
        exclude_cd: Exclusion code ("exclude" for exclusion conditions)
        entity_name_ced: Entity name
        pol_risk_name_ced: Policy risk name
        country_cd: Country code
        region: Region
        class_of_business_1: Class of business level 1
        class_of_business_2: Class of business level 2
        class_of_business_3: Class of business level 3
        currency_cd: Currency code
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
        "BUSCL_EXCLUDE_CD": exclude_cd,
        "BUSCL_ENTITY_NAME_CED": entity_name_ced,
        "POL_RISK_NAME_CED": pol_risk_name_ced,
        "BUSCL_COUNTRY_CD": country_cd,
        "BUSCL_REGION": region,
        "BUSCL_CLASS_OF_BUSINESS_1": class_of_business_1,
        "BUSCL_CLASS_OF_BUSINESS_2": class_of_business_2,
        "BUSCL_CLASS_OF_BUSINESS_3": class_of_business_3,
        "BUSCL_LIMIT_CURRENCY_CD": currency_cd,
        "INCLUDES_HULL": includes_hull,
        "INCLUDES_LIABILITY": includes_liability,
    }
    
    condition_data.update(kwargs)
    
    return condition(condition_data)


def build_exclusion_condition(
    country_cd: Optional[str] = None,
    region: Optional[str] = None,
    class_of_business_1: Optional[str] = None,
    class_of_business_2: Optional[str] = None,
    class_of_business_3: Optional[str] = None,
    currency_cd: Optional[str] = None,
    entity_name_ced: Optional[str] = None,
    pol_risk_name_ced: Optional[str] = None,
    **kwargs
) -> condition:
    """
    Build an exclusion condition.
    
    Exclusion conditions don't have cession_pct, attachment, limit, or signed_share.
    They only define what to exclude based on dimensions.
    """
    return build_condition(
        exclude_cd="exclude",
        country_cd=country_cd,
        region=region,
        class_of_business_1=class_of_business_1,
        class_of_business_2=class_of_business_2,
        class_of_business_3=class_of_business_3,
        currency_cd=currency_cd,
        entity_name_ced=entity_name_ced,
        pol_risk_name_ced=pol_risk_name_ced,
        cession_pct=None,
        attachment=None,
        limit=None,
        signed_share=None,
        **kwargs
    )

