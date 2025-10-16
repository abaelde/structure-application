import pandas as pd
from typing import Dict, Any
from .calculation_engine import apply_program
from ..domain.bordereau import Bordereau
from ..domain.policy import Policy
from ..domain.models import Program


def apply_program_to_row(
    row_data: Dict[str, Any],
    program: Program,
    calculation_date: str,
) -> Dict[str, Any]:
    """
    Applique un programme à une ligne de bordereau (dict).
    Compatible avec l'approche DataFrame.apply() pour Snowpark.
    """
    # Créer une Policy temporaire pour cette ligne
    # Utilise l'underwriting_department du programme (pas le line of business de la police)
    uw_dept = program.underwriting_department
    policy = Policy(raw=row_data, uw_dept=uw_dept)

    # Appliquer le programme
    return apply_program(policy, program, calculation_date)


def apply_program_to_bordereau(
    bordereau: Bordereau,
    program: Program,
    calculation_date: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:

    # Associe le programme au bordereau si pas déjà fait
    if not bordereau.program:
        bordereau.program = program

    # Validation avec l'underwriting_department du programme associé
    bordereau.validate_exposure_columns()

    df = bordereau.to_engine_dataframe().copy()

    # Calcul via apply pour compatibilité Snowpark
    results_df = df.apply(
        lambda row: pd.Series(
            apply_program_to_row(row.to_dict(), program, calculation_date)
        ),
        axis=1,
    )

    bordereau_with_net = df.copy()
    bordereau_with_net["cession_to_reinsurer"] = results_df["cession_to_reinsurer"]

    return bordereau_with_net, results_df
