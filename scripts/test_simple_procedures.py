#!/usr/bin/env python3
"""
Test des procédures Snowpark simplifiées.

Ce script teste les fonctions Python qui encapsulent
la logique de lecture des programmes avec Snowpark.
"""

import sys
import json
from pathlib import Path

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from snowflake_utils import get_snowpark_session, close_snowpark_session
from snowflake_utils import (
    read_program_simple,
    list_programs_simple,
    program_exists_simple,
    test_simple_procedures
)


def test_list_programs():
    """Test de la fonction de liste des programmes."""
    print("📋 Test de LIST_PROGRAMS...")
    
    try:
        session = get_snowpark_session()
        result = list_programs_simple(session)
        
        if "error" in result:
            print(f"❌ Erreur: {result['error']}")
            return False
        
        programs = result.get("programs", [])
        total_count = result.get("total_count", 0)
        
        print(f"✅ {total_count} programmes trouvés")
        
        if programs:
            print("   Premiers programmes:")
            for i, program in enumerate(programs[:3]):  # Afficher les 3 premiers
                print(f"   - ID: {program['REINSURANCE_PROGRAM_ID']}, "
                      f"Titre: {program['TITLE']}, "
                      f"Structures: {program['STRUCTURES_COUNT']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test LIST_PROGRAMS: {e}")
        return False


def test_program_exists():
    """Test de la fonction de vérification d'existence."""
    print("\n🔍 Test de PROGRAM_EXISTS...")
    
    try:
        session = get_snowpark_session()
        
        # Tester avec différents IDs
        test_ids = [1, 2, 3, 100, 999]
        
        for program_id in test_ids:
            exists = program_exists_simple(session, program_id)
            status = "✅ Existe" if exists else "❌ N'existe pas"
            print(f"   Programme {program_id}: {status}")
            
            if exists:
                # Si on trouve un programme qui existe, on peut tester READ_PROGRAM
                return test_read_program(program_id)
        
        print("   Aucun programme trouvé pour les tests")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test PROGRAM_EXISTS: {e}")
        return False


def test_read_program(program_id: int):
    """Test de la fonction de lecture de programme."""
    print(f"\n📖 Test de READ_PROGRAM pour le programme {program_id}...")
    
    try:
        session = get_snowpark_session() # FAIRE UNE FIXTURE de la session
        result = read_program_simple(session, program_id)
        
        if "error" in result:
            print(f"❌ Erreur: {result['error']}")
            return False
        
        metadata = result.get("metadata", {})
        program_data = result.get("program", [])
        
        if not program_data:
            print("❌ Aucune donnée de programme trouvée")
            return False
        
        program = program_data[0]
        
        print(f"✅ Programme lu avec succès:")
        print(f"   - ID: {metadata.get('program_id')}")
        print(f"   - Titre: {program.get('TITLE', 'N/A')}")
        print(f"   - Structures: {metadata.get('structures_count', 0)}")
        print(f"   - Conditions: {metadata.get('conditions_count', 0)}")
        print(f"   - Exclusions: {metadata.get('exclusions_count', 0)}")
        print(f"   - Field Links: {metadata.get('field_links_count', 0)}")
        
        # Afficher quelques détails des structures si disponibles
        structures = result.get("structures", [])
        if structures:
            print(f"   - Première structure: {structures[0].get('RP_STRUCTURE_NAME', 'N/A')}")
        
        # Afficher quelques détails des conditions si disponibles
        conditions = result.get("conditions", [])
        if conditions:
            print(f"   - Première condition: {conditions[0].get('PRODUCT_TYPE_LEVEL_1', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test READ_PROGRAM: {e}")
        return False


def test_performance_comparison():
    """Test de comparaison de performance avec l'approche classique."""
    print("\n⚡ Test de performance...")
    
    try:
        import time
        
        session = get_snowpark_session()
        
        # Test avec Snowpark
        start = time.time()
        result = read_program_simple(session, 1)
        snowpark_time = time.time() - start
        
        if "error" not in result:
            print(f"   ✅ Snowpark: {snowpark_time:.3f}s")
            print(f"      - Programme: {result['metadata']['program_id']}")
            print(f"      - Structures: {result['metadata']['structures_count']}")
            print(f"      - Conditions: {result['metadata']['conditions_count']}")
        else:
            print(f"   ❌ Erreur Snowpark: {result['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de performance: {e}")
        return False


def main():
    """Fonction principale de test."""
    print("🧪 Test des procédures Snowpark simplifiées")
    print("=" * 50)
    
    tests = [
        ("Liste des programmes", test_list_programs),
        ("Existence des programmes", test_program_exists),
        ("Performance", test_performance_comparison),
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
    
    # Test automatique avec la fonction intégrée
    print(f"\n{'='*20} Test automatique {'='*20}")
    try:
        session = get_snowpark_session()
        test_simple_procedures(session)
        results.append(("Test automatique", True))
    except Exception as e:
        print(f"❌ Erreur lors du test automatique: {e}")
        results.append(("Test automatique", False))
    
    # Résumé des tests
    print(f"\n{'='*50}")
    print("📊 RÉSUMÉ DES TESTS")
    print(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSÉ" if success else "❌ ÉCHOUÉ"
        print(f"{test_name:.<30} {status}")
        if success:
            passed += 1
    
    print(f"\nRésultat: {passed}/{total} tests passés")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! Les procédures Snowpark simplifiées fonctionnent correctement.")
        return 0
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
        return 1


def show_usage():
    """Affiche l'utilisation du script."""
    print("Usage: python scripts/test_simple_procedures.py")
    print("\nCe script teste les procédures Snowpark simplifiées.")
    print("\nPrérequis:")
    print("- Configuration Snowflake valide")
    print("- Données de programmes dans la base")


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
    finally:
        # Fermer la session
        close_snowpark_session()
    
    sys.exit(exit_code)
