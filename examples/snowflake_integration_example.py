#!/usr/bin/env python3
"""
Exemple d'intégration Snowflake pour les programmes et runs.

Ce script démontre comment utiliser les nouveaux adapters Snowflake
avec le modèle payload JSON pour une intégration pragmatique et rapide.

Usage:
    python examples/snowflake_integration_example.py

Prérequis:
    - snowflake-connector-python installé
    - Accès à une instance Snowflake avec les permissions appropriées
    - Configuration des paramètres de connexion ci-dessous
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au path pour les imports
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.managers import ProgramManager
from src.io import RunSnowflakeIO, SnowflakeProgramIO


def get_connection_params():
    """
    Récupère les paramètres de connexion Snowflake.

    Configurez ces variables d'environnement ou modifiez directement les valeurs :
    - SNOWFLAKE_ACCOUNT
    - SNOWFLAKE_USER
    - SNOWFLAKE_PASSWORD
    - SNOWFLAKE_WAREHOUSE
    - SNOWFLAKE_DATABASE
    - SNOWFLAKE_SCHEMA
    - SNOWFLAKE_ROLE
    """
    return {
        "account": os.getenv("SNOWFLAKE_ACCOUNT", "your_account"),
        "user": os.getenv("SNOWFLAKE_USER", "your_user"),
        "password": os.getenv("SNOWFLAKE_PASSWORD", "your_password"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "your_warehouse"),
        "database": os.getenv("SNOWFLAKE_DATABASE", "MYDB"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "MYSCHEMA"),
        "role": os.getenv("SNOWFLAKE_ROLE", "your_role"),
    }


def example_program_operations():
    """
    Exemple d'opérations sur les programmes avec Snowflake.
    """
    print("=== Exemple d'opérations sur les programmes ===")

    # Configuration
    connection_params = get_connection_params()
    dsn = f"snowflake://{connection_params['database']}.{connection_params['schema']}?program_title=Test_Program"

    # Initialiser le manager avec backend Snowflake
    pm = ProgramManager(backend="snowflake")

    try:
        # 1. Charger un programme depuis CSV (exemple)
        print("1. Chargement d'un programme depuis CSV...")
        csv_source = "examples/programs/aviation_axa_xl_2024"
        program = pm.load(csv_source)
        print(f"   Programme chargé: {program.title}")

        # 2. Sauvegarder dans Snowflake
        print("2. Sauvegarde dans Snowflake...")
        pm.save(
            program,
            dsn,
            io_kwargs={
                "connection_params": connection_params,
                "if_exists": "replace_program",
            },
        )
        print(f"   Programme sauvegardé dans: {dsn}")

        # 3. Recharger depuis Snowflake
        print("3. Rechargement depuis Snowflake...")
        pm.switch_backend("snowflake")
        reloaded_program = pm.load(
            dsn, io_kwargs={"connection_params": connection_params}
        )
        print(f"   Programme rechargé: {reloaded_program.title}")
        print(f"   Nombre de structures: {len(reloaded_program.structures)}")
        print(f"   Nombre de conditions: {len(reloaded_program.conditions)}")

        return True

    except Exception as e:
        print(f"Erreur lors des opérations sur les programmes: {e}")
        return False


def example_run_operations():
    """
    Exemple d'opérations sur les runs avec Snowflake.
    """
    print("\n=== Exemple d'opérations sur les runs ===")

    # Configuration
    connection_params = get_connection_params()
    dsn = f"snowflake://{connection_params['database']}.{connection_params['schema']}"

    try:
        # Créer des DataFrames de test (simulation)
        import pandas as pd

        # Simulation d'un run
        runs_df = pd.DataFrame(
            [
                {
                    "RUN_ID": "test_run_001",
                    "PROGRAM_ID": "test_program_001",
                    "PROGRAM_NAME": "Test Program",
                    "UW_DEPT": "AVIATION",
                    "CALCULATION_DATE": "2024-01-15",
                    "SOURCE_PROGRAM": "examples/programs/aviation_axa_xl_2024",
                    "SOURCE_BORDEREAU": "examples/bordereaux/bordereau_aviation_axa_xl.csv",
                    "PROGRAM_FINGERPRINT": "abc123",
                    "STARTED_AT": "2024-01-15 10:00:00",
                    "ENDED_AT": "2024-01-15 10:05:00",
                    "ROW_COUNT": 100,
                    "NOTES": "Test run",
                }
            ]
        )

        # Simulation de politiques
        run_policies_df = pd.DataFrame(
            [
                {
                    "POLICY_RUN_ID": "policy_001",
                    "RUN_ID": "test_run_001",
                    "POLICY_ID": "POL_001",
                    "INSURED_NAME": "Test Insured",
                    "INCEPTION_DT": "2024-01-01",
                    "EXPIRE_DT": "2024-12-31",
                    "EXCLUSION_STATUS": "INCLUDED",
                    "EXCLUSION_REASON": None,
                    "EXPOSURE": 1000000.0,
                    "EFFECTIVE_EXPOSURE": 1000000.0,
                    "CESSION_TO_LAYER_100PCT": 500000.0,
                    "CESSION_TO_REINSURER": 500000.0,
                    "RETAINED_BY_CEDANT": 500000.0,
                    "RAW_RESULT_JSON": '{"test": "data"}',
                }
            ]
        )

        # Simulation de structures
        run_policy_structures_df = pd.DataFrame(
            [
                {
                    "STRUCTURE_ROW_ID": "struct_001",
                    "POLICY_RUN_ID": "policy_001",
                    "STRUCTURE_NAME": "Test Structure",
                    "TYPE_OF_PARTICIPATION": "QUOTA_SHARE",
                    "PREDECESSOR_TITLE": None,
                    "CLAIM_BASIS": "OCCURRENCE",
                    "PERIOD_START": "2024-01-01",
                    "PERIOD_END": "2024-12-31",
                    "APPLIED": True,
                    "REASON": "Matched condition",
                    "SCOPE": "FULL",
                    "INPUT_EXPOSURE": 1000000.0,
                    "CEDED_TO_LAYER_100PCT": 500000.0,
                    "CEDED_TO_REINSURER": 500000.0,
                    "RETAINED_AFTER": 500000.0,
                    "TERMS_JSON": '{"share": 0.5}',
                    "MATCHED_CONDITION_JSON": '{"id": 1}',
                    "RESCALING_JSON": "{}",
                    "MATCHING_DETAILS_JSON": '{"method": "exact"}',
                    "METRICS_JSON": '{"processing_time": 0.1}',
                }
            ]
        )

        # Sauvegarder dans Snowflake
        print("1. Sauvegarde des runs dans Snowflake...")
        run_io = RunSnowflakeIO()
        run_io.write(
            dsn,
            runs_df,
            run_policies_df,
            run_policy_structures_df,
            connection_params=connection_params,
        )
        print(f"   Runs sauvegardés dans: {dsn}")

        # Recharger depuis Snowflake
        print("2. Rechargement des runs depuis Snowflake...")
        loaded_runs, loaded_policies, loaded_structures = run_io.read(
            dsn, connection_params=connection_params
        )
        print(
            f"   Runs rechargés: {len(loaded_runs)} runs, {len(loaded_policies)} politiques, {len(loaded_structures)} structures"
        )

        return True

    except Exception as e:
        print(f"Erreur lors des opérations sur les runs: {e}")
        return False


def example_admin_operations():
    """
    Exemple d'opérations d'administration (reset, drop).
    """
    print("\n=== Exemple d'opérations d'administration ===")

    connection_params = get_connection_params()
    dsn = f"snowflake://{connection_params['database']}.{connection_params['schema']}"

    try:
        # Attention: ces opérations suppriment des données !
        print("⚠️  ATTENTION: Ces opérations suppriment des données !")
        print("   Décommentez les lignes ci-dessous pour les exécuter...")

        # # Reset complet (truncate)
        # print("1. Reset complet des tables...")
        # program_io = SnowflakeProgramIO()
        # program_io.write(
        #     dsn + "?program_title=reset_test",
        #     pd.DataFrame([{"TITLE": "Reset Test", "UW_LOB": "TEST"}]),
        #     pd.DataFrame(),
        #     pd.DataFrame(),
        #     pd.DataFrame(),
        #     if_exists="truncate_all",
        #     connection_params=connection_params
        # )
        # print("   Tables tronquées")

        # # Drop complet
        # print("2. Suppression complète des tables...")
        # program_io.drop_all_tables(dsn, connection_params=connection_params)
        # run_io = RunSnowflakeIO()
        # run_io.drop_all_tables(dsn, connection_params=connection_params)
        # print("   Tables supprimées")

        print("   (Opérations d'administration non exécutées pour sécurité)")
        return True

    except Exception as e:
        print(f"Erreur lors des opérations d'administration: {e}")
        return False


def main():
    """
    Fonction principale qui exécute tous les exemples.
    """
    print("🚀 Exemple d'intégration Snowflake")
    print("=" * 50)

    # Vérifier la configuration
    connection_params = get_connection_params()
    if connection_params["account"] == "your_account":
        print("❌ Configuration Snowflake requise !")
        print(
            "   Configurez les variables d'environnement ou modifiez get_connection_params()"
        )
        return

    success_count = 0
    total_tests = 3

    # Exécuter les exemples
    if example_program_operations():
        success_count += 1

    if example_run_operations():
        success_count += 1

    if example_admin_operations():
        success_count += 1

    # Résumé
    print(f"\n📊 Résumé: {success_count}/{total_tests} tests réussis")
    if success_count == total_tests:
        print("✅ Tous les tests sont passés ! L'intégration Snowflake fonctionne.")
    else:
        print(
            "⚠️  Certains tests ont échoué. Vérifiez la configuration et les permissions."
        )


if __name__ == "__main__":
    main()
