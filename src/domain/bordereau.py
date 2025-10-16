# src/domain/bordereau.py
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

import pandas as pd

from src.domain.constants import FIELDS
from src.domain.schema import COLUMNS, exposure_rules_for_lob, build_alias_to_canonical
from src.domain.dimension_mapping import (
    get_all_mappable_dimensions,
)
from src.domain import UNDERWRITING_DEPARTMENT_VALUES
from src.domain.policy import Policy  # ⬅️ nouveau


class BordereauValidationError(Exception):
    pass


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
        program: Optional[Any] = None,
    ):
        self._raw_df = df.copy()
        self._df = self._normalize_columns(self._raw_df)
        self.line_of_business = line_of_business or self._infer_lob(self._df)
        self.source = source
        self.program = program  # Référence vers le programme associé
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
        missing_required = [
            spec.canonical
            for spec in COLUMNS.values()
            if spec.required and spec.canonical not in cols
        ]
        if missing_required:
            self.validation_errors.append(
                f"Missing required columns: {', '.join(missing_required)}"
            )
        # colonnes inconnues -> warning (tolérance)
        known = set(COLUMNS.keys())
        unknown = [c for c in cols if c not in known]
        if unknown:
            self.validation_warnings.append(
                f"Ignored unknown columns: {', '.join(unknown)}"
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
        col = (
            FIELDS["LINE_OF_BUSINESS"]
            if FIELDS["LINE_OF_BUSINESS"] in df.columns
            else "line_of_business"
        )
        if col in df.columns:
            vals = df[col].dropna().astype(str).str.lower().unique().tolist()
            if len(vals) == 1:
                return vals[0]
        return None

    def get_underwriting_department(self) -> str:
        """
        Retourne l'underwriting_department du programme associé.

        Returns:
            str: L'underwriting_department du programme

        Raises:
            BordereauValidationError: Si aucun programme n'est associé ou si le programme n'a pas d'underwriting_department
        """
        if not self.program:
            raise BordereauValidationError(
                "No program associated with this bordereau. "
                "Cannot determine underwriting_department."
            )

        # Support pour dict et objet Program
        if isinstance(self.program, dict):
            underwriting_department = self.program.get("underwriting_department")
        else:
            underwriting_department = getattr(
                self.program, "underwriting_department", None
            )

        if not underwriting_department:
            raise BordereauValidationError(
                "Associated program must specify an underwriting_department."
            )

        return underwriting_department

    def validate_exposure_columns(
        self, underwriting_department: Optional[str] = None
    ) -> None:
        """
        Valide les colonnes d'exposition selon l'underwriting_department.

        Args:
            underwriting_department: Si fourni, utilise cette valeur. Sinon, utilise celle du programme associé.
        """

        # Si pas fourni, récupère depuis le programme associé
        if not underwriting_department:
            underwriting_department = self.get_underwriting_department()

        uw_dept_lower = underwriting_department.lower()

        if uw_dept_lower not in UNDERWRITING_DEPARTMENT_VALUES:
            raise BordereauValidationError(
                f"Unknown underwriting department '{underwriting_department}'. "
                f"Supported underwriting departments: {', '.join(sorted(UNDERWRITING_DEPARTMENT_VALUES))}"
            )

        self._validate_exposure_via_schema(uw_dept_lower)

    def _validate_exposure_via_schema(self, lob: str) -> None:
        """Méthode privée pour valider les colonnes d'exposition selon le schéma."""

        cols = set(self.columns)
        rules = exposure_rules_for_lob(lob)

        # requis par LOB
        missing = [
            name
            for name, spec in COLUMNS.items()
            if spec.required_by_lob.get(lob) and name not in cols
        ]
        if missing:
            raise BordereauValidationError(
                f"{lob.title()} bordereau must have: {', '.join(missing)}. "
                f"Found columns: {', '.join(self.columns)}"
            )

        # at least one of
        atleast = rules.get("at_least_one_of")
        if atleast:
            groups = (
                [set(g.split("|")) for g in atleast.split(";")]
                if ";" in atleast
                else [set(atleast.split("|"))]
            )
            for g in groups:
                if not any(x in cols for x in g):
                    raise BordereauValidationError(
                        f"{lob.title()} bordereau must have at least one of: {', '.join(sorted(g))}. "
                        f"Found columns: {', '.join(self.columns)}"
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
                raise BordereauValidationError(
                    f"Invalid {lob.title()} exposure columns. "
                    f"Errors: {'; '.join(errors)}. "
                    f"Found columns: {', '.join(self.columns)}"
                )

    def _validate_exposure_columns_via_schema(self, lob: str):
        """Méthode privée utilisée par validate() - utilise la logique interne."""
        try:
            self._validate_exposure_via_schema(lob)
        except BordereauValidationError as e:
            # Convertit l'exception en ajout d'erreur pour la validation globale
            self.validation_errors.append(str(e))

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
            # Les colonnes sont déjà canonisées/typées par _normalize_columns
            yield Policy(raw=row.to_dict(), lob=self.line_of_business)

    def policies(self) -> Iterable[Policy]:
        return iter(self)

    def head(self, n: int = 5) -> "Bordereau":
        return Bordereau(
            self._df.head(n).copy(),
            line_of_business=self.line_of_business,
            source=self.source,
        )

    def filter(self, expr: str) -> "Bordereau":
        """Filtre via DataFrame.query et retourne un nouveau Bordereau."""
        return Bordereau(
            self._df.query(expr).copy(),
            line_of_business=self.line_of_business,
            source=self.source,
        )

    def with_line_of_business(self, lob: str) -> "Bordereau":
        """Clone avec LOB fixé/écrasé (utile si non inférable)."""
        return Bordereau(self._df.copy(), line_of_business=lob, source=self.source)

    def __repr__(self) -> str:
        src = f"source='{self.source}', " if self.source else ""
        lob = f"lob='{self.line_of_business}'" if self.line_of_business else "lob=None"
        return f"Bordereau({src}{lob}, rows={len(self)})"
