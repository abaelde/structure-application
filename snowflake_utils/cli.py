#!/usr/bin/env python3
"""
CLI pour le module snowflake_utils - Interface en ligne de commande pour la gestion Snowflake.

Usage:
    python -m snowflake_utils.cli <command> [options]
    ou
    snowflake-cli <command> [options]
"""

import sys
import argparse
from typing import List, Optional
from pathlib import Path

# Ajouter le chemin du projet pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from snowflake_utils import (
    SnowflakeConfig,
    test_connection,
    list_programs,
    delete_program,
    reset_all_tables,
    truncate_all_tables,
    save_program,
)


def cmd_test_connection(args):
    """Teste la connexion Snowflake."""
    print("🔗 Test de connexion Snowflake...")
    if test_connection():
        print("✅ Connexion réussie !")
        return 0
    else:
        print("❌ Échec de la connexion")
        return 1


def cmd_list_programs(args):
    """Liste tous les programmes."""
    print("📊 Liste des programmes...")
    programs = list_programs()
    if programs:
        print(f"   {len(programs)} programme(s) trouvé(s):")
        for program in programs:
            print(
                f"   - ID: {program['id']}, Titre: {program['title']}, Créé: {program['created_at']}"
            )
    else:
        print("   Aucun programme trouvé")
    return 0


def cmd_delete_program(args):
    """Supprime un programme."""
    if not args.title:
        print("❌ Erreur: Le titre du programme est requis")
        return 1

    print(f"🗑️  Suppression du programme '{args.title}'...")
    if delete_program(args.title):
        print("✅ Programme supprimé avec succès")
        return 0
    else:
        print("❌ Échec de la suppression")
        return 1


def cmd_reset_tables(args):
    """Reset complet des tables."""
    if not args.force:
        confirm = (
            input("⚠️  Reset complet (suppression + recréation) ? (oui/non): ")
            .strip()
            .lower()
        )
        if confirm not in ["oui", "o", "yes", "y"]:
            print("❌ Opération annulée")
            return 0

    print("🔄 Reset complet des tables...")
    if reset_all_tables():
        print("✅ Reset terminé avec succès")
        return 0
    else:
        print("❌ Échec du reset")
        return 1


def cmd_truncate_tables(args):
    """Vide toutes les tables."""
    if not args.force:
        confirm = input("⚠️  Vider toutes les tables ? (oui/non): ").strip().lower()
        if confirm not in ["oui", "o", "yes", "y"]:
            print("❌ Opération annulée")
            return 0

    print("🧹 Vidage de toutes les tables...")
    if truncate_all_tables():
        print("✅ Tables vidées avec succès")
        return 0
    else:
        print("❌ Échec du vidage")
        return 1


def cmd_config_info(args):
    """Affiche les informations de configuration."""
    print("⚙️  Configuration Snowflake:")
    try:
        config = SnowflakeConfig.load()
        print(f"   Account: {config.account}")
        print(f"   User: {config.user}")
        print(f"   Warehouse: {config.warehouse}")
        print(f"   Database: {config.database}")
        print(f"   Schema: {config.schema}")
        print(f"   Role: {config.role}")
        print(f"   Validation: {'✅ Valide' if config.validate() else '❌ Invalide'}")
    except Exception as e:
        print(f"❌ Erreur de configuration: {e}")
        return 1
    return 0


def cmd_status(args):
    """Affiche le statut complet du système."""
    print("📊 Statut du système Snowflake")
    print("=" * 50)

    # Configuration
    print("\n⚙️  Configuration:")
    try:
        config = SnowflakeConfig.load()
        print(f"   Account: {config.account}")
        print(f"   Database: {config.database}.{config.schema}")
        print(f"   Warehouse: {config.warehouse}")
        print(f"   Validation: {'✅ Valide' if config.validate() else '❌ Invalide'}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return 1

    # Connexion
    print("\n🔗 Connexion:")
    if test_connection():
        print("   ✅ Connexion réussie")
    else:
        print("   ❌ Échec de connexion")
        return 1

    # Données
    print("\n📊 Données:")
    programs = list_programs()
    print(f"   Programmes: {len(programs)}")

    if programs:
        print("   Détails:")
        for program in programs:
            print(f"     - {program['title']} (ID: {program['id']})")

    return 0


def cmd_sql_query(args):
    """Exécute une requête SQL personnalisée."""
    if not args.query:
        print("❌ Erreur: La requête SQL est requise")
        return 1

    try:
        import snowflake.connector

        config = SnowflakeConfig.load()
        cnx = snowflake.connector.connect(**config.to_dict())
        cur = cnx.cursor()

        print(f"🔍 Exécution de la requête: {args.query}")
        cur.execute(args.query)

        results = cur.fetchall()
        if results:
            print(f"📊 {len(results)} résultat(s):")
            for row in results:
                print(f"   {row}")
        else:
            print("   Aucun résultat")

        cur.close()
        cnx.close()
        return 0

    except Exception as e:
        print(f"❌ Erreur SQL: {e}")
        return 1


def main():
    """Point d'entrée principal de la CLI."""
    parser = argparse.ArgumentParser(
        description="CLI pour la gestion Snowflake",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  snowflake-cli test                    # Tester la connexion
  snowflake-cli status                  # Statut complet du système
  snowflake-cli list-programs           # Lister tous les programmes
  snowflake-cli delete-program "TITRE"  # Supprimer un programme
  snowflake-cli reset-tables --force    # Reset complet des tables
  snowflake-cli truncate-tables         # Vider les tables
  snowflake-cli sql "SELECT COUNT(*) FROM PROGRAMS"  # Requête SQL
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")

    # Test de connexion
    subparsers.add_parser("test", help="Tester la connexion Snowflake")

    # Statut complet
    subparsers.add_parser("status", help="Afficher le statut complet du système")

    # Configuration
    subparsers.add_parser("config", help="Afficher les informations de configuration")

    # Lister les programmes
    subparsers.add_parser("list-programs", help="Lister tous les programmes")

    # Supprimer un programme
    delete_parser = subparsers.add_parser(
        "delete-program", help="Supprimer un programme"
    )
    delete_parser.add_argument("title", help="Titre du programme à supprimer")

    # Reset des tables
    reset_parser = subparsers.add_parser(
        "reset-tables", help="Reset complet des tables"
    )
    reset_parser.add_argument(
        "--force", action="store_true", help="Forcer sans confirmation"
    )

    # Truncate des tables
    truncate_parser = subparsers.add_parser(
        "truncate-tables", help="Vider toutes les tables"
    )
    truncate_parser.add_argument(
        "--force", action="store_true", help="Forcer sans confirmation"
    )

    # Requête SQL
    sql_parser = subparsers.add_parser("sql", help="Exécuter une requête SQL")
    sql_parser.add_argument("query", help="Requête SQL à exécuter")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Dispatch des commandes
    commands = {
        "test": cmd_test_connection,
        "status": cmd_status,
        "config": cmd_config_info,
        "list-programs": cmd_list_programs,
        "delete-program": cmd_delete_program,
        "reset-tables": cmd_reset_tables,
        "truncate-tables": cmd_truncate_tables,
        "sql": cmd_sql_query,
    }

    command_func = commands.get(args.command)
    if command_func:
        return command_func(args)
    else:
        print(f"❌ Commande inconnue: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
