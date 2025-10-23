#!/usr/bin/env python3
"""
Test d'intégration Snowpark avec l'architecture existante.

Ce script teste le chargement d'un programme via Snowpark
et sa conversion en objet Program en mémoire via le ProgramSerializer.
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from snowflake_utils import get_snowpark_session, close_snowpark_session
from src.managers.program_snowpark_manager import SnowparkProgramManager


def test_snowpark_program_loading():
    """Test du chargement d'un programme via Snowpark."""
    print("🧪 Test d'intégration Snowpark avec l'architecture existante")
    print("=" * 60)
    
    try:
        # 1. Obtenir une session Snowpark
        print("1. Connexion Snowpark...")
        session = get_snowpark_session()
        print("   ✅ Session Snowpark obtenue")
        
        # 2. Créer le manager Snowpark
        print("\n2. Création du ProgramManager Snowpark...")
        manager = SnowparkProgramManager(session)
        print("   ✅ ProgramManager Snowpark créé")
        
        # 3. Charger un programme par ID
        print("\n3. Chargement du programme...")
        program_id = 1
        
        program = manager.load(program_id)
        print(f"   ✅ Programme chargé: {program.name}")
        print(f"   ✅ Département: {program.underwriting_department}")
        print(f"   ✅ Nombre de structures: {len(program.structures)}")
        print(f"   ✅ Nombre d'exclusions: {len(program.exclusions)}")
        
        # 4. Utiliser la méthode describe() du programme
        print("\n4. Description du programme:")
        print("-" * 40)
        program.describe()
        
        # 5. Afficher quelques détails des structures
        print("\n5. Détails des structures:")
        print("-" * 40)
        for i, structure in enumerate(program.structures[:3]):  # Afficher les 3 premières
            print(f"   Structure {i+1}: {structure.structure_name}")
            print(f"   - Type: {structure.type_of_participation}")
            print(f"   - Claim Basis: {structure.claim_basis}")
            print(f"   - Limit: {structure.limit}")
            print(f"   - Attachment: {structure.attachment}")
            print(f"   - Cession: {structure.cession_pct}%")
            print(f"   - Conditions: {len(structure.conditions)}")
            print()
        
        # 6. Tester l'accès aux données du programme
        print("6. Test d'accès aux données:")
        print("-" * 40)
        print(f"   ✅ Nom du programme: {program.name}")
        print(f"   ✅ Département UW: {program.underwriting_department}")
        print(f"   ✅ Colonnes de dimensions: {program.dimension_columns}")
        print(f"   ✅ Programme chargé avec ID: {manager.get_loaded_program_id()}")
        
        print("\n✅ Test d'intégration réussi !")
        print("   Le programme a été chargé via Snowpark et converti en objet Program")
        print("   L'objet Program est maintenant disponible en mémoire avec toutes ses méthodes")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        close_snowpark_session()


def test_program_serialization():
    """Test de la sérialisation du programme chargé."""
    print("\n" + "=" * 60)
    print("🧪 Test de sérialisation du programme")
    print("=" * 60)
    
    try:
        session = get_snowpark_session()
        manager = SnowparkProgramManager(session)
        
        # Charger le programme
        program_id = 1
        program = manager.load(program_id)
        
        # Tester la sérialisation en DataFrames
        print("1. Test de sérialisation en DataFrames...")
        dfs = manager.serializer.program_to_dataframes(program)
        
        print(f"   ✅ Program DataFrame: {len(dfs['program'])} ligne(s)")
        print(f"   ✅ Structures DataFrame: {len(dfs['structures'])} ligne(s)")
        print(f"   ✅ Conditions DataFrame: {len(dfs['conditions'])} ligne(s)")
        print(f"   ✅ Exclusions DataFrame: {len(dfs['exclusions'])} ligne(s)")
        print(f"   ✅ Field Links DataFrame: {len(dfs['field_links'])} ligne(s)")
        
        # Afficher quelques colonnes des DataFrames
        print("\n2. Aperçu des DataFrames:")
        print("   Program:")
        print(f"     - TITLE: {dfs['program']['TITLE'].iloc[0]}")
        print(f"     - UW_LOB_ID: {dfs['program']['UW_LOB_ID'].iloc[0]}")
        
        print("   Structures:")
        if not dfs['structures'].empty:
            print(f"     - Première structure: {dfs['structures']['RP_STRUCTURE_NAME'].iloc[0]}")
            print(f"     - Type: {dfs['structures']['TYPE_OF_PARTICIPATION'].iloc[0]}")
        
        print("\n✅ Test de sérialisation réussi !")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test de sérialisation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        close_snowpark_session()


def main():
    """Fonction principale de test."""
    print("🚀 Test d'intégration Snowpark avec l'architecture existante")
    print("=" * 80)
    
    tests = [
        ("Chargement de programme", test_snowpark_program_loading),
        ("Sérialisation", test_program_serialization),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Erreur inattendue dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé des tests
    print(f"\n{'='*80}")
    print("📊 RÉSUMÉ DES TESTS")
    print(f"{'='*80}")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSÉ" if success else "❌ ÉCHOUÉ"
        print(f"{test_name:.<50} {status}")
        if success:
            passed += 1
    
    print(f"\nRésultat: {passed}/{total} tests passés")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! L'intégration Snowpark fonctionne parfaitement.")
        print("\n📋 Prochaines étapes possibles:")
        print("   - Intégrer dans run_program_analysis.py")
        print("   - Créer des fonctions d'écriture")
        print("   - Migrer progressivement du connecteur classique")
        return 0
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
        return 1


def show_usage():
    """Affiche l'utilisation du script."""
    print("Usage: python scripts/test_snowpark_integration.py")
    print("\nCe script teste l'intégration Snowpark avec l'architecture existante.")
    print("\nPrérequis:")
    print("- Configuration Snowflake valide")
    print("- Données de programmes dans la base")
    print("- Programme avec ID 1 doit exister")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        show_usage()
        sys.exit(0)
    
    try:
        exit_code = main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu par l'utilisateur")
        exit_code = 1
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        exit_code = 1
    
    sys.exit(exit_code)
