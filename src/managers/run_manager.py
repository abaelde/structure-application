# src/managers/run_manager.py
from __future__ import annotations
from typing import Literal, Optional, Dict, Any
import pandas as pd
from src.serialization.run_serializer import RunSerializer, RunMeta
from src.io.run_csv_adapter import RunCsvIO
from src.io.run_snowflake_adapter import RunSnowflakeIO

Backend = Literal["csv", "snowflake"]


class RunManager:
    """
    Manager pour persister les résultats de run:
      - backend 'csv' (implémenté)
      - backend 'snowflake' (stub)
    """

    @staticmethod
    def detect_backend(dest: str) -> Backend:
        return "snowflake" if dest.lower().startswith("snowflake://") else "csv"

    def __init__(self, backend: Backend = "csv"):
        self.backend = backend
        self.serializer = RunSerializer()
        self.io = self._make_io(backend)

    def _make_io(self, backend: Backend):
        if backend == "csv":
            return RunCsvIO()
        elif backend == "snowflake":
            return RunSnowflakeIO()
        raise ValueError(f"Unknown run backend: {backend}")

    def save(
        self,
        run_meta: RunMeta,
        results_df: pd.DataFrame,
        dest: str,
        *,
        source_policy_df: Optional[pd.DataFrame] = None,
        io_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, pd.DataFrame]:
        io_kwargs = io_kwargs or {}
        dfs = self.serializer.build_dataframes(run_meta, results_df, source_policy_df)

        if self.backend == "csv":
            self.io.write(
                dest, dfs["runs"], dfs["run_policies"], dfs["run_policy_structures"]
            )
        else:
            self.io.write(
                dest,
                dfs["runs"],
                dfs["run_policies"],
                dfs["run_policy_structures"],
                **io_kwargs,
            )

        return dfs
