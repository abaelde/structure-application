# src/serialization/compact.py
from __future__ import annotations
from typing import Any, Dict, List, Sequence
import pandas as pd
from .codecs import split_multi, join_multi

def compact_multivalue(
    df: pd.DataFrame,
    *,
    dims: Sequence[str],
    group_cols: Sequence[str],
    sep: str = ";",
) -> pd.DataFrame:
    """Regroupe les lignes identiques hors dimensions et concatène chaque dimension en tokens dédupliqués/ordonnés."""
    if df is None or df.empty or not dims:
        return df
    norm = df.copy()
    for col in dims:
        if col in norm.columns:
            norm[col] = norm[col].map(split_multi, na_action="ignore")
    rows: List[Dict[str, Any]] = []
    # dropna=False pour garder les groupes avec NaN
    for keys, grp in norm.groupby(list(group_cols), dropna=False, sort=False):
        if not isinstance(keys, tuple): keys = (keys,)
        base = {c: v for c, v in zip(group_cols, keys)}
        for dim in dims:
            vals = []
            seen = set()
            for cell in grp.get(dim, []):
                for t in (cell or []):
                    if t not in seen:
                        seen.add(t); vals.append(t)
            base[dim] = join_multi(vals, sep=sep)
        rows.append(base)
    # colonnes en sortie = group_cols + dims (ordre stable)
    return pd.DataFrame(rows, columns=[*group_cols, *dims])
