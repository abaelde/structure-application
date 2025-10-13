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
    
    results = []

    for _, row in bordereau_df.iterrows():
        policy_data = row.to_dict()
        result = apply_program(policy_data, program, calculation_date)
        results.append(result)

    results_df = pd.DataFrame(results)

    bordereau_with_net = bordereau_df.copy()
    bordereau_with_net["Cession_To_Reinsurer"] = results_df["cession_to_reinsurer"]

    return bordereau_with_net, results_df
