"""
Création d'un programme avec deux quota shares en parallèle

Programme: Double Quota Share
- Quota Share 1: 10%
- Quota Share 2: 15%
Les deux s'appliquent en parallèle sur toutes les polices
"""

import sys
import os
from pathlib import Path

# Navigate to project root (same logic as conftest.py but 2 levels deeper)
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np

# Import utilities
from examples.program_creation.excel_utils import auto_adjust_column_widths
from src.domain import PRODUCT, SHEETS

# =============================================================================
# PROGRAMME: DOUBLE QUOTA SHARE
# =============================================================================

print("Création du programme Double Quota Share...")

program_data = {
    "REPROG_ID_PRE": [1],
    "REPROG_TITLE": ["DOUBLE_QUOTA_SHARE_2024"],
    "CED_ID_PRE": [None],
    "CED_NAME_PRE": [None],
    "REPROG_ACTIVE_IND": [True],
    "REPROG_COMMENT": [None],
    "REPROG_UW_DEPARTMENT_CD": [None],
    "REPROG_UW_DEPARTMENT_NAME": [None],
    "REPROG_UW_DEPARTMENT_LOB_CD": [None],
    "REPROG_UW_DEPARTMENT_LOB_NAME": [None],
    "BUSPAR_CED_REG_CLASS_CD": [None],
    "BUSPAR_CED_REG_CLASS_NAME": [None],
    "REPROG_MAIN_CURRENCY_CD": [None],
    "REPROG_MANAGEMENT_REPORTING_LOB_CD": [None],
}

structures_data = {
    "INSPER_ID_PRE": [1, 2],
    "BUSINESS_ID_PRE": [None, None],
    "TYPE_OF_PARTICIPATION_CD": [PRODUCT.QUOTA_SHARE, PRODUCT.QUOTA_SHARE],
    "TYPE_OF_INSURED_PERIOD_CD": [None, None],
    "ACTIVE_FLAG_CD": [True, True],
    "INSPER_EFFECTIVE_DATE": [None, None],
    "INSPER_EXPIRY_DATE": [None, None],
    "REPROG_ID_PRE": [1, 1],
    "BUSINESS_TITLE": ["QS_10", "QS_15"],
    "INSPER_LAYER_NO": [None, None],
    "INSPER_MAIN_CURRENCY_CD": [None, None],
    "INSPER_UW_YEAR": [None, None],
    "INSPER_CONTRACT_ORDER": [None, None],
    "INSPER_PREDECESSOR_TITLE": [None, None],
    "INSPER_CONTRACT_FORM_CD_SLAV": [None, None],
    "INSPER_CONTRACT_LODRA_CD_SLAV": [None, None],
    "INSPER_CONTRACT_COVERAGE_CD_SLAV": [None, None],
    "INSPER_CLAIM_BASIS_CD": [None, None],
    "INSPER_LODRA_CD_SLAV": [None, None],
    "INSPER_LOD_TO_RA_DATE_SLAV": [None, None],
    "INSPER_COMMENT": [None, None],
}

sections_data = {
    # Keys and References
    "BUSCL_ID_PRE": [1, 2],
    "REPROG_ID_PRE": [1, 1],
    "CED_ID_PRE": [None, None],
    "BUSINESS_ID_PRE": [None, None],
    "INSPER_ID_PRE": [1, 2],
    # Exclusions and Names
    "BUSCL_EXCLUDE_CD": [None, None],
    "BUSCL_ENTITY_NAME_CED": [None, None],
    "POL_RISK_NAME_CED": [None, None],
    # Geographic and Product Dimensions
    "BUSCL_COUNTRY_CD": [None, None],
    "BUSCL_COUNTRY": [None, None],
    "BUSCL_REGION": [None, None],
    "BUSCL_CLASS_OF_BUSINESS_1": [None, None],
    "BUSCL_CLASS_OF_BUSINESS_2": [None, None],
    "BUSCL_CLASS_OF_BUSINESS_3": [None, None],
    # Currency and Limits
    "BUSCL_LIMIT_CURRENCY_CD": [None, None],
    "AAD_100": [None, None],
    "LIMIT_100": [None, None],
    "LIMIT_FLOATER_100": [None, None],
    "ATTACHMENT_POINT_100": [np.nan, np.nan],
    "OLW_100": [None, None],
    "LIMIT_OCCURRENCE_100": [None, None],
    "LIMIT_AGG_100": [None, None],
    # Cession and Retention
    "CESSION_PCT": [0.10, 0.15],
    "RETENTION_PCT": [None, None],
    "SUPI_100": [None, None],
    # Premiums
    "BUSCL_PREMIUM_CURRENCY_CD": [None, None],
    "BUSCL_PREMIUM_GROSS_NET_CD": [None, None],
    "PREMIUM_RATE_PCT": [None, None],
    "PREMIUM_DEPOSIT_100": [None, None],
    "PREMIUM_MIN_100": [None, None],
    # Coverage and Participations
    "BUSCL_LIABILITY_1_LINE_100": [None, None],
    "MAX_COVER_PCT": [None, None],
    "MIN_EXCESS_PCT": [None, None],
    "SIGNED_SHARE_PCT": [1.0, 1.0],
    "AVERAGE_LINE_SLAV_CED": [None, None],
    "PML_DEFAULT_PCT": [None, None],
    "LIMIT_EVENT": [None, None],
    "NO_OF_REINSTATEMENTS": [None, None],
}

program_df = pd.DataFrame(program_data)
structures_df = pd.DataFrame(structures_data)
sections_df = pd.DataFrame(sections_data)

# Créer le dossier programs s'il n'existe pas
output_dir = Path(__file__).parent / "programs"
os.makedirs(output_dir, exist_ok=True)

output_file = output_dir / "double_quota_share.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    program_df.to_excel(writer, sheet_name=SHEETS.PROGRAM, index=False)
    structures_df.to_excel(writer, sheet_name=SHEETS.STRUCTURES, index=False)
    sections_df.to_excel(writer, sheet_name=SHEETS.SECTIONS, index=False)

# Auto-adjust column widths for better readability
auto_adjust_column_widths(output_file)

print(f"✓ Programme Double Quota Share créé: {output_file}")

# =============================================================================
# AFFICHAGE DES DÉTAILS
# =============================================================================

print("\n" + "=" * 80)
print("PROGRAMME DOUBLE QUOTA SHARE")
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

print(
    """
Exemple avec une police de 1M d'exposition:

PROGRAMME DOUBLE QUOTA SHARE:
1. QS_10% s'applique sur 1M → 0.1M cédé
2. QS_15% s'applique sur 1M → 0.15M cédé
   Total cédé: 0.25M (10% + 15%)
   Total retenu: 0.75M

PRINCIPE:
- Deux quota shares qui s'appliquent en parallèle
- Pas de conditions géographiques ou autres
- Les deux structures s'appliquent sur la même exposition brute
- Les cessions s'additionnent
"""
)

print("\n✓ Le programme Double Quota Share est prêt !")

