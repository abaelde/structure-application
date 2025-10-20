from typing import Dict
from src.domain.products import PRODUCT_REGISTRY
from src.domain.condition import Condition


def apply_condition(
    exposure: float, condition: Condition, type_of_participation: str
) -> Dict[str, float]:
    product = PRODUCT_REGISTRY.get(type_of_participation)
    if product is None:
        raise ValueError(f"Unknown product type: {type_of_participation}")

    ceded_to_layer_100pct = product.apply(exposure, condition)
    ceded_to_reinsurer = ceded_to_layer_100pct * condition.signed_share

    return {
        "ceded_to_layer_100pct": ceded_to_layer_100pct,
        "ceded_to_reinsurer": ceded_to_reinsurer,
    }
