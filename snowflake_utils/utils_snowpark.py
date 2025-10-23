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
    """
    Sauvegarde un programme dans Snowflake en utilisant Snowpark.

    Args:
        program: Objet Program à sauvegarder
        program_name: Nom du programme

    Returns:
        bool: True si la sauvegarde réussit

    Raises:
        ValueError: Si la configuration Snowflake est invalide
        RuntimeError: Si la sauvegarde échoue
    """
    

    try:
        print(f"💾 Sauvegarde du programme '{program_name}' via Snowpark...")
        
        # Obtenir la configuration Snowflake
        config = SnowflakeConfig.load()
        if not config.validate():
            raise ValueError("Configuration Snowflake invalide")
    
        
        # Obtenir une session Snowpark
        session = get_snowpark_session()
        
        try:
            # Créer le manager Snowpark
            manager = SnowparkProgramManager(session)
            
            # Sauvegarder le programme (pas besoin de passer la destination)
            manager.save(program)
            
            print(f"✅ Programme '{program_name}' sauvegardé avec succès via Snowpark !")
            return True
            
        finally:
            # Fermer la session Snowpark
            close_snowpark_session()
            
    except Exception as e:
        error_msg = f"Échec de la sauvegarde du programme '{program_name}' via Snowpark: {e}"
        print(f"❌ {error_msg}")
        raise RuntimeError(error_msg) from e
