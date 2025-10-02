"""
Création de programmes simples avec la nouvelle logique basée sur l'ordre

Programme 1: QS_30% puis XOL_500K_1M
- Le quota share s'applique d'abord sur l'exposition totale (order=1)
- L'excess of loss s'applique ensuite sur l'exposition restante (order=2)

Programme 2: Même configuration (pour compatibilité)
- Maintenant les deux programmes donnent le même résultat car la logique est basée sur l'ordre
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
import numpy as np

# =============================================================================
# PROGRAMME 1: SIMPLE
# =============================================================================

print("Création du programme SIMPLE...")

program_sequential_data = {
    "program_name": ["SIMPLE_SEQUENTIAL_2024"]
}

structures_sequential_data = {
    "structure_name": ["QS_30", "XOL_0.5M_1M"],
    "order": [1, 2],
    "product_type": ["quote_share", "excess_of_loss"]
}

sections_sequential_data = {
    "structure_name": ["QS_30", "XOL_0.5M_1M"],
    "session_rate": [0.30, np.nan],
    "priority": [np.nan, 0.5],  # 0.5 million
    "limit": [np.nan, 1.0],     # 1.0 million
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
# PROGRAMME 2: SIMPLE (COMPATIBILITÉ)
# =============================================================================

print("\nCréation du programme SIMPLE (compatibilité)...")

program_parallel_data = {
    "program_name": ["SIMPLE_PARALLEL_2024"]
}

structures_parallel_data = {
    "structure_name": ["QS_30", "XOL_0.5M_1M"],
    "order": [1, 2],
    "product_type": ["quote_share", "excess_of_loss"]
}

sections_parallel_data = {
    "structure_name": ["QS_30", "XOL_0.5M_1M"],
    "session_rate": [0.30, np.nan],
    "priority": [np.nan, 0.5],  # 0.5 million
    "limit": [np.nan, 1.0],     # 1.0 million
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
print("NOUVELLE LOGIQUE BASÉE SUR L'ORDRE")
print("=" * 80)

print("""
Exemple avec une police de 1M d'exposition:

NOUVELLE LOGIQUE (ORDRE-BASED):
1. QS_30% (order=1) s'applique sur 1M → 0.3M cédé, 0.7M restant
2. XOL_0.5M_1M (order=2) s'applique sur 0.7M restant → 0.2M cédé (0.7M - 0.5M)
   Total cédé: 0.5M (0.3M + 0.2M)
   Total retenu: 0.5M

PRINCIPE:
- Quote Share (order=1): Réduit l'exposition restante
- Excess of Loss (order=2): S'applique sur l'exposition restante après les Quote Share
- Les deux programmes donnent maintenant le même résultat car la logique est basée sur l'ordre
""")

print("\n✓ Les deux programmes sont prêts pour les tests !")
