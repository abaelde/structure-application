import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from products import quota_share, excess_of_loss
from .treaty_manager import TreatyManager


def match_section(policy_data: Dict[str, Any], sections: list, dimension_columns: list) -> Optional[Dict[str, Any]]:
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


def apply_section(exposure: float, section: Dict[str, Any], type_of_participation: str) -> Dict[str, float]:
    if type_of_participation == "quota_share":
        cession_PCT = section["cession_PCT"]
        if pd.isna(cession_PCT):
            raise ValueError("cession_PCT is required for quota_share")
        gross_ceded = quota_share(exposure, cession_PCT)
    
    elif type_of_participation == "excess_of_loss":
        attachment_point_100 = section["attachment_point_100"]
        limit_occurrence_100 = section["limit_occurrence_100"]
        if pd.isna(attachment_point_100) or pd.isna(limit_occurrence_100):
            raise ValueError("attachment_point_100 and limit_occurrence_100 are required for excess_of_loss")
        gross_ceded = excess_of_loss(exposure, attachment_point_100, limit_occurrence_100)
    
    else:
        raise ValueError(f"Unknown product type: {type_of_participation}")
    
    # Appliquer le reinsurer_share pour obtenir la net exposure
    reinsurer_share = section.get("reinsurer_share", 1.0)
    if pd.isna(reinsurer_share):
        reinsurer_share = 1.0
    
    net_ceded = gross_ceded * reinsurer_share
    
    return {
        "gross_ceded": gross_ceded,
        "net_ceded": net_ceded,
        "reinsurer_share": reinsurer_share
    }


def apply_program(policy_data: Dict[str, Any], program: Dict[str, Any]) -> Dict[str, Any]:
    exposure = policy_data.get("exposition")
    structures = program["structures"]
    dimension_columns = program["dimension_columns"]
    
    # Trier les structures par ordre
    sorted_structures = sorted(structures, key=lambda x: x["contract_order"])
    
    total_gross_ceded = 0.0
    total_net_ceded = 0.0
    structures_detail = []
    remaining_exposure = exposure
    
    for structure in sorted_structures:
        matched_section = match_section(policy_data, structure["sections"], dimension_columns)
        
        if matched_section is None:
            structures_detail.append({
                "structure_name": structure["structure_name"],
                "type_of_participation": structure["type_of_participation"],
                "claim_basis": structure.get("claim_basis"),
                "inception_date": structure.get("inception_date"),
                "expiry_date": structure.get("expiry_date"),
                "input_exposure": remaining_exposure,
                "gross_ceded": 0.0,
                "net_ceded": 0.0,
                "reinsurer_share": 0.0,
                "applied": False,
                "section": None
            })
            continue
        
        # Déterminer l'exposition d'entrée selon le type de produit
        if structure["type_of_participation"] == "quota_share":
            # Quota Share s'applique sur l'exposition restante
            input_exposure = remaining_exposure
        elif structure["type_of_participation"] == "excess_of_loss":
            # Excess of Loss s'applique sur l'exposition restante (après les Quota Share)
            # Si pas de Quota Share appliqué, utiliser l'exposition originale
            input_exposure = remaining_exposure
        else:
            raise ValueError(f"Unknown product type: {structure['type_of_participation']}")
        
        ceded_result = apply_section(input_exposure, matched_section, structure["type_of_participation"])
        
        structures_detail.append({
            "structure_name": structure["structure_name"],
            "type_of_participation": structure["type_of_participation"],
            "claim_basis": structure.get("claim_basis"),
            "inception_date": structure.get("inception_date"),
            "expiry_date": structure.get("expiry_date"),
            "input_exposure": input_exposure,
            "gross_ceded": ceded_result["gross_ceded"],
            "net_ceded": ceded_result["net_ceded"],
            "reinsurer_share": ceded_result["reinsurer_share"],
            "applied": True,
            "section": matched_section
        })
        
        total_gross_ceded += ceded_result["gross_ceded"]
        total_net_ceded += ceded_result["net_ceded"]
        
        # Mettre à jour l'exposition restante
        if structure["type_of_participation"] == "quota_share":
            # Quota Share réduit l'exposition restante
            remaining_exposure -= ceded_result["gross_ceded"]
        # Pour les Excess of Loss, on ne réduit pas l'exposition restante
        # car ils sont empilés et calculent sur la même base
    
    return {
        "policy_number": policy_data.get("numero_police"),
        "exposure": exposure,
        "gross_ceded": total_gross_ceded,
        "net_ceded": total_net_ceded,
        "retained": exposure - total_gross_ceded,
        "policy_inception_date": policy_data.get("inception_date"),
        "policy_expiry_date": policy_data.get("expiry_date"),
        "structures_detail": structures_detail
    }


def apply_program_to_bordereau(bordereau_df: pd.DataFrame, program: Dict[str, Any]) -> pd.DataFrame:
    results = []
    
    for _, row in bordereau_df.iterrows():
        policy_data = row.to_dict()
        result = apply_program(policy_data, program)
        results.append(result)
    
    # Créer un DataFrame avec les résultats détaillés
    results_df = pd.DataFrame(results)
    
    # Ajouter la colonne "Net Exposure" au bordereau original
    bordereau_with_net = bordereau_df.copy()
    bordereau_with_net["Net_Exposure"] = results_df["net_ceded"]
    
    return bordereau_with_net, results_df


def generate_detailed_report(results_df: pd.DataFrame, output_file: str = "detailed_report.txt"):
    """
    Génère un rapport détaillé de l'application des structures
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("RAPPORT DÉTAILLÉ D'APPLICATION DES STRUCTURES\n")
        f.write("=" * 80 + "\n\n")
        
        for _, policy_result in results_df.iterrows():
            f.write(f"POLICE: {policy_result['policy_number']}\n")
            f.write(f"Exposition initiale: {policy_result['exposure']:,.2f}\n")
            f.write(f"Total cédé (gross): {policy_result['gross_ceded']:,.2f}\n")
            f.write(f"Total cédé (net): {policy_result['net_ceded']:,.2f}\n")
            f.write(f"Rétention: {policy_result['retained']:,.2f}\n")
            f.write("-" * 60 + "\n")
            
            for i, struct in enumerate(policy_result["structures_detail"], 1):
                status = "✓ APPLIQUÉE" if struct.get('applied', False) else "✗ NON APPLIQUÉE"
                f.write(f"\n{i}. {struct['structure_name']} ({struct['type_of_participation']}) - {status}\n")
                f.write(f"   Exposition d'entrée: {struct['input_exposure']:,.2f}\n")
                
                if struct.get('applied', False):
                    f.write(f"   Cédé (gross): {struct['gross_ceded']:,.2f}\n")
                    f.write(f"   Cédé (net): {struct['net_ceded']:,.2f}\n")
                    f.write(f"   Reinsurer Share: {struct['reinsurer_share']:.4f} ({struct['reinsurer_share']*100:.2f}%)\n")
                    
                    if struct.get('section'):
                        section = struct['section']
                        f.write(f"   Section appliquée:\n")
                        for key, value in section.items():
                            if pd.notna(value) and key not in ['structure_name']:
                                f.write(f"     {key}: {value}\n")
                else:
                    f.write(f"   Raison: Aucune section correspondante trouvée\n")
            
            f.write("\n" + "=" * 80 + "\n\n")
    
    print(f"✓ Rapport détaillé généré: {output_file}")


def apply_treaty_with_claim_basis(policy_data: Dict[str, Any], treaty_manager: TreatyManager, 
                                 calculation_date: str = None) -> Dict[str, Any]:
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
    policy_inception_date = policy_data.get("inception_date")
    policy_expiry_date = policy_data.get("expiry_date")
    
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
        calculation_date=calculation_date
    )
    
    if selected_treaty is None:
        # Aucun traité trouvé - pas de couverture
        return {
            "policy_number": policy_data.get("numero_police"),
            "exposure": policy_data.get("exposition", 0),
            "ceded": 0.0,
            "retained": policy_data.get("exposition", 0),
            "policy_inception_date": policy_inception_date,
            "policy_expiry_date": policy_expiry_date,
            "selected_treaty_year": None,
            "claim_basis": claim_basis,
            "structures_detail": [],
            "coverage_status": "no_treaty_found"
        }
    
    # Appliquer le traité sélectionné
    result = apply_program(policy_data, selected_treaty)
    
    # Ajouter des informations sur la sélection du traité
    selected_year = None
    for year, treaty in treaty_manager.treaties.items():
        if treaty == selected_treaty:
            selected_year = year
            break
    
    result.update({
        "selected_treaty_year": selected_year,
        "claim_basis": claim_basis,
        "coverage_status": "covered"
    })
    
    return result


def apply_treaty_manager_to_bordereau(bordereau_df: pd.DataFrame, treaty_manager: TreatyManager,
                                    calculation_date: str = None) -> pd.DataFrame:
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
        result = apply_treaty_with_claim_basis(policy_data, treaty_manager, calculation_date)
        results.append(result)
    
    return pd.DataFrame(results)

