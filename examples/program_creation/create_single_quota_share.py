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
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.builders import build_quota_share, build_program
from snowflake_utils import save_program

print("Création du programme Single Quota share...")
print(f"Backend de sauvegarde: {BACKEND}")

qs = build_quota_share(
    name="QS_30",
    cession_pct=0.30,
    claim_basis="risk_attaching",
    inception_date="2024-01-01",
    expiry_date="2025-01-01",
)

# Construction du programme avec timestamp unique
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
program_name = f"SINGLE_QUOTA_SHARE_2024_{timestamp}"

program = build_program(
    name=program_name, 
    structures=[qs], 
    main_currency="EUR",
    underwriting_department="test"
)

# =============================================================================
# SAUVEGARDE
# =============================================================================

# Sauvegarde avec l'utilitaire partagé
output_path = save_program(program, BACKEND, program_name)

# =============================================================================
# AFFICHAGE
# =============================================================================

print("\n" + "=" * 80)
print("PROGRAMME SINGLE QUOTA SHARE")
print("=" * 80)
program.describe()

print(f"\n✓ Programme Single Quota share créé et sauvegardé en {BACKEND} !")
