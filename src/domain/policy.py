from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
import pandas as pd

from src.domain.constants import FIELDS
from src.domain.exposure_components import ExposureComponents
from src.domain.exposure import ExposureCalculationError


@dataclass
class Policy:
    """
    Objet domaine riche représentant une police normalisée.
    - Cache les dates (inception/expiry)
    - Expose les composants d'exposition (Hull / Liability / Total)
    - Expose les valeurs de dimensions (accès direct à raw, déjà canonisé)
    """

    raw: Dict[str, Any]
    lob: Optional[str] = None  # "aviation" | "casualty" | "test"

    _inception: Optional[pd.Timestamp] = field(default=None, init=False, repr=False)
    _expiry: Optional[pd.Timestamp] = field(default=None, init=False, repr=False)
    _aviation_components: Optional[ExposureComponents] = field(
        default=None, init=False, repr=False
    )
    _casualty_total: Optional[float] = field(default=None, init=False, repr=False)
    _test_total: Optional[float] = field(default=None, init=False, repr=False)

    # --- Accès de type mapping (compat utile en interne) ---
    def get(self, key: str, default=None) -> Any:
        return self.raw.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.raw[key]

    # --- Dates (avec cache) ---
    @property
    def inception(self) -> Optional[pd.Timestamp]:
        if self._inception is None:
            val = self.get(FIELDS["INCEPTION_DATE"])
            self._inception = pd.to_datetime(val) if val is not None else None
        return self._inception

    @property
    def expiry(self) -> Optional[pd.Timestamp]:
        if self._expiry is None:
            val = self.get(FIELDS["EXPIRY_DATE"])
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
    def get_values(self, key: str) -> Optional[List[str]]:
        v = self.raw.get(key)
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        if isinstance(v, (list, tuple, set)):
            return list(v)
        return [str(v)]

    def get_dimension_value(self, dimension: str) -> Any:
        """Utilise le mapping de dimensions pour récupérer la valeur."""
        from src.domain.dimension_mapping import get_policy_value

        return get_policy_value(self.raw, dimension, self.lob)

    # --- Exposition (et composants) ---
    def exposure_components(self, uw_dept: str) -> ExposureComponents:
        uw = (uw_dept or (self.lob or "")).lower()

        if uw == "aviation":
            if self._aviation_components is None:
                from src.domain.exposure import AviationExposureCalculator
                calc = AviationExposureCalculator()
                self._aviation_components = calc.calculate_components(self.raw)
            return self._aviation_components

        if uw == "casualty":
            if self._casualty_total is None:
                from src.domain.exposure import CasualtyExposureCalculator
                self._casualty_total = CasualtyExposureCalculator().calculate(self.raw)
            return ExposureComponents(hull=self._casualty_total, liability=0.0)

        if uw == "test":
            if self._test_total is None:
                from src.domain.exposure import TestExposureCalculator
                self._test_total = TestExposureCalculator().calculate(self.raw)
            return ExposureComponents(hull=self._test_total, liability=0.0)
        
        raise ExposureCalculationError(
            f"Unknown underwriting department '{uw_dept}'. "
            f"Supported departments: aviation, casualty, test"
        )
