from typing import Dict, Any, List, Optional, Literal
import pandas as pd
import sys
from .constants import condition_COLS, PRODUCT


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

        if self.includes_hull is not None and self.includes_liability is not None:
            if not self.includes_hull and not self.includes_liability:
                raise ValueError(
                    f"At least one of INCLUDES_HULL or INCLUDES_LIABILITY must be True. "
                    f"condition data: {self._data}"
                )

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
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        # En mémoire on s'assure déjà d'avoir list[str] via le loader,
        # mais on reste tolérant si des tests injectent un scalaire.
        if isinstance(v, (list, tuple, set)):
            return list(v)
        return [str(v)]

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

        if type_of_participation == PRODUCT.QUOTA_SHARE:
            if pd.notna(self.get(condition_COLS.CESSION_PCT)):
                cession_pct = self[condition_COLS.CESSION_PCT]
                lines.append(
                    f"{indent}Cession rate: {cession_pct:.1%} ({cession_pct * 100:.1f}%)"
                )

            if pd.notna(self.get(condition_COLS.LIMIT)):
                lines.append(f"{indent}Limit: {self[condition_COLS.LIMIT]:,.2f}M")

        elif type_of_participation == PRODUCT.EXCESS_OF_LOSS:
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


class Structure:
    def __init__(
        self,
        structure_name: str,
        contract_order: int,
        type_of_participation: str,
        conditions: List[Condition],
        predecessor_title: Optional[str] = None,
        claim_basis: Optional[str] = None,
        inception_date: Optional[str] = None,
        expiry_date: Optional[str] = None,
    ):
        self.structure_name = structure_name
        self.contract_order = contract_order
        self.type_of_participation = type_of_participation
        self.predecessor_title = predecessor_title
        self.claim_basis = claim_basis
        self.inception_date = inception_date
        self.expiry_date = expiry_date
        self.conditions = conditions

    @classmethod
    def from_row(
        cls,
        structure_row: Dict[str, Any],
        conditions_data: List[Dict[str, Any]],
        structure_cols,
    ) -> "Structure":
        """
        Factory method: create Structure from dictionary data.
        The Structure knows how to find and link its own conditions.
        """
        # Create condition objects
        conditions = [Condition.from_dict(s) for s in conditions_data]

        # Create and return Structure
        return cls(
            structure_name=structure_row[structure_cols.NAME],
            contract_order=structure_row[structure_cols.ORDER],
            type_of_participation=structure_row[structure_cols.TYPE],
            conditions=conditions,
            predecessor_title=structure_row.get(structure_cols.PREDECESSOR),
            claim_basis=structure_row.get(structure_cols.CLAIM_BASIS),
            inception_date=structure_row.get(structure_cols.INCEPTION),
            expiry_date=structure_row.get(structure_cols.EXPIRY),
        )

    def get(self, key: str, default=None):
        return getattr(self, key, default)

    def __getitem__(self, key: str):
        if not hasattr(self, key):
            raise KeyError(f"'{key}' not found in Structure")
        return getattr(self, key)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "structure_name": self.structure_name,
            "contract_order": self.contract_order,
            "type_of_participation": self.type_of_participation,
            "predecessor_title": self.predecessor_title,
            "claim_basis": self.claim_basis,
            "inception_date": self.inception_date,
            "expiry_date": self.expiry_date,
            "conditions": [s.to_dict() for s in self.conditions],
        }

    def has_predecessor(self) -> bool:
        return self.predecessor_title is not None

    def is_quota_share(self) -> bool:
        return self.type_of_participation == PRODUCT.QUOTA_SHARE

    def is_excess_of_loss(self) -> bool:
        return self.type_of_participation == PRODUCT.EXCESS_OF_LOSS

    def calculate_retention_pct(self, matched_condition: Condition) -> float:
        if self.is_quota_share() and matched_condition.has_cession_pct():
            return 1.0 - matched_condition.cession_pct
        return 1.0

    def describe(self, dimension_columns: list, structure_number: int) -> str:
        """Generate a text description of this structure"""
        lines = []

        lines.append(f"\nStructure {structure_number}: {self.structure_name}")
        lines.append(f"   Type: {self.type_of_participation}")

        predecessor_title = self.predecessor_title
        if predecessor_title and pd.notna(predecessor_title):
            lines.append(f"   Predecessor: {predecessor_title} (Inuring)")
        else:
            lines.append(f"   Predecessor: None (Entry point)")

        lines.append(f"   Number of conditions: {len(self.conditions)}")

        if self.claim_basis and pd.notna(self.claim_basis):
            lines.append(f"   Claim basis: {self.claim_basis}")
        if self.inception_date and pd.notna(self.inception_date):
            lines.append(f"   Inception date: {self.inception_date}")
        if self.expiry_date and pd.notna(self.expiry_date):
            lines.append(f"   Expiry date: {self.expiry_date}")

        if len(self.conditions) == 1:
            condition = self.conditions[0]
            lines.append("   Single condition:")
            lines.append(
                condition.describe(
                    dimension_columns,
                    self.type_of_participation,
                    indent="      ",
                )
            )
        else:
            lines.append("   conditions:")
            for j, condition in enumerate(self.conditions, 1):
                lines.append(f"      condition {j}:")
                lines.append(
                    condition.describe(
                        dimension_columns,
                        self.type_of_participation,
                        indent="         ",
                    )
                )

        return "\n".join(lines)


class Program:
    def __init__(
        self,
        name: str,
        structures: List[Structure],
        dimension_columns: List[str],
        underwriting_department: Literal["aviation", "casualty", "test"],
    ):
        self.name = name
        self.dimension_columns = dimension_columns
        self.structures = structures
        self.underwriting_department = underwriting_department

    def __getitem__(self, key: str):
        if not hasattr(self, key):
            raise KeyError(f"'{key}' not found in Program")
        return getattr(self, key)

    @property
    def all_conditions(self) -> List[Condition]:
        """Returns all conditions from all structures"""
        conditions = []
        for structure in self.structures:
            conditions.extend(structure.conditions)
        return conditions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "structures": [s.to_dict() for s in self.structures],
            "dimension_columns": self.dimension_columns,
            "underwriting_department": self.underwriting_department,
        }

    def describe(self, file=None) -> str:
        """Generate a complete text description of the program"""
        if file is None:
            file = sys.stdout

        lines = []
        lines.append("=" * 80)
        lines.append("PROGRAM CONFIGURATION")
        lines.append("=" * 80)
        lines.append(f"Program name: {self.name}")
        lines.append(f"Underwriting department: {self.underwriting_department}")
        lines.append(f"Number of structures: {len(self.structures)}")
        lines.append(f"Matching dimensions: {len(self.dimension_columns)}")

        if self.dimension_columns:
            lines.append(f"   Dimensions: {', '.join(self.dimension_columns)}")
        else:
            lines.append("   No dimensions (all policies treated the same way)")

        lines.append("\n" + "-" * 80)
        lines.append("STRUCTURE DETAILS")
        lines.append("-" * 80)

        for i, structure in enumerate(self.structures, 1):
            lines.append(structure.describe(self.dimension_columns, i))

        lines.append("\n" + "=" * 80)

        description = "\n".join(lines)
        file.write(description + "\n")
        return description
