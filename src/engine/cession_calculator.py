import pandas as pd
from typing import Dict, Any
from src.domain.products import quota_share, excess_of_loss
from src.domain import PRODUCT, SECTION_COLS as SC


def apply_section(
    exposure: float, section: Dict[str, Any], type_of_participation: str
) -> Dict[str, float]:
    if type_of_participation == PRODUCT.QUOTA_SHARE:
        cession_PCT = section[SC.CESSION_PCT]
        if pd.isna(cession_PCT):
            raise ValueError("CESSION_PCT is required for quota_share")
        limit = section.get(SC.LIMIT)
        if pd.notna(limit):
            cession_to_layer_100pct = quota_share(exposure, cession_PCT, limit)
        else:
            cession_to_layer_100pct = quota_share(exposure, cession_PCT)

    elif type_of_participation == PRODUCT.EXCESS_OF_LOSS:
        attachment_point_100 = section[SC.ATTACHMENT]
        limit_100 = section[SC.LIMIT]
        if pd.isna(attachment_point_100) or pd.isna(limit_100):
            raise ValueError(
                "ATTACHMENT_POINT_100 and LIMIT_100 are required for excess_of_loss"
            )
        cession_to_layer_100pct = excess_of_loss(
            exposure, attachment_point_100, limit_100
        )

    else:
        raise ValueError(f"Unknown product type: {type_of_participation}")

    reinsurer_share = section.get(SC.SIGNED_SHARE, 1.0)
    if pd.isna(reinsurer_share):
        reinsurer_share = 1.0

    cession_to_reinsurer = cession_to_layer_100pct * reinsurer_share

    return {
        "cession_to_layer_100pct": cession_to_layer_100pct,
        "cession_to_reinsurer": cession_to_reinsurer,
        "reinsurer_share": reinsurer_share,
    }

