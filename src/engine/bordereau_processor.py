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
    
    program_lob = program.line_of_business if hasattr(program, 'line_of_business') else None
    
    if program_lob:
        try:
            found_column, target_column = find_exposure_column(
                bordereau_df.columns.tolist(), program_lob
            )
            
            if found_column and found_column != target_column:
                bordereau_df = bordereau_df.rename(columns={found_column: target_column})
                print(
                    f"ℹ️  Colonne d'exposure '{found_column}' mappée vers '{target_column}' "
                    f"(programme {program_lob})"
                )
        except ExposureMappingError as e:
            print(f"⚠️  {e}")
            print(f"   Le bordereau sera traité sans mapping de colonne d'exposition.")
    
    if "exposure" not in bordereau_df.columns:
        raise ValueError(
            f"Colonne 'exposure' manquante dans le bordereau après mapping. "
            f"Line of business du programme: {program_lob}. "
            f"Colonnes disponibles: {', '.join(bordereau_df.columns.tolist())}"
        )

    results_df = bordereau_df.apply(
        lambda row: pd.Series(apply_program(row.to_dict(), program, calculation_date)),
        axis=1
    )

    bordereau_with_net = bordereau_df.copy()
    bordereau_with_net["cession_to_reinsurer"] = results_df["cession_to_reinsurer"]

    return bordereau_with_net, results_df
