from typing import Dict, Any, List, Optional, Literal
import sys
from .structure import Structure
from .condition import Condition


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
