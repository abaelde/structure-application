# src/domain/exposure.py
from typing import Dict, Any
from abc import ABC, abstractmethod
from src.domain.exposure_bundle import ExposureBundle


class ExposureCalculationError(Exception):
    pass


class ExposureCalculator(ABC):
    @abstractmethod
    def calculate(self, policy_data: Dict[str, Any]) -> float: ...

    # Ajout : constructeur générique de bundle (par défaut : total seul)
    def bundle(self, policy_data: Dict[str, Any]) -> ExposureBundle:
        return ExposureBundle(total=self.calculate(policy_data))


class AviationExposureCalculator(ExposureCalculator):
    def bundle(self, policy_data: Dict[str, Any]) -> ExposureBundle:
        hull_limit = policy_data.get("HULL_LIMIT")
        liability_limit = policy_data.get("LIAB_LIMIT")
        hull_share = policy_data.get("HULL_SHARE")
        liability_share = policy_data.get("LIAB_SHARE")

        has_hull = hull_limit is not None
        has_liability = liability_limit is not None

        hull_exposure = 0.0
        liability_exposure = 0.0

        if has_hull:
            if hull_share is None:
                raise ExposureCalculationError(
                    f"Missing HULL_SHARE value for this policy. "
                    f"HULL_LIMIT={hull_limit}, HULL_SHARE={hull_share}"
                )
            try:
                hull_exposure = float(hull_limit) * float(hull_share)
            except (ValueError, TypeError) as e:
                raise ExposureCalculationError(
                    f"Invalid numeric values for Hull exposure: {e}"
                )

        if has_liability:
            if liability_share is None:
                raise ExposureCalculationError(
                    f"Missing LIAB_SHARE value for this policy. "
                    f"LIAB_LIMIT={liability_limit}, LIAB_SHARE={liability_share}"
                )
            try:
                liability_exposure = float(liability_limit) * float(liability_share)
            except (ValueError, TypeError) as e:
                raise ExposureCalculationError(
                    f"Invalid numeric values for Liability exposure: {e}"
                )

        return ExposureBundle(
            total=hull_exposure + liability_exposure,
            components={"hull": hull_exposure, "liability": liability_exposure},
        )

    def calculate(self, policy_data: Dict[str, Any]) -> float:
        return self.bundle(policy_data).total


class CasualtyExposureCalculator(ExposureCalculator):
    def calculate(self, policy_data: Dict[str, Any]) -> float:
        limit = policy_data.get("OCCURRENCE_LIMIT_100_ORIG")
        cedent_share = policy_data.get("CEDENT_SHARE")

        if limit is None or cedent_share is None:
            raise ExposureCalculationError(
                f"Missing exposure value for this policy. "
                f"OCCURRENCE_LIMIT_100_ORIG={limit}, CEDENT_SHARE={cedent_share}"
            )

        try:
            return float(limit) * float(cedent_share)
        except (ValueError, TypeError) as e:
            raise ExposureCalculationError(
                f"Invalid numeric value in Casualty exposure columns: {e}"
            )


class TestExposureCalculator(ExposureCalculator):
    def calculate(self, policy_data: Dict[str, Any]) -> float:
        exposure = policy_data.get("exposure")
        if exposure is None:
            raise ExposureCalculationError(
                f"Missing exposure value for this policy. exposure={exposure}"
            )
        try:
            return float(exposure)
        except (ValueError, TypeError) as e:
            raise ExposureCalculationError(
                f"Invalid numeric value in Test exposure column: {e}"
            )


def get_exposure_calculator(underwriting_department: str) -> ExposureCalculator:
    uw = (underwriting_department or "").lower()
    calculators = {
        "aviation": AviationExposureCalculator,
        "casualty": CasualtyExposureCalculator,
        "test": TestExposureCalculator,
    }
    cls = calculators.get(uw)
    if cls is None:
        raise ExposureCalculationError(
            f"Unknown underwriting department '{underwriting_department}'. "
            f"Supported departments: {', '.join(sorted(calculators.keys()))}"
        )
    return cls()
