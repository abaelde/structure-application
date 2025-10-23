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


def main():
    """Test unique du workflow complet Snowpark + bordereau."""
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
            return 1
        
        # Utiliser le BordereauManager pour charger et valider
        b_backend = BordereauManager.detect_backend(str(bordereau_path))
        b_manager = BordereauManager(backend=b_backend)
        bordereau = b_manager.load(str(bordereau_path), program=program, validate=True)
        
        print(f"   ✅ Bordereau chargé: {len(bordereau)} polices")
        print(f"   ✅ Validation réussie")
        
        # 4. Application du programme sur le bordereau
        print("\n4. Application du programme sur le bordereau...")
        calculation_date = "2024-06-01"
        
        # Test avec export simplifié
        print("   📊 Export simplifié...")
        simple_results = apply_program_to_bordereau_simple(
            bordereau, program, calculation_date
        )
        print(f"   ✅ Export simplifié: {len(simple_results)} polices traitées")
        
        # Test avec export détaillé
        print("   📊 Export détaillé...")
        bordereau_with_net, detailed_results = apply_program_to_bordereau(
            bordereau, program, calculation_date
        )
        print(f"   ✅ Export détaillé: {len(detailed_results)} polices traitées")
        
        # 5. Vérification des résultats
        print("\n5. Vérification des résultats:")
        print(f"   - Résultats simplifiés: {len(simple_results)} polices")
        print(f"   - Résultats détaillés: {len(detailed_results)} polices")
        if not simple_results.empty:
            first_col = simple_results.columns[0]
            print(f"   - Première police: {simple_results.iloc[0][first_col]}")
        
        # 6. Génération du rapport détaillé
        print("\n6. Génération du rapport détaillé...")
        output_dir = project_root / "output" / f"snowpark_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = output_dir / "detailed_report.txt"
        generate_detailed_report(detailed_results, program, str(report_file))
        print(f"   ✅ Rapport détaillé: {report_file}")
        
        # 7. Sauvegarde des résultats
        print("\n7. Sauvegarde des résultats...")
        
        # Sauvegarder les résultats
        simple_file = output_dir / "simple_results.csv"
        simple_results.to_csv(simple_file, index=False)
        print(f"   ✅ Résultats simplifiés: {simple_file}")
        
        detailed_file = output_dir / "detailed_results.csv"
        detailed_results.to_csv(detailed_file, index=False)
        print(f"   ✅ Résultats détaillés: {detailed_file}")
        
        bordereau_file = output_dir / "bordereau_with_cessions.csv"
        bordereau_with_net.to_csv(bordereau_file, index=False)
        print(f"   ✅ Bordereau avec cessions: {bordereau_file}")
        
        print("\n✅ Test d'intégration Snowpark + bordereau réussi !")
        print("   Le workflow complet fonctionne :")
        print("   - Chargement programme via Snowpark ✓")
        print("   - Chargement bordereau CSV ✓")
        print("   - Application du programme ✓")
        print("   - Génération du rapport détaillé ✓")
        print("   - Export des fichiers ✓")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        close_snowpark_session()


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
