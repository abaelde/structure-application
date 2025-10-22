"""
Création du programme Aviation Complex Multi-Currency

Programme aviation avec 1 structure Quota Share + 6 layers excess of loss, chacun défini pour 5 devises:
- USD, CAD, EUR, AUD (valeurs identiques)
- GBP (valeurs spécifiques)

Structure:
- 1 structure Quota Share (QS_1) avec rétention 75% et reinsurer_share 1.65%
- 6 layers XOL empilés (XOL_1 à XOL_6)
- Chaque structure a des conditions pour USD, CAD, EUR, AUD et GBP
- Priorités et limites définies par devise
"""

# =============================================================================
# CONFIGURATION
# =============================================================================
# Choisir le backend de sauvegarde : "snowflake" ou "csv_folder"
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

from src.builders import build_quota_share, build_excess_of_loss, build_program
from snowflake_utils import save_program

print("Création du programme Aviation Complex Multi-Currency...")
print(f"Backend de sauvegarde: {BACKEND}")

LAYER_VALUES_COMMON = {
    "XOL_1": (65_000_000, 35_000_000),
    "XOL_2": (50_000_000, 65_000_000),
    "XOL_3": (100_000_000, 115_000_000),
    "XOL_4": (100_000_000, 215_000_000),
    "XOL_5": (100_000_000, 315_000_000),
    "XOL_6": (150_000_000, 415_000_000),
}

LAYER_VALUES_GBP = {
    "XOL_1": (43_333_333, 23_333_333),
    "XOL_2": (33_333_333, 43_333_333),
    "XOL_3": (66_666_666, 76_666_666),
    "XOL_4": (66_666_666, 143_333_333),
    "XOL_5": (66_666_666, 210_000_000),
    "XOL_6": (100_000_000, 276_666_666),
}

CURRENCIES_COMMON = ["USD", "CAD", "EUR", "AUD"]
CURRENCIES_GBP = ["GBP"]

CESSION_RATE_QS = 0.25  # 25% cédé
REINSURER_SHARE_QS = 0.0165  # 1.65%

# Construction du Quota Share
qs = build_quota_share(
    name="QS_1",
    cession_pct=CESSION_RATE_QS,
    signed_share=REINSURER_SHARE_QS,
    special_conditions=[
        {
            "currency_cd": CURRENCIES_COMMON + CURRENCIES_GBP,  # Liste de toutes les devises
            "includes_hull": True,
            "includes_liability": True,
        }
    ],
    claim_basis="risk_attaching",
    inception_date="2024-01-01",
    expiry_date="2025-01-01",
)

# Construction des layers XOL
xol_layers = []
for i, (layer_name, (limit_common, priority_common)) in enumerate(
    LAYER_VALUES_COMMON.items(), 1
):
    limit_gbp, priority_gbp = LAYER_VALUES_GBP[layer_name]

    special_conditions = []

    # Condition pour USD, CAD, EUR, AUD (valeurs communes)
    special_conditions.append(
        {
            "currency_cd": CURRENCIES_COMMON,  # Liste de devises
            "includes_hull": True,
            "includes_liability": True,
        }
    )

    # Condition pour GBP (avec valeurs spécifiques)
    special_conditions.append(
        {
            "currency_cd": CURRENCIES_GBP,  # Liste de devises
            "ATTACHMENT_POINT_100": priority_gbp,  # Valeur spécifique pour GBP
            "LIMIT_100": limit_gbp,                # Valeur spécifique pour GBP
            "includes_hull": True,
            "includes_liability": True,
        }
    )

    xol = build_excess_of_loss(
        name=layer_name,
        attachment=priority_common,  # Valeur par défaut pour les devises communes
        limit=limit_common,          # Valeur par défaut pour les devises communes
        signed_share=0.05,           # 5% signed share pour les excess of loss
        special_conditions=special_conditions,
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
        predecessor_title="QS_1",
    )
    xol_layers.append(xol)

# Construction du programme avec timestamp unique
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
program_name = f"AVIATION_AXA_XL_2024_{timestamp}"

program = build_program(
    name=program_name,
    structures=[qs] + xol_layers,
    underwriting_department="aviation",
)

# =============================================================================
# SAUVEGARDE
# =============================================================================

if __name__ == "__main__":
    # Vérification de la création du programme avec describe
    print("\n" + "=" * 80)
    print("VÉRIFICATION DE LA CRÉATION DU PROGRAMME")
    print("=" * 80)
    
    print(f"✓ Programme créé en mémoire: {program.name}")
    print(f"✓ Nombre de structures: {len(program.structures)}")
    print(f"✓ Département: {program.underwriting_department}")
    print(f"✓ Dimensions de matching: {len(program.dimension_columns)}")
    
    # Sauvegarde avec l'utilitaire partagé
    try:
        output_path = save_program(program, BACKEND, program_name)
        print(f"✓ Programme sauvegardé avec succès: {output_path}")
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        print("Le programme a été construit correctement mais la sauvegarde a échoué.")

# =============================================================================
# AFFICHAGE
# =============================================================================

print("\n" + "=" * 80)
print("PROGRAMME AVIATION AXA XL 2024")
print("=" * 80)

# Utilisation de l'API simple de describe()
program.describe()

print(f"\n✓ Le programme Aviation AXA XL 2024 est prêt et sauvegardé en {BACKEND} !")
