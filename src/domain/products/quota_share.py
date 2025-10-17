import pandas as pd
from .base import Product
from src.domain.condition import Condition


def quota_share(exposure: float, cession_PCT: float, limit: float = None) -> float:
    if not 0 <= cession_PCT <= 1:
        raise ValueError("Cession rate must be between 0 and 1")

    if limit is not None and limit < 0:
        raise ValueError("Limit must be positive if specified")

    ceded_amount = exposure * cession_PCT

    if limit is not None:
        return min(ceded_amount, limit)

    return ceded_amount


class QuotaShare(Product):
    def apply(self, exposure: float, condition: Condition) -> float:
        if pd.isna(condition.cession_pct):
            raise ValueError("CESSION_PCT is required for quota_share")

        if pd.notna(condition.limit):
            return quota_share(exposure, condition.cession_pct, condition.limit)
        else:
            return quota_share(exposure, condition.cession_pct)
