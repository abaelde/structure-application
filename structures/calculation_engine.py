import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from products import quota_share, excess_of_loss
from .treaty_manager import TreatyManager
from .constants import FIELDS, PRODUCT, SECTION_COLS as SC


def match_section(
    policy_data: Dict[str, Any], sections: list, dimension_columns: list
) -> Optional[Dict[str, Any]]:
    matched_sections = []

    for section in sections:
        matches = True
        specificity = 0

        for dimension in dimension_columns:
            section_value = section.get(dimension)

            if pd.notna(section_value):
                policy_value = policy_data.get(dimension)
                if policy_value != section_value:
                    matches = False
                    break
                specificity += 1

        if matches:
            matched_sections.append((section, specificity))

    if not matched_sections:
        return None

    matched_sections.sort(key=lambda x: x[1], reverse=True)
    return matched_sections[0][0]


def apply_section(
    exposure: float, section: Dict[str, Any], type_of_participation: str
) -> Dict[str, float]:
    if type_of_participation == PRODUCT.QUOTA_SHARE:
        cession_PCT = section[SC.CESSION_PCT]
        if pd.isna(cession_PCT):
            raise ValueError("CESSION_PCT is required for quota_share")
        limit = section.get(SC.LIMIT)
        if pd.notna(limit):
            cession_to_layer_100pct = quota_share(exposure, cession_PCT, limit)
        else:
            cession_to_layer_100pct = quota_share(exposure, cession_PCT)

    elif type_of_participation == PRODUCT.EXCESS_OF_LOSS:
        attachment_point_100 = section[SC.ATTACHMENT]
        limit_100 = section[SC.LIMIT]
        if pd.isna(attachment_point_100) or pd.isna(limit_100):
            raise ValueError(
                "ATTACHMENT_POINT_100 and LIMIT_100 are required for excess_of_loss"
            )
        cession_to_layer_100pct = excess_of_loss(
            exposure, attachment_point_100, limit_100
        )

    else:
        raise ValueError(f"Unknown product type: {type_of_participation}")

    reinsurer_share = section.get(SC.SIGNED_SHARE, 1.0)
    if pd.isna(reinsurer_share):
        reinsurer_share = 1.0

    cession_to_reinsurer = cession_to_layer_100pct * reinsurer_share

    return {
        "cession_to_layer_100pct": cession_to_layer_100pct,
        "cession_to_reinsurer": cession_to_reinsurer,
        "reinsurer_share": reinsurer_share,
    }


def apply_program(
    policy_data: Dict[str, Any], program: Dict[str, Any]
) -> Dict[str, Any]:
    exposure = policy_data.get(FIELDS["EXPOSURE"])
    structures = program["structures"]
    dimension_columns = program["dimension_columns"]

    sorted_structures = sorted(structures, key=lambda x: x["contract_order"])

    total_cession_to_layer_100pct = 0.0
    total_cession_to_reinsurer = 0.0
    structures_detail = []
    remaining_exposure = exposure

    for structure in sorted_structures:
        matched_section = match_section(
            policy_data, structure["sections"], dimension_columns
        )

        if matched_section is None:
            structures_detail.append(
                {
                    "structure_name": structure["structure_name"],
                    "type_of_participation": structure["type_of_participation"],
                    "claim_basis": structure.get("claim_basis"),
                    "inception_date": structure.get("inception_date"),
                    "expiry_date": structure.get("expiry_date"),
                    "input_exposure": remaining_exposure,
                    "cession_to_layer_100pct": 0.0,
                    "cession_to_reinsurer": 0.0,
                    "reinsurer_share": 0.0,
                    "applied": False,
                    "section": None,
                }
            )
            continue

        if structure["type_of_participation"] == PRODUCT.QUOTA_SHARE:
            input_exposure = remaining_exposure
        elif structure["type_of_participation"] == PRODUCT.EXCESS_OF_LOSS:
            input_exposure = remaining_exposure
        else:
            raise ValueError(
                f"Unknown product type: {structure['type_of_participation']}"
            )

        ceded_result = apply_section(
            input_exposure, matched_section, structure["type_of_participation"]
        )

        structures_detail.append(
            {
                "structure_name": structure["structure_name"],
                "type_of_participation": structure["type_of_participation"],
                "claim_basis": structure.get("claim_basis"),
                "inception_date": structure.get("inception_date"),
                "expiry_date": structure.get("expiry_date"),
                "input_exposure": input_exposure,
                "cession_to_layer_100pct": ceded_result["cession_to_layer_100pct"],
                "cession_to_reinsurer": ceded_result["cession_to_reinsurer"],
                "reinsurer_share": ceded_result["reinsurer_share"],
                "applied": True,
                "section": matched_section,
            }
        )

        total_cession_to_layer_100pct += ceded_result["cession_to_layer_100pct"]
        total_cession_to_reinsurer += ceded_result["cession_to_reinsurer"]

        if structure["type_of_participation"] == PRODUCT.QUOTA_SHARE:
            remaining_exposure -= ceded_result["cession_to_layer_100pct"]

    return {
        "insured_name": policy_data.get(FIELDS["INSURED_NAME"]),
        "exposure": exposure,
        "cession_to_layer_100pct": total_cession_to_layer_100pct,
        "cession_to_reinsurer": total_cession_to_reinsurer,
        "retained_by_cedant": exposure - total_cession_to_layer_100pct,
        "policy_inception_date": policy_data.get(FIELDS["INCEPTION_DATE"]),
        "policy_expiry_date": policy_data.get(FIELDS["EXPIRY_DATE"]),
        "structures_detail": structures_detail,
    }


def apply_program_to_bordereau(
    bordereau_df: pd.DataFrame, program: Dict[str, Any]
) -> pd.DataFrame:
    results = []

    for _, row in bordereau_df.iterrows():
        policy_data = row.to_dict()
        result = apply_program(policy_data, program)
        results.append(result)

    results_df = pd.DataFrame(results)

    bordereau_with_net = bordereau_df.copy()
    bordereau_with_net["Cession_To_Reinsurer"] = results_df["cession_to_reinsurer"]

    return bordereau_with_net, results_df


def apply_treaty_with_claim_basis(
    policy_data: Dict[str, Any],
    treaty_manager: TreatyManager,
    calculation_date: str = None,
) -> Dict[str, Any]:
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
            "insured_name": policy_data.get(FIELDS["INSURED_NAME"]),
            "exposure": policy_data.get(FIELDS["EXPOSURE"], 0),
            "cession_to_reinsurer": 0.0,
            "retained_by_cedant": policy_data.get(FIELDS["EXPOSURE"], 0),
            "policy_inception_date": policy_inception_date,
            "policy_expiry_date": policy_expiry_date,
            "selected_treaty_year": None,
            "claim_basis": claim_basis,
            "structures_detail": [],
            "coverage_status": "no_treaty_found",
        }

    result = apply_program(policy_data, selected_treaty)

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
    calculation_date: str = None,
) -> pd.DataFrame:
    results = []

    for _, row in bordereau_df.iterrows():
        policy_data = row.to_dict()
        result = apply_treaty_with_claim_basis(
            policy_data, treaty_manager, calculation_date
        )
        results.append(result)

    return pd.DataFrame(results)

