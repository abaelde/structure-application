# src/serialization/program_frames.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Set
import pandas as pd
from src.domain.schema import PROGRAM_TO_BORDEREAU_DIMENSIONS

DIM_FLAGS = {"INCLUDES_HULL", "INCLUDES_LIABILITY"}


def _snowflake_dim_names() -> Set[str]:
    names: Set[str] = set()
    for v in PROGRAM_TO_BORDEREAU_DIMENSIONS.values():
        if isinstance(v, dict):
            names.update(v.values())
        else:
            names.add(v)
    return names - DIM_FLAGS


def condition_dims_in(df: pd.DataFrame) -> List[str]:
    """Colonnes de dimensions présentes dans un DF 'conditions' (noms Snowflake)."""
    if df is None or df.empty:
        return []
    snow_cols = _snowflake_dim_names()
    return [c for c in df.columns if c in snow_cols]


def exclusion_dims_in(df: pd.DataFrame) -> List[str]:
    if df is None or df.empty:
        return []
    snow_cols = _snowflake_dim_names()
    return [c for c in df.columns if c in snow_cols]


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