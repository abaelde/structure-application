import pandas as pd
from pathlib import Path
from typing import Optional, Union
from .bordereau_validator import BordereauValidator, BordereauValidationError


class BordereauLoader:
    def __init__(
        self,
        source: Union[str, Path],
        data_source: str = "file",
        source_type: str = "auto",
        validate: bool = True,
    ):
        self.data_source = data_source
        self.source = Path(source) if isinstance(source, str) else source
        self.source_type = (
            source_type if source_type != "auto" else self._detect_source_type()
        )
        self.validate_on_load = validate
        self.df: Optional[pd.DataFrame] = None
        self.validation_warnings: list = []
        self.validation_errors: list = []

    def _detect_source_type(self) -> str:
        suffix = self.source.suffix.lower()
        if suffix == ".csv":
            return "csv"
        else:
            raise ValueError(
                f"Unsupported file type: {suffix}. Only CSV files are supported."
            )

    def load(self) -> pd.DataFrame:
        if self.data_source == "file":
            self.df = self._load_from_file()
        elif self.data_source == "snowflake":
            self.df = self._load_from_snowflake()
        else:
            raise ValueError(f"Unknown data_source: {self.data_source}")

        if self.validate_on_load:
            validator = BordereauValidator(self.df)
            validator.validate()
            self.validation_warnings = validator.validation_warnings
            self.validation_errors = validator.validation_errors

        return self.df

    def _load_from_file(self) -> pd.DataFrame:
        if self.source_type == "csv":
            try:
                df = pd.read_csv(self.source)
                return df
            except Exception as e:
                raise BordereauValidationError(f"Error reading CSV file: {e}")
        else:
            raise ValueError(f"Unsupported source type: {self.source_type}")

    def _load_from_snowflake(self) -> pd.DataFrame:
        raise NotImplementedError("Snowflake loading not yet implemented")


def load_bordereau(
    source: Union[str, Path],
    data_source: str = "file",
    source_type: str = "auto",
) -> pd.DataFrame:
    loader = BordereauLoader(source, data_source, source_type)
    return loader.load()
