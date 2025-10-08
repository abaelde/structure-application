"""
Création du programme Casualty AIG 2024

Programme casualty avec 1 structure Quota Share avec 2 sections:
1. Section générale: Quota Share 100% avec limite de 25M
2. Section cyber: Quota Share 100% avec limite de 10M sur le risque cyber

Programme risk attaching avec réassureur share à 10% (à déterminer)
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pandas as pd
import numpy as np
from excel_utils import auto_adjust_column_widths

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from structures.constants import PRODUCT, SHEETS

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

# Limites pour chaque section (valeurs absolues)
LIMITS = {
    "general": 25_000_000,  # Limite section générale: 25M
    "cyber": 10_000_000,  # Limite section cyber: 10M
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
    "REPROG_MANAGEMENT_REPORTING_LOB_CD": [None],  # Management Reporting LOB Code
}

# =============================================================================
# DÉFINITION DES STRUCTURES (1 Quota Share)
# =============================================================================

structures_data = {
    "INSPER_ID_PRE": [1],  # Auto-increment key
    "BUSINESS_ID_PRE": [None],  # Tnumber
    "TYPE_OF_PARTICIPATION_CD": [PRODUCT.QUOTA_SHARE],  # Former type_of_participation
    "TYPE_OF_INSURED_PERIOD_CD": [None],  # TBD
    "ACTIVE_FLAG_CD": [True],  # Default active
    "INSPER_EFFECTIVE_DATE": [None],  # Former inception_date
    "INSPER_EXPIRY_DATE": [None],  # Former expiry_date
    "REPROG_ID_PRE": [1],  # Reference to program
    "BUSINESS_TITLE": ["QS_1"],  # Former structure_name
    "INSPER_LAYER_NO": [None],  # Layer number
    "INSPER_MAIN_CURRENCY_CD": [None],  # Main currency
    "INSPER_UW_YEAR": [None],  # UW Year
    "INSPER_CONTRACT_ORDER": [0],  # Former contract_order
    "INSPER_CONTRACT_FORM_CD_SLAV": [None],  # Contract form code
    "INSPER_CONTRACT_LODRA_CD_SLAV": [None],  # Contract LODRA code
    "INSPER_CONTRACT_COVERAGE_CD_SLAV": [None],  # Contract coverage code
    "INSPER_CLAIM_BASIS_CD": ["risk_attaching"],  # Former claim_basis
    "INSPER_LODRA_CD_SLAV": [None],  # LODRA code
    "INSPER_LOD_TO_RA_DATE_SLAV": [None],  # LOD to RA date
    "INSPER_COMMENT": [None],  # Comments
}

# =============================================================================
# DÉFINITION DES SECTIONS
# =============================================================================

sections_data = {
    # Keys and References
    "BUSCL_ID_PRE": [1, 2],  # Auto-increment key
    "REPROG_ID_PRE": [1, 1],  # Reference to program
    "CED_ID_PRE": [None, None],  # Reference to cedant
    "BUSINESS_ID_PRE": [None, None],  # Reference to business
    "INSPER_ID_PRE": [1, 1],  # Reference to structure (QS_1)
    # Exclusions and Names
    "BUSCL_EXCLUDE_CD": [None, "INCLUDE"],  # Section cyber uses INCLUDE for cyber
    "BUSCL_ENTITY_NAME_CED": [None, None],  # Cedant entity name
    "POL_RISK_NAME_CED": [None, "cyber"],  # Policy risk name - identifies cyber section
    # Geographic and Product Dimensions
    "BUSCL_COUNTRY_CD": [None, None],  # Former country
    "BUSCL_COUNTRY": [None, None],  # Country name
    "BUSCL_REGION": [None, None],  # Former region
    "BUSCL_CLASS_OF_BUSINESS_1": [None, None],  # Former product_type_1
    "BUSCL_CLASS_OF_BUSINESS_2": [None, None],  # Former product_type_2
    "BUSCL_CLASS_OF_BUSINESS_3": [None, None],  # Former product_type_3
    # Currency and Limits
    "BUSCL_LIMIT_CURRENCY_CD": [None, None],  # Former currency
    "AAD_100": [None, None],  # Annual Aggregate Deductible
    "LIMIT_100": [LIMITS["general"], LIMITS["cyber"]],  # Limits in millions
    "LIMIT_FLOATER_100": [None, None],  # Floater limit
    "ATTACHMENT_POINT_100": [
        np.nan,
        np.nan,
    ],  # Quota Share n'utilise pas attachment_point_100
    "OLW_100": [None, None],  # Original Line Written
    "LIMIT_OCCURRENCE_100": [None, None],  # Deprecated - use LIMIT_100 instead
    "LIMIT_AGG_100": [None, None],  # Aggregate limit
    # Cession and Retention
    "CESSION_PCT": [
        CESSION_RATE_VALUES["QS_1"],
        CESSION_RATE_VALUES["QS_1"],
    ],  # 100% cédé
    "RETENTION_PCT": [None, None],  # Retention percentage
    "SUPI_100": [None, None],  # SUPI
    # Premiums
    "BUSCL_PREMIUM_CURRENCY_CD": [None, None],  # Premium currency
    "BUSCL_PREMIUM_GROSS_NET_CD": [None, None],  # Gross/Net premium
    "PREMIUM_RATE_PCT": [None, None],  # Premium rate percentage
    "PREMIUM_DEPOSIT_100": [None, None],  # Premium deposit
    "PREMIUM_MIN_100": [None, None],  # Minimum premium
    # Coverage and Participations
    "BUSCL_LIABILITY_1_LINE_100": [None, None],  # Liability line 1
    "MAX_COVER_PCT": [None, None],  # Maximum coverage percentage
    "MIN_EXCESS_PCT": [None, None],  # Minimum excess percentage
    "SIGNED_SHARE_PCT": [
        REINSURER_SHARE_VALUES["QS_1"],
        REINSURER_SHARE_VALUES["QS_1"],
    ],  # Former reinsurer_share
    "AVERAGE_LINE_SLAV_CED": [None, None],  # Average line
    "PML_DEFAULT_PCT": [None, None],  # PML default percentage
    "LIMIT_EVENT": [None, None],  # Limit per event
    "NO_OF_REINSTATEMENTS": [None, None],  # Number of reinstatements
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
    program_df.to_excel(writer, sheet_name=SHEETS.PROGRAM, index=False)
    structures_df.to_excel(writer, sheet_name=SHEETS.STRUCTURES, index=False)
    sections_df.to_excel(writer, sheet_name=SHEETS.SECTIONS, index=False)

# Auto-adjust column widths for better readability
auto_adjust_column_widths(output_file)

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

print(
    """
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

"""
)

print("✓ Le programme Casualty AIG 2024 est prêt !")
print("\nNotes importantes:")
print("- Les montants sont exprimés en valeurs absolues")
print("- Le reinsurer share de 10% reste à déterminer selon les négociations")
print(
    "- La fonction quota_share a été modifiée pour supporter les limites optionnelles"
)
