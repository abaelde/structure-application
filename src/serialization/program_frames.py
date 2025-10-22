# src/serialization/program_frames.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Set
import pandas as pd
from src.domain.schema import dims_in

# Wrappers pour compatibilité (ou on peut appeler dims_in directement)
def condition_dims_in(df: pd.DataFrame) -> List[str]:
    """Colonnes de dimensions présentes dans un DF 'conditions' (noms Snowflake)."""
    return dims_in(df)


def exclusion_dims_in(df: pd.DataFrame) -> List[str]:
    """Colonnes de dimensions présentes dans un DF 'exclusions' (noms Snowflake)."""
    return dims_in(df)


@dataclass
class ProgramFrames:
    program: pd.DataFrame
    structures: pd.DataFrame
    conditions: pd.DataFrame
    exclusions: pd.DataFrame

    def clone(self) -> "ProgramFrames":
        return ProgramFrames(
            self.program.copy(),
            self.structures.copy(),
            self.conditions.copy(),
            self.exclusions.copy(),
        )

    def for_csv(self) -> "ProgramFrames":
        """Encode les listes de dimensions en 'a;b;c' pour l'export CSV/Snowflake (stockage string)."""
        from .codecs import join_multi

        out = self.clone()
        for col in condition_dims_in(out.conditions):
            out.conditions[col] = out.conditions[col].map(join_multi)
        for col in exclusion_dims_in(out.exclusions):
            out.exclusions[col] = out.exclusions[col].map(join_multi)
        return out