"""
Création d'un programme simple avec quota share

Programme: Single Quota share
- Un seul quota share de 30% appliqué à toutes les polices
"""

# =============================================================================
# CONFIGURATION
# =============================================================================
# Choisir le backend de sauvegarde : "csv_folder" ou "snowflake"
BACKEND = "snowflake"  # Changez cette valeur selon vos besoins

# Configuration Snowflake (utilisée seulement si BACKEND = "snowflake")
# Les paramètres sont chargés depuis le fichier snowflake_config.env

# =============================================================================
# SCRIPT
# =============================================================================

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from tests.builders import build_quota_share, build_program
from snowflake_utils import save_program

print("Création du programme Single Quota share...")
print(f"Backend de sauvegarde: {BACKEND}")

qs = build_quota_share(
    name="QS_30",
    conditions_config=[
        {
            "cession_pct": 0.30,
        }
    ],
    claim_basis="risk_attaching",
    inception_date="2024-01-01",
    expiry_date="2025-01-01",
)

program = build_program(
    name="SINGLE_QUOTA_SHARE_2024", structures=[qs], underwriting_department="test"
)

# =============================================================================
# SAUVEGARDE
# =============================================================================

# Sauvegarde avec l'utilitaire partagé
output_path = save_program(program, BACKEND, "SINGLE_QUOTA_SHARE_2024")

# =============================================================================
# AFFICHAGE
# =============================================================================

print("\n" + "=" * 80)
print("PROGRAMME SINGLE QUOTA SHARE")
print("=" * 80)
program.describe()

print(f"\n✓ Programme Single Quota share créé et sauvegardé en {BACKEND} !")
