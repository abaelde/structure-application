# src/domain/bordereau.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

import pandas as pd

from src.domain.schema import COLUMNS, exposure_rules_for_lob, build_alias_to_canonical
from src.domain.schema import (
    get_all_mappable_dimensions,
)
from src.domain import Program
from src.domain.policy import Policy  # ⬅️ nouveau


class BordereauValidationError(Exception):
    pass


class Bordereau:
    """
    Wrapper autour d'un DataFrame pour :
      - Charger (CSV) et valider le bordereau
      - Exposer les colonnes de dimension réellement disponibles
      - Itérer sous forme d'objets Policy typés
      - Valider les données d'entrée selon le schéma métier
    """

    def __init__(
        self,
        df: pd.DataFrame,
        *,
        uw_dept: Optional[str] = None,
        source: Optional[str] = None,
        program: Optional[Program] = None,
    ):
        self._raw_df = df.copy()
        self._df = self._normalize_columns(self._raw_df)
        self.uw_dept = uw_dept or self._infer_uw_dept(self._df) or self._get_underwriting_department()
        self.source = source
        self.program = program  # Référence vers le programme associé
        self.validation_warnings: List[str] = []
        self.validation_errors: List[str] = []

        # Si uw_dept non fourni, on tente de l'inférer depuis la colonne line_of_business
        if self.uw_dept is None and "line_of_business" in df.columns:
            vals = (
                df["line_of_business"]
                .dropna()
                .astype(str)
                .str.lower()
                .unique()
                .tolist()
            )
            if len(vals) == 1:
                self.uw_dept = vals[0]  # ex: "aviation", "casualty", "test"

    # ──────────────────────────────────────────────────────────────────────
    # Chargement
    # ──────────────────────────────────────────────────────────────────────
    @classmethod
    def from_csv(
        cls,
        path: Union[str, Path],
        *,
        uw_dept: Optional[str] = None,
        validate: bool = True,
        read_csv_kwargs: Optional[Dict[str, object]] = None,
    ) -> "Bordereau":
        read_csv_kwargs = read_csv_kwargs or {}
        df = pd.read_csv(path, **read_csv_kwargs)
        obj = cls(df, uw_dept=uw_dept, source=str(path))
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

        # En plus : validation des colonnes d'exposition selon uw_dept, si connue
        if check_exposure_columns and self.uw_dept:
            self._accumulate_exposure_errors(self.uw_dept)

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

    def _infer_uw_dept(self, df: pd.DataFrame) -> Optional[str]:
        col = "line_of_business" # AURE
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

        underwriting_department = self.program.underwriting_department

        if not underwriting_department:
            raise BordereauValidationError(
                "Associated program must specify an underwriting_department."
            )

        return underwriting_department

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

    def _accumulate_exposure_errors(self, lob: str):
        """Méthode privée utilisée par validate() - accumule les erreurs d'exposition."""
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
        return get_all_mappable_dimensions(self.columns, self.uw_dept)

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
            yield Policy(raw=row.to_dict(), uw_dept=self.uw_dept)

    def policies(self) -> Iterable[Policy]:
        return iter(self)

    def head(self, n: int = 5) -> "Bordereau":
        return Bordereau(
            self._df.head(n).copy(),
            uw_dept=self.uw_dept,
            source=self.source,
        )

    def filter(self, expr: str) -> "Bordereau":
        """Filtre via DataFrame.query et retourne un nouveau Bordereau."""
        return Bordereau(
            self._df.query(expr).copy(),
            uw_dept=self.uw_dept,
            source=self.source,
        )

    def with_uw_dept(self, uw_dept: str) -> "Bordereau":
        """Clone avec underwriting department fixé/écrasé (utile si non inférable)."""
        return Bordereau(self._df.copy(), uw_dept=uw_dept, source=self.source)

    def __repr__(self) -> str:
        src = f"source='{self.source}', " if self.source else ""
        uw_dept = f"uw_dept='{self.uw_dept}'" if self.uw_dept else "uw_dept=None"
        return f"Bordereau({src}{uw_dept}, rows={len(self)})"
