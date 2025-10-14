"""
Création du programme Aviation Old Republic 2024

Programme risk attaching avec 3 structures excess of loss pour United States et Canada:
1. XOL_1: Priorité 3M, Limite 8.75M
2. XOL_2: Priorité 11.75M, Limite 10M
3. XOL_3: Priorité 21.75M, Limite 23.25M
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from tests.builders import build_excess_of_loss, build_program
from excel_utils import program_to_excel

print("Création du programme Aviation Old Republic 2024...")

REINSURER_SHARE_VALUES = {
    "XOL_1": 0.1,
    "XOL_2": 0.1,
    "XOL_3": 0.0979,
}

COUNTRIES = ["United States", "Canada"]

xol_1 = build_excess_of_loss(
    name="XOL_1",
    sections_config=[
        {
            "attachment": 3_000_000,
            "limit": 8_750_000,
            "signed_share": REINSURER_SHARE_VALUES["XOL_1"],
            "country_cd": country,
            "includes_hull": True,
            "includes_liability": True,
        }
        for country in COUNTRIES
    ],
    claim_basis="risk_attaching"
)

xol_2 = build_excess_of_loss(
    name="XOL_2",
    sections_config=[
        {
            "attachment": 11_750_000,
            "limit": 10_000_000,
            "signed_share": REINSURER_SHARE_VALUES["XOL_2"],
            "country_cd": country,
            "includes_hull": True,
            "includes_liability": True,
        }
        for country in COUNTRIES
    ],
    claim_basis="risk_attaching"
)

xol_3 = build_excess_of_loss(
    name="XOL_3",
    sections_config=[
        {
            "attachment": 21_750_000,
            "limit": 23_250_000,
            "signed_share": REINSURER_SHARE_VALUES["XOL_3"],
            "country_cd": country,
            "includes_hull": True,
            "includes_liability": True,
        }
        for country in COUNTRIES
    ],
    claim_basis="risk_attaching"
)

program = build_program(
    name="AVIATION_OLD_REPUBLIC_2024",
    structures=[xol_1, xol_2, xol_3],
    underwriting_department="aviation"
)

output_file = "../programs/aviation_old_republic_2024.xlsx"

program_to_excel(program, output_file)

print(f"✓ Programme créé: {output_file}")

print("\n" + "=" * 80)
print("PROGRAMME AVIATION OLD REPUBLIC 2024")
print("=" * 80)
program.describe()
