"""
Création du programme Aviation Old Republic 2024

Programme risk attaching avec 3 structures excess of loss pour United States et Canada:
1. XOL_1: Priorité 3M, Limite 8.75M
2. XOL_2: Priorité 11.75M, Limite 10M
3. XOL_3: Priorité 21.75M, Limite 23.25M
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pandas as pd
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from structures.constants import PRODUCT, SHEETS

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
    "REPROG_MANAGEMENT_REPORTING_LOB_CD": [None],  # Management Reporting LOB Code
}

# =============================================================================
# DÉFINITION DES STRUCTURES
# =============================================================================

structures_data = {
    "INSPER_ID_PRE": [1, 2, 3],  # Auto-increment key
    "BUSINESS_ID_PRE": [None, None, None],  # Tnumber
    "TYPE_OF_PARTICIPATION_CD": [
        PRODUCT.EXCESS_OF_LOSS,
        PRODUCT.EXCESS_OF_LOSS,
        PRODUCT.EXCESS_OF_LOSS,
    ],  # Former type_of_participation
    "TYPE_OF_INSURED_PERIOD_CD": [None, None, None],  # TBD
    "ACTIVE_FLAG_CD": [True, True, True],  # Default active
    "INSPER_EFFECTIVE_DATE": [None, None, None],  # Former inception_date
    "INSPER_EXPIRY_DATE": [None, None, None],  # Former expiry_date
    "REPROG_ID_PRE": [1, 1, 1],  # Reference to program
    "BUSINESS_TITLE": ["XOL_1", "XOL_2", "XOL_3"],  # Former structure_name
    "INSPER_LAYER_NO": [None, None, None],  # Layer number
    "INSPER_MAIN_CURRENCY_CD": [None, None, None],  # Main currency
    "INSPER_UW_YEAR": [None, None, None],  # UW Year
    "INSPER_CONTRACT_ORDER": [1, 2, 3],  # Former contract_order
    "INSPER_PREDECESSOR_TITLE": [None, None, None],  # All are entry points (parallel XOLs)
    "INSPER_CONTRACT_FORM_CD_SLAV": [None, None, None],  # Contract form code
    "INSPER_CONTRACT_LODRA_CD_SLAV": [None, None, None],  # Contract LODRA code
    "INSPER_CONTRACT_COVERAGE_CD_SLAV": [None, None, None],  # Contract coverage code
    "INSPER_CLAIM_BASIS_CD": [
        "risk_attaching",
        "risk_attaching",
        "risk_attaching",
    ],  # Former claim_basis
    "INSPER_LODRA_CD_SLAV": [None, None, None],  # LODRA code
    "INSPER_LOD_TO_RA_DATE_SLAV": [None, None, None],  # LOD to RA date
    "INSPER_COMMENT": [None, None, None],  # Comments
}

# Reinsurer Share Values
# Définir le pourcentage de réassurance pour chaque structure
REINSURER_SHARE_VALUES = {
    "XOL_1": 0.1,  # 100% réassuré
    "XOL_2": 0.1,  # 100% réassuré
    "XOL_3": 0.0979,  # 100% réassuré
}

# =============================================================================
# DÉFINITION DES SECTIONS
# =============================================================================

sections_data = {
    # Keys and References
    "BUSCL_ID_PRE": [1, 2, 3],  # Auto-increment key
    "REPROG_ID_PRE": [1, 1, 1],  # Reference to program
    "CED_ID_PRE": [None, None, None],  # Reference to cedant
    "BUSINESS_ID_PRE": [None, None, None],  # Reference to business
    "INSPER_ID_PRE": [1, 2, 3],  # Reference to structures (XOL_1, XOL_2, XOL_3)
    # Exclusions and Names
    "BUSCL_EXCLUDE_CD": [None, None, None],  # ENUM: INCLUDE or EXCLUDE
    "BUSCL_ENTITY_NAME_CED": [None, None, None],  # Cedant entity name
    "POL_RISK_NAME_CED": [None, None, None],  # Policy risk name
    # Geographic and Product Dimensions
    "BUSCL_COUNTRY_CD": [
        "United States",
        "United States",
        "United States",
    ],  # Former country
    "BUSCL_COUNTRY": [None, None, None],  # Country name
    "BUSCL_REGION": [None, None, None],  # Former region
    "BUSCL_CLASS_OF_BUSINESS_1": [None, None, None],  # Former product_type_1
    "BUSCL_CLASS_OF_BUSINESS_2": [None, None, None],  # Former product_type_2
    "BUSCL_CLASS_OF_BUSINESS_3": [None, None, None],  # Former product_type_3
    # Currency and Limits
    "BUSCL_LIMIT_CURRENCY_CD": [None, None, None],  # Former currency
    "AAD_100": [None, None, None],  # Annual Aggregate Deductible
    "LIMIT_100": [8_750_000, 10_000_000, 23_250_000],  # Limits in absolute values
    "LIMIT_FLOATER_100": [None, None, None],  # Floater limit
    "ATTACHMENT_POINT_100": [3_000_000, 11_750_000, 21_750_000],  # Priorités en valeurs absolues
    "OLW_100": [None, None, None],  # Original Line Written
    "LIMIT_OCCURRENCE_100": [None, None, None],  # Deprecated - use LIMIT_100 instead
    "LIMIT_AGG_100": [None, None, None],  # Aggregate limit
    # Cession and Retention
    "CESSION_PCT": [np.nan, np.nan, np.nan],  # XOL n'utilise pas cession_PCT
    "RETENTION_PCT": [None, None, None],  # Retention percentage
    "SUPI_100": [None, None, None],  # SUPI
    # Premiums
    "BUSCL_PREMIUM_CURRENCY_CD": [None, None, None],  # Premium currency
    "BUSCL_PREMIUM_GROSS_NET_CD": [None, None, None],  # Gross/Net premium
    "PREMIUM_RATE_PCT": [None, None, None],  # Premium rate percentage
    "PREMIUM_DEPOSIT_100": [None, None, None],  # Premium deposit
    "PREMIUM_MIN_100": [None, None, None],  # Minimum premium
    # Coverage and Participations
    "BUSCL_LIABILITY_1_LINE_100": [None, None, None],  # Liability line 1
    "MAX_COVER_PCT": [None, None, None],  # Maximum coverage percentage
    "MIN_EXCESS_PCT": [None, None, None],  # Minimum excess percentage
    "SIGNED_SHARE_PCT": [
        REINSURER_SHARE_VALUES["XOL_1"],
        REINSURER_SHARE_VALUES["XOL_2"],
        REINSURER_SHARE_VALUES["XOL_3"],
    ],  # Former reinsurer_share
    "AVERAGE_LINE_SLAV_CED": [None, None, None],  # Average line
    "PML_DEFAULT_PCT": [None, None, None],  # PML default percentage
    "LIMIT_EVENT": [None, None, None],  # Limit per event
    "NO_OF_REINSTATEMENTS": [None, None, None],  # Number of reinstatements
}

# Ajouter les sections pour le Canada (ajout direct aux listes existantes)
for key in sections_data.keys():
    if key == "BUSCL_ID_PRE":
        sections_data[key].extend([4, 5, 6])  # IDs 4, 5, 6 pour Canada
    elif key == "INSPER_ID_PRE":
        sections_data[key].extend([1, 2, 3])  # Même structures XOL_1, XOL_2, XOL_3
    elif key == "BUSCL_COUNTRY_CD":
        sections_data[key].extend(["Canada", "Canada", "Canada"])
    elif key == "ATTACHMENT_POINT_100":
        sections_data[key].extend([3_000_000, 11_750_000, 21_750_000])
    elif key == "LIMIT_100":
        sections_data[key].extend([8_750_000, 10_000_000, 23_250_000])
    elif key == "LIMIT_OCCURRENCE_100":
        sections_data[key].extend([None, None, None])
    elif key == "CESSION_PCT":
        sections_data[key].extend([np.nan, np.nan, np.nan])
    elif key == "SIGNED_SHARE_PCT":
        sections_data[key].extend(
            [
                REINSURER_SHARE_VALUES["XOL_1"],
                REINSURER_SHARE_VALUES["XOL_2"],
                REINSURER_SHARE_VALUES["XOL_3"],
            ]
        )
    elif key == "REPROG_ID_PRE":
        sections_data[key].extend([1, 1, 1])
    else:
        sections_data[key].extend([None, None, None])

# Use the combined sections_data directly
sections_combined_data = sections_data

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
    program_df.to_excel(writer, sheet_name=SHEETS.PROGRAM, index=False)
    structures_df.to_excel(writer, sheet_name=SHEETS.STRUCTURES, index=False)
    sections_df.to_excel(writer, sheet_name=SHEETS.SECTIONS, index=False)

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

print(
    """
Programme: Aviation Old Republic 2024
Géographie: United States et Canada

Structures XOL (empilées selon l'ordre):
1. XOL_1 (contract_order=1): 8.75M xs 3M (pour US et Canada)
2. XOL_2 (contract_order=2): 10M xs 11.75M (pour US et Canada)  
3. XOL_3 (contract_order=3): 23.25M xs 21.75M (pour US et Canada)

"""
)

print("\n✓ Le programme Aviation Old Republic 2024 est prêt !")
