#!/usr/bin/env python3
"""
Script pour créer les tables Snowflake.
Gère les erreurs de configuration et propose des solutions.
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

def load_config_file():
    """Charge la configuration depuis un fichier .env si disponible."""
    config_file = Path(__file__).parent.parent / "snowflake_config.env"
    if config_file.exists():
        print(f"📁 Chargement de la configuration depuis: {config_file}")
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        return True
    return False

def get_connection_params():
    """Récupère les paramètres de connexion depuis les variables d'environnement."""
    return {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database": os.getenv("SNOWFLAKE_DATABASE", "MYDB"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "MYSCHEMA"),
        "role": os.getenv("SNOWFLAKE_ROLE"),
    }

def check_configuration():
    """Vérifie la configuration et affiche les paramètres manquants."""
    params = get_connection_params()
    missing = []
    
    required_params = ["account", "user", "password", "warehouse"]
    for param in required_params:
        if not params.get(param):
            missing.append(param)
    
    print("🔍 Vérification de la configuration Snowflake...")
    print(f"   Account: {'✅' if params['account'] else '❌'} {params['account'] or 'MANQUANT'}")
    print(f"   User: {'✅' if params['user'] else '❌'} {params['user'] or 'MANQUANT'}")
    print(f"   Password: {'✅' if params['password'] else '❌'} {'***' if params['password'] else 'MANQUANT'}")
    print(f"   Warehouse: {'✅' if params['warehouse'] else '❌'} {params['warehouse'] or 'MANQUANT'}")
    print(f"   Database: {params['database']}")
    print(f"   Schema: {params['schema']}")
    print(f"   Role: {'✅' if params['role'] else '⚠️  (optionnel)'} {params['role'] or 'Non défini'}")
    
    if missing:
        print(f"\n❌ Paramètres manquants: {', '.join(missing)}")
        print("\n💡 Solutions:")
        print("   1. Définir les variables d'environnement:")
        for param in missing:
            print(f"      export SNOWFLAKE_{param.upper()}=votre_valeur")
        print("\n   2. Ou créer un fichier snowflake_config.env et le sourcer:")
        print("      source snowflake_config.env")
        print("\n   3. Ou modifier directement ce script avec vos valeurs")
        return False
    
    print("\n✅ Configuration complète !")
    return True

def read_ddl_script():
    """Lit le script DDL depuis le fichier SQL."""
    ddl_file = Path(__file__).parent / "setup_snowflake_tables_simple.sql"
    if not ddl_file.exists():
        raise FileNotFoundError(f"Script DDL non trouvé: {ddl_file}")
    
    with open(ddl_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return content

def execute_ddl():
    """Exécute le script DDL dans Snowflake."""
    try:
        import snowflake.connector
        from snowflake.connector import ProgrammingError
        
        params = get_connection_params()
        ddl_content = read_ddl_script()
        
        print(f"\n🚀 Connexion à Snowflake...")
        print(f"   Account: {params['account']}")
        print(f"   Database: {params['database']}")
        print(f"   Schema: {params['schema']}")
        
        # Connexion (sans database/schema pour commencer)
        conn_params = {k: v for k, v in params.items() if k not in ['database', 'schema']}
        conn = snowflake.connector.connect(**conn_params)
        cursor = conn.cursor()
        
        print("✅ Connexion réussie !")
        
        # Utiliser la database existante et créer le schema
        print(f"\n🏗️  Utilisation de la database {params['database']} et création du schema {params['schema']}...")
        
        try:
            cursor.execute(f"USE DATABASE {params['database']}")
            print(f"   ✅ Database {params['database']} sélectionnée")
        except Exception as e:
            print(f"   ❌ Erreur avec database {params['database']}: {e}")
            return False
        
        try:
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {params['schema']}")
            print(f"   ✅ Schema {params['schema']} créé")
        except Exception as e:
            print(f"   ⚠️  Schema {params['schema']}: {e}")
        
        # Maintenant se connecter avec la database et le schema
        cursor.close()
        conn.close()
        
        # Reconnexion avec database et schema
        conn = snowflake.connector.connect(**params)
        cursor = conn.cursor()
        
        # Exécuter le DDL
        print("\n📝 Exécution du script DDL...")
        
        # Diviser le script en statements individuels
        statements = [stmt.strip() for stmt in ddl_content.split(';') if stmt.strip()]
        
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements, 1):
            if not statement or statement.startswith('--'):
                continue
                
            try:
                print(f"   [{i:2d}/{len(statements)}] Exécution...")
                cursor.execute(statement)
                success_count += 1
                
                # Afficher le type d'opération
                if statement.upper().startswith('CREATE SCHEMA'):
                    print(f"      ✅ Schéma créé")
                elif statement.upper().startswith('CREATE TABLE'):
                    table_name = statement.split()[2].split('.')[-1]
                    print(f"      ✅ Table {table_name} créée")
                elif statement.upper().startswith('CREATE INDEX'):
                    index_name = statement.split()[4]
                    print(f"      ✅ Index {index_name} créé")
                elif statement.upper().startswith('CREATE OR REPLACE VIEW'):
                    view_name = statement.split()[4].split('.')[-1]
                    print(f"      ✅ Vue {view_name} créée")
                elif statement.upper().startswith('COMMENT ON TABLE'):
                    print(f"      ✅ Commentaire ajouté")
                else:
                    print(f"      ✅ Statement exécuté")
                    
            except ProgrammingError as e:
                error_count += 1
                # Ignorer les erreurs d'index sur des tables non existantes
                if "does not exist" in str(e) and "INDEX" in statement.upper():
                    print(f"      ⚠️  Index ignoré (table pas encore créée): {statement.split()[4] if 'INDEX' in statement.upper() else 'N/A'}")
                else:
                    print(f"      ❌ Erreur: {e}")
                # Continuer avec les autres statements
                continue
            except Exception as e:
                error_count += 1
                print(f"      ❌ Erreur inattendue: {e}")
                continue
        
        print(f"\n📊 Résumé:")
        print(f"   ✅ Succès: {success_count}")
        print(f"   ❌ Erreurs: {error_count}")
        
        if error_count == 0:
            print("\n🎉 Toutes les tables ont été créées avec succès !")
        else:
            print(f"\n⚠️  {error_count} erreur(s) détectée(s). Vérifiez les messages ci-dessus.")
        
        # Fermer la connexion
        cursor.close()
        conn.close()
        print("🔌 Connexion fermée.")
        
        return error_count == 0
        
    except ImportError:
        print("❌ snowflake-connector-python non installé !")
        print("   Exécutez: uv add snowflake-connector-python")
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print("\n💡 Vérifiez:")
        print("   - Vos paramètres de connexion")
        print("   - Votre accès réseau à Snowflake")
        print("   - Les permissions de votre utilisateur")
        return False

def main():
    """Fonction principale."""
    print("🏗️  Création des tables Snowflake")
    print("=" * 50)
    
    # Essayer de charger la configuration depuis un fichier
    config_loaded = load_config_file()
    
    # Vérifier la configuration
    if not check_configuration():
        print("\n❌ Configuration incomplète. Arrêt du script.")
        if not config_loaded:
            print("\n💡 Pour configurer rapidement:")
            print("   1. Éditez le fichier snowflake_config.env avec vos vraies valeurs")
            print("   2. Relancez ce script")
        return False
    
    # Exécuter le DDL
    success = execute_ddl()
    
    if success:
        print("\n✅ Script terminé avec succès !")
        print("\n🚀 Prochaines étapes:")
        print("   1. Tester l'intégration: python examples/snowflake_integration_example.py")
        print("   2. Migrer vos programmes existants vers Snowflake")
        print("   3. Configurer vos applications pour utiliser Snowflake")
    else:
        print("\n❌ Script terminé avec des erreurs.")
        print("\n🔧 Actions recommandées:")
        print("   1. Vérifiez les messages d'erreur ci-dessus")
        print("   2. Corrigez la configuration si nécessaire")
        print("   3. Relancez le script")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
