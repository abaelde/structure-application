#!/usr/bin/env python3
"""
Test simple de Snowpark sans procédures stockées.

Ce script teste les fonctionnalités de base de Snowpark
sans créer de procédures stockées permanentes.
"""

import sys
import json
from pathlib import Path

# Ajouter le répertoire racine au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from snowflake_utils import get_snowpark_session, close_snowpark_session
from snowflake.snowpark.functions import col


def test_basic_snowpark():
    """Test des fonctionnalités de base de Snowpark."""
    print("🧪 Test simple de Snowpark")
    print("=" * 30)
    
    try:
        # Obtenir une session
        session = get_snowpark_session()
        print("✅ Session Snowpark obtenue")
        
        # Test 1: Requête simple
        print("\n1. Test de requête simple...")
        result = session.sql("SELECT CURRENT_VERSION() as version, CURRENT_DATABASE() as database, CURRENT_SCHEMA() as schema").collect()
        print(f"   Version: {result[0]['VERSION']}")
        print(f"   Database: {result[0]['DATABASE']}")
        print(f"   Schema: {result[0]['SCHEMA']}")
        
        # Test 2: Vérifier les tables existantes
        print("\n2. Test de liste des tables...")
        tables_result = session.sql("SHOW TABLES").collect()
        print(f"   {len(tables_result)} tables trouvées")
        
        # Afficher les premières tables
        for i, table in enumerate(tables_result[:5]):
            print(f"   - {table['name']}")
        
        # Test 3: Vérifier si les tables de programmes existent
        print("\n3. Test des tables de programmes...")
        program_tables = ["REINSURANCE_PROGRAM", "RP_STRUCTURES", "RP_CONDITIONS", "RP_GLOBAL_EXCLUSION"]
        
        for table_name in program_tables:
            try:
                count_result = session.sql(f"SELECT COUNT(*) as count FROM {table_name}").collect()
                count = count_result[0]['COUNT']
                print(f"   ✅ {table_name}: {count} enregistrements")
            except Exception as e:
                print(f"   ❌ {table_name}: Erreur - {e}")
        
        # Test 4: Lire un programme directement avec Snowpark
        print("\n4. Test de lecture directe avec Snowpark...")
        try:
            # Essayer de lire le premier programme
            program_df = session.table("REINSURANCE_PROGRAM").limit(1).to_pandas()
            
            if not program_df.empty:
                program = program_df.iloc[0]
                program_id = program['REINSURANCE_PROGRAM_ID']
                title = program['TITLE']
                print(f"   ✅ Programme trouvé: {title} (ID: {program_id})")
                
                # Lire les structures pour ce programme
                structures_df = session.table("RP_STRUCTURES").filter(
                    col("REINSURANCE_PROGRAM_ID") == int(program_id)
                ).to_pandas()
                
                print(f"   ✅ Structures: {len(structures_df)} trouvées")
                
                # Lire les conditions pour ce programme
                conditions_df = session.table("RP_CONDITIONS").filter(
                    col("REINSURANCE_PROGRAM_ID") == int(program_id)
                ).to_pandas()
                
                print(f"   ✅ Conditions: {len(conditions_df)} trouvées")
                
            else:
                print("   ⚠️  Aucun programme trouvé")
                
        except Exception as e:
            print(f"   ❌ Erreur lors de la lecture: {e}")
        
        print("\n✅ Tests Snowpark de base terminés avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        return False
    
    finally:
        close_snowpark_session()


def main():
    """Fonction principale."""
    success = test_basic_snowpark()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
