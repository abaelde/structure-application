# src/managers/program_manager.py
import os
from pathlib import Path
import pandas as pd
from typing import Literal, Optional
from src.io.program_snowflake_adapter import SnowflakeProgramIO
from src.io.program_csv_folder_adapter import CsvProgramFolderIO
from src.serialization.program_serializer import ProgramSerializer
from src.domain.program import Program

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
            raise ValueError(f"Excel files (.xlsx/.xls) are no longer supported. Please use CSV folder format instead. File: {source}")
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
        program_df, structures_df, conditions_df, exclusions_df = self.io.read(source, **(io_kwargs or {}))
        self._loaded_program = self.serializer.dataframes_to_program(
            program_df, structures_df, conditions_df, exclusions_df
        )
        self._loaded_source = source
        return self._loaded_program

    def save(self, program: Program, dest: str, io_kwargs: Optional[dict] = None) -> None:
        """
        Save a program to the specified destination.

        Args:
            program: The Program object to save
            dest: Destination path/identifier
            io_kwargs: Additional parameters for the I/O adapter (e.g., connection_params, if_exists for Snowflake)
        """
        dfs = self.serializer.program_to_dataframes(program)
        self.io.write(dest, dfs["program"], dfs["structures"], dfs["conditions"], dfs["exclusions"], **(io_kwargs or {}))

    def save_current(self, dest: str, io_kwargs: Optional[dict] = None) -> None:
        """
        Save the currently loaded program to the specified destination.

        Args:
            dest: Destination path/identifier
            io_kwargs: Additional parameters for the I/O adapter (e.g., connection_params, if_exists for Snowflake)

        Raises:
            ValueError: If no program is currently loaded
        """
        if not self._loaded_program:
            raise ValueError("No program currently loaded. Call load() first.")
        self.save(self._loaded_program, dest, io_kwargs)

    def get_current_program(self) -> Program:
        """
        Get the currently loaded program.

        Returns:
            The currently loaded Program object

        Raises:
            ValueError: If no program is currently loaded
        """
        if not self._loaded_program:
            raise ValueError("No program currently loaded. Call load() first.")
        return self._loaded_program

    def get_current_source(self) -> str:
        """
        Get the source of the currently loaded program.

        Returns:
            The source path/identifier of the currently loaded program

        Raises:
            ValueError: If no program is currently loaded
        """
        if not self._loaded_source:
            raise ValueError("No program currently loaded. Call load() first.")
        return self._loaded_source

    def switch_backend(self, backend: Backend) -> None:
        """
        Switch to a different backend.

        Args:
            backend: The new backend to use
        """
        self.backend = backend
        self.io = self._make_io(backend)
        # Clear the loaded program since it was loaded with the previous backend
        self._loaded_program = None
        self._loaded_source = None

    def reload(self, io_kwargs: Optional[dict] = None) -> Program:
        """
        Reload the program from the current source.

        Args:
            io_kwargs: Additional parameters for the I/O adapter (e.g., connection_params for Snowflake)

        Returns:
            The reloaded Program object

        Raises:
            ValueError: If no program is currently loaded
        """
        if not self._loaded_source:
            raise ValueError("No program currently loaded. Call load() first.")
        return self.load(self._loaded_source, io_kwargs)

    def copy_to_backend(self, program: Program, dest: str, backend: Backend, io_kwargs: Optional[dict] = None) -> None:
        """
        Copy a program to a different backend.

        Args:
            program: The Program object to copy
            dest: Destination path/identifier
            backend: Target backend
            io_kwargs: Additional parameters for the I/O adapter (e.g., connection_params, if_exists for Snowflake)
        """
        # Save current backend
        current_backend = self.backend

        # Switch to target backend
        self.switch_backend(backend)

        # Save the program
        self.save(program, dest, io_kwargs)

        # Restore original backend
        self.switch_backend(current_backend)

    def is_loaded(self) -> bool:
        """
        Check if a program is currently loaded.

        Returns:
            True if a program is loaded, False otherwise
        """
        return self._loaded_program is not None

    def clear(self) -> None:
        """
        Clear the currently loaded program.
        """
        self._loaded_program = None
        self._loaded_source = None
