import pandas as pd
from pathlib import Path
from typing import List, Optional, Union
from .constants import FIELDS, DIMENSIONS


class BordereauValidationError(Exception):
    pass


class BordereauLoader:
    REQUIRED_COLUMNS = [
        FIELDS["INSURED_NAME"],
        FIELDS["EXPOSURE"],
        FIELDS["INCEPTION_DATE"],
        FIELDS["EXPIRY_DATE"],
    ]
    
    DIMENSION_COLUMNS = [
        FIELDS["COUNTRY"],
        FIELDS["REGION"],
        FIELDS["CLASS_1"],
        FIELDS["CLASS_2"],
        FIELDS["CLASS_3"],
        FIELDS["CURRENCY"],
        FIELDS["LINE_OF_BUSINESS"],
        FIELDS["INDUSTRY"],
        FIELDS["SIC_CODE"],
        FIELDS["INCLUDE"],
    ]
    
    OPTIONAL_COLUMNS = [
        FIELDS["POLICY_NUMBER"],
    ]
    
    ALLOWED_COLUMNS = REQUIRED_COLUMNS + DIMENSION_COLUMNS + OPTIONAL_COLUMNS

    NUMERIC_COLUMNS = [FIELDS["EXPOSURE"]]

    DATE_COLUMNS = [FIELDS["INCEPTION_DATE"], FIELDS["EXPIRY_DATE"]]

    def __init__(self, source: Union[str, Path], source_type: str = "auto"):
        self.source = Path(source) if isinstance(source, str) else source
        self.source_type = source_type if source_type != "auto" else self._detect_source_type()
        self.df: Optional[pd.DataFrame] = None
        self.validation_warnings: List[str] = []
        self.validation_errors: List[str] = []

    def _detect_source_type(self) -> str:
        suffix = self.source.suffix.lower()
        if suffix == ".csv":
            return "csv"
        else:
            raise ValueError(f"Unsupported file type: {suffix}. Only CSV files are supported.")

    def load(self) -> pd.DataFrame:
        if self.source_type == "csv":
            self.df = self._load_from_csv()
        else:
            raise ValueError(f"Unsupported source type: {self.source_type}")

        self._validate()

        if self.validation_errors:
            raise BordereauValidationError(
                f"Bordereau validation failed:\n" + "\n".join(f"  - {err}" for err in self.validation_errors)
            )

        if self.validation_warnings:
            print("⚠️  Bordereau validation warnings:")
            for warning in self.validation_warnings:
                print(f"  - {warning}")
            print()

        return self.df

    def _load_from_csv(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(self.source)
            return df
        except Exception as e:
            raise BordereauValidationError(f"Error reading CSV file: {e}")

    def _validate(self):
        if self.df is None:
            raise BordereauValidationError("No data loaded")

        self._validate_not_empty()
        self._validate_all_columns_present()
        self._validate_non_null_values()
        self._validate_data_types()
        self._validate_dates()
        self._validate_numeric_values()
        self._validate_business_logic()

    def _validate_not_empty(self):
        if self.df.empty:
            self.validation_errors.append("Bordereau is empty (no rows)")

    def _validate_all_columns_present(self):
        missing_required = [col for col in self.REQUIRED_COLUMNS if col not in self.df.columns]
        if missing_required:
            self.validation_errors.append(
                f"Missing required columns: {', '.join(missing_required)}"
            )

        unknown_columns = [
            col
            for col in self.df.columns
            if col not in self.ALLOWED_COLUMNS
        ]
        if unknown_columns:
            self.validation_errors.append(
                f"Unknown columns not allowed: {', '.join(unknown_columns)}"
            )

    def _validate_non_null_values(self):
        if self.df is None:
            return

        for col in self.REQUIRED_COLUMNS:
            if col not in self.df.columns:
                continue

            null_rows = []
            for idx, val in self.df[col].items():
                if pd.isna(val) or (isinstance(val, str) and val.strip() == ""):
                    null_rows.append(f"row {idx + 2}")

            if null_rows:
                self.validation_errors.append(
                    f"Column '{col}' contains null or empty values: {', '.join(null_rows[:5])}"
                    + (f" and {len(null_rows) - 5} more" if len(null_rows) > 5 else "")
                )

    def _validate_data_types(self):
        if self.df is None:
            return

        for col in self.NUMERIC_COLUMNS:
            if col in self.df.columns:
                non_numeric = []
                for idx, val in self.df[col].items():
                    if pd.isna(val):
                        continue
                    try:
                        float(val)
                    except (ValueError, TypeError):
                        non_numeric.append(f"row {idx + 2}: '{val}'")

                if non_numeric:
                    self.validation_errors.append(
                        f"Column '{col}' contains non-numeric values: {', '.join(non_numeric[:5])}"
                        + (f" and {len(non_numeric) - 5} more" if len(non_numeric) > 5 else "")
                    )

    def _validate_dates(self):
        if self.df is None:
            return

        for col in self.DATE_COLUMNS:
            if col not in self.df.columns:
                continue

            invalid_dates = []
            for idx, val in self.df[col].items():
                if pd.isna(val):
                    invalid_dates.append(f"row {idx + 2}: empty date")
                    continue

                try:
                    pd.to_datetime(val)
                except Exception:
                    invalid_dates.append(f"row {idx + 2}: '{val}'")

            if invalid_dates:
                self.validation_errors.append(
                    f"Column '{col}' contains invalid dates: {', '.join(invalid_dates[:5])}"
                    + (f" and {len(invalid_dates) - 5} more" if len(invalid_dates) > 5 else "")
                )

    def _validate_numeric_values(self):
        exposure_col = FIELDS["EXPOSURE"]
        if self.df is None or exposure_col not in self.df.columns:
            return

        negative_expositions = []
        zero_expositions = []

        for idx, val in self.df[exposure_col].items():
            if pd.isna(val):
                continue

            try:
                numeric_val = float(val)
                if numeric_val < 0:
                    negative_expositions.append(f"row {idx + 2}: {numeric_val}")
                elif numeric_val == 0:
                    zero_expositions.append(f"row {idx + 2}")
            except (ValueError, TypeError):
                continue

        if negative_expositions:
            self.validation_errors.append(
                f"Column '{exposure_col}' contains negative values: {', '.join(negative_expositions[:5])}"
                + (f" and {len(negative_expositions) - 5} more" if len(negative_expositions) > 5 else "")
            )

        if zero_expositions:
            self.validation_warnings.append(
                f"Column '{exposure_col}' contains zero values: {', '.join(zero_expositions[:5])}"
                + (f" and {len(zero_expositions) - 5} more" if len(zero_expositions) > 5 else "")
            )

    def _validate_business_logic(self):
        if self.df is None:
            return

        inception_col = FIELDS["INCEPTION_DATE"]
        expiry_col = FIELDS["EXPIRY_DATE"]
        
        if inception_col not in self.df.columns or expiry_col not in self.df.columns:
            return

        invalid_periods = []
        for idx, row in self.df.iterrows():
            try:
                inception = pd.to_datetime(row[inception_col])
                expiry = pd.to_datetime(row[expiry_col])

                if expiry <= inception:
                    invalid_periods.append(
                        f"row {idx + 2}: expiry ({expiry.date()}) <= inception ({inception.date()})"
                    )
            except Exception:
                continue

        if invalid_periods:
            self.validation_errors.append(
                f"Invalid policy periods (expiry <= inception): {', '.join(invalid_periods[:5])}"
                + (f" and {len(invalid_periods) - 5} more" if len(invalid_periods) > 5 else "")
            )


def load_bordereau(source: Union[str, Path], source_type: str = "auto") -> pd.DataFrame:
    loader = BordereauLoader(source, source_type)
    return loader.load()

