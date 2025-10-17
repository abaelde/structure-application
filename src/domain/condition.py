from typing import Dict, Any, List, Optional
import pandas as pd
from .constants import condition_COLS


class Condition:
    def __init__(self, data: Dict[str, Any]):
        self._data = data.copy()
        self.cession_pct = data.get(condition_COLS.CESSION_PCT)
        self.attachment = data.get(condition_COLS.ATTACHMENT)
        self.limit = data.get(condition_COLS.LIMIT)
        self.signed_share = data.get(condition_COLS.SIGNED_SHARE)
        self.includes_hull = data.get(condition_COLS.INCLUDES_HULL)
        self.includes_liability = data.get(condition_COLS.INCLUDES_LIABILITY)
        self._validate()

    def _validate(self):

        # Les conditions d'exclusion n'ont pas besoin de SIGNED_SHARE_PCT ni de INCLUDES_HULL/LIABILITY
        is_exclusion = self._data.get("BUSCL_EXCLUDE_CD") == "exclude"
        if is_exclusion:
            return

        if self.signed_share is None:
            raise ValueError(
                f"SIGNED_SHARE_PCT is required for all non-exclusion conditions. "
                f"condition data: {self._data}"
            )
        if not 0 <= self.signed_share <= 1:
            raise ValueError(
                f"SIGNED_SHARE_PCT must be between 0 and 1, got {self.signed_share}"
            )

        # Si un des deux flags est fourni, exiger qu'au moins un soit True
        if (self.includes_hull is not None or self.includes_liability is not None):
            if not bool(self.includes_hull) and not bool(self.includes_liability):
                raise ValueError("At least one of INCLUDES_HULL / INCLUDES_LIABILITY must be True")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Condition":
        """Factory method: create condition from dictionary"""
        return cls(data)

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def __getitem__(self, key: str):
        return self._data[key]

    def __setitem__(self, key: str, value: Any):
        self._data[key] = value
        if key == condition_COLS.CESSION_PCT:
            self.cession_pct = value
        elif key == condition_COLS.ATTACHMENT:
            self.attachment = value
        elif key == condition_COLS.LIMIT:
            self.limit = value
        elif key == condition_COLS.SIGNED_SHARE:
            self.signed_share = value
        elif key == condition_COLS.INCLUDES_HULL:
            self.includes_hull = value
        elif key == condition_COLS.INCLUDES_LIABILITY:
            self.includes_liability = value

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def copy(self) -> "Condition":
        return Condition(self._data.copy())

    def to_dict(self) -> Dict[str, Any]:
        return self._data.copy()

    def has_attachment(self) -> bool:
        return self.attachment is not None

    def has_limit(self) -> bool:
        return self.limit is not None

    def has_cession_pct(self) -> bool:
        return self.cession_pct is not None

    def get_values(self, key: str) -> list[str] | None:
        v = self._data.get(key)
        if v is None:
            return None
        if isinstance(v, (float, int)) and pd.isna(v):
            return None
        # Handle pandas NA specifically
        if hasattr(pd, "NA") and v is pd.NA:
            return None
        if isinstance(v, list):
            return v
        # Éventuellement, si tu veux fail-fast plutôt que convertir implicitement :
        raise ValueError(
            f"Dimension values must be a list[str]; got {type(v)} for key={key}"
        )

    def has_dimension(self, key: str) -> bool:
        vals = self.get_values(key)
        return vals is not None and len(vals) > 0

    def is_exclusion(self) -> bool:
        return self.get("BUSCL_EXCLUDE_CD") == "exclude"

    def describe(
        self,
        dimension_columns: list,
        type_of_participation: str,
        indent: str = "",
    ) -> str:
        """Generate a text description of this condition"""
        lines = []

        if type_of_participation == "quota_share":
            if pd.notna(self.get(condition_COLS.CESSION_PCT)):
                cession_pct = self[condition_COLS.CESSION_PCT]
                lines.append(
                    f"{indent}Cession rate: {cession_pct:.1%} ({cession_pct * 100:.1f}%)"
                )

            if pd.notna(self.get(condition_COLS.LIMIT)):
                lines.append(f"{indent}Limit: {self[condition_COLS.LIMIT]:,.2f}M")

        elif type_of_participation == "excess_of_loss":
            if pd.notna(self.get(condition_COLS.ATTACHMENT)) and pd.notna(
                self.get(condition_COLS.LIMIT)
            ):
                attachment = self[condition_COLS.ATTACHMENT]
                limit = self[condition_COLS.LIMIT]
                lines.append(f"{indent}Coverage: {limit:,.2f}M xs {attachment:,.2f}M")
                lines.append(
                    f"{indent}Range: {attachment:,.2f}M to {attachment + limit:,.2f}M"
                )

        if pd.notna(self.get(condition_COLS.SIGNED_SHARE)):
            reinsurer_share = self[condition_COLS.SIGNED_SHARE]
            lines.append(
                f"{indent}Reinsurer share: {reinsurer_share:.2%} ({reinsurer_share * 100:.2f}%)"
            )

        if self.includes_hull is not None or self.includes_liability is not None:
            coverage_parts = []
            if self.includes_hull is True:
                coverage_parts.append("Hull")
            if self.includes_liability is True:
                coverage_parts.append("Liability")

            if coverage_parts:
                coverage_str = " + ".join(coverage_parts)
                lines.append(f"{indent}Coverage scope: {coverage_str}")
            elif self.includes_hull is False and self.includes_liability is False:
                lines.append(f"{indent}Coverage scope: None (invalid)")

        conditions = []
        for dim in dimension_columns:
            vals = self.get_values(dim)
            if vals:
                conditions.append(f"{dim}=" + ";".join(map(str, vals)))

        if conditions:
            lines.append(f"{indent}Matching conditions: {', '.join(conditions)}")
        else:
            lines.append(f"{indent}Matching conditions: None (applies to all policies)")

        return "\n".join(lines)

    def rescale_for_predecessor(
        self, retention_factor: float
    ) -> tuple["Condition", Dict[str, Any]]:
        rescaled_condition = self.copy()
        rescaling_info = {
            "retention_factor": retention_factor,
            "original_attachment": None,
            "rescaled_attachment": None,
            "original_limit": None,
            "rescaled_limit": None,
        }

        if self.has_attachment():
            rescaling_info["original_attachment"] = self.attachment
            rescaled_condition[condition_COLS.ATTACHMENT] = (
                self.attachment * retention_factor
            )
            rescaling_info["rescaled_attachment"] = rescaled_condition.attachment

        if self.has_limit():
            rescaling_info["original_limit"] = self.limit
            rescaled_condition[condition_COLS.LIMIT] = self.limit * retention_factor
            rescaling_info["rescaled_limit"] = rescaled_condition.limit

        return rescaled_condition, rescaling_info
