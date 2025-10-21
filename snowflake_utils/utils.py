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
    Retourne la configuration de sauvegarde selon le backend choisi.

    Args:
        backend: "csv_folder" ou "snowflake"
        program_name: Nom du programme (pour Snowflake)
        output_dir: Dossier de sortie pour CSV (par défaut "../programs")

    Returns:
        Tuple: (output_path, io_kwargs)

    Raises:
        ValueError: Si le backend n'est pas supporté
    """
    if backend == "csv_folder":
        os.makedirs(output_dir, exist_ok=True)
        output_path = f"{output_dir}/{program_name.lower()}"
        io_kwargs = None
        return output_path, io_kwargs

    elif backend == "snowflake":
        config = SnowflakeConfig.load()
        output_path = config.get_dsn(program_name)
        io_kwargs = {"connection_params": config.to_dict()}
        return output_path, io_kwargs

    else:
        raise ValueError(
            f"Backend non supporté: {backend}. Utilisez 'csv_folder' ou 'snowflake'"
        )


def save_program(
    program, backend: str, program_name: str, output_dir: str = "../programs"
) -> str:
    """
    Sauvegarde un programme avec la configuration appropriée.

    Args:
        program: Objet Program à sauvegarder
        backend: "snowflake" ou "csv_folder"
        program_name: Nom du programme
        output_dir: Dossier de sortie pour CSV (par défaut "../programs")

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
            SELECT REINSURANCE_PROGRAM_ID, TITLE, CREATED_AT, UPDATED_AT 
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


def delete_program(program_title: str) -> bool:
    """
    Supprime un programme et toutes ses données liées.

    Args:
        program_title: Titre du programme à supprimer

    Returns:
        True si la suppression réussit, False sinon
    """
    try:
        import snowflake.connector

        config = SnowflakeConfig.load()
        cnx = snowflake.connector.connect(**config.to_dict())
        cur = cnx.cursor()

        # Récupérer l'ID du programme
        cur.execute(
            f"""
            SELECT REINSURANCE_PROGRAM_ID FROM "{config.database}"."{config.schema}"."REINSURANCE_PROGRAM" 
            WHERE TITLE = %s
        """,
            (program_title,),
        )

        result = cur.fetchone()
        if not result:
            print(f"❌ Programme '{program_title}' non trouvé")
            return False

        program_id = result[0]

        # Supprimer les données liées
        cur.execute(
            f'DELETE FROM "{config.database}"."{config.schema}"."RP_GLOBAL_EXCLUSION" WHERE RP_ID = %s',
            (program_id,),
        )
        cur.execute(
            f'DELETE FROM "{config.database}"."{config.schema}"."RP_CONDITIONS" WHERE PROGRAM_ID = %s',
            (program_id,),
        )
        cur.execute(
            f'DELETE FROM "{config.database}"."{config.schema}"."RP_STRUCTURES" WHERE PROGRAM_ID = %s',
            (program_id,),
        )
        cur.execute(
            f'DELETE FROM "{config.database}"."{config.schema}"."REINSURANCE_PROGRAM" WHERE REINSURANCE_PROGRAM_ID = %s',
            (program_id,),
        )

        cnx.commit()
        cur.close()
        cnx.close()

        print(f"✅ Programme '{program_title}' supprimé avec succès")
        return True

    except Exception as e:
        print(f"❌ Erreur lors de la suppression: {e}")
        return False


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
        print("\n🗑️  Suppression des tables existantes...")
        tables = [
            "RP_GLOBAL_EXCLUSION",
            "RP_CONDITIONS",
            "RP_STRUCTURES",
            "REINSURANCE_PROGRAM",
        ]

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

        # 3. Créer des index pour les performances
        print("\n📊 Création des index...")

        indexes = [
            f'CREATE INDEX IDX_REINSURANCE_PROGRAM_TITLE ON "{db}"."{schema}"."REINSURANCE_PROGRAM"(TITLE)',
            f'CREATE INDEX IDX_RP_STRUCTURES_PROGRAM_ID ON "{db}"."{schema}"."RP_STRUCTURES"(PROGRAM_ID)',
            f'CREATE INDEX IDX_RP_CONDITIONS_PROGRAM_ID ON "{db}"."{schema}"."RP_CONDITIONS"(PROGRAM_ID)',
            f'CREATE INDEX IDX_RP_GLOBAL_EXCLUSION_RP_ID ON "{db}"."{schema}"."RP_GLOBAL_EXCLUSION"(RP_ID)',
        ]

        for index_sql in indexes:
            try:
                cur.execute(index_sql)
                print(f"   ✅ Index créé")
            except Exception as e:
                print(f"   ⚠️  Erreur création index: {e}")

        cnx.commit()
        cur.close()
        cnx.close()

        print("\n✅ Reset complet terminé avec succès !")
        print(
            "💡 Les nouveaux programmes auront maintenant des IDs uniques automatiques."
        )
        return True

    except Exception as e:
        print(f"❌ Erreur lors du reset: {e}")
        return False


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
