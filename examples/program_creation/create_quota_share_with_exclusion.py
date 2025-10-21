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

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from tests.builders import build_quota_share, build_program
from src.domain.exclusion import ExclusionRule
from snowflake_utils import save_program

print("Création du programme Quota Share with Exclusions...")
print(f"Backend de sauvegarde: {BACKEND}")

# Créer un quota share avec condition normale uniquement
qs = build_quota_share(
    name="QS Aviation 25%",
    conditions_config=[
        {
            "country_cd": None,
            "cession_pct": 0.25,
            "signed_share": 1.0,
            "includes_hull": True,
            "includes_liability": True,
        },
    ],
    claim_basis="risk_attaching",
    inception_date="2024-01-01",
    expiry_date="2024-12-31",
)

program = build_program(
    name="Quota Share with Exclusions Test",
    structures=[qs],
    underwriting_department="aviation",
)

# Ajouter les exclusions au niveau programme
exclusions = [
    ExclusionRule(
        values_by_dimension={'BUSCL_COUNTRY_CD': ['Iran']},
        name='Sanctions Iran'
    ),
    ExclusionRule(
        values_by_dimension={'BUSCL_COUNTRY_CD': ['Russia']},
        name='Sanctions Russia'
    ),
]
program.exclusions = exclusions

# =============================================================================
# SAUVEGARDE
# =============================================================================

# Sauvegarde avec l'utilitaire partagé
output_path = save_program(program, BACKEND, "Quota Share with Exclusions Test")

print(f"✓ Programme créé: {output_path}")
print("\nStructure du programme:")
print("  - 1 structure: QS Aviation 25%")
print("  - 2 exclusions globales de programme:")
print("    - Iran (pays) - Sanctions Iran")
print("    - Russia (pays) - Sanctions Russia")
print("  - 1 condition normale: 25% cession sur tout le reste")
