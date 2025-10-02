"""
Création du programme Aviation Old Republic 2024

Programme risk attaching avec 3 structures excess of loss pour United States et Canada:
1. XOL_1: Priorité 3M, Limite 8.75M
2. XOL_2: Priorité 11.75M, Limite 10M  
3. XOL_3: Priorité 21.75M, Limite 23.25M
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
import numpy as np

print("Création du programme Aviation Old Republic 2024...")

# =============================================================================
# DÉFINITION DU PROGRAMME
# =============================================================================

program_data = {
    "program_name": ["AVIATION_OLD_REPUBLIC_2024"],
    "mode": ["sequential"]  # Risk attaching = mode séquentiel
}

# =============================================================================
# DÉFINITION DES STRUCTURES
# =============================================================================

structures_data = {
    "structure_name": ["XOL_1", "XOL_2", "XOL_3"],
    "order": [1, 2, 3],
    "product_type": ["excess_of_loss", "excess_of_loss", "excess_of_loss"]
}

# =============================================================================
# DÉFINITION DES SECTIONS
# =============================================================================

sections_data = {
    "structure_name": ["XOL_1", "XOL_2", "XOL_3"],
    "session_rate": [np.nan, np.nan, np.nan],  # XOL n'utilise pas session_rate
    "priority": [3000000, 11750000, 21750000],  # Priorités en dollars
    "limit": [8750000, 10000000, 23250000],     # Limites en dollars
    # Conditions géographiques
    "country": ["United States", "United States", "United States"],
    "region": [np.nan, np.nan, np.nan],
    "product_type_1": [np.nan, np.nan, np.nan],
    "product_type_2": [np.nan, np.nan, np.nan],
    "product_type_3": [np.nan, np.nan, np.nan],
    "currency": [np.nan, np.nan, np.nan],
    "line_of_business": [np.nan, np.nan, np.nan],
    "industry": [np.nan, np.nan, np.nan],
    "sic_code": [np.nan, np.nan, np.nan],
    "include": [np.nan, np.nan, np.nan]
}

# Ajouter les sections pour le Canada
sections_canada_data = {
    "structure_name": ["XOL_1", "XOL_2", "XOL_3"],
    "session_rate": [np.nan, np.nan, np.nan],
    "priority": [3000000, 11750000, 21750000],
    "limit": [8750000, 10000000, 23250000],
    "country": ["Canada", "Canada", "Canada"],
    "region": [np.nan, np.nan, np.nan],
    "product_type_1": [np.nan, np.nan, np.nan],
    "product_type_2": [np.nan, np.nan, np.nan],
    "product_type_3": [np.nan, np.nan, np.nan],
    "currency": [np.nan, np.nan, np.nan],
    "line_of_business": [np.nan, np.nan, np.nan],
    "industry": [np.nan, np.nan, np.nan],
    "sic_code": [np.nan, np.nan, np.nan],
    "include": [np.nan, np.nan, np.nan]
}

# Combiner les sections US et Canada
sections_combined_data = {
    "structure_name": sections_data["structure_name"] + sections_canada_data["structure_name"],
    "session_rate": sections_data["session_rate"] + sections_canada_data["session_rate"],
    "priority": sections_data["priority"] + sections_canada_data["priority"],
    "limit": sections_data["limit"] + sections_canada_data["limit"],
    "country": sections_data["country"] + sections_canada_data["country"],
    "region": sections_data["region"] + sections_canada_data["region"],
    "product_type_1": sections_data["product_type_1"] + sections_canada_data["product_type_1"],
    "product_type_2": sections_data["product_type_2"] + sections_canada_data["product_type_2"],
    "product_type_3": sections_data["product_type_3"] + sections_canada_data["product_type_3"],
    "currency": sections_data["currency"] + sections_canada_data["currency"],
    "line_of_business": sections_data["line_of_business"] + sections_canada_data["line_of_business"],
    "industry": sections_data["industry"] + sections_canada_data["industry"],
    "sic_code": sections_data["sic_code"] + sections_canada_data["sic_code"],
    "include": sections_data["include"] + sections_canada_data["include"]
}

# =============================================================================
# CRÉATION DES DATAFRAMES
# =============================================================================

program_df = pd.DataFrame(program_data)
structures_df = pd.DataFrame(structures_data)
sections_df = pd.DataFrame(sections_combined_data)

# =============================================================================
# GÉNÉRATION DU FICHIER EXCEL
# =============================================================================

output_file = "examples/programs/aviation_old_republic_2024.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    program_df.to_excel(writer, sheet_name="program", index=False)
    structures_df.to_excel(writer, sheet_name="structures", index=False)
    sections_df.to_excel(writer, sheet_name="sections", index=False)

print(f"✓ Programme créé: {output_file}")

# =============================================================================
# AFFICHAGE DES DÉTAILS
# =============================================================================

print("\n" + "=" * 80)
print("PROGRAMME AVIATION OLD REPUBLIC 2024")
print("=" * 80)

print("\nProgram:")
print(program_df)

print("\nStructures:")
print(structures_df)

print("\nSections:")
print(sections_df)

# =============================================================================
# RÉSUMÉ DU PROGRAMME
# =============================================================================

print("\n" + "=" * 80)
print("RÉSUMÉ DU PROGRAMME")
print("=" * 80)

print("""
Programme: Aviation Old Republic 2024
Mode: Sequential (Risk Attaching)
Géographie: United States et Canada

Structures XOL (en mode séquentiel):
1. XOL_1: 8.75M xs 3M (pour US et Canada)
2. XOL_2: 10M xs 11.75M (pour US et Canada)  
3. XOL_3: 23.25M xs 21.75M (pour US et Canada)

Comportement séquentiel:
- XOL_1 s'applique d'abord sur l'exposition totale
- XOL_2 s'applique sur l'exposition restante après XOL_1
- XOL_3 s'applique sur l'exposition restante après XOL_2

Exemple avec une police de 50M d'exposition:
1. XOL_1: 8.75M cédé (50M - 3M = 47M, limité à 8.75M)
2. XOL_2: 10M cédé (47M - 8.75M = 38.25M restant, 38.25M - 11.75M = 26.5M, limité à 10M)
3. XOL_3: 23.25M cédé (26.5M - 10M = 16.5M restant, 16.5M - 21.75M = négatif, donc 0 cédé)
   Total cédé: 18.75M (8.75M + 10M + 0M)
   Total retenu: 31.25M
""")

print("\n✓ Le programme Aviation Old Republic 2024 est prêt !")
