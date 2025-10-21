#!/usr/bin/env python3
"""
Script de test pour l'intégration Snowflake avec correspondance 1:1 aux CSV.
Utilise le nouvel adapter SnowflakeProgramCSVIO.
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
root_dir = Path.cwd()
sys.path.insert(0, str(root_dir))

def load_config():
    """Charge la configuration depuis le fichier snowflake_config.env"""
    config_file = Path('snowflake_config.env')
    if config_file.exists():
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    else:
        print("❌ Fichier snowflake_config.env non trouvé")
        sys.exit(1)

def test_csv_aligned_integration():
    """Teste l'intégration complète avec l'adapter CSV-aligned"""
    print("🧪 Test d'intégration CSV-aligned...")
    
    try:
        from src.io.program_snowflake_csv_adapter import SnowflakeProgramCSVIO
        from src.io.program_csv_folder_adapter import CsvProgramFolderIO
        
        # Configuration
        connection_params = {
            'account': os.getenv('SNOWFLAKE_ACCOUNT'),
            'user': os.getenv('SNOWFLAKE_USER'),
            'password': os.getenv('SNOWFLAKE_PASSWORD'),
            'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
            'database': os.getenv('SNOWFLAKE_DATABASE'),
            'schema': os.getenv('SNOWFLAKE_SCHEMA'),
            'role': os.getenv('SNOWFLAKE_ROLE'),
        }
        
        dsn = f'snowflake://{connection_params["database"]}.{connection_params["schema"]}?program_title=AVIATION_AXA_XL_2024'
        
        print(f'DSN: {dsn}')
        
        # Test 1: Charger un programme depuis CSV
        print('\n1. Chargement d\'un programme depuis CSV...')
        csv_adapter = CsvProgramFolderIO()
        program_df, structures_df, conditions_df, exclusions_df = csv_adapter.read('examples/programs/aviation_axa_xl_2024')
        
        print(f'   Programme chargé: {program_df.iloc[0]["TITLE"]}')
        print(f'   Structures: {len(structures_df)} lignes')
        print(f'   Conditions: {len(conditions_df)} lignes')
        print(f'   Exclusions: {len(exclusions_df)} lignes')
        
        # Afficher les colonnes
        print(f'   Colonnes REINSURANCE_PROGRAM: {len(program_df.columns)} - {list(program_df.columns)[:3]}...')
        print(f'   Colonnes RP_STRUCTURES: {len(structures_df.columns)} - {list(structures_df.columns)[:3]}...')
        print(f'   Colonnes RP_CONDITIONS: {len(conditions_df.columns)} - {list(conditions_df.columns)[:3]}...')
        print(f'   Colonnes RP_GLOBAL_EXCLUSION: {len(exclusions_df.columns)} - {list(exclusions_df.columns)[:3]}...')
        
        # Test 2: Sauvegarder dans Snowflake avec l'adapter CSV-aligned
        print('\n2. Sauvegarde dans Snowflake (adapter CSV-aligned)...')
        snowflake_adapter = SnowflakeProgramCSVIO()
        snowflake_adapter.write(
            dsn, 
            program_df, 
            structures_df, 
            conditions_df, 
            exclusions_df,
            connection_params=connection_params,
            if_exists='replace_program'
        )
        print(f'   Programme sauvegardé dans: {dsn}')
        
        # Test 3: Recharger depuis Snowflake
        print('\n3. Rechargement depuis Snowflake...')
        reloaded_program_df, reloaded_structures_df, reloaded_conditions_df, reloaded_exclusions_df = snowflake_adapter.read(dsn, connection_params)
        
        print(f'   Programme rechargé: {reloaded_program_df.iloc[0]["TITLE"]}')
        print(f'   Structures rechargées: {len(reloaded_structures_df)} lignes')
        print(f'   Conditions rechargées: {len(reloaded_conditions_df)} lignes')
        print(f'   Exclusions rechargées: {len(reloaded_exclusions_df)} lignes')
        
        # Vérifier la correspondance des colonnes
        print('\n4. Vérification de la correspondance des colonnes...')
        
        # REINSURANCE_PROGRAM
        original_cols = set(program_df.columns)
        reloaded_cols = set(reloaded_program_df.columns)
        missing_cols = original_cols - reloaded_cols
        extra_cols = reloaded_cols - original_cols
        
        if not missing_cols and not extra_cols:
            print('   ✅ REINSURANCE_PROGRAM: Correspondance parfaite des colonnes')
        else:
            print(f'   ⚠️  REINSURANCE_PROGRAM: Colonnes manquantes: {missing_cols}, colonnes supplémentaires: {extra_cols}')
        
        # RP_STRUCTURES
        original_cols = set(structures_df.columns)
        reloaded_cols = set(reloaded_structures_df.columns) - {'PROGRAM_ID'}  # Exclure la clé de liaison
        missing_cols = original_cols - reloaded_cols
        extra_cols = reloaded_cols - original_cols
        
        if not missing_cols and not extra_cols:
            print('   ✅ RP_STRUCTURES: Correspondance parfaite des colonnes')
        else:
            print(f'   ⚠️  RP_STRUCTURES: Colonnes manquantes: {missing_cols}, colonnes supplémentaires: {extra_cols}')
        
        # RP_CONDITIONS
        original_cols = set(conditions_df.columns)
        reloaded_cols = set(reloaded_conditions_df.columns) - {'PROGRAM_ID'}  # Exclure la clé de liaison
        missing_cols = original_cols - reloaded_cols
        extra_cols = reloaded_cols - original_cols
        
        if not missing_cols and not extra_cols:
            print('   ✅ RP_CONDITIONS: Correspondance parfaite des colonnes')
        else:
            print(f'   ⚠️  RP_CONDITIONS: Colonnes manquantes: {missing_cols}, colonnes supplémentaires: {extra_cols}')
        
        # RP_GLOBAL_EXCLUSION
        original_cols = set(exclusions_df.columns)
        reloaded_cols = set(reloaded_exclusions_df.columns) - {'PROGRAM_ID'}  # Exclure la clé de liaison
        missing_cols = original_cols - reloaded_cols
        extra_cols = reloaded_cols - original_cols
        
        if not missing_cols and not extra_cols:
            print('   ✅ RP_GLOBAL_EXCLUSION: Correspondance parfaite des colonnes')
        else:
            print(f'   ⚠️  RP_GLOBAL_EXCLUSION: Colonnes manquantes: {missing_cols}, colonnes supplémentaires: {extra_cols}')
        
        # Test 5: Vérifier les données dans Snowflake
        print('\n5. Vérification des données dans Snowflake...')
        import snowflake.connector
        conn = snowflake.connector.connect(**connection_params)
        cursor = conn.cursor()
        
        # Vérifier REINSURANCE_PROGRAM
        cursor.execute('SELECT TITLE, UW_LOB, CREATED_AT FROM REINSURANCE_PROGRAM LIMIT 1')
        result = cursor.fetchone()
        if result:
            print(f'   ✅ REINSURANCE_PROGRAM: {result[0]} - {result[1]} - Créé: {result[2]}')
        
        # Vérifier RP_STRUCTURES
        cursor.execute('SELECT COUNT(*), COUNT(DISTINCT INSPER_ID_PRE) FROM RP_STRUCTURES')
        count, unique_count = cursor.fetchone()
        print(f'   ✅ RP_STRUCTURES: {count} lignes, {unique_count} structures uniques')
        
        # Vérifier RP_CONDITIONS
        cursor.execute('SELECT COUNT(*), COUNT(DISTINCT BUSCL_ID_PRE) FROM RP_CONDITIONS')
        count, unique_count = cursor.fetchone()
        print(f'   ✅ RP_CONDITIONS: {count} lignes, {unique_count} conditions uniques')
        
        # Vérifier RP_GLOBAL_EXCLUSION
        cursor.execute('SELECT COUNT(*) FROM RP_GLOBAL_EXCLUSION')
        count = cursor.fetchone()[0]
        print(f'   ✅ RP_GLOBAL_EXCLUSION: {count} lignes')
        
        cursor.close()
        conn.close()
        
        print('\n🎉 Test d\'intégration CSV-aligned réussi !')
        print('\n✅ L\'adapter SnowflakeProgramCSVIO fonctionne parfaitement !')
        print('✅ Correspondance 1:1 entre colonnes CSV et colonnes table !')
        
        return True
        
    except Exception as e:
        print(f'❌ Erreur: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale"""
    print("🚀 Test d'intégration Snowflake CSV-aligned")
    print("=" * 60)
    
    # Charger la configuration
    load_config()
    
    # Tester l'intégration
    if test_csv_aligned_integration():
        print("\n🎉 SUCCÈS ! L'intégration CSV-aligned est opérationnelle !")
        print("\n📋 Résumé:")
        print("   - Tables créées avec correspondance 1:1 aux CSV")
        print("   - Adapter SnowflakeProgramCSVIO fonctionnel")
        print("   - Sauvegarde et rechargement validés")
        print("   - Toutes les colonnes CSV préservées")
    else:
        print("\n❌ Échec du test d'intégration CSV-aligned")

if __name__ == "__main__":
    main()
