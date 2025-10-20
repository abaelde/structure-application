import pytest
import pandas as pd
from src.domain.structure import Structure
from src.domain.condition import Condition
from src.domain.constants import PRODUCT, CLAIM_BASIS, CLAIM_BASIS_VALUES


class TestStructure:
    def test_structure_creation_with_required_fields(self):
        """Test that Structure can be created with all required fields."""
        conditions = [Condition.from_dict({"cession_pct": 0.3, "SIGNED_SHARE_PCT": 1.0})]
        
        structure = Structure(
            structure_name="Test Structure",
            contract_order=1,
            type_of_participation=PRODUCT.QUOTA_SHARE,
            conditions=conditions,
            claim_basis=CLAIM_BASIS.RISK_ATTACHING,
            inception_date="2024-01-01",
            expiry_date="2025-01-01"
        )
        
        assert structure.structure_name == "Test Structure"
        assert structure.claim_basis == CLAIM_BASIS.RISK_ATTACHING
        assert structure.inception_date == pd.Timestamp("2024-01-01")
        assert structure.expiry_date == pd.Timestamp("2025-01-01")

    def test_structure_creation_missing_claim_basis(self):
        """Test that Structure creation fails when claim_basis is missing."""
        conditions = [Condition.from_dict({"cession_pct": 0.3, "SIGNED_SHARE_PCT": 1.0})]
        
        with pytest.raises(ValueError, match="INSPER_CLAIM_BASIS_CD is required"):
            Structure(
                structure_name="Test Structure",
                contract_order=1,
                type_of_participation=PRODUCT.QUOTA_SHARE,
                conditions=conditions,
                claim_basis=None,
                inception_date="2024-01-01",
                expiry_date="2025-01-01"
            )

    def test_structure_creation_invalid_claim_basis(self):
        """Test that Structure creation fails when claim_basis is invalid."""
        conditions = [Condition.from_dict({"cession_pct": 0.3, "SIGNED_SHARE_PCT": 1.0})]
        
        with pytest.raises(ValueError, match="INSPER_CLAIM_BASIS_CD is required"):
            Structure(
                structure_name="Test Structure",
                contract_order=1,
                type_of_participation=PRODUCT.QUOTA_SHARE,
                conditions=conditions,
                claim_basis="invalid_basis",
                inception_date="2024-01-01",
                expiry_date="2025-01-01"
            )

    def test_structure_creation_missing_inception_date(self):
        """Test that Structure creation fails when inception_date is missing."""
        conditions = [Condition.from_dict({"cession_pct": 0.3, "SIGNED_SHARE_PCT": 1.0})]
        
        with pytest.raises(ValueError, match="INSPER_EFFECTIVE_DATE is required"):
            Structure(
                structure_name="Test Structure",
                contract_order=1,
                type_of_participation=PRODUCT.QUOTA_SHARE,
                conditions=conditions,
                claim_basis=CLAIM_BASIS.RISK_ATTACHING,
                inception_date=None,
                expiry_date="2025-01-01"
            )

    def test_structure_creation_missing_expiry_date(self):
        """Test that Structure creation fails when expiry_date is missing."""
        conditions = [Condition.from_dict({"cession_pct": 0.3, "SIGNED_SHARE_PCT": 1.0})]
        
        with pytest.raises(ValueError, match="INSPER_EXPIRY_DATE is required"):
            Structure(
                structure_name="Test Structure",
                contract_order=1,
                type_of_participation=PRODUCT.QUOTA_SHARE,
                conditions=conditions,
                claim_basis=CLAIM_BASIS.RISK_ATTACHING,
                inception_date="2024-01-01",
                expiry_date=None
            )

    def test_structure_creation_invalid_date_range(self):
        """Test that Structure creation fails when expiry_date <= inception_date."""
        conditions = [Condition.from_dict({"cession_pct": 0.3, "SIGNED_SHARE_PCT": 1.0})]
        
        with pytest.raises(ValueError, match="INSPER_EXPIRY_DATE must be strictly after INSPER_EFFECTIVE_DATE"):
            Structure(
                structure_name="Test Structure",
                contract_order=1,
                type_of_participation=PRODUCT.QUOTA_SHARE,
                conditions=conditions,
                claim_basis=CLAIM_BASIS.RISK_ATTACHING,
                inception_date="2024-01-01",
                expiry_date="2024-01-01"  # Same date
            )

    def test_structure_creation_invalid_date_range_reversed(self):
        """Test that Structure creation fails when expiry_date < inception_date."""
        conditions = [Condition.from_dict({"cession_pct": 0.3, "SIGNED_SHARE_PCT": 1.0})]
        
        with pytest.raises(ValueError, match="INSPER_EXPIRY_DATE must be strictly after INSPER_EFFECTIVE_DATE"):
            Structure(
                structure_name="Test Structure",
                contract_order=1,
                type_of_participation=PRODUCT.QUOTA_SHARE,
                conditions=conditions,
                claim_basis=CLAIM_BASIS.RISK_ATTACHING,
                inception_date="2025-01-01",
                expiry_date="2024-01-01"  # Earlier date
            )

    def test_structure_claim_basis_normalization(self):
        """Test that claim_basis is normalized to lowercase."""
        conditions = [Condition.from_dict({"cession_pct": 0.3, "SIGNED_SHARE_PCT": 1.0})]
        
        structure = Structure(
            structure_name="Test Structure",
            contract_order=1,
            type_of_participation=PRODUCT.QUOTA_SHARE,
            conditions=conditions,
            claim_basis="RISK_ATTACHING",  # Uppercase
            inception_date="2024-01-01",
            expiry_date="2025-01-01"
        )
        
        assert structure.claim_basis == CLAIM_BASIS.RISK_ATTACHING  # Should be lowercase

    def test_structure_is_applicable_risk_attaching(self):
        """Test is_applicable method for risk attaching basis."""
        conditions = [Condition.from_dict({"cession_pct": 0.3, "SIGNED_SHARE_PCT": 1.0})]
        
        structure = Structure(
            structure_name="Test Structure",
            contract_order=1,
            type_of_participation=PRODUCT.QUOTA_SHARE,
            conditions=conditions,
            claim_basis=CLAIM_BASIS.RISK_ATTACHING,
            inception_date="2024-01-01",
            expiry_date="2025-01-01"
        )
        
        # Mock policy with inception date
        class MockPolicy:
            def __init__(self, inception):
                self.inception = inception
        
        policy = MockPolicy(pd.Timestamp("2024-06-01"))
        
        # Should be applicable (policy inception is within structure period)
        assert structure.is_applicable(policy) is True
        
        # Should not be applicable (policy inception is before structure period)
        policy_early = MockPolicy(pd.Timestamp("2023-06-01"))
        assert structure.is_applicable(policy_early) is False

    def test_structure_is_applicable_loss_occurring(self):
        """Test is_applicable method for loss occurring basis."""
        conditions = [Condition.from_dict({"cession_pct": 0.3, "SIGNED_SHARE_PCT": 1.0})]
        
        structure = Structure(
            structure_name="Test Structure",
            contract_order=1,
            type_of_participation=PRODUCT.QUOTA_SHARE,
            conditions=conditions,
            claim_basis=CLAIM_BASIS.LOSS_OCCURRING,
            inception_date="2024-01-01",
            expiry_date="2025-01-01"
        )
        
        # Mock policy
        class MockPolicy:
            def __init__(self, inception):
                self.inception = inception
        
        policy = MockPolicy(pd.Timestamp("2024-06-01"))
        
        # Should be applicable (evaluation date is within structure period)
        assert structure.is_applicable(policy, evaluation_date="2024-06-01") is True
        
        # Should not be applicable (evaluation date is before structure period)
        assert structure.is_applicable(policy, evaluation_date="2023-06-01") is False
