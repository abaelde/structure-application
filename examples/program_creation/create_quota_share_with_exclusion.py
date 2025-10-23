"""
Création d'un programme Quota Share avec exclusions

Programme: Quota Share with Exclusions Test
- 2 exclusions globales de programme (Iran, Russia)
- 1 condition normale: 25% cession sur tout le reste
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
from src.domain.exclusion import ExclusionRule
from snowflake_utils.utils_snowpark import save_program_snowpark

print("Création du programme Quota Share with Exclusions...")
print("Backend de sauvegarde: Snowpark")

# Créer un quota share avec condition normale uniquement
qs = build_quota_share(
    name="QS Casualty 25%",
    cession_pct=0.25,
    signed_share=1.0,
    claim_basis="risk_attaching",
    inception_date="2024-01-01",
    expiry_date="2024-12-31",
)

# Créer les exclusions - Test de compaction multi-valeurs
exclusions = [
    ExclusionRule(
        values_by_dimension={"COUNTRY": ["Iran", "Russia"]},
        name="Sanctions Countries",
    ),
]

# Créer le programme avec les exclusions et timestamp unique
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
program_name = f"Quota_Share_with_Exclusions_Test_{timestamp}"

program = build_program(
    name=program_name,
    structures=[qs],
    main_currency="EUR", underwriting_department="casualty",
    exclusions=exclusions,
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
print("\nStructure du programme:")
print("  - 1 structure: QS Casualty 25%")
print("  - 1 exclusion globale de programme:")
print("    - Iran, Russia (pays) - Sanctions Countries")
print("  - 1 condition normale: 25% cession sur tout le reste")
