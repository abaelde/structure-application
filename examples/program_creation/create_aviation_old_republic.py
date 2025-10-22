"""
Création du programme Aviation Old Republic 2024

Programme risk attaching avec 3 structures excess of loss pour United States et Canada:
1. XOL_1: Priorité 3M, Limite 8.75M
2. XOL_2: Priorité 11.75M, Limite 10M
3. XOL_3: Priorité 21.75M, Limite 23.25M
"""

# =============================================================================
# CONFIGURATION
# =============================================================================
# Choisir le backend de sauvegarde : "snowflake" ou "csv_folder"
BACKEND = "snowflake"  # Changez cette valeur selon vos besoins

# =============================================================================
# SCRIPT
# =============================================================================

import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.builders import build_excess_of_loss, build_program
from snowflake_utils import save_program

print("Création du programme Aviation Old Republic 2024...")
print(f"Backend de sauvegarde: {BACKEND}")

REINSURER_SHARE_VALUES = {
    "XOL_1": 0.1,
    "XOL_2": 0.1,
    "XOL_3": 0.0979,
}

xol_1 = build_excess_of_loss(
    name="XOL_1",
    # Valeurs par défaut de la structure (s'appliquent à tous les pays)
    attachment=3_000_000,
    limit=8_750_000,
    signed_share=REINSURER_SHARE_VALUES["XOL_1"],
    # Aucune condition spéciale - les mêmes valeurs s'appliquent partout
    claim_basis="risk_attaching",
    inception_date="2024-01-01",
    expiry_date="2025-01-01",
)

xol_2 = build_excess_of_loss(
    name="XOL_2",
    # Valeurs par défaut de la structure (s'appliquent à tous les pays)
    attachment=11_750_000,
    limit=10_000_000,
    signed_share=REINSURER_SHARE_VALUES["XOL_2"],
    # Aucune condition spéciale - les mêmes valeurs s'appliquent partout
    claim_basis="risk_attaching",
    inception_date="2024-01-01",
    expiry_date="2025-01-01",
)

xol_3 = build_excess_of_loss(
    name="XOL_3",
    # Valeurs par défaut de la structure (s'appliquent à tous les pays)
    attachment=21_750_000,
    limit=23_250_000,
    signed_share=REINSURER_SHARE_VALUES["XOL_3"],
    # Aucune condition spéciale - les mêmes valeurs s'appliquent partout
    claim_basis="risk_attaching",
    inception_date="2024-01-01",
    expiry_date="2025-01-01",
)

# Construction du programme avec timestamp unique
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
program_name = f"AVIATION_OLD_REPUBLIC_2024_{timestamp}"

program = build_program(
    name=program_name,
    structures=[xol_1, xol_2, xol_3],
    underwriting_department="aviation",
)

# =============================================================================
# SAUVEGARDE
# =============================================================================

# Sauvegarde avec l'utilitaire partagé
output_path = save_program(program, BACKEND, program_name)

print(f"✓ Programme créé: {output_path}")

print("\n" + "=" * 80)
print("PROGRAMME AVIATION OLD REPUBLIC 2024")
print("=" * 80)
program.describe()
