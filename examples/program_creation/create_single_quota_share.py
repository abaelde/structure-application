"""
Création d'un programme simple avec quota share

Programme: Single Quota share
- Un seul quota share de 30% appliqué à toutes les polices
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import pandas as pd
import numpy as np

# =============================================================================
# PROGRAMME: SINGLE QUOTA SHARE
# =============================================================================

print("Création du programme Single Quota share...")

program_data = {
    "REPROG_ID_PRE": [1],  # Auto-increment key
    "REPROG_TITLE": ["SINGLE_QUOTA_SHARE_2024"],  # Former program_name
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

structures_data = {
    "INSPER_ID_PRE": [1],  # Auto-increment key
    "BUSINESS_ID_PRE": [None],  # Tnumber
    "TYPE_OF_PARTICIPATION_CD": ["quota_share"],  # Former type_of_participation
    "TYPE_OF_INSURED_PERIOD_CD": [None],  # TBD
    "ACTIVE_FLAG_CD": [True],  # Default active
    "INSPER_EFFECTIVE_DATE": [None],  # Former inception_date
    "INSPER_EXPIRY_DATE": [None],  # Former expiry_date
    "REPROG_ID_PRE": [1],  # Reference to program
    "BUSINESS_TITLE": ["QS_30"],  # Former structure_name
    "INSPER_LAYER_NO": [None],  # Layer number
    "INSPER_MAIN_CURRENCY_CD": [None],  # Main currency
    "INSPER_UW_YEAR": [None],  # UW Year
    "INSPER_CONTRACT_ORDER": [1],  # Former contract_order
    "INSPER_CONTRACT_FORM_CD_SLAV": [None],  # Contract form code
    "INSPER_CONTRACT_LODRA_CD_SLAV": [None],  # Contract LODRA code
    "INSPER_CONTRACT_COVERAGE_CD_SLAV": [None],  # Contract coverage code
    "INSPER_CLAIM_BASIS_CD": [None],  # Former claim_basis
    "INSPER_LODRA_CD_SLAV": [None],  # LODRA code
    "INSPER_LOD_TO_RA_DATE_SLAV": [None],  # LOD to RA date
    "INSPER_COMMENT": [None]  # Comments
}

sections_data = {
    "BUSINESS_TITLE": ["QS_30"],  # Former structure_name
    "cession_PCT": [0.30],  # 30% de cession
    "attachment_point_100": [np.nan],
    "limit_occurrence_100": [np.nan],
    "country": [np.nan],
    "region": [np.nan],
    "product_type_1": [np.nan],
    "product_type_2": [np.nan],
    "product_type_3": [np.nan],
    "currency": [np.nan],
    "line_of_business": [np.nan],
    "industry": [np.nan],
    "sic_code": [np.nan],
    "include": [np.nan]
}

program_df = pd.DataFrame(program_data)
structures_df = pd.DataFrame(structures_data)
sections_df = pd.DataFrame(sections_data)

# Créer le dossier programs s'il n'existe pas
output_dir = "../programs"
os.makedirs(output_dir, exist_ok=True)

with pd.ExcelWriter("../programs/single_quota_share.xlsx", engine="openpyxl") as writer:
    program_df.to_excel(writer, sheet_name="program", index=False)
    structures_df.to_excel(writer, sheet_name="structures", index=False)
    sections_df.to_excel(writer, sheet_name="sections", index=False)

print("✓ Programme Single Quota share créé: examples/programs/single_quota_share.xlsx")

# =============================================================================
# AFFICHAGE DES DÉTAILS
# =============================================================================

print("\n" + "=" * 80)
print("PROGRAMME SINGLE QUOTA SHARE")
print("=" * 80)

print("\nProgram:")
print(program_df)

print("\nStructures:")
print(structures_df)

print("\nSections:")
print(sections_df)

# =============================================================================
# EXPLICATION DU COMPORTEMENT
# =============================================================================

print("\n" + "=" * 80)
print("COMPORTEMENT DU PROGRAMME")
print("=" * 80)

print("""
Exemple avec une police de 1M d'exposition:

PROGRAMME SINGLE QUOTA SHARE:
1. QS_30% s'applique sur 1M → 0.3M cédé, 0.7M retenu
   Total cédé: 0.3M
   Total retenu: 0.7M

PRINCIPE:
- Un seul quota share de 30% appliqué à toutes les polices
- Pas de conditions géographiques ou autres
- Simple et efficace pour tester la logique de base
""")

print("\n✓ Le programme Single Quota share est prêt !")
