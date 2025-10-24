"""
Utilitaires Snowpark pour la sauvegarde et la gestion des programmes.

Ce module fournit des fonctions utilitaires pour travailler avec Snowpark
dans le contexte de l'application.
"""

from typing import Dict, Any

from .config import SnowflakeConfig
from .snowpark_config import get_snowpark_session, close_snowpark_session
from src.managers.program_snowpark_manager import SnowparkProgramManager


def save_program_snowpark(program, program_name: str) -> bool:

    print(f"💾 Sauvegarde du programme '{program_name}' via Snowpark...")
    
    # Obtenir la configuration Snowflake
    config = SnowflakeConfig.load()
    print(config.validate())
    
        
    # Obtenir une session Snowpark
    session = get_snowpark_session()
    
    # Créer le manager Snowpark
    manager = SnowparkProgramManager(session)
    
    # Sauvegarder le programme (pas besoin de passer la destination)
    manager.save(program)
    
    print(f"✅ Programme '{program_name}' sauvegardé avec succès via Snowpark !")
    return True
    
    # Fermer la session Snowpark
    close_snowpark_session()
            