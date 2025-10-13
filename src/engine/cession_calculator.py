from typing import Dict
from src.domain.products import PRODUCT_REGISTRY
from src.domain.models import Section


def apply_section(
    exposure: float, section: Section, type_of_participation: str
) -> Dict[str, float]:
    product = PRODUCT_REGISTRY.get(type_of_participation)
    if product is None:
        raise ValueError(f"Unknown product type: {type_of_participation}")
    
    cession_to_layer_100pct = product.apply(exposure, section)
    cession_to_reinsurer = cession_to_layer_100pct * section.signed_share

    return {
        "cession_to_layer_100pct": cession_to_layer_100pct,
        "cession_to_reinsurer": cession_to_reinsurer,
        "reinsurer_share": section.signed_share,
    }
