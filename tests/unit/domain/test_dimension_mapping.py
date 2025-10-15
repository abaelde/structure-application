"""
Tests for the dimension mapping system.

This module tests the new configuration-driven dimension mapping between programs and bordereaux.
"""

import pytest
from src.domain.dimension_mapping import (
    get_policy_value,
    validate_program_bordereau_compatibility,
    validate_aviation_currency_consistency,
    get_all_mappable_dimensions,
    DIMENSION_COLUMN_MAPPING,
)


class TestGetPolicyValue:
    """Test the get_policy_value function."""
    
    def test_direct_mapping(self):
        """Test direct string mapping for standard dimensions."""
        policy_data = {
            "BUSCL_COUNTRY_CD": "France",
            "BUSCL_REGION": "Europe",
            "CURRENCY": "EUR"
        }
        
        assert get_policy_value(policy_data, "BUSCL_COUNTRY_CD") == "France"
        assert get_policy_value(policy_data, "BUSCL_REGION") == "Europe"
    
    def test_currency_mapping_aviation(self):
        """Test currency mapping for aviation line of business."""
        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "USD"
        }
        
        result = get_policy_value(policy_data, "BUSCL_LIMIT_CURRENCY_CD", "aviation")
        assert result == "USD"
    
    def test_currency_mapping_casualty(self):
        """Test currency mapping for casualty line of business."""
        policy_data = {
            "CURRENCY": "EUR"
        }
        
        result = get_policy_value(policy_data, "BUSCL_LIMIT_CURRENCY_CD", "casualty")
        assert result == "EUR"
    
    def test_missing_dimension_returns_none(self):
        """Test that missing dimensions return None (default regime)."""
        policy_data = {
            "POLICY_ID": "TEST-001"
        }
        
        result = get_policy_value(policy_data, "BUSCL_COUNTRY_CD")
        assert result is None
        
        result = get_policy_value(policy_data, "BUSCL_LIMIT_CURRENCY_CD", "aviation")
        assert result is None
    
    def test_fallback_to_direct_name(self):
        """Test fallback to direct column name if not in mapping."""
        policy_data = {
            "CUSTOM_DIMENSION": "custom_value"
        }
        
        result = get_policy_value(policy_data, "CUSTOM_DIMENSION")
        assert result == "custom_value"
    
    def test_aviation_currency_inconsistency_uses_hull(self):
        """Test that aviation currency inconsistency uses HULL_CURRENCY."""
        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "EUR"  # Different from HULL
        }
        
        result = get_policy_value(policy_data, "BUSCL_LIMIT_CURRENCY_CD", "aviation")
        assert result == "USD"  # Should take HULL_CURRENCY


class TestValidateProgramBordereauCompatibility:
    """Test the compatibility validation function."""
    
    def test_all_dimensions_mappable(self):
        """Test when all program dimensions are mappable."""
        program_dimensions = ["BUSCL_COUNTRY_CD", "BUSCL_REGION"]
        bordereau_columns = ["BUSCL_COUNTRY_CD", "BUSCL_REGION", "CURRENCY"]
        
        errors, warnings = validate_program_bordereau_compatibility(
            program_dimensions, bordereau_columns, "casualty"
        )
        
        assert errors == []  # No errors
        assert warnings == []  # No warnings
    
    def test_missing_dimensions_generate_warnings(self):
        """Test that missing dimensions generate warnings, not errors."""
        program_dimensions = ["BUSCL_COUNTRY_CD", "BUSCL_REGION", "BUSCL_LIMIT_CURRENCY_CD"]
        bordereau_columns = ["BUSCL_COUNTRY_CD"]  # Missing REGION and CURRENCY
        
        errors, warnings = validate_program_bordereau_compatibility(
            program_dimensions, bordereau_columns, "casualty"
        )
        
        assert errors == []  # No errors - all dimensions are optional
        assert len(warnings) == 2  # Two missing dimensions
        assert "BUSCL_REGION" in warnings[0]
        assert "BUSCL_LIMIT_CURRENCY_CD" in warnings[1]
    
    def test_aviation_currency_mapping(self):
        """Test aviation currency dimension mapping."""
        program_dimensions = ["BUSCL_LIMIT_CURRENCY_CD"]
        bordereau_columns = ["HULL_CURRENCY", "LIABILITY_CURRENCY"]
        
        errors, warnings = validate_program_bordereau_compatibility(
            program_dimensions, bordereau_columns, "aviation"
        )
        
        assert errors == []
        assert warnings == []  # HULL_CURRENCY is mappable
    
    def test_casualty_currency_mapping(self):
        """Test casualty currency dimension mapping."""
        program_dimensions = ["BUSCL_LIMIT_CURRENCY_CD"]
        bordereau_columns = ["CURRENCY"]
        
        errors, warnings = validate_program_bordereau_compatibility(
            program_dimensions, bordereau_columns, "casualty"
        )
        
        assert errors == []
        assert warnings == []  # CURRENCY is mappable


class TestValidateAviationCurrencyConsistency:
    """Test the aviation currency consistency validation."""
    
    def test_aviation_with_both_currency_columns(self):
        """Test aviation validation when both currency columns are present."""
        bordereau_columns = ["HULL_CURRENCY", "LIABILITY_CURRENCY"]
        
        warnings = validate_aviation_currency_consistency(bordereau_columns, "aviation")
        
        assert len(warnings) > 0
        assert "HULL_CURRENCY" in warnings[0]
        assert "LIABILITY_CURRENCY" in warnings[0]
    
    def test_aviation_with_one_currency_column(self):
        """Test aviation validation with only one currency column."""
        bordereau_columns = ["HULL_CURRENCY"]
        
        warnings = validate_aviation_currency_consistency(bordereau_columns, "aviation")
        
        assert warnings == []  # No warning if only one column
    
    def test_casualty_no_warning(self):
        """Test that casualty line of business generates no warnings."""
        bordereau_columns = ["CURRENCY"]
        
        warnings = validate_aviation_currency_consistency(bordereau_columns, "casualty")
        
        assert warnings == []
    
    def test_no_currency_columns(self):
        """Test when no currency columns are present."""
        bordereau_columns = ["BUSCL_COUNTRY_CD"]
        
        warnings = validate_aviation_currency_consistency(bordereau_columns, "aviation")
        
        assert warnings == []  # No warning if no currency columns


class TestGetAllMappableDimensions:
    """Test the get_all_mappable_dimensions function."""
    
    def test_casualty_mappable_dimensions(self):
        """Test getting mappable dimensions for casualty."""
        bordereau_columns = [
            "BUSCL_COUNTRY_CD", 
            "BUSCL_REGION", 
            "CURRENCY",
            "POLICY_ID"  # Not in mapping
        ]
        
        mappable = get_all_mappable_dimensions(bordereau_columns, "casualty")
        
        assert "BUSCL_COUNTRY_CD" in mappable
        assert "BUSCL_REGION" in mappable
        assert "BUSCL_LIMIT_CURRENCY_CD" in mappable
        assert mappable["BUSCL_LIMIT_CURRENCY_CD"] == "CURRENCY"
    
    def test_aviation_mappable_dimensions(self):
        """Test getting mappable dimensions for aviation."""
        bordereau_columns = [
            "BUSCL_COUNTRY_CD",
            "HULL_CURRENCY",
            "LIABILITY_CURRENCY"
        ]
        
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
        assert isinstance(DIMENSION_COLUMN_MAPPING, dict)
        
        # Test direct mappings
        assert DIMENSION_COLUMN_MAPPING["BUSCL_COUNTRY_CD"] == "BUSCL_COUNTRY_CD"
        assert DIMENSION_COLUMN_MAPPING["BUSCL_REGION"] == "BUSCL_REGION"
        
        # Test complex mappings
        currency_mapping = DIMENSION_COLUMN_MAPPING["BUSCL_LIMIT_CURRENCY_CD"]
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
            "BUSCL_LIMIT_CURRENCY_CD"
        ]
        
        for dimension in expected_dimensions:
            assert dimension in DIMENSION_COLUMN_MAPPING


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
            "LIABILITY_LIMIT": 1000000000
        }
        
        # Test all dimension mappings
        assert get_policy_value(policy_data, "BUSCL_COUNTRY_CD") == "France"
        assert get_policy_value(policy_data, "BUSCL_REGION") == "Europe"
        assert get_policy_value(policy_data, "BUSCL_LIMIT_CURRENCY_CD", "aviation") == "USD"
        
        # Test missing optional dimension
        assert get_policy_value(policy_data, "BUSCL_ENTITY_NAME_CED") is None
    
    def test_casualty_bordereau_scenario(self):
        """Test realistic casualty bordereau scenario."""
        policy_data = {
            "POLICY_ID": "CAS-2024-001",
            "INSURED_NAME": "CARREFOUR SA",
            "BUSCL_COUNTRY_CD": "France",
            "BUSCL_REGION": "Europe",
            "CURRENCY": "EUR",
            "LIMIT": 8500000
        }
        
        # Test all dimension mappings
        assert get_policy_value(policy_data, "BUSCL_COUNTRY_CD") == "France"
        assert get_policy_value(policy_data, "BUSCL_REGION") == "Europe"
        assert get_policy_value(policy_data, "BUSCL_LIMIT_CURRENCY_CD", "casualty") == "EUR"
        
        # Test missing optional dimension
        assert get_policy_value(policy_data, "BUSCL_ENTITY_NAME_CED") is None
    
    def test_minimal_bordereau_scenario(self):
        """Test minimal bordereau with only essential columns."""
        policy_data = {
            "POLICY_ID": "MIN-2024-001",
            "CURRENCY": "USD"
        }
        
        # All dimensions should return None except currency
        assert get_policy_value(policy_data, "BUSCL_COUNTRY_CD") is None
        assert get_policy_value(policy_data, "BUSCL_REGION") is None
        assert get_policy_value(policy_data, "BUSCL_LIMIT_CURRENCY_CD", "casualty") == "USD"
        
        # Should not crash
        errors, warnings = validate_program_bordereau_compatibility(
            ["BUSCL_COUNTRY_CD", "BUSCL_LIMIT_CURRENCY_CD"], 
            ["CURRENCY"], 
            "casualty"
        )
        assert errors == []
        assert len(warnings) == 1  # Only BUSCL_COUNTRY_CD missing
