import pandas as pd
from src.engine import apply_program_to_bordereau
from src.domain.bordereau import Bordereau
from tests.builders import build_quota_share, build_program


def test_double_quota_share_parallel():
    """
    Test avec deux quota shares appliqués en parallèle

    STRUCTURE DU PROGRAMME:
    - QS_10% : Quota Share 10% (reinsurer share 100%)
    - QS_15% : Quota Share 15% (reinsurer share 100%)

    BORDEREAU:
    - Une seule police avec 1,000,000 d'exposure

    CALCUL ATTENDU:
    - Exposition brute: 1,000,000
    - Cession QS_10% (10%): 100,000
    - Cession QS_15% (15%): 150,000
    - Cession totale: 250,000 (10% + 15% = 25%)
    - Retenu (75%): 750,000

    PRINCIPE:
    - Les deux quota shares s'appliquent sur la même exposure brute
    - Les cessions s'additionnent
    - Retenu = Exposition brute - Total des cessions
    """
    qs_10 = build_quota_share(
        name="QS_10",
        conditions_config=[
            {
                "cession_pct": 0.10,
                "includes_hull": True,
                "includes_liability": True,
            }
        ],
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )
    qs_15 = build_quota_share(
        name="QS_15",
        conditions_config=[
            {
                "cession_pct": 0.15,
                "includes_hull": True,
                "includes_liability": True,
            }
        ],
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    program = build_program(
        name="DOUBLE_QUOTA_SHARE_2024",
        structures=[qs_10, qs_15],
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

    result = results_df.iloc[0]  # AURE : toujours bizarre cette sortie
    structures_detail = result["structures_detail"]

    exposure = 1_000_000
    expected_cession_qs_10 = exposure * 0.10
    expected_cession_qs_15 = exposure * 0.15
    expected_total_cession = expected_cession_qs_10 + expected_cession_qs_15
    expected_retained = exposure - expected_total_cession
    tolerance = 1

    assert result["exposure"] == exposure
    assert abs(result["cession_to_layer_100pct"] - expected_total_cession) < tolerance
    assert abs(result["retained_by_cedant"] - expected_retained) < tolerance

    total = result["cession_to_layer_100pct"] + result["retained_by_cedant"]
    assert abs(result["exposure"] - total) < tolerance

    assert len(structures_detail) >= 2
    applied_structures = [s for s in structures_detail if s["applied"]]
    assert len(applied_structures) == 2

    qs_10_detail = next(
        (s for s in applied_structures if "QS_10" in s.get("structure_name", "")), None
    )
    qs_15_detail = next(
        (s for s in applied_structures if "QS_15" in s.get("structure_name", "")), None
    )

    assert qs_10_detail is not None
    assert qs_15_detail is not None

    assert (
        abs(qs_10_detail.get("ceded_to_layer_100pct", 0) - expected_cession_qs_10)
        < tolerance
    )
    assert (
        abs(qs_15_detail.get("ceded_to_layer_100pct", 0) - expected_cession_qs_15)
        < tolerance
    )
