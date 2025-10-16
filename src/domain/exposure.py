# src/domain/exposure.py
from typing import Dict, Any
from abc import ABC, abstractmethod
from src.domain.exposure_components import ExposureComponents


class ExposureCalculationError(Exception):
    pass


class ExposureCalculator(ABC):
    @abstractmethod
    def calculate(self, policy_data: Dict[str, Any]) -> float:
        ...

    @abstractmethod
    def get_required_columns(self) -> list[str]:
        ...


class AviationExposureCalculator(ExposureCalculator):
    def calculate(self, policy_data: Dict[str, Any]) -> float:
        components = self.calculate_components(policy_data)
        return components.total

    def calculate_components(self, policy_data: Dict[str, Any]) -> ExposureComponents:
        hull_limit = policy_data.get("HULL_LIMIT")
        liability_limit = policy_data.get("LIABILITY_LIMIT")
        hull_share = policy_data.get("HULL_SHARE")
        liability_share = policy_data.get("LIABILITY_SHARE")

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
                    f"Missing LIABILITY_SHARE value for this policy. "
                    f"LIABILITY_LIMIT={liability_limit}, LIABILITY_SHARE={liability_share}"
                )
            try:
                liability_exposure = float(liability_limit) * float(liability_share)
            except (ValueError, TypeError) as e:
                raise ExposureCalculationError(
                    f"Invalid numeric values for Liability exposure: {e}"
                )

        return ExposureComponents(hull=hull_exposure, liability=liability_exposure)

    def get_required_columns(self) -> list[str]:
        return ["HULL_LIMIT", "LIABILITY_LIMIT", "HULL_SHARE", "LIABILITY_SHARE"]


class CasualtyExposureCalculator(ExposureCalculator):
    def calculate(self, policy_data: Dict[str, Any]) -> float:
        limit = policy_data.get("LIMIT")
        cedent_share = policy_data.get("CEDENT_SHARE")

        if limit is None or cedent_share is None:
            raise ExposureCalculationError(
                f"Missing exposure value for this policy. "
                f"LIMIT={limit}, CEDENT_SHARE={cedent_share}"
            )

        try:
            return float(limit) * float(cedent_share)
        except (ValueError, TypeError) as e:
            raise ExposureCalculationError(
                f"Invalid numeric value in Casualty exposure columns: {e}"
            )

    def get_required_columns(self) -> list[str]:
        return ["LIMIT", "CEDENT_SHARE"]


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

    def get_required_columns(self) -> list[str]:
        return ["exposure"]


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
