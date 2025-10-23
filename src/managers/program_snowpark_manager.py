"""
Program Manager utilisant Snowpark.

Ce manager utilise Snowpark pour charger les programmes depuis Snowflake
et les convertir en objets Program en mémoire via le ProgramSerializer.
"""

from __future__ import annotations
from typing import Optional
from snowflake.snowpark import Session

from .program_manager import ProgramManager
from src.io.program_snowpark_adapter import SnowparkProgramIO
from src.serialization.program_serializer import ProgramSerializer
from src.domain.program import Program


class SnowparkProgramManager:
    """
    Program Manager utilisant Snowpark pour la lecture des programmes.
    
    Ce manager charge les programmes depuis Snowflake en utilisant Snowpark
    et les convertit en objets Program en mémoire via le ProgramSerializer.
    """
    
    def __init__(self, session: Session):
        """
        Initialise le manager avec une session Snowpark.
        
        Args:
            session: Session Snowpark active
        """
        self.session = session
        self.serializer = ProgramSerializer()
        self.io = SnowparkProgramIO(session)
        self._loaded_program: Optional[Program] = None
        self._loaded_source: Optional[str] = None

    def load(self, source: str, io_kwargs: Optional[dict] = None) -> Program:
        """
        Charge un programme depuis Snowflake en utilisant Snowpark.
        
        Args:
            source: DSN Snowflake (format: snowflake://database.schema?program_id=X)
            io_kwargs: Paramètres supplémentaires (non utilisés avec Snowpark)
            
        Returns:
            Objet Program chargé en mémoire
            
        Raises:
            ValueError: Si le program_id n'est pas fourni dans la DSN
            RuntimeError: Si le chargement échoue
        """
        # Extraire program_id de la DSN
        program_id = self._extract_program_id(source)
        
        if not program_id:
            raise ValueError("program_id is required in the DSN for Snowpark loading")
        
        try:
            # Lire les DataFrames depuis Snowflake via Snowpark
            program_df, structures_df, conditions_df, exclusions_df, field_links_df = self.io.read(
                source, connection_params={}, program_id=program_id
            )
            
            # Convertir les DataFrames en objet Program via le serializer
            program = self.serializer.dataframes_to_program(
                program_df, structures_df, conditions_df, exclusions_df, field_links_df
            )
            
            # Sauvegarder l'état
            self._loaded_program = program
            self._loaded_source = source
            
            return program
            
        except Exception as e:
            raise RuntimeError(f"Failed to load program {program_id} via Snowpark: {e}")

    def save(self, program: Program, dest: str, io_kwargs: Optional[dict] = None) -> None:
        """
        Sauvegarde un programme (non implémenté pour l'instant).
        
        Args:
            program: Programme à sauvegarder
            dest: Destination
            io_kwargs: Paramètres supplémentaires
        """
        raise NotImplementedError("Save functionality not yet implemented for Snowpark manager")

    def _extract_program_id(self, source: str) -> Optional[int]:
        """
        Extrait le program_id de la DSN Snowflake.
        
        Args:
            source: DSN au format snowflake://database.schema?program_id=X
            
        Returns:
            ID du programme ou None si non trouvé
        """
        try:
            from urllib.parse import urlparse, parse_qsl
            
            parsed = urlparse(source)
            if parsed.scheme.lower() != "snowflake":
                return None
            
            params = dict(parse_qsl(parsed.query))
            program_id = params.get("program_id")
            
            return int(program_id) if program_id else None
            
        except (ValueError, AttributeError):
            return None

    def get_loaded_program(self) -> Optional[Program]:
        """
        Retourne le programme actuellement chargé.
        
        Returns:
            Programme chargé ou None
        """
        return self._loaded_program

    def get_loaded_source(self) -> Optional[str]:
        """
        Retourne la source du programme actuellement chargé.
        
        Returns:
            Source du programme ou None
        """
        return self._loaded_source
