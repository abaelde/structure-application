"""
Création de deux programmes simples pour comparer les modes séquentiel et parallèle

Programme 1 (SÉQUENTIEL): QS_30% puis XOL_500K_1M
- Le quota share s'applique d'abord sur l'exposition totale
- L'excess of loss s'applique ensuite sur l'exposition restante

Programme 2 (PARALLÈLE): QS_30% et XOL_500K_1M simultanés
- Les deux structures s'appliquent sur l'exposition originale
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
import numpy as np

# =============================================================================
# PROGRAMME 1: SÉQUENTIEL
# =============================================================================

print("Création du programme SÉQUENTIEL...")

program_sequential_data = {
    "program_name": ["SIMPLE_SEQUENTIAL_2024"],
    "mode": ["sequential"]
}

structures_sequential_data = {
    "structure_name": ["QS_30", "XOL_500K_1M"],
    "order": [1, 2],
    "product_type": ["quote_share", "excess_of_loss"]
}

sections_sequential_data = {
    "structure_name": ["QS_30", "XOL_500K_1M"],
    "session_rate": [0.30, np.nan],
    "priority": [np.nan, 500000],
    "limit": [np.nan, 1000000],
    "country": [np.nan, np.nan],
    "region": [np.nan, np.nan],
    "product_type_1": [np.nan, np.nan],
    "product_type_2": [np.nan, np.nan],
    "product_type_3": [np.nan, np.nan],
    "currency": [np.nan, np.nan],
    "line_of_business": [np.nan, np.nan],
    "industry": [np.nan, np.nan],
    "sic_code": [np.nan, np.nan],
    "include": [np.nan, np.nan]
}

program_sequential_df = pd.DataFrame(program_sequential_data)
structures_sequential_df = pd.DataFrame(structures_sequential_data)
sections_sequential_df = pd.DataFrame(sections_sequential_data)

with pd.ExcelWriter("examples/programs/program_simple_sequential.xlsx", engine="openpyxl") as writer:
    program_sequential_df.to_excel(writer, sheet_name="program", index=False)
    structures_sequential_df.to_excel(writer, sheet_name="structures", index=False)
    sections_sequential_df.to_excel(writer, sheet_name="sections", index=False)

print("✓ Programme séquentiel créé: examples/programs/program_simple_sequential.xlsx")

# =============================================================================
# PROGRAMME 2: PARALLÈLE
# =============================================================================

print("\nCréation du programme PARALLÈLE...")

program_parallel_data = {
    "program_name": ["SIMPLE_PARALLEL_2024"],
    "mode": ["parallel"]
}

structures_parallel_data = {
    "structure_name": ["QS_30", "XOL_500K_1M"],
    "order": [1, 2],
    "product_type": ["quote_share", "excess_of_loss"]
}

sections_parallel_data = {
    "structure_name": ["QS_30", "XOL_500K_1M"],
    "session_rate": [0.30, np.nan],
    "priority": [np.nan, 500000],
    "limit": [np.nan, 1000000],
    "country": [np.nan, np.nan],
    "region": [np.nan, np.nan],
    "product_type_1": [np.nan, np.nan],
    "product_type_2": [np.nan, np.nan],
    "product_type_3": [np.nan, np.nan],
    "currency": [np.nan, np.nan],
    "line_of_business": [np.nan, np.nan],
    "industry": [np.nan, np.nan],
    "sic_code": [np.nan, np.nan],
    "include": [np.nan, np.nan]
}

program_parallel_df = pd.DataFrame(program_parallel_data)
structures_parallel_df = pd.DataFrame(structures_parallel_data)
sections_parallel_df = pd.DataFrame(sections_parallel_data)

with pd.ExcelWriter("examples/programs/program_simple_parallel.xlsx", engine="openpyxl") as writer:
    program_parallel_df.to_excel(writer, sheet_name="program", index=False)
    structures_parallel_df.to_excel(writer, sheet_name="structures", index=False)
    sections_parallel_df.to_excel(writer, sheet_name="sections", index=False)

print("✓ Programme parallèle créé: examples/programs/program_simple_parallel.xlsx")

# =============================================================================
# AFFICHAGE DES DÉTAILS
# =============================================================================

print("\n" + "=" * 80)
print("PROGRAMME SÉQUENTIEL")
print("=" * 80)

print("\nProgram:")
print(program_sequential_df)

print("\nStructures:")
print(structures_sequential_df)

print("\nSections:")
print(sections_sequential_df)

print("\n" + "=" * 80)
print("PROGRAMME PARALLÈLE")
print("=" * 80)

print("\nProgram:")
print(program_parallel_df)

print("\nStructures:")
print(structures_parallel_df)

print("\nSections:")
print(sections_parallel_df)

# =============================================================================
# COMPARAISON DES COMPORTEMENTS
# =============================================================================

print("\n" + "=" * 80)
print("COMPARAISON DES COMPORTEMENTS")
print("=" * 80)

print("""
Exemple avec une police de 1,000,000 d'exposition:

MODE SÉQUENTIEL:
1. QS_30% s'applique sur 1,000,000 → 300,000 cédé, 700,000 restant
2. XOL_500K_1M s'applique sur 700,000 restant → 200,000 cédé (700K - 500K)
   Total cédé: 500,000 (300K + 200K)
   Total retenu: 500,000

MODE PARALLÈLE:
1. QS_30% s'applique sur 1,000,000 → 300,000 cédé
2. XOL_500K_1M s'applique sur 1,000,000 → 500,000 cédé (1M - 500K)
   Total cédé: 800,000 (300K + 500K)
   Total retenu: 200,000

DIFFÉRENCE CLÉE:
- Séquentiel: L'XOL s'applique sur l'exposition restante après le QS
- Parallèle: L'XOL s'applique sur l'exposition originale
""")

print("\n✓ Les deux programmes sont prêts pour les tests !")
