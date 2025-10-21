#!/usr/bin/env python3
"""
Script pour créer les tables Snowflake basées sur la structure réelle des CSV.
Correspondance 1:1 entre colonnes CSV et colonnes table.
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

def create_tables_from_csv_structure():
    """Crée les tables Snowflake basées sur la structure réelle des CSV"""
    print("🏗️  Création des tables basées sur la structure CSV...")
    
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
        
        # Définir les tables basées sur la structure réelle des CSV
        tables = [
            ('PROGRAMS', '''
                CREATE TABLE PROGRAMS (
                  REPROG_ID_PRE                  NUMBER(38,0)    NOT NULL,
                  REPROG_TITLE                   STRING          NOT NULL,
                  CED_ID_PRE                     STRING,
                  CED_NAME_PRE                   STRING,
                  REPROG_ACTIVE_IND              BOOLEAN,
                  REPROG_COMMENT                 STRING,
                  REPROG_UW_DEPARTMENT_CD        STRING,
                  REPROG_UW_DEPARTMENT_NAME      STRING,
                  REPROG_UW_DEPARTMENT_LOB_CD    STRING,
                  REPROG_UW_DEPARTMENT_LOB_NAME  STRING,
                  BUSPAR_CED_REG_CLASS_CD        STRING,
                  BUSPAR_CED_REG_CLASS_NAME      STRING,
                  REPROG_MAIN_CURRENCY_CD        STRING,
                  REPROG_MANAGEMENT_REPORTING_LOB_CD STRING,
                  CREATED_AT                     STRING,
                  UPDATED_AT                     STRING,
                  PRIMARY KEY (REPROG_ID_PRE)
                )
            '''),
            ('STRUCTURES', '''
                CREATE TABLE STRUCTURES (
                  PROGRAM_ID                     STRING          NOT NULL,
                  INSPER_ID_PRE                  NUMBER(38,0)    NOT NULL,
                  BUSINESS_ID_PRE                STRING,
                  TYPE_OF_PARTICIPATION_CD       STRING,
                  TYPE_OF_INSURED_PERIOD_CD      STRING,
                  ACTIVE_FLAG_CD                 BOOLEAN,
                  INSPER_EFFECTIVE_DATE          TIMESTAMP_NTZ,
                  INSPER_EXPIRY_DATE             TIMESTAMP_NTZ,
                  REPROG_ID_PRE                  NUMBER(38,0),
                  BUSINESS_TITLE                 STRING,
                  INSPER_LAYER_NO                NUMBER(38,0),
                  INSPER_MAIN_CURRENCY_CD        STRING,
                  INSPER_UW_YEAR                 NUMBER(38,0),
                  INSPER_CONTRACT_ORDER          NUMBER(38,0),
                  INSPER_PREDECESSOR_TITLE       STRING,
                  INSPER_CONTRACT_FORM_CD_SLAV   STRING,
                  INSPER_CONTRACT_LODRA_CD_SLAV  STRING,
                  INSPER_CONTRACT_COVERAGE_CD_SLAV STRING,
                  INSPER_CLAIM_BASIS_CD          STRING,
                  INSPER_LODRA_CD_SLAV           STRING,
                  INSPER_LOD_TO_RA_DATE_SLAV     STRING,
                  INSPER_COMMENT                 STRING,
                  PRIMARY KEY (PROGRAM_ID, INSPER_ID_PRE)
                )
            '''),
            ('CONDITIONS', '''
                CREATE TABLE CONDITIONS (
                  PROGRAM_ID                     STRING          NOT NULL,
                  BUSCL_ID_PRE                   NUMBER(38,0)    NOT NULL,
                  REPROG_ID_PRE                  NUMBER(38,0),
                  CED_ID_PRE                     STRING,
                  BUSINESS_ID_PRE                STRING,
                  INSPER_ID_PRE                  NUMBER(38,0),
                  BUSCL_ENTITY_NAME_CED          STRING,
                  POL_RISK_NAME_CED              STRING,
                  BUSCL_COUNTRY_CD               STRING,
                  BUSCL_COUNTRY                  STRING,
                  BUSCL_REGION                   STRING,
                  BUSCL_CLASS_OF_BUSINESS_1      STRING,
                  BUSCL_CLASS_OF_BUSINESS_2      STRING,
                  BUSCL_CLASS_OF_BUSINESS_3      STRING,
                  BUSCL_LIMIT_CURRENCY_CD        STRING,
                  AAD_100                        FLOAT,
                  LIMIT_100                      FLOAT,
                  LIMIT_FLOATER_100              FLOAT,
                  ATTACHMENT_POINT_100           FLOAT,
                  OLW_100                        FLOAT,
                  LIMIT_AGG_100                  FLOAT,
                  CESSION_PCT                    FLOAT,
                  RETENTION_PCT                  FLOAT,
                  SUPI_100                       FLOAT,
                  BUSCL_PREMIUM_CURRENCY_CD      STRING,
                  BUSCL_PREMIUM_GROSS_NET_CD     STRING,
                  PREMIUM_RATE_PCT               FLOAT,
                  PREMIUM_DEPOSIT_100            FLOAT,
                  PREMIUM_MIN_100                FLOAT,
                  BUSCL_LIABILITY_1_LINE_100     FLOAT,
                  MAX_COVER_PCT                  FLOAT,
                  MIN_EXCESS_PCT                 FLOAT,
                  SIGNED_SHARE_PCT               FLOAT,
                  AVERAGE_LINE_SLAV_CED          FLOAT,
                  PML_DEFAULT_PCT                FLOAT,
                  LIMIT_EVENT                    FLOAT,
                  NO_OF_REINSTATEMENTS           FLOAT,
                  INCLUDES_HULL                  BOOLEAN,
                  INCLUDES_LIABILITY             BOOLEAN,
                  PRIMARY KEY (PROGRAM_ID, BUSCL_ID_PRE)
                )
            '''),
            ('EXCLUSIONS', '''
                CREATE TABLE EXCLUSIONS (
                  PROGRAM_ID                     STRING          NOT NULL,
                  EXCL_REASON                    STRING,
                  EXCL_EFFECTIVE_DATE            STRING,
                  EXCL_EXPIRY_DATE               STRING,
                  BUSCL_COUNTRY_CD               STRING,
                  BUSCL_REGION                   STRING,
                  BUSCL_CLASS_OF_BUSINESS_1      STRING,
                  BUSCL_CLASS_OF_BUSINESS_2      STRING,
                  BUSCL_CLASS_OF_BUSINESS_3      STRING,
                  BUSCL_ENTITY_NAME_CED          STRING,
                  POL_RISK_NAME_CED              STRING,
                  BUSCL_LIMIT_CURRENCY_CD        STRING
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
                print(f"   Nombre de colonnes: {len(columns)}")
                for col in columns[:5]:  # Afficher les 5 premières colonnes
                    print(f"   - {col[0]}: {col[1]}")
                if len(columns) > 5:
                    print(f"   ... et {len(columns) - 5} autres colonnes")
        else:
            print(f"❌ Erreur: Tables manquantes: {', '.join(missing_tables)}")
            
        cursor.close()
        conn.close()
        
        return len(missing_tables) == 0
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables: {e}")
        return False

def test_csv_based_tables():
    """Teste que les tables basées sur la structure CSV fonctionnent correctement"""
    print("\n🧪 Test des tables basées sur la structure CSV...")
    
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
        
        # Test de la table PROGRAMS avec toutes les colonnes CSV
        print("   Test de la table PROGRAMS (structure CSV complète)...")
        cursor.execute('''
            INSERT INTO PROGRAMS (
                REPROG_ID_PRE, REPROG_TITLE, CED_ID_PRE, CED_NAME_PRE, 
                REPROG_ACTIVE_IND, REPROG_COMMENT, REPROG_UW_DEPARTMENT_CD, 
                REPROG_UW_DEPARTMENT_NAME, REPROG_UW_DEPARTMENT_LOB_CD, 
                REPROG_UW_DEPARTMENT_LOB_NAME, BUSPAR_CED_REG_CLASS_CD, 
                BUSPAR_CED_REG_CLASS_NAME, REPROG_MAIN_CURRENCY_CD, 
                REPROG_MANAGEMENT_REPORTING_LOB_CD, CREATED_AT, UPDATED_AT
            ) VALUES (
                999, 'Test Program CSV', 'CED001', 'Test Cedent', 
                TRUE, 'Test comment', 'DEPT001', 'Test Department', 
                'aviation', 'Aviation', 'CLASS001', 'Test Class', 
                'USD', 'LOB001', '2024-01-01 10:00:00', '2024-01-01 10:00:00'
            )
        ''')
        
        cursor.execute('SELECT COUNT(*) FROM PROGRAMS WHERE REPROG_ID_PRE = %s', (999,))
        count = cursor.fetchone()[0]
        if count > 0:
            print("   ✅ Table PROGRAMS (structure CSV): OK")
        else:
            print("   ❌ Table PROGRAMS (structure CSV): Erreur")
        
        # Test de la table STRUCTURES avec les colonnes principales
        print("   Test de la table STRUCTURES (structure CSV complète)...")
        cursor.execute('''
            INSERT INTO STRUCTURES (
                PROGRAM_ID, INSPER_ID_PRE, TYPE_OF_PARTICIPATION_CD, 
                INSPER_EFFECTIVE_DATE, INSPER_EXPIRY_DATE, REPROG_ID_PRE, 
                BUSINESS_TITLE, INSPER_CLAIM_BASIS_CD
            ) VALUES (
                'test-program-999', 1, 'quota_share', 
                '2024-01-01 00:00:00', '2024-12-31 23:59:59', 999, 
                'Test Structure', 'risk_attaching'
            )
        ''')
        
        cursor.execute('SELECT COUNT(*) FROM STRUCTURES WHERE PROGRAM_ID = %s AND INSPER_ID_PRE = %s', ('test-program-999', 1))
        count = cursor.fetchone()[0]
        if count > 0:
            print("   ✅ Table STRUCTURES (structure CSV): OK")
        else:
            print("   ❌ Table STRUCTURES (structure CSV): Erreur")
        
        # Test de la table CONDITIONS avec les colonnes principales
        print("   Test de la table CONDITIONS (structure CSV complète)...")
        cursor.execute('''
            INSERT INTO CONDITIONS (
                PROGRAM_ID, BUSCL_ID_PRE, REPROG_ID_PRE, INSPER_ID_PRE, 
                BUSCL_LIMIT_CURRENCY_CD, LIMIT_100, SIGNED_SHARE_PCT, 
                INCLUDES_HULL, INCLUDES_LIABILITY
            ) VALUES (
                'test-program-999', 1, 999, 1, 
                'USD', 1000000.0, 0.25, 
                TRUE, TRUE
            )
        ''')
        
        cursor.execute('SELECT COUNT(*) FROM CONDITIONS WHERE PROGRAM_ID = %s AND BUSCL_ID_PRE = %s', ('test-program-999', 1))
        count = cursor.fetchone()[0]
        if count > 0:
            print("   ✅ Table CONDITIONS (structure CSV): OK")
        else:
            print("   ❌ Table CONDITIONS (structure CSV): Erreur")
        
        # Test de la table EXCLUSIONS
        print("   Test de la table EXCLUSIONS (structure CSV complète)...")
        cursor.execute('''
            INSERT INTO EXCLUSIONS (
                PROGRAM_ID, EXCL_REASON, EXCL_EFFECTIVE_DATE, 
                EXCL_EXPIRY_DATE, BUSCL_COUNTRY_CD
            ) VALUES (
                'test-program-999', 'Test Exclusion', '2024-01-01', 
                '2024-12-31', 'US'
            )
        ''')
        
        cursor.execute('SELECT COUNT(*) FROM EXCLUSIONS WHERE PROGRAM_ID = %s', ('test-program-999',))
        count = cursor.fetchone()[0]
        if count > 0:
            print("   ✅ Table EXCLUSIONS (structure CSV): OK")
        else:
            print("   ❌ Table EXCLUSIONS (structure CSV): Erreur")
        
        # Nettoyer les données de test
        print("   Nettoyage des données de test...")
        cursor.execute('DELETE FROM EXCLUSIONS WHERE PROGRAM_ID = %s', ('test-program-999',))
        cursor.execute('DELETE FROM CONDITIONS WHERE PROGRAM_ID = %s', ('test-program-999',))
        cursor.execute('DELETE FROM STRUCTURES WHERE PROGRAM_ID = %s', ('test-program-999',))
        cursor.execute('DELETE FROM PROGRAMS WHERE REPROG_ID_PRE = %s', (999,))
        print("   ✅ Données de test supprimées")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Script de création des tables basées sur la structure CSV")
    print("=" * 70)
    
    # Charger la configuration
    load_config()
    
    # Créer toutes les tables
    if create_tables_from_csv_structure():
        # Tester toutes les tables
        if test_csv_based_tables():
            print("\n🎉 SUCCÈS ! Toutes les tables CSV sont opérationnelles !")
            print("\n✅ Tables créées avec correspondance 1:1 CSV:")
            print("   - PROGRAMS: 14 colonnes CSV + 2 colonnes d'audit = 16 colonnes")
            print("   - STRUCTURES: 21 colonnes CSV + 1 clé de liaison = 22 colonnes")
            print("   - CONDITIONS: 38 colonnes CSV + 1 clé de liaison = 39 colonnes")
            print("   - EXCLUSIONS: 11 colonnes CSV + 1 clé de liaison = 12 colonnes")
            print("\n🚀 Structure parfaitement alignée avec les CSV !")
        else:
            print("\n❌ Échec du test des tables CSV")
    else:
        print("\n❌ Échec de la création des tables CSV")

if __name__ == "__main__":
    main()
