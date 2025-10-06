"""
Création du programme Aviation Old Republic 2024

Programme risk attaching avec 3 structures excess of loss pour United States et Canada:
1. XOL_1: Priorité 3M, Limite 8.75M
2. XOL_2: Priorité 11.75M, Limite 10M  
3. XOL_3: Priorité 21.75M, Limite 23.25M
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import pandas as pd
import numpy as np

print("Création du programme Aviation Old Republic 2024...")

# =============================================================================
# DÉFINITION DU PROGRAMME
# =============================================================================

program_data = {
    "REPROG_ID_PRE": [1],  # Auto-increment key
    "REPROG_TITLE": ["AVIATION_OLD_REPUBLIC_2024"],  # Former program_name
    "CED_ID_PRE": [None],  # TBD
    "CED_NAME_PRE": [None],  # TBD
    "REPROG_ACTIVE_IND": [True],  # Default active
    "REPROG_COMMENT": [None],  # Optional comments
    "REPROG_UW_DEPARTMENT_CD": [None],  # UW Department Code
    "REPROG_UW_DEPARTMENT_NAME": [None],  # UW Department Name
    "REPROG_UW_DEPARTMENT_LOB_CD": [None],  # UW Department LOB Code
    "REPROG_UW_DEPARTMENT_LOB_NAME": [None],  # UW Department LOB Name
    "BUSPAR_CED_REG_CLASS_CD": [None],  # Regulatory Class Code
    "BUSPAR_CED_REG_CLASS_NAME": [None],  # Regulatory Class Name
    "REPROG_MAIN_CURRENCY_CD": [None],  # Main Currency Code
    "REPROG_MANAGEMENT_REPORTING_LOB_CD": [None]  # Management Reporting LOB Code
}

# =============================================================================
# DÉFINITION DES STRUCTURES
# =============================================================================

structures_data = {
    "structure_name": ["XOL_1", "XOL_2", "XOL_3"],
    "contract_order": [1, 2, 3],
    "type_of_participation": ["excess_of_loss", "excess_of_loss", "excess_of_loss"],
    "claim_basis": ["risk_attaching", "risk_attaching", "risk_attaching"]
}

# Reinsurer Share Values
# Définir le pourcentage de réassurance pour chaque structure
REINSURER_SHARE_VALUES = {
    "XOL_1": 0.1,   # 100% réassuré
    "XOL_2": 0.1,   # 100% réassuré
    "XOL_3": 0.0979,   # 100% réassuré
}

# =============================================================================
# DÉFINITION DES SECTIONS
# =============================================================================

sections_data = {
    "structure_name": ["XOL_1", "XOL_2", "XOL_3"],
    "cession_PCT": [np.nan, np.nan, np.nan],  # XOL n'utilise pas cession_PCT
    "attachment_point_100": [3.0, 11.75, 21.75],           # Priorités en millions
    "limit_occurrence_100": [8.75, 10.0, 23.25],              # Limites en millions
    "reinsurer_share": [REINSURER_SHARE_VALUES["XOL_1"], REINSURER_SHARE_VALUES["XOL_2"], REINSURER_SHARE_VALUES["XOL_3"]],
    # Conditions géographiques
    "country": ["United States", "United States", "United States"],
    "region": [np.nan, np.nan, np.nan],
    "product_type_1": [np.nan, np.nan, np.nan],
    "product_type_2": [np.nan, np.nan, np.nan],
    "product_type_3": [np.nan, np.nan, np.nan],
    "currency": [np.nan, np.nan, np.nan],
    "line_of_business": [np.nan, np.nan, np.nan],
    "industry": [np.nan, np.nan, np.nan],
    "sic_code": [np.nan, np.nan, np.nan],
    "include": [np.nan, np.nan, np.nan]
}

# Ajouter les sections pour le Canada
sections_canada_data = {
    "structure_name": ["XOL_1", "XOL_2", "XOL_3"],
    "cession_PCT": [np.nan, np.nan, np.nan],
    "attachment_point_100": [3.0, 11.75, 21.75],           # Priorités en millions
    "limit_occurrence_100": [8.75, 10.0, 23.25],              # Limites en millions
    "reinsurer_share": [REINSURER_SHARE_VALUES["XOL_1"], REINSURER_SHARE_VALUES["XOL_2"], REINSURER_SHARE_VALUES["XOL_3"]],
    "country": ["Canada", "Canada", "Canada"],
    "region": [np.nan, np.nan, np.nan],
    "product_type_1": [np.nan, np.nan, np.nan],
    "product_type_2": [np.nan, np.nan, np.nan],
    "product_type_3": [np.nan, np.nan, np.nan],
    "currency": [np.nan, np.nan, np.nan],
    "line_of_business": [np.nan, np.nan, np.nan],
    "industry": [np.nan, np.nan, np.nan],
    "sic_code": [np.nan, np.nan, np.nan],
    "include": [np.nan, np.nan, np.nan]
}

# Combiner les sections US et Canada
sections_combined_data = {
    "structure_name": sections_data["structure_name"] + sections_canada_data["structure_name"],
    "cession_PCT": sections_data["cession_PCT"] + sections_canada_data["cession_PCT"],
    "attachment_point_100": sections_data["attachment_point_100"] + sections_canada_data["attachment_point_100"],
    "limit_occurrence_100": sections_data["limit_occurrence_100"] + sections_canada_data["limit_occurrence_100"],
    "reinsurer_share": sections_data["reinsurer_share"] + sections_canada_data["reinsurer_share"],
    "country": sections_data["country"] + sections_canada_data["country"],
    "region": sections_data["region"] + sections_canada_data["region"],
    "product_type_1": sections_data["product_type_1"] + sections_canada_data["product_type_1"],
    "product_type_2": sections_data["product_type_2"] + sections_canada_data["product_type_2"],
    "product_type_3": sections_data["product_type_3"] + sections_canada_data["product_type_3"],
    "currency": sections_data["currency"] + sections_canada_data["currency"],
    "line_of_business": sections_data["line_of_business"] + sections_canada_data["line_of_business"],
    "industry": sections_data["industry"] + sections_canada_data["industry"],
    "sic_code": sections_data["sic_code"] + sections_canada_data["sic_code"],
    "include": sections_data["include"] + sections_canada_data["include"]
}

# =============================================================================
# CRÉATION DES DATAFRAMES
# =============================================================================

program_df = pd.DataFrame(program_data)
structures_df = pd.DataFrame(structures_data)
sections_df = pd.DataFrame(sections_combined_data)

# =============================================================================
# GÉNÉRATION DU FICHIER EXCEL
# =============================================================================

output_file = "../programs/aviation_old_republic_2024.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    program_df.to_excel(writer, sheet_name="program", index=False)
    structures_df.to_excel(writer, sheet_name="structures", index=False)
    sections_df.to_excel(writer, sheet_name="sections", index=False)

print(f"✓ Programme créé: {output_file}")

# =============================================================================
# AFFICHAGE DES DÉTAILS
# =============================================================================

print("\n" + "=" * 80)
print("PROGRAMME AVIATION OLD REPUBLIC 2024")
print("=" * 80)

print("\nProgram:")
print(program_df)

print("\nStructures:")
print(structures_df)

print("\nSections:")
print(sections_df)

# =============================================================================
# RÉSUMÉ DU PROGRAMME
# =============================================================================

print("\n" + "=" * 80)
print("RÉSUMÉ DU PROGRAMME")
print("=" * 80)

print("""
Programme: Aviation Old Republic 2024
Géographie: United States et Canada

Structures XOL (empilées selon l'ordre):
1. XOL_1 (contract_order=1): 8.75M xs 3M (pour US et Canada)
2. XOL_2 (contract_order=2): 10M xs 11.75M (pour US et Canada)  
3. XOL_3 (contract_order=3): 23.25M xs 21.75M (pour US et Canada)

""")

print("\n✓ Le programme Aviation Old Republic 2024 est prêt !")
