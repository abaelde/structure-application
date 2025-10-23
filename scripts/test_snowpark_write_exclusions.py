#!/usr/bin/env python3
"""
Test d'écriture Snowpark - Programme avec exclusions

Ce script teste l'écriture d'un programme Quota Share avec exclusions via Snowpark.
Il s'inspire du script create_quota_share_with_exclusion.py pour créer un programme
avec des exclusions et vérifier que l'écriture Snowpark les gère correctement.
"""

import sys
import os
from datetime import datetime

# Ajouter le répertoire racine au path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.builders import build_quota_share, build_program
from src.domain.exclusion import ExclusionRule
from snowflake_utils import save_program_snowpark
from snowflake_utils.snowpark_config import get_snowpark_session, close_snowpark_session
from src.managers.program_snowpark_manager import SnowparkProgramManager


def create_quota_share_with_exclusions_program():
    """Crée le programme Quota Share avec exclusions en utilisant exactement le même code que create_quota_share_with_exclusion.py."""
    from datetime import datetime
    
    # Créer un quota share avec condition normale uniquement
    qs = build_quota_share(
        name="QS Casualty 25%",
        cession_pct=0.25,
        signed_share=1.0,
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2024-12-31",
    )
    
    # Créer les exclusions - Test de compaction multi-valeurs
    exclusions = [
        ExclusionRule(
            values_by_dimension={"COUNTRY": ["Iran", "Russia"]},
            name="Sanctions Countries",
        ),
    ]
    
    # Créer le programme avec les exclusions et timestamp unique
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    program_name = f"Quota_Share_with_Exclusions_SNOWPARK_TEST_{timestamp}"
    
    program = build_program(
        name=program_name,
        structures=[qs],
        underwriting_department="casualty",
        exclusions=exclusions,
    )
    
    return program


def test_write_quota_share_with_exclusions_snowpark():
    """Test d'écriture du programme Quota Share avec exclusions via Snowpark."""
    print("🚀 Test d'écriture Snowpark - Programme Quota Share avec exclusions")
    print("=" * 80)
    
    try:
        # 1. Création du programme
        print("1. Création du programme Quota Share avec exclusions...")
        program = create_quota_share_with_exclusions_program()
        program_name = program.name
        
        print(f"   ✅ Programme créé: {program_name}")
        print(f"   ✅ Structures: {len(program.structures)}")
        print(f"   ✅ Exclusions: {len(program.exclusions)}")
        
        # 2. Sauvegarde via Snowpark
        print("\n2. Sauvegarde via Snowpark...")
        success = save_program_snowpark(program, program_name)
        print(f"   ✅ Programme sauvegardé: {success}")
        
        # 3. Vérification - Lecture du programme sauvegardé
        print("\n3. Vérification - Lecture du programme sauvegardé...")
        session = get_snowpark_session()
        
        try:
            manager = SnowparkProgramManager(session)
            
            # Trouver l'ID du programme créé par son nom
            result = session.sql(f"SELECT REINSURANCE_PROGRAM_ID FROM REINSURANCE_PROGRAM WHERE TITLE = '{program_name}'").collect()
            if not result:
                print(f"   ❌ Programme '{program_name}' non trouvé")
                return False
            
            program_id = int(result[0][0])
            
            print(f"   🔍 Lecture du programme avec ID: {program_id}")
            loaded_program = manager.load(program_id)
            
            print(f"   ✅ Programme relu: {loaded_program.name}")
            print(f"   ✅ Structures: {len(loaded_program.structures)}")
            print(f"   ✅ Exclusions: {len(loaded_program.exclusions)}")
            
            # 4. Vérification de la cohérence
            print("\n4. Vérification de la cohérence...")
            
            # Vérifier le nom
            if program.name == loaded_program.name:
                print("   ✅ Nom cohérent")
            else:
                print(f"   ❌ Nom différent: original='{program.name}', chargé='{loaded_program.name}'")
                return False
            
            # Vérifier le département
            if program.underwriting_department == loaded_program.underwriting_department:
                print("   ✅ Département cohérent")
            else:
                print(f"   ❌ Département différent: original='{program.underwriting_department}', chargé='{loaded_program.underwriting_department}'")
                return False
            
            # Vérifier le nombre de structures
            if len(program.structures) == len(loaded_program.structures):
                print("   ✅ Nombre de structures cohérent")
            else:
                print(f"   ❌ Nombre de structures différent: original={len(program.structures)}, chargé={len(loaded_program.structures)}")
                return False
            
            # Vérifier le nombre d'exclusions
            if len(program.exclusions) == len(loaded_program.exclusions):
                print("   ✅ Nombre d'exclusions cohérent")
            else:
                print(f"   ❌ Nombre d'exclusions différent: original={len(program.exclusions)}, chargé={len(loaded_program.exclusions)}")
                return False
            
            # Vérifier les détails des exclusions
            if len(program.exclusions) > 0:
                original_exclusion = program.exclusions[0]
                loaded_exclusion = loaded_program.exclusions[0]
                
                # Note: Le nom de l'exclusion n'est pas stocké dans Snowflake, donc il sera toujours None
                print(f"   ℹ️  Nom d'exclusion original: '{original_exclusion.name}' (non stocké en base)")
                print(f"   ℹ️  Nom d'exclusion chargé: '{loaded_exclusion.name}' (attendu: None)")
                
                # Vérifier les valeurs d'exclusion (ce qui est vraiment important)
                original_values = original_exclusion.values_by_dimension.get("COUNTRY", [])
                loaded_values = loaded_exclusion.values_by_dimension.get("COUNTRY", [])
                
                if set(original_values) == set(loaded_values):
                    print("   ✅ Valeurs d'exclusion cohérentes")
                    print(f"      Original: {original_values}")
                    print(f"      Chargé: {loaded_values}")
                else:
                    print(f"   ❌ Valeurs d'exclusion différentes: original={original_values}, chargé={loaded_values}")
                    return False
            
            print("\n🎉 Test d'écriture Snowpark réussi !")
            print("   Le programme Quota Share avec exclusions a été écrit et relu avec succès")
            print("   Toutes les vérifications de cohérence sont passées")
            
            return True
            
        finally:
            close_snowpark_session()
            
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Fonction principale de test."""
    print("🧪 Test d'écriture Snowpark - Programme Quota Share avec exclusions")
    print("=" * 80)
    
    success = test_write_quota_share_with_exclusions_snowpark()
    
    if success:
        print("\n🎉 Test réussi !")
        print("   L'écriture Snowpark avec exclusions fonctionne correctement")
        print("   Le programme Quota Share avec exclusions a été sauvegardé et relu avec succès")
    else:
        print("\n❌ Test échoué !")
        print("   Vérifiez les erreurs ci-dessus")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
