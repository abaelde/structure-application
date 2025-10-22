import pandas as pd
from src.engine import apply_program_to_bordereau
from src.domain.bordereau import Bordereau
from src.builders import build_quota_share, build_program, build_excess_of_loss


def test_single_line_quota_share_basic():
    """
    Test simple : Application d'un Quota Share 30% sur une unique ligne de bordereau

    STRUCTURE DU PROGRAMME:
    - QS_30% : Quota Share 30% (reinsurer share 100%)

    BORDEREAU:
    - Une seule police avec 1,000,000 d'exposure

    CALCUL ATTENDU:
    - Exposition brute: 1,000,000
    - Cession (30%): 300,000
    - Retenu (70%): 700,000
    """
    qs_structure = build_quota_share(
        name="QS_30",
        cession_pct=0.30,
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    program = build_program(
        name="SINGLE_QUOTA_SHARE_2024",
        structures=[qs_structure],
        underwriting_department="test",
    )

    test_data = {
        "INSURED_NAME": ["COMPANY TEST"],
        "exposure": [1_000_000],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2025-01-01"],
    }

    bordereau_df = pd.DataFrame(test_data)
    bordereau = Bordereau(bordereau_df, uw_dept="test")
    calculation_date = "2024-06-01"
    bordereau_with_net, results_df = apply_program_to_bordereau(
        bordereau, program, calculation_date=calculation_date
    )

    result = results_df.iloc[0]
    structures_detail = result["structures_detail"]

    exposure = 1_000_000
    expected_cession_rate = 0.30
    expected_cession = exposure * expected_cession_rate
    expected_retained = exposure * (1 - expected_cession_rate)
    tolerance = 1

    assert result["exposure"] == exposure
    assert abs(result["cession_to_layer_100pct"] - expected_cession) < tolerance
    assert abs(result["retained_by_cedant"] - expected_retained) < tolerance

    total = result["cession_to_layer_100pct"] + result["retained_by_cedant"]
    assert abs(result["exposure"] - total) < tolerance

    assert len(structures_detail) >= 1
    applied_structures = [s for s in structures_detail if s["applied"]]
    assert len(applied_structures) == 1


def test_single_line_quota_share_with_currency_matching():
    """
    Test avec matching sur la currency

    Programme avec 2 conditions:
    - condition USD: QS 25% pour BUSCL_LIMIT_CURRENCY_CD = USD
    - condition EUR: QS 35% pour BUSCL_LIMIT_CURRENCY_CD = EUR

    BORDEREAU:
    - Police USD avec exposure 1,000,000
    - Police EUR avec exposure 800,000

    CALCUL ATTENDU:
    - Police USD: doit matcher la condition USD (25%)
      * Exposition: 1,000,000
      * Cession (25%): 250,000
      * Retenu (75%): 750,000
    - Police EUR: doit matcher la condition EUR (35%)
      * Exposition: 800,000
      * Cession (35%): 280,000
      * Retenu (65%): 520,000
    """
    qs_structure = build_quota_share(
        name="QS_BY_CURRENCY",
        cession_pct=0.30,  # Valeur par défaut
        special_conditions=[
            {
                "currency_cd": "USD",
                "cession_pct": 0.25,
            },
            {
                "currency_cd": "EUR",
                "cession_pct": 0.35,
            },
        ],
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    program = build_program(
        name="QS_BY_CURRENCY_2024",
        structures=[qs_structure],
        underwriting_department="test",
    )

    test_data = {
        "INSURED_NAME": ["COMPANY USD", "COMPANY EUR"],
        "exposure": [1_000_000, 800_000],
        "INCEPTION_DT": ["2024-01-01", "2024-01-01"],
        "EXPIRE_DT": ["2025-01-01", "2025-01-01"],
        "CURRENCY": ["USD", "EUR"],
    }

    bordereau_df = pd.DataFrame(test_data)
    bordereau = Bordereau(bordereau_df, uw_dept="test")
    calculation_date = "2024-06-01"
    bordereau_with_net, results_df = apply_program_to_bordereau(
        bordereau, program, calculation_date=calculation_date
    )

    # Test de la première police (USD)
    usd_result = results_df.iloc[0]
    usd_exposure = 1_000_000
    usd_expected_cession_rate = 0.25
    usd_expected_cession = usd_exposure * usd_expected_cession_rate
    usd_expected_retained = usd_exposure * (1 - usd_expected_cession_rate)
    tolerance = 1

    assert usd_result["exposure"] == usd_exposure
    assert abs(usd_result["cession_to_layer_100pct"] - usd_expected_cession) < tolerance
    assert abs(usd_result["retained_by_cedant"] - usd_expected_retained) < tolerance

    usd_total = usd_result["cession_to_layer_100pct"] + usd_result["retained_by_cedant"]
    assert abs(usd_result["exposure"] - usd_total) < tolerance

    # Test de la deuxième police (EUR)
    eur_result = results_df.iloc[1]
    eur_exposure = 800_000
    eur_expected_cession_rate = 0.35
    eur_expected_cession = eur_exposure * eur_expected_cession_rate
    eur_expected_retained = eur_exposure * (1 - eur_expected_cession_rate)

    assert eur_result["exposure"] == eur_exposure
    assert abs(eur_result["cession_to_layer_100pct"] - eur_expected_cession) < tolerance
    assert abs(eur_result["retained_by_cedant"] - eur_expected_retained) < tolerance

    eur_total = eur_result["cession_to_layer_100pct"] + eur_result["retained_by_cedant"]
    assert abs(eur_result["exposure"] - eur_total) < tolerance
