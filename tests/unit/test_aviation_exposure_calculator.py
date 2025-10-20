import pytest
from src.domain.exposure import (
    AviationExposureCalculator,
    ExposureCalculationError,
)


class TestAviationExposureCalculator:
    def test_calculate_valid_exposure(self):
        """
        Test de calcul d'exposition aviation avec Hull et Liability complets

        DONNÉES:
        - Hull: 50M × 15% = 7.5M
        - Liability: 300M × 10% = 30M

        ATTENDU:
        - Total: 37.5M
        """
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
        """
        Test de calcul avec des valeurs string (conversion automatique)

        DONNÉES:
        - Hull: "50000000" × "0.15" = 7.5M
        - Liability: "300000000" × "0.10" = 30M

        ATTENDU:
        - Total: 37.5M
        """
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
        """
        Test de calcul avec Hull manquant (seulement Liability)

        DONNÉES:
        - Hull: None
        - Liability: 300M × 10% = 30M

        ATTENDU:
        - Total: 30M
        """
        calculator = AviationExposureCalculator()
        policy_data = {
            "LIABILITY_LIMIT": 300_000_000,
            "LIABILITY_SHARE": 0.10,
        }

        result = calculator.calculate(policy_data)

        assert result == 300_000_000 * 0.10
        assert result == 30_000_000

    def test_calculate_missing_liability_limit(self):
        """
        Test de calcul avec Liability manquant (seulement Hull)

        DONNÉES:
        - Hull: 50M × 15% = 7.5M
        - Liability: None

        ATTENDU:
        - Total: 7.5M
        """
        calculator = AviationExposureCalculator()
        policy_data = {
            "HULL_LIMIT": 50_000_000,
            "HULL_SHARE": 0.15,
        }

        result = calculator.calculate(policy_data)

        assert result == 50_000_000 * 0.15
        assert result == 7_500_000

    def test_calculate_missing_hull_share(self):
        """
        Test d'erreur quand HULL_SHARE est manquant

        DONNÉES:
        - Hull: 50M (sans HULL_SHARE)
        - Liability: 300M × 10% = 30M

        ATTENDU:
        - Exception ExposureCalculationError
        """
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
        """
        Test d'erreur quand LIABILITY_SHARE est manquant

        DONNÉES:
        - Hull: 50M × 15% = 7.5M
        - Liability: 300M (sans LIABILITY_SHARE)

        ATTENDU:
        - Exception ExposureCalculationError
        """
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
        """
        Test d'erreur avec valeur numérique invalide

        DONNÉES:
        - Hull: "not_a_number" (invalide)
        - Liability: 300M × 10% = 30M

        ATTENDU:
        - Exception ExposureCalculationError
        """
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

    def test_realistic_aviation_exposure(self):
        """
        Test avec des valeurs réalistes d'aviation

        DONNÉES:
        - Hull: 250M × 15% = 37.5M
        - Liability: 1B × 10% = 100M

        ATTENDU:
        - Total: 137.5M
        """
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
        Test que le calculateur retourne 0.0 quand aucune exposition n'est présente.

        Note: La validation de la présence des colonnes d'exposition au niveau DataFrame
        est faite par validate(). Le calculateur traite ligne par ligne
        et retourne 0.0 si aucune valeur d'exposition n'est présente sur cette ligne.

        DONNÉES:
        - Hull: None
        - Liability: None

        ATTENDU:
        - Total: 0.0
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
        """
        Test avec HULL_SHARE mais sans HULL_LIMIT (seulement Liability)

        DONNÉES:
        - Hull: HULL_SHARE présent mais HULL_LIMIT manquant
        - Liability: 300M × 10% = 30M

        ATTENDU:
        - Total: 30M
        """
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
        """
        Test avec LIABILITY_SHARE mais sans LIABILITY_LIMIT (seulement Hull)

        DONNÉES:
        - Hull: 50M × 15% = 7.5M
        - Liability: LIABILITY_SHARE présent mais LIABILITY_LIMIT manquant

        ATTENDU:
        - Total: 7.5M
        """
        calculator = AviationExposureCalculator()
        policy_data = {
            "HULL_LIMIT": 50_000_000,
            "HULL_SHARE": 0.15,
            "LIABILITY_SHARE": 0.10,
        }

        result = calculator.calculate(policy_data)

        assert result == 50_000_000 * 0.15
        assert result == 7_500_000

    def test_calculate_components_with_both(self):
        """
        Test calculate_components avec Hull et Liability

        DONNÉES:
        - Hull: 100M × 15% = 15M
        - Liability: 500M × 10% = 50M

        ATTENDU:
        - Hull exposure: 15M
        - Liability exposure: 50M
        - Total: 65M
        """
        calculator = AviationExposureCalculator()
        policy_data = {
            "HULL_LIMIT": 100_000_000,
            "LIABILITY_LIMIT": 500_000_000,
            "HULL_SHARE": 0.15,
            "LIABILITY_SHARE": 0.10,
        }

        bundle = calculator.bundle(policy_data)

        assert bundle.components["hull"] == 15_000_000
        assert bundle.components["liability"] == 50_000_000
        assert bundle.total == 65_000_000

    def test_calculate_components_hull_only(self):
        """
        Test calculate_components avec seulement Hull

        DONNÉES:
        - Hull: 100M × 15% = 15M
        - Liability: None

        ATTENDU:
        - Hull exposure: 15M
        - Liability exposure: 0
        - Total: 15M
        """
        calculator = AviationExposureCalculator()
        policy_data = {
            "HULL_LIMIT": 100_000_000,
            "HULL_SHARE": 0.15,
        }

        bundle = calculator.bundle(policy_data)

        assert bundle.components["hull"] == 15_000_000
        assert bundle.components["liability"] == 0.0
        assert bundle.total == 15_000_000

    def test_calculate_components_liability_only(self):
        """
        Test calculate_components avec seulement Liability

        DONNÉES:
        - Hull: None
        - Liability: 500M × 10% = 50M

        ATTENDU:
        - Hull exposure: 0
        - Liability exposure: 50M
        - Total: 50M
        """
        calculator = AviationExposureCalculator()
        policy_data = {
            "LIABILITY_LIMIT": 500_000_000,
            "LIABILITY_SHARE": 0.10,
        }

        bundle = calculator.bundle(policy_data)

        assert bundle.components["hull"] == 0.0
        assert bundle.components["liability"] == 50_000_000
        assert bundle.total == 50_000_000

    def test_calculate_components_none(self):
        """
        Test calculate_components sans aucune exposition

        DONNÉES:
        - Hull: None
        - Liability: None

        ATTENDU:
        - Hull exposure: 0
        - Liability exposure: 0
        - Total: 0
        """
        calculator = AviationExposureCalculator()
        policy_data = {}

        bundle = calculator.bundle(policy_data)

        assert bundle.components["hull"] == 0.0
        assert bundle.components["liability"] == 0.0
        assert bundle.total == 0.0
