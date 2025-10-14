import pandas as pd
from typing import Dict, Any, Optional
from .calculation_engine import apply_program
from src.loaders.exposure_mapping import validate_exposure_columns, ExposureMappingError


def apply_program_to_bordereau(
    bordereau_df: pd.DataFrame,
    program: Dict[str, Any],
    calculation_date: Optional[str] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    
    bordereau_df = bordereau_df.copy()
    
    validate_exposure_columns(
        bordereau_df.columns.tolist(), program.underwriting_department
    )
    
    print(
        f"ℹ️  Colonnes d'exposure validées pour underwriting department: {program.underwriting_department}"
    )

    results_df = bordereau_df.apply(
        lambda row: pd.Series(apply_program(row.to_dict(), program, calculation_date)),
        axis=1
    )

    bordereau_with_net = bordereau_df.copy()
    bordereau_with_net["cession_to_reinsurer"] = results_df["cession_to_reinsurer"]

    return bordereau_with_net, results_df
