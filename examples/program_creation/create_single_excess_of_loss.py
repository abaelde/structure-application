"""
Création d'un programme simple avec excess of loss

Programme: Single Excess of Loss
- Un seul excess of loss de 1M xs 0.5M appliqué à toutes les polices
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import pandas as pd
import numpy as np

# =============================================================================
# PROGRAMME: SINGLE EXCESS OF LOSS
# =============================================================================

print("Création du programme Single Excess of Loss...")

program_data = {
    "program_name": ["SINGLE_EXCESS_OF_LOSS_2024"]
}

structures_data = {
    "structure_name": ["XOL_0.5M_1M"],
    "order": [1],
    "product_type": ["excess_of_loss"]
}

sections_data = {
    "structure_name": ["XOL_0.5M_1M"],
    "cession_rate": [np.nan],
    "priority": [0.5],  # 0.5 million
    "limit": [1.0],     # 1.0 million
    "country": [np.nan],
    "region": [np.nan],
    "product_type_1": [np.nan],
    "product_type_2": [np.nan],
    "product_type_3": [np.nan],
    "currency": [np.nan],
    "line_of_business": [np.nan],
    "industry": [np.nan],
    "sic_code": [np.nan],
    "include": [np.nan]
}

program_df = pd.DataFrame(program_data)
structures_df = pd.DataFrame(structures_data)
sections_df = pd.DataFrame(sections_data)

# Créer le dossier programs s'il n'existe pas
output_dir = "../programs"
os.makedirs(output_dir, exist_ok=True)

with pd.ExcelWriter("../programs/single_excess_of_loss.xlsx", engine="openpyxl") as writer:
    program_df.to_excel(writer, sheet_name="program", index=False)
    structures_df.to_excel(writer, sheet_name="structures", index=False)
    sections_df.to_excel(writer, sheet_name="sections", index=False)

print("✓ Programme Single Excess of Loss créé: examples/programs/single_excess_of_loss.xlsx")
# =============================================================================
# AFFICHAGE DES DÉTAILS
# =============================================================================

print("\n" + "=" * 80)
print("PROGRAMME SINGLE EXCESS OF LOSS")
print("=" * 80)

print("\nProgram:")
print(program_df)

print("\nStructures:")
print(structures_df)

print("\nSections:")
print(sections_df)

# =============================================================================
# EXPLICATION DU COMPORTEMENT
# =============================================================================

print("\n" + "=" * 80)
print("COMPORTEMENT DU PROGRAMME")
print("=" * 80)

print("""
Exemple avec une police de 1M d'exposition:

PROGRAMME SINGLE EXCESS OF LOSS:
1. XOL_0.5M_1M s'applique sur 1M → 0.5M cédé (1M - 0.5M = 0.5M, limité à 1M)
   Total cédé: 0.5M
   Total retenu: 0.5M

Exemple avec une police de 2M d'exposition:
1. XOL_0.5M_1M s'applique sur 2M → 1M cédé (2M - 0.5M = 1.5M, limité à 1M)
   Total cédé: 1M
   Total retenu: 1M

PRINCIPE:
- Un seul excess of loss de 1M xs 0.5M appliqué à toutes les polices
- Pas de conditions géographiques ou autres
- Simple et efficace pour tester la logique XOL de base
""")

print("\n✓ Le programme Single Excess of Loss est prêt !")

