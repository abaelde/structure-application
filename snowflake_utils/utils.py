"""
Utilitaires Snowflake pour la sauvegarde et la gestion des programmes.

Ce module fournit des fonctions utilitaires simplifiées pour travailler
avec Snowflake dans le contexte de l'application.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from .config import SnowflakeConfig


def get_save_config(
    backend: str, program_name: str, output_dir: str = "../programs"
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Retourne la configuration de sauvegarde pour Snowflake.

    Args:
        backend: "snowflake" uniquement
        program_name: Nom du programme
        output_dir: Non utilisé (gardé pour compatibilité)

    Returns:
        Tuple: (output_path, io_kwargs)

    Raises:
        ValueError: Si le backend n'est pas supporté
    """
    if backend == "snowflake":
        config = SnowflakeConfig.load()
        output_path = config.get_dsn(program_name)
        io_kwargs = {"connection_params": config.to_dict()}
        return output_path, io_kwargs

    else:
        raise ValueError(
            f"Backend non supporté: {backend}. Seul 'snowflake' est supporté"
        )


def save_program(
    program, backend: str, program_name: str, output_dir: str = "../programs"
) -> str:
    """
    Sauvegarde un programme dans Snowflake.

    Args:
        program: Objet Program à sauvegarder
        backend: "snowflake" uniquement
        program_name: Nom du programme
        output_dir: Non utilisé (gardé pour compatibilité)

    Returns:
        str: Chemin de destination utilisé pour la sauvegarde

    Raises:
        ValueError: Si le backend n'est pas supporté
        RuntimeError: Si la sauvegarde échoue
    """
    from src.managers import ProgramManager

    output_path, io_kwargs = get_save_config(backend, program_name, output_dir)

    print(f"💾 Sauvegarde du programme '{program_name}'...")
    print(f"   Backend: {backend}")
    print(f"   Destination: {output_path}")

    try:
        manager = ProgramManager(backend=backend)
        manager.save(program, output_path, io_kwargs=io_kwargs)

        print(f"✅ Programme '{program_name}' sauvegardé avec succès !")
        return output_path

    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde: {e}")
        raise RuntimeError(f"Échec de la sauvegarde du programme '{program_name}': {e}")


def test_connection() -> bool:
    """
    Teste la connexion à Snowflake.

    Returns:
        True si la connexion réussit, False sinon
    """
    try:
        import snowflake.connector

        config = SnowflakeConfig.load()
        if not config.validate():
            print("❌ Configuration Snowflake invalide")
            return False

        print(f"🔗 Test de connexion à Snowflake: {config.account}")

        cnx = snowflake.connector.connect(**config.to_dict())
        cur = cnx.cursor()

        # Test simple
        cur.execute("SELECT CURRENT_VERSION()")
        version = cur.fetchone()[0]

        cur.close()
        cnx.close()

        print(f"✅ Connexion réussie ! Version Snowflake: {version}")
        return True

    except Exception as e:
        print(f"❌ Échec de la connexion: {e}")
        return False


def list_programs() -> list:
    """
    Liste tous les programmes dans Snowflake.

    Returns:
        Liste des programmes avec leurs informations
    """
    try:
        import snowflake.connector

        config = SnowflakeConfig.load()
        cnx = snowflake.connector.connect(**config.to_dict())
        cur = cnx.cursor()

        cur.execute(
            f"""
            SELECT REINSURANCE_PROGRAM_ID, TITLE, CREATED_AT, MODIFIED_AT 
            FROM "{config.database}"."{config.schema}"."REINSURANCE_PROGRAM" 
            ORDER BY CREATED_AT DESC
        """
        )

        programs = cur.fetchall()

        cur.close()
        cnx.close()

        return [
            {
                "id": prog[0],
                "title": prog[1],
                "created_at": prog[2],
                "updated_at": prog[3],
            }
            for prog in programs
        ]

    except Exception as e:
        print(f"❌ Erreur lors de la récupération des programmes: {e}")
        return []


def reset_all_tables() -> bool:
    """
    Supprime et recrée toutes les tables Snowflake.

    Cette fonction effectue un reset complet :
    - Supprime toutes les tables existantes
    - Recrée les tables avec la structure correcte (auto-increment)
    - Crée les index pour les performances

    Returns:
        True si le reset réussit, False sinon
    """
    try:
        import snowflake.connector
        from pathlib import Path

        config = SnowflakeConfig.load()
        db = config.database
        schema = config.schema

        print("🗑️  Reset complet des tables Snowflake")
        print(f"🔗 Connexion à Snowflake: {config.account}")
        print(f"📊 Base: {db}.{schema}")

        cnx = snowflake.connector.connect(**config.to_dict())
        cur = cnx.cursor()

        # 1. Supprimer toutes les tables existantes
        print("\n🗑️  Suppression de toutes les tables existantes...")

        # Récupérer toutes les tables du schéma
        cur.execute(f'SHOW TABLES IN SCHEMA "{db}"."{schema}"')
        tables_result = cur.fetchall()

        # Extraire les noms de tables
        tables = [
            row[1] for row in tables_result
        ]  # Le nom de la table est dans la colonne 1

        if not tables:
            print("   ℹ️  Aucune table trouvée dans le schéma")
        else:
            for table in tables:
                try:
                    cur.execute(f'DROP TABLE IF EXISTS "{db}"."{schema}"."{table}"')
                    print(f"   ✅ Table {table} supprimée")
                except Exception as e:
                    print(f"   ⚠️  Erreur suppression {table}: {e}")

        # 2. Recréer les tables avec la nouvelle structure (auto-increment)
        print("\n🏗️  Création des nouvelles tables...")

        # Lire le DDL corrigé
        ddl_file = (
            Path(__file__).parent.parent / "scripts" / "correct_snowflake_ddl.sql"
        )
        with open(ddl_file, "r") as f:
            ddl_content = f.read()

        # Diviser le DDL en instructions individuelles
        statements = [stmt.strip() for stmt in ddl_content.split(";") if stmt.strip()]

        for statement in statements:
            if statement:
                # Remplacer les noms de tables par les noms qualifiés
                statement = statement.replace(
                    "CREATE TABLE REINSURANCE_PROGRAM",
                    f'CREATE TABLE "{db}"."{schema}"."REINSURANCE_PROGRAM"',
                )
                statement = statement.replace(
                    "CREATE TABLE RP_STRUCTURES",
                    f'CREATE TABLE "{db}"."{schema}"."RP_STRUCTURES"',
                )
                statement = statement.replace(
                    "CREATE TABLE RP_CONDITIONS",
                    f'CREATE TABLE "{db}"."{schema}"."RP_CONDITIONS"',
                )
                statement = statement.replace(
                    "CREATE TABLE RP_GLOBAL_EXCLUSION",
                    f'CREATE TABLE "{db}"."{schema}"."RP_GLOBAL_EXCLUSION"',
                )

                cur.execute(statement)

        print("   ✅ Toutes les tables créées avec le DDL corrigé (auto-increment)")

        # 3. (Optionnel) Clustering keys pour filtrage efficace
        print("\n📊 Définition des clés de clustering (optionnel)...")
        cluster_sql = [
            f'ALTER TABLE "{db}"."{schema}"."RP_STRUCTURES" CLUSTER BY (RP_ID)',
            f'ALTER TABLE "{db}"."{schema}"."RP_CONDITIONS" CLUSTER BY (RP_ID)',
            f'ALTER TABLE "{db}"."{schema}"."RP_GLOBAL_EXCLUSION" CLUSTER BY (RP_ID)',
            f'ALTER TABLE "{db}"."{schema}"."RP_STRUCTURE_FIELD_LINK" CLUSTER BY (RP_STRUCTURE_ID, RP_CONDITION_ID)',
        ]
        for stmt in cluster_sql:
            try:
                cur.execute(stmt)
                print("   ✅ Clustering appliqué")
            except Exception as e:
                print(f"   ⚠️  Clustering non appliqué: {e}")

        cnx.commit()
        cur.close()
        cnx.close()

        print("\n✅ Reset complet terminé avec succès !")
        return True

    except Exception as e:
        print(f"❌ Erreur lors du reset: {e}")
        return False


def load_program_by_id(program_id: int) -> str:
    """
    Charge un programme depuis Snowflake en utilisant son ID.

    Args:
        program_id: ID du programme à charger

    Returns:
        str: DSN Snowflake pour charger le programme

    Raises:
        ValueError: Si le programme n'existe pas
    """
    try:
        import snowflake.connector

        config = SnowflakeConfig.load()
        if not config.validate():
            raise ValueError("Configuration Snowflake invalide")

        print(f"🔍 Recherche du programme avec ID: {program_id}")

        cnx = snowflake.connector.connect(**config.to_dict())
        cur = cnx.cursor()

        # Vérifier que le programme existe
        cur.execute(
            f'SELECT TITLE FROM "{config.database}"."{config.schema}"."REINSURANCE_PROGRAM" WHERE REINSURANCE_PROGRAM_ID=%s',
            (program_id,),
        )
        row = cur.fetchone()

        cur.close()
        cnx.close()

        if not row:
            raise ValueError(f"Programme avec ID {program_id} non trouvé")

        program_title = row[0]
        print(f"✅ Programme trouvé: '{program_title}' (ID: {program_id})")

        # Retourner la DSN pour le chargement
        return f"snowflake://{config.database}.{config.schema}?program_id={program_id}"

    except Exception as e:
        print(f"❌ Erreur lors du chargement du programme {program_id}: {e}")
        raise


def truncate_all_tables() -> bool:
    """
    Vide toutes les tables Snowflake (supprime les données mais garde les tables).

    Returns:
        True si le truncate réussit, False sinon
    """
    try:
        import snowflake.connector

        config = SnowflakeConfig.load()
        db = config.database
        schema = config.schema

        print("🗑️  Vidage de toutes les tables Snowflake")
        print(f"🔗 Connexion à Snowflake: {config.account}")
        print(f"📊 Base: {db}.{schema}")

        cnx = snowflake.connector.connect(**config.to_dict())
        cur = cnx.cursor()

        # Ordre de suppression (respecter les contraintes de clés étrangères)
        tables = [
            "RP_STRUCTURE_FIELD_LINK",
            "RP_GLOBAL_EXCLUSION",
            "RP_CONDITIONS",
            "RP_STRUCTURES",
            "REINSURANCE_PROGRAM",
        ]

        for table in tables:
            try:
                cur.execute(f'TRUNCATE TABLE "{db}"."{schema}"."{table}"')
                print(f"   ✅ Table {table} vidée")
            except Exception as e:
                print(f"   ⚠️  Erreur vidage {table}: {e}")

        cnx.commit()
        cur.close()
        cnx.close()

        print("\n✅ Toutes les tables ont été vidées avec succès !")
        return True

    except Exception as e:
        print(f"❌ Erreur lors du vidage: {e}")
        return False
