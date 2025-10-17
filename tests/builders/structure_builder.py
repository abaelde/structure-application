from typing import Optional, List, Dict, Any
from src.domain.structure import Structure
from src.domain.constants import PRODUCT
from .condition_builder import build_condition


def build_quota_share(
    name: str,
    cession_pct: Optional[float] = None,
    conditions_config: Optional[List[Dict[str, Any]]] = None,
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
        cession_pct: Default cession percentage (if conditions_config is None)
        conditions_config: List of condition configurations. Each dict can contain:
            - cession_pct: Cession percentage for this condition
            - signed_share: Reinsurer share (default 1.0)
            - country_cd, region, currency_cd, etc.: Dimension filters
        contract_order: Contract order (optional)
        predecessor_title: Name of predecessor structure (for inuring)
        claim_basis: Claim basis (e.g., "risk_attaching")
        inception_date: Effective date
        expiry_date: Expiry date
        signed_share: Default signed share if not specified in conditions_config

    Returns:
        Structure object ready to use

    Example:
        # Simple QS 30%
        qs = build_quota_share(name="QS_30", cession_pct=0.30)

        # QS with multiple conditions by currency
        qs = build_quota_share(
            name="QS_BY_CURRENCY",
            conditions_config=[
                {"currency_cd": "USD", "cession_pct": 0.25},
                {"currency_cd": "EUR", "cession_pct": 0.35},
            ]
        )
    """
    if conditions_config is None:
        if cession_pct is None:
            raise ValueError("Either cession_pct or conditions_config must be provided")
        conditions_config = [{"cession_pct": cession_pct}]

    conditions = []
    for condition_config in conditions_config:
        if "signed_share" not in condition_config:
            condition_config["signed_share"] = signed_share

        condition = build_condition(**condition_config)
        conditions.append(condition)

    return Structure(
        structure_name=name,
        contract_order=contract_order,
        type_of_participation=PRODUCT.QUOTA_SHARE,
        conditions=conditions,
        predecessor_title=predecessor_title,
        claim_basis=claim_basis,
        inception_date=inception_date,
        expiry_date=expiry_date,
    )


def build_excess_of_loss(
    name: str,
    attachment: Optional[float] = None,
    limit: Optional[float] = None,
    conditions_config: Optional[List[Dict[str, Any]]] = None,
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
        attachment: Default attachment point (if conditions_config is None)
        limit: Default limit (if conditions_config is None)
        conditions_config: List of condition configurations. Each dict can contain:
            - attachment: Attachment point for this condition
            - limit: Limit for this condition
            - signed_share: Reinsurer share (default 1.0)
            - country_cd, region, currency_cd, etc.: Dimension filters
        contract_order: Contract order (optional)
        predecessor_title: Name of predecessor structure (for inuring)
        claim_basis: Claim basis (e.g., "risk_attaching")
        inception_date: Effective date
        expiry_date: Expiry date
        signed_share: Default signed share if not specified in conditions_config

    Returns:
        Structure object ready to use

    Example:
        # Simple XL 50M xs 20M
        xl = build_excess_of_loss(
            name="XL_50xs20",
            attachment=20_000_000,
            limit=50_000_000
        )

        # XL with multiple conditions by currency
        xl = build_excess_of_loss(
            name="XL_BY_CURRENCY",
            conditions_config=[
                {"currency_cd": "USD", "attachment": 10_000_000, "limit": 40_000_000},
                {"currency_cd": "EUR", "attachment": 15_000_000, "limit": 35_000_000},
            ]
        )
    """
    if conditions_config is None:
        if attachment is None or limit is None:
            raise ValueError(
                "Either (attachment, limit) or conditions_config must be provided"
            )
        conditions_config = [{"attachment": attachment, "limit": limit}]

    conditions = []
    for condition_config in conditions_config:
        if "signed_share" not in condition_config:
            condition_config["signed_share"] = signed_share

        condition = build_condition(**condition_config)
        conditions.append(condition)

    return Structure(
        structure_name=name,
        contract_order=contract_order,
        type_of_participation=PRODUCT.EXCESS_OF_LOSS,
        conditions=conditions,
        predecessor_title=predecessor_title,
        claim_basis=claim_basis,
        inception_date=inception_date,
        expiry_date=expiry_date,
    )
