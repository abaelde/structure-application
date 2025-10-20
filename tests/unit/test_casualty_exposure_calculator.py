import pytest
from src.domain.exposure import (
    get_exposure_calculator,
    CasualtyExposureCalculator,
    TestExposureCalculator,
    ExposureCalculationError,
)


class TestCasualtyExposureCalculator:
    def test_calculate_valid_exposure(self):
        """
        Test de calcul d'exposition casualty standard

        DONNÉES:
        - Limit: 1M
        - Cedent Share: 75%

        ATTENDU:
        - Total: 750K
        """
        calculator = CasualtyExposureCalculator()
        policy_data = {
            "LIMIT": 1_000_000,
            "CEDENT_SHARE": 0.75,
        }

        result = calculator.calculate(policy_data)

        assert result == 750_000

    def test_calculate_with_string_value(self):
        """
        Test de calcul avec des valeurs string (conversion automatique)

        DONNÉES:
        - Limit: "1000000"
        - Cedent Share: "0.75"

        ATTENDU:
        - Total: 750K
        """
        calculator = CasualtyExposureCalculator()
        policy_data = {
            "LIMIT": "1000000",
            "CEDENT_SHARE": "0.75",
        }

        result = calculator.calculate(policy_data)

        assert result == 750_000

    def test_calculate_missing_limit(self):
        """
        Test d'erreur quand LIMIT est manquant

        DONNÉES:
        - Limit: manquant
        - Cedent Share: 75%

        ATTENDU:
        - Exception ExposureCalculationError
        """
        calculator = CasualtyExposureCalculator()
        policy_data = {
            "CEDENT_SHARE": 0.75,
        }

        with pytest.raises(ExposureCalculationError) as exc_info:
            calculator.calculate(policy_data)

        assert "Missing exposure value" in str(exc_info.value)
        assert "LIMIT" in str(exc_info.value)

    def test_calculate_missing_cedent_share(self):
        """
        Test d'erreur quand CEDENT_SHARE est manquant

        DONNÉES:
        - Limit: 1M
        - Cedent Share: manquant

        ATTENDU:
        - Exception ExposureCalculationError
        """
        calculator = CasualtyExposureCalculator()
        policy_data = {
            "LIMIT": 1_000_000,
        }

        with pytest.raises(ExposureCalculationError) as exc_info:
            calculator.calculate(policy_data)

        assert "Missing exposure value" in str(exc_info.value)
        assert "CEDENT_SHARE" in str(exc_info.value)

    def test_calculate_invalid_numeric_value(self):
        """
        Test d'erreur avec valeur numérique invalide

        DONNÉES:
        - Limit: "invalid"
        - Cedent Share: 75%

        ATTENDU:
        - Exception ExposureCalculationError
        """
        calculator = CasualtyExposureCalculator()
        policy_data = {
            "LIMIT": "invalid",
            "CEDENT_SHARE": 0.75,
        }

        with pytest.raises(ExposureCalculationError) as exc_info:
            calculator.calculate(policy_data)

        assert "Invalid numeric value" in str(exc_info.value)


class TestTestExposureCalculator:
    def test_calculate_valid_exposure(self):
        """
        Test de calcul d'exposition test (simple)

        DONNÉES:
        - Exposure: 500K

        ATTENDU:
        - Total: 500K
        """
        calculator = TestExposureCalculator()
        policy_data = {
            "exposure": 500_000,
        }

        result = calculator.calculate(policy_data)

        assert result == 500_000

    def test_calculate_with_string_value(self):
        """
        Test de calcul avec valeur string (conversion automatique)

        DONNÉES:
        - Exposure: "500000"

        ATTENDU:
        - Total: 500K
        """
        calculator = TestExposureCalculator()
        policy_data = {
            "exposure": "500000",
        }

        result = calculator.calculate(policy_data)

        assert result == 500_000

    def test_calculate_missing_exposure(self):
        """
        Test d'erreur quand exposure est manquant

        DONNÉES:
        - Exposure: manquant

        ATTENDU:
        - Exception ExposureCalculationError
        """
        calculator = TestExposureCalculator()
        policy_data = {}

        with pytest.raises(ExposureCalculationError) as exc_info:
            calculator.calculate(policy_data)

        assert "Missing exposure value" in str(exc_info.value)
        assert "exposure" in str(exc_info.value)

    def test_calculate_invalid_numeric_value(self):
        """
        Test d'erreur avec valeur numérique invalide

        DONNÉES:
        - Exposure: "invalid"

        ATTENDU:
        - Exception ExposureCalculationError
        """
        calculator = TestExposureCalculator()
        policy_data = {
            "exposure": "invalid",
        }

        with pytest.raises(ExposureCalculationError) as exc_info:
            calculator.calculate(policy_data)

        assert "Invalid numeric value" in str(exc_info.value)


class TestGetExposureCalculator:
    def test_get_aviation_calculator(self):
        """
        Test de récupération du calculateur aviation
        """
        calculator = get_exposure_calculator("aviation")
        from src.domain.exposure import AviationExposureCalculator

        assert isinstance(calculator, AviationExposureCalculator)

    def test_get_casualty_calculator(self):
        """
        Test de récupération du calculateur casualty
        """
        calculator = get_exposure_calculator("casualty")
        assert isinstance(calculator, CasualtyExposureCalculator)

    def test_get_test_calculator(self):
        """
        Test de récupération du calculateur test
        """
        calculator = get_exposure_calculator("test")
        assert isinstance(calculator, TestExposureCalculator)

    def test_get_aviation_calculator_uppercase(self):
        """
        Test de récupération du calculateur aviation en majuscules
        """
        calculator = get_exposure_calculator("AVIATION")
        from src.domain.exposure import AviationExposureCalculator

        assert isinstance(calculator, AviationExposureCalculator)

    def test_get_unknown_department(self):
        """
        Test d'erreur avec département inconnu

        ATTENDU:
        - Exception ExposureCalculationError
        """
        with pytest.raises(ExposureCalculationError) as exc_info:
            get_exposure_calculator("unknown")

        assert "Unknown underwriting department" in str(exc_info.value)
        assert "unknown" in str(exc_info.value)

    def test_get_calculator_none_department(self):
        """
        Test d'erreur avec département None

        ATTENDU:
        - Exception ExposureCalculationError
        """
        with pytest.raises(ExposureCalculationError) as exc_info:
            get_exposure_calculator(None)

        assert "Unknown underwriting department" in str(exc_info.value)

    def test_get_calculator_empty_department(self):
        """
        Test d'erreur avec département vide

        ATTENDU:
        - Exception ExposureCalculationError
        """
        with pytest.raises(ExposureCalculationError) as exc_info:
            get_exposure_calculator("")

        assert "Unknown underwriting department" in str(exc_info.value)
