# src/io/bordereau_csv_adapter.py
from __future__ import annotations
from typing import Optional, Dict, Any
import pandas as pd

class CsvBordereauIO:
    def read(self, source: str, read_csv_kwargs: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        read_csv_kwargs = read_csv_kwargs or {}
        return pd.read_csv(source, **read_csv_kwargs)

    def write(self, dest: str, df: pd.DataFrame, *, index: bool = False) -> None:
        df.to_csv(dest, index=index)
