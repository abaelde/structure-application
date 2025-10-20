# src/io/program_csv_folder_adapter.py
from __future__ import annotations
from pathlib import Path
from typing import Tuple
import pandas as pd


class CsvProgramFolderIO:
    """
    Lit/écrit un programme stocké dans un dossier contenant 3 CSV:
      - program.csv
      - structures.csv
      - conditions.csv

    """

    PROGRAM_FILE = "program.csv"
    STRUCTURES_FILE = "structures.csv"
    CONDITIONS_FILE = "conditions.csv"
    EXCLUSIONS_FILE = "exclusions.csv"

    def _read_one(self, folder: Path, primary: str, *alts: str) -> pd.DataFrame:
        candidates = [folder / primary, *[folder / a for a in alts]]
        for f in candidates:
            if f.exists():
                # Laisse pandas inférer les types (comme Excel)
                return pd.read_csv(f)
        names = ", ".join(str(c.name) for c in candidates)
        raise FileNotFoundError(f"Missing required CSV in {folder}: one of [{names}]")

    def read(self, folder: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        p = Path(folder)
        if not p.exists() or not p.is_dir():
            raise ValueError(
                f"Program source must be a folder with CSV files: {folder}"
            )

        program_df = self._read_one(p, self.PROGRAM_FILE, "PROGRAM.csv", "programs.csv")
        structures_df = self._read_one(p, self.STRUCTURES_FILE, "STRUCTURES.csv")
        conditions_df = self._read_one(p, self.CONDITIONS_FILE, "CONDITIONS.csv")
        excl_path = p / self.EXCLUSIONS_FILE
        exclusions_df = pd.read_csv(excl_path) if excl_path.exists() else pd.DataFrame()
        return program_df, structures_df, conditions_df, exclusions_df

    def write(
        self,
        dest_folder: str,
        program_df: pd.DataFrame,
        structures_df: pd.DataFrame,
        conditions_df: pd.DataFrame,
        exclusions_df: pd.DataFrame,
    ) -> None:
        p = Path(dest_folder)
        p.mkdir(parents=True, exist_ok=True)
        program_df.to_csv(p / self.PROGRAM_FILE, index=False)
        structures_df.to_csv(p / self.STRUCTURES_FILE, index=False)
        conditions_df.to_csv(p / self.CONDITIONS_FILE, index=False)
        exclusions_df.to_csv(p / self.EXCLUSIONS_FILE, index=False)
