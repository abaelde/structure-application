from typing import Dict, Any
from src.domain.products import PRODUCT_REGISTRY
from src.domain import SECTION_COLS as SC


def apply_section(
    exposure: float, section: Dict[str, Any], type_of_participation: str
) -> Dict[str, float]:
    product = PRODUCT_REGISTRY.get(type_of_participation)
    if product is None:
        raise ValueError(f"Unknown product type: {type_of_participation}")
    
    cession_to_layer_100pct = product.apply(exposure, section)
    reinsurer_share = section[SC.SIGNED_SHARE]
    cession_to_reinsurer = cession_to_layer_100pct * reinsurer_share

    return {
        "cession_to_layer_100pct": cession_to_layer_100pct,
        "cession_to_reinsurer": cession_to_reinsurer,
        "reinsurer_share": reinsurer_share,
    }
