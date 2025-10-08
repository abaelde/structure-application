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

    # Appliquer le SIGNED_SHARE_PCT pour obtenir la cession effective au réassureur
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

    # Trier les structures par ordre
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

        # Déterminer l'exposition d'entrée selon le type de produit
        if structure["type_of_participation"] == PRODUCT.QUOTA_SHARE:
            # Quota Share s'applique sur l'exposition restante
            input_exposure = remaining_exposure
        elif structure["type_of_participation"] == PRODUCT.EXCESS_OF_LOSS:
            # Excess of Loss s'applique sur l'exposition restante (après les Quota Share)
            # Si pas de Quota Share appliqué, utiliser l'exposition originale
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

        # Mettre à jour l'exposition restante
        if structure["type_of_participation"] == PRODUCT.QUOTA_SHARE:
            # Quota Share réduit l'exposition restante
            remaining_exposure -= ceded_result["cession_to_layer_100pct"]
        # Pour les Excess of Loss, on ne réduit pas l'exposition restante
        # car ils sont empilés et calculent sur la même base

    return {
        "policy_number": policy_data.get(FIELDS["POLICY_NUMBER"]),
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

    # Créer un DataFrame avec les résultats détaillés
    results_df = pd.DataFrame(results)

    # Ajouter la colonne "Cession to Reinsurer" au bordereau original
    bordereau_with_net = bordereau_df.copy()
    bordereau_with_net["Cession_To_Reinsurer"] = results_df["cession_to_reinsurer"]

    return bordereau_with_net, results_df


def write_detailed_results(
    results_df: pd.DataFrame, dimension_columns: list, file=None
):
    import sys

    if file is None:
        file = sys.stdout

    file.write("=" * 80 + "\n")
    file.write("DETAILED BREAKDOWN BY POLICY\n")
    file.write("=" * 80 + "\n")

    for _, policy_result in results_df.iterrows():
        file.write(f"\n{'─' * 80}\n")
        file.write(f"POLICY: {policy_result['policy_number']}\n")
        file.write(f"Cedant gross exposure: {policy_result['exposure']:,.2f}\n")
        file.write(f"Cession at layer (100%): {policy_result['cession_to_layer_100pct']:,.2f}\n")
        file.write(f"Reinsurer net exposure: {policy_result['cession_to_reinsurer']:,.2f}\n")
        file.write(f"Retained by cedant: {policy_result['retained_by_cedant']:,.2f}\n")
        file.write(f"\nStructures applied:\n")

        for i, struct in enumerate(policy_result["structures_detail"], 1):
            status = "✓ APPLIED" if struct.get("applied", False) else "✗ NOT APPLIED"
            file.write(
                f"\n{i}. {struct['structure_name']} ({struct['type_of_participation']}) - {status}\n"
            )
            file.write(f"   Input exposure: {struct['input_exposure']:,.2f}\n")

            if struct.get("applied", False):
                file.write(f"   Cession at layer (100%): {struct['cession_to_layer_100pct']:,.2f}\n")
                file.write(f"   Cession to reinsurer: {struct['cession_to_reinsurer']:,.2f}\n")
                file.write(
                    f"   Reinsurer Share: {struct['reinsurer_share']:.4f} ({struct['reinsurer_share']*100:.2f}%)\n"
                )

                if struct.get("section"):
                    section = struct["section"]
                    file.write(f"   Applied section parameters:\n")

                    if struct["type_of_participation"] == PRODUCT.QUOTA_SHARE:
                        if pd.notna(section.get(SC.CESSION_PCT)):
                            file.write(f"      CESSION_PCT: {section[SC.CESSION_PCT]}\n")
                        if pd.notna(section.get(SC.LIMIT)):
                            file.write(f"      LIMIT_100: {section[SC.LIMIT]}\n")
                    elif struct["type_of_participation"] == PRODUCT.EXCESS_OF_LOSS:
                        if pd.notna(section.get(SC.ATTACHMENT)):
                            file.write(
                                f"      ATTACHMENT_POINT_100: {section[SC.ATTACHMENT]}\n"
                            )
                        if pd.notna(section.get(SC.LIMIT)):
                            file.write(f"      LIMIT_100: {section[SC.LIMIT]}\n")

                    if pd.notna(section.get(SC.SIGNED_SHARE)):
                        file.write(
                            f"      SIGNED_SHARE_PCT: {section[SC.SIGNED_SHARE]}\n"
                        )

                    conditions = []
                    for dim in dimension_columns:
                        value = section.get(dim)
                        if pd.notna(value):
                            conditions.append(f"{dim}={value}")
                    conditions_str = (
                        ", ".join(conditions) if conditions else "All (no conditions)"
                    )
                    file.write(f"   Matching conditions: {conditions_str}\n")
            else:
                file.write(f"   Reason: No matching section found\n")


def generate_detailed_report(
    results_df: pd.DataFrame,
    program: Dict[str, Any],
    output_file: str = "detailed_report.txt",
):
    from .program_display import write_program_config

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("DETAILED STRUCTURES APPLICATION REPORT\n")
        f.write("=" * 80 + "\n\n")

        write_program_config(program, file=f)
        f.write("\n\n")

        write_detailed_results(results_df, program["dimension_columns"], file=f)

    print(f"✓ Detailed report generated: {output_file}")


def apply_treaty_with_claim_basis(
    policy_data: Dict[str, Any],
    treaty_manager: TreatyManager,
    calculation_date: str = None,
) -> Dict[str, Any]:
    """
    Applique le traité approprié selon la logique claim_basis

    Args:
        policy_data: Données de la police
        treaty_manager: Gestionnaire de traités
        calculation_date: Date de calcul "as of now" (YYYY-MM-DD)

    Returns:
        Résultat de l'application du traité
    """
    # Récupérer les informations de la police
    policy_inception_date = policy_data.get(FIELDS["INCEPTION_DATE"])
    policy_expiry_date = policy_data.get(FIELDS["EXPIRY_DATE"])

    if not policy_inception_date:
        raise ValueError("inception_date est requis pour la police")

    # Pour l'instant, on suppose que toutes les structures ont le même claim_basis
    # Dans un cas plus complexe, on pourrait avoir des structures avec des claim_basis différents
    # Ici, on prend le claim_basis de la première structure disponible

    # Chercher un traité disponible pour déterminer le claim_basis
    available_years = treaty_manager.get_available_years()
    if not available_years:
        raise ValueError("Aucun traité disponible")

    # Prendre le premier traité disponible pour récupérer le claim_basis
    first_treaty = treaty_manager.get_treaty_for_year(available_years[0])
    if not first_treaty or not first_treaty["structures"]:
        raise ValueError("Aucune structure trouvée dans les traités")

    # Supposer que toutes les structures ont le même claim_basis
    # (dans un cas plus complexe, on pourrait gérer des claim_basis différents par structure)
    claim_basis = first_treaty["structures"][0].get("claim_basis", "risk_attaching")

    # Sélectionner le traité approprié
    selected_treaty = treaty_manager.select_treaty(
        claim_basis=claim_basis,
        policy_inception_date=policy_inception_date,
        calculation_date=calculation_date,
    )

    if selected_treaty is None:
        # Aucun traité trouvé - pas de couverture
        return {
            "policy_number": policy_data.get(FIELDS["POLICY_NUMBER"]),
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

    # Appliquer le traité sélectionné
    result = apply_program(policy_data, selected_treaty)

    # Ajouter des informations sur la sélection du traité
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
    """
    Applique le gestionnaire de traités à un bordereau complet

    Args:
        bordereau_df: DataFrame du bordereau
        treaty_manager: Gestionnaire de traités
        calculation_date: Date de calcul "as of now" (YYYY-MM-DD)

    Returns:
        DataFrame avec les résultats
    """
    results = []

    for _, row in bordereau_df.iterrows():
        policy_data = row.to_dict()
        result = apply_treaty_with_claim_basis(
            policy_data, treaty_manager, calculation_date
        )
        results.append(result)

    return pd.DataFrame(results)
