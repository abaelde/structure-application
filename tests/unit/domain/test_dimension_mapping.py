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
            "BUSCL_COUNTRY_CD": "France",
            "BUSCL_REGION": "Europe",
            "CURRENCY": "EUR",
        }

        policy = Policy(raw=policy_data)
        assert policy.get_dimension_value("BUSCL_COUNTRY_CD") == "France"
        assert policy.get_dimension_value("BUSCL_REGION") == "Europe"

    def test_currency_mapping_aviation(self):
        """Test currency mapping for aviation line of business."""
        policy_data = {"HULL_CURRENCY": "USD", "LIABILITY_CURRENCY": "USD"}

        policy = Policy(raw=policy_data, uw_dept="aviation")
        result = policy.get_dimension_value("BUSCL_LIMIT_CURRENCY_CD")
        assert result == "USD"

    def test_currency_mapping_casualty(self):
        """Test currency mapping for casualty line of business."""
        policy_data = {"CURRENCY": "EUR"}

        policy = Policy(raw=policy_data, uw_dept="casualty")
        result = policy.get_dimension_value("BUSCL_LIMIT_CURRENCY_CD")
        assert result == "EUR"

    def test_missing_dimension_returns_none(self):
        """Test that missing dimensions return None (default regime)."""
        policy_data = {"POLICY_ID": "TEST-001"}

        policy = Policy(raw=policy_data)
        result = policy.get_dimension_value("BUSCL_COUNTRY_CD")
        assert result is None

        policy_aviation = Policy(raw=policy_data, uw_dept="aviation")
        result = policy_aviation.get_dimension_value("BUSCL_LIMIT_CURRENCY_CD")
        assert result is None

    def test_unknown_dimension_raises_error(self):
        """Test that unknown dimensions raise a clear error."""
        policy_data = {"CUSTOM_DIMENSION": "custom_value"}

        policy = Policy(raw=policy_data)
        with pytest.raises(ValueError, match="Unknown dimension 'CUSTOM_DIMENSION'"):
            policy.get_dimension_value("CUSTOM_DIMENSION")

    def test_aviation_currency_inconsistency_uses_hull(self):
        """Test that aviation currency inconsistency uses HULL_CURRENCY."""
        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "EUR",  # Different from HULL
        }

        policy = Policy(raw=policy_data, uw_dept="aviation")
        result = policy.get_dimension_value("BUSCL_LIMIT_CURRENCY_CD")
        assert result == "USD"  # Should take HULL_CURRENCY




class TestGetAllMappableDimensions:
    """Test the get_all_mappable_dimensions function."""

    def test_casualty_mappable_dimensions(self):
        """Test getting mappable dimensions for casualty."""
        bordereau_columns = [
            "BUSCL_COUNTRY_CD",
            "BUSCL_REGION",
            "CURRENCY",
            "POLICY_ID",  # Not in mapping
        ]

        mappable = get_all_mappable_dimensions(bordereau_columns, "casualty")

        assert "BUSCL_COUNTRY_CD" in mappable
        assert "BUSCL_REGION" in mappable
        assert "BUSCL_LIMIT_CURRENCY_CD" in mappable
        assert mappable["BUSCL_LIMIT_CURRENCY_CD"] == "CURRENCY"

    def test_aviation_mappable_dimensions(self):
        """Test getting mappable dimensions for aviation."""
        bordereau_columns = ["BUSCL_COUNTRY_CD", "HULL_CURRENCY", "LIABILITY_CURRENCY"]

        mappable = get_all_mappable_dimensions(bordereau_columns, "aviation")

        assert "BUSCL_COUNTRY_CD" in mappable
        assert "BUSCL_LIMIT_CURRENCY_CD" in mappable
        assert mappable["BUSCL_LIMIT_CURRENCY_CD"] == "HULL_CURRENCY"

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
        assert PROGRAM_TO_BORDEREAU_DIMENSIONS["BUSCL_COUNTRY_CD"] == "BUSCL_COUNTRY_CD"
        assert PROGRAM_TO_BORDEREAU_DIMENSIONS["BUSCL_REGION"] == "BUSCL_REGION"

        # Test complex mappings
        currency_mapping = PROGRAM_TO_BORDEREAU_DIMENSIONS["BUSCL_LIMIT_CURRENCY_CD"]
        assert isinstance(currency_mapping, dict)
        assert currency_mapping["aviation"] == "HULL_CURRENCY"
        assert currency_mapping["casualty"] == "CURRENCY"

    def test_all_expected_dimensions_present(self):
        """Test that all expected dimensions are present in the mapping."""
        expected_dimensions = [
            "BUSCL_COUNTRY_CD",
            "BUSCL_REGION",
            "BUSCL_CLASS_OF_BUSINESS_1",
            "BUSCL_CLASS_OF_BUSINESS_2",
            "BUSCL_CLASS_OF_BUSINESS_3",
            "BUSCL_ENTITY_NAME_CED",
            "POL_RISK_NAME_CED",
            "BUSCL_EXCLUDE_CD",
            "BUSCL_LIMIT_CURRENCY_CD",
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
            "BUSCL_COUNTRY_CD": "France",
            "BUSCL_REGION": "Europe",
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "USD",
            "HULL_LIMIT": 250000000,
            "LIABILITY_LIMIT": 1000000000,
        }

        # Test all dimension mappings
        policy = Policy(raw=policy_data, uw_dept="aviation")
        assert policy.get_dimension_value("BUSCL_COUNTRY_CD") == "France"
        assert policy.get_dimension_value("BUSCL_REGION") == "Europe"
        assert policy.get_dimension_value("BUSCL_LIMIT_CURRENCY_CD") == "USD"

        # Test missing optional dimension
        assert policy.get_dimension_value("BUSCL_ENTITY_NAME_CED") is None

    def test_casualty_bordereau_scenario(self):
        """Test realistic casualty bordereau scenario."""
        policy_data = {
            "POLICY_ID": "CAS-2024-001",
            "INSURED_NAME": "CARREFOUR SA",
            "BUSCL_COUNTRY_CD": "France",
            "BUSCL_REGION": "Europe",
            "CURRENCY": "EUR",
            "LIMIT": 8500000,
        }

        # Test all dimension mappings
        policy = Policy(raw=policy_data, uw_dept="casualty")
        assert policy.get_dimension_value("BUSCL_COUNTRY_CD") == "France"
        assert policy.get_dimension_value("BUSCL_REGION") == "Europe"
        assert policy.get_dimension_value("BUSCL_LIMIT_CURRENCY_CD") == "EUR"

        # Test missing optional dimension
        assert policy.get_dimension_value("BUSCL_ENTITY_NAME_CED") is None

    def test_minimal_bordereau_scenario(self):
        """Test minimal bordereau with only essential columns."""
        policy_data = {"POLICY_ID": "MIN-2024-001", "CURRENCY": "USD"}

        # All dimensions should return None except currency
        policy = Policy(raw=policy_data, uw_dept="casualty")
        assert policy.get_dimension_value("BUSCL_COUNTRY_CD") is None
        assert policy.get_dimension_value("BUSCL_REGION") is None
        assert policy.get_dimension_value("BUSCL_LIMIT_CURRENCY_CD") == "USD"

