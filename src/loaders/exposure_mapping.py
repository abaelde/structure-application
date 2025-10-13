EXPOSURE_COLUMN_ALIASES = {
    "aviation": ["hull_limit", "liab_limit"],
    "casualty": ["limit"],
    "test": ["expo", "exposition"],
}


def find_exposure_column(df_columns: list, line_of_business: str = None) -> tuple:
    if not line_of_business or line_of_business.lower() not in EXPOSURE_COLUMN_ALIASES:
        return None, "exposition"

    available_names = EXPOSURE_COLUMN_ALIASES[line_of_business.lower()]

    for col_name in available_names:
        if col_name in df_columns:
            return col_name, "exposition"

    return None, "exposition"
