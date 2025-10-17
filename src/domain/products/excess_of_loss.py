import pandas as pd
from .base import Product
from src.domain.condition import Condition


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
    def apply(self, exposure: float, condition: Condition) -> float:
        if pd.isna(condition.attachment) or pd.isna(condition.limit):
            raise ValueError(
                "ATTACHMENT_POINT_100 and LIMIT_100 are required for excess_of_loss"
            )

        return excess_of_loss(exposure, condition.attachment, condition.limit)
