import pytest
import pandas as pd
from src.engine.condition_matcher import (
    match_condition,
    check_exclusion,
)
from src.domain import Condition
from src.domain.policy import Policy


class TestCurrencyMapping:
    """Tests for the currency mapping logic via Policy.get_dimension_value"""

    def test_aviation_mapping_hull_currency(self):
        """Test aviation mapping returns HULL_CURRENCY"""
        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "EUR",
        }
        uw_departement = "aviation"

        policy = Policy(raw=policy_data, uw_dept=uw_departement)
        result = policy.get_dimension_value("BUSCL_LIMIT_CURRENCY_CD")

        assert result == "USD"

    def test_casualty_mapping_currency(self):
        """Test casualty mapping returns CURRENCY"""
        policy_data = {
            "CURRENCY": "USD",
        }
        uw_departement = "casualty"

        policy = Policy(raw=policy_data, uw_dept=uw_departement)
        result = policy.get_dimension_value("BUSCL_LIMIT_CURRENCY_CD")

        assert result == "USD"

    def test_unknown_line_of_business_fallback(self):
        """Test fallback for unknown line of business"""
        policy_data = {
            "CURRENCY": "USD",
        }
        uw_departement = "unknown"

        policy = Policy(raw=policy_data, uw_dept=uw_departement)
        result = policy.get_dimension_value("BUSCL_LIMIT_CURRENCY_CD")

        # Should fallback to direct dimension name # AURE
        assert result is None  # BUSCL_LIMIT_CURRENCY_CD not in policy_data

    def test_missing_currency_data(self):
        """Test when currency data is missing"""
        policy_data = {
            "BUSCL_COUNTRY_CD": "France",
        }
        uw_departement = "aviation"

        policy = Policy(raw=policy_data, uw_dept=uw_departement)
        result = policy.get_dimension_value("BUSCL_LIMIT_CURRENCY_CD")

        assert result is None


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
        test_condition = Condition(condition_data)

        # Policy with HULL_CURRENCY=USD (should match)
        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "EUR",
            "BUSCL_COUNTRY_CD": "France",
        }

        dimension_columns = ["BUSCL_LIMIT_CURRENCY_CD", "BUSCL_COUNTRY_CD"]
        uw_departement = "aviation"

        policy = Policy(raw=policy_data, uw_dept=uw_departement)
        result = match_condition(
            policy, [test_condition], dimension_columns
        )

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
        test_condition = Condition(condition_data)

        # Policy with different currencies (should not match)
        policy_data = {
            "HULL_CURRENCY": "EUR",
            "LIABILITY_CURRENCY": "EUR",
            "BUSCL_COUNTRY_CD": "France",
        }

        dimension_columns = ["BUSCL_LIMIT_CURRENCY_CD", "BUSCL_COUNTRY_CD"]
        uw_departement = "aviation"

        policy = Policy(raw=policy_data, uw_dept=uw_departement)
        result = match_condition(
            policy, [test_condition], dimension_columns
        )

        assert result is None

    def test_casualty_currency_matching(self):
        """Test that casualty conditions match based on currency mapping"""
        # Create a condition with BUSCL_LIMIT_CURRENCY_CD=USD
        condition_data = {
            "BUSCL_LIMIT_CURRENCY_CD": "USD",
            "CESSION_PCT": 0.30,
            "SIGNED_SHARE_PCT": 0.6,
        }
        test_condition = Condition(condition_data)

        # Policy with CURRENCY=USD (should match)
        policy_data = {
            "CURRENCY": "USD",
            "BUSCL_COUNTRY_CD": "United States",
        }

        dimension_columns = ["BUSCL_LIMIT_CURRENCY_CD", "BUSCL_COUNTRY_CD"]
        uw_departement = "casualty"

        policy = Policy(raw=policy_data, uw_dept=uw_departement)
        result = match_condition(
            policy, [test_condition], dimension_columns
        )

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
        test_condition = Condition(condition_data)

        # Policy with different currency (should not match)
        policy_data = {
            "CURRENCY": "EUR",
            "BUSCL_COUNTRY_CD": "France",
        }

        dimension_columns = ["BUSCL_LIMIT_CURRENCY_CD", "BUSCL_COUNTRY_CD"]
        uw_departement = "casualty"

        policy = Policy(raw=policy_data, uw_dept=uw_departement)
        result = match_condition(
            policy, [test_condition], dimension_columns
        )

        assert result is None

    def test_condition_without_currency_matches_everything(self):
        """Test that conditions without currency constraints match everything"""
        # Create a condition without BUSCL_LIMIT_CURRENCY_CD
        condition_data = {
            "BUSCL_COUNTRY_CD": "France",
            "CESSION_PCT": 0.25,
            "SIGNED_SHARE_PCT": 0.5,
        }
        test_condition = Condition(condition_data)

        # Any policy should match
        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "EUR",
            "BUSCL_COUNTRY_CD": "France",
        }

        dimension_columns = ["BUSCL_LIMIT_CURRENCY_CD", "BUSCL_COUNTRY_CD"]
        uw_departement = "aviation"

        policy = Policy(raw=policy_data, uw_dept=uw_departement)
        result = match_condition(
            policy, [test_condition], dimension_columns
        )

        assert result is not None
        assert result.get("BUSCL_COUNTRY_CD") == "France"

    def test_multiple_conditions_specificity(self):
        """Test that the most specific condition is chosen"""
        # Create two conditions with different specificity
        condition_general = Condition(
            {
                "BUSCL_LIMIT_CURRENCY_CD": "USD",
                "CESSION_PCT": 0.20,
                "SIGNED_SHARE_PCT": 0.4,
            }
        )

        condition_specific = Condition(
            {
                "BUSCL_LIMIT_CURRENCY_CD": "USD",
                "BUSCL_COUNTRY_CD": "France",
                "CESSION_PCT": 0.25,
                "SIGNED_SHARE_PCT": 0.5,
            }
        )

        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "USD",
            "BUSCL_COUNTRY_CD": "France",
        }

        dimension_columns = ["BUSCL_LIMIT_CURRENCY_CD", "BUSCL_COUNTRY_CD"]
        uw_departement = "aviation"

        policy = Policy(raw=policy_data, uw_dept=uw_departement)
        result = match_condition(
            policy,
            [condition_general, condition_specific],
            dimension_columns,
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
        exclusion_condition = Condition(exclusion_data)

        # Policy that matches the exclusion (should be excluded)
        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "EUR",
        }

        dimension_columns = ["BUSCL_EXCLUDE_CD", "BUSCL_LIMIT_CURRENCY_CD"]
        uw_departement = "aviation"

        policy = Policy(raw=policy_data, uw_dept=uw_departement)
        result = check_exclusion(
            policy, [exclusion_condition], dimension_columns
        )

        assert result is True

    def test_exclusion_with_currency_no_match(self):
        """Test that exclusions don't trigger when currencies don't match"""
        # Create an exclusion condition
        exclusion_data = {
            "BUSCL_EXCLUDE_CD": "exclude",
            "BUSCL_LIMIT_CURRENCY_CD": "USD",
        }
        exclusion_condition = Condition(exclusion_data)

        # Policy that doesn't match the exclusion (should not be excluded)
        policy_data = {
            "HULL_CURRENCY": "EUR",
            "LIABILITY_CURRENCY": "EUR",
        }

        dimension_columns = ["BUSCL_EXCLUDE_CD", "BUSCL_LIMIT_CURRENCY_CD"]
        uw_departement = "aviation"

        policy = Policy(raw=policy_data, uw_dept=uw_departement)
        result = check_exclusion(
            policy, [exclusion_condition], dimension_columns
        )

        assert result is False

    def test_non_exclusion_condition_ignored(self):
        """Test that non-exclusion conditions are ignored in check_exclusion"""
        # Create a non-exclusion condition
        normal_condition = Condition(
            {
                "BUSCL_LIMIT_CURRENCY_CD": "USD",
                "CESSION_PCT": 0.25,
                "SIGNED_SHARE_PCT": 0.5,
            }
        )

        policy_data = {
            "HULL_CURRENCY": "USD",
            "LIABILITY_CURRENCY": "EUR",
        }

        dimension_columns = ["BUSCL_LIMIT_CURRENCY_CD"]
        uw_departement = "aviation"

        policy = Policy(raw=policy_data, uw_dept=uw_departement)
        result = check_exclusion(
            policy, [normal_condition], dimension_columns
        )

        assert result is False
