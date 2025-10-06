"""
Création du programme Casualty AIG 2024

Programme casualty avec 1 structure Quota Share avec 2 sections:
1. Section générale: Quota Share 100% avec limite de 25M
2. Section cyber: Quota Share 100% avec limite de 10M sur le risque cyber

Programme risk attaching avec réassureur share à 10% (à déterminer)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import pandas as pd
import numpy as np

print("Création du programme Casualty AIG 2024...")

# =============================================================================
# CONFIGURATION DES VALEURS
# =============================================================================

# Cession Rate Values (pourcentage cédé au réassureur)
CESSION_RATE_VALUES = {
    "QS_1": 1.0,  # 100% cédé (quota share complet)
}

# Reinsurer Share Values (part du réassureur dans la cession)
# TODO: À déterminer selon les négociations
REINSURER_SHARE_VALUES = {
    "QS_1": 0.10,  # 10% du réassureur (à déterminer)
}

# Limites pour chaque section (en millions)
LIMITS = {
    "general": 25.0,    # Limite section générale: 25M
    "cyber": 10.0,      # Limite section cyber: 10M
}

# =============================================================================
# DÉFINITION DU PROGRAMME
# =============================================================================

program_data = {
    "REPROG_ID_PRE": [1],  # Auto-increment key
    "REPROG_TITLE": ["CASUALTY_AIG_2024"],  # Former program_name
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
# DÉFINITION DES STRUCTURES (1 Quota Share)
# =============================================================================

structures_data = {
    "structure_name": ["QS_1"],
    "contract_order": [0],
    "type_of_participation": ["quota_share"],
    "claim_basis": ["risk_attaching"]
}

# =============================================================================
# DÉFINITION DES SECTIONS
# =============================================================================

sections_data = {
    "structure_name": ["QS_1", "QS_1"],
    "cession_PCT": [CESSION_RATE_VALUES["QS_1"], CESSION_RATE_VALUES["QS_1"]],
    "attachment_point_100": [np.nan, np.nan],  # Quota Share n'utilise pas attachment_point_100
    "limit_occurrence_100": [LIMITS["general"], LIMITS["cyber"]],  # Limites en millions
    "reinsurer_share": [REINSURER_SHARE_VALUES["QS_1"], REINSURER_SHARE_VALUES["QS_1"]],
    # Conditions géographiques - pas de restriction spécifique
    "country": [np.nan, np.nan],
    "region": [np.nan, np.nan],
    "product_type_1": [np.nan, np.nan],
    "product_type_2": [np.nan, np.nan],
    "product_type_3": [np.nan, np.nan],
    "currency": [np.nan, np.nan],
    "line_of_business": [np.nan, np.nan],
    "industry": [np.nan, np.nan],
    "sic_code": [np.nan, np.nan],
    "include": [np.nan, "cyber"]  # Section cyber identifiée par le champ include
}

# =============================================================================
# CRÉATION DES DATAFRAMES
# =============================================================================

program_df = pd.DataFrame(program_data)
structures_df = pd.DataFrame(structures_data)
sections_df = pd.DataFrame(sections_data)

# =============================================================================
# GÉNÉRATION DU FICHIER EXCEL
# =============================================================================

# Créer le dossier programs s'il n'existe pas
output_dir = "../programs"
os.makedirs(output_dir, exist_ok=True)

output_file = os.path.join(output_dir, "casualty_aig_2024.xlsx")

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    program_df.to_excel(writer, sheet_name="program", index=False)
    structures_df.to_excel(writer, sheet_name="structures", index=False)
    sections_df.to_excel(writer, sheet_name="sections", index=False)

print(f"✓ Programme créé: {output_file}")

# =============================================================================
# AFFICHAGE DES DÉTAILS
# =============================================================================

print("\n" + "=" * 80)
print("PROGRAMME CASUALTY AIG 2024")
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
Programme: Casualty AIG 2024
Claim basis: Risk attaching

Structure unique:
- QS_1 (contract_order=0): Quota Share 100% cédé

Sections:
1. Section générale: Quota Share 100% avec limite de 25M
   - Pas de restriction spécifique
   - Reinsurer share: 10% (à déterminer)

2. Section cyber: Quota Share 100% avec limite de 10M
   - Restriction sur le risque cyber (include="cyber")
   - Reinsurer share: 10% (à déterminer)

""")

print("✓ Le programme Casualty AIG 2024 est prêt !")
print("\nNotes importantes:")
print("- Les montants sont exprimés en millions")
print("- Le reinsurer share de 10% reste à déterminer selon les négociations")
print("- La fonction quota_share a été modifiée pour supporter les limites optionnelles")
