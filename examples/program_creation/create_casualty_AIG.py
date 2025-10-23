"""
Création du programme Casualty AIG 2024

Programme casualty avec 1 structure Quota Share avec 2 conditions:
1. condition générale: Quota Share 100% avec limite de 25M
2. condition cyber: Quota Share 100% avec limite de 10M sur le produit Cyber

Programme risk attaching avec réassureur share à 10% (à déterminer)
"""

# =============================================================================
# CONFIGURATION
# =============================================================================
# Ce script utilise Snowpark pour la sauvegarde des programmes
# La configuration Snowflake est chargée depuis le fichier snowflake_config.env

# =============================================================================
# SCRIPT
# =============================================================================

import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.builders import build_quota_share, build_program
from snowflake_utils.utils_snowpark import save_program_snowpark

print("Création du programme Casualty AIG 2024...")
print("Backend de sauvegarde: Snowpark")

CESSION_RATE = 1.0
REINSURER_SHARE = 0.10

qs = build_quota_share(
    name="QS_1",
    cession_pct=CESSION_RATE,
    signed_share=REINSURER_SHARE,
    special_conditions=[
        {
            "limit": 10_000_000,
            "PRODUCT_TYPE_LEVEL_1": ["Cyber"],  # Condition sur le type de produit (liste)
        },
    ],
    claim_basis="risk_attaching",
    inception_date="2024-01-01",
    expiry_date="2025-01-01",
)

# Construction du programme avec timestamp unique
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
program_name = f"CASUALTY_AIG_2024_{timestamp}"

program = build_program(
    name=program_name, structures=[qs], main_currency="EUR", underwriting_department="casualty"
)

# =============================================================================
# SAUVEGARDE
# =============================================================================

# Sauvegarde avec l'utilitaire Snowpark
try:
    success = save_program_snowpark(program, program_name)
    if success:
        print(f"✓ Programme sauvegardé avec succès via Snowpark: {program_name}")
    else:
        print(f"❌ Échec de la sauvegarde du programme: {program_name}")
except Exception as e:
    print(f"❌ Erreur lors de la sauvegarde: {e}")
    print("Le programme a été construit correctement mais la sauvegarde a échoué.")

print("\n" + "=" * 80)
print("PROGRAMME CASUALTY AIG 2024")
print("=" * 80)

program.describe()
