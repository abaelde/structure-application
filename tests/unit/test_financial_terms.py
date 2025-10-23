"""
Tests unitaires pour le Value Object FinancialTerms et les nouvelles méthodes de Structure.
"""

import pytest
import pandas as pd
from src.domain.financial_terms import FinancialTerms
from src.domain.structure import Structure
from src.domain.condition import Condition


class TestFinancialTerms:
    """Tests pour le Value Object FinancialTerms"""

    def test_creation_with_all_values(self):
        """Test de création avec toutes les valeurs"""
        terms = FinancialTerms(
            cession_pct=0.2,
            attachment=10.0,
            limit=50.0,
            signed_share=0.8
        )
        
        assert terms.cession_pct == 0.2
        assert terms.attachment == 10.0
        assert terms.limit == 50.0
        assert terms.signed_share == 0.8

    def test_creation_with_defaults(self):
        """Test de création avec valeurs par défaut"""
        terms = FinancialTerms()
        
        assert terms.cession_pct is None
        assert terms.attachment is None
        assert terms.limit is None
        assert terms.signed_share is None  # pas de valeur par défaut

    def test_merge_with_overrides(self):
        """Test de fusion avec des overrides"""
        base = FinancialTerms(cession_pct=0.2, attachment=10.0, limit=50.0, signed_share=0.8)
        merged = base.merge(cession_pct=0.3, limit=75.0)
        
        assert merged.cession_pct == 0.3  # overridé
        assert merged.attachment == 10.0  # inchangé
        assert merged.limit == 75.0  # overridé
        assert merged.signed_share == 0.8  # inchangé

    def test_merge_with_none_values(self):
        """Test de fusion avec des valeurs None (ne doit pas changer)"""
        base = FinancialTerms(cession_pct=0.2, attachment=10.0)
        merged = base.merge(cession_pct=None, attachment=None, limit=50.0)
        
        assert merged.cession_pct == 0.2  # inchangé car None dans overrides
        assert merged.attachment == 10.0  # inchangé car None dans overrides
        assert merged.limit == 50.0  # ajouté

    def test_to_condition_dict(self):
        """Test de conversion vers le format condition"""
        terms = FinancialTerms(cession_pct=0.2, attachment=10.0, limit=50.0, signed_share=0.8)
        condition_dict = terms.to_condition_dict()
        
        expected = {
            "CESSION_PCT": 0.2,
            "ATTACHMENT_POINT_100": 10.0,
            "LIMIT_100": 50.0,
            "SIGNED_SHARE_PCT": 0.8,
        }
        assert condition_dict == expected

    def test_diff_identical_terms(self):
        """Test de différence avec des termes identiques"""
        terms1 = FinancialTerms(cession_pct=0.2, attachment=10.0)
        terms2 = FinancialTerms(cession_pct=0.2, attachment=10.0)
        
        diff = terms1.diff(terms2)
        assert diff == {}

    def test_diff_different_terms(self):
        """Test de différence avec des termes différents"""
        terms1 = FinancialTerms(cession_pct=0.2, attachment=10.0, limit=50.0)
        terms2 = FinancialTerms(cession_pct=0.3, attachment=10.0, limit=75.0)
        
        diff = terms1.diff(terms2)
        expected = {"CESSION_PCT": 0.3, "LIMIT_100": 75.0}
        assert diff == expected

    def test_diff_with_none_values(self):
        """Test de différence avec des valeurs None"""
        terms1 = FinancialTerms(cession_pct=0.2, attachment=10.0)
        terms2 = FinancialTerms(cession_pct=0.3, attachment=None, limit=50.0)
        
        diff = terms1.diff(terms2)
        expected = {"CESSION_PCT": 0.3, "LIMIT_100": 50.0}
        assert diff == expected

    def test_string_representation(self):
        """Test de la représentation string"""
        terms = FinancialTerms(cession_pct=0.2, attachment=10.0, limit=50.0, signed_share=0.8)
        str_repr = str(terms)
        
        assert "cession=0.2%" in str_repr
        assert "attachment=10.0" in str_repr
        assert "limit=50.0" in str_repr
        assert "share=0.8" in str_repr

    def test_string_representation_with_defaults(self):
        """Test de la représentation string avec valeurs par défaut"""
        terms = FinancialTerms()
        str_repr = str(terms)
        
        assert str_repr == "FinancialTerms()"


class TestStructureFinancialMethods:
    """Tests pour les nouvelles méthodes financières de Structure"""

    @pytest.fixture
    def sample_structure(self):
        """Structure de test avec valeurs par défaut"""
        return Structure(
            structure_name="Test Structure",
            type_of_participation="QUOTA_SHARE",
            conditions=[],
            claim_basis="risk_attaching",
            inception_date="2024-01-01",
            expiry_date="2024-12-31",
            cession_pct=0.15,
            attachment=5.0,
            limit=25.0,
            signed_share=0.9
        )

    def test_default_terms_property(self, sample_structure):
        """Test de la propriété default_terms"""
        default_terms = sample_structure.default_terms
        
        assert isinstance(default_terms, FinancialTerms)
        assert default_terms.cession_pct == 0.15
        assert default_terms.attachment == 5.0
        assert default_terms.limit == 25.0
        assert default_terms.signed_share == 0.9

    def test_default_terms_with_none_signed_share(self):
        """Test de default_terms avec signed_share None (doit rester None)"""
        structure = Structure(
            structure_name="Test",
            type_of_participation="QUOTA_SHARE",
            conditions=[],
            claim_basis="risk_attaching",
            inception_date="2024-01-01",
            expiry_date="2024-12-31",
            signed_share=None
        )
        
        default_terms = structure.default_terms
        assert default_terms.signed_share is None

    def test_resolve_condition(self, sample_structure):
        """Test de résolution de condition avec overrides"""
        template = {
            "INCLUDES_HULL": True,
            "INCLUDES_LIABILITY": False,
            "AIRCRAFT_TYPE": "Commercial"
        }
        overrides = {
            "CESSION_PCT": 0.25,
            "LIMIT_100": 30.0
        }
        
        condition = sample_structure.resolve_condition(template, overrides)
        
        # Vérifier que c'est bien une Condition
        assert isinstance(condition, Condition)
        
        # Vérifier les valeurs résolues
        assert condition.cession_pct == 0.25  # overridé
        assert condition.attachment == 5.0  # default de la structure
        assert condition.limit == 30.0  # overridé
        assert condition.signed_share == 0.9  # default de la structure
        
        # Vérifier que les autres champs du template sont préservés
        assert condition.includes_hull is True
        assert condition.includes_liability is False

    def test_resolve_condition_with_unknown_overrides(self, sample_structure):
        """Test de résolution avec des overrides inconnus (doivent être ignorés)"""
        template = {"INCLUDES_HULL": True}
        overrides = {
            "CESSION_PCT": 0.25,
            "UNKNOWN_FIELD": "ignored"
        }
        
        condition = sample_structure.resolve_condition(template, overrides)
        assert condition.cession_pct == 0.25
        # UNKNOWN_FIELD ne doit pas apparaître dans la condition

    def test_overrides_for(self, sample_structure):
        """Test de détection des overrides"""
        condition_dict = {
            "CESSION_PCT": 0.25,  # différent du default (0.15)
            "ATTACHMENT_POINT_100": 5.0,  # identique au default
            "LIMIT_100": 30.0,  # différent du default (25.0)
            "SIGNED_SHARE_PCT": 0.9  # identique au default
        }
        
        overrides = sample_structure.overrides_for(condition_dict)
        
        expected = {
            "CESSION_PCT": 0.25,
            "LIMIT_100": 30.0
        }
        assert overrides == expected

    def test_overrides_for_no_differences(self, sample_structure):
        """Test de détection des overrides quand il n'y en a pas"""
        condition_dict = {
            "CESSION_PCT": 0.15,  # identique au default
            "ATTACHMENT_POINT_100": 5.0,  # identique au default
            "LIMIT_100": 25.0,  # identique au default
            "SIGNED_SHARE_PCT": 0.9  # identique au default
        }
        
        overrides = sample_structure.overrides_for(condition_dict)
        assert overrides == {}

    def test_overrides_for_with_none_values(self, sample_structure):
        """Test de détection des overrides avec des valeurs None"""
        condition_dict = {
            "CESSION_PCT": None,
            "ATTACHMENT_POINT_100": 5.0,
            "LIMIT_100": 30.0,
            "SIGNED_SHARE_PCT": 0.9
        }
        
        overrides = sample_structure.overrides_for(condition_dict)
        
        # Seule LIMIT_100 diffère (None vs 25.0)
        expected = {"LIMIT_100": 30.0}
        assert overrides == expected

    def test_roundtrip_consistency(self, sample_structure):
        """Test de cohérence round-trip: resolve_condition puis overrides_for"""
        template = {"INCLUDES_HULL": True}
        overrides = {"CESSION_PCT": 0.25, "LIMIT_100": 30.0}
        
        # 1. Résoudre la condition
        condition = sample_structure.resolve_condition(template, overrides)
        
        # 2. Extraire les overrides
        extracted_overrides = sample_structure.overrides_for(condition.to_dict())
        
        # 3. Vérifier la cohérence
        assert extracted_overrides == overrides
