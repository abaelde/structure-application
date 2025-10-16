import pandas as pd
from typing import Dict, Any
from .calculation_engine import apply_program
from ..domain.bordereau import Bordereau


def apply_program_to_bordereau(
    bordereau: Bordereau,
    program: Dict[str, Any],
    calculation_date: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    
    # Associe le programme au bordereau si pas déjà fait
    if not bordereau.program:
        bordereau.program = program
    
    # Validation avec l'underwriting_department du programme associé
    bordereau.validate_exposure_columns()

    df = bordereau.to_engine_dataframe().copy()
    results_df = df.apply(
        lambda row: pd.Series(apply_program(row.to_dict(), program, calculation_date)),
        axis=1
    )

    bordereau_with_net = df.copy()
    bordereau_with_net["cession_to_reinsurer"] = results_df["cession_to_reinsurer"]

    return bordereau_with_net, results_df
