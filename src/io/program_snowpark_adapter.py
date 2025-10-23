"""
Adapter Snowpark pour la lecture des programmes de réassurance.

Cet adapter utilise Snowpark pour lire les données depuis Snowflake
et les convertit en DataFrames pandas compatibles avec le ProgramSerializer existant.
"""

from __future__ import annotations
from typing import Tuple, Optional, Dict, Any
import pandas as pd
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, lit

from .snowflake_db import parse_db_schema


class SnowparkProgramIO:
    """
    I/O adapter pour les programmes utilisant Snowpark.
    
    Cet adapter lit les données depuis Snowflake en utilisant Snowpark
    et retourne des DataFrames pandas dans le format attendu par ProgramSerializer.
    """
    
    PROGRAMS = "REINSURANCE_PROGRAM"
    STRUCTURES = "RP_STRUCTURES"
    CONDITIONS = "RP_CONDITIONS"
    EXCLUSIONS = "RP_GLOBAL_EXCLUSION"
    FIELD_LINKS = "RP_STRUCTURE_FIELD_LINK"

    def __init__(self, session: Session):
        """
        Initialise l'adapter avec une session Snowpark.
        
        Args:
            session: Session Snowpark active
        """
        self.session = session

    def read(
        self,
        source: str,
        connection_params: Dict[str, Any],
        program_id: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Lit un programme depuis Snowflake par son ID.
        
        Args:
            source: DSN Snowflake (format: snowflake://database.schema)
            connection_params: Paramètres de connexion (non utilisés avec Snowpark)
            program_id: ID du programme à lire
            
        Returns:
            Tuple: (program_df, structures_df, conditions_df, exclusions_df, field_links_df)
            
        Raises:
            ValueError: Si program_id n'est pas fourni ou si le programme n'existe pas
        """
        if not program_id:
            raise ValueError("program_id is required for Snowpark program loading")
        
        # Parser la DSN pour obtenir database et schema
        db, schema, params = parse_db_schema(source)
        
        try:
            # 1. Lire le programme principal
            program_df = self._read_program(db, schema, program_id)
            
            # 2. Lire les structures
            structures_df = self._read_structures(db, schema, program_id)
            
            # 3. Lire les conditions
            conditions_df = self._read_conditions(db, schema, program_id)
            
            # 4. Lire les exclusions
            exclusions_df = self._read_exclusions(db, schema, program_id)
            
            # 5. Lire les field links (overrides)
            field_links_df = self._read_field_links(db, schema, program_id)
            
            return program_df, structures_df, conditions_df, exclusions_df, field_links_df
            
        except Exception as e:
            raise RuntimeError(f"Error reading program {program_id} from Snowflake: {e}")

    def _read_program(self, db: str, schema: str, program_id: int) -> pd.DataFrame:
        """Lit les données du programme principal."""
        program_df = self.session.table(f'"{db}"."{schema}"."{self.PROGRAMS}"').filter(
            col("REINSURANCE_PROGRAM_ID") == lit(program_id)
        ).to_pandas()
        
        if program_df.empty:
            raise ValueError(f"Program with ID {program_id} not found")
        
        return program_df

    def _read_structures(self, db: str, schema: str, program_id: int) -> pd.DataFrame:
        """Lit les structures du programme."""
        structures_df = self.session.table(f'"{db}"."{schema}"."{self.STRUCTURES}"').filter(
            col("REINSURANCE_PROGRAM_ID") == lit(program_id)
        ).to_pandas()
        
        return structures_df

    def _read_conditions(self, db: str, schema: str, program_id: int) -> pd.DataFrame:
        """Lit les conditions du programme."""
        conditions_df = self.session.table(f'"{db}"."{schema}"."{self.CONDITIONS}"').filter(
            col("REINSURANCE_PROGRAM_ID") == lit(program_id)
        ).to_pandas()
        
        return conditions_df

    def _read_exclusions(self, db: str, schema: str, program_id: int) -> pd.DataFrame:
        """Lit les exclusions du programme."""
        exclusions_df = self.session.table(f'"{db}"."{schema}"."{self.EXCLUSIONS}"').filter(
            col("REINSURANCE_PROGRAM_ID") == lit(program_id)
        ).to_pandas()
        
        return exclusions_df

    def _read_field_links(self, db: str, schema: str, program_id: int) -> pd.DataFrame:
        """Lit les field links (overrides) du programme."""
        # Requête SQL pour joindre les field links avec les conditions
        field_links_df = self.session.sql(f"""
            SELECT 
                fl.RP_STRUCTURE_FIELD_LINK_ID,
                fl.RP_CONDITION_ID,
                fl.RP_STRUCTURE_ID,
                fl.FIELD_NAME,
                fl.NEW_VALUE
            FROM "{db}"."{schema}"."{self.FIELD_LINKS}" fl
            JOIN "{db}"."{schema}"."{self.CONDITIONS}" c 
                ON fl.RP_CONDITION_ID = c.RP_CONDITION_ID
            WHERE c.REINSURANCE_PROGRAM_ID = {program_id}
            ORDER BY fl.RP_STRUCTURE_FIELD_LINK_ID
        """).to_pandas()
        
        return field_links_df

    def write(
        self,
        dest: str,
        program_df: pd.DataFrame,
        structures_df: pd.DataFrame,
        conditions_df: pd.DataFrame,
        exclusions_df: pd.DataFrame,
        field_links_df: pd.DataFrame,
        connection_params: Dict[str, Any],
    ) -> None:
        """
        Écrit un programme dans Snowflake.
        
        Note: Cette méthode n'est pas encore implémentée.
        Pour l'instant, on se concentre sur la lecture.
        
        Args:
            dest: DSN de destination
            program_df: DataFrame du programme
            structures_df: DataFrame des structures
            conditions_df: DataFrame des conditions
            exclusions_df: DataFrame des exclusions
            field_links_df: DataFrame des field links
            connection_params: Paramètres de connexion
        """
        raise NotImplementedError("Write functionality not yet implemented for Snowpark adapter")
