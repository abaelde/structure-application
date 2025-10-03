"""
Création du programme Aviation Complex Multi-Currency

Programme aviation avec 6 layers excess of loss, chacun défini pour 5 devises:
- USD, CAD, EUR, AUD (valeurs identiques)
- GBP (valeurs spécifiques)

Structure:
- 6 layers XOL empilés (XOL_1 à XOL_6)
- Chaque layer a des sections pour USD, CAD, EUR, AUD et GBP
- Priorités et limites définies par devise
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import pandas as pd
import numpy as np

print("Création du programme Aviation Complex Multi-Currency...")

# =============================================================================
# CONFIGURATION DES VALEURS - À MODIFIER SELON VOS BESOINS
# =============================================================================

# Définir les valeurs pour chaque layer (en millions)
# Format: (priority, limit)
# Les valeurs sont identiques pour USD, CAD, EUR, AUD
LAYER_VALUES_COMMON = {
    "XOL_1": (65, 0),   
    "XOL_2": (50, 65),   
    "XOL_3": (100, 115),  
    "XOL_4": (100, 215), 
    "XOL_5": (100, 315), 
    "XOL_6": (150, 415), 
}

# Valeurs spécifiques pour GBP (en millions)
LAYER_VALUES_GBP = {
    "XOL_1": (43.333333, 23.333333),   
    "XOL_2": (33.333333, 43.333333),  
    "XOL_3": (66.666666, 76.666666),   
    "XOL_4": (66.666666, 143.333333), 
    "XOL_5": (66.666666, 210),
    "XOL_6": (100, 276.666666),
}

# Reinsurer Share Values
REINSURER_SHARE_VALUES = {
    "XOL_1": 0.05,   
    "XOL_2": 0.05,   
    "XOL_3": 0.05,   
    "XOL_4": 0.05,
    "XOL_5": 0.05,
    "XOL_6": 0.05,
}

# =============================================================================
# DÉFINITION DU PROGRAMME
# =============================================================================

program_data = {
    "program_name": ["AVIATION_AXA_XL_2024"]
}

# =============================================================================
# DÉFINITION DES STRUCTURES (6 layers XOL)
# =============================================================================

structures_data = {
    "structure_name": ["XOL_1", "XOL_2", "XOL_3", "XOL_4", "XOL_5", "XOL_6"],
    "order": [1, 2, 3, 4, 5, 6],
    "product_type": ["excess_of_loss", "excess_of_loss", "excess_of_loss", 
                    "excess_of_loss", "excess_of_loss", "excess_of_loss"],
    "claim_basis": ["risk_attaching", "risk_attaching", "risk_attaching", 
                   "risk_attaching", "risk_attaching", "risk_attaching"]
}

# =============================================================================
# DÉFINITION DES SECTIONS
# =============================================================================

# Devises communes (USD, CAD, EUR, AUD)
COMMON_CURRENCIES = ["USD", "CAD", "EUR", "AUD"]

# Initialiser les listes pour les sections
sections_data = {
    "structure_name": [],
    "session_rate": [],
    "priority": [],
    "limit": [],
    "reinsurer_share": [],
    "country": [],
    "region": [],
    "product_type_1": [],
    "product_type_2": [],
    "product_type_3": [],
    "currency": [],
    "line_of_business": [],
    "industry": [],
    "sic_code": [],
    "include": []
}

# Créer les sections pour les devises communes (USD, CAD, EUR, AUD)
for layer_name in ["XOL_1", "XOL_2", "XOL_3", "XOL_4", "XOL_5", "XOL_6"]:
    priority, limit = LAYER_VALUES_COMMON[layer_name]
    reinsurer_share = REINSURER_SHARE_VALUES[layer_name]
    
    for currency in COMMON_CURRENCIES:
        sections_data["structure_name"].append(layer_name)
        sections_data["session_rate"].append(np.nan)  # XOL n'utilise pas session_rate
        sections_data["priority"].append(priority)
        sections_data["limit"].append(limit)
        sections_data["reinsurer_share"].append(reinsurer_share)
        sections_data["country"].append(np.nan)  # Pas de restriction géographique
        sections_data["region"].append(np.nan)
        sections_data["product_type_1"].append(np.nan)
        sections_data["product_type_2"].append(np.nan)
        sections_data["product_type_3"].append(np.nan)
        sections_data["currency"].append(currency)  # Devise spécifique
        sections_data["line_of_business"].append(np.nan)
        sections_data["industry"].append(np.nan)
        sections_data["sic_code"].append(np.nan)
        sections_data["include"].append(np.nan)

# Créer les sections pour GBP (valeurs spécifiques)
for layer_name in ["XOL_1", "XOL_2", "XOL_3", "XOL_4", "XOL_5", "XOL_6"]:
    priority, limit = LAYER_VALUES_GBP[layer_name]
    reinsurer_share = REINSURER_SHARE_VALUES[layer_name]
    
    sections_data["structure_name"].append(layer_name)
    sections_data["session_rate"].append(np.nan)
    sections_data["priority"].append(priority)
    sections_data["limit"].append(limit)
    sections_data["reinsurer_share"].append(reinsurer_share)
    sections_data["country"].append(np.nan)
    sections_data["region"].append(np.nan)
    sections_data["product_type_1"].append(np.nan)
    sections_data["product_type_2"].append(np.nan)
    sections_data["product_type_3"].append(np.nan)
    sections_data["currency"].append("GBP")
    sections_data["line_of_business"].append(np.nan)
    sections_data["industry"].append(np.nan)
    sections_data["sic_code"].append(np.nan)
    sections_data["include"].append(np.nan)

# =============================================================================
# CRÉATION DES DATAFRAMES
# =============================================================================

program_df = pd.DataFrame(program_data)
structures_df = pd.DataFrame(structures_data)
sections_df = pd.DataFrame(sections_data)

# =============================================================================
# GÉNÉRATION DU FICHIER EXCEL
# =============================================================================

# Créer le dossier programs s'il n'existe pas
output_dir = "../programs"
os.makedirs(output_dir, exist_ok=True)

output_file = os.path.join(output_dir, "aviation_axa_xl_2024.xlsx")

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    program_df.to_excel(writer, sheet_name="program", index=False)
    structures_df.to_excel(writer, sheet_name="structures", index=False)
    sections_df.to_excel(writer, sheet_name="sections", index=False)

print(f"✓ Programme créé: {output_file}")

# =============================================================================
# AFFICHAGE DES DÉTAILS
# =============================================================================

print("\n" + "=" * 80)
print("PROGRAMME AVIATION AXA XL 2024")
print("=" * 80)

print("\nProgram:")
print(program_df)

print("\nStructures:")
print(structures_df)

print("\nSections (premières 10 lignes):")
print(sections_df.head(10))

print(f"\nTotal sections créées: {len(sections_df)}")
print(f"Répartition par devise:")
print(sections_df['currency'].value_counts())

# =============================================================================
# RÉSUMÉ DU PROGRAMME
# =============================================================================

print("\n" + "=" * 80)
print("RÉSUMÉ DU PROGRAMME")
print("=" * 80)

print("""
Programme: Aviation AXA XL 2024
Devises: USD, CAD, EUR, AUD (valeurs identiques) + GBP (valeurs spécifiques)

Structures XOL (empilées selon l'ordre):
""")

for i, layer in enumerate(["XOL_1", "XOL_2", "XOL_3", "XOL_4", "XOL_5", "XOL_6"], 1):
    priority_common, limit_common = LAYER_VALUES_COMMON[layer]
    priority_gbp, limit_gbp = LAYER_VALUES_GBP[layer]
    print(f"{i}. {layer} (order={i}):")
    print(f"   - USD/CAD/EUR/AUD: {limit_common}M xs {priority_common}M")
    print(f"   - GBP: {limit_gbp}M xs {priority_gbp}M")


print("\n✓ Le programme Aviation AXA XL 2024 est prêt !")
print("\nPour modifier les valeurs:")
print("1. Éditez les dictionnaires LAYER_VALUES_COMMON et LAYER_VALUES_GBP")
print("2. Éditez le dictionnaire REINSURER_SHARE_VALUES pour ajuster les pourcentages de réassurance")
print("3. Relancez ce script pour régénérer le fichier Excel")
