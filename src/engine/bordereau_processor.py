import pandas as pd
from typing import Dict, Any, Optional
from src.domain import FIELDS
from .treaty_manager import TreatyManager


def apply_program_to_bordereau(
    bordereau_df: pd.DataFrame,
    program: Dict[str, Any],
    calculation_date: Optional[str] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    from .calculation_engine import apply_program
    
    results = bordereau_df.apply(
        lambda row: apply_program(row.to_dict(), program, calculation_date),
        axis=1
    ).tolist()

    results_df = pd.DataFrame(results)

    bordereau_with_net = bordereau_df.copy()
    bordereau_with_net["cession_to_reinsurer"] = results_df["cession_to_reinsurer"]

    return bordereau_with_net, results_df
