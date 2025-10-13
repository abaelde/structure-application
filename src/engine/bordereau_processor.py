import pandas as pd
from typing import Dict, Any, Optional
from .calculation_engine import apply_program


def apply_program_to_bordereau(
    bordereau_df: pd.DataFrame,
    program: Dict[str, Any],
    calculation_date: Optional[str] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    

    results_df = bordereau_df.apply(
        lambda row: pd.Series(apply_program(row.to_dict(), program, calculation_date)),
        axis=1
    )

    bordereau_with_net = bordereau_df.copy()
    bordereau_with_net["cession_to_reinsurer"] = results_df["cession_to_reinsurer"]

    return bordereau_with_net, results_df
