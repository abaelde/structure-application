from typing import Dict, Any, List, Optional, Self
import pandas as pd
from .condition import Condition
from .constants import CONDITION_COLS, PRODUCT, CLAIM_BASIS, CLAIM_BASIS_VALUES
from .financial_terms import FinancialTerms, FIELD_TO_TERMS_KEY


class Structure:
    def __init__(
        self,
        structure_name: str,
        type_of_participation: str,
        conditions: List[Condition],
        predecessor_title: Optional[str] = None,
        claim_basis: str = None,
        inception_date: str = None,
        expiry_date: str = None,
        # Valeurs par défaut (nouvelle architecture)
        cession_pct: Optional[float] = None,
        limit: Optional[float] = None,
        attachment: Optional[float] = None,
        signed_share: float = 1.0,
    ):
        self.structure_name = structure_name
        self.type_of_participation = type_of_participation
        self.predecessor_title = predecessor_title
        
        # Valeurs par défaut (nouvelle architecture)
        self.cession_pct = cession_pct
        self.limit = limit
        self.attachment = attachment
        self.signed_share = signed_share

        # --- validation claim basis obligatoire
        basis = (claim_basis or "").strip().lower()
        if basis not in CLAIM_BASIS_VALUES:
            raise ValueError(
                f"CLAIMS_BASIS is required and must be one of "
                f"{sorted(CLAIM_BASIS_VALUES)}; got '{claim_basis}'"
            )
        self.claim_basis = basis

        # --- dates obligatoires
        self.inception_date = self._require_ts(inception_date, "EFFECTIVE_DATE")
        self.expiry_date = self._require_ts(expiry_date, "INSPER_EXPIRY_DATE")
        # borne: [inception; expiry[
        if self.expiry_date <= self.inception_date:
            raise ValueError(
                f"INSPER_EXPIRY_DATE must be strictly after EFFECTIVE_DATE "
                f"({self.inception_date} .. {self.expiry_date})"
            )
        self.conditions = conditions

    @property
    def default_terms(self) -> FinancialTerms:
        """
        Retourne les termes financiers par défaut de la structure.
        
        Returns:
            Instance FinancialTerms avec les valeurs par défaut de la structure
        """
        return FinancialTerms(
            cession_pct=self.cession_pct,
            attachment=self.attachment,
            limit=self.limit,
            signed_share=self.signed_share,
        )

    @staticmethod
    def _require_ts(val, field_name: str) -> pd.Timestamp:
        try:
            ts = pd.to_datetime(val)
        except Exception:
            ts = None
        if ts is None or (isinstance(ts, pd.Timestamp) and pd.isna(ts)):
            raise ValueError(
                f"{field_name} is required and must be a valid date, got: {val}"
            )
        return ts

    @classmethod
    def from_row(
        cls,
        structure_row: Dict[str, Any],
        conditions_data: List[Dict[str, Any]],
        structure_cols,
    ) -> Self:
        """
        Factory method: create Structure from dictionary data.
        The Structure knows how to find and link its own conditions.
        """
        # Create condition objects
        conditions = [Condition.from_dict(s) for s in conditions_data]

        # Create and return Structure
        return cls(
            structure_name=structure_row[structure_cols.NAME],
            type_of_participation=structure_row[structure_cols.TYPE],
            conditions=conditions,
            predecessor_title=structure_row.get(structure_cols.PREDECESSOR),
            claim_basis=structure_row.get(structure_cols.CLAIM_BASIS),
            inception_date=structure_row.get(structure_cols.INCEPTION),
            expiry_date=structure_row.get(structure_cols.EXPIRY),
            # Valeurs par défaut de la structure
            cession_pct=structure_row.get("CESSION_PCT"),
            limit=structure_row.get("LIMIT_100"),
            attachment=structure_row.get("ATTACHMENT_POINT_100"),
            signed_share=structure_row.get("SIGNED_SHARE_PCT"),
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

    def create_default_condition(self) -> Condition:
        """Créer une condition par défaut avec les valeurs de la structure."""
        base = self.default_terms.to_condition_dict()
        base |= {"INCLUDES_HULL": None, "INCLUDES_LIABILITY": None}
        return Condition.from_dict(base)

    def resolve_condition(self, template_condition_dict: Dict[str, Any], overrides: Dict[str, Any]) -> Condition:
        """
        Fusionne les defaults de la structure + overrides financiers dans une Condition 'résolue'.
        
        Args:
            template_condition_dict: Dictionnaire de base de la condition (dimensions, flags, etc.)
            overrides: Dictionnaire des overrides financiers à appliquer
            
        Returns:
            Condition résolue avec les termes financiers fusionnés
        """
        # 1) termes par défaut
        terms = self.default_terms
        # 2) appliquer overrides (convertir noms de champs physiques -> attributs du VO)
        kw = {FIELD_TO_TERMS_KEY[k]: v for k, v in overrides.items() if k in FIELD_TO_TERMS_KEY}
        terms = terms.merge(**kw)
        # 3) produire la condition finale (dimensions/flags du template + termes effectifs)
        data = dict(template_condition_dict)
        data.update(terms.to_condition_dict())
        return Condition.from_dict(data)

    # ─── Sélection temporelle RA/LO multi-année (sans LossDate) ───────────
    def _in_range(self, dt: Optional[pd.Timestamp]) -> bool:
        """Intervalle [inception_date ; expiry_date[ (expiry exclusive)."""
        if dt is None:
            return False
        if self.inception_date and dt < self.inception_date:
            return False
        if self.expiry_date and dt >= self.expiry_date:
            return False
        return True

    def is_applicable(
        self,
        policy,  # Policy
        *,
        evaluation_date: Optional[str] = None,
    ) -> bool:
        """
        - Risk attaching  → référence = INCEPTION_DT de la police
        - Loss occurring  → référence = calculation_date (evaluation_date)
        """
        # - RA → référence = INCEPTION_DT
        # - LO → référence = calculation_date
        if self.claim_basis == CLAIM_BASIS.LOSS_OCCURRING:
            ref = (
                pd.to_datetime(evaluation_date) if evaluation_date is not None else None
            )
            return self._in_range(ref)
        # RA
        return self._in_range(policy.inception)

    def describe(self, dimension_columns: list, structure_number: int) -> str:
        """Generate a compact text description of this structure, grouping similar conditions"""
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

        # Afficher les valeurs par défaut de la structure
        lines.append("   Default values (applies to all policies not matching specific conditions):")
        if self.type_of_participation == PRODUCT.QUOTA_SHARE:
            if self.cession_pct is not None:
                lines.append(f"      Cession rate: {self.cession_pct:.1%} ({self.cession_pct * 100:.1f}%)")
            if self.signed_share is not None:
                lines.append(f"      Reinsurer share: {self.signed_share:.2%} ({self.signed_share * 100:.2f}%)")
        elif self.type_of_participation == PRODUCT.EXCESS_OF_LOSS:
            if self.attachment is not None and self.limit is not None:
                lines.append(f"      Coverage: {self.limit:,.2f}M xs {self.attachment:,.2f}M")
                lines.append(f"      Range: {self.attachment:,.2f}M to {self.attachment + self.limit:,.2f}M")

        # Afficher les conditions spécifiques
        if self.conditions:
            lines.append("   Specific conditions:")
            # Group conditions by their core parameters (excluding dimension values)
            condition_groups = self._group_similar_conditions()

            if len(condition_groups) == 1:
                group = condition_groups[0]
                lines.append(
                    self._describe_condition_group(group, dimension_columns, "      ")
                )
            else:
                for j, group in enumerate(condition_groups, 1):
                    lines.append(f"      Group {j}:")
                    lines.append(
                        self._describe_condition_group(
                            group, dimension_columns, "         "
                        )
                    )
        else:
            lines.append("   No specific conditions (only default values apply)")

        return "\n".join(lines)

    def _group_similar_conditions(self) -> List[Dict]:
        """Group conditions that have the same core parameters but different dimension values"""
        groups = []

        for condition in self.conditions:
            # Create a signature for the condition (excluding dimension values)
            signature = self._get_condition_signature(condition)

            # Find existing group with same signature
            found_group = None
            for group in groups:
                if group["signature"] == signature:
                    found_group = group
                    break

            if found_group:
                found_group["conditions"].append(condition)
            else:
                groups.append(
                    {
                        "signature": signature,
                        "conditions": [condition],
                        "sample_condition": condition,
                    }
                )

        return groups

    def _get_condition_signature(self, condition: Condition) -> tuple:
        """Get a signature for a condition excluding dimension values"""
        signature = (
            condition.cession_pct,
            condition.attachment,
            condition.limit,
            condition.signed_share,
            condition.includes_hull,
            condition.includes_liability,
        )
        return signature

    def defaults_dict(self) -> Dict[str, Any]:
        """Retourne un dictionnaire des valeurs par défaut de la structure."""
        return {
            "CESSION_PCT": self.cession_pct,
            "LIMIT_100": self.limit,
            "ATTACHMENT_POINT_100": self.attachment,
            "SIGNED_SHARE_PCT": self.signed_share,
        }

    def overrides_for(self, condition_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Restitue les overrides (diff) vs defaults à partir d'une condition finale.
        
        Args:
            condition_dict: Dictionnaire de la condition finale
            
        Returns:
            Dictionnaire des overrides (valeurs qui diffèrent des defaults)
        """
        base = self.default_terms
        actual = FinancialTerms(
            cession_pct=condition_dict.get("CESSION_PCT"),
            attachment=condition_dict.get("ATTACHMENT_POINT_100"),
            limit=condition_dict.get("LIMIT_100"),
            signed_share=condition_dict.get("SIGNED_SHARE_PCT"),
        )
        return base.diff(actual)

    def _describe_condition_group(
        self, group: Dict, dimension_columns: list, indent: str
    ) -> str:
        """Describe a group of similar conditions"""
        sample_condition = group["sample_condition"]
        conditions = group["conditions"]

        lines = []

        # Describe the core parameters (same for all conditions in the group)
        if self.type_of_participation == PRODUCT.QUOTA_SHARE:
            if pd.notna(sample_condition.get(CONDITION_COLS.CESSION_PCT)):
                cession_pct = sample_condition[CONDITION_COLS.CESSION_PCT]
                lines.append(
                    f"{indent}Cession rate: {cession_pct:.1%} ({cession_pct * 100:.1f}%)"
                )

            if pd.notna(
                sample_condition.get(CONDITION_COLS.LIMIT)
            ):  # AURE : pk du pandas a ce niveau ?
                lines.append(
                    f"{indent}Limit: {sample_condition[CONDITION_COLS.LIMIT]:,.2f}M"
                )

        elif self.type_of_participation == PRODUCT.EXCESS_OF_LOSS:
            if pd.notna(sample_condition.get(CONDITION_COLS.ATTACHMENT)) and pd.notna(
                sample_condition.get(CONDITION_COLS.LIMIT)
            ):
                attachment = sample_condition[CONDITION_COLS.ATTACHMENT]
                limit = sample_condition[CONDITION_COLS.LIMIT]
                lines.append(f"{indent}Coverage: {limit:,.2f}M xs {attachment:,.2f}M")
                lines.append(
                    f"{indent}Range: {attachment:,.2f}M to {attachment + limit:,.2f}M"
                )

        if pd.notna(sample_condition.get(CONDITION_COLS.SIGNED_SHARE)):
            reinsurer_share = sample_condition[CONDITION_COLS.SIGNED_SHARE]
            lines.append(
                f"{indent}Reinsurer share: {reinsurer_share:.2%} ({reinsurer_share * 100:.2f}%)"
            )

        if (
            sample_condition.includes_hull is not None
            or sample_condition.includes_liability is not None
        ):
            coverage_parts = []
            if sample_condition.includes_hull is True:
                coverage_parts.append("Hull")
            if sample_condition.includes_liability is True:
                coverage_parts.append("Liability")

            if coverage_parts:
                coverage_str = " + ".join(coverage_parts)
                lines.append(f"{indent}Coverage scope: {coverage_str}")
            elif (
                sample_condition.includes_hull is False
                and sample_condition.includes_liability is False
            ):
                lines.append(f"{indent}Coverage scope: None (invalid)")

        # Describe dimension values (grouped by dimension)
        dimension_info = []
        for dim in dimension_columns:
            # Collect all unique values for this dimension across all conditions in the group
            all_values = set()
            for condition in conditions:
                vals = condition.get_values(dim)
                if vals:
                    all_values.update(vals)

            if all_values:
                sorted_values = sorted(all_values)
                if len(sorted_values) == 1:
                    dimension_info.append(f"{dim}={sorted_values[0]}")
                else:
                    dimension_info.append(f"{dim}=[{', '.join(sorted_values)}]")

        if dimension_info:
            lines.append(f"{indent}Matching conditions: {', '.join(dimension_info)}")
        else:
            lines.append(f"{indent}Matching conditions: None (applies to all policies)")

        return "\n".join(lines)
