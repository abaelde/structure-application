from src.domain import UNDERWRITING_DEPARTMENT_VALUES
from src.domain.schema import COLUMNS, exposure_rules_for_lob


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

    _validate_via_schema(df_columns, uw_dept_lower)


def _validate_via_schema(df_columns: list, lob: str) -> None:
    cols = set(df_columns)
    rules = exposure_rules_for_lob(lob)

    # requis par LOB
    missing = [name for name, spec in COLUMNS.items()
               if spec.required_by_lob.get(lob) and name not in cols]
    if missing:
        raise ExposureValidationError(
            f"{lob.title()} bordereau must have: {', '.join(missing)}. "
            f"Found columns: {', '.join(df_columns)}"
        )

    # at least one of
    atleast = rules.get("at_least_one_of")
    if atleast:
        groups = [set(g.split("|")) for g in atleast.split(";")] if ";" in atleast else [set(atleast.split("|"))]
        for g in groups:
            if not any(x in cols for x in g):
                raise ExposureValidationError(
                    f"{lob.title()} bordereau must have at least one of: {', '.join(sorted(g))}. "
                    f"Found columns: {', '.join(df_columns)}"
                )

    # pairs (co-dépendance)
    pairs = rules.get("pairs")
    if pairs:
        errors = []
        for pair in pairs.split(";"):
            left, right = map(str.strip, pair.split("<->"))
            if (left in cols) ^ (right in cols):
                errors.append(f"{left} requires {right} (and vice versa)")
        if errors:
            raise ExposureValidationError(
                f"Invalid {lob.title()} exposure columns. "
                f"Errors: {'; '.join(errors)}. "
                f"Found columns: {', '.join(df_columns)}"
            )
