from src.domain import UNDERWRITING_DEPARTMENT, UNDERWRITING_DEPARTMENT_VALUES


class ExposureMappingError(Exception):
    pass


EXPOSURE_COLUMN_ALIASES = {
    UNDERWRITING_DEPARTMENT.AVIATION: ["HULL_LIMIT", "LIAB_LIMIT"],
    UNDERWRITING_DEPARTMENT.CASUALTY: ["LIMIT"],
    UNDERWRITING_DEPARTMENT.TEST: ["exposure"],
}


def find_exposure_column(df_columns: list, underwriting_department: str) -> tuple:
    if not underwriting_department:
        raise ExposureMappingError(
            "Underwriting department is required for exposure column mapping. "
            "The program must specify an underwriting department."
        )

    uw_dept_lower = underwriting_department.lower()
    
    if uw_dept_lower not in UNDERWRITING_DEPARTMENT_VALUES:
        raise ExposureMappingError(
            f"Unknown underwriting department '{underwriting_department}'. "
            f"Supported underwriting departments: {', '.join(sorted(UNDERWRITING_DEPARTMENT_VALUES))}"
        )

    available_names = EXPOSURE_COLUMN_ALIASES[uw_dept_lower]

    for col_name in available_names:
        if col_name in df_columns:
            return col_name, "exposure"

    raise ExposureMappingError(
        f"No valid exposure column found for underwriting department '{underwriting_department}'. "
        f"Expected one of: {', '.join(available_names)}. "
        f"Found columns: {', '.join(df_columns)}"
    )
