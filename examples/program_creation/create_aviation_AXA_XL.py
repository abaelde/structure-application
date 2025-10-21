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
    conditions_config=[
        {
            "cession_pct": CESSION_RATE_QS,
            "limit": 575_000_000,
            "signed_share": REINSURER_SHARE_QS,
            "currency_cd": currency,
            "includes_hull": True,
            "includes_liability": True,
        }
        for currency in CURRENCIES_COMMON + CURRENCIES_GBP
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

    conditions_config = []

    # Conditions pour USD, CAD, EUR, AUD
    for currency in CURRENCIES_COMMON:
        conditions_config.append(
            {
                "limit": limit_common,
                "attachment": priority_common,
                "currency_cd": currency,
                "includes_hull": True,
                "includes_liability": True,
            }
        )

    # Conditions pour GBP
    for currency in CURRENCIES_GBP:
        conditions_config.append(
            {
                "limit": limit_gbp,
                "attachment": priority_gbp,
                "currency_cd": currency,
                "includes_hull": True,
                "includes_liability": True,
            }
        )

    xol = build_excess_of_loss(
        name=layer_name,
        conditions_config=conditions_config,
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
        predecessor_title="QS_1",
        signed_share=0.05,  # 5% signed share pour les excess of loss
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
    # Sauvegarde avec l'utilitaire partagé
    output_path = save_program(program, BACKEND, program_name)

# =============================================================================
# AFFICHAGE
# =============================================================================

print("\n" + "=" * 80)
print("PROGRAMME AVIATION AXA XL 2024")
print("=" * 80)

program.describe()

print("\n" + "=" * 80)
print("RÉSUMÉ DU PROGRAMME")
print("=" * 80)

print(
    f"""
Programme: Aviation AXA XL 2024
Devises: USD, CAD, EUR, AUD, GBP
Backend: {BACKEND}

Structures (empilées selon l'ordre):
"""
)

print("0. QS_1:")
print(
    f"   - Toutes devises: Quota Share {CESSION_RATE_QS:.1%} cédé avec limite de 575M, {REINSURER_SHARE_QS:.2%} reinsurer share"
)

for i, layer in enumerate(["XOL_1", "XOL_2", "XOL_3", "XOL_4", "XOL_5", "XOL_6"], 1):
    limit_common, priority_common = LAYER_VALUES_COMMON[layer]
    limit_gbp, priority_gbp = LAYER_VALUES_GBP[layer]
    print(f"{i}. {layer}:")
    print(f"   - USD/CAD/EUR/AUD: {limit_common:,.0f} xs {priority_common:,.0f}")
    print(f"   - GBP: {limit_gbp:,.0f} xs {priority_gbp:,.0f}")

print(f"\n✓ Le programme Aviation AXA XL 2024 est prêt et sauvegardé en {BACKEND} !")
