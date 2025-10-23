"""
Fonctions de test pour les procédures Snowpark.

Ce module contient les fonctions de test pour valider
le bon fonctionnement des procédures Snowpark.
"""

from snowflake.snowpark import Session
from .read_program import read_program_simple
from .list_programs import list_programs_simple
from .program_exists import program_exists_simple


def test_simple_procedures(session: Session) -> None:
    """
    Teste les procédures simplifiées.
    
    Args:
        session: Session Snowpark active
    """
    print("🧪 Test des procédures Snowpark simplifiées...")
    
    try:
        # Test de la procédure LIST_PROGRAMS
        print("   Test de LIST_PROGRAMS...")
        programs_result = list_programs_simple(session)
        
        if "error" in programs_result:
            print(f"   ❌ Erreur LIST_PROGRAMS: {programs_result['error']}")
        else:
            print(f"   ✅ LIST_PROGRAMS: {programs_result['total_count']} programmes trouvés")
        
        # Test de la procédure PROGRAM_EXISTS
        print("   Test de PROGRAM_EXISTS...")
        exists_result = program_exists_simple(session, 1)
        print(f"   ✅ PROGRAM_EXISTS(1): {exists_result}")
        
        # Test de la procédure READ_PROGRAM si un programme existe
        if exists_result:
            print("   Test de READ_PROGRAM...")
            program_result = read_program_simple(session, 1)
            
            if "error" in program_result:
                print(f"   ❌ Erreur READ_PROGRAM: {program_result['error']}")
            else:
                metadata = program_result.get("metadata", {})
                print(f"   ✅ READ_PROGRAM: Programme {metadata.get('program_id')} lu avec succès")
                print(f"      - Structures: {metadata.get('structures_count')}")
                print(f"      - Conditions: {metadata.get('conditions_count')}")
                print(f"      - Exclusions: {metadata.get('exclusions_count')}")
        
        print("✅ Tests des procédures simplifiées terminés")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
