# src/managers/program_manager.py
import os
from pathlib import Path
import pandas as pd
from typing import Literal, Optional
from src.io.program_snowflake_adapter import SnowflakeProgramIO
from src.serialization.program_serializer import ProgramSerializer
from src.domain.program import Program
from src.io.snowflake_db import parse_db_schema  # ⬅️ nouveau import

# Backends supportés par ProgramManager
Backend = Literal["snowflake"]


class ProgramManager:
    """
    Unified Program Manager that handles import/export for Snowflake backend.

    This is the main entry point for all program operations (load, save) with Snowflake.

    Features:
    - Load programs from Snowflake by ID
    - Save programs to Snowflake
    - State management (track loaded program and source)

        Examples:
        # Snowflake
        manager = ProgramManager(backend="snowflake")
        program = manager.load("snowflake://database.schema?program_id=1")
        manager.save(program, "snowflake://database.schema?program_title=MY_PROGRAM")
    """

    @staticmethod
    def detect_backend(source: str) -> Backend:
        """Détection du backend Snowflake uniquement."""
        if source.lower().startswith("snowflake://"):
            return "snowflake"
        else:
            raise ValueError(
                f"Only Snowflake backend is supported. Source must start with 'snowflake://'. Got: {source}"
            )

    def __init__(self, backend: Backend = "snowflake"):
        """
        Initialize the program manager.

        Args:
            backend: Backend to use (only "snowflake" supported)
        """
        self.backend = backend
        self.serializer = ProgramSerializer()
        self.io = self._make_io(backend)
        self._loaded_program: Optional[Program] = None
        self._loaded_source: Optional[str] = None

    def _make_io(self, backend: Backend):
        """Create the appropriate I/O adapter for the backend."""
        if backend == "snowflake":
            return SnowflakeProgramIO()
        else:
            raise ValueError(f"Unknown backend: {backend}")

    def load(self, source: str, io_kwargs: Optional[dict] = None) -> Program:
        """
        Load a program from the specified source.

        Args:
            source: Source path/identifier for the program data
            io_kwargs: Additional parameters for the I/O adapter (e.g., connection_params for Snowflake)

        Returns:
            The loaded Program object
        """
        # Extraire program_id de la DSN Snowflake si présent
        program_id = None
        if source.lower().startswith("snowflake://"):
            try:
                _, _, params = parse_db_schema(source)
                program_id = params.get("program_id")
                if program_id:
                    program_id = int(program_id)
            except Exception:
                pass  # si l'extraction échoue, on continue sans paramètres

        # Préparer les paramètres pour Snowflake
        connection_params = io_kwargs or {}
        if program_id:
            # Retirer program_id des paramètres de connexion
            connection_params = {k: v for k, v in connection_params.items() if k != "program_id"}
        program_df, structures_df, conditions_df, exclusions_df, field_links_df = self.io.read(
            source, connection_params=connection_params, program_id=program_id
        )
        self._loaded_program = self.serializer.dataframes_to_program(
            program_df, structures_df, conditions_df, exclusions_df, field_links_df
        )
        self._loaded_source = source
        return self._loaded_program

    def save(
        self, program: Program, dest: str, io_kwargs: Optional[dict] = None
    ) -> None:
        """
        Save a program to the specified destination.

        Args:
            program: The Program object to save
            dest: Destination path/identifier
            io_kwargs: Additional parameters for the I/O adapter (e.g., connection_params, if_exists for Snowflake)
        """
        dfs = self.serializer.program_to_dataframes(program)
        self.io.write(
            dest,
            dfs["program"],
            dfs["structures"],
            dfs["conditions"],
            dfs["exclusions"],
            dfs["field_links"],
            **(io_kwargs or {}),
        )
