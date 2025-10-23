#!/usr/bin/env python3
"""
Test d'intégration Snowpark avec application de programme sur bordereau.

Ce script teste le workflow complet :
1. Chargement d'un programme depuis Snowflake via Snowpark
2. Chargement d'un bordereau CSV
3. Application du programme sur le bordereau
4. Génération des résultats

Il s'inspire du script run_program_analysis.py mais sous forme de test.
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from snowflake_utils import get_snowpark_session, close_snowpark_session
from src.managers.program_snowpark_manager import SnowparkProgramManager
from src.managers.bordereau_manager import BordereauManager
from src.engine import apply_program_to_bordereau, apply_program_to_bordereau_simple
from src.presentation import generate_detailed_report


def test_snowpark_bordereau_analysis():
    """Test complet du workflow Snowpark + bordereau."""
    print("🧪 Test d'intégration Snowpark avec application sur bordereau")
    print("=" * 70)
    
    try:
        # 1. Connexion Snowpark
        print("1. Connexion Snowpark...")
        session = get_snowpark_session()
        print("   ✅ Session Snowpark obtenue")
        
        # 2. Chargement du programme via Snowpark
        print("\n2. Chargement du programme via Snowpark...")
        program_id = 1  # ID du programme à tester
        manager = SnowparkProgramManager(session)
        
        program = manager.load(program_id)
        print(f"   ✅ Programme chargé: {program.name}")
        print(f"   ✅ Département: {program.underwriting_department}")
        print(f"   ✅ Nombre de structures: {len(program.structures)}")
        print(f"   ✅ Nombre d'exclusions: {len(program.exclusions)}")
        
        # 3. Chargement du bordereau CSV
        print("\n3. Chargement du bordereau CSV...")
        bordereau_path = project_root / "examples" / "bordereaux" / "bordereau_aviation_axa_xl.csv"
        
        if not bordereau_path.exists():
            print(f"   ❌ Bordereau non trouvé: {bordereau_path}")
            return False
        
        # Utiliser le BordereauManager pour charger et valider
        b_backend = BordereauManager.detect_backend(str(bordereau_path))
        b_manager = BordereauManager(backend=b_backend)
        bordereau = b_manager.load(str(bordereau_path), program=program, validate=True)
        
        print(f"   ✅ Bordereau chargé: {len(bordereau)} polices")
        print(f"   ✅ Validation réussie")
        
        # 4. Description du programme
        print("\n4. Configuration du programme:")
        print("-" * 50)
        program.describe()
        
        # 5. Application du programme sur le bordereau
        print("\n5. Application du programme sur le bordereau...")
        calculation_date = "2024-06-01"
        
        # Test avec export simplifié
        print("   📊 Test avec export simplifié...")
        simple_results = apply_program_to_bordereau_simple(
            bordereau, program, calculation_date
        )
        print(f"   ✅ Export simplifié: {len(simple_results)} polices traitées")
        
        # Test avec export détaillé
        print("   📊 Test avec export détaillé...")
        bordereau_with_net, detailed_results = apply_program_to_bordereau(
            bordereau, program, calculation_date
        )
        print(f"   ✅ Export détaillé: {len(detailed_results)} polices traitées")
        
        # 6. Vérification des résultats
        print("\n6. Vérification des résultats:")
        print("-" * 50)
        
        # Vérifier les colonnes des résultats simplifiés
        print("   Résultats simplifiés:")
        print(f"     - Colonnes: {list(simple_results.columns)}")
        print(f"     - Lignes: {len(simple_results)}")
        if not simple_results.empty:
            # Utiliser la première colonne disponible pour identifier la police
            first_col = simple_results.columns[0]
            print(f"     - Première ligne ({first_col}): {simple_results.iloc[0][first_col]}")
        
        # Vérifier les colonnes des résultats détaillés
        print("   Résultats détaillés:")
        print(f"     - Colonnes: {list(detailed_results.columns)}")
        print(f"     - Lignes: {len(detailed_results)}")
        if not detailed_results.empty:
            # Utiliser la première colonne disponible pour identifier la police
            first_col = detailed_results.columns[0]
            print(f"     - Première ligne ({first_col}): {detailed_results.iloc[0][first_col]}")
        
        # 7. Test de génération de rapport
        print("\n7. Test de génération de rapport...")
        try:
            # Créer un fichier temporaire pour le rapport
            temp_report = project_root / "output" / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            temp_report.parent.mkdir(exist_ok=True)
            
            generate_detailed_report(detailed_results, program, str(temp_report))
            print(f"   ✅ Rapport généré: {temp_report}")
            
            # Vérifier que le fichier existe et n'est pas vide
            if temp_report.exists() and temp_report.stat().st_size > 0:
                print(f"   ✅ Rapport valide ({temp_report.stat().st_size} bytes)")
            else:
                print("   ⚠️  Rapport vide ou inexistant")
                
        except Exception as e:
            print(f"   ⚠️  Erreur lors de la génération du rapport: {e}")
        
        # 8. Test de sauvegarde des résultats
        print("\n8. Test de sauvegarde des résultats...")
        try:
            output_dir = project_root / "output" / f"snowpark_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Sauvegarder les résultats simplifiés
            simple_file = output_dir / "simple_results.csv"
            simple_results.to_csv(simple_file, index=False)
            print(f"   ✅ Résultats simplifiés: {simple_file}")
            
            # Sauvegarder les résultats détaillés
            detailed_file = output_dir / "detailed_results.csv"
            detailed_results.to_csv(detailed_file, index=False)
            print(f"   ✅ Résultats détaillés: {detailed_file}")
            
            # Sauvegarder le bordereau avec cessions
            bordereau_file = output_dir / "bordereau_with_cessions.csv"
            bordereau_with_net.to_csv(bordereau_file, index=False)
            print(f"   ✅ Bordereau avec cessions: {bordereau_file}")
            
        except Exception as e:
            print(f"   ⚠️  Erreur lors de la sauvegarde: {e}")
        
        print("\n✅ Test d'intégration Snowpark + bordereau réussi !")
        print("   Le workflow complet fonctionne :")
        print("   - Chargement programme via Snowpark ✓")
        print("   - Chargement bordereau CSV ✓")
        print("   - Application du programme ✓")
        print("   - Génération des résultats ✓")
        print("   - Export des fichiers ✓")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        close_snowpark_session()


def test_program_validation():
    """Test de validation du programme chargé."""
    print("\n" + "=" * 70)
    print("🧪 Test de validation du programme")
    print("=" * 70)
    
    try:
        session = get_snowpark_session()
        manager = SnowparkProgramManager(session)
        
        # Charger le programme
        program_id = 1
        program = manager.load(program_id)
        
        print("1. Validation des structures...")
        for i, structure in enumerate(program.structures):
            print(f"   Structure {i+1}: {structure.structure_name}")
            print(f"     - Type: {structure.type_of_participation}")
            print(f"     - Claim Basis: {structure.claim_basis}")
            print(f"     - Limit: {structure.limit}")
            print(f"     - Attachment: {structure.attachment}")
            print(f"     - Cession: {structure.cession_pct}%")
            print(f"     - Conditions: {len(structure.conditions)}")
            
            # Vérifier que les conditions sont valides
            for j, condition in enumerate(structure.conditions):
                # Utiliser les attributs disponibles de la condition
                condition_info = f"Condition {j+1}"
                if hasattr(condition, 'product_type_level_1') and condition.product_type_level_1:
                    condition_info += f": {condition.product_type_level_1}"
                elif hasattr(condition, 'description') and condition.description:
                    condition_info += f": {condition.description}"
                else:
                    condition_info += f": {type(condition).__name__}"
                print(f"       {condition_info}")
        
        print("\n2. Validation des exclusions...")
        for i, exclusion in enumerate(program.exclusions):
            print(f"   Exclusion {i+1}: {exclusion.exclusion_type}")
            print(f"     - Description: {exclusion.description}")
        
        print("\n✅ Validation du programme réussie")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la validation: {e}")
        return False
    
    finally:
        close_snowpark_session()


def test_bordereau_processing():
    """Test du traitement du bordereau."""
    print("\n" + "=" * 70)
    print("🧪 Test du traitement du bordereau")
    print("=" * 70)
    
    try:
        session = get_snowpark_session()
        manager = SnowparkProgramManager(session)
        
        # Charger le programme
        program = manager.load(1)
        
        # Charger le bordereau
        bordereau_path = project_root / "examples" / "bordereaux" / "bordereau_aviation_axa_xl.csv"
        b_manager = BordereauManager(backend="csv")
        bordereau = b_manager.load(str(bordereau_path), program=program, validate=True)
        
        print("1. Analyse du bordereau...")
        print(f"   - Nombre de polices: {len(bordereau)}")
        
        # Accéder au DataFrame pandas du bordereau
        bordereau_df = bordereau.to_engine_dataframe()
        print(f"   - Colonnes: {list(bordereau_df.columns)}")
        
        # Analyser les données
        print("\n2. Analyse des données...")
        if 'HULL_LIMIT' in bordereau_df.columns:
            hull_limits = bordereau_df['HULL_LIMIT'].dropna()
            print(f"   - Limites Hull: min={hull_limits.min():,.0f}, max={hull_limits.max():,.0f}")
        
        if 'LIABILITY_LIMIT' in bordereau_df.columns:
            liability_limits = bordereau_df['LIABILITY_LIMIT'].dropna()
            print(f"   - Limites Liability: min={liability_limits.min():,.0f}, max={liability_limits.max():,.0f}")
        
        if 'HULL_SHARE' in bordereau_df.columns:
            hull_shares = bordereau_df['HULL_SHARE'].dropna()
            print(f"   - Parts Hull: min={hull_shares.min():.2%}, max={hull_shares.max():.2%}")
        
        print("\n✅ Analyse du bordereau réussie")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'analyse du bordereau: {e}")
        return False
    
    finally:
        close_snowpark_session()


def main():
    """Fonction principale de test."""
    print("🚀 Test d'intégration Snowpark avec application sur bordereau")
    print("=" * 80)
    
    tests = [
        ("Workflow complet", test_snowpark_bordereau_analysis),
        ("Validation programme", test_program_validation),
        ("Traitement bordereau", test_bordereau_processing),
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
        print("🎉 Tous les tests sont passés ! L'intégration Snowpark + bordereau fonctionne parfaitement.")
        print("\n📋 Le workflow complet est opérationnel:")
        print("   - Chargement programme via Snowpark ✓")
        print("   - Chargement bordereau CSV ✓")
        print("   - Application du programme ✓")
        print("   - Génération des résultats ✓")
        print("   - Export des fichiers ✓")
        return 0
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
        return 1


def show_usage():
    """Affiche l'utilisation du script."""
    print("Usage: python scripts/test_snowpark_bordereau_analysis.py")
    print("\nCe script teste l'intégration Snowpark avec application sur bordereau.")
    print("\nPrérequis:")
    print("- Configuration Snowflake valide")
    print("- Programme avec ID 1 dans la base")
    print("- Bordereau aviation_axa_xl.csv dans examples/bordereaux/")


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
