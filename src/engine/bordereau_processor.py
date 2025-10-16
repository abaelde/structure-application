import pandas as pd
from typing import Dict, Any, Optional, Union
from .calculation_engine import apply_program
from .exposure_validation import validate_exposure_columns, ExposureValidationError


def apply_program_to_bordereau(
    bordereau_df: Union[pd.DataFrame, Any],  # Any pour éviter l'import circulaire avec Bordereau
    program: Dict[str, Any],
    calculation_date: Optional[str] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    
    # Duck typing : détecte si c'est notre wrapper Bordereau
    if hasattr(bordereau_df, "to_dataframe"):
        # C'est un objet Bordereau
        df = bordereau_df.to_dataframe().copy()
        # Optionnel : on peut (ré)valider les colonnes d'expo avec la LOB la plus fiable disponible
        lob = getattr(bordereau_df, "line_of_business", None) or program.underwriting_department
    else:
        # C'est un DataFrame classique
        df = bordereau_df.copy()
        lob = program.underwriting_department
    
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
