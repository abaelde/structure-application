import pandas as pd
from pathlib import Path
from typing import Optional, Union
from .exposure_mapping import find_exposure_column
from .bordereau_validator import BordereauValidator, BordereauValidationError


class BordereauLoader:
    def __init__(
        self,
        source: Union[str, Path],
        data_source: str = "file",
        source_type: str = "auto",
        line_of_business: Optional[str] = None,
        validate: bool = True,
    ):
        self.data_source = data_source
        self.source = Path(source) if isinstance(source, str) else source
        self.source_type = (
            source_type if source_type != "auto" else self._detect_source_type()
        )
        self.line_of_business = line_of_business or self._detect_line_of_business()
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

    def _detect_line_of_business(self) -> Optional[str]:
        parts = self.source.parts

        if "bordereaux" in parts:
            bordereaux_idx = parts.index("bordereaux")
            if len(parts) > bordereaux_idx + 2:
                return parts[bordereaux_idx + 1]

        return None

    def load(self) -> pd.DataFrame:
        if self.data_source == "file":
            self.df = self._load_from_file()
        elif self.data_source == "snowflake":
            self.df = self._load_from_snowflake()
        else:
            raise ValueError(f"Unknown data_source: {self.data_source}")

        if self.validate_on_load:
            validator = BordereauValidator(self.df, self.line_of_business)
            validator.validate()
            self.validation_warnings = validator.validation_warnings
            self.validation_errors = validator.validation_errors

        return self.df

    def _load_from_file(self) -> pd.DataFrame:
        if self.source_type == "csv":
            try:
                df = pd.read_csv(self.source)

                found_column, target_column = find_exposure_column(
                    df.columns.tolist(), self.line_of_business
                )

                if found_column and found_column != target_column:
                    df = df.rename(columns={found_column: target_column})
                    print(
                        f"ℹ️  Colonne d'exposure '{found_column}' mappée vers '{target_column}'"
                    )

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
    line_of_business: Optional[str] = None,
) -> pd.DataFrame:
    loader = BordereauLoader(source, data_source, source_type, line_of_business)
    return loader.load()
