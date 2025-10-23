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
# Choisir le backend de sauvegarde : "snowflake" ou "csv_folder"
BACKEND = "csv_folder"  # Changez cette valeur selon vos besoins

# =============================================================================
# SCRIPT
# =============================================================================

import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.builders import build_quota_share, build_program
from snowflake_utils import save_program

print("Création du programme Casualty AIG 2024...")
print(f"Backend de sauvegarde: {BACKEND}")

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

# Sauvegarde avec l'utilitaire partagé
output_path = save_program(program, BACKEND, program_name)

print(f"✓ Programme créé: {output_path}")

print("\n" + "=" * 80)
print("PROGRAMME CASUALTY AIG 2024")
print("=" * 80)

program.describe()
