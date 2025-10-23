"""
Création d'un programme simple avec quota share

Programme: Single Quota share
- Un seul quota share de 30% appliqué à toutes les polices
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

print("Création du programme Single Quota share...")
print("Backend de sauvegarde: Snowpark")

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
print("PROGRAMME SINGLE QUOTA SHARE")
print("=" * 80)
program.describe()

print(f"\n✓ Programme Single Quota share créé et sauvegardé via Snowpark !")
