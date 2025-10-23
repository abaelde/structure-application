"""
Module Snowflake Utils - Configuration et utilitaires pour l'intégration Snowflake

Ce module centralise toute la configuration et les utilitaires liés à Snowflake :
- Configuration de connexion
- Utilitaires de sauvegarde
- Gestion des tables
- Scripts de maintenance

Usage:
    from snowflake_utils import SnowflakeConfig, save_program

    # Configuration automatique
    config = SnowflakeConfig.load()

    # Sauvegarde d'un programme
    save_program(program, "MY_PROGRAM_2024")
"""

from .config import SnowflakeConfig
from .utils import (
    save_program,
    get_save_config,
    test_connection,
    list_programs,
    load_program_by_id,
    reset_all_tables,
    truncate_all_tables,
)

__all__ = [
    "SnowflakeConfig",
    "save_program",
    "get_save_config",
    "test_connection",
    "list_programs",
    "load_program_by_id",
    "reset_all_tables",
    "truncate_all_tables",
]
