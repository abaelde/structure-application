from src.domain import UNDERWRITING_DEPARTMENT, UNDERWRITING_DEPARTMENT_VALUES


class ExposureValidationError(Exception):
    pass


def validate_exposure_columns(df_columns: list, underwriting_department: str) -> None:
    if not underwriting_department:
        raise ExposureValidationError(
            "Underwriting department is required for exposure column validation. "
            "The program must specify an underwriting department."
        )

    uw_dept_lower = underwriting_department.lower()
    
    if uw_dept_lower not in UNDERWRITING_DEPARTMENT_VALUES:
        raise ExposureValidationError(
            f"Unknown underwriting department '{underwriting_department}'. "
            f"Supported underwriting departments: {', '.join(sorted(UNDERWRITING_DEPARTMENT_VALUES))}"
        )

    if uw_dept_lower == UNDERWRITING_DEPARTMENT.AVIATION:
        _validate_aviation_exposure_columns(df_columns)
    elif uw_dept_lower == UNDERWRITING_DEPARTMENT.CASUALTY:
        _validate_casualty_exposure_columns(df_columns)
    elif uw_dept_lower == UNDERWRITING_DEPARTMENT.TEST:
        _validate_test_exposure_columns(df_columns)


def _validate_casualty_exposure_columns(df_columns: list) -> None:
    missing_columns = []
    
    if "LIMIT" not in df_columns:
        missing_columns.append("LIMIT")
    
    if "CEDENT_SHARE" not in df_columns:
        missing_columns.append("CEDENT_SHARE")
    
    if missing_columns:
        raise ExposureValidationError(
            f"Casualty bordereau must have LIMIT and CEDENT_SHARE columns. "
            f"Missing: {', '.join(missing_columns)}. "
            f"Found columns: {', '.join(df_columns)}"
        )


def _validate_test_exposure_columns(df_columns: list) -> None:
    if "exposure" not in df_columns:
        raise ExposureValidationError(
            f"Test bordereau must have exposure column. "
            f"Found columns: {', '.join(df_columns)}"
        )


def _validate_aviation_exposure_columns(df_columns: list) -> None:
    has_hull_limit = "HULL_LIMIT" in df_columns
    has_hull_share = "HULL_SHARE" in df_columns
    has_liability_limit = "LIABILITY_LIMIT" in df_columns
    has_liability_share = "LIABILITY_SHARE" in df_columns

    if not has_hull_limit and not has_liability_limit:
        raise ExposureValidationError(
            f"Aviation bordereau must have at least one exposure type. "
            f"Required: HULL_LIMIT or LIABILITY_LIMIT (or both). "
            f"Found columns: {', '.join(df_columns)}"
        )

    errors = []
    
    if has_hull_limit and not has_hull_share:
        errors.append("HULL_LIMIT requires HULL_SHARE")
    
    if has_hull_share and not has_hull_limit:
        errors.append("HULL_SHARE requires HULL_LIMIT")
    
    if has_liability_limit and not has_liability_share:
        errors.append("LIABILITY_LIMIT requires LIABILITY_SHARE")
    
    if has_liability_share and not has_liability_limit:
        errors.append("LIABILITY_SHARE requires LIABILITY_LIMIT")

    if errors:
        raise ExposureValidationError(
            f"Invalid Aviation exposure columns. "
            f"Errors: {'; '.join(errors)}. "
            f"Found columns: {', '.join(df_columns)}"
        )
