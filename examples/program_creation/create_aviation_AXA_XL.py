"""
Création du programme Aviation Complex Multi-Currency

Programme aviation avec 1 structure Quota Share + 6 layers excess of loss, chacun défini pour 5 devises:
- USD, CAD, EUR, AUD (valeurs identiques)
- GBP (valeurs spécifiques)

Structure:
- 1 structure Quota Share (QS_1) avec rétention 75% et reinsurer_share 1.65%
- 6 layers XOL empilés (XOL_1 à XOL_6)
- Chaque structure a des sections pour USD, CAD, EUR, AUD et GBP
- Priorités et limites définies par devise
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pandas as pd
import numpy as np
from excel_utils import auto_adjust_column_widths

print("Création du programme Aviation Complex Multi-Currency...")

# =============================================================================
# CONFIGURATION DES VALEURS - À MODIFIER SELON VOS BESOINS
# =============================================================================

# Définir les valeurs pour chaque layer (en millions)
# Format: (attachment_point_100, limit_occurrence_100)
# Les valeurs sont identiques pour USD, CAD, EUR, AUD
LAYER_VALUES_COMMON = {
    "XOL_1": (65, 0),
    "XOL_2": (50, 65),
    "XOL_3": (100, 115),
    "XOL_4": (100, 215),
    "XOL_5": (100, 315),
    "XOL_6": (150, 415),
}

# Valeurs spécifiques pour GBP (en millions)
LAYER_VALUES_GBP = {
    "XOL_1": (43.333333, 23.333333),
    "XOL_2": (33.333333, 43.333333),
    "XOL_3": (66.666666, 76.666666),
    "XOL_4": (66.666666, 143.333333),
    "XOL_5": (66.666666, 210),
    "XOL_6": (100, 276.666666),
}

# Cession Rate Values (pourcentage cédé au réassureur)
CESSION_RATE_VALUES = {
    "QS_1": 0.25,  # 25% cédé (rétention 75%)
    "XOL_1": np.nan,  # XOL n'utilise pas cession_PCT
    "XOL_2": np.nan,
    "XOL_3": np.nan,
    "XOL_4": np.nan,
    "XOL_5": np.nan,
    "XOL_6": np.nan,
}

# Reinsurer Share Values (part du réassureur dans la cession)
REINSURER_SHARE_VALUES = {
    "QS_1": 0.0165,  # 1.65% du réassureur dans la cession de 25%
    "XOL_1": 0.05,
    "XOL_2": 0.05,
    "XOL_3": 0.05,
    "XOL_4": 0.05,
    "XOL_5": 0.05,
    "XOL_6": 0.05,
}

# =============================================================================
# DÉFINITION DU PROGRAMME
# =============================================================================

program_data = {
    "REPROG_ID_PRE": [1],  # Auto-increment key
    "REPROG_TITLE": ["AVIATION_AXA_XL_2024"],  # Former program_name
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
# DÉFINITION DES STRUCTURES (1 Quota Share + 6 layers XOL)
# =============================================================================

structures_data = {
    "INSPER_ID_PRE": [1, 2, 3, 4, 5, 6, 7],  # Auto-increment key
    "BUSINESS_ID_PRE": [None, None, None, None, None, None, None],  # Tnumber
    "TYPE_OF_PARTICIPATION_CD": [
        "quota_share",
        "excess_of_loss",
        "excess_of_loss",
        "excess_of_loss",
        "excess_of_loss",
        "excess_of_loss",
        "excess_of_loss",
    ],  # Former type_of_participation
    "TYPE_OF_INSURED_PERIOD_CD": [None, None, None, None, None, None, None],  # TBD
    "ACTIVE_FLAG_CD": [True, True, True, True, True, True, True],  # Default active
    "INSPER_EFFECTIVE_DATE": [
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ],  # Former inception_date
    "INSPER_EXPIRY_DATE": [
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ],  # Former expiry_date
    "REPROG_ID_PRE": [1, 1, 1, 1, 1, 1, 1],  # Reference to program
    "BUSINESS_TITLE": [
        "QS_1",
        "XOL_1",
        "XOL_2",
        "XOL_3",
        "XOL_4",
        "XOL_5",
        "XOL_6",
    ],  # Former structure_name
    "INSPER_LAYER_NO": [None, None, None, None, None, None, None],  # Layer number
    "INSPER_MAIN_CURRENCY_CD": [
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ],  # Main currency
    "INSPER_UW_YEAR": [None, None, None, None, None, None, None],  # UW Year
    "INSPER_CONTRACT_ORDER": [0, 1, 2, 3, 4, 5, 6],  # Former contract_order
    "INSPER_CONTRACT_FORM_CD_SLAV": [
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ],  # Contract form code
    "INSPER_CONTRACT_LODRA_CD_SLAV": [
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ],  # Contract LODRA code
    "INSPER_CONTRACT_COVERAGE_CD_SLAV": [
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ],  # Contract coverage code
    "INSPER_CLAIM_BASIS_CD": [
        "risk_attaching",
        "risk_attaching",
        "risk_attaching",
        "risk_attaching",
        "risk_attaching",
        "risk_attaching",
        "risk_attaching",
    ],  # Former claim_basis
    "INSPER_LODRA_CD_SLAV": [None, None, None, None, None, None, None],  # LODRA code
    "INSPER_LOD_TO_RA_DATE_SLAV": [
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ],  # LOD to RA date
    "INSPER_COMMENT": [None, None, None, None, None, None, None],  # Comments
}

# =============================================================================
# DÉFINITION DES SECTIONS
# =============================================================================

# Devises communes (USD, CAD, EUR, AUD)
COMMON_CURRENCIES = ["USD", "CAD", "EUR", "AUD"]

# Initialiser les listes pour les sections
sections_data = {
    # Keys and References
    "BUSCL_ID_PRE": [],  # Auto-increment key
    "REPROG_ID_PRE": [],  # Reference to program
    "CED_ID_PRE": [],  # Reference to cedant
    "BUSINESS_ID_PRE": [],  # Reference to business
    "INSPER_ID_PRE": [],  # Reference to structure
    # Exclusions and Names
    "BUSCL_EXCLUDE_CD": [],  # ENUM: INCLUDE or EXCLUDE
    "BUSCL_ENTITY_NAME_CED": [],  # Cedant entity name
    "POL_RISK_NAME_CED": [],  # Policy risk name
    # Geographic and Product Dimensions
    "BUSCL_COUNTRY_CD": [],  # Former country
    "BUSCL_COUNTRY": [],  # Country name
    "BUSCL_REGION": [],  # Former region
    "BUSCL_CLASS_OF_BUSINESS_1": [],  # Former product_type_1
    "BUSCL_CLASS_OF_BUSINESS_2": [],  # Former product_type_2
    "BUSCL_CLASS_OF_BUSINESS_3": [],  # Former product_type_3
    # Currency and Limits
    "BUSCL_LIMIT_CURRENCY_CD": [],  # Former currency
    "AAD_100": [],  # Annual Aggregate Deductible
    "LIMIT_100": [],  # General limit
    "LIMIT_FLOATER_100": [],  # Floater limit
    "ATTACHMENT_POINT_100": [],  # Former attachment_point_100
    "OLW_100": [],  # Original Line Written
    "LIMIT_OCCURRENCE_100": [],  # Former limit_occurrence_100
    "LIMIT_AGG_100": [],  # Aggregate limit
    # Cession and Retention
    "CESSION_PCT": [],  # Former cession_PCT
    "RETENTION_PCT": [],  # Retention percentage
    "SUPI_100": [],  # SUPI
    # Premiums
    "BUSCL_PREMIUM_CURRENCY_CD": [],  # Premium currency
    "BUSCL_PREMIUM_GROSS_NET_CD": [],  # Gross/Net premium
    "PREMIUM_RATE_PCT": [],  # Premium rate percentage
    "PREMIUM_DEPOSIT_100": [],  # Premium deposit
    "PREMIUM_MIN_100": [],  # Minimum premium
    # Coverage and Participations
    "BUSCL_LIABILITY_1_LINE_100": [],  # Liability line 1
    "MAX_COVER_PCT": [],  # Maximum coverage percentage
    "MIN_EXCESS_PCT": [],  # Minimum excess percentage
    "SIGNED_SHARE_PCT": [],  # Former reinsurer_share
    "AVERAGE_LINE_SLAV_CED": [],  # Average line
    "PML_DEFAULT_PCT": [],  # PML default percentage
    "LIMIT_EVENT": [],  # Limit per event
    "NO_OF_REINSTATEMENTS": [],  # Number of reinstatements
}

# Counter for section IDs
section_id_counter = 1


# Helper function to add a section
def add_section(
    insper_id,
    cession_pct,
    attachment_point,
    limit_occurrence,
    signed_share,
    currency_cd,
):
    global section_id_counter
    sections_data["BUSCL_ID_PRE"].append(section_id_counter)
    sections_data["REPROG_ID_PRE"].append(1)
    sections_data["CED_ID_PRE"].append(None)
    sections_data["BUSINESS_ID_PRE"].append(None)
    sections_data["INSPER_ID_PRE"].append(insper_id)
    sections_data["BUSCL_EXCLUDE_CD"].append(None)
    sections_data["BUSCL_ENTITY_NAME_CED"].append(None)
    sections_data["POL_RISK_NAME_CED"].append(None)
    sections_data["BUSCL_COUNTRY_CD"].append(None)
    sections_data["BUSCL_COUNTRY"].append(None)
    sections_data["BUSCL_REGION"].append(None)
    sections_data["BUSCL_CLASS_OF_BUSINESS_1"].append(None)
    sections_data["BUSCL_CLASS_OF_BUSINESS_2"].append(None)
    sections_data["BUSCL_CLASS_OF_BUSINESS_3"].append(None)
    sections_data["BUSCL_LIMIT_CURRENCY_CD"].append(currency_cd)
    sections_data["AAD_100"].append(None)
    sections_data["LIMIT_100"].append(None)
    sections_data["LIMIT_FLOATER_100"].append(None)
    sections_data["ATTACHMENT_POINT_100"].append(attachment_point)
    sections_data["OLW_100"].append(None)
    sections_data["LIMIT_OCCURRENCE_100"].append(limit_occurrence)
    sections_data["LIMIT_AGG_100"].append(None)
    sections_data["CESSION_PCT"].append(cession_pct)
    sections_data["RETENTION_PCT"].append(None)
    sections_data["SUPI_100"].append(None)
    sections_data["BUSCL_PREMIUM_CURRENCY_CD"].append(None)
    sections_data["BUSCL_PREMIUM_GROSS_NET_CD"].append(None)
    sections_data["PREMIUM_RATE_PCT"].append(None)
    sections_data["PREMIUM_DEPOSIT_100"].append(None)
    sections_data["PREMIUM_MIN_100"].append(None)
    sections_data["BUSCL_LIABILITY_1_LINE_100"].append(None)
    sections_data["MAX_COVER_PCT"].append(None)
    sections_data["MIN_EXCESS_PCT"].append(None)
    sections_data["SIGNED_SHARE_PCT"].append(signed_share)
    sections_data["AVERAGE_LINE_SLAV_CED"].append(None)
    sections_data["PML_DEFAULT_PCT"].append(None)
    sections_data["LIMIT_EVENT"].append(None)
    sections_data["NO_OF_REINSTATEMENTS"].append(None)
    section_id_counter += 1


# Créer les sections pour la structure Quota Share (QS_1) - toutes devises
cession_rate_qs = CESSION_RATE_VALUES["QS_1"]
reinsurer_share_qs = REINSURER_SHARE_VALUES["QS_1"]
for currency in COMMON_CURRENCIES + ["GBP"]:
    add_section(
        insper_id=1,  # QS_1 has INSPER_ID_PRE = 1
        cession_pct=cession_rate_qs,
        attachment_point=np.nan,
        limit_occurrence=np.nan,
        signed_share=reinsurer_share_qs,
        currency_cd=currency,
    )

# Créer les sections pour les devises communes (USD, CAD, EUR, AUD) - structures XOL
for idx, layer_name in enumerate(
    ["XOL_1", "XOL_2", "XOL_3", "XOL_4", "XOL_5", "XOL_6"], start=2
):
    limit_occurrence_100, attachment_point_100 = LAYER_VALUES_COMMON[layer_name]
    cession_PCT = CESSION_RATE_VALUES[layer_name]
    reinsurer_share = REINSURER_SHARE_VALUES[layer_name]

    for currency in COMMON_CURRENCIES:
        add_section(
            insper_id=idx,  # XOL_1=2, XOL_2=3, ..., XOL_6=7
            cession_pct=cession_PCT,
            attachment_point=attachment_point_100,
            limit_occurrence=limit_occurrence_100,
            signed_share=reinsurer_share,
            currency_cd=currency,
        )

# Créer les sections pour GBP (valeurs spécifiques) - structures XOL
for idx, layer_name in enumerate(
    ["XOL_1", "XOL_2", "XOL_3", "XOL_4", "XOL_5", "XOL_6"], start=2
):
    limit_occurrence_100, attachment_point_100 = LAYER_VALUES_GBP[layer_name]
    cession_PCT = CESSION_RATE_VALUES[layer_name]
    reinsurer_share = REINSURER_SHARE_VALUES[layer_name]

    add_section(
        insper_id=idx,  # XOL_1=2, XOL_2=3, ..., XOL_6=7
        cession_pct=cession_PCT,
        attachment_point=attachment_point_100,
        limit_occurrence=limit_occurrence_100,
        signed_share=reinsurer_share,
        currency_cd="GBP",
    )

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

output_file = os.path.join(output_dir, "aviation_axa_xl_2024.xlsx")

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    program_df.to_excel(writer, sheet_name="program", index=False)
    structures_df.to_excel(writer, sheet_name="structures", index=False)
    sections_df.to_excel(writer, sheet_name="sections", index=False)

# Auto-adjust column widths for better readability
auto_adjust_column_widths(output_file)

print(f"✓ Programme créé: {output_file}")

# =============================================================================
# AFFICHAGE DES DÉTAILS
# =============================================================================

print("\n" + "=" * 80)
print("PROGRAMME AVIATION AXA XL 2024")
print("=" * 80)

print("\nProgram:")
print(program_df)

print("\nStructures:")
print(structures_df)

print("\nSections (premières 10 lignes):")
print(sections_df.head(10))

print(f"\nTotal sections créées: {len(sections_df)}")
print(f"Répartition par devise:")
print(sections_df["BUSCL_LIMIT_CURRENCY_CD"].value_counts())

# =============================================================================
# RÉSUMÉ DU PROGRAMME
# =============================================================================

print("\n" + "=" * 80)
print("RÉSUMÉ DU PROGRAMME")
print("=" * 80)

print(
    """
Programme: Aviation AXA XL 2024
Devises: USD, CAD, EUR, AUD, GBP

Structures (empilées selon l'ordre):
"""
)

print("0. QS_1 (contract_order=0):")
print(
    "   - Toutes devises: Quota Share 25% cédé, 1.65% reinsurer share (rétention 75%)"
)

for i, layer in enumerate(["XOL_1", "XOL_2", "XOL_3", "XOL_4", "XOL_5", "XOL_6"], 1):
    priority_common, limit_common = LAYER_VALUES_COMMON[layer]
    priority_gbp, limit_gbp = LAYER_VALUES_GBP[layer]
    print(f"{i}. {layer} (contract_order={i}):")
    print(f"   - USD/CAD/EUR/AUD: {limit_common}M xs {priority_common}M")
    print(f"   - GBP: {limit_gbp}M xs {priority_gbp}M")


print("\n✓ Le programme Aviation AXA XL 2024 est prêt !")
print("\nPour modifier les valeurs:")
print(
    "1. Éditez le dictionnaire CESSION_RATE_VALUES pour ajuster les pourcentages de cession"
)
print(
    "2. Éditez le dictionnaire REINSURER_SHARE_VALUES pour ajuster les parts du réassureur"
)
print(
    "3. Éditez les dictionnaires LAYER_VALUES_COMMON et LAYER_VALUES_GBP pour les XOL"
)
print("4. Relancez ce script pour régénérer le fichier Excel")
