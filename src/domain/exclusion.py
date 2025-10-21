from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import pandas as pd

@dataclass(frozen=True)
class ExclusionRule:
    values_by_dimension: Dict[str, List[str]]
    name: Optional[str] = None
    effective_date: Optional[pd.Timestamp] = None  # optional
    expiry_date: Optional[pd.Timestamp] = None     # optional

    @staticmethod
    def _to_ts(v) -> Optional[pd.Timestamp]:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        try:
            return pd.to_datetime(v)
        except Exception:
            return None

    @classmethod
    def from_row(cls, row: Dict[str, Any], dimension_columns: List[str]) -> "ExclusionRule":
        values: Dict[str, List[str]] = {}
        for dim in dimension_columns:
            cell = row.get(dim)
            if cell is None or (isinstance(cell, float) and pd.isna(cell)):
                continue
            if isinstance(cell, list):
                vals = [str(x).strip() for x in cell if str(x).strip()]
            else:
                # support CSV "a;b;c"
                vals = [t.strip() for t in str(cell).split(";") if t.strip()]
            if vals:
                values[dim] = vals

        return cls(
            values_by_dimension=values,
            name=row.get("EXCLUSION_NAME"),
            effective_date=cls._to_ts(row.get("EXCL_EFFECTIVE_DATE")),
            expiry_date=cls._to_ts(row.get("EXCL_EXPIRY_DATE")),
        )

    def matches(self, policy, dimension_mapping: Dict[str, str], *, calculation_date: Optional[str] = None) -> bool:
        # Optional temporal filter (if dates provided)
        if self.effective_date is not None or self.expiry_date is not None:
            calc = pd.to_datetime(calculation_date) if calculation_date else None
            if calc is None:
                return False
            if self.effective_date and calc < self.effective_date:
                return False
            if self.expiry_date and calc >= self.expiry_date:
                return False

        # Dimension matching
        for dim, cond_values in self.values_by_dimension.items():
            policy_val = policy.get_dimension_value(dim)
            if policy_val is None or not isinstance(policy_val, str):
                return False
            pv = policy_val.strip()
            if pv not in {str(v).strip() for v in cond_values}:
                return False
        return True
