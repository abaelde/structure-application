# src/serialization/codecs.py
from __future__ import annotations
from typing import Any, List, Optional
import pandas as pd

MULTI_VALUE_SEPARATOR = ";"


def to_bool(value) -> Optional[bool]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in {"1", "true", "yes", "y"}:
        return True
    if s in {"0", "false", "no", "n"}:
        return False
    return None


def split_multi(cell, sep: str = MULTI_VALUE_SEPARATOR) -> Optional[List[str]]:
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return None
    if isinstance(cell, list):
        vals = [str(t).strip() for t in cell if str(t).strip()]
        return vals or None
    toks = [t.strip() for t in str(cell).split(sep)]
    toks = [t for t in toks if t]
    return toks or None


def join_multi(
    values: Optional[List[str]], sep: str = MULTI_VALUE_SEPARATOR
) -> Optional[str]:
    if not values:
        return None
    out, seen = [], set()
    for v in values:
        s = str(v).strip()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return sep.join(out) if out else None


def pandas_to_native(v):
    if isinstance(v, list):
        return v
    if v is None:
        return None
    if isinstance(v, (float, int)) and pd.isna(v):
        return None
    if hasattr(pd, "NA") and v is pd.NA:
        return None
    return None if (hasattr(pd, "isna") and pd.isna(v)) else v
