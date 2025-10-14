import pandas as pd
from typing import List
from src.domain import FIELDS


class BordereauValidationError(Exception):
    pass


class BordereauValidator:
    REQUIRED_COLUMNS = [
        FIELDS["INSURED_NAME"],
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
    ]

    OPTIONAL_COLUMNS = [
        FIELDS["POLICY_NUMBER"],
        "POLICY_ID",
        "INDUSTRY",
        "SIC_CODE",
    ]

    EXPOSURE_COLUMNS_ALL_DEPARTMENTS = [
        "exposure",
        "HULL_LIMIT",
        "LIABILITY_LIMIT",
        "HULL_SHARE",
        "LIABILITY_SHARE",
        "LIMIT",
        "CEDENT_SHARE",
    ]

    ALLOWED_COLUMNS = REQUIRED_COLUMNS + DIMENSION_COLUMNS + OPTIONAL_COLUMNS + EXPOSURE_COLUMNS_ALL_DEPARTMENTS

    DATE_COLUMNS = [FIELDS["INCEPTION_DATE"], FIELDS["EXPIRY_DATE"]]

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.validation_warnings: List[str] = []
        self.validation_errors: List[str] = []

    def validate(self) -> bool:
        if self.df is None:
            raise BordereauValidationError("No data to validate")

        self._validate_not_empty()
        self._validate_all_columns_present()
        self._validate_non_null_values()
        self._validate_dates()
        self._validate_insured_name_uppercase()
        self._validate_business_logic()

        if self.validation_errors:
            raise BordereauValidationError(
                f"Bordereau validation failed:\n"
                + "\n".join(f"  - {err}" for err in self.validation_errors)
            )

        if self.validation_warnings:
            print("⚠️  Bordereau validation warnings:")
            for warning in self.validation_warnings:
                print(f"  - {warning}")
            print()

        return True

    def _validate_not_empty(self):
        if self.df.empty:
            self.validation_errors.append("Bordereau is empty (no rows)")

    def _validate_all_columns_present(self):
        missing_required = [
            col for col in self.REQUIRED_COLUMNS if col not in self.df.columns
        ]
        if missing_required:
            self.validation_errors.append(
                f"Missing required columns: {', '.join(missing_required)}"
            )

        unknown_columns = [
            col for col in self.df.columns if col not in self.ALLOWED_COLUMNS
        ]
        if unknown_columns:
            self.validation_errors.append(
                f"Unknown columns not allowed: {', '.join(unknown_columns)}"
            )

    def _validate_non_null_values(self):
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

    def _validate_dates(self):
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
                    + (
                        f" and {len(invalid_dates) - 5} more"
                        if len(invalid_dates) > 5
                        else ""
                    )
                )

    def _validate_insured_name_uppercase(self):
        insured_col = FIELDS["INSURED_NAME"]
        if insured_col not in self.df.columns:
            return

        non_uppercase = []
        for idx, val in self.df[insured_col].items():
            if pd.isna(val):
                continue

            str_val = str(val)
            if str_val != str_val.upper():
                non_uppercase.append(f"row {idx + 2}: '{str_val}'")

        if non_uppercase:
            self.validation_errors.append(
                f"Column '{insured_col}' must contain only uppercase values: {', '.join(non_uppercase[:5])}"
                + (
                    f" and {len(non_uppercase) - 5} more"
                    if len(non_uppercase) > 5
                    else ""
                )
            )

    def _validate_business_logic(self):
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
                + (
                    f" and {len(invalid_periods) - 5} more"
                    if len(invalid_periods) > 5
                    else ""
                )
            )


def validate_bordereau(df: pd.DataFrame) -> bool:
    validator = BordereauValidator(df)
    return validator.validate()
