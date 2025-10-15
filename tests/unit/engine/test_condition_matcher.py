import pytest
import pandas as pd
from src.engine.condition_matcher import (
    map_currency_condition,
    match_condition,
    check_exclusion,
)
from src.domain import condition


class TestMapCurrencyCondition:
    """Tests for the currency mapping logic"""
    
    def test_aviation_matching_hull_currency(self):
        """Test aviation matching when hull currency matches"""
        condition_value = "USD"
        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "EUR",
        }
        line_of_business = "aviation"
        
        result = map_currency_condition(condition_value, policy_data, line_of_business)
        
        assert result is True
    
    def test_aviation_matching_liability_currency(self):
        """Test aviation matching when liability currency matches"""
        condition_value = "EUR"
        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "EUR",
        }
        line_of_business = "aviation"
        
        result = map_currency_condition(condition_value, policy_data, line_of_business)
        
        assert result is True
    
    def test_aviation_no_match(self):
        """Test aviation when neither currency matches"""
        condition_value = "GBP"
        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "EUR",
        }
        line_of_business = "aviation"
        
        result = map_currency_condition(condition_value, policy_data, line_of_business)
        
        assert result is False
    
    def test_casualty_matching(self):
        """Test casualty matching when currency matches"""
        condition_value = "USD"
        policy_data = {
            "CURRENCY": "USD",
        }
        line_of_business = "casualty"
        
        result = map_currency_condition(condition_value, policy_data, line_of_business)
        
        assert result is True
    
    def test_casualty_no_match(self):
        """Test casualty when currency doesn't match"""
        condition_value = "EUR"
        policy_data = {
            "CURRENCY": "USD",
        }
        line_of_business = "casualty"
        
        result = map_currency_condition(condition_value, policy_data, line_of_business)
        
        assert result is False
    
    def test_condition_value_none(self):
        """Test when condition value is None/NaN (should match everything)"""
        condition_value = None
        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "EUR",
        }
        line_of_business = "aviation"
        
        result = map_currency_condition(condition_value, policy_data, line_of_business)
        
        assert result is True
    
    def test_condition_value_nan(self):
        """Test when condition value is NaN (should match everything)"""
        condition_value = pd.NA
        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "EUR",
        }
        line_of_business = "aviation"
        
        result = map_currency_condition(condition_value, policy_data, line_of_business)
        
        assert result is True
    
    def test_unknown_line_of_business_fallback(self):
        """Test fallback for unknown line of business"""
        condition_value = "USD"
        policy_data = {
            "CURRENCY": "USD",
        }
        line_of_business = "unknown"
        
        result = map_currency_condition(condition_value, policy_data, line_of_business)
        
        assert result is True


class TestMatchConditionWithCurrencyMapping:
    """Tests for match_condition with currency mapping"""
    
    def test_aviation_currency_matching(self):
        """Test that aviation conditions match based on currency mapping"""
        # Create a condition with BUSCL_LIMIT_CURRENCY_CD=USD
        condition_data = {
            "BUSCL_LIMIT_CURRENCY_CD": "USD",
            "CESSION_PCT": 0.25,
            "SIGNED_SHARE_PCT": 0.5,
        }
        test_condition = condition(condition_data)
        
        # Policy with HULL_CURRENCY=USD (should match)
        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "EUR",
            "BUSCL_COUNTRY_CD": "France",
        }
        
        dimension_columns = ["BUSCL_LIMIT_CURRENCY_CD", "BUSCL_COUNTRY_CD"]
        line_of_business = "aviation"
        
        result = match_condition(policy_data, [test_condition], dimension_columns, line_of_business)
        
        assert result is not None
        assert result.get("BUSCL_LIMIT_CURRENCY_CD") == "USD"
    
    def test_aviation_currency_no_match(self):
        """Test that aviation conditions don't match when currencies don't match"""
        # Create a condition with BUSCL_LIMIT_CURRENCY_CD=USD
        condition_data = {
            "BUSCL_LIMIT_CURRENCY_CD": "USD",
            "CESSION_PCT": 0.25,
            "SIGNED_SHARE_PCT": 0.5,
        }
        test_condition = condition(condition_data)
        
        # Policy with different currencies (should not match)
        policy_data = {
            "HULL_CURRENCY": "EUR",
            "LIABILITY_CURRENCY": "EUR",
            "BUSCL_COUNTRY_CD": "France",
        }
        
        dimension_columns = ["BUSCL_LIMIT_CURRENCY_CD", "BUSCL_COUNTRY_CD"]
        line_of_business = "aviation"
        
        result = match_condition(policy_data, [test_condition], dimension_columns, line_of_business)
        
        assert result is None
    
    def test_casualty_currency_matching(self):
        """Test that casualty conditions match based on currency mapping"""
        # Create a condition with BUSCL_LIMIT_CURRENCY_CD=USD
        condition_data = {
            "BUSCL_LIMIT_CURRENCY_CD": "USD",
            "CESSION_PCT": 0.30,
            "SIGNED_SHARE_PCT": 0.6,
        }
        test_condition = condition(condition_data)
        
        # Policy with CURRENCY=USD (should match)
        policy_data = {
            "CURRENCY": "USD",
            "BUSCL_COUNTRY_CD": "United States",
        }
        
        dimension_columns = ["BUSCL_LIMIT_CURRENCY_CD", "BUSCL_COUNTRY_CD"]
        line_of_business = "casualty"
        
        result = match_condition(policy_data, [test_condition], dimension_columns, line_of_business)
        
        assert result is not None
        assert result.get("BUSCL_LIMIT_CURRENCY_CD") == "USD"
    
    def test_casualty_currency_no_match(self):
        """Test that casualty conditions don't match when currency doesn't match"""
        # Create a condition with BUSCL_LIMIT_CURRENCY_CD=USD
        condition_data = {
            "BUSCL_LIMIT_CURRENCY_CD": "USD",
            "CESSION_PCT": 0.30,
            "SIGNED_SHARE_PCT": 0.6,
        }
        test_condition = condition(condition_data)
        
        # Policy with different currency (should not match)
        policy_data = {
            "CURRENCY": "EUR",
            "BUSCL_COUNTRY_CD": "France",
        }
        
        dimension_columns = ["BUSCL_LIMIT_CURRENCY_CD", "BUSCL_COUNTRY_CD"]
        line_of_business = "casualty"
        
        result = match_condition(policy_data, [test_condition], dimension_columns, line_of_business)
        
        assert result is None
    
    def test_condition_without_currency_matches_everything(self):
        """Test that conditions without currency constraints match everything"""
        # Create a condition without BUSCL_LIMIT_CURRENCY_CD
        condition_data = {
            "BUSCL_COUNTRY_CD": "France",
            "CESSION_PCT": 0.25,
            "SIGNED_SHARE_PCT": 0.5,
        }
        test_condition = condition(condition_data)
        
        # Any policy should match
        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "EUR",
            "BUSCL_COUNTRY_CD": "France",
        }
        
        dimension_columns = ["BUSCL_LIMIT_CURRENCY_CD", "BUSCL_COUNTRY_CD"]
        line_of_business = "aviation"
        
        result = match_condition(policy_data, [test_condition], dimension_columns, line_of_business)
        
        assert result is not None
        assert result.get("BUSCL_COUNTRY_CD") == "France"
    
    def test_multiple_conditions_specificity(self):
        """Test that the most specific condition is chosen"""
        # Create two conditions with different specificity
        condition_general = condition({
            "BUSCL_LIMIT_CURRENCY_CD": "USD",
            "CESSION_PCT": 0.20,
            "SIGNED_SHARE_PCT": 0.4,
        })
        
        condition_specific = condition({
            "BUSCL_LIMIT_CURRENCY_CD": "USD",
            "BUSCL_COUNTRY_CD": "France",
            "CESSION_PCT": 0.25,
            "SIGNED_SHARE_PCT": 0.5,
        })
        
        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "USD",
            "BUSCL_COUNTRY_CD": "France",
        }
        
        dimension_columns = ["BUSCL_LIMIT_CURRENCY_CD", "BUSCL_COUNTRY_CD"]
        line_of_business = "aviation"
        
        result = match_condition(
            policy_data, 
            [condition_general, condition_specific], 
            dimension_columns, 
            line_of_business
        )
        
        assert result is not None
        # Should choose the more specific one
        assert result.get("BUSCL_COUNTRY_CD") == "France"
        assert result.get("CESSION_PCT") == 0.25


class TestCheckExclusionWithCurrencyMapping:
    """Tests for check_exclusion with currency mapping"""
    
    def test_exclusion_with_currency_matching(self):
        """Test that exclusions work with currency mapping"""
        # Create an exclusion condition
        exclusion_data = {
            "BUSCL_EXCLUDE_CD": "exclude",
            "BUSCL_LIMIT_CURRENCY_CD": "USD",
        }
        exclusion_condition = condition(exclusion_data)
        
        # Policy that matches the exclusion (should be excluded)
        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "EUR",
        }
        
        dimension_columns = ["BUSCL_EXCLUDE_CD", "BUSCL_LIMIT_CURRENCY_CD"]
        line_of_business = "aviation"
        
        result = check_exclusion(policy_data, [exclusion_condition], dimension_columns, line_of_business)
        
        assert result is True
    
    def test_exclusion_with_currency_no_match(self):
        """Test that exclusions don't trigger when currencies don't match"""
        # Create an exclusion condition
        exclusion_data = {
            "BUSCL_EXCLUDE_CD": "exclude",
            "BUSCL_LIMIT_CURRENCY_CD": "USD",
        }
        exclusion_condition = condition(exclusion_data)
        
        # Policy that doesn't match the exclusion (should not be excluded)
        policy_data = {
            "HULL_CURRENCY": "EUR",
            "LIABILITY_CURRENCY": "EUR",
        }
        
        dimension_columns = ["BUSCL_EXCLUDE_CD", "BUSCL_LIMIT_CURRENCY_CD"]
        line_of_business = "aviation"
        
        result = check_exclusion(policy_data, [exclusion_condition], dimension_columns, line_of_business)
        
        assert result is False
    
    def test_non_exclusion_condition_ignored(self):
        """Test that non-exclusion conditions are ignored in check_exclusion"""
        # Create a non-exclusion condition
        normal_condition = condition({
            "BUSCL_LIMIT_CURRENCY_CD": "USD",
            "CESSION_PCT": 0.25,
            "SIGNED_SHARE_PCT": 0.5,
        })
        
        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "EUR",
        }
        
        dimension_columns = ["BUSCL_LIMIT_CURRENCY_CD"]
        line_of_business = "aviation"
        
        result = check_exclusion(policy_data, [normal_condition], dimension_columns, line_of_business)
        
        assert result is False
