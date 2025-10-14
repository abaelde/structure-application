from src.domain import UNDERWRITING_DEPARTMENT, UNDERWRITING_DEPARTMENT_VALUES


class ExposureMappingError(Exception):
    pass


REQUIRED_EXPOSURE_COLUMNS = {
    UNDERWRITING_DEPARTMENT.CASUALTY: ["LIMIT"],
    UNDERWRITING_DEPARTMENT.TEST: ["exposure"],
}


def validate_exposure_columns(df_columns: list, underwriting_department: str) -> None:
    if not underwriting_department:
        raise ExposureMappingError(
            "Underwriting department is required for exposure column validation. "
            "The program must specify an underwriting department."
        )

    uw_dept_lower = underwriting_department.lower()
    
    if uw_dept_lower not in UNDERWRITING_DEPARTMENT_VALUES:
        raise ExposureMappingError(
            f"Unknown underwriting department '{underwriting_department}'. "
            f"Supported underwriting departments: {', '.join(sorted(UNDERWRITING_DEPARTMENT_VALUES))}"
        )

    if uw_dept_lower == UNDERWRITING_DEPARTMENT.AVIATION:
        _validate_aviation_exposure_columns(df_columns)
    else:
        required_columns = REQUIRED_EXPOSURE_COLUMNS[uw_dept_lower]
        missing_columns = [col for col in required_columns if col not in df_columns]

        if missing_columns:
            raise ExposureMappingError(
                f"Missing required exposure columns for underwriting department '{underwriting_department}'. "
                f"Required: {', '.join(required_columns)}. "
                f"Missing: {', '.join(missing_columns)}. "
                f"Found columns: {', '.join(df_columns)}"
            )


def _validate_aviation_exposure_columns(df_columns: list) -> None:
    has_hull_limit = "HULL_LIMIT" in df_columns
    has_hull_share = "HULL_SHARE" in df_columns
    has_liability_limit = "LIABILITY_LIMIT" in df_columns
    has_liability_share = "LIABILITY_SHARE" in df_columns

    if not has_hull_limit and not has_liability_limit:
        raise ExposureMappingError(
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
        raise ExposureMappingError(
            f"Invalid Aviation exposure columns. "
            f"Errors: {'; '.join(errors)}. "
            f"Found columns: {', '.join(df_columns)}"
        )
