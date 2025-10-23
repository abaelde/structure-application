"""
Création d'un programme de test avec des exclusions multi-valeurs
pour vérifier la logique de compaction dans Snowflake.
"""

# =============================================================================
# CONFIGURATION
# =============================================================================
BACKEND = "snowflake"

# =============================================================================
# SCRIPT
# =============================================================================

import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.builders import build_quota_share, build_program
from src.domain.exclusion import ExclusionRule
from snowflake_utils import save_program

print("Création du programme de test avec exclusions multi-valeurs...")
print(f"Backend de sauvegarde: {BACKEND}")

# Construction d'un Quota Share simple
qs = build_quota_share(
    name="QS_TEST",
    cession_pct=0.30,
    claim_basis="risk_attaching",
    inception_date="2024-01-01",
    expiry_date="2025-01-01",
)

# Construction des exclusions avec multi-valeurs
exclusions = [
    # Exclusion 1: Multi-pays
    ExclusionRule(
        name="Cyber_Exclusion",
        values_by_dimension={
            "COUNTRY": ["US", "CA", "UK", "DE"],
            "PRODUCT_TYPE_LEVEL_1": ["Cyber", "Technology"],
        },
        effective_date="2024-01-01",
        expiry_date="2025-01-01",
    ),
    # Exclusion 2: Multi-régions et multi-produits
    ExclusionRule(
        name="War_Exclusion",
        values_by_dimension={
            "REGION": ["Middle East", "Africa", "Asia"],
            "PRODUCT_TYPE_LEVEL_1": ["War", "Terrorism"],
            "PRODUCT_TYPE_LEVEL_2": ["Marine", "Aviation"],
        },
        effective_date="2024-01-01",
        expiry_date="2025-01-01",
    ),
    # Exclusion 3: Multi-entités
    ExclusionRule(
        name="Entity_Exclusion",
        values_by_dimension={
            "BUSCL_ENTITY_NAME_CED": ["Entity_A", "Entity_B", "Entity_C"],
            "POL_RISK_NAME_CED": ["Risk_1", "Risk_2"],
        },
        effective_date="2024-01-01",
        expiry_date="2025-01-01",
    ),
]

# Construction du programme avec timestamp unique
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
program_name = f"TEST_EXCLUSIONS_2024_{timestamp}"

program = build_program(
    name=program_name,
    structures=[qs],
    underwriting_department="casualty",
    exclusions=exclusions,
)

# =============================================================================
# SAUVEGARDE
# =============================================================================

if __name__ == "__main__":
    # Sauvegarde avec l'utilitaire partagé
    output_path = save_program(program, BACKEND, program_name)

# =============================================================================
# AFFICHAGE
# =============================================================================

print("\n" + "=" * 80)
print("PROGRAMME TEST EXCLUSIONS 2024")
print("=" * 80)

program.describe()

print("\n" + "=" * 80)
print("RÉSUMÉ DU PROGRAMME")
print("=" * 80)

print(
    f"""
Programme: Test Exclusions 2024
Backend: {BACKEND}

Structures:
- QS_TEST: Quota Share 30% cédé

Exclusions:
- Cyber_Exclusion: Pays [US, CA, UK, DE] + Produits [Cyber, Technology]
- War_Exclusion: Régions [Middle East, Africa, Asia] + Produits [War, Terrorism, Marine, Aviation]
- Entity_Exclusion: Entités [Entity_A, Entity_B, Entity_C] + Risques [Risk_1, Risk_2]
"""
)

print(f"\n✓ Le programme Test Exclusions 2024 est prêt et sauvegardé en {BACKEND} !")
