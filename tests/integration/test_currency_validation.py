"""
Tests d'intégration pour la validation des devises.
"""

import pandas as pd
from src.engine import apply_program_to_bordereau
from src.domain.bordereau import Bordereau
from src.builders import build_quota_share, build_program


def test_currency_validation_comprehensive():
    """Test complet de la validation des devises"""
    # Programme avec devise principale EUR et conditions multi-devises
    qs = build_quota_share(
        name="QS_MULTI",
        cession_pct=0.25,
        special_conditions=[
            {"ORIGINAL_CURRENCY": "EUR", "cession_pct": 0.30},
            {"ORIGINAL_CURRENCY": "USD", "cession_pct": 0.20},
        ]
    )
    program = build_program(
        name="MULTI_CURRENCY_PROGRAM",
        structures=[qs],
        main_currency="EUR",
        underwriting_department="casualty"
    )
    
    # Bordereau avec 3 polices : EUR (OK), USD (OK), GBP (Mismatch)
    test_data = {
        "INSURED_NAME": ["COMPANY EUR", "COMPANY USD", "COMPANY GBP"],
        "OCCURRENCE_LIMIT_100_ORIG": [1_000_000, 800_000, 600_000],
        "CEDENT_SHARE": [1.0, 1.0, 1.0],
        "INCEPTION_DT": ["2024-01-01", "2024-01-01", "2024-01-01"],
        "EXPIRE_DT": ["2025-01-01", "2025-01-01", "2025-01-01"],
        "ORIGINAL_CURRENCY": ["EUR", "USD", "GBP"],
    }
    
    bordereau_df = pd.DataFrame(test_data)
    bordereau = Bordereau(bordereau_df, uw_dept="casualty")
    calculation_date = "2024-06-01"
    bordereau_with_net, results_df = apply_program_to_bordereau(
        bordereau, program, calculation_date=calculation_date
    )
    
    # Vérifier les résultats
    assert len(results_df) == 3
    
    # Police EUR → OK (devise principale)
    result_eur = results_df.iloc[0]
    assert result_eur["exclusion_status"] == "included"
    assert result_eur["cession_to_reinsurer"] == 300_000  # 30% de 1M
    
    # Police USD → OK (condition spécifique autorise USD)
    result_usd = results_df.iloc[1]
    assert result_usd["exclusion_status"] == "included"
    assert result_usd["cession_to_reinsurer"] == 160_000  # 20% de 800K
    
    # Police GBP → Mismatch (ni devise principale ni condition spécifique)
    result_gbp = results_df.iloc[2]
    assert result_gbp["exclusion_status"] == "currency_mismatch"
    assert result_gbp["cession_to_reinsurer"] == 0
    assert result_gbp["effective_exposure"] == 0


def test_program_without_main_currency():
    """Test programme avec devise principale (main_currency est maintenant obligatoire)"""
    qs = build_quota_share(name="QS_ANY", cession_pct=0.25)
    program = build_program(
        name="ANY_CURRENCY_PROGRAM",
        structures=[qs],
        main_currency="USD",  # Maintenant obligatoire
        underwriting_department="casualty"
    )
    
    # Police USD → OK (devise principale)
    test_data = {
        "INSURED_NAME": ["COMPANY USD"],
        "OCCURRENCE_LIMIT_100_ORIG": [1_000_000],
        "CEDENT_SHARE": [1.0],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2025-01-01"],
        "ORIGINAL_CURRENCY": ["USD"],
    }
    
    bordereau_df = pd.DataFrame(test_data)
    bordereau = Bordereau(bordereau_df, uw_dept="casualty")
    calculation_date = "2024-06-01"
    bordereau_with_net, results_df = apply_program_to_bordereau(
        bordereau, program, calculation_date=calculation_date
    )
    
    result = results_df.iloc[0]
    assert result["exclusion_status"] == "included"
    assert result["cession_to_reinsurer"] == 250_000  # 25% de 1M