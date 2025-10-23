from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
import pandas as pd

from src.domain.exposure_bundle import ExposureBundle
from src.domain.schema import resolve_bordereau_column


@dataclass
class Policy:
    """
    Objet domaine riche représentant une police normalisée.
    - Cache les dates (inception/expiry)
    - Expose les composants d'exposition (Hull / Liability / Total)
    - Expose les valeurs de dimensions (accès direct à raw, déjà canonisé)
    """

    raw: Dict[str, Any]
    uw_dept: Optional[str] = (
        None  # "aviation" | "casualty" | "test" - underwriting department
    )

    _inception: Optional[pd.Timestamp] = field(default=None, init=False, repr=False)
    _expiry: Optional[pd.Timestamp] = field(default=None, init=False, repr=False)
    _bundles: Dict[str, ExposureBundle] = field(
        default_factory=dict, init=False, repr=False
    )

    # --- Accès de type mapping (compat utile en interne) ---
    def get(self, key: str, default=None) -> Any:
        return self.raw.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.raw[key]

    # --- Dates (avec cache) ---
    @property
    def inception(self) -> Optional[pd.Timestamp]:
        if self._inception is None:
            val = self.get("INCEPTION_DT")
            self._inception = pd.to_datetime(val) if val is not None else None
        return self._inception

    @property
    def expiry(self) -> Optional[pd.Timestamp]:
        if self._expiry is None:
            val = self.get("EXPIRE_DT")
            self._expiry = pd.to_datetime(val) if val is not None else None
        return self._expiry

    def is_active(self, calculation_date: str) -> tuple[bool, Optional[str]]:
        calc = pd.to_datetime(calculation_date)
        if self.expiry is not None and self.expiry <= calc:
            return (
                False,
                f"Policy expired on {self.expiry.date()} (calculation date: {calc.date()})",
            )
        return True, None

    # --- Dimensions & valeurs ---
    def get_dimension_value(self, dimension: str) -> Any:
        """
        Récupère la valeur de dimension avec mapping intelligent.
        
        Pour les dimensions de programme,
        fait le mapping vers les colonnes de bordereau appropriées selon le LOB.
        """
        # Si la dimension existe directement dans raw, la retourner
        if dimension in self.raw:
            return self.raw.get(dimension)
        
        # Sinon, essayer le mapping via resolve_bordereau_column
        col = resolve_bordereau_column(dimension, self.uw_dept)
        if col is not None:
            return self.raw.get(col)
        
        # Si la dimension n'est pas dans le mapping, lever une erreur
        raise ValueError(f"Unknown dimension '{dimension}'")

    # --- Exposition (et composants) ---
    def exposure_bundle(self, uw_dept: str) -> ExposureBundle:
        uw = uw_dept.lower()
        if uw in self._bundles:
            return self._bundles[uw]
        from src.domain.exposure import get_exposure_calculator

        calc = get_exposure_calculator(uw)
        bundle = calc.bundle(self.raw)
        self._bundles[uw] = bundle
        return bundle
