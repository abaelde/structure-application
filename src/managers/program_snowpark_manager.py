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
        self._loaded_program_id: Optional[int] = None

    def load(self, program_id: int) -> Program:
        """
        Charge un programme depuis Snowflake en utilisant Snowpark.
        
        Args:
            program_id: ID du programme à charger
            
        Returns:
            Objet Program chargé en mémoire
            
        Raises:
            RuntimeError: Si le chargement échoue
        """
        try:
            # Lire les DataFrames depuis Snowflake via Snowpark
            program_df, structures_df, conditions_df, exclusions_df, field_links_df = self.io.read(program_id)
            
            # Convertir les DataFrames en objet Program via le serializer
            program = self.serializer.dataframes_to_program(
                program_df, structures_df, conditions_df, exclusions_df, field_links_df
            )
            
            # Sauvegarder l'état
            self._loaded_program = program
            self._loaded_program_id = program_id
            
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


    def get_loaded_program(self) -> Optional[Program]:
        """
        Retourne le programme actuellement chargé.
        
        Returns:
            Programme chargé ou None
        """
        return self._loaded_program

    def get_loaded_program_id(self) -> Optional[int]:
        """
        Retourne l'ID du programme actuellement chargé.
        
        Returns:
            ID du programme ou None
        """
        return self._loaded_program_id
