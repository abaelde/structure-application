# src/domain/bordereau.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

import pandas as pd

from src.domain.constants import FIELDS
from src.domain.schema import COLUMNS, exposure_rules_for_lob, build_alias_to_canonical
from src.engine.exposure_validation import (
    validate_exposure_columns,
    ExposureValidationError,
)
from src.domain.dimension_mapping import (
    get_all_mappable_dimensions,
    validate_program_bordereau_compatibility,
    validate_aviation_currency_consistency,
)
# NOTE: on n'importe PAS l'engine ici → pas de dépendance circulaire


class BordereauValidationError(Exception):
    pass


@dataclass(frozen=True)
class Policy:
    """Représente une ligne de bordereau (compat. avec dict attendu par l'engine)."""
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.data)

    def get(self, key: str, default=None) -> Any:
        return self.data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]


class Bordereau:
    """
    Petit wrapper autour d'un DataFrame pour :
      - Charger (CSV) et valider le bordereau
      - Exposer les colonnes de dimension réellement disponibles
      - Itérer sous forme d'objets Policy
      - Rester 100% compatible avec l'engine actuel (on peut toujours passer un DataFrame)
    """

    def __init__(
        self,
        df: pd.DataFrame,
        *,
        line_of_business: Optional[str] = None,
        source: Optional[str] = None,
    ):
        self._raw_df = df.copy()
        self._df = self._normalize_columns(self._raw_df)
        self.line_of_business = line_of_business or self._infer_lob(self._df)
        self.source = source
        self.validation_warnings: List[str] = []
        self.validation_errors: List[str] = []

        # Si LOB non fourni, on tente de l'inférer depuis la colonne FIELDS["LINE_OF_BUSINESS"]
        if self.line_of_business is None and FIELDS["LINE_OF_BUSINESS"] in df.columns:
            vals = (
                df[FIELDS["LINE_OF_BUSINESS"]]
                .dropna()
                .astype(str)
                .str.lower()
                .unique()
                .tolist()
            )
            if len(vals) == 1:
                self.line_of_business = vals[0]  # ex: "aviation", "casualty", "test"

    # ──────────────────────────────────────────────────────────────────────
    # Chargement
    # ──────────────────────────────────────────────────────────────────────
    @classmethod
    def from_csv(
        cls,
        path: Union[str, Path],
        *,
        line_of_business: Optional[str] = None,
        validate: bool = True,
        read_csv_kwargs: Optional[Dict[str, Any]] = None,
    ) -> "Bordereau":
        read_csv_kwargs = read_csv_kwargs or {}
        df = pd.read_csv(path, **read_csv_kwargs)
        obj = cls(df, line_of_business=line_of_business, source=str(path))
        if validate:
            obj.validate()
        return obj

    # ──────────────────────────────────────────────────────────────────────
    # Validation
    # ──────────────────────────────────────────────────────────────────────
    def validate(self, *, check_exposure_columns: bool = True) -> bool:
        if self._df is None:
            raise BordereauValidationError("No data to validate")

        # Reset validation state
        self.validation_warnings = []
        self.validation_errors = []

        # Run all validation checks
        self._validate_not_empty()
        self._validate_all_columns_present_via_schema()
        self._validate_non_null_values()
        self._validate_dates()
        self._validate_insured_name_uppercase()
        self._validate_business_logic()
        self._validate_currency_presence()

        # En plus : validation des colonnes d'exposition selon LOB, si connue
        if check_exposure_columns and self.line_of_business:
            self._validate_exposure_columns_via_schema(self.line_of_business)

        # Raise exception if there are errors
        if self.validation_errors:
            raise BordereauValidationError(
                f"Bordereau validation failed:\n"
                + "\n".join(f"  - {err}" for err in self.validation_errors)
            )

        # Print warnings if any
        if self.validation_warnings:
            print("⚠️  Bordereau validation warnings:")
            for warning in self.validation_warnings:
                print(f"  - {warning}")
            print()

        return True

    def _validate_not_empty(self):
        if self._df.empty:
            self.validation_errors.append("Bordereau is empty (no rows)")

    def _validate_all_columns_present_via_schema(self):
        cols = set(self._df.columns)
        # requis globaux
        missing_required = [spec.canonical for spec in COLUMNS.values()
                            if spec.required and spec.canonical not in cols]
        if missing_required:
            self.validation_errors.append(f"Missing required columns: {', '.join(missing_required)}")
        # colonnes inconnues -> warning (tolérance)
        known = set(COLUMNS.keys())
        unknown = [c for c in cols if c not in known]
        if unknown:
            self.validation_warnings.append(f"Ignored unknown columns: {', '.join(unknown)}")

    def _validate_non_null_values(self):
        required_columns = [
            FIELDS["INSURED_NAME"],
            FIELDS["INCEPTION_DATE"],
            FIELDS["EXPIRY_DATE"],
        ]
        
        for col in required_columns:
            if col not in self._df.columns:
                continue

            null_rows = []
            for idx, val in self._df[col].items():
                if pd.isna(val) or (isinstance(val, str) and val.strip() == ""):
                    null_rows.append(f"row {idx + 2}")

            if null_rows:
                self.validation_errors.append(
                    f"Column '{col}' contains null or empty values: {', '.join(null_rows[:5])}"
                    + (f" and {len(null_rows) - 5} more" if len(null_rows) > 5 else "")
                )

    def _validate_dates(self):
        date_columns = [FIELDS["INCEPTION_DATE"], FIELDS["EXPIRY_DATE"]]
        
        for col in date_columns:
            if col not in self._df.columns:
                continue

            invalid_dates = []
            for idx, val in self._df[col].items():
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
        if insured_col not in self._df.columns:
            return

        non_uppercase = []
        for idx, val in self._df[insured_col].items():
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

        if inception_col not in self._df.columns or expiry_col not in self._df.columns:
            return

        invalid_periods = []
        for idx, row in self._df.iterrows():
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

    def _validate_currency_presence(self):
        if not self.line_of_business:
            return

        line_of_business_lower = self.line_of_business.lower()
        
        if line_of_business_lower == "aviation":
            self._validate_aviation_currency()
        elif line_of_business_lower == "casualty":
            self._validate_casualty_currency()

    def _validate_aviation_currency(self):
        hull_present = "HULL_CURRENCY" in self._df.columns
        liability_present = "LIABILITY_CURRENCY" in self._df.columns
        
        if not (hull_present or liability_present):
            self.validation_errors.append(
                "Aviation bordereau must have at least HULL_CURRENCY or LIABILITY_CURRENCY"
            )
        
        # Check for old currency column
        if "BUSCL_LIMIT_CURRENCY_CD" in self._df.columns:
            self.validation_errors.append(
                "BUSCL_LIMIT_CURRENCY_CD not allowed in aviation, use HULL_CURRENCY/LIABILITY_CURRENCY"
            )

    def _validate_casualty_currency(self):
        if "CURRENCY" not in self._df.columns:
            self.validation_errors.append(
                "Casualty bordereau must have CURRENCY column"
            )
        
        # Check for old currency column
        if "BUSCL_LIMIT_CURRENCY_CD" in self._df.columns:
            self.validation_errors.append(
                "BUSCL_LIMIT_CURRENCY_CD not allowed in casualty, use CURRENCY"
            )

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Renomme les alias -> noms canoniques et applique les coercions déclarées dans schema."""
        rename_map = build_alias_to_canonical()
        df2 = df.rename(columns=rename_map).copy()
        # coercions par colonne
        for name, spec in COLUMNS.items():
            if spec.coerce and name in df2.columns:
                df2[name] = df2[name].map(spec.coerce)
        return df2

    def _infer_lob(self, df: pd.DataFrame) -> Optional[str]:
        col = FIELDS["LINE_OF_BUSINESS"] if FIELDS["LINE_OF_BUSINESS"] in df.columns else "line_of_business"
        if col in df.columns:
            vals = df[col].dropna().astype(str).str.lower().unique().tolist()
            if len(vals) == 1:
                return vals[0]
        return None

    def _validate_exposure_columns_via_schema(self, lob: str):
        rules = exposure_rules_for_lob(lob)
        cols = set(self._df.columns)
        # requis par LOB
        missing = [name for name, spec in COLUMNS.items()
                   if spec.required_by_lob.get(lob) and name not in cols]
        if missing:
            self.validation_errors.append(f"{lob.title()} bordereau missing: {', '.join(missing)}")
        # at least one of (aviation)
        atleast = rules.get("at_least_one_of")
        if atleast:
            groups = [set(g.split("|")) for g in atleast.split(";")] if ";" in atleast else [set(atleast.split("|"))]
            for g in groups:
                if not any(x in cols for x in g):
                    self.validation_errors.append(f"{lob.title()} requires at least one of: {', '.join(sorted(g))}")
        # paires (aviation)
        pairs = rules.get("pairs")
        if pairs:
            for pair in pairs.split(";"):
                left, right = map(str.strip, pair.split("<->"))
                if (left in cols) ^ (right in cols):
                    self.validation_errors.append(f"{lob.title()} pair mismatch: {left} requires {right} and vice versa")

    def compatibility_report(self, program) -> Dict[str, Any]:
        """
        Informe sur la compatibilité program ↔︎ bordereau (dimensions mappables, warnings…).
        N'affecte pas l'engine, purement diagnostique.
        """
        lob = program.underwriting_department or self.line_of_business
        errors, warnings = validate_program_bordereau_compatibility(
            program_dimensions=program.dimension_columns,
            bordereau_columns=self.columns,
            line_of_business=lob,
        )
        warnings += validate_aviation_currency_consistency(self.columns, lob)
        return {
            "line_of_business": lob,
            "mapped_dimensions": self.dimension_mapping(),  # program-dimension -> bordereau column
            "warnings": warnings,
            "errors": errors,  # devrait rester vide (design optionnel des dimensions)
        }

    # ──────────────────────────────────────────────────────────────────────
    # Exposition des dimensions
    # ──────────────────────────────────────────────────────────────────────
    def dimension_mapping(self) -> Dict[str, str]:
        """
        Retourne {dimension_programme -> colonne_bordereau} pour les dimensions présentes.
        Utilise le mapping centralisé (dimension_mapping.py).
        """
        return get_all_mappable_dimensions(self.columns, self.line_of_business)

    def dimension_columns(self) -> List[str]:
        """
        Retourne la liste des *dimensions de programme* détectées dans le bordereau.
        (clés du mapping ci-dessus)
        """
        return list(self.dimension_mapping().keys())

    # ──────────────────────────────────────────────────────────────────────
    # Accès / itération / helpers
    # ──────────────────────────────────────────────────────────────────────
    @property
    def df(self) -> pd.DataFrame:
        return self._df

    def to_dataframe(self) -> pd.DataFrame:
        """Alias explicite (pour duck typing dans l'engine)."""
        return self._df

    def to_engine_dataframe(self) -> pd.DataFrame:
        """DF **canonique** (noms & types) prêt pour l'engine."""
        return self._df.copy()

    @property
    def columns(self) -> List[str]:
        return list(self._df.columns)

    def __len__(self) -> int:
        return len(self._df)

    def __iter__(self) -> Iterable[Policy]:
        for _, row in self._df.iterrows():
            yield Policy(row.to_dict())

    def policies(self) -> Iterable[Policy]:
        return iter(self)

    def head(self, n: int = 5) -> "Bordereau":
        return Bordereau(self._df.head(n).copy(), line_of_business=self.line_of_business, source=self.source)

    def filter(self, expr: str) -> "Bordereau":
        """Filtre via DataFrame.query et retourne un nouveau Bordereau."""
        return Bordereau(self._df.query(expr).copy(), line_of_business=self.line_of_business, source=self.source)

    def with_line_of_business(self, lob: str) -> "Bordereau":
        """Clone avec LOB fixé/écrasé (utile si non inférable)."""
        return Bordereau(self._df.copy(), line_of_business=lob, source=self.source)

    def __repr__(self) -> str:
        src = f"source='{self.source}', " if self.source else ""
        lob = f"lob='{self.line_of_business}'" if self.line_of_business else "lob=None"
        return f"Bordereau({src}{lob}, rows={len(self)})"


