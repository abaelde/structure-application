import pandas as pd
from typing import Dict, Any
from .base import Product
from src.domain.constants import SECTION_COLS as SC


def excess_of_loss(
    exposure: float, attachment_point_100: float, limit_100: float
) -> float:
    if attachment_point_100 < 0 or limit_100 < 0:
        raise ValueError("attachment_point_100 and limit_100 must be positive")

    if exposure <= attachment_point_100:
        return 0.0

    amount_above_priority = exposure - attachment_point_100
    return min(amount_above_priority, limit_100)


class ExcessOfLoss(Product):
    def apply(self, exposure: float, section: Dict[str, Any]) -> float:
        attachment_point_100 = section[SC.ATTACHMENT]
        limit_100 = section[SC.LIMIT]
        
        if pd.isna(attachment_point_100) or pd.isna(limit_100):
            raise ValueError(
                "ATTACHMENT_POINT_100 and LIMIT_100 are required for excess_of_loss"
            )
        
        return excess_of_loss(exposure, attachment_point_100, limit_100)
