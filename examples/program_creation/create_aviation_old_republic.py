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
# Ce script utilise Snowpark pour la sauvegarde des programmes
# La configuration Snowflake est chargée depuis le fichier snowflake_config.env

# =============================================================================
# SCRIPT
# =============================================================================

import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.builders import build_excess_of_loss, build_program
from snowflake_utils.utils_snowpark import save_program_snowpark

print("Création du programme Aviation Old Republic 2024...")
print("Backend de sauvegarde: Snowpark")

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
    main_currency="EUR", underwriting_department="aviation",
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
print("PROGRAMME AVIATION OLD REPUBLIC 2024")
print("=" * 80)
program.describe()
