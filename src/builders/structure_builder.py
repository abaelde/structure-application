from typing import Optional, List, Dict, Any
from src.domain.structure import Structure
from src.domain.constants import PRODUCT, CLAIM_BASIS
from .condition_builder import build_condition


def build_quota_share(
    name: str,
    # Valeurs par défaut de la structure
    cession_pct: Optional[float] = None,
    signed_share: float = 1.0,
    # Conditions spéciales (exceptions aux valeurs par défaut)
    special_conditions: Optional[List[Dict[str, Any]]] = None,
    # Autres paramètres
    predecessor_title: Optional[str] = None,
    claim_basis: Optional[str] = None,
    inception_date: Optional[str] = None,
    expiry_date: Optional[str] = None,
) -> Structure:
    """
    Build a Quota Share structure directly in memory.

    Args:
        name: Structure name
        cession_pct: Default cession percentage for the structure
        signed_share: Default reinsurer share (default 1.0 = 100%)
        special_conditions: List of special conditions that override default values.
            Each dict should contain dimension filters and any values that differ from defaults:
            - country_cd, region, currency_cd, etc.: Dimension filters
            - cession_pct: Override default cession percentage (optional)
            - signed_share: Override default signed share (optional)
        predecessor_title: Name of predecessor structure (for inuring)
        claim_basis: Claim basis (e.g., "risk_attaching")
        inception_date: Effective date
        expiry_date: Expiry date

    Returns:
        Structure object ready to use

    Example:
        # Simple QS 30% (no special conditions)
        qs = build_quota_share(name="QS_30", cession_pct=0.30)

        # QS with special conditions by currency
        qs = build_quota_share(
            name="QS_BY_CURRENCY",
            cession_pct=0.30,  # Default value
            signed_share=1.0,  # Default value
            special_conditions=[
                {"currency_cd": "USD", "cession_pct": 0.25},  # Override for USD
                {"currency_cd": "EUR", "cession_pct": 0.35},  # Override for EUR
            ]
        )
    """
    # Construire les conditions spéciales en fusionnant avec les valeurs par défaut
    conditions = []
    if special_conditions is not None:
        for special_condition in special_conditions:
            # Fusionner les valeurs par défaut avec les valeurs spéciales
            condition_data = {
                "cession_pct": cession_pct,  # Valeur par défaut
                "signed_share": signed_share,  # Valeur par défaut
            }
            
            # Override avec les valeurs spéciales si fournies
            condition_data.update(special_condition)
            
            # Ne créer une condition que si elle a des dimensions spécifiques
            has_dimensions = any(
                key in condition_data and condition_data[key] is not None
                for key in ["country_cd", "region", "currency_cd", "class_of_business_1", "class_of_business_2", "class_of_business_3"]
            )
            
            if has_dimensions:
                condition = build_condition(**condition_data)
                conditions.append(condition)

    # Defaults obligatoires pour passer la validation (claim_basis + période)
    if claim_basis is None:
        claim_basis = CLAIM_BASIS.RISK_ATTACHING
    if inception_date is None:
        inception_date = "1900-01-01"
    if expiry_date is None:
        expiry_date = "2100-01-01"

    return Structure(
        structure_name=name,
        type_of_participation=PRODUCT.QUOTA_SHARE,
        conditions=conditions,
        predecessor_title=predecessor_title,
        claim_basis=claim_basis,
        inception_date=inception_date,
        expiry_date=expiry_date,
        cession_pct=cession_pct,
        signed_share=signed_share,
    )


def build_excess_of_loss(
    name: str,
    # Valeurs par défaut de la structure
    attachment: Optional[float] = None,
    limit: Optional[float] = None,
    signed_share: float = 1.0,
    # Conditions spéciales (exceptions aux valeurs par défaut)
    special_conditions: Optional[List[Dict[str, Any]]] = None,
    # Autres paramètres
    predecessor_title: Optional[str] = None,
    claim_basis: Optional[str] = None,
    inception_date: Optional[str] = None,
    expiry_date: Optional[str] = None,
) -> Structure:
    """
    Build an Excess of Loss structure directly in memory.

    Args:
        name: Structure name
        attachment: Default attachment point for the structure
        limit: Default limit for the structure
        signed_share: Default reinsurer share (default 1.0 = 100%)
        special_conditions: List of special conditions that override default values.
            Each dict should contain dimension filters and any values that differ from defaults:
            - country_cd, region, currency_cd, etc.: Dimension filters
            - attachment: Override default attachment point (optional)
            - limit: Override default limit (optional)
            - signed_share: Override default signed share (optional)
        predecessor_title: Name of predecessor structure (for inuring)
        claim_basis: Claim basis (e.g., "risk_attaching")
        inception_date: Effective date
        expiry_date: Expiry date

    Returns:
        Structure object ready to use

    Example:
        # Simple XL 50M xs 20M (no special conditions)
        xl = build_excess_of_loss(
            name="XL_50xs20",
            attachment=20_000_000,
            limit=50_000_000
        )

        # XL with special conditions by currency
        xl = build_excess_of_loss(
            name="XL_BY_CURRENCY",
            attachment=20_000_000,  # Default value
            limit=50_000_000,       # Default value
            signed_share=1.0,       # Default value
            special_conditions=[
                {"currency_cd": "USD", "attachment": 10_000_000, "limit": 40_000_000},
                {"currency_cd": "EUR", "attachment": 15_000_000, "limit": 35_000_000},
            ]
        )
    """
    # Construire les conditions spéciales en fusionnant avec les valeurs par défaut
    conditions = []
    if special_conditions is not None:
        for special_condition in special_conditions:
            # Fusionner les valeurs par défaut avec les valeurs spéciales
            condition_data = {
                "attachment": attachment,  # Valeur par défaut
                "limit": limit,            # Valeur par défaut
                "signed_share": signed_share,  # Valeur par défaut
            }
            
            # Override avec les valeurs spéciales si fournies
            condition_data.update(special_condition)
            
            # Ne créer une condition que si elle a des dimensions spécifiques
            has_dimensions = any(
                key in condition_data and condition_data[key] is not None
                for key in ["country_cd", "region", "currency_cd", "class_of_business_1", "class_of_business_2", "class_of_business_3"]
            )
            
            if has_dimensions:
                condition = build_condition(**condition_data)
                conditions.append(condition)

    if claim_basis is None:
        claim_basis = CLAIM_BASIS.RISK_ATTACHING
    if inception_date is None:
        inception_date = "1900-01-01"
    if expiry_date is None:
        expiry_date = "2100-01-01"

    return Structure(
        structure_name=name,
        type_of_participation=PRODUCT.EXCESS_OF_LOSS,
        conditions=conditions,
        predecessor_title=predecessor_title,
        claim_basis=claim_basis,
        inception_date=inception_date,
        expiry_date=expiry_date,
        limit=limit,
        attachment=attachment,
        signed_share=signed_share,
    )
