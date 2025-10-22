# src/managers/program_manager.py
import os
from pathlib import Path
import pandas as pd
from typing import Literal, Optional
from src.io.program_snowflake_adapter import SnowflakeProgramIO
from src.io.program_csv_folder_adapter import CsvProgramFolderIO
from src.serialization.program_serializer import ProgramSerializer
from src.domain.program import Program
from src.io.snowflake_db import parse_db_schema  # ⬅️ nouveau import

# Backends supportés par ProgramManager
Backend = Literal["snowflake", "csv_folder"]


class ProgramManager:
    """
    Unified Program Manager that handles import/export for multiple backends.

    This is the main entry point for all program operations (load, save) across
    different backends (Snowflake, CSV folder, etc.).

    Features:
    - Load programs from Snowflake or CSV folder
    - Save programs to Snowflake or CSV folder
    - Switch backends dynamically
    - Consistent API across all backends
    - State management (track loaded program and source)
    - Auto-detection of backend from source path

        Examples:
        # CSV folder (default)
        manager = ProgramManager()  # ou backend="csv_folder"
        program = manager.load("path/to/my_program_folder")  # contient 3 CSV
        manager.save(program, "path/to/another_folder")

        # Snowflake
        manager = ProgramManager(backend="snowflake")
        program = manager.load("snowflake://database.schema.table")
        manager.save(program, "snowflake://database.schema.output_table")
    """

    @staticmethod
    def detect_backend(source: str) -> Backend:
        """Heuristique simple:
        - 'snowflake://...' -> snowflake
        - dossier existant -> csv_folder
        - fichier .xlsx/.xls -> erreur (Excel non supporté)
        """
        if source.lower().startswith("snowflake://"):
            return "snowflake"
        p = Path(source)
        if p.exists() and p.is_dir():
            return "csv_folder"
        if p.suffix.lower() in {".xlsx", ".xls"}:
            raise ValueError(
                f"Excel files (.xlsx/.xls) are no longer supported. Please use CSV folder format instead. File: {source}"
            )
        # défaut: si le chemin n'existe pas encore mais ressemble à un dossier (sans suffixe) -> csv_folder
        return "csv_folder"

    def __init__(self, backend: Backend = "csv_folder"):
        """
        Initialize the program manager.

        Args:
            backend: Default backend to use ("snowflake" or "csv_folder")
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
        elif backend == "csv_folder":
            return CsvProgramFolderIO()
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
        # Extraire program_title de la DSN Snowflake si présent
        program_title = None
        if source.lower().startswith("snowflake://"):
            try:
                _, _, params = parse_db_schema(source)
                program_title = params.get("program_title")
            except Exception:
                pass  # si l'extraction échoue, on continue sans program_title

        # Préparer les paramètres selon le backend
        if self.backend == "snowflake":
            connection_params = io_kwargs or {}
            if program_title:
                # Retirer program_title des paramètres de connexion
                connection_params = {k: v for k, v in connection_params.items() if k != "program_title"}
            program_df, structures_df, conditions_df, exclusions_df, field_links_df = self.io.read(
                source, connection_params=connection_params, program_title=program_title
            )
        else:
            # Pour les autres backends (CSV), pas de paramètres spéciaux
            program_df, structures_df, conditions_df, exclusions_df, field_links_df = self.io.read(source)
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
