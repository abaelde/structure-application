"""
Création du programme New Line

Programme casualty avec 3 layers Excess of Loss:
- Layer 1: 2 sous-conditions (a et b) avec des lignes de business spécifiques, multi-devises
- Layer 2: Multi-devises
- Layer 3: Multi-devises

Line of Business utilisées (à affiner selon référentiel):
- Sub-condition a: Financial Institutions, Commercial Crime, Professional Indemnity/E&O, 
                 Commercial D&O, Medical Malpractice, Transactional Liability
- Sub-condition b: Employers' Liability, General Liability
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from tests.builders import build_excess_of_loss, build_program
from excel_utils import program_to_excel

print("Création du programme New Line...")

CURRENCIES = ["GBP", "USD", "EUR", "CAD", "AUD"]
REINSURER_SHARE = 0.10

LAYER_1_SUB_A = {
    "GBP": (3_000_000, 1_000_000),
    "USD": (4_500_000, 1_500_000),
    "EUR": (4_500_000, 1_500_000),
    "CAD": (5_250_000, 1_750_000),
    "AUD": (8_000_000, 2_000_000),
}

LAYER_1_SUB_B = {
    "GBP": (2_500_000, 1_500_000),
    "USD": (3_750_000, 2_250_000),
    "EUR": (3_750_000, 2_250_000),
    "CAD": (4_375_000, 2_625_000),
    "AUD": (7_000_000, 3_000_000),
}

LAYER_2_VALUES = {
    "GBP": (6_000_000, 4_000_000),
    "USD": (9_000_000, 6_000_000),
    "EUR": (9_000_000, 6_000_000),
    "CAD": (10_500_000, 7_000_000),
    "AUD": (15_000_000, 10_000_000),
}

LAYER_3_VALUES = {
    "GBP": (5_000_000, 10_000_000),
    "USD": (10_000_000, 15_000_000),
    "EUR": (10_000_000, 15_000_000),
    "CAD": (8_750_000, 17_500_000),
    "AUD": (5_000_000, 25_000_000),
}

LOB_SUB_A = [
    "Financial Institutions",
    "Commercial Crime",
    "Professional Indemnity / Errors and Omissions",
    "Commercial Directors and Officers",
    "Medical Malpractice",
    "Transactional Liability",
]

LOB_SUB_B = [
    "Employers' Liability",
    "General Liability",
]

layer_1_conditions = []
for currency in CURRENCIES:
    limit_a, attachment_a = LAYER_1_SUB_A[currency]
    for lob in LOB_SUB_A:
        layer_1_conditions.append({
            "attachment": attachment_a,
            "limit": limit_a,
            "signed_share": REINSURER_SHARE,
            "currency_cd": currency,
            "class_of_business_1": lob,
        })

for currency in CURRENCIES:
    limit_b, attachment_b = LAYER_1_SUB_B[currency]
    for lob in LOB_SUB_B:
        layer_1_conditions.append({
            "attachment": attachment_b,
            "limit": limit_b,
            "signed_share": REINSURER_SHARE,
            "currency_cd": currency,
            "class_of_business_1": lob,
        })

layer_1 = build_excess_of_loss(
    name="LAYER_1",
    conditions_config=layer_1_conditions,
    claim_basis="risk_attaching"
)

layer_2_conditions = []
for currency in CURRENCIES:
    limit, attachment = LAYER_2_VALUES[currency]
    layer_2_conditions.append({
        "attachment": attachment,
        "limit": limit,
        "signed_share": REINSURER_SHARE,
        "currency_cd": currency,
    })

layer_2 = build_excess_of_loss(
    name="LAYER_2",
    conditions_config=layer_2_conditions,
    claim_basis="risk_attaching"
)

layer_3_conditions = []
for currency in CURRENCIES:
    limit, attachment = LAYER_3_VALUES[currency]
    layer_3_conditions.append({
        "attachment": attachment,
        "limit": limit,
        "signed_share": REINSURER_SHARE,
        "currency_cd": currency,
    })

layer_3 = build_excess_of_loss(
    name="LAYER_3",
    conditions_config=layer_3_conditions,
    claim_basis="risk_attaching"
)

program = build_program(
    name="NEW_LINE_2024",
    structures=[layer_1, layer_2, layer_3],
    underwriting_department="casualty"
)

output_dir = "../programs"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "new_line_2024.xlsx")

program_to_excel(program, output_file)

print(f"✓ Programme créé: {output_file}")

print("\n" + "=" * 80)
print("PROGRAMME NEW LINE 2024")
print("=" * 80)

program.describe()

print("\n" + "=" * 80)
print("RÉSUMÉ DU PROGRAMME")
print("=" * 80)

print(f"""
Programme: New Line 2024
Type: Casualty - Multi-currency XOL Layers
Devises: GBP, USD, EUR, CAD, AUD

LAYER 1 - conditions par Line of Business et Devise:
  Sub-condition a) - Financial Institutions, Commercial Crime, Professional Indemnity/E&O,
                   Commercial D&O, Medical Malpractice, Transactional Liability:
    GBP: 3,000,000 xs 1,000,000
    USD: 4,500,000 xs 1,500,000
    EUR: 4,500,000 xs 1,500,000
    CAD: 5,250,000 xs 1,750,000
    AUD: 8,000,000 xs 2,000,000
    
  Sub-condition b) - Employers' Liability, General Liability:
    GBP: 2,500,000 xs 1,500,000
    USD: 3,750,000 xs 2,250,000
    EUR: 3,750,000 xs 2,250,000
    CAD: 4,375,000 xs 2,625,000
    AUD: 7,000,000 xs 3,000,000
    
  Total conditions Layer 1: {len(layer_1_conditions)} ({len(LOB_SUB_A)} LOB × 5 devises + {len(LOB_SUB_B)} LOB × 5 devises)

LAYER 2 - conditions par Devise uniquement:
    GBP: 6,000,000 xs 4,000,000
    USD: 9,000,000 xs 6,000,000
    EUR: 9,000,000 xs 6,000,000
    CAD: 10,500,000 xs 7,000,000
    AUD: 15,000,000 xs 10,000,000
    
  Total conditions Layer 2: {len(layer_2_conditions)} (5 devises)

LAYER 3 - conditions par Devise uniquement:
    GBP: 5,000,000 xs 10,000,000
    USD: 10,000,000 xs 15,000,000
    EUR: 10,000,000 xs 15,000,000
    CAD: 8,750,000 xs 17,500,000
    AUD: 5,000,000 xs 25,000,000
    
  Total conditions Layer 3: {len(layer_3_conditions)} (5 devises)

TOTAL conditions: {len(layer_1_conditions) + len(layer_2_conditions) + len(layer_3_conditions)}

Reinsurer share: {REINSURER_SHARE:.1%} pour toutes les conditions
""")

print("✓ Le programme New Line 2024 est prêt !")
print("\nNotes importantes:")
print("- Les lignes de business sont prises telles quelles en attendant le référentiel")
print("- Layer 1 utilise BUSCL_CLASS_OF_BUSINESS_1 pour distinguer les sous-conditions")
print("- Toutes les structures sont des entry points (pas d'inuring)")
print(f"- Total: 3 structures, {len(layer_1_conditions) + len(layer_2_conditions) + len(layer_3_conditions)} conditions")

