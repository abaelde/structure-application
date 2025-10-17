import pandas as pd
from src.engine import apply_program_to_bordereau
from src.domain.bordereau import Bordereau
from tests.builders import build_excess_of_loss, build_program


def test_single_line_excess_of_loss_basic():
    """
    Test simple : Application d'un Excess of Loss sur une unique ligne de bordereau

    STRUCTURE DU PROGRAMME:
    - XL_15Mxs10M : Excess of Loss 15M xs 10M (reinsurer share 100%)

    BORDEREAU:
    - Une seule police avec 30,000,000 d'exposure

    CALCUL ATTENDU:
    - Exposition brute: 30,000,000
    - Priorité (attachment): 10,000,000
    - Limite: 15,000,000
    - Cession: min(30M - 10M, 15M) = 15,000,000
    - Retenu: 30M - 15M = 15,000,000
    """
    xl_structure = build_excess_of_loss(
        name="XL_15Mxs10M",
        attachment=10_000_000,
        limit=15_000_000,
    )

    program = build_program(
        name="SINGLE_EXCESS_OF_LOSS_2024",
        structures=[xl_structure],
        underwriting_department="test",
    )

    test_data = {
        "INSURED_NAME": ["COMPANY TEST"],
        "exposure": [30_000_000],
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

    exposure = 30_000_000
    attachment = 10_000_000
    limit = 15_000_000
    expected_cession = min(exposure - attachment, limit)
    expected_retained = exposure - expected_cession
    tolerance = 1

    assert result["exposure"] == exposure
    assert abs(result["cession_to_layer_100pct"] - expected_cession) < tolerance
    assert abs(result["retained_by_cedant"] - expected_retained) < tolerance

    total = result["cession_to_layer_100pct"] + result["retained_by_cedant"]
    assert abs(result["exposure"] - total) < tolerance

    assert len(structures_detail) >= 1
    applied_structures = [s for s in structures_detail if s["applied"]]
    assert len(applied_structures) == 1


def test_single_line_excess_of_loss_by_country():
    """
    Test Excess of Loss avec filtrage par pays

    STRUCTURE DU PROGRAMME:
    - XL_BY_COUNTRY : Deux conditions XL différentes selon le pays
      - US: 20M xs 5M (pour BUSCL_COUNTRY_CD = US)
      - FR: 15M xs 10M (pour BUSCL_COUNTRY_CD = FR)

    BORDEREAU:
    - Police US avec 30,000,000 d'exposure
    - Police FR avec 25,000,000 d'exposure

    CALCUL ATTENDU:
    - Police US: doit matcher la condition US (20M xs 5M)
      * Exposition: 30,000,000
      * Cession: min(30M - 5M, 20M) = 20,000,000
      * Retenu: 30M - 20M = 10,000,000
    - Police FR: doit matcher la condition FR (15M xs 10M)
      * Exposition: 25,000,000
      * Cession: min(25M - 10M, 15M) = 15,000,000
      * Retenu: 25M - 15M = 10,000,000
    """
    xl_structure = build_excess_of_loss(
        name="XL_BY_COUNTRY",
        conditions_config=[
            {
                "country_cd": "US",
                "attachment": 5_000_000,
                "limit": 20_000_000,
            },
            {
                "country_cd": "FR",
                "attachment": 10_000_000,
                "limit": 15_000_000,
            },
        ],
    )

    program = build_program(
        name="XL_BY_COUNTRY_2024",
        structures=[xl_structure],
        underwriting_department="test",
    )

    test_data = {
        "INSURED_NAME": ["COMPANY US", "COMPANY FR"],
        "exposure": [30_000_000, 25_000_000],
        "INCEPTION_DT": ["2024-01-01", "2024-01-01"],
        "EXPIRE_DT": ["2025-01-01", "2025-01-01"],
        "BUSCL_COUNTRY_CD": ["US", "FR"],
    }

    bordereau_df = pd.DataFrame(test_data)
    bordereau = Bordereau(bordereau_df, uw_dept="test")
    calculation_date = "2024-06-01"
    bordereau_with_net, results_df = apply_program_to_bordereau(
        bordereau, program, calculation_date=calculation_date
    )

    # Test de la première police (US)
    us_result = results_df.iloc[0]
    us_exposure = 30_000_000
    us_attachment = 5_000_000  # Condition US
    us_limit = 20_000_000  # Condition US
    us_expected_cession = min(us_exposure - us_attachment, us_limit)
    us_expected_retained = us_exposure - us_expected_cession
    tolerance = 1

    assert us_result["exposure"] == us_exposure
    assert abs(us_result["cession_to_layer_100pct"] - us_expected_cession) < tolerance
    assert abs(us_result["retained_by_cedant"] - us_expected_retained) < tolerance

    us_total = us_result["cession_to_layer_100pct"] + us_result["retained_by_cedant"]
    assert abs(us_result["exposure"] - us_total) < tolerance

    # Test de la deuxième police (FR)
    fr_result = results_df.iloc[1]
    fr_exposure = 25_000_000
    fr_attachment = 10_000_000  # Condition FR
    fr_limit = 15_000_000  # Condition FR
    fr_expected_cession = min(fr_exposure - fr_attachment, fr_limit)
    fr_expected_retained = fr_exposure - fr_expected_cession

    assert fr_result["exposure"] == fr_exposure
    assert abs(fr_result["cession_to_layer_100pct"] - fr_expected_cession) < tolerance
    assert abs(fr_result["retained_by_cedant"] - fr_expected_retained) < tolerance

    fr_total = fr_result["cession_to_layer_100pct"] + fr_result["retained_by_cedant"]
    assert abs(fr_result["exposure"] - fr_total) < tolerance
