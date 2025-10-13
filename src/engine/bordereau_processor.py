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


def apply_treaty_with_claim_basis(
    policy_data: Dict[str, Any],
    treaty_manager: TreatyManager,
    calculation_date: Optional[str] = None,
) -> Dict[str, Any]:
    from .calculation_engine import apply_program
    
    policy_inception_date = policy_data.get(FIELDS["INCEPTION_DATE"])
    policy_expiry_date = policy_data.get(FIELDS["EXPIRY_DATE"])

    if not policy_inception_date:
        raise ValueError("inception_date est requis pour la police")

    available_years = treaty_manager.get_available_years()
    if not available_years:
        raise ValueError("Aucun traité disponible")

    first_treaty = treaty_manager.get_treaty_for_year(available_years[0])
    if not first_treaty or not first_treaty["structures"]:
        raise ValueError("Aucune structure trouvée dans les traités")

    claim_basis = first_treaty["structures"][0].get("claim_basis", "risk_attaching")

    selected_treaty = treaty_manager.select_treaty(
        claim_basis=claim_basis,
        policy_inception_date=policy_inception_date,
        calculation_date=calculation_date,
    )

    if selected_treaty is None:
        return {
            FIELDS["INSURED_NAME"]: policy_data.get(FIELDS["INSURED_NAME"]),
            "exposure": policy_data.get(FIELDS["EXPOSURE"], 0),
            "effective_exposure": policy_data.get(FIELDS["EXPOSURE"], 0),
            "cession_to_reinsurer": 0.0,
            "retained_by_cedant": policy_data.get(FIELDS["EXPOSURE"], 0),
            "policy_inception_date": policy_inception_date,
            "policy_expiry_date": policy_expiry_date,
            "selected_treaty_year": None,
            "claim_basis": claim_basis,
            "structures_detail": [],
            "coverage_status": "no_treaty_found",
            "exclusion_status": "included",
        }

    result = apply_program(policy_data, selected_treaty, calculation_date)

    selected_year = None
    for year, treaty in treaty_manager.treaties.items():
        if treaty == selected_treaty:
            selected_year = year
            break

    result.update(
        {
            "selected_treaty_year": selected_year,
            "claim_basis": claim_basis,
            "coverage_status": "covered",
        }
    )

    return result


def apply_treaty_manager_to_bordereau(
    bordereau_df: pd.DataFrame,
    treaty_manager: TreatyManager,
    calculation_date: Optional[str] = None,
) -> pd.DataFrame:
    results = []

    for _, row in bordereau_df.iterrows():
        policy_data = row.to_dict()
        result = apply_treaty_with_claim_basis(
            policy_data, treaty_manager, calculation_date
        )
        results.append(result)

    return pd.DataFrame(results)

