import pandas as pd
from typing import Dict, Any, Optional
from .calculation_engine import apply_program
from src.loaders.exposure_mapping import find_exposure_column, ExposureMappingError


def apply_program_to_bordereau(
    bordereau_df: pd.DataFrame,
    program: Dict[str, Any],
    calculation_date: Optional[str] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    
    bordereau_df = bordereau_df.copy()
    
    # Map exposure column based on program's underwriting department
    found_column, target_column = find_exposure_column(
        bordereau_df.columns.tolist(), program.underwriting_department
    )
    
    if found_column and found_column != target_column:
        bordereau_df = bordereau_df.rename(columns={found_column: target_column})
        print(
            f"ℹ️  Colonne d'exposure '{found_column}' mappée vers '{target_column}' "
            f"(underwriting department: {program.underwriting_department})"
        )

    results_df = bordereau_df.apply(
        lambda row: pd.Series(apply_program(row.to_dict(), program, calculation_date)),
        axis=1
    )

    bordereau_with_net = bordereau_df.copy()
    bordereau_with_net["cession_to_reinsurer"] = results_df["cession_to_reinsurer"]

    return bordereau_with_net, results_df
