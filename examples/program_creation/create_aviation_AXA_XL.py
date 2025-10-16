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

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from tests.builders import build_quota_share, build_excess_of_loss, build_program
from src.managers import ProgramManager

print("Création du programme Aviation Complex Multi-Currency...")

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

CESSION_RATE_QS = 0.25
REINSURER_SHARE_QS = 0.0165
REINSURER_SHARE_XOL = 0.05

COMMON_CURRENCIES = ["USD", "CAD", "EUR", "AUD"]
ALL_CURRENCIES = COMMON_CURRENCIES + ["GBP"]

qs_1 = build_quota_share(
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
        for currency in ALL_CURRENCIES
    ],
    claim_basis="risk_attaching"
)

def create_xol_layer(layer_name: str) -> object:
    conditions = []
    
    for currency in COMMON_CURRENCIES:
        limit, attachment = LAYER_VALUES_COMMON[layer_name]
        conditions.append({
            "attachment": attachment,
            "limit": limit,
            "signed_share": REINSURER_SHARE_XOL,
            "currency_cd": currency,
            "includes_hull": True,
            "includes_liability": True,
        })
    
    limit_gbp, attachment_gbp = LAYER_VALUES_GBP[layer_name]
    conditions.append({
        "attachment": attachment_gbp,
        "limit": limit_gbp,
        "signed_share": REINSURER_SHARE_XOL,
        "currency_cd": "GBP",
        "includes_hull": True,
        "includes_liability": True,
    })
    
    return build_excess_of_loss(
        name=layer_name,
        conditions_config=conditions,
        predecessor_title="QS_1",
        claim_basis="risk_attaching"
    )

xol_1 = create_xol_layer("XOL_1")
xol_2 = create_xol_layer("XOL_2")
xol_3 = create_xol_layer("XOL_3")
xol_4 = create_xol_layer("XOL_4")
xol_5 = create_xol_layer("XOL_5")
xol_6 = create_xol_layer("XOL_6")

program = build_program(
    name="AVIATION_AXA_XL_2024",
    structures=[qs_1, xol_1, xol_2, xol_3, xol_4, xol_5, xol_6],
    underwriting_department="aviation"
)

output_dir = "../programs"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "aviation_axa_xl_2024.xlsx")

manager = ProgramManager(backend="excel")
manager.save(program, output_file)

print(f"✓ Programme créé: {output_file}")

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

Structures (empilées selon l'ordre):
"""
)

print("0. QS_1 (contract_order=0):")
print(
    f"   - Toutes devises: Quota Share {CESSION_RATE_QS:.1%} cédé avec limite de 575M, {REINSURER_SHARE_QS:.2%} reinsurer share"
)

for i, layer in enumerate(["XOL_1", "XOL_2", "XOL_3", "XOL_4", "XOL_5", "XOL_6"], 1):
    limit_common, priority_common = LAYER_VALUES_COMMON[layer]
    limit_gbp, priority_gbp = LAYER_VALUES_GBP[layer]
    print(f"{i}. {layer} (contract_order={i}):")
    print(f"   - USD/CAD/EUR/AUD: {limit_common:,.0f} xs {priority_common:,.0f}")
    print(f"   - GBP: {limit_gbp:,.0f} xs {priority_gbp:,.0f}")


print("\n✓ Le programme Aviation AXA XL 2024 est prêt !")
