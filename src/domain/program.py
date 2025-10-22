from typing import Dict, Any, List, Optional, Literal
import sys
from .structure import Structure
from .condition import Condition
from .exclusion import ExclusionRule


class Program:
    def __init__(
        self,
        name: str,
        structures: List[Structure],
        dimension_columns: List[str],
        underwriting_department: Literal["aviation", "casualty", "test"],
        exclusions: Optional[List[ExclusionRule]] = None,
    ):
        self.name = name
        self.dimension_columns = dimension_columns
        self.structures = structures
        self.underwriting_department = underwriting_department
        self.exclusions = exclusions or []

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

    def _sort_structures_logically(self) -> List[Structure]:
        """Trier les structures par ordre logique métier :
        1. Quota Share en premier (point d'entrée)
        2. XOL par ordre d'attachment croissant
        """
        quota_shares = []
        excess_of_loss = []
        
        for structure in self.structures:
            if structure.type_of_participation == "quota_share":
                quota_shares.append(structure)
            elif structure.type_of_participation == "excess_of_loss":
                excess_of_loss.append(structure)
            else:
                # Autres types de structures (pour l'avenir)
                excess_of_loss.append(structure)
        
        # Trier les XOL par attachment croissant (ou par nom si attachment identique)
        excess_of_loss.sort(key=lambda s: (s.attachment or 0, s.structure_name))
        
        return quota_shares + excess_of_loss

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "structures": [s.to_dict() for s in self.structures],
            "dimension_columns": self.dimension_columns,
            "underwriting_department": self.underwriting_department,
            "exclusions": [
                {
                    "values_by_dimension": e.values_by_dimension,
                    "reason": e.reason,
                    "effective_date": (
                        str(e.effective_date) if e.effective_date is not None else None
                    ),
                    "expiry_date": (
                        str(e.expiry_date) if e.expiry_date is not None else None
                    ),
                }
                for e in self.exclusions
            ],
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

        # Trier les structures par ordre logique métier
        sorted_structures = self._sort_structures_logically()
        
        for i, structure in enumerate(sorted_structures, 1):
            lines.append(structure.describe(self.dimension_columns, i))

        lines.append("\n" + "=" * 80)
        if self.exclusions:
            lines.append("PROGRAM EXCLUSIONS")
            lines.append("=" * 80)
            for i, e in enumerate(self.exclusions, 1):
                dims = ", ".join(
                    f"{k}=[{', '.join(v)}]" for k, v in e.values_by_dimension.items()
                )
                period = ""
                if e.effective_date or e.expiry_date:
                    period = (
                        f" (period: {e.effective_date} .. {e.expiry_date} exclusive)"
                    )
                lines.append(f"- Excl {i}: {dims}{period}  name={e.name or 'N/A'}")
            lines.append("=" * 80)

        description = "\n".join(lines)
        file.write(description + "\n")
        return description
