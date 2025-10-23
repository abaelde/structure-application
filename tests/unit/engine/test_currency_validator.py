"""
Tests unitaires pour le service de validation des devises.
"""

import pytest
from src.domain.policy import Policy
from src.domain.program import Program
from src.engine.currency_validator import CurrencyValidator
from src.builders import build_condition


def test_currency_validation_comprehensive():
    """Test complet du service de validation des devises"""
    # Programme avec devise principale EUR
    program = Program(
        name="TEST",
        structures=[],
        dimension_columns=[],
        underwriting_department="casualty",
        main_currency="EUR"
    )
    
    # Test 1: Police EUR → OK
    policy_eur = Policy({"ORIGINAL_CURRENCY": "EUR"}, uw_dept="casualty")
    is_valid, error = CurrencyValidator.validate_policy_currency(policy_eur, program)
    assert is_valid
    assert error is None
    
    # Test 2: Police USD → Mismatch
    policy_usd = Policy({"ORIGINAL_CURRENCY": "USD"}, uw_dept="casualty")
    is_valid, error = CurrencyValidator.validate_policy_currency(policy_usd, program)
    assert not is_valid
    assert "USD" in error
    assert "EUR" in error
    
    # Test 3: Police USD avec condition qui l'autorise → OK
    condition = build_condition(currency_cd=["USD", "GBP"])
    is_valid, error = CurrencyValidator.validate_policy_currency(policy_usd, program, condition)
    assert is_valid
    assert error is None
    
    # Test 4: Programme avec devise principale différente → Mismatch
    program_usd = Program(
        name="TEST",
        structures=[],
        dimension_columns=[],
        underwriting_department="casualty",
        main_currency="USD"
    )
    is_valid, error = CurrencyValidator.validate_policy_currency(policy_usd, program_usd)
    assert is_valid  # USD = USD
    assert error is None