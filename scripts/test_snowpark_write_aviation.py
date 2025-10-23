#!/usr/bin/env python3
"""
Test d'écriture Snowpark avec le programme Aviation AXA XL.

Ce script teste l'écriture d'un programme complexe via Snowpark
en utilisant le programme Aviation AXA XL comme référence.
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from snowflake_utils import save_program_snowpark, get_snowpark_session, close_snowpark_session
from src.managers.program_snowpark_manager import SnowparkProgramManager


def test_write_aviation_program_snowpark():
    """Test d'écriture du programme Aviation AXA XL via Snowpark."""
    print("🧪 Test d'écriture Snowpark - Programme Aviation AXA XL")
    print("=" * 70)
    
    try:
        # 1. Créer le programme Aviation AXA XL (même logique que create_aviation_AXA_XL.py)
        print("1. Création du programme Aviation AXA XL...")
        program = create_aviation_program()
        print(f"   ✅ Programme créé: {program.name}")
        print(f"   ✅ Structures: {len(program.structures)}")
        print(f"   ✅ Exclusions: {len(program.exclusions)}")
        
        # 2. Sauvegarder via Snowpark
        print("\n2. Sauvegarde via Snowpark...")
        program_name = program.name
        success = save_program_snowpark(program, program_name)
        print(f"   ✅ Programme sauvegardé: {success}")
        
        # 3. Relire le programme pour vérifier
        print("\n3. Vérification - Lecture du programme sauvegardé...")
        session = get_snowpark_session()
        
        try:
            manager = SnowparkProgramManager(session)
            
            # Trouver l'ID du programme créé (le plus récent)
            result = session.sql("SELECT MAX(REINSURANCE_PROGRAM_ID) FROM REINSURANCE_PROGRAM").collect()
            if not result or result[0][0] is None:
                print("   ❌ Aucun programme trouvé")
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
            if program.name != loaded_program.name:
                print(f"   ❌ Nom différent: original='{program.name}', chargé='{loaded_program.name}'")
                return False
            print("   ✅ Nom cohérent")
            
            # Vérifier le département
            if program.underwriting_department != loaded_program.underwriting_department:
                print(f"   ❌ Département différent: original='{program.underwriting_department}', chargé='{loaded_program.underwriting_department}'")
                return False
            print("   ✅ Département cohérent")
            
            # Vérifier la devise principale
            if program.main_currency != loaded_program.main_currency:
                print(f"   ❌ Devise principale différente: original='{program.main_currency}', chargé='{loaded_program.main_currency}'")
                return False
            print("   ✅ Devise principale cohérente")
            
            # Vérifier le nombre de structures
            if len(program.structures) != len(loaded_program.structures):
                print(f"   ❌ Nombre de structures différent: original={len(program.structures)}, chargé={len(loaded_program.structures)}")
                return False
            print("   ✅ Nombre de structures cohérent")
            
            # Vérifier les noms des structures
            original_names = [s.structure_name for s in program.structures]
            loaded_names = [s.structure_name for s in loaded_program.structures]
            
            if set(original_names) != set(loaded_names):
                print(f"   ❌ Noms de structures différents")
                print(f"      Original: {original_names}")
                print(f"      Chargé: {loaded_names}")
                return False
            print("   ✅ Noms de structures cohérents")
            
            print("\n🎉 Test d'écriture Snowpark réussi !")
            print("   Le programme Aviation AXA XL a été écrit et relu avec succès")
            print("   Toutes les vérifications de cohérence sont passées")
            
            return True
            
        finally:
            close_snowpark_session()
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_aviation_program():
    """Crée le programme Aviation AXA XL en utilisant exactement le même code que create_aviation_AXA_XL.py."""
    from src.builders import build_quota_share, build_excess_of_loss, build_program
    from datetime import datetime
    
    # Configuration du programme (identique au script original)
    LAYER_VALUES_COMMON = {
        "XOL_1": (65_000_000, 35_000_000),
        "XOL_2": (50_000_000, 65_000_000),
        "XOL_3": (100_000_000, 115_000_000),
        "XOL_4": (100_000_000, 215_000_000),
        "XOL_5": (100_000_000, 315_000_000),
        "XOL_6": (150_000_000, 415_000_000),
    }
    
    LAYER_VALUES_GBP = {
        "XOL_1": (43_333_333, 23_333_333),
        "XOL_2": (33_333_333, 43_333_333),
        "XOL_3": (66_666_666, 76_666_666),
        "XOL_4": (66_666_666, 143_333_333),
        "XOL_5": (66_666_666, 210_000_000),
        "XOL_6": (100_000_000, 276_666_666),
    }
    
    CURRENCIES_COMMON = ["USD", "CAD", "EUR", "AUD"]
    CURRENCIES_GBP = ["GBP"]
    
    CESSION_RATE_QS = 0.25  # 25% cédé
    REINSURER_SHARE_QS = 0.0165  # 1.65%
    
    # Construction du Quota Share
    qs = build_quota_share(
        name="QS_1",
        cession_pct=CESSION_RATE_QS,
        signed_share=REINSURER_SHARE_QS,
        special_conditions=[
            {
                "CURRENCY": CURRENCIES_COMMON + CURRENCIES_GBP,  # Liste de toutes les devises
                "includes_hull": True,
                "includes_liability": True,
            }
        ],
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )
    
    # Construction des layers XOL
    xol_layers = []
    for i, (layer_name, (limit_common, priority_common)) in enumerate(
        LAYER_VALUES_COMMON.items(), 1
    ):
        limit_gbp, priority_gbp = LAYER_VALUES_GBP[layer_name]
        
        special_conditions = []
        
        # Condition pour USD, CAD, EUR, AUD (valeurs communes)
        special_conditions.append(
            {
                "CURRENCY": CURRENCIES_COMMON,  # Liste de devises
                "includes_hull": True,
                "includes_liability": True,
            }
        )
        
        # Condition pour GBP (avec valeurs spécifiques)
        special_conditions.append(
            {
                "CURRENCY": CURRENCIES_GBP,  # Liste de devises
                "ATTACHMENT_POINT_100": priority_gbp,  # Valeur spécifique pour GBP
                "LIMIT_100": limit_gbp,                # Valeur spécifique pour GBP
                "includes_hull": True,
                "includes_liability": True,
            }
        )
        
        xol = build_excess_of_loss(
            name=layer_name,
            attachment=priority_common,  # Valeur par défaut pour les devises communes
            limit=limit_common,          # Valeur par défaut pour les devises communes
            signed_share=0.05,           # 5% signed share pour les excess of loss
            special_conditions=special_conditions,
            claim_basis="risk_attaching",
            inception_date="2024-01-01",
            expiry_date="2025-01-01",
            predecessor_title="QS_1",
        )
        xol_layers.append(xol)
    
    # Construction du programme avec timestamp unique
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    program_name = f"AVIATION_AXA_XL_SNOWPARK_TEST_{timestamp}"
    
    program = build_program(
        name=program_name,
        structures=[qs] + xol_layers,
        main_currency="USD",  # Devise principale du programme
        underwriting_department="aviation",
    )
    
    return program


def main():
    """Fonction principale de test."""
    print("🚀 Test d'écriture Snowpark - Programme Aviation AXA XL")
    print("=" * 80)
    
    try:
        success = test_write_aviation_program_snowpark()
        
        if success:
            print("\n🎉 Test réussi !")
            print("   L'écriture Snowpark fonctionne correctement")
            print("   Le programme Aviation AXA XL a été sauvegardé et relu avec succès")
            return 0
        else:
            print("\n❌ Test échoué !")
            print("   Vérifiez les erreurs ci-dessus")
            return 1
            
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu par l'utilisateur")
        exit_code = 1
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        exit_code = 1
    
    sys.exit(exit_code)
