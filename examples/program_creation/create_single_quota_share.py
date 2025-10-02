"""
Création d'un programme simple avec quota share

Programme: Single Quota share
- Un seul quota share de 30% appliqué à toutes les polices
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import pandas as pd
import numpy as np

# =============================================================================
# PROGRAMME: SINGLE QUOTA SHARE
# =============================================================================

print("Création du programme Single Quota share...")

program_data = {
    "program_name": ["SINGLE_QUOTA_SHARE_2024"]
}

structures_data = {
    "structure_name": ["QS_30"],
    "order": [1],
    "product_type": ["quote_share"]
}

sections_data = {
    "structure_name": ["QS_30"],
    "session_rate": [0.30],  # 30% de cession
    "priority": [np.nan],
    "limit": [np.nan],
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

with pd.ExcelWriter("../programs/single_quota_share.xlsx", engine="openpyxl") as writer:
    program_df.to_excel(writer, sheet_name="program", index=False)
    structures_df.to_excel(writer, sheet_name="structures", index=False)
    sections_df.to_excel(writer, sheet_name="sections", index=False)

print("✓ Programme Single Quota share créé: examples/programs/single_quota_share.xlsx")

# =============================================================================
# AFFICHAGE DES DÉTAILS
# =============================================================================

print("\n" + "=" * 80)
print("PROGRAMME SINGLE QUOTA SHARE")
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

PROGRAMME SINGLE QUOTA SHARE:
1. QS_30% s'applique sur 1M → 0.3M cédé, 0.7M retenu
   Total cédé: 0.3M
   Total retenu: 0.7M

PRINCIPE:
- Un seul quota share de 30% appliqué à toutes les polices
- Pas de conditions géographiques ou autres
- Simple et efficace pour tester la logique de base
""")

print("\n✓ Le programme Single Quota share est prêt !")
