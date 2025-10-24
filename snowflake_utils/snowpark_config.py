"""
Configuration et gestion des sessions Snowpark.

Ce module fournit la gestion centralisée des sessions Snowpark
pour l'application de réassurance.
"""

from typing import Optional
from snowflake.snowpark import Session
from .config import SnowflakeConfig


class SnowparkSessionManager:
    """
    Gestionnaire centralisé des sessions Snowpark.
    
    Fournit une interface simple pour créer et gérer les sessions Snowpark
    avec la configuration centralisée de l'application.
    """
    
    def __init__(self):
        self._session: Optional[Session] = None
        self._config: Optional[SnowflakeConfig] = None
    
    def get_session(self) -> Session:

        if self._session is None:
            self._config = SnowflakeConfig.load()
            
            print(self._config.validate())
            
            print(f"🔗 Création de la session Snowpark: {self._config.account}")
            
            # Créer la session Snowpark
            IF_PERSO = True
            if IF_PERSO:
                self._session = Session.builder.configs(self._config.to_dict()).create()
            else:
                self._session = Session.builder.config("connection_name", "").create()
            # Add PRE VERSION HERE
            
            print(f"✅ Session Snowpark créée avec succès")
        
        return self._session
    
    def close(self):
        """Ferme la session Snowpark active."""
        if self._session:
            print("🔒 Fermeture de la session Snowpark")
            self._session.close()
            self._session = None
            self._config = None
    
    def is_connected(self) -> bool:

        return self._session is not None
    
    def test_connection(self) -> bool:

        session = self.get_session()
        
        # Test simple avec une requête
        result = session.sql("SELECT CURRENT_VERSION()").collect()
        version = result[0][0]
        
        print(f"✅ Connexion Snowpark réussie ! Version: {version}")
        return True
            
    
    def get_config(self) -> SnowflakeConfig:

        if self._config is None:
            self._config = SnowflakeConfig.load()
        return self._config


# Instance globale du gestionnaire de sessions
session_manager = SnowparkSessionManager()


def get_snowpark_session() -> Session:

    return session_manager.get_session()


def close_snowpark_session():
    """Fonction utilitaire pour fermer la session Snowpark."""
    session_manager.close()


def test_snowpark_connection() -> bool:

    return session_manager.test_connection()
