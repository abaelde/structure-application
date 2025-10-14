from src.domain import LINE_OF_BUSINESS, LINE_OF_BUSINESS_VALUES


class ExposureMappingError(Exception):
    pass


EXPOSURE_COLUMN_ALIASES = {
    LINE_OF_BUSINESS.AVIATION: ["HULL_LIMIT", "LIAB_LIMIT"],
    LINE_OF_BUSINESS.CASUALTY: ["LIMIT"],
    LINE_OF_BUSINESS.TEST: ["expo", "exposure"],
}


def find_exposure_column(df_columns: list, line_of_business: str) -> tuple:
    if not line_of_business:
        raise ExposureMappingError(
            "Line of business is required for strict column validation. "
            "Ensure the bordereau is in the correct folder structure "
            "(e.g., 'bordereaux/aviation/file.csv') or specify it explicitly."
        )

    lob_lower = line_of_business.lower()
    
    if lob_lower not in LINE_OF_BUSINESS_VALUES:
        raise ExposureMappingError(
            f"Unknown line of business '{line_of_business}'. "
            f"Supported lines of business: {', '.join(sorted(LINE_OF_BUSINESS_VALUES))}"
        )

    available_names = EXPOSURE_COLUMN_ALIASES[lob_lower]

    for col_name in available_names:
        if col_name in df_columns:
            return col_name, "exposure"

    raise ExposureMappingError(
        f"No valid exposure column found for line of business '{line_of_business}'. "
        f"Expected one of: {', '.join(available_names)}. "
        f"Found columns: {', '.join(df_columns)}"
    )
