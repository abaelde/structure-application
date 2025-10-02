"""
Test des deux programmes simples pour vérifier les différences entre séquentiel et parallèle
"""

import pandas as pd
import numpy as np
from structures.structure_loader import ProgramLoader
from structures.structure_engine import apply_program_to_bordereau
from structures.program_display import display_program

# Créer un bordereau de test simple
test_bordereau = pd.DataFrame({
    "numero_police": ["POL001", "POL002", "POL003"],
    "exposition": [1000000, 2000000, 500000],
    "country": ["France", "Germany", "France"],
    "region": ["EMEA", "EMEA", "APAC"]
})

print("Bordereau de test:")
print(test_bordereau)
print("\n" + "=" * 80)

# =============================================================================
# TEST DU PROGRAMME SÉQUENTIEL
# =============================================================================

print("TEST DU PROGRAMME SÉQUENTIEL")
print("=" * 80)

try:
    loader_sequential = ProgramLoader("program_simple_sequential.xlsx")
    program_sequential = loader_sequential.get_program()
    
    # Afficher la configuration du programme
    display_program(program_sequential)
    
    results_sequential = apply_program_to_bordereau(test_bordereau, program_sequential)
    
    print("Résultats séquentiel:")
    for _, row in results_sequential.iterrows():
        print(f"\nPolice {row['policy_number']} (Exposition: {row['exposure']:,.0f}):")
        print(f"  Total cédé: {row['ceded']:,.0f}")
        print(f"  Total retenu: {row['retained']:,.0f}")
        
        for detail in row['structures_detail']:
            if detail['applied']:
                print(f"  - {detail['structure_name']}: {detail['ceded']:,.0f} cédé (sur {detail['input_exposure']:,.0f})")
            else:
                print(f"  - {detail['structure_name']}: Non appliqué")

except Exception as e:
    print(f"Erreur avec le programme séquentiel: {e}")

print("\n" + "=" * 80)

# =============================================================================
# TEST DU PROGRAMME PARALLÈLE
# =============================================================================

print("TEST DU PROGRAMME PARALLÈLE")
print("=" * 80)

try:
    loader_parallel = ProgramLoader("program_simple_parallel.xlsx")
    program_parallel = loader_parallel.get_program()
    
    # Afficher la configuration du programme
    display_program(program_parallel)
    
    results_parallel = apply_program_to_bordereau(test_bordereau, program_parallel)
    
    print("Résultats parallèle:")
    for _, row in results_parallel.iterrows():
        print(f"\nPolice {row['policy_number']} (Exposition: {row['exposure']:,.0f}):")
        print(f"  Total cédé: {row['ceded']:,.0f}")
        print(f"  Total retenu: {row['retained']:,.0f}")
        
        for detail in row['structures_detail']:
            if detail['applied']:
                print(f"  - {detail['structure_name']}: {detail['ceded']:,.0f} cédé (sur {detail['input_exposure']:,.0f})")
            else:
                print(f"  - {detail['structure_name']}: Non appliqué")

except Exception as e:
    print(f"Erreur avec le programme parallèle: {e}")

print("\n" + "=" * 80)
print("COMPARAISON DES RÉSULTATS")
print("=" * 80)

if 'results_sequential' in locals() and 'results_parallel' in locals():
    comparison = pd.DataFrame({
        'Police': results_sequential['policy_number'],
        'Exposition': results_sequential['exposure'],
        'Cédé_Séquentiel': results_sequential['ceded'],
        'Retenu_Séquentiel': results_sequential['retained'],
        'Cédé_Parallèle': results_parallel['ceded'],
        'Retenu_Parallèle': results_parallel['retained'],
        'Différence_Cédé': results_parallel['ceded'] - results_sequential['ceded']
    })
    
    print(comparison.to_string(index=False))
    
    print(f"\nDifférence moyenne cédé: {comparison['Différence_Cédé'].mean():,.0f}")
    print(f"Différence maximale cédé: {comparison['Différence_Cédé'].max():,.0f}")

print("\n✓ Tests terminés !")
