"""
Démonstration de l'utilisation des exemples organisés
"""

import os
import pandas as pd
from structures.structure_loader import ProgramLoader
from structures.treaty_manager import TreatyManager
from structures.structure_engine import apply_program_to_bordereau, apply_treaty_manager_to_bordereau

def demo_organized_examples():
    print("Démonstration des exemples organisés")
    print("=" * 50)
    
    # Vérifier la structure des dossiers
    print("1. Structure des dossiers d'exemples:")
    examples_dir = "examples"
    if os.path.exists(examples_dir):
        for root, dirs, files in os.walk(examples_dir):
            level = root.replace(examples_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
    else:
        print("   ⚠️  Dossier examples non trouvé")
    
    # Test 1: Programme simple
    print(f"\n2. Test d'un programme simple:")
    print("-" * 30)
    
    try:
        # Charger un programme simple
        program_path = "examples/programs/program_simple_parallel.xlsx"
        if os.path.exists(program_path):
            loader = ProgramLoader(program_path)
            program = loader.get_program()
            print(f"   ✓ Programme chargé: {program['name']}")
            print(f"   ✓ Mode: {program['mode']}")
            print(f"   ✓ Structures: {len(program['structures'])}")
        else:
            print(f"   ⚠️  Fichier non trouvé: {program_path}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 2: Bordereau
    print(f"\n3. Test d'un bordereau:")
    print("-" * 30)
    
    try:
        # Charger un bordereau
        bordereau_path = "examples/bordereaux/bordereau_exemple.csv"
        if os.path.exists(bordereau_path):
            bordereau_df = pd.read_csv(bordereau_path)
            print(f"   ✓ Bordereau chargé: {len(bordereau_df)} polices")
            print(f"   ✓ Colonnes: {list(bordereau_df.columns)}")
        else:
            print(f"   ⚠️  Fichier non trouvé: {bordereau_path}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 3: Traités multi-années
    print(f"\n4. Test des traités multi-années:")
    print("-" * 30)
    
    try:
        # Charger les traités
        treaty_paths = {
            "2023": "examples/treaties/treaty_2023.xlsx",
            "2024": "examples/treaties/treaty_2024.xlsx", 
            "2025": "examples/treaties/treaty_2025.xlsx"
        }
        
        # Vérifier que tous les fichiers existent
        missing_files = []
        for year, path in treaty_paths.items():
            if not os.path.exists(path):
                missing_files.append(f"{year}: {path}")
        
        if missing_files:
            print(f"   ⚠️  Fichiers manquants:")
            for missing in missing_files:
                print(f"     - {missing}")
        else:
            treaty_manager = TreatyManager(treaty_paths)
            print(f"   ✓ Traités chargés: {treaty_manager.get_available_years()}")
            print(f"   ✓ Nombre de traités: {len(treaty_manager.treaties)}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test 4: Scripts d'exemple
    print(f"\n5. Test des scripts d'exemple:")
    print("-" * 30)
    
    scripts_dir = "examples/scripts"
    if os.path.exists(scripts_dir):
        scripts = [f for f in os.listdir(scripts_dir) if f.endswith('.py')]
        print(f"   ✓ Scripts disponibles: {len(scripts)}")
        for script in scripts:
            print(f"     - {script}")
    else:
        print(f"   ⚠️  Dossier scripts non trouvé: {scripts_dir}")
    
    # Test 5: Exemple complet
    print(f"\n6. Exemple complet avec claim_basis:")
    print("-" * 30)
    
    try:
        # Charger les traités et le bordereau de test
        treaty_paths = {
            "2023": "examples/treaties/treaty_2023.xlsx",
            "2024": "examples/treaties/treaty_2024.xlsx", 
            "2025": "examples/treaties/treaty_2025.xlsx"
        }
        
        bordereau_path = "examples/bordereaux/bordereau_multi_year_test.csv"
        
        if all(os.path.exists(path) for path in treaty_paths.values()) and os.path.exists(bordereau_path):
            treaty_manager = TreatyManager(treaty_paths)
            bordereau_df = pd.read_csv(bordereau_path)
            
            # Test rapide avec une seule police
            test_policy = bordereau_df.iloc[0].to_dict()
            print(f"   ✓ Test avec la police: {test_policy['numero_police']}")
            print(f"   ✓ Souscription: {test_policy['inception_date']}")
            
            # Appliquer la logique claim_basis
            result = apply_treaty_manager_to_bordereau(
                bordereau_df.head(1), treaty_manager, "2025-06-15"
            )
            
            if len(result) > 0:
                first_result = result.iloc[0]
                print(f"   ✓ Traité appliqué: {first_result['selected_treaty_year']}")
                print(f"   ✓ Claim basis: {first_result['claim_basis']}")
                print(f"   ✓ Cédé: {first_result['ceded']:,.0f}")
            else:
                print(f"   ⚠️  Aucun résultat obtenu")
        else:
            print(f"   ⚠️  Fichiers requis non trouvés")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print(f"\n✅ Démonstration terminée !")
    print(f"\nPour utiliser les exemples:")
    print(f"  • Programmes simples: examples/programs/")
    print(f"  • Bordereaux: examples/bordereaux/")
    print(f"  • Traités multi-années: examples/treaties/")
    print(f"  • Scripts d'exemple: examples/scripts/")
    print(f"  • Documentation: examples/README.md")

if __name__ == "__main__":
    demo_organized_examples()
