#!/usr/bin/env python3
"""
Script pour créer les tables principales (PROGRAMS, STRUCTURES, CONDITIONS, EXCLUSIONS) 
dans Snowflake et tester qu'elles fonctionnent correctement.
"""

import os
import sys
from pathlib import Path
import snowflake.connector

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

def create_all_tables():
    """Crée toutes les tables principales dans Snowflake"""
    print("🏗️  Création des tables principales...")
    
    try:
        # Connexion à Snowflake
        conn = snowflake.connector.connect(
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
            database=os.getenv('SNOWFLAKE_DATABASE'),
            schema=os.getenv('SNOWFLAKE_SCHEMA'),
            role=os.getenv('SNOWFLAKE_ROLE'),
        )
        
        cursor = conn.cursor()
        
        # Définir les tables à créer
        tables = [
            ('PROGRAMS', '''
                CREATE TABLE PROGRAMS (
                  PROGRAM_ID             STRING          PRIMARY KEY,
                  REPROG_TITLE           STRING          NOT NULL,
                  REPROG_UW_DEPARTMENT_LOB_CD STRING     NOT NULL,
                  CREATED_AT             STRING,
                  UPDATED_AT             STRING,
                  PAYLOAD                STRING
                )
            '''),
            ('STRUCTURES', '''
                CREATE TABLE STRUCTURES (
                  PROGRAM_ID                 STRING       NOT NULL,
                  INSPER_ID_PRE              NUMBER       NOT NULL,
                  INSPER_CONTRACT_ORDER      NUMBER,
                  TYPE_OF_PARTICIPATION_CD   STRING,
                  INSPER_PREDECESSOR_TITLE   STRING,
                  INSPER_CLAIM_BASIS_CD      STRING,
                  INSPER_EFFECTIVE_DATE      TIMESTAMP_NTZ,
                  INSPER_EXPIRY_DATE         TIMESTAMP_NTZ,
                  PAYLOAD                    STRING,
                  PRIMARY KEY (PROGRAM_ID, INSPER_ID_PRE)
                )
            '''),
            ('CONDITIONS', '''
                CREATE TABLE CONDITIONS (
                  PROGRAM_ID               STRING     NOT NULL,
                  INSPER_ID_PRE            NUMBER     NOT NULL,
                  BUSCL_ID_PRE             NUMBER     NOT NULL,
                  SIGNED_SHARE_PCT         FLOAT,
                  INCLUDES_HULL            BOOLEAN,
                  INCLUDES_LIABILITY       BOOLEAN,
                  PAYLOAD                  STRING,
                  PRIMARY KEY (PROGRAM_ID, BUSCL_ID_PRE)
                )
            '''),
            ('EXCLUSIONS', '''
                CREATE TABLE EXCLUSIONS (
                  PROGRAM_ID             STRING     NOT NULL,
                  EXCL_REASON            STRING,
                  PAYLOAD                STRING
                )
            ''')
        ]
        
        # Créer chaque table
        for table_name, ddl in tables:
            print(f"   Création de la table {table_name}...")
            
            # Supprimer la table si elle existe
            cursor.execute(f'DROP TABLE IF EXISTS {table_name}')
            
            # Créer la table
            cursor.execute(ddl)
            print(f"   ✅ Table {table_name} créée avec succès !")
        
        # Vérifier que toutes les tables ont été créées
        cursor.execute('SHOW TABLES IN SCHEMA')
        tables_result = cursor.fetchall()
        created_tables = [table[1] for table in tables_result]
        
        expected_tables = ['PROGRAMS', 'STRUCTURES', 'CONDITIONS', 'EXCLUSIONS']
        missing_tables = [t for t in expected_tables if t not in created_tables]
        
        if not missing_tables:
            print(f"\n✅ Toutes les tables ont été créées avec succès !")
            print(f"📁 Tables créées: {', '.join(created_tables)}")
            
            # Afficher la structure de chaque table
            for table_name in expected_tables:
                print(f"\n📋 Structure de la table {table_name}:")
                cursor.execute(f'DESCRIBE TABLE {table_name}')
                columns = cursor.fetchall()
                for col in columns:
                    print(f"   - {col[0]}: {col[1]}")
        else:
            print(f"❌ Erreur: Tables manquantes: {', '.join(missing_tables)}")
            
        cursor.close()
        conn.close()
        
        return len(missing_tables) == 0
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables: {e}")
        return False

def test_all_tables():
    """Teste que toutes les tables fonctionnent correctement"""
    print("\n🧪 Test de toutes les tables...")
    
    try:
        # Connexion à Snowflake
        conn = snowflake.connector.connect(
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
            database=os.getenv('SNOWFLAKE_DATABASE'),
            schema=os.getenv('SNOWFLAKE_SCHEMA'),
            role=os.getenv('SNOWFLAKE_ROLE'),
        )
        
        cursor = conn.cursor()
        
        # Test de la table PROGRAMS
        print("   Test de la table PROGRAMS...")
        cursor.execute('''
            INSERT INTO PROGRAMS (PROGRAM_ID, REPROG_TITLE, REPROG_UW_DEPARTMENT_LOB_CD, CREATED_AT, UPDATED_AT, PAYLOAD)
            VALUES ('test-programs-123', 'Test Program', 'AVIATION', '2024-01-01 10:00:00', '2024-01-01 10:00:00', '{"test": "programs"}')
        ''')
        
        cursor.execute('SELECT COUNT(*) FROM PROGRAMS WHERE PROGRAM_ID = %s', ('test-programs-123',))
        count = cursor.fetchone()[0]
        if count > 0:
            print("   ✅ Table PROGRAMS: OK")
        else:
            print("   ❌ Table PROGRAMS: Erreur")
        
        # Test de la table STRUCTURES
        print("   Test de la table STRUCTURES...")
        cursor.execute('''
            INSERT INTO STRUCTURES (PROGRAM_ID, INSPER_ID_PRE, INSPER_CONTRACT_ORDER, TYPE_OF_PARTICIPATION_CD, INSPER_PREDECESSOR_TITLE, INSPER_CLAIM_BASIS_CD, INSPER_EFFECTIVE_DATE, INSPER_EXPIRY_DATE, PAYLOAD)
            VALUES ('test-programs-123', 1, 1, 'QUOTA', 'Test Predecessor', 'OCCURRENCE', '2024-01-01 00:00:00', '2024-12-31 23:59:59', '{"test": "structures"}')
        ''')
        
        cursor.execute('SELECT COUNT(*) FROM STRUCTURES WHERE PROGRAM_ID = %s AND INSPER_ID_PRE = %s', ('test-programs-123', 1))
        count = cursor.fetchone()[0]
        if count > 0:
            print("   ✅ Table STRUCTURES: OK")
        else:
            print("   ❌ Table STRUCTURES: Erreur")
        
        # Test de la table CONDITIONS
        print("   Test de la table CONDITIONS...")
        cursor.execute('''
            INSERT INTO CONDITIONS (PROGRAM_ID, INSPER_ID_PRE, BUSCL_ID_PRE, SIGNED_SHARE_PCT, INCLUDES_HULL, INCLUDES_LIABILITY, PAYLOAD)
            VALUES ('test-programs-123', 1, 1, 50.0, TRUE, FALSE, '{"test": "conditions"}')
        ''')
        
        cursor.execute('SELECT COUNT(*) FROM CONDITIONS WHERE PROGRAM_ID = %s AND BUSCL_ID_PRE = %s', ('test-programs-123', 1))
        count = cursor.fetchone()[0]
        if count > 0:
            print("   ✅ Table CONDITIONS: OK")
        else:
            print("   ❌ Table CONDITIONS: Erreur")
        
        # Test de la table EXCLUSIONS
        print("   Test de la table EXCLUSIONS...")
        cursor.execute('''
            INSERT INTO EXCLUSIONS (PROGRAM_ID, EXCL_REASON, PAYLOAD)
            VALUES ('test-programs-123', 'Test Exclusion', '{"test": "exclusions"}')
        ''')
        
        cursor.execute('SELECT COUNT(*) FROM EXCLUSIONS WHERE PROGRAM_ID = %s', ('test-programs-123',))
        count = cursor.fetchone()[0]
        if count > 0:
            print("   ✅ Table EXCLUSIONS: OK")
        else:
            print("   ❌ Table EXCLUSIONS: Erreur")
        
        # Nettoyer les données de test
        print("   Nettoyage des données de test...")
        cursor.execute('DELETE FROM EXCLUSIONS WHERE PROGRAM_ID = %s', ('test-programs-123',))
        cursor.execute('DELETE FROM CONDITIONS WHERE PROGRAM_ID = %s', ('test-programs-123',))
        cursor.execute('DELETE FROM STRUCTURES WHERE PROGRAM_ID = %s', ('test-programs-123',))
        cursor.execute('DELETE FROM PROGRAMS WHERE PROGRAM_ID = %s', ('test-programs-123',))
        print("   ✅ Données de test supprimées")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Script de création et test des tables principales")
    print("=" * 60)
    
    # Charger la configuration
    load_config()
    
    # Créer toutes les tables
    if create_all_tables():
        # Tester toutes les tables
        if test_all_tables():
            print("\n🎉 SUCCÈS ! Toutes les tables sont opérationnelles !")
            print("\n✅ Tables créées et testées:")
            print("   - PROGRAMS: Table principale des programmes")
            print("   - STRUCTURES: Structures de réassurance")
            print("   - CONDITIONS: Conditions de réassurance")
            print("   - EXCLUSIONS: Exclusions de réassurance")
            print("\n🚀 Vous pouvez maintenant utiliser ces tables pour vos programmes.")
        else:
            print("\n❌ Échec du test des tables")
    else:
        print("\n❌ Échec de la création des tables")

if __name__ == "__main__":
    main()
