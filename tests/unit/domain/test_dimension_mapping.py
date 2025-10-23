"""
Tests for the dimension mapping system.

This module tests the new configuration-driven dimension mapping between programs and bordereaux.
"""

import pytest
from src.domain.schema import (
    get_all_mappable_dimensions,
)
from src.domain.policy import Policy
from src.domain.schema import PROGRAM_TO_BORDEREAU_DIMENSIONS


class TestPolicyDimensionValue:
    """Test the Policy.get_dimension_value function."""

    def test_direct_mapping(self):
        """Test direct string mapping for standard dimensions."""
        policy_data = {
            "COUNTRY": "France",
            "REGION": "Europe",
            "CURRENCY": "EUR",
        }

        policy = Policy(raw=policy_data)
        assert policy.get_dimension_value("COUNTRY") == "France"
        assert policy.get_dimension_value("REGION") == "Europe"

    def test_currency_mapping_aviation(self):
        """Test currency mapping for aviation line of business."""
        policy_data = {"CURRENCY": "USD"}

        policy = Policy(raw=policy_data, uw_dept="aviation")
        result = policy.get_dimension_value("CURRENCY")
        assert result == "USD"

    def test_currency_mapping_casualty(self):
        """Test currency mapping for casualty line of business."""
        policy_data = {"CURRENCY": "EUR"}

        policy = Policy(raw=policy_data, uw_dept="casualty")
        result = policy.get_dimension_value("CURRENCY")
        assert result == "EUR"

    def test_missing_dimension_returns_none(self):
        """Test that missing dimensions return None (default regime)."""
        policy_data = {"POLICY_ID": "TEST-001"}

        policy = Policy(raw=policy_data)
        result = policy.get_dimension_value("COUNTRY")
        assert result is None

        policy_aviation = Policy(raw=policy_data, uw_dept="aviation")
        result = policy_aviation.get_dimension_value("CURRENCY")
        assert result is None

    def test_unknown_dimension_raises_error(self):
        """Test that unknown dimensions raise a clear error."""
        policy_data = {"POLICY_ID": "TEST-001"}

        policy = Policy(raw=policy_data)
        with pytest.raises(ValueError, match="Unknown dimension 'CUSTOM_DIMENSION'"):
            policy.get_dimension_value("CUSTOM_DIMENSION")

    def test_aviation_currency_inconsistency_uses_hull(self):
        """Test that aviation currency inconsistency uses HULL_CURRENCY."""
        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIAB_CURRENCY": "EUR",  # Different from HULL
        }

        policy = Policy(raw=policy_data, uw_dept="aviation")
        result = policy.get_dimension_value("CURRENCY")
        assert result == "USD"  # Should take HULL_CURRENCY


class TestGetAllMappableDimensions:
    """Test the get_all_mappable_dimensions function."""

    def test_casualty_mappable_dimensions(self):
        """Test getting mappable dimensions for casualty."""
        bordereau_columns = [
            "COUNTRY",
            "REGION",
            "CURRENCY",
            "POLICY_ID",  # Not in mapping
        ]

        mappable = get_all_mappable_dimensions(bordereau_columns, "casualty")

        assert "COUNTRY" in mappable
        assert "REGION" in mappable
        assert "CURRENCY" in mappable
        assert mappable["CURRENCY"] == "CURRENCY"

    def test_aviation_mappable_dimensions(self):
        """Test getting mappable dimensions for aviation."""
        bordereau_columns = ["COUNTRY", "HULL_CURRENCY", "LIAB_CURRENCY"]

        mappable = get_all_mappable_dimensions(bordereau_columns, "aviation")

        assert "COUNTRY" in mappable
        assert "CURRENCY" in mappable
        assert mappable["CURRENCY"] == "HULL_CURRENCY"

    def test_no_mappable_dimensions(self):
        """Test when no dimensions are mappable."""
        bordereau_columns = ["POLICY_ID", "CUSTOM_COLUMN"]

        mappable = get_all_mappable_dimensions(bordereau_columns, "casualty")

        assert mappable == {}


class TestDimensionMappingConfiguration:
    """Test the dimension mapping configuration."""

    def test_mapping_structure(self):
        """Test that the mapping configuration has the expected structure."""
        assert isinstance(PROGRAM_TO_BORDEREAU_DIMENSIONS, dict)

        # Test direct mappings
        assert PROGRAM_TO_BORDEREAU_DIMENSIONS["COUNTRY"] == "COUNTRY"
        assert PROGRAM_TO_BORDEREAU_DIMENSIONS["REGION"] == "REGION"

        # Test complex mappings
        currency_mapping = PROGRAM_TO_BORDEREAU_DIMENSIONS["CURRENCY"]
        assert isinstance(currency_mapping, dict)
        assert currency_mapping["aviation"] == "HULL_CURRENCY"
        assert currency_mapping["casualty"] == "CURRENCY"

    def test_all_expected_dimensions_present(self):
        """Test that all expected dimensions are present in the mapping."""
        expected_dimensions = [
            "COUNTRY",
            "REGION",
            "PRODUCT_TYPE_LEVEL_1",
            "PRODUCT_TYPE_LEVEL_2",
            "PRODUCT_TYPE_LEVEL_3",
            "CURRENCY",
        ]

        for dimension in expected_dimensions:
            assert dimension in PROGRAM_TO_BORDEREAU_DIMENSIONS


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_aviation_bordereau_scenario(self):
        """Test realistic aviation bordereau scenario."""
        policy_data = {
            "POLICY_ID": "AVI-2024-001",
            "INSURED_NAME": "AIR FRANCE-KLM",
            "COUNTRY": "France",
            "REGION": "Europe",
            "HULL_CURRENCY": "USD",
            "LIAB_CURRENCY": "USD",
            "HULL_LIMIT": 250000000,
            "LIAB_LIMIT": 1000000000,
        }

        # Test all dimension mappings
        policy = Policy(raw=policy_data, uw_dept="aviation")
        assert policy.get_dimension_value("COUNTRY") == "France"
        assert policy.get_dimension_value("REGION") == "Europe"
        assert policy.get_dimension_value("CURRENCY") == "USD"

        # Test missing optional dimension
        assert policy.get_dimension_value("PRODUCT_TYPE_LEVEL_1") is None

    def test_casualty_bordereau_scenario(self):
        """Test realistic casualty bordereau scenario."""
        policy_data = {
            "POLICY_ID": "CAS-2024-001",
            "INSURED_NAME": "CARREFOUR SA",
            "COUNTRY": "France",
            "REGION": "Europe",
            "CURRENCY": "EUR",
            "OCCURRENCE_LIMIT_100_ORIG": 8500000,
        }

        # Test all dimension mappings
        policy = Policy(raw=policy_data, uw_dept="casualty")
        assert policy.get_dimension_value("COUNTRY") == "France"
        assert policy.get_dimension_value("REGION") == "Europe"
        assert policy.get_dimension_value("CURRENCY") == "EUR"

        # Test missing optional dimension
        assert policy.get_dimension_value("PRODUCT_TYPE_LEVEL_1") is None

    def test_minimal_bordereau_scenario(self):
        """Test minimal bordereau with only essential columns."""
        policy_data = {"POLICY_ID": "MIN-2024-001", "CURRENCY": "USD"}

        # All dimensions should return None except currency
        policy = Policy(raw=policy_data, uw_dept="casualty")
        assert policy.get_dimension_value("COUNTRY") is None
        assert policy.get_dimension_value("REGION") is None
        assert policy.get_dimension_value("CURRENCY") == "USD"
