# src/io/run_csv_adapter.py
from __future__ import annotations
from pathlib import Path
import pandas as pd


class RunCsvIO:
    """
    Écrit/Lit les 3 tables de run dans un dossier CSV.
    Fichiers:
      - runs.csv
      - run_policies.csv
      - run_policy_structures.csv
    """

    RUNS = "runs.csv"
    POLICIES = "run_policies.csv"
    STRUCTURES = "run_policy_structures.csv"

    def write(
        self,
        dest_folder: str,
        runs_df: pd.DataFrame,
        run_policies_df: pd.DataFrame,
        run_policy_structures_df: pd.DataFrame,
    ) -> None:
        p = Path(dest_folder)
        p.mkdir(parents=True, exist_ok=True)
        runs_df.to_csv(p / self.RUNS, index=False)
        run_policies_df.to_csv(p / self.POLICIES, index=False)
        run_policy_structures_df.to_csv(p / self.STRUCTURES, index=False)

    def read(self, folder: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        p = Path(folder)
        runs = pd.read_csv(p / self.RUNS)
        pols = pd.read_csv(p / self.POLICIES)
        strs = pd.read_csv(p / self.STRUCTURES)
        return runs, pols, strs
