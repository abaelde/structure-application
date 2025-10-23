"""
Module Snowflake Utils - Configuration et utilitaires pour l'intégration Snowflake

Ce module centralise toute la configuration et les utilitaires liés à Snowflake :
- Configuration de connexion (classique et Snowpark)
- Utilitaires de sauvegarde et chargement de programmes
- Gestion des tables
- Scripts de maintenance
- Procédures Snowpark pour la lecture de programmes

Usage classique:
    from snowflake_utils import SnowflakeConfig, save_program, load_program_by_id

    # Configuration automatique
    config = SnowflakeConfig.load()

    # Sauvegarde d'un programme
    save_program(program, "snowflake", "MY_PROGRAM_2024")
    
    # Chargement d'un programme par ID
    dsn = load_program_by_id(1)

Usage Snowpark:
    from snowflake_utils import get_snowpark_session, read_program_simple

    # Obtenir une session Snowpark
    session = get_snowpark_session()
    
    # Lire un programme via Snowpark
    program_data = read_program_simple(session, program_id=1)
"""

from .config import SnowflakeConfig
from .utils import (
    save_program,
    save_program_snowpark,
    get_save_config,
    test_connection,
    list_programs,
    load_program_by_id,
    reset_all_tables,
    truncate_all_tables,
)

# Imports Snowpark
from .snowpark_config import (
    SnowparkSessionManager,
    session_manager,
    get_snowpark_session,
    close_snowpark_session,
    test_snowpark_connection,
)
from .procedures import (
    read_program_simple,
    write_program_simple,
    list_programs_simple,
    program_exists_simple,
    test_simple_procedures,
)

__all__ = [
    # Configuration classique
    "SnowflakeConfig",
    "save_program",
    "save_program_snowpark",
    "get_save_config",
    "test_connection",
    "list_programs",
    "load_program_by_id",
    "reset_all_tables",
    "truncate_all_tables",
    
    # Snowpark
    "SnowparkSessionManager",
    "session_manager",
    "get_snowpark_session",
    "close_snowpark_session",
    "test_snowpark_connection",
    "read_program_simple",
    "write_program_simple",
    "list_programs_simple",
    "program_exists_simple",
    "test_simple_procedures",
]
