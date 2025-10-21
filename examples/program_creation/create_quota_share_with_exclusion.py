"""
Création d'un programme Quota Share avec exclusions

Programme: Quota Share with Exclusions Test
- 2 exclusions globales de programme (Iran, Russia)
- 1 condition normale: 25% cession sur tout le reste
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

from tests.builders import build_quota_share, build_program
from src.domain.exclusion import ExclusionRule
from snowflake_utils import save_program

print("Création du programme Quota Share with Exclusions...")
print(f"Backend de sauvegarde: {BACKEND}")

# Créer un quota share avec condition normale uniquement
qs = build_quota_share(
    name="QS Casualty 25%",
    conditions_config=[
        {
            "country_cd": None,
            "cession_pct": 0.25,
            "signed_share": 1.0,
        },
    ],
    claim_basis="risk_attaching",
    inception_date="2024-01-01",
    expiry_date="2024-12-31",
)

# Créer les exclusions - Test de compaction multi-valeurs
exclusions = [
    ExclusionRule(
        values_by_dimension={"BUSCL_COUNTRY_CD": ["Iran", "Russia"]}, 
        name="Sanctions Countries"
    ),
]

# Créer le programme avec les exclusions et timestamp unique
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
program_name = f"Quota_Share_with_Exclusions_Test_{timestamp}"

program = build_program(
    name=program_name,
    structures=[qs],
    underwriting_department="casualty",
    exclusions=exclusions,
)

# =============================================================================
# SAUVEGARDE
# =============================================================================

# Sauvegarde avec l'utilitaire partagé
output_path = save_program(program, BACKEND, program_name)

print(f"✓ Programme créé: {output_path}")
print("\nStructure du programme:")
print("  - 1 structure: QS Casualty 25%")
print("  - 1 exclusion globale de programme:")
print("    - Iran, Russia (pays) - Sanctions Countries")
print("  - 1 condition normale: 25% cession sur tout le reste")
