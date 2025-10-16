import pandas as pd
from src.engine import apply_program_to_bordereau
from src.domain.bordereau import Bordereau
from tests.builders import build_quota_share, build_program


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
        conditions_config=[
            {
                "cession_pct": 0.30,
                "includes_hull": True,
                "includes_liability": True,
            }
        ],
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
    bordereau = Bordereau(bordereau_df, line_of_business="test")
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
    - Police en USD avec exposure 1,000,000

    CALCUL ATTENDU:
    - Doit matcher la condition USD
    - Exposition: 1,000,000
    - Cession (25%): 250,000
    - Retenu (75%): 750,000
    """
    qs_structure = build_quota_share(
        name="QS_BY_CURRENCY",
        conditions_config=[
            {
                "currency_cd": "USD",
                "cession_pct": 0.25,
                "includes_hull": True,
                "includes_liability": True,
            },
            {
                "currency_cd": "EUR",
                "cession_pct": 0.35,
                "includes_hull": True,
                "includes_liability": True,
            },
        ],
    )

    program = build_program(
        name="QS_BY_CURRENCY_2024",
        structures=[qs_structure],
        underwriting_department="test",
    )

    test_data = {
        "INSURED_NAME": ["COMPANY USD"],
        "exposure": [1_000_000],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2025-01-01"],
        "CURRENCY": ["USD"],
    }

    bordereau_df = pd.DataFrame(test_data)
    bordereau = Bordereau(bordereau_df, line_of_business="test")
    calculation_date = "2024-06-01"
    bordereau_with_net, results_df = apply_program_to_bordereau(
        bordereau, program, calculation_date=calculation_date
    )

    result = results_df.iloc[0]

    exposure = 1_000_000
    expected_cession_rate = 0.25
    expected_cession = exposure * expected_cession_rate
    expected_retained = exposure * (1 - expected_cession_rate)
    tolerance = 1

    assert result["exposure"] == exposure
    assert abs(result["cession_to_layer_100pct"] - expected_cession) < tolerance
    assert abs(result["retained_by_cedant"] - expected_retained) < tolerance
