import pytest
from src.engine.exposure_calculator import (
    get_exposure_calculator,
    AviationExposureCalculator,
    CasualtyExposureCalculator,
    TestExposureCalculator,
    ExposureCalculationError,
)


class TestAviationExposureCalculator:
    def test_calculate_valid_exposure(self):
        calculator = AviationExposureCalculator()
        policy_data = {
            "HULL_LIMIT": 50_000_000,
            "LIABILITY_LIMIT": 300_000_000,
            "HULL_SHARE": 0.15,
            "LIABILITY_SHARE": 0.10,
        }
        
        result = calculator.calculate(policy_data)
        
        expected = (50_000_000 * 0.15) + (300_000_000 * 0.10)
        assert result == expected
        assert result == 37_500_000

    def test_calculate_with_string_values(self):
        calculator = AviationExposureCalculator()
        policy_data = {
            "HULL_LIMIT": "50000000",
            "LIABILITY_LIMIT": "300000000",
            "HULL_SHARE": "0.15",
            "LIABILITY_SHARE": "0.10",
        }
        
        result = calculator.calculate(policy_data)
        
        assert result == 37_500_000

    def test_calculate_missing_hull_limit(self):
        calculator = AviationExposureCalculator()
        policy_data = {
            "LIABILITY_LIMIT": 300_000_000,
            "LIABILITY_SHARE": 0.10,
        }
        
        result = calculator.calculate(policy_data)
        
        assert result == 300_000_000 * 0.10
        assert result == 30_000_000

    def test_calculate_missing_liability_limit(self):
        calculator = AviationExposureCalculator()
        policy_data = {
            "HULL_LIMIT": 50_000_000,
            "HULL_SHARE": 0.15,
        }
        
        result = calculator.calculate(policy_data)
        
        assert result == 50_000_000 * 0.15
        assert result == 7_500_000

    def test_calculate_missing_hull_share(self):
        calculator = AviationExposureCalculator()
        policy_data = {
            "HULL_LIMIT": 50_000_000,
            "LIABILITY_LIMIT": 300_000_000,
            "LIABILITY_SHARE": 0.10,
        }
        
        with pytest.raises(ExposureCalculationError) as exc_info:
            calculator.calculate(policy_data)
        
        assert "Missing HULL_SHARE value" in str(exc_info.value)
        assert "HULL_SHARE" in str(exc_info.value)

    def test_calculate_missing_liability_share(self):
        calculator = AviationExposureCalculator()
        policy_data = {
            "HULL_LIMIT": 50_000_000,
            "LIABILITY_LIMIT": 300_000_000,
            "HULL_SHARE": 0.15,
        }
        
        with pytest.raises(ExposureCalculationError) as exc_info:
            calculator.calculate(policy_data)
        
        assert "Missing LIABILITY_SHARE value" in str(exc_info.value)
        assert "LIABILITY_SHARE" in str(exc_info.value)

    def test_calculate_invalid_numeric_value(self):
        calculator = AviationExposureCalculator()
        policy_data = {
            "HULL_LIMIT": "not_a_number",
            "LIABILITY_LIMIT": 300_000_000,
            "HULL_SHARE": 0.15,
            "LIABILITY_SHARE": 0.10,
        }
        
        with pytest.raises(ExposureCalculationError) as exc_info:
            calculator.calculate(policy_data)
        
        assert "Invalid numeric values" in str(exc_info.value)

    def test_get_required_columns(self):
        calculator = AviationExposureCalculator()
        required = calculator.get_required_columns()
        
        assert required == ["HULL_LIMIT", "LIABILITY_LIMIT", "HULL_SHARE", "LIABILITY_SHARE"]

    def test_realistic_aviation_exposure(self):
        calculator = AviationExposureCalculator()
        policy_data = {
            "HULL_LIMIT": 250_000_000,
            "LIABILITY_LIMIT": 1_000_000_000,
            "HULL_SHARE": 0.15,
            "LIABILITY_SHARE": 0.10,
        }
        
        result = calculator.calculate(policy_data)
        hull_exposure = 250_000_000 * 0.15
        liability_exposure = 1_000_000_000 * 0.10
        
        assert result == hull_exposure + liability_exposure
        assert result == 137_500_000

    def test_calculate_missing_both_exposures(self):
        """
        Test que le calculateur retourne 0.0 quand aucune exposition n'est presente.
        
        Note: La validation de la presence des colonnes d'exposition au niveau DataFrame
        est faite par validate_exposure_columns(). Le calculateur traite ligne par ligne
        et retourne 0.0 si aucune valeur d'exposition n'est presente sur cette ligne.
        """
        calculator = AviationExposureCalculator()
        policy_data = {
            "HULL_LIMIT": None,
            "LIABILITY_LIMIT": None,
            "HULL_SHARE": 0.15,
            "LIABILITY_SHARE": 0.10,
        }
        
        result = calculator.calculate(policy_data)
        assert result == 0.0

    def test_calculate_hull_share_without_hull_limit(self):
        calculator = AviationExposureCalculator()
        policy_data = {
            "LIABILITY_LIMIT": 300_000_000,
            "HULL_SHARE": 0.15,
            "LIABILITY_SHARE": 0.10,
        }
        
        result = calculator.calculate(policy_data)
        
        assert result == 300_000_000 * 0.10
        assert result == 30_000_000

    def test_calculate_liability_share_without_liability_limit(self):
        calculator = AviationExposureCalculator()
        policy_data = {
            "HULL_LIMIT": 50_000_000,
            "HULL_SHARE": 0.15,
            "LIABILITY_SHARE": 0.10,
        }
        
        result = calculator.calculate(policy_data)
        
        assert result == 50_000_000 * 0.15
        assert result == 7_500_000


class TestCasualtyExposureCalculator:
    def test_calculate_valid_exposure(self):
        calculator = CasualtyExposureCalculator()
        policy_data = {
            "LIMIT": 1_000_000,
            "CEDENT_SHARE": 0.75,
        }
        
        result = calculator.calculate(policy_data)
        
        assert result == 750_000

    def test_calculate_with_string_value(self):
        calculator = CasualtyExposureCalculator()
        policy_data = {
            "LIMIT": "1000000",
            "CEDENT_SHARE": "0.75",
        }
        
        result = calculator.calculate(policy_data)
        
        assert result == 750_000

    def test_calculate_missing_limit(self):
        calculator = CasualtyExposureCalculator()
        policy_data = {
            "CEDENT_SHARE": 0.75,
        }
        
        with pytest.raises(ExposureCalculationError) as exc_info:
            calculator.calculate(policy_data)
        
        assert "Missing exposure value" in str(exc_info.value)
        assert "LIMIT" in str(exc_info.value)

    def test_calculate_missing_cedent_share(self):
        calculator = CasualtyExposureCalculator()
        policy_data = {
            "LIMIT": 1_000_000,
        }
        
        with pytest.raises(ExposureCalculationError) as exc_info:
            calculator.calculate(policy_data)
        
        assert "Missing exposure value" in str(exc_info.value)
        assert "CEDENT_SHARE" in str(exc_info.value)

    def test_calculate_invalid_numeric_value(self):
        calculator = CasualtyExposureCalculator()
        policy_data = {
            "LIMIT": "invalid",
            "CEDENT_SHARE": 0.75,
        }
        
        with pytest.raises(ExposureCalculationError) as exc_info:
            calculator.calculate(policy_data)
        
        assert "Invalid numeric value" in str(exc_info.value)

    def test_get_required_columns(self):
        calculator = CasualtyExposureCalculator()
        required = calculator.get_required_columns()
        
        assert required == ["LIMIT", "CEDENT_SHARE"]


class TestTestExposureCalculator:
    def test_calculate_valid_exposure(self):
        calculator = TestExposureCalculator()
        policy_data = {
            "exposure": 500_000,
        }
        
        result = calculator.calculate(policy_data)
        
        assert result == 500_000

    def test_calculate_with_string_value(self):
        calculator = TestExposureCalculator()
        policy_data = {
            "exposure": "500000",
        }
        
        result = calculator.calculate(policy_data)
        
        assert result == 500_000

    def test_calculate_missing_exposure(self):
        calculator = TestExposureCalculator()
        policy_data = {}
        
        with pytest.raises(ExposureCalculationError) as exc_info:
            calculator.calculate(policy_data)
        
        assert "Missing exposure value" in str(exc_info.value)
        assert "exposure" in str(exc_info.value)

    def test_calculate_invalid_numeric_value(self):
        calculator = TestExposureCalculator()
        policy_data = {
            "exposure": "invalid",
        }
        
        with pytest.raises(ExposureCalculationError) as exc_info:
            calculator.calculate(policy_data)
        
        assert "Invalid numeric value" in str(exc_info.value)

    def test_get_required_columns(self):
        calculator = TestExposureCalculator()
        required = calculator.get_required_columns()
        
        assert required == ["exposure"]


class TestGetExposureCalculator:
    def test_get_aviation_calculator(self):
        calculator = get_exposure_calculator("aviation")
        assert isinstance(calculator, AviationExposureCalculator)

    def test_get_casualty_calculator(self):
        calculator = get_exposure_calculator("casualty")
        assert isinstance(calculator, CasualtyExposureCalculator)

    def test_get_test_calculator(self):
        calculator = get_exposure_calculator("test")
        assert isinstance(calculator, TestExposureCalculator)

    def test_get_aviation_calculator_uppercase(self):
        calculator = get_exposure_calculator("AVIATION")
        assert isinstance(calculator, AviationExposureCalculator)

    def test_get_unknown_department(self):
        with pytest.raises(ExposureCalculationError) as exc_info:
            get_exposure_calculator("unknown")
        
        assert "Unknown underwriting department" in str(exc_info.value)
        assert "unknown" in str(exc_info.value)

    def test_get_calculator_none_department(self):
        with pytest.raises(ExposureCalculationError) as exc_info:
            get_exposure_calculator(None)
        
        assert "Unknown underwriting department" in str(exc_info.value)

    def test_get_calculator_empty_department(self):
        with pytest.raises(ExposureCalculationError) as exc_info:
            get_exposure_calculator("")
        
        assert "Unknown underwriting department" in str(exc_info.value)

