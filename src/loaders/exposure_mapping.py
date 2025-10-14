from src.domain import UNDERWRITING_DEPARTMENT, UNDERWRITING_DEPARTMENT_VALUES


class ExposureMappingError(Exception):
    pass


REQUIRED_EXPOSURE_COLUMNS = {
    UNDERWRITING_DEPARTMENT.AVIATION: ["HULL_LIMIT", "LIABILITY_LIMIT", "HULL_SHARE", "LIABILITY_SHARE"],
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

    required_columns = REQUIRED_EXPOSURE_COLUMNS[uw_dept_lower]
    missing_columns = [col for col in required_columns if col not in df_columns]

    if missing_columns:
        raise ExposureMappingError(
            f"Missing required exposure columns for underwriting department '{underwriting_department}'. "
            f"Required: {', '.join(required_columns)}. "
            f"Missing: {', '.join(missing_columns)}. "
            f"Found columns: {', '.join(df_columns)}"
        )
