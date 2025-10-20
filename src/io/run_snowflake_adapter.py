# src/io/run_snowflake_adapter.py
from __future__ import annotations
import pandas as pd


class RunSnowflakeIO:
    """
    Connecteur Run pour Snowflake (non implémenté).
    Prévu pour:
      - write(dest_dsn, runs_df, run_policies_df, run_policy_structures_df)
      - read(source_dsn) -> (runs_df, run_policies_df, run_policy_structures_df)
    DSN attendu: "snowflake://DB.SCHEMA.PREFIX" (ex: tables PREFIX_runs, PREFIX_run_policies, ...)
    """

    def write(
        self,
        dest_dsn: str,
        runs_df: pd.DataFrame,
        run_policies_df: pd.DataFrame,
        run_policy_structures_df: pd.DataFrame,
        **kwargs,
    ) -> None:
        raise NotImplementedError("RunSnowflakeIO.write is not implemented yet")

    def read(self, source_dsn: str, **kwargs):
        raise NotImplementedError("RunSnowflakeIO.read is not implemented yet")
