import pandas as pd
from typing import Dict, Any
from .calculation_engine import apply_program
from ..domain.bordereau import Bordereau
from ..domain.policy import Policy


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

    # Calcul ligne à ligne avec des Policy riches # AURE non car on va faire du snowpark
    results_list = []
    for pol in bordereau.policies():  # -> Policy
        result = apply_program(pol, program, calculation_date)
        results_list.append(result)

    results_df = pd.DataFrame(results_list, index=df.index)

    bordereau_with_net = df.copy()
    bordereau_with_net["cession_to_reinsurer"] = results_df["cession_to_reinsurer"]

    return bordereau_with_net, results_df
