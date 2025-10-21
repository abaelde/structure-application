import pandas as pd
from tests.builders import build_quota_share, build_excess_of_loss, build_program
from src.engine import apply_program_to_bordereau
from src.domain.bordereau import Bordereau


def test_hull_liability_filtering_aviation():
    """
    Test du filtrage Hull/Liability en Aviation

    PROGRAMME:
    - QS_ALL: Quota Share 25% sur Hull + Liability (par défaut)
    - XOL_HULL: Excess of Loss 10M xs 5M sur Hull uniquement
    - XOL_LIABILITY: Excess of Loss 40M xs 10M sur Liability uniquement

    BORDEREAU:
    - Une police avec:
      * Hull: 100M × 15% = 15M
      * Liability: 500M × 10% = 50M
      * Total: 65M

    RÉSULTATS ATTENDUS:

    1. QS_ALL (25% sur 65M):
       - Input: 65M
       - Cession: 16.25M (65M × 25%)
       - Rétention: 48.75M

    2. XOL_HULL (10M xs 5M sur Hull uniquement): # AURE pas certain car si on fait un QS, prend t on la rétention du hull ou toute la rétention ?
       - Retained total après QS: 48.75M
       - Composant Hull de ce retained: 48.75M × (15M / 65M) = 11.25M
       - Input XOL_HULL: 11.25M (filtré sur Hull)
       - RESCALING (QS retention 75%): Attachment 5M × 0.75 = 3.75M, Limit 10M × 0.75 = 7.5M
       - Exposition dépassant attachment: 11.25M - 3.75M = 7.5M
       - Cession: min(7.5M, 7.5M) = 7.5M

    3. XOL_LIABILITY (40M xs 10M sur Liability uniquement):
       - Retained total après QS: 48.75M
       - Composant Liability de ce retained: 48.75M × (50M / 65M) = 37.5M
       - Input XOL_LIABILITY: 37.5M (filtré sur Liability)
       - RESCALING (QS retention 75%): Attachment 10M × 0.75 = 7.5M, Limit 40M × 0.75 = 30M
       - Exposition dépassant attachment: 37.5M - 7.5M = 30M
       - Cession: min(30M, 30M) = 30M
    """
    qs_all = build_quota_share(
        name="QS_ALL",
        conditions_config=[
            {
                "cession_pct": 0.25,
                "signed_share": 1.0,
                "includes_hull": True,
                "includes_liability": True,
            }
        ],
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    xol_hull = build_excess_of_loss(
        name="XOL_HULL",
        conditions_config=[
            {
                "attachment": 5_000_000,
                "limit": 10_000_000,
                "signed_share": 1.0,
                "includes_hull": True,
                "includes_liability": False,
            }
        ],
        predecessor_title="QS_ALL",
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    xol_liability = build_excess_of_loss(
        name="XOL_LIABILITY",
        conditions_config=[
            {
                "attachment": 10_000_000,
                "limit": 40_000_000,
                "signed_share": 1.0,
                "includes_hull": False,
                "includes_liability": True,
            }
        ],
        predecessor_title="QS_ALL",
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    program = build_program(
        name="AVIATION_HULL_LIABILITY_SPLIT",
        structures=[qs_all, xol_hull, xol_liability],
        underwriting_department="aviation",
    )

    bordereau_data = {
        "policy_id": ["POL-001"],
        "INSURED_NAME": ["AIR FRANCE"],
        "HULL_LIMIT": [100_000_000],
        "LIABILITY_LIMIT": [500_000_000],
        "HULL_SHARE": [0.15],
        "LIABILITY_SHARE": [0.10],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2025-12-31"],
        "BUSCL_COUNTRY_CD": [None],
        "BUSCL_REGION": [None],
    }

    bordereau_df = pd.DataFrame(bordereau_data)

    bordereau = Bordereau(bordereau_df, uw_dept="aviation")
    calculation_date = "2024-06-01"
    bordereau_with_net, results_df = apply_program_to_bordereau(
        bordereau, program, calculation_date=calculation_date
    )

    tolerance = 0.1
    result = results_df.iloc[0]

    hull_exposure = 100_000_000 * 0.15
    liability_exposure = 500_000_000 * 0.10
    total_exposure = hull_exposure + liability_exposure

    assert abs(result["exposure"] - total_exposure) < tolerance

    structures = result["structures_detail"]
    assert len(structures) == 3

    qs_all_detail = structures[0]
    assert qs_all_detail["structure_name"] == "QS_ALL"
    assert qs_all_detail["applied"] is True
    assert abs(qs_all_detail["input_exposure"] - 65_000_000) < tolerance
    expected_qs_cession = 65_000_000 * 0.25
    assert abs(qs_all_detail["ceded_to_layer_100pct"] - expected_qs_cession) < tolerance
    assert abs(qs_all_detail["ceded_to_reinsurer"] - expected_qs_cession) < tolerance

    xol_hull_detail = structures[1]
    assert xol_hull_detail["structure_name"] == "XOL_HULL"
    assert xol_hull_detail["applied"] is True
    retained_after_qs = total_exposure * 0.75
    hull_component_of_retained = retained_after_qs * (hull_exposure / total_exposure)
    assert (
        abs(xol_hull_detail["input_exposure"] - hull_component_of_retained) < tolerance
    )
    # SANS rescaling: attachment et limit restent inchangés
    attachment_hull = 5_000_000  # NON rescalé
    limit_hull = 10_000_000  # NON rescalé
    expected_hull_cession = max(
        0,
        min(limit_hull, hull_component_of_retained - attachment_hull),
    )
    assert (
        abs(xol_hull_detail["ceded_to_layer_100pct"] - expected_hull_cession)
        < tolerance
    )

    xol_liability_detail = structures[2]
    assert xol_liability_detail["structure_name"] == "XOL_LIABILITY"
    assert xol_liability_detail["applied"] is True
    liability_component_of_retained = retained_after_qs * (
        liability_exposure / total_exposure
    )
    assert (
        abs(xol_liability_detail["input_exposure"] - liability_component_of_retained)
        < tolerance
    )
    # SANS rescaling: attachment et limit restent inchangés
    attachment_liability = 10_000_000  # NON rescalé
    limit_liability = 40_000_000  # NON rescalé
    expected_liability_cession = max(
        0,
        min(
            limit_liability,
            liability_component_of_retained - attachment_liability,
        ),
    )
    assert (
        abs(xol_liability_detail["ceded_to_layer_100pct"] - expected_liability_cession)
        < tolerance
    )


def test_hull_only_structure():
    """
    Test d'une structure couvrant uniquement Hull

    PROGRAMME:
    - QS_HULL: Quota Share 30% sur Hull uniquement

    BORDEREAU:
    - Une police avec:
      * Hull: 100M × 15% = 15M
      * Liability: 500M × 10% = 50M
      * Total: 65M

    RÉSULTAT ATTENDU:
    - Cession: 4.5M (15M × 30%)
    - La partie Liability (50M) n'est pas cédée
    """
    qs_hull = build_quota_share(
        name="QS_HULL",
        conditions_config=[
            {
                "cession_pct": 0.30,
                "signed_share": 1.0,
                "includes_hull": True,
                "includes_liability": False,
            }
        ],
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    program = build_program(
        name="HULL_ONLY_PROGRAM",
        structures=[qs_hull],
        underwriting_department="aviation",
    )

    bordereau_data = {
        "policy_id": ["POL-001"],
        "INSURED_NAME": ["LUFTHANSA"],
        "HULL_LIMIT": [100_000_000],
        "LIABILITY_LIMIT": [500_000_000],
        "HULL_SHARE": [0.15],
        "LIABILITY_SHARE": [0.10],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2025-12-31"],
        "BUSCL_COUNTRY_CD": [None],
        "BUSCL_REGION": [None],
        "BUSCL_CLASS_OF_BUSINESS_1": [None],
        "BUSCL_CLASS_OF_BUSINESS_2": [None],
        "BUSCL_CLASS_OF_BUSINESS_3": [None],
        "BUSCL_LIMIT_CURRENCY_CD": [None],
    }

    bordereau_df = pd.DataFrame(bordereau_data)

    bordereau = Bordereau(bordereau_df, uw_dept="aviation")
    calculation_date = "2024-06-01"
    bordereau_with_net, results_df = apply_program_to_bordereau(
        bordereau, program, calculation_date=calculation_date
    )

    tolerance = 0.1
    result = results_df.iloc[0]

    hull_exposure = 100_000_000 * 0.15

    structures = result["structures_detail"]
    assert len(structures) == 1

    qs_detail = structures[0]
    assert qs_detail["structure_name"] == "QS_HULL"
    assert qs_detail["applied"] is True
    assert abs(qs_detail["input_exposure"] - hull_exposure) < tolerance
    expected_cession = hull_exposure * 0.30
    assert abs(qs_detail["ceded_to_layer_100pct"] - expected_cession) < tolerance
    assert abs(qs_detail["ceded_to_reinsurer"] - expected_cession) < tolerance


def test_liability_only_structure():
    """
    Test d'une structure couvrant uniquement Liability

    PROGRAMME:
    - QS_LIABILITY: Quota Share 20% sur Liability uniquement

    BORDEREAU:
    - Une police avec:
      * Hull: 100M × 15% = 15M
      * Liability: 500M × 10% = 50M
      * Total: 65M

    RÉSULTAT ATTENDU:
    - Cession: 10M (50M × 20%)
    - La partie Hull (15M) n'est pas cédée
    """
    qs_liability = build_quota_share(
        name="QS_LIABILITY",
        conditions_config=[
            {
                "cession_pct": 0.20,
                "signed_share": 1.0,
                "includes_hull": False,
                "includes_liability": True,
            }
        ],
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    program = build_program(
        name="LIABILITY_ONLY_PROGRAM",
        structures=[qs_liability],
        underwriting_department="aviation",
    )

    bordereau_data = {
        "policy_id": ["POL-001"],
        "INSURED_NAME": ["EMIRATES"],
        "HULL_LIMIT": [100_000_000],
        "LIABILITY_LIMIT": [500_000_000],
        "HULL_SHARE": [0.15],
        "LIABILITY_SHARE": [0.10],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2025-12-31"],
        "BUSCL_COUNTRY_CD": [None],
        "BUSCL_REGION": [None],
        "BUSCL_CLASS_OF_BUSINESS_1": [None],
        "BUSCL_CLASS_OF_BUSINESS_2": [None],
        "BUSCL_CLASS_OF_BUSINESS_3": [None],
        "BUSCL_LIMIT_CURRENCY_CD": [None],
    }

    bordereau_df = pd.DataFrame(bordereau_data)

    bordereau = Bordereau(bordereau_df, uw_dept="aviation")
    calculation_date = "2024-06-01"
    bordereau_with_net, results_df = apply_program_to_bordereau(
        bordereau, program, calculation_date=calculation_date
    )

    tolerance = 0.1
    result = results_df.iloc[0]

    liability_exposure = 500_000_000 * 0.10

    structures = result["structures_detail"]
    assert len(structures) == 1

    qs_detail = structures[0]
    assert qs_detail["structure_name"] == "QS_LIABILITY"
    assert qs_detail["applied"] is True
    assert abs(qs_detail["input_exposure"] - liability_exposure) < tolerance
    expected_cession = liability_exposure * 0.20
    assert abs(qs_detail["ceded_to_layer_100pct"] - expected_cession) < tolerance
    assert abs(qs_detail["ceded_to_reinsurer"] - expected_cession) < tolerance


def test_casualty_unaffected_by_hull_liability_flags():
    """
    Test que Casualty n'est pas affecté par les flags Hull/Liability

    PROGRAMME Casualty:
    - QS_30: Quota Share 30% (flags Hull/Liability non pertinents)

    BORDEREAU Casualty:
    - Une police avec LIMIT × CEDENT_SHARE

    RÉSULTAT ATTENDU:
    - Le programme fonctionne normalement (pas d'impact des flags)
    """
    qs_30 = build_quota_share(
        name="QS_30",
        conditions_config=[
            {
                "cession_pct": 0.30,
                "signed_share": 1.0,
                "includes_hull": True,
                "includes_liability": True,
            }
        ],
        claim_basis="risk_attaching",
        inception_date="2024-01-01",
        expiry_date="2025-01-01",
    )

    program = build_program(
        name="CASUALTY_PROGRAM", structures=[qs_30], underwriting_department="casualty"
    )

    bordereau_data = {
        "policy_id": ["CAS-001"],
        "INSURED_NAME": ["COMPANY A"],
        "LIMIT": [10_000_000],
        "CEDENT_SHARE": [0.75],
        "INCEPTION_DT": ["2024-01-01"],
        "EXPIRE_DT": ["2025-12-31"],
        "BUSCL_COUNTRY_CD": [None],
        "BUSCL_REGION": [None],
        "BUSCL_CLASS_OF_BUSINESS_1": [None],
        "BUSCL_CLASS_OF_BUSINESS_2": [None],
        "BUSCL_CLASS_OF_BUSINESS_3": [None],
        "BUSCL_LIMIT_CURRENCY_CD": [None],
    }

    bordereau_df = pd.DataFrame(bordereau_data)

    bordereau = Bordereau(bordereau_df, uw_dept="casualty")
    calculation_date = "2024-06-01"
    bordereau_with_net, results_df = apply_program_to_bordereau(
        bordereau, program, calculation_date=calculation_date
    )

    tolerance = 0.1
    result = results_df.iloc[0]

    exposure = 10_000_000 * 0.75

    structures = result["structures_detail"]
    assert len(structures) == 1

    qs_detail = structures[0]
    assert qs_detail["structure_name"] == "QS_30"
    assert qs_detail["applied"] is True
    assert abs(qs_detail["input_exposure"] - exposure) < tolerance
    expected_cession = exposure * 0.30
    assert abs(qs_detail["ceded_to_layer_100pct"] - expected_cession) < tolerance
