"""
Création du programme Casualty AIG 2024

Programme casualty avec 1 structure Quota Share avec 2 conditions:
1. condition générale: Quota Share 100% avec limite de 25M
2. condition cyber: Quota Share 100% avec limite de 10M sur le risque cyber

Programme risk attaching avec réassureur share à 10% (à déterminer)
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from tests.builders import build_quota_share, build_program
from excel_utils import program_to_excel

print("Création du programme Casualty AIG 2024...")

CESSION_RATE = 1.0
REINSURER_SHARE = 0.10

qs = build_quota_share(
    name="QS_1",
    conditions_config=[
        {
            "cession_pct": CESSION_RATE,
            "limit": 25_000_000,
            "signed_share": REINSURER_SHARE,
        },
        {
            "cession_pct": CESSION_RATE,
            "limit": 10_000_000,
            "signed_share": REINSURER_SHARE,
            "pol_risk_name_ced": "cyber",
            "exclude_cd": "INCLUDE",
        },
    ],
    claim_basis="risk_attaching"
)

program = build_program(
    name="CASUALTY_AIG_2024",
    structures=[qs],
    underwriting_department="casualty"
)

output_dir = "../programs"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "casualty_aig_2024.xlsx")

program_to_excel(program, output_file)

print(f"✓ Programme créé: {output_file}")

print("\n" + "=" * 80)
print("PROGRAMME CASUALTY AIG 2024")
print("=" * 80)

program.describe()