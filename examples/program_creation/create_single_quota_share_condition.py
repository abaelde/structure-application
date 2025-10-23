"""
Création d'un programme avec quota share et condition spécifique

Programme: Quota Share with Country Condition
- Quota share de 30% par défaut
- Condition spéciale : 50% de cession pour les polices en France
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

print("Création du programme Quota Share with Country Condition...")
print("Backend de sauvegarde: Snowpark")

qs = build_quota_share(
    name="QS_30_with_France_50",
    cession_pct=0.30,  # Valeur par défaut : 30%
    signed_share=1.0,
    special_conditions=[
        {
            "COUNTRY": "France",  # Condition spécifique pour la France
            "cession_pct": 0.50,     # 50% de cession pour la France
        }
    ],
    claim_basis="risk_attaching",
    inception_date="2024-01-01",
    expiry_date="2025-01-01",
)

# Construction du programme avec timestamp unique
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
program_name = f"QUOTA_SHARE_WITH_FRANCE_CONDITION_{timestamp}"

program = build_program(
    name=program_name, structures=[qs], main_currency="EUR", underwriting_department="test"
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

# =============================================================================
# AFFICHAGE
# =============================================================================

print("\n" + "=" * 80)
print("PROGRAMME QUOTA SHARE WITH FRANCE CONDITION")
print("=" * 80)
program.describe()

print(f"\n✓ Programme Quota Share with France Condition créé et sauvegardé via Snowpark !")
print("\nStructure du programme:")
print("  - 1 structure: QS_30_with_France_50")
print("  - Valeur par défaut: 30% de cession")
print("  - Condition spéciale: 50% de cession pour les polices en France")
