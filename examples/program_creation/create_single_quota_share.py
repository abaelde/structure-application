"""
Création d'un programme simple avec quota share

Programme: Single Quota share
- Un seul quota share de 30% appliqué à toutes les polices
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from tests.builders import build_quota_share, build_program
from src.managers import ProgramManager

print("Création du programme Single Quota share...")

qs = build_quota_share(
    name="QS_30",
    conditions_config=[
        {
            "cession_pct": 0.30,
        }
    ],
)

program = build_program(
    name="SINGLE_QUOTA_SHARE_2024", structures=[qs], underwriting_department="test"
)

output_dir = "../programs"
os.makedirs(output_dir, exist_ok=True)
output_file = "../programs/single_quota_share.xlsx"

manager = ProgramManager(backend="excel")
manager.save(program, output_file)

print("✓ Programme Single Quota share créé: examples/programs/single_quota_share.xlsx")

print("\n" + "=" * 80)
print("PROGRAMME SINGLE QUOTA SHARE")
print("=" * 80)
program.describe()
