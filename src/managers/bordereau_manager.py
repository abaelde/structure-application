# src/managers/bordereau_manager.py
from __future__ import annotations
from typing import Literal, Optional, Dict, Any
import pandas as pd
from src.serialization.bordereau_serializer import BordereauSerializer
from src.domain.bordereau import Bordereau
from src.domain.program import Program
from src.io.bordereau_csv_adapter import CsvBordereauIO
from src.io.bordereau_snowflake_adapter import SnowflakeBordereauIO

Backend = Literal["csv", "snowflake"]  # AURE : maerge enle rogrm et le bordereau


class BordereauManager:
    """
    Entrée unique pour charger/sauvegarder un bordereau depuis plusieurs backends.
    API symétrique à ProgramManager.
    """

    def __init__(self, backend: Backend = "csv"):
        self.backend = backend
        self.serializer = BordereauSerializer()
        self.io = self._make_io(backend)
        self._loaded: Optional[Bordereau] = None
        self._source: Optional[str] = None

    @staticmethod
    def detect_backend(source: str) -> Backend:
        return "snowflake" if source.lower().startswith("snowflake://") else "csv"

    def _make_io(self, backend: Backend):
        if backend == "csv":
            return CsvBordereauIO()
        elif backend == "snowflake":
            return SnowflakeBordereauIO()
        raise ValueError(f"Unknown backend: {backend}")

    def load(
        self,
        source: str,
        *,
        program: Optional[Program] = None,
        uw_dept: Optional[str] = None,
        validate: bool = True,
        io_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Bordereau:
        io_kwargs = io_kwargs or {}
        df: pd.DataFrame = self.io.read(source, **io_kwargs)
        uw = uw_dept or (program.underwriting_department if program else None)
        b = self.serializer.dataframe_to_bordereau(
            df, uw_dept=uw, source=source, program=program, validate=validate
        )
        self._loaded = b
        self._source = source
        return b

    def save(
        self,
        bordereau: Bordereau,
        dest: str,
        *,
        io_kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        io_kwargs = io_kwargs or {}
        df = self.serializer.bordereau_to_dataframe(bordereau)
        self.io.write(dest, df, **io_kwargs)
