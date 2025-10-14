from typing import Dict, Any
from abc import ABC, abstractmethod


class ExposureCalculationError(Exception):
    pass


class ExposureCalculator(ABC):
    @abstractmethod
    def calculate(self, policy_data: Dict[str, Any]) -> float:
        pass

    @abstractmethod
    def get_required_columns(self) -> list[str]:
        pass


class AviationExposureCalculator(ExposureCalculator):
    def calculate(self, policy_data: Dict[str, Any]) -> float:
        hull_limit = policy_data.get("HULL_LIMIT")
        liability_limit = policy_data.get("LIABILITY_LIMIT")
        hull_share = policy_data.get("HULL_SHARE")
        liability_share = policy_data.get("LIABILITY_SHARE")

        has_hull = hull_limit is not None
        has_liability = liability_limit is not None

        total_exposure = 0.0

        if has_hull:
            if hull_share is None:
                raise ExposureCalculationError(
                    f"Missing HULL_SHARE value for this policy. "
                    f"HULL_LIMIT={hull_limit}, HULL_SHARE={hull_share}"
                )
            try:
                hull_limit_float = float(hull_limit)
                hull_share_float = float(hull_share)
                total_exposure += hull_limit_float * hull_share_float
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
                liability_limit_float = float(liability_limit)
                liability_share_float = float(liability_share)
                total_exposure += liability_limit_float * liability_share_float
            except (ValueError, TypeError) as e:
                raise ExposureCalculationError(
                    f"Invalid numeric values for Liability exposure: {e}"
                )

        return total_exposure

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
            limit_float = float(limit)
            cedent_share_float = float(cedent_share)
            return limit_float * cedent_share_float
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
    uw_dept_lower = underwriting_department.lower() if underwriting_department else ""

    calculators = {
        "aviation": AviationExposureCalculator,
        "casualty": CasualtyExposureCalculator,
        "test": TestExposureCalculator,
    }

    calculator_class = calculators.get(uw_dept_lower)

    if calculator_class is None:
        raise ExposureCalculationError(
            f"Unknown underwriting department '{underwriting_department}'. "
            f"Supported departments: {', '.join(sorted(calculators.keys()))}"
        )

    return calculator_class()
