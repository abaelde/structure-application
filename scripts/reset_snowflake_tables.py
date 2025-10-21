#!/usr/bin/env python3
"""
Script simple pour supprimer et recréer toutes les tables Snowflake.

Pas de migration, pas de complexité - on supprime tout et on recrée.
"""

import sys
import os
from pathlib import Path

# Ajouter le chemin du projet
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import snowflake.connector


def load_snowflake_config():
    """Charge la configuration Snowflake depuis le fichier snowflake_config.env"""
    config_file = Path(__file__).parent.parent / "snowflake_config.env"
    config = {}

    if config_file.exists():
        with open(config_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    config[key] = value
    else:
        raise FileNotFoundError(
            f"Fichier de configuration Snowflake non trouvé: {config_file}"
        )

    return {
        "account": config.get("SNOWFLAKE_ACCOUNT"),
        "user": config.get("SNOWFLAKE_USER"),
        "password": config.get("SNOWFLAKE_PASSWORD"),
        "warehouse": config.get("SNOWFLAKE_WAREHOUSE"),
        "database": config.get("SNOWFLAKE_DATABASE"),
        "schema": config.get("SNOWFLAKE_SCHEMA"),
        "role": config.get("SNOWFLAKE_ROLE"),
    }


def reset_snowflake_tables():
    """Supprime et recrée toutes les tables Snowflake"""
    print("🗑️  Suppression et recréation des tables Snowflake")
    print("=" * 60)

    config = load_snowflake_config()
    db = config["database"]
    schema = config["schema"]

    print(f"🔗 Connexion à Snowflake: {config['account']}")
    print(f"📊 Base: {db}.{schema}")

    cnx = snowflake.connector.connect(**config)
    cur = cnx.cursor()

    try:
        # 1. Supprimer TOUTES les tables existantes
        print("\n🗑️  Suppression de toutes les tables existantes...")

        # Récupérer la liste de toutes les tables
        cur.execute(f'SHOW TABLES IN SCHEMA "{db}"."{schema}"')
        tables = cur.fetchall()

        print(f"   📊 {len(tables)} table(s) trouvée(s)")

        for table_info in tables:
            table_name = table_info[1]  # Le nom de la table est dans la 2ème colonne
            try:
                cur.execute(f'DROP TABLE IF EXISTS "{db}"."{schema}"."{table_name}"')
                print(f"   ✅ Table {table_name} supprimée")
            except Exception as e:
                print(f"   ⚠️  Erreur suppression {table_name}: {e}")

        # 2. Recréer les tables avec la nouvelle structure (auto-increment)
        print("\n🏗️  Création des nouvelles tables...")

        # Lire le DDL corrigé
        ddl_file = Path(__file__).parent / "correct_snowflake_ddl.sql"
        with open(ddl_file, "r") as f:
            ddl_content = f.read()

        # Diviser le DDL en instructions individuelles
        statements = [stmt.strip() for stmt in ddl_content.split(";") if stmt.strip()]

        for statement in statements:
            if statement:
                # Remplacer les noms de tables par les noms qualifiés
                statement = statement.replace(
                    "CREATE TABLE PROGRAMS",
                    f'CREATE TABLE "{db}"."{schema}"."PROGRAMS"',
                )
                statement = statement.replace(
                    "CREATE TABLE STRUCTURES",
                    f'CREATE TABLE "{db}"."{schema}"."STRUCTURES"',
                )
                statement = statement.replace(
                    "CREATE TABLE CONDITIONS",
                    f'CREATE TABLE "{db}"."{schema}"."CONDITIONS"',
                )
                statement = statement.replace(
                    "CREATE TABLE RP_GLOBAL_EXCLUSION",
                    f'CREATE TABLE "{db}"."{schema}"."RP_GLOBAL_EXCLUSION"',
                )

                cur.execute(statement)

        print(
            "   ✅ Toutes les tables créées avec le DDL généré (modifié pour auto-increment)"
        )

        # 3. Créer des index pour les performances
        print("\n📊 Création des index...")

        indexes = [
            f'CREATE INDEX IDX_PROGRAMS_TITLE ON "{db}"."{schema}"."PROGRAMS"(TITLE)',
            f'CREATE INDEX IDX_STRUCTURES_PROGRAM_ID ON "{db}"."{schema}"."STRUCTURES"(PROGRAM_ID)',
            f'CREATE INDEX IDX_CONDITIONS_PROGRAM_ID ON "{db}"."{schema}"."CONDITIONS"(PROGRAM_ID)',
            f'CREATE INDEX IDX_RP_GLOBAL_EXCLUSION_RP_ID ON "{db}"."{schema}"."RP_GLOBAL_EXCLUSION"(RP_ID)',
        ]

        for index_sql in indexes:
            try:
                cur.execute(index_sql)
                print(f"   ✅ Index créé")
            except Exception as e:
                print(f"   ⚠️  Erreur création index: {e}")

        cnx.commit()
        print("\n✅ Toutes les tables ont été recréées avec succès !")
        print(
            "💡 Les nouveaux programmes auront maintenant des IDs uniques automatiques."
        )

    except Exception as e:
        print(f"❌ Erreur: {e}")
        cnx.rollback()
        raise
    finally:
        cur.close()
        cnx.close()


def main():
    print("🔄 Reset complet des tables Snowflake")
    print("=" * 60)

    try:
        reset_snowflake_tables()

    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
