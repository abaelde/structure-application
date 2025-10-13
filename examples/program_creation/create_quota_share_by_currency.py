"""
Création d'un programme avec quota share différent selon la currency

Programme: Quota Share by Currency
- Section USD: 25% cession pour polices en USD
- Section EUR: 35% cession pour polices en EUR
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pandas as pd
import numpy as np
from excel_utils import auto_adjust_column_widths

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.domain import PRODUCT, SHEETS

print("Création du programme Quota Share by Currency...")

program_data = {
    "REPROG_ID_PRE": [1],
    "REPROG_TITLE": ["QS_BY_CURRENCY_2024"],
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
    "INSPER_ID_PRE": [1],
    "BUSINESS_ID_PRE": [None],
    "TYPE_OF_PARTICIPATION_CD": [PRODUCT.QUOTA_SHARE],
    "TYPE_OF_INSURED_PERIOD_CD": [None],
    "ACTIVE_FLAG_CD": [True],
    "INSPER_EFFECTIVE_DATE": [None],
    "INSPER_EXPIRY_DATE": [None],
    "REPROG_ID_PRE": [1],
    "BUSINESS_TITLE": ["QS_BY_CURRENCY"],
    "INSPER_LAYER_NO": [None],
    "INSPER_MAIN_CURRENCY_CD": [None],
    "INSPER_UW_YEAR": [None],
    "INSPER_CONTRACT_ORDER": [None],
    "INSPER_PREDECESSOR_TITLE": [None],
    "INSPER_CONTRACT_FORM_CD_SLAV": [None],
    "INSPER_CONTRACT_LODRA_CD_SLAV": [None],
    "INSPER_CONTRACT_COVERAGE_CD_SLAV": [None],
    "INSPER_CLAIM_BASIS_CD": [None],
    "INSPER_LODRA_CD_SLAV": [None],
    "INSPER_LOD_TO_RA_DATE_SLAV": [None],
    "INSPER_COMMENT": [None],
}

sections_data = {
    "BUSCL_ID_PRE": [1, 2],
    "REPROG_ID_PRE": [1, 1],
    "CED_ID_PRE": [None, None],
    "BUSINESS_ID_PRE": [None, None],
    "INSPER_ID_PRE": [1, 1],
    "BUSCL_EXCLUDE_CD": [None, None],
    "BUSCL_ENTITY_NAME_CED": [None, None],
    "POL_RISK_NAME_CED": [None, None],
    "BUSCL_COUNTRY_CD": [None, None],
    "BUSCL_COUNTRY": [None, None],
    "BUSCL_REGION": [None, None],
    "BUSCL_CLASS_OF_BUSINESS_1": [None, None],
    "BUSCL_CLASS_OF_BUSINESS_2": [None, None],
    "BUSCL_CLASS_OF_BUSINESS_3": [None, None],
    "BUSCL_LIMIT_CURRENCY_CD": ["USD", "EUR"],
    "AAD_100": [None, None],
    "LIMIT_100": [None, None],
    "LIMIT_FLOATER_100": [None, None],
    "ATTACHMENT_POINT_100": [np.nan, np.nan],
    "OLW_100": [None, None],
    "LIMIT_OCCURRENCE_100": [None, None],
    "LIMIT_AGG_100": [None, None],
    "CESSION_PCT": [0.25, 0.35],
    "RETENTION_PCT": [None, None],
    "SUPI_100": [None, None],
    "BUSCL_PREMIUM_CURRENCY_CD": [None, None],
    "BUSCL_PREMIUM_GROSS_NET_CD": [None, None],
    "PREMIUM_RATE_PCT": [None, None],
    "PREMIUM_DEPOSIT_100": [None, None],
    "PREMIUM_MIN_100": [None, None],
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

output_dir = "../programs"
os.makedirs(output_dir, exist_ok=True)

output_file = "../programs/quota_share_by_currency.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    program_df.to_excel(writer, sheet_name=SHEETS.PROGRAM, index=False)
    structures_df.to_excel(writer, sheet_name=SHEETS.STRUCTURES, index=False)
    sections_df.to_excel(writer, sheet_name=SHEETS.SECTIONS, index=False)

auto_adjust_column_widths(output_file)

print("✓ Programme Quota Share by Currency créé: examples/programs/quota_share_by_currency.xlsx")

print("\n" + "=" * 80)
print("PROGRAMME QUOTA SHARE BY CURRENCY")
print("=" * 80)

print("\nProgram:")
print(program_df)

print("\nStructures:")
print(structures_df)

print("\nSections:")
print(sections_df[["BUSCL_ID_PRE", "INSPER_ID_PRE", "BUSCL_LIMIT_CURRENCY_CD", "CESSION_PCT", "SIGNED_SHARE_PCT"]])

print("\n" + "=" * 80)
print("COMPORTEMENT DU PROGRAMME")
print("=" * 80)

print("""
Exemple avec 2 polices:
- Police USD de 1M: QS 25% → 0.25M cédé, 0.75M retenu
- Police EUR de 1M: QS 35% → 0.35M cédé, 0.65M retenu

PRINCIPE:
- Une structure avec 2 sections selon la currency
- Section USD: 25% de cession
- Section EUR: 35% de cession
- Permet de tester le matching dimensionnel
""")

print("\n✓ Le programme Quota Share by Currency est prêt !")

