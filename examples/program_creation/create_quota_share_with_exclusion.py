"""
Création d'un programme Quota Share avec exclusions

Programme: Quota Share with Exclusions Test
- 2 conditions d'exclusion (Iran, Russia)
- 1 condition normale: 25% cession sur tout le reste
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from tests.builders import build_quota_share, build_program
from src.managers import ProgramManager

print("Création du programme Quota Share with Exclusions...")

# Créer un quota share avec exclusions et condition normale
qs = build_quota_share(
    name="QS Aviation 25%",
    conditions_config=[
        {
            "exclude_cd": "exclude",
            "country_cd": "Iran",
            "cession_pct": None,
        },
        {
            "exclude_cd": "exclude",
            "country_cd": "Russia",
            "cession_pct": None,
        },
        {
            "exclude_cd": None,
            "country_cd": None,
            "cession_pct": 0.25,
            "signed_share": 1.0,
        },
    ],
    claim_basis="risk_attaching",
    inception_date="2024-01-01",
    expiry_date="2024-12-31",
)

program = build_program(
    name="Quota Share with Exclusions Test",
    structures=[qs],
    underwriting_department="aviation",
)

output_dir = "../programs"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "quota_share_with_exclusion.xlsx")

manager = ProgramManager(backend="excel")
manager.save(program, output_file)

print(f"✓ Programme créé: {output_file}")
print("\nStructure du programme:")
print("  - 1 structure: QS Aviation 25%")
print("  - 3 conditions d'exclusion:")
print("    - Iran (pays)")
print("    - Russia (pays)")
print("  - 1 condition normale: 25% cession sur tout le reste")
