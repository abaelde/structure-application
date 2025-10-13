import pandas as pd
from pathlib import Path
from typing import Optional, Union
from .exposure_mapping import find_exposure_column
from .bordereau_validator import BordereauValidator, BordereauValidationError


class BordereauLoader:
    def __init__(self, source: Union[str, Path], source_type: str = "auto", line_of_business: Optional[str] = None, validate: bool = True):
        self.source = Path(source) if isinstance(source, str) else source
        self.source_type = source_type if source_type != "auto" else self._detect_source_type()
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
            raise ValueError(f"Unsupported file type: {suffix}. Only CSV files are supported.")
    
    def _detect_line_of_business(self) -> Optional[str]:
        parts = self.source.parts
        
        if "bordereaux" in parts:
            bordereaux_idx = parts.index("bordereaux")
            if len(parts) > bordereaux_idx + 2:
                return parts[bordereaux_idx + 1]
        
        return None

    def load(self) -> pd.DataFrame:
        if self.source_type == "csv":
            self.df = self._load_from_csv()
        else:
            raise ValueError(f"Unsupported source type: {self.source_type}")

        if self.validate_on_load:
            validator = BordereauValidator(self.df, self.line_of_business)
            validator.validate()
            self.validation_warnings = validator.validation_warnings
            self.validation_errors = validator.validation_errors

        return self.df

    def _load_from_csv(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(self.source)
            
            found_column, target_column = find_exposure_column(df.columns.tolist(), self.line_of_business)
            
            if found_column and found_column != target_column:
                df = df.rename(columns={found_column: target_column})
                print(f"ℹ️  Colonne d'exposition '{found_column}' mappée vers '{target_column}'")
            
            return df
        except Exception as e:
            raise BordereauValidationError(f"Error reading CSV file: {e}")


def load_bordereau(source: Union[str, Path], source_type: str = "auto", line_of_business: Optional[str] = None) -> pd.DataFrame:
    loader = BordereauLoader(source, source_type, line_of_business)
    return loader.load()

