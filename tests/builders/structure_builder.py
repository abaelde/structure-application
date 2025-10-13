from typing import Optional, List, Dict, Any
from src.domain.models import Structure, Section
from src.domain.constants import PRODUCT
from .section_builder import build_section


def build_quota_share(
    name: str,
    cession_pct: Optional[float] = None,
    sections_config: Optional[List[Dict[str, Any]]] = None,
    contract_order: Optional[int] = None,
    predecessor_title: Optional[str] = None,
    claim_basis: Optional[str] = None,
    inception_date: Optional[str] = None,
    expiry_date: Optional[str] = None,
    signed_share: float = 1.0,
) -> Structure:
    """
    Build a Quota Share structure directly in memory.
    
    Args:
        name: Structure name
        cession_pct: Default cession percentage (if sections_config is None)
        sections_config: List of section configurations. Each dict can contain:
            - cession_pct: Cession percentage for this section
            - signed_share: Reinsurer share (default 1.0)
            - country_cd, region, currency_cd, etc.: Dimension filters
        contract_order: Contract order (optional)
        predecessor_title: Name of predecessor structure (for inuring)
        claim_basis: Claim basis (e.g., "risk_attaching")
        inception_date: Effective date
        expiry_date: Expiry date
        signed_share: Default signed share if not specified in sections_config
    
    Returns:
        Structure object ready to use
    
    Example:
        # Simple QS 30%
        qs = build_quota_share(name="QS_30", cession_pct=0.30)
        
        # QS with multiple sections by currency
        qs = build_quota_share(
            name="QS_BY_CURRENCY",
            sections_config=[
                {"currency_cd": "USD", "cession_pct": 0.25},
                {"currency_cd": "EUR", "cession_pct": 0.35},
            ]
        )
    """
    if sections_config is None:
        if cession_pct is None:
            raise ValueError("Either cession_pct or sections_config must be provided")
        sections_config = [{"cession_pct": cession_pct}]
    
    sections = []
    for section_config in sections_config:
        if "signed_share" not in section_config:
            section_config["signed_share"] = signed_share
        
        section = build_section(**section_config)
        sections.append(section)
    
    return Structure(
        structure_name=name,
        contract_order=contract_order,
        type_of_participation=PRODUCT.QUOTA_SHARE,
        sections=sections,
        predecessor_title=predecessor_title,
        claim_basis=claim_basis,
        inception_date=inception_date,
        expiry_date=expiry_date,
    )


def build_excess_of_loss(
    name: str,
    attachment: Optional[float] = None,
    limit: Optional[float] = None,
    sections_config: Optional[List[Dict[str, Any]]] = None,
    contract_order: Optional[int] = None,
    predecessor_title: Optional[str] = None,
    claim_basis: Optional[str] = None,
    inception_date: Optional[str] = None,
    expiry_date: Optional[str] = None,
    signed_share: float = 1.0,
) -> Structure:
    """
    Build an Excess of Loss structure directly in memory.
    
    Args:
        name: Structure name
        attachment: Default attachment point (if sections_config is None)
        limit: Default limit (if sections_config is None)
        sections_config: List of section configurations. Each dict can contain:
            - attachment: Attachment point for this section
            - limit: Limit for this section
            - signed_share: Reinsurer share (default 1.0)
            - country_cd, region, currency_cd, etc.: Dimension filters
        contract_order: Contract order (optional)
        predecessor_title: Name of predecessor structure (for inuring)
        claim_basis: Claim basis (e.g., "risk_attaching")
        inception_date: Effective date
        expiry_date: Expiry date
        signed_share: Default signed share if not specified in sections_config
    
    Returns:
        Structure object ready to use
    
    Example:
        # Simple XL 50M xs 20M
        xl = build_excess_of_loss(
            name="XL_50xs20",
            attachment=20_000_000,
            limit=50_000_000
        )
        
        # XL with multiple sections by currency
        xl = build_excess_of_loss(
            name="XL_BY_CURRENCY",
            sections_config=[
                {"currency_cd": "USD", "attachment": 10_000_000, "limit": 40_000_000},
                {"currency_cd": "EUR", "attachment": 15_000_000, "limit": 35_000_000},
            ]
        )
    """
    if sections_config is None:
        if attachment is None or limit is None:
            raise ValueError("Either (attachment, limit) or sections_config must be provided")
        sections_config = [{"attachment": attachment, "limit": limit}]
    
    sections = []
    for section_config in sections_config:
        if "signed_share" not in section_config:
            section_config["signed_share"] = signed_share
        
        section = build_section(**section_config)
        sections.append(section)
    
    return Structure(
        structure_name=name,
        contract_order=contract_order,
        type_of_participation=PRODUCT.EXCESS_OF_LOSS,
        sections=sections,
        predecessor_title=predecessor_title,
        claim_basis=claim_basis,
        inception_date=inception_date,
        expiry_date=expiry_date,
    )

