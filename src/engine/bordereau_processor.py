import pandas as pd
from typing import Dict, Any, Optional
from .calculation_engine import apply_program
from .exposure_validation import validate_exposure_columns
from ..domain.bordereau import Bordereau


def apply_program_to_bordereau(
    bordereau: Bordereau,
    program: Dict[str, Any],
    calculation_date: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    
    # Utilise le DataFrame canonique de l'objet Bordereau
    df = bordereau.to_engine_dataframe().copy()
    # LOB la plus fiable dispo
    lob = bordereau.line_of_business or program.underwriting_department
    
    validate_exposure_columns(df.columns.tolist(), lob)
    
    print(
        f"ℹ️  Colonnes d'exposure validées pour underwriting department: {lob}"
    )

    results_df = df.apply(
        lambda row: pd.Series(apply_program(row.to_dict(), program, calculation_date)),
        axis=1
    )

    bordereau_with_net = df.copy()
    bordereau_with_net["cession_to_reinsurer"] = results_df["cession_to_reinsurer"]

    return bordereau_with_net, results_df
