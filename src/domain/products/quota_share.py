import pandas as pd
from typing import Dict, Any
from .base import Product
from src.domain.constants import SECTION_COLS as SC


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
    def apply(self, exposure: float, section: Dict[str, Any]) -> float:
        cession_PCT = section[SC.CESSION_PCT]
        if pd.isna(cession_PCT):
            raise ValueError("CESSION_PCT is required for quota_share")
        
        limit = section.get(SC.LIMIT)
        if pd.notna(limit):
            return quota_share(exposure, cession_PCT, limit)
        else:
            return quota_share(exposure, cession_PCT)
