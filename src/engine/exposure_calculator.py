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

        if hull_limit is None or liability_limit is None:
            raise ExposureCalculationError(
                f"Missing required exposure columns for Aviation. "
                f"Required: HULL_LIMIT, LIABILITY_LIMIT, HULL_SHARE, LIABILITY_SHARE. "
                f"Found: HULL_LIMIT={hull_limit}, LIABILITY_LIMIT={liability_limit}, "
                f"HULL_SHARE={hull_share}, LIABILITY_SHARE={liability_share}"
            )

        if hull_share is None or liability_share is None:
            raise ExposureCalculationError(
                f"Missing required share columns for Aviation. "
                f"Required: HULL_SHARE, LIABILITY_SHARE. "
                f"Found: HULL_SHARE={hull_share}, LIABILITY_SHARE={liability_share}"
            )

        try:
            hull_limit = float(hull_limit)
            liability_limit = float(liability_limit)
            hull_share = float(hull_share)
            liability_share = float(liability_share)
        except (ValueError, TypeError) as e:
            raise ExposureCalculationError(
                f"Invalid numeric values in Aviation exposure columns: {e}"
            )

        hull_exposure = hull_limit * hull_share
        liability_exposure = liability_limit * liability_share

        total_exposure = hull_exposure + liability_exposure

        return total_exposure

    def get_required_columns(self) -> list[str]:
        return ["HULL_LIMIT", "LIABILITY_LIMIT", "HULL_SHARE", "LIABILITY_SHARE"]
# ⚠️ HYPOTHÈSE FORTE (TEMPORAIRE) :
# On additionne (HULL_LIMIT × HULL_SHARE) + (LIABILITY_LIMIT × LIABILITY_SHARE)
# pour obtenir une exposition unique à passer dans le programme.
# 
# Cette sommation est une SIMPLIFICATION. Dans la réalité, HULL et LIABILITY
# sont deux expositions distinctes qui devraient être traitées séparément
# dans les calculs de cession (sections différentes, limites différentes, etc.).
# 
# TODO FUTUR: Supporter plusieurs expositions par policy (multi-exposure),
# avec des sections de programme pouvant cibler spécifiquement HULL ou LIABILITY.
        hull_exposure = hull_limit * hull_share

class CasualtyExposureCalculator(ExposureCalculator):
    def calculate(self, policy_data: Dict[str, Any]) -> float:
        limit = policy_data.get("LIMIT")

        if limit is None:
            raise ExposureCalculationError(
                f"Missing required exposure column for Casualty. "
                f"Required: LIMIT. Found: LIMIT={limit}"
            )

        try:
            return float(limit)
        except (ValueError, TypeError) as e:
            raise ExposureCalculationError(
                f"Invalid numeric value in Casualty exposure column LIMIT: {e}"
            )

    def get_required_columns(self) -> list[str]:
        return ["LIMIT"]


class TestExposureCalculator(ExposureCalculator):
    def calculate(self, policy_data: Dict[str, Any]) -> float:
        exposure = policy_data.get("exposure")

        if exposure is None:
            raise ExposureCalculationError(
                f"Missing required exposure column for Test. "
                f"Required: exposure. Found: exposure={exposure}"
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
